"""Regime-switching real-data simulation and Polymarket valuation for matches 103-104.

The probability engine never reads market prices.  Prices are joined only after
all simulations and stress scenarios have been frozen.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from simulate_match_real_data_engine import (
    build_player_table,
    derive_event_rates,
    derive_team_profiles,
    fit_historical,
    normalized_minute_curve,
    referee_posterior,
    score_distribution,
    shootout_home_win,
)


ROOT = Path(__file__).resolve().parents[1]


def fee(price: float, rate: float) -> float:
    return rate * price * (1.0 - price)


def probability_ci(p: float, n: int) -> list[float]:
    half = 1.96 * math.sqrt(max(p * (1-p), 1e-9) / n)
    return [max(0.0, p-half), min(1.0, p+half)]


def projected_lineups(payload: dict, home: str, away: str) -> dict:
    out = {"status": payload["status"]}
    for team in (home, away):
        spec = payload["teams"][team]
        out[team] = {
            "starters": [x["name"] for x in spec["starting_xi"]],
            "bench_priority": [x["name"] for x in spec["bench"]],
            "availability": {x["name"]: float(x.get("availability", 1.0))
                             for x in spec["starting_xi"] + spec["bench"]},
            "appearance_probability": {x["name"]: float(x["appearance_probability"])
                                       for x in spec["starting_xi"] + spec["bench"] if "appearance_probability" in x},
            "minutes_if_appears": {x["name"]: float(x["minutes_if_appears"])
                                   for x in spec["starting_xi"] + spec["bench"] if "minutes_if_appears" in x},
            "tournament_assists": {x["name"]: int(x["tournament_assists"])
                                   for x in spec["starting_xi"] + spec["bench"] if "tournament_assists" in x},
        }
    return out


def regime_draw(rng: np.random.Generator, fixture: dict, n: int, override: dict) -> tuple[np.ndarray, ...]:
    names = ["cagey", "normal", "open"]
    weights = dict(fixture["regime_weights"])
    weights.update(override.get("regime_weights", {}))
    p = np.array([weights[x] for x in names], float); p /= p.sum()
    idx = rng.choice(3, n, p=p)
    tempo = np.array([fixture["regime_tempo"][x] for x in names])[idx]
    conversion = np.array([fixture["regime_conversion"][x] for x in names])[idx]
    sot_multiplier = np.array([
        fixture.get("regime_sot_multiplier", {}).get(x, 1.0) for x in names
    ])[idx]
    corner_multiplier = np.array([
        fixture.get("regime_corner_multiplier", {}).get(x, 1.0) for x in names
    ])[idx]
    return idx, tempo, conversion, sot_multiplier, corner_multiplier


def policy_multiplier(own: np.ndarray, opp: np.ndarray, minute: int, subs: np.ndarray,
                      fixture: dict) -> np.ndarray:
    """Score-dependent tactical policy with stage-specific feedback strength."""
    policy = fixture.get("score_policy", {})
    start = float(policy.get("start_minute", 52))
    urgency = np.clip((minute - start) / max(95-start, 1), 0, 1)
    deficit = np.maximum(opp-own, 0)
    trailing_base = float(policy.get("trailing_boost", .30))
    multi_goal = float(policy.get("multi_goal_boost", .10))
    substitution = float(policy.get("substitution_boost", .025))
    leading_drag = float(policy.get("leading_drag", .17))
    trailing = 1 + urgency * (trailing_base + multi_goal*np.minimum(deficit-1, 1)) + substitution*subs
    leading = 1 - urgency*leading_drag
    return np.where(own < opp, trailing, np.where(own > opp, leading, 1.0))


def simulate(fixture: dict, cfg: dict, profiles: dict, rates: dict, dynamics: dict,
             rng: np.random.Generator, n: int, override: dict | None = None,
             keep_rows: bool = False) -> dict:
    override = override or {}
    home, away = fixture["home"], fixture["away"]
    rr = dict(rates)
    for key, value in fixture.get("central_rate_multipliers", {}).items():
        rr[key] *= value
    for key, value in override.get("rate_multipliers", {}).items():
        rr[key] *= value
    max_minute = 102
    curves = {}
    for metric in ("shots", "fouls", "yellow_cards", "red_cards", "penalties", "corners", "substitutions", "injuries"):
        base = normalized_minute_curve(dynamics, metric, 95)
        curves[metric] = np.r_[base, np.repeat(base[-1], max_minute-95)]
    regime, tempo, conversion, sot_multiplier, corner_multiplier = regime_draw(rng, fixture, n, override)
    physical = rng.lognormal(-.5*.18**2, .18, n)
    dead_ball_drag = np.exp(-.13*(physical-1))
    lineup_sigma = fixture["lineup_attack_sigma"]
    h_attack = rng.lognormal(-.5*lineup_sigma**2, lineup_sigma, n)
    a_attack = rng.lognormal(-.5*lineup_sigma**2, lineup_sigma, n)
    finishing_sigma = float(override.get("shared_finishing_sigma",
                                         fixture.get("shared_finishing_sigma", .08)))
    shared_finishing = rng.lognormal(-.5*finishing_sigma**2, finishing_sigma, n)
    weather = fixture["weather_shot_multiplier"]
    motivation = fixture["motivation_goal_multiplier"]

    hg = np.zeros(n, np.int8); ag = np.zeros(n, np.int8)
    h45 = np.zeros(n, np.int8); a45 = np.zeros(n, np.int8)
    hr = np.zeros(n, np.int8); ar = np.zeros(n, np.int8)
    hs = np.zeros(n, np.int8); ass = np.zeros(n, np.int8)
    hsot = np.zeros(n, np.int8); asot = np.zeros(n, np.int8)
    hf = np.zeros(n, np.int8); af = np.zeros(n, np.int8)
    hy = np.zeros(n, np.int8); ay = np.zeros(n, np.int8)
    hc = np.zeros(n, np.int8); ac = np.zeros(n, np.int8)
    hc45 = np.zeros(n, np.int8); ac45 = np.zeros(n, np.int8)
    hsub = np.zeros(n, np.int8); asub = np.zeros(n, np.int8)
    var_count = np.zeros(n, np.int8); injury_count = np.zeros(n, np.int8)
    first_side = np.zeros(n, np.int8); first_minute = np.zeros(n, np.int8)
    first_corner = np.zeros(n, np.int8)
    stoppage = np.full(n, 5, np.int8)

    h_open_xg = max(.12, rr["home_xg"] - .76*rr["home_penalties"])
    a_open_xg = max(.12, rr["away_xg"] - .76*rr["away_penalties"])
    hconv = np.clip(h_open_xg/max(rr["home_shots"], .1), .025, .24)
    aconv = np.clip(a_open_xg/max(rr["away_shots"], .1), .025, .24)
    rows: list[dict] = []
    for mi in range(max_minute):
        minute = mi + 1
        active = np.ones(n, bool) if minute <= 90 else minute <= 90 + stoppage
        late = np.clip((minute-65)/35, 0, 1)
        hfatigue = 1 - late*(1-fixture.get("home_late_fatigue_multiplier", fixture.get("late_fatigue_multiplier", 1.0)))
        afatigue = 1 - late*(1-fixture.get("away_late_fatigue_multiplier", fixture.get("late_fatigue_multiplier", 1.0)))
        hpolicy = policy_multiplier(hg, ag, minute, hsub, fixture)
        apolicy = policy_multiplier(ag, hg, minute, asub, fixture)
        hred = np.power(.66, hr)*np.power(1.30, ar)
        ared = np.power(.66, ar)*np.power(1.30, hr)
        hp = np.clip(rr["home_shots"]*curves["shots"][mi]*tempo*dead_ball_drag*weather*hfatigue*hpolicy*hred*h_attack, 0, .58)
        ap = np.clip(rr["away_shots"]*curves["shots"][mi]*tempo*dead_ball_drag*weather*afatigue*apolicy*ared*a_attack, 0, .58)
        hshot = active & (rng.random(n) < hp)
        ashot = active & (rng.random(n) < ap)
        hsot_evt = hshot & (rng.random(n) < np.clip(rr["home_sot_rate"]*sot_multiplier, .05, .75))
        asot_evt = ashot & (rng.random(n) < np.clip(rr["away_sot_rate"]*sot_multiplier, .05, .75))
        hxq = np.where(hg<ag, 1-.05*late, np.where(hg>ag, 1+.03*late, 1.0))
        axq = np.where(ag<hg, 1-.05*late, np.where(ag>hg, 1+.03*late, 1.0))
        hgoal = hshot & (rng.random(n) < np.clip(hconv*conversion*shared_finishing*motivation*hxq, .005, .38))
        agoal = ashot & (rng.random(n) < np.clip(aconv*conversion*shared_finishing*motivation*axq, .005, .38))
        hpen = active & (rng.random(n) < np.clip(rr["home_penalties"]*curves["penalties"][mi]*hpolicy, 0, .035))
        apen = active & (rng.random(n) < np.clip(rr["away_penalties"]*curves["penalties"][mi]*apolicy, 0, .035))
        hgoal |= hpen & (rng.random(n) < .79)
        agoal |= apen & (rng.random(n) < .78)
        hfp = np.clip(rr["home_fouls"]*curves["fouls"][mi]*physical, 0, .50)
        afp = np.clip(rr["away_fouls"]*curves["fouls"][mi]*physical, 0, .50)
        hfoul = active & (rng.random(n) < hfp); afoul = active & (rng.random(n) < afp)
        hy_evt = hfoul & (rng.random(n) < np.clip(rr["home_yellows"]*curves["yellow_cards"][mi]/max(hfp.mean(), 1e-5), 0, .72))
        ay_evt = afoul & (rng.random(n) < np.clip(rr["away_yellows"]*curves["yellow_cards"][mi]/max(afp.mean(), 1e-5), 0, .72))
        hr_evt = hfoul & (rng.random(n) < np.clip(rr["home_reds"]*curves["red_cards"][mi]/max(hfp.mean(), 1e-5), 0, .06))
        ar_evt = afoul & (rng.random(n) < np.clip(rr["away_reds"]*curves["red_cards"][mi]/max(afp.mean(), 1e-5), 0, .06))
        hcorner = active & (rng.random(n) < np.clip(rr["home_corners"]*curves["corners"][mi]*tempo*corner_multiplier*hpolicy, 0, .28))
        acorner = active & (rng.random(n) < np.clip(rr["away_corners"]*curves["corners"][mi]*tempo*corner_multiplier*apolicy, 0, .28))
        injury_base = dynamics["factors"]["base_rate_per_team_minute"]["injuries"]
        injury = active & (rng.random(n) < 2*injury_base*curves["injuries"][mi]*95*(1+.7*late))
        if minute >= 50:
            hp_sub = np.clip(5*curves["substitutions"][mi]*np.where(hg<ag, 1.15, 1.0), 0, .32)
            ap_sub = np.clip(5*curves["substitutions"][mi]*np.where(ag<hg, 1.15, 1.0), 0, .32)
            hsub_evt = active & (hsub<5) & (rng.random(n)<hp_sub)
            asub_evt = active & (asub<5) & (rng.random(n)<ap_sub)
        else:
            hsub_evt = np.zeros(n,bool); asub_evt = np.zeros(n,bool)
        review = active & ((hpen|apen)|(hgoal|agoal)&(rng.random(n)<.09)|(hr_evt|ar_evt)&(rng.random(n)<.70))
        new_goal = first_side == 0
        hfirst = new_goal & hgoal & ~agoal; afirst = new_goal & agoal & ~hgoal
        both = new_goal & hgoal & agoal; coin = rng.random(n)<.5
        hfirst |= both&coin; afirst |= both&~coin
        first_side[hfirst]=1; first_side[afirst]=2; first_minute[hfirst|afirst]=minute
        new_corner = first_corner == 0
        hfc = new_corner & hcorner & ~acorner; afc = new_corner & acorner & ~hcorner
        bothc = new_corner & hcorner & acorner; coinc = rng.random(n)<.5
        first_corner[hfc|(bothc&coinc)] = 1; first_corner[afc|(bothc&~coinc)] = 2
        hg += hgoal; ag += agoal; hr += hr_evt; ar += ar_evt
        hs += hshot; ass += ashot; hsot += hsot_evt|hpen; asot += asot_evt|apen
        hf += hfoul; af += afoul; hy += hy_evt; ay += ay_evt
        hc += hcorner; ac += acorner; hsub += hsub_evt; asub += asub_evt
        var_count += review; injury_count += injury
        if minute == 45:
            h45 = hg.copy(); a45 = ag.copy(); hc45 = hc.copy(); ac45 = ac.copy()
        if minute == 90:
            raw_stop = 2 + rng.poisson(1.3, n) + np.minimum(hg+ag, 4)//2 + np.minimum(hsub+asub, 10)//4 + np.minimum(var_count, 3) + np.minimum(injury_count, 2)
            stoppage = np.clip(raw_stop, 2, 12).astype(np.int8)
        if keep_rows:
            rows.append({
                "minute": minute if minute<=90 else f"90+{minute-90}",
                "p_active": float(active.mean()),
                "p_home_shot": float(hshot.mean()), "p_away_shot": float(ashot.mean()),
                "p_home_goal": float(hgoal.mean()), "p_away_goal": float(agoal.mean()),
                "p_home_foul": float(hfoul.mean()), "p_away_foul": float(afoul.mean()),
                "p_home_yellow": float(hy_evt.mean()), "p_away_yellow": float(ay_evt.mean()),
                "p_home_corner": float(hcorner.mean()), "p_away_corner": float(acorner.mean()),
                "p_home_leading_after": float((hg>ag).mean()), "p_draw_after": float((hg==ag).mean()),
                "p_away_leading_after": float((hg<ag).mean()),
                "p_scoreless_after": float(((hg+ag)==0).mean()),
                "p_btts_after": float(((hg>0)&(ag>0)).mean()),
                "expected_home_goals_after": float(hg.mean()), "expected_away_goals_after": float(ag.mean()),
            })
    total = hg+ag
    extra_time_goal_multiplier = float(fixture.get("extra_time_goal_multiplier", 1.05))
    et_h_lambda = rr["home_xg"]*30/95*extra_time_goal_multiplier
    et_a_lambda = rr["away_xg"]*30/95*extra_time_goal_multiplier
    draw_mask = hg==ag; ndraw = int(draw_mask.sum())
    eth = rng.poisson(et_h_lambda, ndraw); eta = rng.poisson(et_a_lambda, ndraw)
    et_tie = eth==eta
    pso = dynamics["extra_time_and_shootout"]
    pool = float(pso["shootout_conversion"])
    by_team = pso.get("shootout_by_team", {})
    raw_ph = float(by_team.get(home, {}).get("beta_binomial_posterior", pool))
    raw_pa = float(by_team.get(away, {}).get("beta_binomial_posterior", pool))
    # Historical World Cup shootout samples are tiny (for example Spain 8 kicks,
    # Argentina 9).  Re-shrink the published posterior toward the tournament
    # pool so that one shootout cannot dominate the advancement market.
    team_shootout_weight = float(fixture.get("team_shootout_weight", .45))
    ph = pool + team_shootout_weight*(raw_ph-pool)
    pa = pool + team_shootout_weight*(raw_pa-pool)
    shootout_home = (float(shootout_home_win(int(et_tie.sum()), ph, pa, rng).mean())
                     if et_tie.any() else .5)
    home_advance = float((hg>ag).mean()) + float(draw_mask.mean())*(float((eth>eta).mean()) + float(et_tie.mean())*shootout_home)
    return {
        "home": home, "away": away, "n": n, "regime": regime,
        "home_goals": hg, "away_goals": ag, "home_ht": h45, "away_ht": a45,
        "home_second": hg-h45, "away_second": ag-a45,
        "home_shots": hs, "away_shots": ass, "home_sot": hsot, "away_sot": asot,
        "home_fouls": hf, "away_fouls": af, "home_yellows": hy, "away_yellows": ay,
        "home_reds": hr, "away_reds": ar, "home_corners": hc, "away_corners": ac,
        "home_corners_ht": hc45, "away_corners_ht": ac45,
        "first_side": first_side, "first_minute": first_minute, "first_corner": first_corner,
        "stoppage": stoppage, "rows": rows,
        "home_advance": home_advance, "away_advance": 1-home_advance,
        "extra_time": float(draw_mask.mean()),
        "penalty_shootout": float(draw_mask.mean()*et_tie.mean()),
        "shootout_home_win": shootout_home, "shootout_conversion_home": ph,
        "shootout_conversion_away": pa,
        "core": {
            "home_win": float((hg>ag).mean()), "draw": float((hg==ag).mean()), "away_win": float((hg<ag).mean()),
            "home_xg": float(hg.mean()), "away_xg": float(ag.mean()),
            "over_1_5": float((total>1).mean()), "over_2_5": float((total>2).mean()),
            "over_3_5": float((total>3).mean()), "btts": float(((hg>0)&(ag>0)).mean()),
            "scorelines": score_distribution(hg, ag),
        },
    }


def line_from(text: str) -> float:
    matches = re.findall(r"(-?\d+(?:\.\d+)?)", text)
    if not matches:
        raise ValueError(text)
    return float(matches[-1])


def norm_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def poisson_tail(lam: float, threshold: int) -> float:
    """P[X >= threshold] for a Poisson variable, without a scipy dependency."""
    if threshold <= 0:
        return 1.0
    lam = max(0.0, float(lam))
    term = math.exp(-lam)
    cdf = term
    for k in range(1, threshold):
        term *= lam / k
        cdf += term
    return float(np.clip(1.0-cdf, 0.0, 1.0))


def attach_player_models(players: list[dict], sim: dict, rates: dict) -> None:
    """Attach appearance-mixture player prop inputs to a simulation result."""
    home, away = sim["home"], sim["away"]
    for team, side in ((home, "home"), (away, "away")):
        team_rows = [x for x in players if x["team"] == team]
        role_factor = {"GK": .15, "DEF": .72, "MID": .92, "FWD": 1.10}
        raw = [float(x["expected_shots"])*role_factor.get(x["role"], 1.0) for x in team_rows]
        target = float(sim[f"{side}_sot"].mean())
        scale = target/max(sum(raw), 1e-9)
        opp = "away" if side == "home" else "home"
        saves_if_starting = max(.05, float(sim[f"{opp}_sot"].mean())-float(sim[f"{opp}_goals"].mean()))
        for x, value in zip(team_rows, raw):
            x["expected_sot"] = value*scale
            x["conditional_goal_lambda"] = float(x["expected_goals"])/max(float(x["p_appearance"]), .02)
            x["conditional_shot_lambda"] = float(x["expected_shots"])/max(float(x["p_appearance"]), .02)
            x["conditional_sot_lambda"] = float(x["expected_sot"])/max(float(x["p_appearance"]), .02)
            assist_mean = -math.log(max(1e-9, 1-float(x["p_assist_90m"])))
            x["conditional_assist_lambda"] = assist_mean/max(float(x["p_appearance"]), .02)
            x["conditional_save_lambda"] = saves_if_starting if x["role"] == "GK" else 0.0
            x["expected_saves"] = float(x["p_appearance"])*x["conditional_save_lambda"]
    sim["player_models"] = {norm_text(x["player"]): x for x in players}


def player_prop_probability(row: dict, sim: dict) -> float | None:
    typ = row["sports_market_type"]
    if not typ.startswith("soccer_player_"):
        return None
    question = row["question"]
    match = re.search(r"^(.+?):\s*(\d+)\+", question)
    if not match:
        return None
    player = sim.get("player_models", {}).get(norm_text(match.group(1)))
    if player is None:
        return None
    threshold = int(match.group(2))
    appearance = float(np.clip(player["p_appearance"], 0, 1))
    if typ == "soccer_player_shots":
        lam = player["conditional_shot_lambda"]
    elif typ == "soccer_player_shots_on_target":
        lam = player["conditional_sot_lambda"]
    elif typ == "soccer_player_goals":
        lam = player["conditional_goal_lambda"]
    elif typ == "soccer_player_assists":
        lam = player["conditional_assist_lambda"]
    elif typ == "soccer_player_goals_plus_assists":
        lam = player["conditional_goal_lambda"]+player["conditional_assist_lambda"]
    elif typ == "soccer_player_goalkeeper_saves":
        lam = player["conditional_save_lambda"]
    else:
        return None
    return appearance*poisson_tail(lam, threshold)


def event_probability(row: dict, sim: dict, exact_listed: set[tuple[int,int]]) -> float | None:
    typ = row["sports_market_type"]
    title = row["group_item_title"]
    question = row["question"]
    home, away = sim["home"], sim["away"]
    h, a = sim["home_goals"], sim["away_goals"]
    if typ == "moneyline":
        if title == home: return float((h>a).mean())
        if title == away: return float((h<a).mean())
        return float((h==a).mean())
    if typ == "soccer_halftime_result":
        x, y = sim["home_ht"], sim["away_ht"]
        return float(((x>y) if title==home else (x<y) if title==away else (x==y)).mean())
    if typ == "soccer_second_half_result":
        x, y = sim["home_second"], sim["away_second"]
        return float(((x>y) if title==home else (x<y) if title==away else (x==y)).mean())
    if typ == "soccer_exact_score":
        if "Any Other" in title:
            return float(np.mean([pair not in exact_listed for pair in zip(h.tolist(), a.tolist())]))
        nums = re.findall(r"\d+", title)
        if len(nums) < 2: return None
        return float(((h==int(nums[-2]))&(a==int(nums[-1]))).mean())
    if typ == "soccer_first_to_score":
        if title == home: return float((sim["first_side"]==1).mean())
        if title == away: return float((sim["first_side"]==2).mean())
        return float((sim["first_side"]==0).mean())
    if typ == "spreads":
        handicap = line_from(title)
        team = row["outcome_0"]
        if team == home: return float((h+handicap>a).mean())
        return float((a+handicap>h).mean())
    if typ == "totals": return float(((h+a)>line_from(title)).mean())
    if typ == "soccer_team_to_advance": return sim["home_advance"] if row["outcome_0"]==home else sim["away_advance"]
    if typ == "soccer_extra_time": return sim["extra_time"]
    if typ == "soccer_penalty_shootout": return sim["penalty_shootout"]
    if typ == "soccer_team_totals":
        goals = h if home in title else a
        return float((goals>line_from(title)).mean())
    if typ == "soccer_first_half_team_totals":
        goals = sim["home_ht"] if home in title else sim["away_ht"]
        return float((goals>line_from(title)).mean())
    if typ == "soccer_second_half_team_totals":
        goals = sim["home_second"] if home in title else sim["away_second"]
        return float((goals>line_from(title)).mean())
    if typ == "first_half_totals":
        return float(((sim["home_ht"]+sim["away_ht"])>line_from(title)).mean())
    if typ == "second_half_totals":
        return float(((sim["home_second"]+sim["away_second"])>line_from(title)).mean())
    if typ == "both_teams_to_score": return float(((h>0)&(a>0)).mean())
    if typ == "both_teams_to_score_first_half":
        return float(((sim["home_ht"]>0)&(sim["away_ht"]>0)).mean())
    if typ == "both_teams_to_score_second_half":
        return float(((sim["home_second"]>0)&(sim["away_second"]>0)).mean())
    corners = sim["home_corners"]+sim["away_corners"]
    if typ == "total_corners": return float((corners>line_from(title)).mean())
    if typ == "soccer_first_half_total_corners":
        return float(((sim["home_corners_ht"]+sim["away_corners_ht"])>line_from(title)).mean())
    if typ == "soccer_second_half_total_corners":
        second = corners-sim["home_corners_ht"]-sim["away_corners_ht"]
        return float((second>line_from(title)).mean())
    if typ == "soccer_game_corners_odd_even": return float((corners%2==1).mean())
    if typ == "soccer_first_corner": return float((sim["first_corner"]==1).mean())
    if typ == "soccer_team_total_corners":
        team_corners = sim["home_corners"] if home in title else sim["away_corners"]
        return float((team_corners>line_from(title)).mean())
    player_probability = player_prop_probability(row, sim)
    if player_probability is not None:
        return player_probability
    return None


def exact_scores(rows: list[dict], fixture_id: str) -> set[tuple[int,int]]:
    out = set()
    for row in rows:
        if row["fixture_id"] != fixture_id or row["sports_market_type"] != "soccer_exact_score" or "Any Other" in row["group_item_title"]:
            continue
        nums = re.findall(r"\d+", row["group_item_title"])
        if len(nums)>=2: out.add((int(nums[-2]), int(nums[-1])))
    return out


def threshold_class(typ: str) -> tuple[float,float]:
    if typ in {"moneyline", "totals", "soccer_team_to_advance", "soccer_extra_time"}: return .025, .012
    if typ in {"soccer_halftime_result", "soccer_second_half_result", "soccer_first_to_score", "spreads"}: return .040, .018
    # v7's only executable third-place selection was a team-corner over and
    # failed despite an 84% model probability. Until a larger out-of-sample
    # corner audit is available, require an 8 pp robust edge and a 3.5 pp
    # model-risk buffer for the whole corner family.
    if "corner" in typ: return .080, .035
    if typ == "soccer_exact_score": return .065, .025
    if typ.startswith("soccer_player_"): return .120, .040
    return .080, .030


def external_side_probability(row: dict, side_index: int, guard: dict) -> float | None:
    """Map a listed outcome to an independent sharp-book fair probability."""
    typ = row["sports_market_type"]
    outcome = row[f"outcome_{side_index}"]
    if typ == "moneyline":
        base = guard.get("fair_1x2", {}).get(row["group_item_title"])
        if base is not None:
            return float(base) if side_index == 0 else 1-float(base)
    if typ == "soccer_team_to_advance":
        base = guard.get("fair_to_win", {}).get(outcome)
        if base is not None:
            return float(base)
    if typ == "totals":
        line = str(line_from(row["group_item_title"])).replace(".", "_")
        under = guard.get(f"under_{line}_fair")
        if under is not None:
            return (1-float(under)) if outcome == "Over" else float(under)
    if typ == "both_teams_to_score" and "btts_yes_fair" in guard:
        base = float(guard["btts_yes_fair"])
        return base if outcome == "Yes" else 1-base
    return None


def valuation(rows: list[dict], central: dict[str,dict], scenarios: dict[str,list[dict]],
              external_validation: dict) -> list[dict]:
    output = []
    for row in rows:
        fixture_id = row["fixture_id"]
        listed = exact_scores(rows, fixture_id)
        p0 = event_probability(row, central[fixture_id], listed)
        if p0 is None:
            output.append({**row, "side": "", "model_probability": "", "scenario_p10": "", "ask": "",
                           "robust_edge": "", "decision": "UNSUPPORTED_OR_LINEUP_FILTER", "max_entry": "", "stake_per_10k": 0})
            continue
        scen0 = [event_probability(row, sim, listed) for sim in scenarios[fixture_id]]
        candidates = []
        required, buffer = threshold_class(row["sports_market_type"])
        for idx, prob, scen in ((0, p0, scen0), (1, 1-p0, [1-x for x in scen0])):
            ask = row.get(f"outcome_{idx}_ask"); bid = row.get(f"outcome_{idx}_bid")
            if ask in (None, "") or bid in (None, ""): continue
            ask=float(ask); bid=float(bid); conservative=float(np.quantile(scen,.10))
            cost_fee=fee(ask,float(row.get("fee_rate") or .05))
            robust=conservative-ask-cost_fee-buffer
            candidates.append({"idx":idx,"side":row[f"outcome_{idx}"],"prob":prob,"p10":conservative,
                               "p90":float(np.quantile(scen,.90)),"ask":ask,"bid":bid,"fee":cost_fee,
                               "central_edge":prob-ask-cost_fee,"robust":robust,
                               "spread":ask-bid,"depth":float(row.get(f"outcome_{idx}_ask_depth_2c_usd") or 0)})
        if not candidates:
            output.append({**row, "side": "", "model_probability": round(p0, 6),
                           "scenario_p10": "", "scenario_p90": "", "ask": "", "bid": "",
                           "spread": "", "estimated_fee": "", "central_net_edge": "",
                           "robust_edge": "", "required_edge": required, "max_entry": "",
                           "depth_2c_usd": "", "external_probability": "",
                           "external_validation_source": "", "external_conflict_reason": "",
                           "lineup_pending_reason": "", "player_data_quality_reason": "",
                           "decision": "ONE_SIDED_OR_UNQUOTED_PASS", "stake_per_10k": 0})
            continue
        best=max(candidates,key=lambda x:x["robust"])
        volume=float(row.get("market_volume") or 0)
        tradable=best["spread"]<=.02+1e-10 and best["depth"]>=500 and volume>=500
        decision="BET_CANDIDATE" if best["robust"]>=required and tradable else "PASS"
        if decision=="PASS" and best["central_edge"]>.01: decision="WATCH"
        lineup_pending_reason=""
        player_data_quality_reason=""
        if row["sports_market_type"].startswith("soccer_player_"):
            player_name=row["question"].split(":",1)[0]
            player=central[fixture_id].get("player_models",{}).get(norm_text(player_name))
            if player is not None and float(player["p_appearance"])<.85:
                lineup_pending_reason=f"Projected appearance probability is only {float(player['p_appearance']):.1%}; wait for the official XI."
                if decision=="BET_CANDIDATE": decision="LINEUP_PENDING_PASS"
            if player is not None and float(player.get("tournament_minutes") or 0)<=0:
                player_data_quality_reason="No verified 2026 World Cup player-minute sample is available; the generic role prior is not sufficient for a bet."
                if decision in ("BET_CANDIDATE", "WATCH", "LINEUP_PENDING_PASS"):
                    decision="PLAYER_DATA_QUALITY_PASS"
        guard=external_validation.get(fixture_id,{})
        model_risk=(row["sports_market_type"] in guard.get("model_risk_groups",[]) or
                    row["question"] in guard.get("model_risk_questions",[]))
        model_risk_reason=""
        if decision=="BET_CANDIDATE" and model_risk:
            decision="MODEL_RISK_PASS"
            model_risk_reason=guard.get(
                "model_risk_reason",
                "The submodel is not sufficiently calibrated for execution.",
            )
        external_probability=external_side_probability(row,best["idx"],guard)
        divergent=(external_probability is not None and
                   abs(best["prob"]-external_probability)>=float(guard.get("guard_on_divergence_pp",1.0)))
        guarded=(guard.get("guard_all", False) or divergent or
                 row["sports_market_type"] in guard.get("guard_groups",[]) or
                 row["question"] in guard.get("guard_questions",[]))
        external_reason=""
        if decision=="BET_CANDIDATE" and guarded:
            decision="EXTERNAL_CONFLICT_PASS";external_reason=guard.get("reason","")
        feasible=[]
        rate=float(row.get("fee_rate") or .05)
        for q in np.arange(.001,.9991,.001):
            if best["p10"]-q-fee(q,rate)-buffer>=required: feasible.append(q)
        max_entry=max(feasible,default=0.0)
        b=max(1e-9,1-best["ask"]-best["fee"])
        kelly=max(0,best["robust"])/b
        cap=25 if "fra-eng" in fixture_id else 50
        stake=min(cap,10000*.125*kelly,best["depth"]*.005) if decision=="BET_CANDIDATE" else 0
        output.append({**row,"side":best["side"],"model_probability":round(best["prob"],6),
                       "scenario_p10":round(best["p10"],6),"scenario_p90":round(best["p90"],6),
                       "ask":best["ask"],"bid":best["bid"],"spread":round(best["spread"],6),
                       "estimated_fee":round(best["fee"],6),"central_net_edge":round(best["central_edge"],6),
                       "robust_edge":round(best["robust"],6),"required_edge":required,
                       "max_entry":round(max_entry,3),"depth_2c_usd":round(best["depth"],2),
                       "external_probability":round(external_probability,6) if external_probability is not None else "",
                       "external_validation_source":guard.get("source","") if guarded else "",
                        "external_conflict_reason":external_reason,
                        "model_risk_reason":model_risk_reason,
                        "lineup_pending_reason":lineup_pending_reason,
                        "player_data_quality_reason":player_data_quality_reason,
                        "decision":decision,"stake_per_10k":round(stake,2) if decision=="BET_CANDIDATE" else 0})
    for fixture_id in central:
        accepted=sorted([x for x in output if x["fixture_id"]==fixture_id and x["decision"]=="BET_CANDIDATE"],
                        key=lambda x:x["robust_edge"],reverse=True)
        if accepted:
            accepted[0]["decision"]="BET"
            for row in accepted[1:]: row["decision"]="CORRELATED_PASS"; row["stake_per_10k"]=0
    return output


def strict_arbitrage(rows: list[dict]) -> list[dict]:
    found=[]
    for row in rows:
        a0=row.get("outcome_0_ask");a1=row.get("outcome_1_ask")
        if a0 in (None,"") or a1 in (None,""):continue
        a0=float(a0);a1=float(a1);rate=float(row.get("fee_rate") or .05)
        cost=a0+a1+fee(a0,rate)+fee(a1,rate)
        if cost<1:found.append({"scope":row["market_id"],"legs":f"{row['outcome_0']} + {row['outcome_1']}","cost":cost,"locked_profit":1-cost})
    exhaustive={"moneyline":3,"soccer_halftime_result":3,"soccer_second_half_result":3,"soccer_exact_score":17,"soccer_first_to_score":3}
    groups={}
    for row in rows:
        typ=row["sports_market_type"]
        if typ in exhaustive:groups.setdefault((row["fixture_id"],row["event_slug"],typ),[]).append(row)
    for (fixture,slug,typ),group in groups.items():
        if len(group)!=exhaustive[typ]:continue
        if any(x.get("outcome_0_ask") in (None,"") for x in group):continue
        cost=sum(float(x["outcome_0_ask"])+fee(float(x["outcome_0_ask"]),float(x.get("fee_rate") or .05)) for x in group)
        if cost<1:found.append({"scope":slug,"legs":f"all {len(group)} mutually exclusive YES outcomes","cost":cost,"locked_profit":1-cost})
    return found


def csv_write(path: Path, rows: list[dict]) -> None:
    keys=[]
    for row in rows:
        for key in row:
            if key not in keys:keys.append(key)
    with path.open("w",encoding="utf-8-sig",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=keys,extrasaction="ignore");writer.writeheader();writer.writerows(rows)


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("--config",default="config/remaining_matches_v6.json")
    parser.add_argument("--output-dir",default="outputs/remaining_matches_v6");args=parser.parse_args()
    cfg=json.loads((ROOT/args.config).read_text(encoding="utf-8"));outdir=ROOT/args.output_dir;outdir.mkdir(parents=True,exist_ok=True)
    team_df=pd.read_csv(ROOT/cfg["data"]["fifa_team_features"]);player_df=pd.read_csv(ROOT/cfg["data"]["fifa_player_features"])
    history=pd.read_csv(ROOT/cfg["data"]["statsbomb_player_history"])
    dynamics=json.loads((ROOT/cfg["data"]["statsbomb_dynamics"]).read_text(encoding="utf-8"))
    lineup_payload=json.loads((ROOT/cfg["data"]["lineups"]).read_text(encoding="utf-8"))
    central={};scenario_runs={};summaries={};all_players=[]
    for idx,fixture in enumerate(cfg["fixtures"]):
        local={**cfg,"match":{**fixture,"regulation_modeled_minutes":95,"extra_time_minutes":30},
               "referee":fixture.get("referee",cfg["generic_referee_prior"]),"lineups":projected_lineups(lineup_payload,fixture["home"],fixture["away"])}
        model,hist_rows=fit_historical(local);profiles=derive_team_profiles(local,team_df,model)
        ref=referee_posterior(local,dynamics);rates=derive_event_rates(local,profiles,ref)
        base=simulate(fixture,cfg,profiles,rates,dynamics,np.random.default_rng(cfg["seed"]+idx),cfg["simulations"],keep_rows=True)
        specs=cfg.get("scenario_specs") or [
            {},
            {"rate_multipliers":{"home_xg":.90,"away_xg":.90,"home_shots":.92,"away_shots":.92},"regime_weights":{"cagey":.55,"normal":.35,"open":.10}},
            {"rate_multipliers":{"home_xg":1.10,"away_xg":1.10,"home_shots":1.08,"away_shots":1.08},"regime_weights":{"cagey":.10,"normal":.35,"open":.55}},
            {"rate_multipliers":{"home_xg":.93,"home_shots":.94}},
            {"rate_multipliers":{"away_xg":.93,"away_shots":.94}},
        ]
        scen=[simulate(fixture,cfg,profiles,rates,dynamics,np.random.default_rng(cfg["seed"]+100+idx*20+j),cfg["scenario_simulations"],ov) for j,ov in enumerate(specs)]
        central[fixture["fixture_id"]]=base;scenario_runs[fixture["fixture_id"]]=scen
        player_rates=dict(rates)
        player_rates["home_xg"]=base["core"]["home_xg"];player_rates["away_xg"]=base["core"]["away_xg"]
        player_rates["home_shots"]=float(base["home_shots"].mean());player_rates["away_shots"]=float(base["away_shots"].mean())
        players=build_player_table(local,player_df,history.copy(),player_rates,base)
        attach_player_models(players,base,player_rates);all_players.extend(players)
        for scenario in scen:
            scenario_rates=dict(rates)
            scenario_rates["home_xg"]=scenario["core"]["home_xg"];scenario_rates["away_xg"]=scenario["core"]["away_xg"]
            scenario_rates["home_shots"]=float(scenario["home_shots"].mean());scenario_rates["away_shots"]=float(scenario["away_shots"].mean())
            scenario_players=build_player_table(local,player_df,history.copy(),scenario_rates,scenario)
            attach_player_models(scenario_players,scenario,scenario_rates)
        csv_write(outdir/f"{fixture['fixture_id']}_minute_hazards.csv",base["rows"])
        summary={"fixture":fixture,"n":base["n"],"team_profiles":profiles,"rates":rates,"referee_prior":ref,
                 "core":base["core"],"progression":{"home":base["home_advance"],"away":base["away_advance"],"extra_time":base["extra_time"],"penalties":base["penalty_shootout"],
                 "shootout_home_win":base["shootout_home_win"],"shootout_conversion_home":base["shootout_conversion_home"],"shootout_conversion_away":base["shootout_conversion_away"]},
                 "means":{"home_shots":float(base["home_shots"].mean()),"away_shots":float(base["away_shots"].mean()),
                          "home_sot":float(base["home_sot"].mean()),"away_sot":float(base["away_sot"].mean()),
                          "home_fouls":float(base["home_fouls"].mean()),"away_fouls":float(base["away_fouls"].mean()),
                          "home_yellows":float(base["home_yellows"].mean()),"away_yellows":float(base["away_yellows"].mean()),
                          "home_corners":float(base["home_corners"].mean()),"away_corners":float(base["away_corners"].mean()),
                          "stoppage":float(base["stoppage"].mean())},
                 "first_goal":{"home":float((base["first_side"]==1).mean()),"away":float((base["first_side"]==2).mean()),"none":float((base["first_side"]==0).mean())},
                 "scenario_core":[x["core"] for x in scen],"historical_training_matches":len(hist_rows)}
        summaries[fixture["fixture_id"]]=summary
    pointer=(ROOT/cfg["data"]["polymarket_latest_pointer"]).read_text(encoding="utf-8").strip();snapshot=ROOT/pointer
    with snapshot.open(encoding="utf-8-sig",newline="") as handle:market_rows=list(csv.DictReader(handle))
    # A final-only run may point at a snapshot created by an earlier multi-fixture
    # collector.  Valuation must never attempt to join a settled fixture that is
    # absent from this run's frozen probability output.
    market_rows=[row for row in market_rows if row["fixture_id"] in central]
    recommendations=valuation(market_rows,central,scenario_runs,cfg.get("external_validation",{}));arbs=strict_arbitrage(market_rows)
    csv_write(outdir/"polymarket_recommendations.csv",recommendations);csv_write(outdir/"player_probabilities.csv",all_players)
    version=cfg.get("model_version","v7")
    method=f"real-data latent-regime minute simulation {version}; Polymarket excluded from probability engine; sharp books used only as a post-model conflict gate"
    payload={"generated_from_snapshot":pointer,"cutoff_utc":cfg["cutoff_utc"],"method":method,
             "summaries":summaries,"strict_arbitrage":arbs,"external_validation":cfg.get("external_validation",{}),
             "bets":[x for x in recommendations if x["decision"]=="BET"],
             "model_risk_passes":[x for x in recommendations if x["decision"]=="MODEL_RISK_PASS"],
             "model_external_conflicts":[x for x in recommendations if x["decision"]=="EXTERNAL_CONFLICT_PASS"],
             "watch":[x for x in recommendations if x["decision"]=="WATCH"][:20]}
    (outdir/"summary.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    report=[f"# 世界杯决赛：真实数据状态切换模型 {version}","",f"数据截点：{cfg['cutoff_utc']}；盘口快照：`{pointer}`。概率引擎未读取 Polymarket；外部体育书只用于事后冲突风控。",""]
    for fixture in cfg["fixtures"]:
        fid=fixture["fixture_id"];s=summaries[fid];c=s["core"];p=s["progression"];m=s["means"]
        report += [f"## {fixture['home']}—{fixture['away']}","",f"90分钟：{fixture['home']} {c['home_win']:.2%} / 平 {c['draw']:.2%} / {fixture['away']} {c['away_win']:.2%}；最终胜出 {p['home']:.2%}/{p['away']:.2%}。",
                   f"期望进球 {c['home_xg']:.2f}–{c['away_xg']:.2f}；大2.5 {c['over_2_5']:.2%}；BTTS {c['btts']:.2%}；平均补时 {m['stoppage']:.1f}分钟。","",
                   "| 最可能比分 | 概率 |","|---|---:|"]+[f"| {x['score']} | {x['probability']:.2%} |" for x in c["scorelines"][:8]]+["",f"射门 {m['home_shots']:.1f}–{m['away_shots']:.1f}，射正 {m['home_sot']:.1f}–{m['away_sot']:.1f}，角球 {m['home_corners']:.1f}–{m['away_corners']:.1f}，犯规 {m['home_fouls']:.1f}–{m['away_fouls']:.1f}。",""]
    report += ["## 严格套利扫描",""]
    if arbs:
        for x in arbs:report.append(f"- {x['scope']}：总成本 {x['cost']:.3%}，锁定毛利 {x['locked_profit']:.3%}。")
    else:report.append("未发现计入 taker fee 后、同时吃单即可锁定正收益的严格套利组合。")
    report += ["","## 可执行建议","","| 比赛 | 合约 | 方向 | 模型 | 情景P10 | 买价 | 稳健边际 | 上限价 | $10k示例仓位 |","|---|---|---|---:|---:|---:|---:|---:|---:|"]
    bets=[x for x in recommendations if x["decision"]=="BET"]
    if bets:
        for x in bets:report.append(f"| {x['fixture_id']} | {x['question']} | {x['side']} | {x['model_probability']:.2%} | {x['scenario_p10']:.2%} | {x['ask']:.2%} | {x['robust_edge']:+.2%} | {x['max_entry']:.2%} | ${x['stake_per_10k']:.0f} |")
    else:report.append("| — | 当前没有通过模型情景、费用、流动性和相关性过滤的吃单 | — | — | — | — | — | — | $0 |")
    conflicts=[x for x in recommendations if x["decision"]=="EXTERNAL_CONFLICT_PASS"]
    report += ["","## 模型分歧观察项（不执行）",""]
    for x in conflicts:
        report.append(f"- {x['question']} {x['side']}：模型 {x['model_probability']:.2%}，情景P10 {x['scenario_p10']:.2%}，现价 {x['ask']:.2%}；因外部基准显著冲突，降级为不下注。")
    report += ["","## 重要限制","","- 季军赛经验只用于修正阶段方差、状态反馈和风控，不直接抬高决赛的中央进球率。","- 球员盘口采用出场概率与条件 Poisson 混合分布；正式首发公布后必须重跑，未进首发的球员信号不得提前当作确定性优势。","- 精确分钟为危险率，不是确定性事件预告；严格套利与模型价值下注是两种不同概念。"]
    (outdir/"prediction_and_betting_report.md").write_text("\n".join(report),encoding="utf-8")
    print(json.dumps({"output":str(outdir),"bets":len(bets),"strict_arbitrage":len(arbs),"snapshot":pointer},ensure_ascii=False))


if __name__=="__main__":main()
