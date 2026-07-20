from __future__ import annotations

import argparse
import copy
import csv
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from wc_model.game_attributes import team_profile


ROOT = Path(__file__).resolve().parents[1]


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def minute_tempo(minute: int, regulation_minutes: int = 95) -> float:
    if minute <= 10:
        return 0.86
    if minute <= 25:
        return 0.96
    if minute <= 40:
        return 1.03
    if minute <= 50:
        return 1.09
    if minute <= 65:
        return 1.01
    if minute <= 75:
        return 1.08
    if minute <= 90:
        return 1.22
    return 1.34


def minute_label(minute: int) -> str:
    return str(minute) if minute <= 90 else f"90+{minute-90}"


def positional_means(players: list[dict]) -> dict:
    out = {}
    for role in ("GK", "DEF", "MID", "FWD"):
        group = [p for p in players if p["role"] == role]
        out[role] = {
            key: float(np.mean([p[key] for p in group]))
            for key in ("ovr", "pac", "sho", "pas", "dri", "def", "phy")
        }
    return out


def derive_team_engine(team: str, opponent: str, ratings: dict, cfg: dict) -> dict:
    players = ratings["teams"][team]["players"]
    bench = ratings["teams"][team].get("bench", [])
    opp_players = ratings["teams"][opponent]["players"]
    profile = team_profile(players)
    roles = positional_means(players)
    opp_roles = positional_means(opp_players)
    tcfg = cfg["teams"][team]
    ocfg = cfg["teams"][opponent]

    forward_finishing = roles["FWD"]["sho"]
    midfield_creation = .55*roles["MID"]["pas"] + .45*roles["MID"]["dri"]
    wide_threat = .55*roles["FWD"]["pac"] + .45*roles["FWD"]["dri"]
    opponent_wide_defense = .55*opp_roles["DEF"]["def"] + .25*opp_roles["DEF"]["pac"] + .20*opp_roles["DEF"]["phy"]
    central_edge = midfield_creation - (.65*opp_roles["MID"]["def"] + .35*opp_roles["MID"]["phy"])
    wide_edge = wide_threat - opponent_wide_defense
    form_rate = tcfg["tournament_regulation_goals_for"] / tcfg["tournament_matches"]
    form_multiplier = (form_rate / 1.55) ** 0.12
    creation = (0.48*profile["attack"] + 0.25*profile["control"] +
                0.14*wide_edge + 0.13*central_edge)
    tactical_multiplier = (tcfg["width_multiplier"] ** .55 *
                           tcfg["central_progression_multiplier"] ** .45)
    defensive_resistance = (0.70*profile["defense"] + 0.20*roles["GK"]["ovr"] +
                            0.10*profile["physical"])
    return {
        "team": team, "players": players, "bench": bench, "profile": profile, "roles": roles,
        "creation": creation, "defensive_resistance": defensive_resistance,
        "forward_finishing": forward_finishing, "goalkeeper": roles["GK"]["ovr"],
        "tactical_multiplier": tactical_multiplier,
        "form_multiplier": form_multiplier,
        "fitness_multiplier": tcfg["fitness_multiplier"],
        "pressing_multiplier": tcfg["pressing_multiplier"],
        "set_piece_multiplier": tcfg["set_piece_multiplier"],
        "bench_quality": float(np.mean([p["ovr"] for p in bench])) if bench else tcfg["bench_quality"],
        "possession_bias": tcfg["possession_bias"],
        "wide_edge": wide_edge, "central_edge": central_edge,
    }


def derive_match_rates(home: dict, away: dict, cfg: dict) -> dict:
    env = cfg["universal_event_environment"]
    match = cfg["match"]
    home_power = home["creation"] - .52*away["defensive_resistance"]
    away_power = away["creation"] - .52*home["defensive_resistance"]
    share_home = logistic((home_power-away_power)/7.5 + math.log(home["tactical_multiplier"]/away["tactical_multiplier"]))
    total_shots = (env["shots_per_match"] * match["pitch_speed_multiplier"] *
                   math.sqrt(home["form_multiplier"]*away["form_multiplier"]))
    shots_home = total_shots * share_home * home["form_multiplier"]
    shots_away = total_shots * (1-share_home) * away["form_multiplier"]

    sot_home = np.clip(env["shot_on_target_base"] * math.exp((home["forward_finishing"]-83)/90), .30, .43)
    sot_away = np.clip(env["shot_on_target_base"] * math.exp((away["forward_finishing"]-83)/90), .30, .43)
    conv_home = np.clip(env["goal_per_shot_on_target_base"] * math.exp(
        (home["forward_finishing"]-84)*.014 - (away["goalkeeper"]-84)*.012), .21, .36)
    conv_away = np.clip(env["goal_per_shot_on_target_base"] * math.exp(
        (away["forward_finishing"]-84)*.014 - (home["goalkeeper"]-84)*.012), .21, .36)
    conv_home *= match["semi_final_caution_multiplier"]
    conv_away *= match["semi_final_caution_multiplier"]

    possession_home = logistic((home["profile"]["control"]-away["profile"]["control"])/9 +
                               home["possession_bias"]-away["possession_bias"])
    foul_share_home = home["pressing_multiplier"] / (home["pressing_multiplier"]+away["pressing_multiplier"])
    penalty_share_home = logistic((home_power-away_power)/9)
    return {
        "shots_home": float(shots_home), "shots_away": float(shots_away),
        "sot_rate_home": float(sot_home), "sot_rate_away": float(sot_away),
        "sot_conversion_home": float(conv_home), "sot_conversion_away": float(conv_away),
        "possession_home": float(possession_home), "foul_share_home": float(foul_share_home),
        "penalty_share_home": float(penalty_share_home),
    }


def score_state_multiplier(own: np.ndarray, opp: np.ndarray, minute: int, end: int) -> np.ndarray:
    urgency = (minute/end) ** 1.7
    diff = own-opp
    out = np.ones_like(own, dtype=float)
    out[diff < 0] *= 1 + .18*urgency
    out[diff > 0] *= 1 - .09*urgency
    out[diff <= -2] *= 1 + .09*urgency
    out[diff >= 2] *= 1 - .08*urgency
    return out


def fatigue_multiplier(engine: dict, minute: int, fitness_override: float = 1.0) -> float:
    if minute <= 55:
        return engine["fitness_multiplier"] * fitness_override
    physical = engine["profile"]["physical"]
    decline = max(0.0, 78.0-physical) * .0025 * ((minute-55)/40)
    return engine["fitness_multiplier"] * fitness_override * (1-decline)


def most_likely_score(home: np.ndarray, away: np.ndarray) -> str:
    code = np.minimum(home, 9)*10 + np.minimum(away, 9)
    value = int(np.bincount(code, minlength=100).argmax())
    return f"{value//10}-{value%10}"


def simulate_regulation(home: dict, away: dict, rates: dict, cfg: dict, rng: np.random.Generator) -> dict:
    n = int(cfg["simulations"]); minutes = int(cfg["match"]["regulation_modeled_minutes"])
    env, ref = cfg["universal_event_environment"], cfg["referee"]
    hg = np.zeros(n, dtype=np.int8); ag = np.zeros(n, dtype=np.int8)
    hr = np.zeros(n, dtype=np.int8); ar = np.zeros(n, dtype=np.int8)
    hs = np.zeros(n, dtype=np.int8); ass = np.zeros(n, dtype=np.int8)
    hy = np.zeros(n, dtype=np.int8); ay = np.zeros(n, dtype=np.int8)
    hsubs = np.zeros(n, dtype=np.int8); asubs = np.zeros(n, dtype=np.int8)
    first_side = np.zeros(n, dtype=np.int8); first_minute = np.zeros(n, dtype=np.int8)
    rows = []

    tempo_norm = sum(minute_tempo(m, minutes) for m in range(1, minutes+1))
    base_h_shot = rates["shots_home"] / tempo_norm
    base_a_shot = rates["shots_away"] / tempo_norm
    foul_h = env["fouls_per_match"]*rates["foul_share_home"] / minutes
    foul_a = env["fouls_per_match"]*(1-rates["foul_share_home"]) / minutes
    pen_h = ref["penalties_per_match_bayesian"]*rates["penalty_share_home"] / minutes
    pen_a = ref["penalties_per_match_bayesian"]*(1-rates["penalty_share_home"]) / minutes
    total_events = Counter()

    for minute in range(1, minutes+1):
        tempo = minute_tempo(minute, minutes)
        h_state = score_state_multiplier(hg, ag, minute, minutes)
        a_state = score_state_multiplier(ag, hg, minute, minutes)
        h_red_effect = np.power(.73, hr) * np.power(1.14, ar)
        a_red_effect = np.power(.73, ar) * np.power(1.14, hr)
        h_sub_quality = np.exp((home["bench_quality"]-home["profile"]["starting_xi_ovr"])/120*hsubs/5)
        a_sub_quality = np.exp((away["bench_quality"]-away["profile"]["starting_xi_ovr"])/120*asubs/5)
        h_fatigue = fatigue_multiplier(home, minute) * (1+.008*hsubs) * h_sub_quality
        a_fatigue = fatigue_multiplier(away, minute) * (1+.008*asubs) * a_sub_quality
        h_shot_p = np.clip(base_h_shot*tempo*h_state*h_red_effect*h_fatigue, 0, .55)
        a_shot_p = np.clip(base_a_shot*tempo*a_state*a_red_effect*a_fatigue, 0, .55)
        hshot = rng.random(n) < h_shot_p; ashot = rng.random(n) < a_shot_p
        hsot = hshot & (rng.random(n) < rates["sot_rate_home"])
        asot = ashot & (rng.random(n) < rates["sot_rate_away"])
        hconv = np.clip(rates["sot_conversion_home"]*(1+.05*(1-a_fatigue)), .15, .45)
        aconv = np.clip(rates["sot_conversion_away"]*(1+.05*(1-h_fatigue)), .15, .45)
        hgoal_open = hsot & (rng.random(n) < hconv)
        agoal_open = asot & (rng.random(n) < aconv)

        hpen = rng.random(n) < np.clip(pen_h*tempo*h_state, 0, .025)
        apen = rng.random(n) < np.clip(pen_a*tempo*a_state, 0, .025)
        hpen_conv = np.clip(.76 + (home["forward_finishing"]-82)*.008 - (away["goalkeeper"]-84)*.006, .62, .88)
        apen_conv = np.clip(.74 + (away["forward_finishing"]-82)*.008 - (home["goalkeeper"]-84)*.006, .60, .86)
        hgoal_pen = hpen & (rng.random(n) < hpen_conv)
        agoal_pen = apen & (rng.random(n) < apen_conv)
        hgoal = hgoal_open.astype(np.int8)+hgoal_pen.astype(np.int8)
        agoal = agoal_open.astype(np.int8)+agoal_pen.astype(np.int8)

        hfoul = rng.random(n) < np.clip(foul_h*tempo*(1+.08*(1-h_fatigue)), 0, .4)
        afoul = rng.random(n) < np.clip(foul_a*tempo*(1+.08*(1-a_fatigue)), 0, .4)
        hyellow = hfoul & (rng.random(n) < ref["yellow_per_foul"])
        ayellow = afoul & (rng.random(n) < ref["yellow_per_foul"])
        hred = hfoul & (rng.random(n) < ref["red_per_foul"])
        ared = afoul & (rng.random(n) < ref["red_per_foul"])
        hcorner = hshot & ~hgoal_open & (rng.random(n) < env["corners_per_non_goal_shot"]*home["set_piece_multiplier"])
        acorner = ashot & ~agoal_open & (rng.random(n) < env["corners_per_non_goal_shot"]*away["set_piece_multiplier"])
        hinjury = rng.random(n) < env["injuries_per_team_match"]/minutes*(1+.8*max(0, minute-65)/30)
        ainjury = rng.random(n) < env["injuries_per_team_match"]/minutes*(1+.8*max(0, minute-65)/30)

        if 55 <= minute <= 88:
            sub_curve = .025 + .105*math.exp(-((minute-70)/9)**2) + .085*math.exp(-((minute-82)/5)**2)
            hsub = (hsubs < 5) & (rng.random(n) < sub_curve*(1+.25*(hg<ag)))
            asub = (asubs < 5) & (rng.random(n) < sub_curve*(1+.25*(ag<hg)))
        else:
            hsub = np.zeros(n, dtype=bool); asub = np.zeros(n, dtype=bool)
        hsub |= hinjury & (hsubs < 5); asub |= ainjury & (asubs < 5)

        var = ((hpen|apen) & (rng.random(n) < env["var_review_given_penalty"]))
        var |= ((hgoal>0)|(agoal>0)) & (rng.random(n) < env["var_review_given_goal"])
        var |= (hred|ared) & (rng.random(n) < env["var_review_given_red"])

        new_first = first_side == 0
        h_first = new_first & (hgoal>0) & (agoal==0)
        a_first = new_first & (agoal>0) & (hgoal==0)
        both_first = new_first & (hgoal>0) & (agoal>0)
        if both_first.any():
            choose_h = rng.random(n) < .5
            h_first |= both_first & choose_h; a_first |= both_first & ~choose_h
        first_side[h_first] = 1; first_side[a_first] = 2
        first_minute[h_first|a_first] = minute

        hg += hgoal; ag += agoal; hr += hred; ar += ared
        hs += hshot.astype(np.int8)+hpen.astype(np.int8); ass += ashot.astype(np.int8)+apen.astype(np.int8)
        hy += hyellow; ay += ayellow; hsubs += hsub; asubs += asub

        poss_state = rates["possession_home"] + .035*(hg<ag) - .035*(hg>ag) - .065*hr + .065*ar
        poss_state = np.clip(poss_state, .27, .73)
        row = {
            "minute": minute_label(minute),
            "p_home_shot": float(np.mean(hshot|hpen)), "p_away_shot": float(np.mean(ashot|apen)),
            "p_home_sot": float(np.mean(hsot|hpen)), "p_away_sot": float(np.mean(asot|apen)),
            "p_home_goal": float(np.mean(hgoal>0)), "p_away_goal": float(np.mean(agoal>0)),
            "p_home_foul": float(np.mean(hfoul)), "p_away_foul": float(np.mean(afoul)),
            "p_home_yellow": float(np.mean(hyellow)), "p_away_yellow": float(np.mean(ayellow)),
            "p_home_red": float(np.mean(hred)), "p_away_red": float(np.mean(ared)),
            "p_home_penalty": float(np.mean(hpen)), "p_away_penalty": float(np.mean(apen)),
            "p_home_corner": float(np.mean(hcorner)), "p_away_corner": float(np.mean(acorner)),
            "p_var_review": float(np.mean(var)), "p_any_injury": float(np.mean(hinjury|ainjury)),
            "p_any_substitution": float(np.mean(hsub|asub)),
            "expected_home_possession": float(np.mean(poss_state)),
            "p_home_leading_after": float(np.mean(hg>ag)), "p_draw_after": float(np.mean(hg==ag)),
            "p_away_leading_after": float(np.mean(hg<ag)),
            "expected_score_home_after": float(np.mean(hg)), "expected_score_away_after": float(np.mean(ag)),
            "most_likely_score_after": most_likely_score(hg, ag),
        }
        rows.append(row)
        for key, arr in (("home_shots", hshot|hpen), ("away_shots", ashot|apen),
                         ("home_sot", hsot|hpen), ("away_sot", asot|apen),
                         ("home_goals", hgoal), ("away_goals", agoal),
                         ("home_fouls", hfoul), ("away_fouls", afoul),
                         ("home_yellows", hyellow), ("away_yellows", ayellow),
                         ("home_reds", hred), ("away_reds", ared),
                         ("home_penalties", hpen), ("away_penalties", apen),
                         ("home_corners", hcorner), ("away_corners", acorner),
                         ("var_reviews", var), ("injuries", hinjury|ainjury),
                         ("substitutions", hsub.astype(np.int8)+asub.astype(np.int8))):
            total_events[key] += float(np.sum(arr))

    return {"rows": rows, "home_goals": hg, "away_goals": ag, "home_reds": hr, "away_reds": ar,
            "home_shots": hs, "away_shots": ass, "home_yellows": hy, "away_yellows": ay,
            "home_subs": hsubs, "away_subs": asubs, "first_side": first_side,
            "first_minute": first_minute,
            "event_means": {k: v/n for k, v in total_events.items()}}


def simulate_extra_time(reg: dict, home: dict, away: dict, rates: dict, cfg: dict,
                        rng: np.random.Generator) -> dict:
    mask = reg["home_goals"] == reg["away_goals"]
    n = int(mask.sum()); minutes = int(cfg["match"]["extra_time_minutes"])
    hg = np.zeros(n, dtype=np.int8); ag = np.zeros(n, dtype=np.int8)
    hr = reg["home_reds"][mask].copy(); ar = reg["away_reds"][mask].copy()
    rows = []
    tempo_weights = np.array([.82 if m <= 15 else .94 for m in range(1, minutes+1)])
    for m in range(1, minutes+1):
        absolute = 95+m
        urgency = 1.0 if m <= 15 else 1.10
        h_state = score_state_multiplier(hg, ag, m, minutes)
        a_state = score_state_multiplier(ag, hg, m, minutes)
        hp = rates["shots_home"]/95*tempo_weights[m-1]*urgency*h_state*np.power(.73, hr)*np.power(1.14, ar)
        ap = rates["shots_away"]/95*tempo_weights[m-1]*urgency*a_state*np.power(.73, ar)*np.power(1.14, hr)
        hshot = rng.random(n) < np.clip(hp, 0, .5); ashot = rng.random(n) < np.clip(ap, 0, .5)
        hsot = hshot & (rng.random(n) < rates["sot_rate_home"]*.97)
        asot = ashot & (rng.random(n) < rates["sot_rate_away"]*.97)
        hgoal = hsot & (rng.random(n) < rates["sot_conversion_home"]*.96)
        agoal = asot & (rng.random(n) < rates["sot_conversion_away"]*.96)
        hg += hgoal; ag += agoal
        rows.append({
            "minute": str(90+m), "conditional_on_extra_time": True,
            "p_home_shot": float(np.mean(hshot)), "p_away_shot": float(np.mean(ashot)),
            "p_home_sot": float(np.mean(hsot)), "p_away_sot": float(np.mean(asot)),
            "p_home_goal": float(np.mean(hgoal)), "p_away_goal": float(np.mean(agoal)),
            "p_home_leading_after_et_minute": float(np.mean(hg>ag)),
            "p_et_still_tied_after_minute": float(np.mean(hg==ag)),
            "p_away_leading_after_et_minute": float(np.mean(hg<ag)),
        })
    return {"reached": n, "rows": rows, "home_goals": hg, "away_goals": ag}


def penalty_skill(players: list[dict], opposing_gk: float) -> float:
    candidates = sorted([p for p in players if p["role"] != "GK"],
                        key=lambda p: .65*p["sho"]+.20*p["ovr"]+.15*p["pas"], reverse=True)[:5]
    quality = np.mean([.65*p["sho"]+.20*p["ovr"]+.15*p["pas"] for p in candidates])
    return float(np.clip(.74+(quality-82)*.008-(opposing_gk-84)*.006, .62, .88))


def simulate_shootout(n: int, p_home: float, p_away: float, rng: np.random.Generator) -> np.ndarray:
    home = rng.binomial(5, p_home, n); away = rng.binomial(5, p_away, n)
    decided = home != away; home_win = home > away
    for _ in range(12):
        pending = ~decided
        if not pending.any():
            break
        h = rng.random(n) < p_home; a = rng.random(n) < p_away
        new = pending & (h != a)
        home_win[new] = h[new]
        decided[new] = True
    home_win[~decided] = rng.random((~decided).sum()) < .5
    return home_win


def score_distribution(home: np.ndarray, away: np.ndarray, limit: int = 15) -> list[dict]:
    counts = Counter(zip(home.tolist(), away.tolist()))
    n = len(home)
    return [{"score": f"{h}-{a}", "probability": c/n} for (h, a), c in counts.most_common(limit)]


def player_event_table(team: dict, opponent: dict, reg: dict, side: str, cfg: dict) -> list[dict]:
    players = team["players"]; form = cfg["player_form_goals"]
    role_shot = {"GK": .01, "DEF": .55, "MID": 1.45, "FWD": 3.20}
    shot_weights = np.array([role_shot[p["role"]]*math.exp((p["sho"]-75)/18)*
                             (1+.035*form.get(p["name"], 0)) for p in players])
    goal_weights = np.array([role_shot[p["role"]]*math.exp((p["sho"]-76)/13)*
                             (1+.07*form.get(p["name"], 0)) for p in players])
    assist_weights = np.array([(.15 if p["role"] == "GK" else 1.0)*
                               math.exp((.55*p["pas"]+.45*p["dri"]-76)/15) for p in players])
    card_weights = np.array([(.2 if p["role"] == "GK" else 1.0)*
                             math.exp((p["def"]+p["phy"]-145)/35) for p in players])
    shot_weights /= shot_weights.sum(); goal_weights /= goal_weights.sum()
    assist_weights /= assist_weights.sum(); card_weights /= card_weights.sum()
    goals = reg[f"{side}_goals"]; shots = reg[f"{side}_shots"]; yellows = reg[f"{side}_yellows"]
    first_team = 1 if side == "home" else 2
    p_team_first = float(np.mean(reg["first_side"] == first_team))
    out = []
    for i, p in enumerate(players):
        anytime = float(np.mean(1-np.power(1-goal_weights[i], goals)))
        first = p_team_first*goal_weights[i]
        assist = float(np.mean(1-np.power(1-.72*assist_weights[i], goals)))
        card = float(np.mean(1-np.power(1-card_weights[i], yellows)))
        sub_base = {"GK": .01, "DEF": .20, "MID": .42, "FWD": .48}[p["role"]]
        importance = np.clip((p["ovr"]-78)*.025, 0, .22)
        availability = p.get("availability", 1.0)
        p_sub = float(np.clip(sub_base-importance+(1-availability)*1.2, .01, .72))
        out.append({
            "team": team["team"], "player": p["name"], "role": p["role"], "squad_status": "starter",
            "fc26_ovr": p["ovr"], "p_appearance": 1.0,
            "expected_shots": float(np.mean(shots)*shot_weights[i]),
            "p_anytime_goal_90m": anytime, "p_first_goal": first,
            "p_assist_90m": assist, "p_yellow_90m": card, "p_substituted": p_sub,
        })
    return sorted(out, key=lambda x: x["p_anytime_goal_90m"], reverse=True)


def bench_event_table(team: dict, reg: dict, side: str) -> list[dict]:
    bench = team.get("bench", [])
    if not bench:
        return []
    subs = reg[f"{side}_subs"]
    role_weight = {"GK": .03, "DEF": .70, "MID": 1.15, "FWD": 1.35}
    weights = np.array([role_weight[p["role"]]*math.exp((p["ovr"]-80)/18) for p in bench])
    weights /= weights.sum()
    out = []
    for i, p in enumerate(bench):
        appearance = float(np.mean(1-np.power(1-weights[i], subs)))
        expected_minutes = appearance*(17 + 4*(p["role"] in ("MID", "FWD")))
        shot_rate = {"GK": .01, "DEF": .45, "MID": 1.25, "FWD": 2.65}[p["role"]]/90
        exp_shots = expected_minutes*shot_rate*math.exp((p["sho"]-75)/22)
        goal_chance = appearance*(1-math.exp(-exp_shots*.35*np.clip(.26+(p["sho"]-80)*.006, .18, .38)))
        assist_chance = appearance*(1-math.exp(-expected_minutes/90*math.exp((p["pas"]-78)/20)*.16))
        out.append({
            "team": team["team"], "player": p["name"], "role": p["role"], "squad_status": "bench",
            "fc26_ovr": p["ovr"], "p_appearance": appearance,
            "expected_shots": exp_shots, "p_anytime_goal_90m": goal_chance,
            "p_first_goal": goal_chance*.28, "p_assist_90m": assist_chance,
            "p_yellow_90m": appearance*.035*(1+.02*max(0, p["def"]-75)),
            "p_substituted": 0.0,
        })
    return sorted(out, key=lambda x: x["p_appearance"], reverse=True)


def binomial_ci(p: float, n: int) -> list[float]:
    half = 1.96*math.sqrt(max(1e-12, p*(1-p)/n))
    return [max(0.0, p-half), min(1.0, p+half)]


def run_sensitivity(home: dict, away: dict, rates: dict, cfg: dict) -> list[dict]:
    scenarios = [
        ("低节奏谨慎半决赛", {"shots": .88, "conv": .95, "home_shots": 1.0, "away_shots": 1.0}),
        ("开放式攻防转换", {"shots": 1.12, "conv": 1.04, "home_shots": 1.0, "away_shots": 1.0}),
        ("Rice状态受限", {"shots": 1.0, "conv": 1.0, "home_shots": .96, "away_shots": 1.03}),
        ("阿根廷切换4-3-3", {"shots": 1.0, "conv": 1.0, "home_shots": 1.02, "away_shots": 1.05}),
        ("低点球/低红牌裁判实现", {"shots": 1.0, "conv": 1.0, "home_shots": 1.0, "away_shots": 1.0}),
    ]
    out = []
    for idx, (name, mult) in enumerate(scenarios):
        local_cfg = copy.deepcopy(cfg)
        local_cfg["simulations"] = 40000
        if name == "低点球/低红牌裁判实现":
            local_cfg["referee"]["penalties_per_match_bayesian"] = .22
            local_cfg["referee"]["red_per_foul"] = .005
        local_rates = dict(rates)
        local_rates["shots_home"] *= mult["shots"]*mult["home_shots"]
        local_rates["shots_away"] *= mult["shots"]*mult["away_shots"]
        local_rates["sot_conversion_home"] *= mult["conv"]
        local_rates["sot_conversion_away"] *= mult["conv"]
        sim = simulate_regulation(home, away, local_rates, local_cfg,
                                  np.random.default_rng(int(cfg["seed"])+100+idx))
        hg, ag = sim["home_goals"], sim["away_goals"]
        total = hg+ag
        out.append({
            "scenario": name, "simulations": len(hg),
            "home_win": float(np.mean(hg>ag)), "draw": float(np.mean(hg==ag)),
            "away_win": float(np.mean(hg<ag)), "xg_home": float(np.mean(hg)),
            "xg_away": float(np.mean(ag)), "over_2_5": float(np.mean(total>2.5)),
            "btts": float(np.mean((hg>0)&(ag>0))),
        })
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/pure_game_engine_eng_arg_20260715.json")
    parser.add_argument("--ratings", default="data/curated/fc26_eng_arg_20260715.json")
    parser.add_argument("--output-dir", default="outputs/pure_game_engine")
    args = parser.parse_args()
    cfg = json.loads((ROOT/args.config).read_text(encoding="utf-8"))
    ratings = json.loads((ROOT/args.ratings).read_text(encoding="utf-8"))
    home_name, away_name = cfg["match"]["home"], cfg["match"]["away"]
    home = derive_team_engine(home_name, away_name, ratings, cfg)
    away = derive_team_engine(away_name, home_name, ratings, cfg)
    rates = derive_match_rates(home, away, cfg)
    rng = np.random.default_rng(int(cfg["seed"]))
    reg = simulate_regulation(home, away, rates, cfg, rng)
    et = simulate_extra_time(reg, home, away, rates, cfg, rng)
    et_tied = et["home_goals"] == et["away_goals"]
    pso_home_skill = penalty_skill(home["players"], away["goalkeeper"])
    pso_away_skill = penalty_skill(away["players"], home["goalkeeper"])
    shootout_home = simulate_shootout(int(et_tied.sum()), pso_home_skill, pso_away_skill, rng)

    n = int(cfg["simulations"])
    home90 = float(np.mean(reg["home_goals"]>reg["away_goals"]))
    draw90 = float(np.mean(reg["home_goals"]==reg["away_goals"]))
    away90 = 1-home90-draw90
    home_et = float(np.mean(et["home_goals"]>et["away_goals"]))
    away_et = float(np.mean(et["home_goals"]<et["away_goals"]))
    tied_et = float(np.mean(et_tied))
    pso_home = float(np.mean(shootout_home)) if len(shootout_home) else .5
    home_advance = home90 + draw90*(home_et+tied_et*pso_home)
    away_advance = 1-home_advance
    total = reg["home_goals"]+reg["away_goals"]

    players = (player_event_table(home, away, reg, "home", cfg)+
               player_event_table(away, home, reg, "away", cfg)+
               bench_event_table(home, reg, "home")+
               bench_event_table(away, reg, "away"))
    sensitivity = run_sensitivity(home, away, rates, cfg)
    summary = {
        "method": "pure player/tactical minute-event game engine; no odds, Elo, FIFA ranking or prior Poisson forecast",
        "simulations": n, "seed": cfg["seed"], "fixture": cfg["match"],
        "team_engine": {
            home_name: {k: v for k, v in home.items() if k not in ("players", "bench", "roles")},
            away_name: {k: v for k, v in away.items() if k not in ("players", "bench", "roles")},
        },
        "derived_pregame_rates": rates,
        "regulation_90m": {
            "home_win": home90, "draw": draw90, "away_win": away90,
            "monte_carlo_95pct_ci": {
                "home_win": binomial_ci(home90, n), "draw": binomial_ci(draw90, n),
                "away_win": binomial_ci(away90, n),
            },
            "expected_goals_home": float(np.mean(reg["home_goals"])),
            "expected_goals_away": float(np.mean(reg["away_goals"])),
            "over_0_5": float(np.mean(total>.5)), "over_1_5": float(np.mean(total>1.5)),
            "over_2_5": float(np.mean(total>2.5)), "over_3_5": float(np.mean(total>3.5)),
            "btts": float(np.mean((reg["home_goals"]>0)&(reg["away_goals"]>0))),
            "scorelines": score_distribution(reg["home_goals"], reg["away_goals"]),
        },
        "progression": {
            "home_advance": home_advance, "away_advance": away_advance,
            "extra_time_given_draw": {"home_win": home_et, "still_tied": tied_et, "away_win": away_et},
            "shootout_conversion_home": pso_home_skill, "shootout_conversion_away": pso_away_skill,
            "home_shootout_win": pso_home,
        },
        "event_means_90m": reg["event_means"],
        "first_goal": {
            "home": float(np.mean(reg["first_side"]==1)), "none": float(np.mean(reg["first_side"]==0)),
            "away": float(np.mean(reg["first_side"]==2)),
            "expected_first_goal_minute_given_goal": float(np.mean(reg["first_minute"][reg["first_minute"]>0])),
        },
        "sensitivity_scenarios": sensitivity,
        "prohibited_inputs_confirmed": cfg["prohibited_inputs"],
        "limitations": [
            "Starting XIs are projected, not official; rerun after lineups are released.",
            "FC 26 launch attributes are static and do not contain every hidden football skill or live-form update.",
            "Minute probabilities are event hazards across simulations, not a claim that a named event will occur at an exact minute.",
            "Substitutions and injuries are role-level hazards because confirmed bench usage is unknown.",
        ],
    }

    outdir = ROOT/args.output_dir; outdir.mkdir(parents=True, exist_ok=True)
    write_csv(outdir/"minute_by_minute_1_95.csv", reg["rows"])
    write_csv(outdir/"extra_time_minute_by_minute_conditional.csv", et["rows"])
    write_csv(outdir/"player_event_probabilities.csv", players)
    (outdir/"pure_game_engine_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    top_scores = summary["regulation_90m"]["scorelines"][:8]
    top_players = sorted([x for x in players if x["squad_status"] == "starter"],
                         key=lambda x: x["p_anytime_goal_90m"], reverse=True)[:10]
    top_bench = sorted([x for x in players if x["squad_status"] == "bench"],
                       key=lambda x: x["p_appearance"], reverse=True)[:10]
    windows = [(1,15),(16,30),(31,45),(46,60),(61,75),(76,90),(91,95)]
    report = ["# 英格兰–阿根廷纯游戏引擎逐分钟预测", "",
              f"模拟 {n:,} 场；随机种子 {cfg['seed']}。完全禁用博彩赔率、Polymarket、Elo/FIFA排名和旧Poisson预测。", "",
              "## 90分钟与晋级", "",
              "| 指标 | 概率/期望 |", "|---|---:|",
              f"| 英格兰90分钟胜 | {home90:.2%} |", f"| 90分钟平局 | {draw90:.2%} |",
              f"| 阿根廷90分钟胜 | {away90:.2%} |", f"| 英格兰晋级 | {home_advance:.2%} |",
              f"| 阿根廷晋级 | {away_advance:.2%} |",
              f"| 预期进球 | {summary['regulation_90m']['expected_goals_home']:.3f}–{summary['regulation_90m']['expected_goals_away']:.3f} |",
              f"| 大2.5 | {summary['regulation_90m']['over_2_5']:.2%} |",
              f"| 双方进球 | {summary['regulation_90m']['btts']:.2%} |", "",
              "## 比分峰值", "", "| 比分 | 概率 |", "|---|---:|"]
    report += [f"| {x['score']} | {x['probability']:.2%} |" for x in top_scores]
    report += ["", "## 分钟区间事件强度", "",
               "| 区间 | 英格兰进球 | 阿根廷进球 | 任意射门 | 任意黄牌 | VAR | 换人 |",
               "|---|---:|---:|---:|---:|---:|---:|"]
    for lo, hi in windows:
        block = reg["rows"][lo-1:hi]
        agg = lambda key: sum(float(x[key]) for x in block)
        report.append(f"| {minute_label(lo)}–{minute_label(hi)} | {agg('p_home_goal'):.2%} | {agg('p_away_goal'):.2%} | {agg('p_home_shot')+agg('p_away_shot'):.2f} | {agg('p_home_yellow')+agg('p_away_yellow'):.2f} | {agg('p_var_review'):.2%} | {agg('p_any_substitution'):.2f} |")
    report += ["", "## 球员事件概率（前10）", "",
               "| 球员 | 进球 | 首球 | 助攻 | 预期射门 | 黄牌 | 被换下 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for x in top_players:
        report.append(f"| {x['player']} | {x['p_anytime_goal_90m']:.2%} | {x['p_first_goal']:.2%} | {x['p_assist_90m']:.2%} | {x['expected_shots']:.2f} | {x['p_yellow_90m']:.2%} | {x['p_substituted']:.2%} |")
    report += ["", "## 关键替补进入比赛概率", "",
               "| 球员 | 出场 | 进球 | 助攻 | 预期射门 |", "|---|---:|---:|---:|---:|"]
    for x in top_bench:
        report.append(f"| {x['player']} | {x['p_appearance']:.2%} | {x['p_anytime_goal_90m']:.2%} | {x['p_assist_90m']:.2%} | {x['expected_shots']:.2f} |")
    report += ["", "## 情景压力测试", "",
               "| 情景 | 英胜 | 平 | 阿胜 | xG | 大2.5 | BTTS |", "|---|---:|---:|---:|---:|---:|---:|"]
    for x in sensitivity:
        report.append(f"| {x['scenario']} | {x['home_win']:.2%} | {x['draw']:.2%} | {x['away_win']:.2%} | {x['xg_home']:.2f}–{x['xg_away']:.2f} | {x['over_2_5']:.2%} | {x['btts']:.2%} |")
    report += ["", "## 如何读取逐分钟文件", "",
               "`minute_by_minute_1_95.csv` 的每一行是该分钟的事件发生概率，以及该分钟结束后的领先/平局、期望比分和众数比分；`extra_time_minute_by_minute_conditional.csv` 以比赛进入加时为条件。概率是模拟频率，不是确定性时间表。", "",
               "最大的剩余误差来自未公布首发、临场阵型变化和游戏静态评分无法完整表达的现实状态。"]
    (outdir/"pure_game_engine_report.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"output": str(outdir), "home90": home90, "draw90": draw90,
                      "away90": away90, "home_advance": home_advance,
                      "xg": [summary['regulation_90m']['expected_goals_home'], summary['regulation_90m']['expected_goals_away']]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
