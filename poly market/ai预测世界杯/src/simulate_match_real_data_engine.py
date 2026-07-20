"""Real-data-only minute event engine for England v Argentina (2026-07-15).

No game ratings, market odds, Polymarket prices, Elo ratings or FIFA rankings
are read by this module.  Team strength comes from time-decayed international
results and opponent-adjusted FIFA 2026 match-report xG; event dynamics come
from StatsBomb's open 2018/2022 World Cup event data.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import unicodedata
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from wc_model.historical import RidgePoisson, load_results


ROOT = Path(__file__).resolve().parents[1]


def norm_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return "".join(c for c in value if c.isalnum())


def logistic(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def haversine_km(a: list[float], b: list[float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dlat, dlon = lat2-lat1, lon2-lon1
    q = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371.0 * 2 * math.asin(math.sqrt(q))


def route_km(route: list[list[float]]) -> float:
    return sum(haversine_km(a, b) for a, b in zip(route, route[1:]))


def weighted_rate(frame: pd.DataFrame, col: str, cutoff: date, half_life: float = 35.0,
                  fallback: float = 0.0) -> float:
    if col not in frame or frame[col].notna().sum() == 0:
        return fallback
    age = np.array([(cutoff - date.fromisoformat(str(x))).days for x in frame.date])
    duration = frame.duration_minutes.to_numpy(float)
    w = duration / 90.0 * np.exp(-math.log(2) * np.maximum(age, 0) / half_life)
    x = frame[col].fillna(0).to_numpy(float) * 90.0 / duration
    return float(np.sum(w*x) / max(np.sum(w), 1e-9))


ALIASES = {
    "Congo DR": "DR Congo", "Cabo Verde": "Cape Verde",
    "Korea Republic": "South Korea", "IR Iran": "Iran",
}


def fit_historical(cfg: dict) -> tuple[RidgePoisson, list[dict]]:
    hc = cfg["historical_strength"]
    rows = load_results(ROOT/hc["results"], date.fromisoformat(hc["training_start"]),
                        date.fromisoformat(hc["cutoff_exclusive"]))
    model_cfg = {
        "world_cup_weight": hc["world_cup_weight"],
        "major_tournament_weight": hc["major_tournament_weight"],
        "friendly_weight": hc["friendly_weight"],
    }
    model = RidgePoisson(hc["half_life_days"], hc["ridge"], model_cfg)
    model.fit(rows, date.fromisoformat(hc["cutoff_exclusive"]))
    return model, rows


def historical_expected(model: RidgePoisson, team: str, opponent: str) -> tuple[float, float]:
    opponent = ALIASES.get(opponent, opponent)
    return model.predict(team, opponent, True)


def derive_team_profiles(cfg: dict, team_df: pd.DataFrame, model: RidgePoisson) -> dict:
    cutoff = datetime.fromisoformat(cfg["cutoff_utc"].replace("Z", "+00:00")).date()
    hc = cfg["historical_strength"]
    profiles = {}
    for team in (cfg["match"]["home"], cfg["match"]["away"]):
        frame = team_df[team_df.team == team].copy()
        frame["historical_xgf"] = [historical_expected(model, team, o)[0] for o in frame.opponent]
        frame["historical_xga"] = [historical_expected(model, team, o)[1] for o in frame.opponent]
        age = np.array([(cutoff-date.fromisoformat(str(x))).days for x in frame.date])
        w = frame.duration_minutes.to_numpy(float)/90 * np.exp(-math.log(2)*np.maximum(age, 0)/35)
        xgf90 = frame.xg.to_numpy(float)*90/frame.duration_minutes.to_numpy(float)
        xga90 = frame.xg_against.to_numpy(float)*90/frame.duration_minutes.to_numpy(float)
        off_resid = np.log((xgf90+.18)/(frame.historical_xgf.to_numpy(float)+.18))
        def_resid = np.log((xga90+.18)/(frame.historical_xga.to_numpy(float)+.18))
        prior = hc["current_form_prior_equivalent_minutes"]/90
        off_log = float(np.sum(w*off_resid)/(np.sum(w)+prior))
        leak_log = float(np.sum(w*def_resid)/(np.sum(w)+prior))
        profiles[team] = {
            "matches": int(len(frame)), "minutes": int(frame.duration_minutes.sum()),
            "historical_attack_residual_log": off_log,
            "historical_defence_leak_residual_log": leak_log,
            "xg_for_per90": weighted_rate(frame, "xg", cutoff),
            "xg_against_per90": weighted_rate(frame, "xg_against", cutoff),
            "shots_per90": weighted_rate(frame, "attempts", cutoff),
            "shots_against_per90": weighted_rate(frame, "attempts_against", cutoff, fallback=12.0),
            "sot_rate": float(frame.shots_on_target.sum()/max(frame.attempts.sum(), 1)),
            "possession": weighted_rate(frame, "possession_active_pct", cutoff)/100,
            "passes_per90": weighted_rate(frame, "passes", cutoff),
            "pass_completion": weighted_rate(frame, "pass_completion_pct", cutoff)/100,
            "line_breaks_per90": weighted_rate(frame, "completed_line_breaks", cutoff),
            "final_third_receptions_per90": weighted_rate(frame, "final_third_receptions", cutoff),
            "crosses_per90": weighted_rate(frame, "crosses", cutoff),
            "corners_per90": weighted_rate(frame, "corners", cutoff, fallback=5.0),
            "corners_against_per90": weighted_rate(frame, "corners_against", cutoff, fallback=5.0),
            "free_kicks_won_per90": weighted_rate(frame, "free_kicks", cutoff, fallback=12.5),
            "free_kicks_conceded_per90": weighted_rate(frame, "free_kicks_against", cutoff, fallback=12.5),
            "throw_ins_per90": weighted_rate(frame, "throw_ins", cutoff, fallback=18.0),
            "pressures_per90": weighted_rate(frame, "pressures", cutoff),
            "direct_pressures_per90": weighted_rate(frame, "direct_pressures", cutoff),
            "forced_turnovers_per90": weighted_rate(frame, "forced_turnovers", cutoff),
            "regains_per90": weighted_rate(frame, "possession_regains", cutoff, fallback=45.0),
            "interceptions_per90": weighted_rate(frame, "interceptions", cutoff, fallback=9.0),
            "tackles_per90": weighted_rate(frame, "tackles", cutoff, fallback=12.0),
            "distance_per90": weighted_rate(frame, "distance_km", cutoff),
            "high_speed_distance_per90": weighted_rate(frame, "zone4_km", cutoff),
            "phase_profile": {c: weighted_rate(frame, c, cutoff) for c in frame.columns if c.startswith("phase_")},
        }
    home, away = cfg["match"]["home"], cfg["match"]["away"]
    base_h, base_a = historical_expected(model, home, away)
    profiles[home]["historical_target_xg"] = base_h
    profiles[away]["historical_target_xg"] = base_a
    # Opponent-adjusted current performance.  The shrinkage above prevents six
    # tournament matches from replacing the much larger historical sample.
    profiles[home]["target_xg"] = base_h*math.exp(.58*profiles[home]["historical_attack_residual_log"] +
                                                  .42*profiles[away]["historical_defence_leak_residual_log"])
    profiles[away]["target_xg"] = base_a*math.exp(.58*profiles[away]["historical_attack_residual_log"] +
                                                  .42*profiles[home]["historical_defence_leak_residual_log"])
    # Shooting volume combines creation and opponent suppression in log space.
    for team, opp in ((home, away), (away, home)):
        profiles[team]["target_shots"] = math.sqrt(max(.1, profiles[team]["shots_per90"])*
                                                    max(.1, profiles[opp]["shots_against_per90"]))
    ph = profiles[home]["possession"]
    pa = profiles[away]["possession"]
    profiles[home]["target_possession"] = float(logistic((math.log(ph/(1-ph))-math.log(pa/(1-pa)))/2))
    profiles[away]["target_possession"] = 1-profiles[home]["target_possession"]
    return profiles


def referee_posterior(cfg: dict, dynamics: dict) -> dict:
    r = cfg["referee"]
    n = r["career_effective_prior_matches"]
    wc_weight = float(r.get("world_cup_match_weight", 1.0))
    wc_matches = float(r["world_cup_2026_matches"])*wc_weight
    career_y = r["career_yellows"]/r["career_matches"]
    career_r = r["career_reds"]/r["career_matches"]
    y = (career_y*n+r["world_cup_2026_yellows"]*wc_weight)/(n+wc_matches)
    red = (career_r*n+r["world_cup_2026_reds"]*wc_weight)/(n+wc_matches)
    fouls = (r["recent_fouls_per_match"]*n+r["world_cup_2026_fouls"]*wc_weight)/(n+wc_matches)
    base_pen = dynamics["factors"]["base_rate_per_team_minute"]["penalties"]*2*95
    pn = r["penalty_prior_matches"]
    pens = (base_pen*pn+r["world_cup_2026_penalties"]*wc_weight)/(pn+wc_matches)
    return {"yellow_per_match": y, "red_per_match": red, "fouls_per_match": fouls,
            "penalties_per_match": pens, "career_yellow_rate": career_y,
            "career_red_rate": career_r, "historical_wc_penalty_rate": base_pen,
            "world_cup_match_weight": wc_weight}


def blended_match_rate(a: float, b: float) -> float:
    return math.sqrt(max(a, .01)*max(b, .01))


def derive_event_rates(cfg: dict, profiles: dict, ref: dict) -> dict:
    h, a = cfg["match"]["home"], cfg["match"]["away"]
    hp, ap = profiles[h], profiles[a]
    total_fouls = .55*ref["fouls_per_match"] + .45*(hp["free_kicks_conceded_per90"]+ap["free_kicks_conceded_per90"])
    foul_share_h = hp["free_kicks_conceded_per90"] / max(hp["free_kicks_conceded_per90"]+ap["free_kicks_conceded_per90"], .1)
    attack_share_h = hp["target_shots"] / (hp["target_shots"]+ap["target_shots"])
    rates = {
        "home_xg": hp["target_xg"], "away_xg": ap["target_xg"],
        "home_shots": hp["target_shots"], "away_shots": ap["target_shots"],
        "home_sot_rate": float(np.clip(hp["sot_rate"], .25, .50)),
        "away_sot_rate": float(np.clip(ap["sot_rate"], .25, .50)),
        "home_fouls": total_fouls*foul_share_h, "away_fouls": total_fouls*(1-foul_share_h),
        "home_yellows": ref["yellow_per_match"]*foul_share_h,
        "away_yellows": ref["yellow_per_match"]*(1-foul_share_h),
        "home_reds": ref["red_per_match"]*foul_share_h,
        "away_reds": ref["red_per_match"]*(1-foul_share_h),
        "home_penalties": ref["penalties_per_match"]*attack_share_h,
        "away_penalties": ref["penalties_per_match"]*(1-attack_share_h),
        "home_corners": blended_match_rate(hp["corners_per90"], ap["corners_against_per90"]),
        "away_corners": blended_match_rate(ap["corners_per90"], hp["corners_against_per90"]),
    }
    for side, p, opp in (("home", hp, ap), ("away", ap, hp)):
        rates.update({
            f"{side}_passes": p["passes_per90"], f"{side}_line_breaks": p["line_breaks_per90"],
            f"{side}_final_third_receptions": p["final_third_receptions_per90"],
            f"{side}_crosses": p["crosses_per90"], f"{side}_throw_ins": p["throw_ins_per90"],
            f"{side}_pressures": p["pressures_per90"], f"{side}_direct_pressures": p["direct_pressures_per90"],
            f"{side}_forced_turnovers": p["forced_turnovers_per90"], f"{side}_regains": p["regains_per90"],
            f"{side}_interceptions": p["interceptions_per90"], f"{side}_tackles": p["tackles_per90"],
        })
    return rates


def normalized_minute_curve(dynamics: dict, target: str, minutes: int = 95) -> np.ndarray:
    raw = dynamics["factors"]["minute_multiplier"].get(target, {})
    v = np.array([float(raw.get(str(min(i, 95)), 1.0)) for i in range(1, minutes+1)])
    return v/v.sum()


def state_values(own: np.ndarray, opp: np.ndarray, mapping: dict) -> np.ndarray:
    return np.where(own>opp, mapping["leading"], np.where(own<opp, mapping["trailing"], mapping["drawing"]))


def red_values(own_red: np.ndarray, opp_red: np.ndarray, mapping: dict) -> np.ndarray:
    diff = np.where(own_red>opp_red, "-1", np.where(own_red<opp_red, "1", "0"))
    return np.where(diff == "-1", mapping["-1"], np.where(diff == "1", mapping["1"], mapping["0"]))


def score_mode(h: np.ndarray, a: np.ndarray) -> str:
    code = np.minimum(h, 9)*10+np.minimum(a, 9)
    m = int(np.bincount(code, minlength=100).argmax())
    return f"{m//10}-{m%10}"


def simulate_regulation(cfg: dict, profiles: dict, rates: dict, dynamics: dict,
                        rng: np.random.Generator, n: int | None = None,
                        overrides: dict | None = None) -> dict:
    n = int(n or cfg["simulations"]); overrides = overrides or {}
    minutes = cfg["match"]["regulation_modeled_minutes"]
    hname, aname = cfg["match"]["home"], cfg["match"]["away"]
    rr = copy.deepcopy(rates)
    for key, mult in overrides.get("rate_multipliers", {}).items():
        rr[key] *= mult
    if "xg_values" in overrides:
        rr["home_xg"], rr["away_xg"] = overrides["xg_values"]
    hf = np.zeros(n, np.int8); af = np.zeros(n, np.int8)
    hg = np.zeros(n, np.int8); ag = np.zeros(n, np.int8)
    hr = np.zeros(n, np.int8); ar = np.zeros(n, np.int8)
    hshots = np.zeros(n, np.int8); ashots = np.zeros(n, np.int8)
    hsot_n = np.zeros(n, np.int8); asot_n = np.zeros(n, np.int8)
    hy = np.zeros(n, np.int8); ay = np.zeros(n, np.int8)
    hsubs = np.zeros(n, np.int8); asubs = np.zeros(n, np.int8)
    first_side = np.zeros(n, np.int8); first_minute = np.zeros(n, np.int8)
    tempo_uncertainty = rng.lognormal(-.5*.07**2, .07, n)
    h_attack_uncertainty = rng.lognormal(-.5*.09**2, .09, n)
    a_attack_uncertainty = rng.lognormal(-.5*.09**2, .09, n)
    curves = {t: normalized_minute_curve(dynamics, t, minutes) for t in
              ("shots", "xg", "fouls", "yellow_cards", "red_cards", "penalties", "corners", "substitutions", "injuries", "pressures")}
    sf = dynamics["factors"]["score_state_multiplier"]
    rf = dynamics["factors"]["red_diff_multiplier"]
    if overrides.get("disable_state_effects"):
        sf = {k: {"leading": 1.0, "drawing": 1.0, "trailing": 1.0} for k in sf}
    # Target xG includes penalty goals.  Remove their posterior mean from open play.
    h_open_xg = max(.15, rr["home_xg"]-.76*rr["home_penalties"])
    a_open_xg = max(.15, rr["away_xg"]-.76*rr["away_penalties"])
    hconv = np.clip(h_open_xg/max(rr["home_shots"], .1), .025, .25)
    aconv = np.clip(a_open_xg/max(rr["away_shots"], .1), .025, .25)
    event_totals = Counter(); rows = []
    total_team_minutes = {hname: profiles[hname]["minutes"], aname: profiles[aname]["minutes"]}
    for mi in range(minutes):
        minute = mi+1
        hss = state_values(hg, ag, sf["shots"]); ass = state_values(ag, hg, sf["shots"])
        hxs = state_values(hg, ag, sf["xg"]); axs = state_values(ag, hg, sf["xg"])
        hrs = red_values(hr, ar, rf["shots"]); ars = red_values(ar, hr, rf["shots"])
        # Accumulated tournament minutes only affect the late-match tail; both
        # teams have equal rest, while Argentina played 30 more match-minutes.
        frac = max(0.0, minute-65)/30
        hfat = 1-max(0, total_team_minutes[hname]-540)/60*.025*frac
        afat = 1-max(0, total_team_minutes[aname]-540)/60*.025*frac
        hp = np.clip(rr["home_shots"]*curves["shots"][mi]*hss*hrs*hfat*tempo_uncertainty, 0, .50)
        ap = np.clip(rr["away_shots"]*curves["shots"][mi]*ass*ars*afat*tempo_uncertainty, 0, .50)
        hshot = rng.random(n) < hp; ashot = rng.random(n) < ap
        hsot = hshot & (rng.random(n) < rr["home_sot_rate"])
        asot = ashot & (rng.random(n) < rr["away_sot_rate"])
        hgoal_open = hshot & (rng.random(n) < np.clip(hconv*hxs*h_attack_uncertainty, .01, .50))
        agoal_open = ashot & (rng.random(n) < np.clip(aconv*axs*a_attack_uncertainty, .01, .50))
        hpenp = np.clip(rr["home_penalties"]*curves["penalties"][mi]*state_values(hg, ag, sf["penalties"]), 0, .04)
        apenp = np.clip(rr["away_penalties"]*curves["penalties"][mi]*state_values(ag, hg, sf["penalties"]), 0, .04)
        hpen = rng.random(n)<hpenp; apen = rng.random(n)<apenp
        hgoal = hgoal_open.astype(np.int8)+(hpen & (rng.random(n)<.79)).astype(np.int8)
        agoal = agoal_open.astype(np.int8)+(apen & (rng.random(n)<.78)).astype(np.int8)
        hfp = np.clip(rr["home_fouls"]*curves["fouls"][mi]*state_values(hg, ag, sf["fouls"]), 0, .45)
        afp = np.clip(rr["away_fouls"]*curves["fouls"][mi]*state_values(ag, hg, sf["fouls"]), 0, .45)
        hfoul = rng.random(n)<hfp; afoul = rng.random(n)<afp
        hyellow = hfoul & (rng.random(n)<np.clip(rr["home_yellows"]*curves["yellow_cards"][mi]/max(hfp.mean(),1e-5),0,.75))
        ayellow = afoul & (rng.random(n)<np.clip(rr["away_yellows"]*curves["yellow_cards"][mi]/max(afp.mean(),1e-5),0,.75))
        hred = hfoul & (rng.random(n)<np.clip(rr["home_reds"]*curves["red_cards"][mi]/max(hfp.mean(),1e-5),0,.08))
        ared = afoul & (rng.random(n)<np.clip(rr["away_reds"]*curves["red_cards"][mi]/max(afp.mean(),1e-5),0,.08))
        hcorner_p = np.clip(rr["home_corners"]*curves["corners"][mi]*state_values(hg,ag,sf["corners"]),0,.25)
        acorner_p = np.clip(rr["away_corners"]*curves["corners"][mi]*state_values(ag,hg,sf["corners"]),0,.25)
        hcorner = rng.random(n)<hcorner_p; acorner = rng.random(n)<acorner_p
        injury_base = dynamics["factors"]["base_rate_per_team_minute"]["injuries"]
        hinjury = rng.random(n)<injury_base*curves["injuries"][mi]*minutes*(1+.5*frac)
        ainjury = rng.random(n)<injury_base*curves["injuries"][mi]*minutes*(1+.5*frac)
        if minute >= 50:
            base_sub_h = 5.0*curves["substitutions"][mi]*state_values(hg,ag,sf["substitutions"])
            base_sub_a = 5.0*curves["substitutions"][mi]*state_values(ag,hg,sf["substitutions"])
            hsub = (hsubs<5)&(rng.random(n)<np.clip(base_sub_h,0,.30))
            asub = (asubs<5)&(rng.random(n)<np.clip(base_sub_a,0,.30))
        else:
            hsub = np.zeros(n,bool); asub=np.zeros(n,bool)
        hsub |= hinjury&(hsubs<5); asub |= ainjury&(asubs<5)
        var = ((hpen|apen)&(rng.random(n)<.92)) | ((hgoal>0)|(agoal>0))&(rng.random(n)<.08) | ((hred|ared)&(rng.random(n)<.70))
        new = first_side==0
        hfirst = new&(hgoal>0)&(agoal==0); afirst = new&(agoal>0)&(hgoal==0)
        both = new&(hgoal>0)&(agoal>0); coin=rng.random(n)<.5
        hfirst |= both&coin; afirst |= both&~coin
        first_side[hfirst]=1; first_side[afirst]=2; first_minute[hfirst|afirst]=minute
        hg += hgoal; ag += agoal; hr += hred; ar += ared
        hf += hfoul; af += afoul; hy += hyellow; ay += ayellow
        hshots += hshot.astype(np.int8)+hpen.astype(np.int8); ashots += ashot.astype(np.int8)+apen.astype(np.int8)
        hsot_n += hsot.astype(np.int8)+hpen.astype(np.int8); asot_n += asot.astype(np.int8)+apen.astype(np.int8)
        hsubs += hsub; asubs += asub
        poss = np.clip(profiles[hname]["target_possession"]+.035*(hg<ag)-.035*(hg>ag)-.07*hr+.07*ar,.25,.75)
        attack_curve = curves["shots"][mi]*minutes
        pressure_curve = curves["pressures"][mi]*minutes
        row = {
            "minute": minute if minute<=90 else f"90+{minute-90}",
            "p_england_shot": float(np.mean(hshot|hpen)), "p_argentina_shot": float(np.mean(ashot|apen)),
            "p_england_sot": float(np.mean(hsot|hpen)), "p_argentina_sot": float(np.mean(asot|apen)),
            "p_england_goal": float(np.mean(hgoal>0)), "p_argentina_goal": float(np.mean(agoal>0)),
            "p_england_foul": float(np.mean(hfoul)), "p_argentina_foul": float(np.mean(afoul)),
            "p_england_yellow": float(np.mean(hyellow)), "p_argentina_yellow": float(np.mean(ayellow)),
            "p_england_red": float(np.mean(hred)), "p_argentina_red": float(np.mean(ared)),
            "p_england_penalty": float(np.mean(hpen)), "p_argentina_penalty": float(np.mean(apen)),
            "p_england_corner": float(np.mean(hcorner)), "p_argentina_corner": float(np.mean(acorner)),
            "p_var_review": float(np.mean(var)), "p_any_injury_stoppage": float(np.mean(hinjury|ainjury)),
            "p_any_substitution": float(np.mean(hsub|asub)), "expected_england_possession": float(np.mean(poss)),
            "p_england_leading_after": float(np.mean(hg>ag)), "p_draw_after": float(np.mean(hg==ag)),
            "p_argentina_leading_after": float(np.mean(hg<ag)),
            "expected_england_goals_after": float(np.mean(hg)), "expected_argentina_goals_after": float(np.mean(ag)),
            "modal_score_after": score_mode(hg,ag),
        }
        for side, prefix in (("home","england"),("away","argentina")):
            for metric in ("passes","line_breaks","final_third_receptions","crosses","throw_ins"):
                expected = rr[f"{side}_{metric}"]/minutes*attack_curve
                row[f"expected_{prefix}_{metric}"] = expected
                row[f"p_any_{prefix}_{metric}"] = 1-math.exp(-expected)
            for metric in ("pressures","direct_pressures","forced_turnovers","regains","interceptions","tackles"):
                expected = rr[f"{side}_{metric}"]/minutes*pressure_curve
                row[f"expected_{prefix}_{metric}"] = expected
                row[f"p_any_{prefix}_{metric}"] = 1-math.exp(-expected)
        rows.append(row)
        for k,v in (("home_shots",hshot|hpen),("away_shots",ashot|apen),("home_sot",hsot|hpen),("away_sot",asot|apen),
                    ("home_goals",hgoal),("away_goals",agoal),("home_fouls",hfoul),("away_fouls",afoul),
                    ("home_yellows",hyellow),("away_yellows",ayellow),("home_reds",hred),("away_reds",ared),
                    ("home_penalties",hpen),("away_penalties",apen),("home_corners",hcorner),("away_corners",acorner),
                    ("var_reviews",var),("injuries",hinjury|ainjury),("substitutions",hsub.astype(int)+asub.astype(int))):
            event_totals[k] += float(np.sum(v))
    return {"home_goals":hg,"away_goals":ag,"home_reds":hr,"away_reds":ar,"home_shots":hshots,
            "away_shots":ashots,"home_sot":hsot_n,"away_sot":asot_n,"home_yellows":hy,"away_yellows":ay,
            "home_subs":hsubs,"away_subs":asubs,"first_side":first_side,"first_minute":first_minute,
            "rows":rows,"event_means":{k:v/n for k,v in event_totals.items()}}


def simulate_extra_time(cfg: dict, reg: dict, rates: dict, dynamics: dict, rng: np.random.Generator) -> dict:
    mask=reg["home_goals"]==reg["away_goals"]; n=int(mask.sum()); minutes=cfg["match"]["extra_time_minutes"]
    hg=np.zeros(n,np.int8); ag=np.zeros(n,np.int8); hr=reg["home_reds"][mask].copy(); ar=reg["away_reds"][mask].copy()
    etf=dynamics["extra_time_and_shootout"]["rate_multiplier_vs_regulation"]
    hshots_target=rates["home_shots"]*minutes/95*etf["shots"]
    ashots_target=rates["away_shots"]*minutes/95*etf["shots"]
    hxg_target=rates["home_xg"]*minutes/95*etf["xg"]; axg_target=rates["away_xg"]*minutes/95*etf["xg"]
    weights=np.array([.90 if m<=15 else 1.10 for m in range(1,31)],float); weights/=weights.sum()
    rows=[]
    for i,w in enumerate(weights):
        hp=np.clip(hshots_target*w*np.power(.63,hr)*np.power(1.34,ar),0,.45)
        ap=np.clip(ashots_target*w*np.power(.63,ar)*np.power(1.34,hr),0,.45)
        hs=rng.random(n)<hp; ass=rng.random(n)<ap
        hg_evt=hs&(rng.random(n)<np.clip(hxg_target/max(hshots_target,.1),.02,.35))
        ag_evt=ass&(rng.random(n)<np.clip(axg_target/max(ashots_target,.1),.02,.35))
        hg+=hg_evt; ag+=ag_evt
        rows.append({"minute":96+i,"conditional_on_extra_time":True,"p_england_shot":float(np.mean(hs)),
                     "p_argentina_shot":float(np.mean(ass)),"p_england_goal":float(np.mean(hg_evt)),
                     "p_argentina_goal":float(np.mean(ag_evt)),"p_england_leading_after":float(np.mean(hg>ag)),
                     "p_tied_after":float(np.mean(hg==ag)),"p_argentina_leading_after":float(np.mean(hg<ag))})
    return {"reached":n,"home_goals":hg,"away_goals":ag,"rows":rows}


def shootout_home_win(n: int, ph: float, pa: float, rng: np.random.Generator) -> np.ndarray:
    h=rng.binomial(5,ph,n); a=rng.binomial(5,pa,n); decided=h!=a; win=h>a
    for _ in range(20):
        pending=~decided
        if not pending.any(): break
        hs=rng.random(n)<ph; ass=rng.random(n)<pa; new=pending&(hs!=ass)
        win[new]=hs[new]; decided[new]=True
    win[~decided]=rng.random((~decided).sum())<.5
    return win


def role_group(role: str) -> str:
    r=str(role).upper()
    if "GK" in r or "GOALKEEPER" in r: return "GK"
    if "DEF" in r or "BACK" in r: return "DEF"
    if "FWD" in r or "FORWARD" in r or "STRIKER" in r or "WING" in r: return "FWD"
    return "MID"


def build_player_table(cfg: dict, player_df: pd.DataFrame, history: pd.DataFrame,
                       rates: dict, reg: dict) -> list[dict]:
    out=[]
    history["key"]=history.player.map(norm_name)
    for team, side in ((cfg["match"]["home"],"home"),(cfg["match"]["away"],"away")):
        pf=player_df[player_df.team==team].copy(); pf["key"]=pf.player.map(norm_name)
        match_count=max(1,int(pf["report"].nunique())) if "report" in pf else 6
        agg=pf.groupby("key").agg({"player":"first","role":"first","minutes":"sum","attempts":"sum","goals":"sum",
                                      "line_breaks_completed":"sum","crosses_completed":"sum","take_ons":"sum",
                                      "passes_completed":"sum","starter":"sum"}).reset_index()
        hagg=history[history.team==team].groupby("key").agg({"shots":"sum","xg":"sum","goals":"sum","key_passes":"sum",
                                                              "crosses":"sum","fouls":"sum","tackles":"sum","cards":"sum",
                                                              "minutes":"sum"}).reset_index()
        lookup={r.key:r for _,r in agg.iterrows()}; hlookup={r.key:r for _,r in hagg.iterrows()}
        lineup=cfg["lineups"][team]; names=lineup["starters"]+lineup["bench_priority"]
        base_shot={"GK":.02,"DEF":.45,"MID":1.25,"FWD":2.35}
        raw=[]
        for rank,name in enumerate(names):
            k=norm_name(name); r=lookup.get(k); old=hlookup.get(k)
            role=role_group(r["role"] if r is not None else ("GK" if rank==0 else "MID"))
            minutes=float(r["minutes"] if r is not None else 0); attempts=float(r["attempts"] if r is not None else 0)
            goals=float(r["goals"] if r is not None else 0); starts=float(r["starter"] if r is not None else 0)
            old_minutes=float(old["minutes"] if old is not None else 0); old_shots=float(old["shots"] if old is not None else 0)
            # 2022 player data is a decayed prior worth 25% of its minutes.
            shot_num=attempts+.25*old_shots+base_shot[role]*2.0
            shot_den=max(minutes+.25*old_minutes+180,90)
            shot_intensity=shot_num/shot_den
            conv=(goals+.25*(float(old["xg"]) if old is not None else 0)+1.1)/(attempts+.25*old_shots+10)
            creation=(float(r["line_breaks_completed"]+2*r["crosses_completed"]+r["take_ons"]+.02*r["passes_completed"]) if r is not None else 1)
            if old is not None: creation += .25*(3*float(old["key_passes"])+float(old["crosses"]))
            card=(.3 if role=="DEF" else .18 if role=="MID" else .10)
            if old is not None: card += .25*(float(old["cards"])+.08*float(old["fouls"])+.04*float(old["tackles"]))
            starter=rank<11
            availability=float(lineup.get("availability",{}).get(name,1.0))
            appearance_override=lineup.get("appearance_probability",{}).get(name)
            minutes_if_appears=lineup.get("minutes_if_appears",{}).get(name)
            tournament_assists=lineup.get("tournament_assists",{}).get(name)
            if starter:
                avg_start_minutes=minutes/max(starts,1)
                sub_prob=float(np.clip(1-avg_start_minutes/95,.02,.75)) if starts else (.05 if role=="GK" else .30)
                appearance=float(appearance_override) if appearance_override is not None else availability
                exp_minutes=appearance*(float(minutes_if_appears) if minutes_if_appears is not None else 95*(1-sub_prob*.28))
            else:
                sub_apps=max(0,len(pf[pf.key==k])-starts) if r is not None else 0
                appearance=(float(appearance_override) if appearance_override is not None else
                            float(np.clip((sub_apps+1.2)/(match_count+3),.10,.70))*availability)
                sub_prob=0.; exp_minutes=appearance*(float(minutes_if_appears) if minutes_if_appears is not None else (24 if role in ("MID","FWD") else 18))
            raw.append({"team":team,"player":name,"role":role,"squad_status":"starter" if starter else "bench",
                        "p_appearance":appearance,"expected_minutes":exp_minutes,"p_substituted":sub_prob,
                        "tournament_minutes":minutes,"tournament_attempts":attempts,"tournament_goals":goals,
                        "tournament_assists":tournament_assists if tournament_assists is not None else "",
                        "shot_weight":shot_intensity*exp_minutes,"goal_weight":shot_intensity*exp_minutes*conv,
                        "assist_weight":creation*exp_minutes/max(minutes,90),"card_weight":card*exp_minutes/90})
        for key in ("shot_weight","goal_weight","assist_weight","card_weight"):
            total=sum(x[key] for x in raw) or 1
            for x in raw: x[key+"_share"]=x[key]/total
        team_first=float(np.mean(reg["first_side"]==(1 if side=="home" else 2)))
        for x in raw:
            exp_shots=rates[f"{side}_shots"]*x["shot_weight_share"]
            exp_goals=rates[f"{side}_xg"]*x["goal_weight_share"]
            exp_assists=rates[f"{side}_xg"]*.72*x["assist_weight_share"]
            if x["tournament_assists"] != "":
                empirical_assists=(float(x["tournament_assists"])+.36)/(x["tournament_minutes"]+270)*x["expected_minutes"]
                exp_assists=.35*exp_assists+.65*empirical_assists
            exp_cards=np.mean(reg[f"{side}_yellows"])*x["card_weight_share"]
            x.update({"expected_shots":exp_shots,"expected_goals":exp_goals,
                      "p_anytime_goal_90m":1-math.exp(-exp_goals),
                      "p_first_goal":team_first*x["goal_weight_share"],
                      "p_assist_90m":1-math.exp(-exp_assists),"p_yellow_90m":1-math.exp(-exp_cards)})
            for key in list(x):
                if key.endswith("_weight") or key.endswith("_share"): del x[key]
            out.append(x)
    return sorted(out,key=lambda x:(x["team"],-x["p_anytime_goal_90m"]))


def score_distribution(h: np.ndarray,a: np.ndarray,limit:int=16)->list[dict]:
    c=Counter(zip(h.tolist(),a.tolist())); n=len(h)
    return [{"score":f"{x}-{y}","probability":v/n} for (x,y),v in c.most_common(limit)]


def ci(p:float,n:int)->list[float]:
    z=1.96*math.sqrt(max(p*(1-p),1e-9)/n); return [max(0,p-z),min(1,p+z)]


def write_csv(path:Path,rows:list[dict]):
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",default="config/real_data_engine_eng_arg_20260715.json")
    ap.add_argument("--output-dir",default="outputs/real_data_engine");args=ap.parse_args()
    cfg=json.loads((ROOT/args.config).read_text(encoding="utf-8"));outdir=ROOT/args.output_dir;outdir.mkdir(parents=True,exist_ok=True)
    team_df=pd.read_csv(ROOT/cfg["data"]["fifa_team_features"]); player_df=pd.read_csv(ROOT/cfg["data"]["fifa_player_features"])
    history=pd.read_csv(ROOT/cfg["data"]["statsbomb_player_history"])
    dynamics=json.loads((ROOT/cfg["data"]["statsbomb_dynamics"]).read_text(encoding="utf-8"))
    model,hist_rows=fit_historical(cfg);profiles=derive_team_profiles(cfg,team_df,model)
    ref=referee_posterior(cfg,dynamics);rates=derive_event_rates(cfg,profiles,ref)
    rng=np.random.default_rng(cfg["seed"]);reg=simulate_regulation(cfg,profiles,rates,dynamics,rng)
    et=simulate_extra_time(cfg,reg,rates,dynamics,rng); tied=et["home_goals"]==et["away_goals"]
    pso=dynamics["extra_time_and_shootout"]; pool=pso["shootout_conversion"]
    ph=pso.get("shootout_by_team",{}).get("England",{}).get("beta_binomial_posterior",pool)
    pa=pso.get("shootout_by_team",{}).get("Argentina",{}).get("beta_binomial_posterior",pool)
    pso_win=shootout_home_win(int(tied.sum()),ph,pa,rng)
    hg,ag=reg["home_goals"],reg["away_goals"];n=len(hg);draw=float(np.mean(hg==ag))
    h90=float(np.mean(hg>ag));a90=float(np.mean(hg<ag));het=float(np.mean(et["home_goals"]>et["away_goals"]))
    aet=float(np.mean(et["home_goals"]<et["away_goals"]));tet=float(np.mean(tied));hpso=float(np.mean(pso_win)) if len(pso_win) else .5
    hadv=h90+draw*(het+tet*hpso);total=hg+ag
    players=build_player_table(cfg,player_df,history,rates,reg)
    scenarios=[
        ("基准",{}),("仅赛前历史实力",{"xg_values":[profiles["England"]["historical_target_xg"],profiles["Argentina"]["historical_target_xg"]]}),
        ("移除比分状态反馈",{"disable_state_effects":True}),("低节奏/终结率-10%",{"rate_multipliers":{"home_xg":.90,"away_xg":.90,"home_shots":.94,"away_shots":.94}}),
        ("开放比赛/终结率+10%",{"rate_multipliers":{"home_xg":1.10,"away_xg":1.10,"home_shots":1.06,"away_shots":1.06}}),
        ("Rice缺阵压力情景",{"rate_multipliers":{"home_xg":.96,"home_shots":.97,"away_xg":1.03,"away_shots":1.02}}),
        ("阿根廷额外疲劳尾部",{"rate_multipliers":{"away_xg":.97,"away_shots":.97}}),
    ]
    sensitivity=[]
    for i,(name,ov) in enumerate(scenarios):
        s=simulate_regulation(cfg,profiles,rates,dynamics,np.random.default_rng(cfg["seed"]+100+i),n=40000,overrides=ov)
        sh,sa=s["home_goals"],s["away_goals"]
        sensitivity.append({"scenario":name,"england_win":float(np.mean(sh>sa)),"draw":float(np.mean(sh==sa)),
                            "argentina_win":float(np.mean(sh<sa)),"england_goals":float(np.mean(sh)),
                            "argentina_goals":float(np.mean(sa)),"over_2_5":float(np.mean(sh+sa>2)),
                            "btts":float(np.mean((sh>0)&(sa>0)))})
    travel={k:route_km(v) for k,v in cfg["travel_route"].items()}
    tactical=[]
    for team,p in profiles.items():
        for metric,value in p["phase_profile"].items(): tactical.append({"team":team,"metric":metric,"weighted_value":value})
    summary={
        "method":"real historical data minute-event engine; no game or market inputs", "cutoff_utc":cfg["cutoff_utc"],
        "fixture":cfg["match"],"simulations":n,"seed":cfg["seed"],"historical_fit":model.fit_info,
        "historical_training_matches":len(hist_rows),"team_profiles":profiles,"derived_event_rates":rates,"referee_posterior":ref,
        "travel_km_measured_not_forced_into_base_rate":travel,"environment":cfg["environment"],
        "regulation":{"england_win":h90,"draw":draw,"argentina_win":a90,"ci95_monte_carlo":{"england_win":ci(h90,n),"draw":ci(draw,n),"argentina_win":ci(a90,n)},
                      "expected_goals_england":float(np.mean(hg)),"expected_goals_argentina":float(np.mean(ag)),
                      "over_0_5":float(np.mean(total>0)),"over_1_5":float(np.mean(total>1)),"over_2_5":float(np.mean(total>2)),
                      "over_3_5":float(np.mean(total>3)),"btts":float(np.mean((hg>0)&(ag>0))),"scorelines":score_distribution(hg,ag)},
        "progression":{"england_advance":hadv,"argentina_advance":1-hadv,"extra_time_given_draw":{"england_win":het,"tied":tet,"argentina_win":aet},
                       "shootout_conversion_england":ph,"shootout_conversion_argentina":pa,"england_shootout_win":hpso},
        "event_means_90m":reg["event_means"],"first_goal":{"england":float(np.mean(reg["first_side"]==1)),"none":float(np.mean(reg["first_side"]==0)),
                                                               "argentina":float(np.mean(reg["first_side"]==2)),"mean_minute_given_goal":float(np.mean(reg["first_minute"][reg["first_minute"]>0]))},
        "validation":dynamics["validation"],"extra_time_empirics":dynamics["extra_time_and_shootout"],"sensitivity":sensitivity,
        "lineup_status":cfg["lineups"]["status"],"prohibited_inputs_confirmed":cfg["prohibited_inputs"],
        "interpretation":"minute rows are conditional event hazards across simulations, not deterministic forecasts of an exact event at an exact minute"
    }
    write_csv(outdir/"minute_by_minute_1_95.csv",reg["rows"]);write_csv(outdir/"extra_time_minute_by_minute_conditional.csv",et["rows"])
    write_csv(outdir/"player_event_probabilities.csv",players);write_csv(outdir/"sensitivity_scenarios.csv",sensitivity);write_csv(outdir/"tactical_phase_profile.csv",tactical)
    (outdir/"real_data_engine_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    windows=[(1,15),(16,30),(31,45),(46,60),(61,75),(76,90),(91,95)]
    report=["# 英格兰—阿根廷：纯真实历史数据逐分钟模型","",f"数据截点：{cfg['cutoff_utc']}；Monte Carlo：{n:,} 次。完全未读取游戏评分、赔率、Polymarket、Elo 或 FIFA 排名。","",
            "## 核心结果","","| 指标 | 结果 |","|---|---:|",f"| 英格兰 90分钟胜 | {h90:.2%} |",f"| 90分钟平局 | {draw:.2%} |",f"| 阿根廷 90分钟胜 | {a90:.2%} |",
            f"| 英格兰晋级 | {hadv:.2%} |",f"| 阿根廷晋级 | {1-hadv:.2%} |",f"| 期望进球 | {np.mean(hg):.3f} – {np.mean(ag):.3f} |",
            f"| 大2.5 | {np.mean(total>2):.2%} |",f"| 双方进球 | {np.mean((hg>0)&(ag>0)):.2%} |","","## 最可能比分","","| 比分 | 概率 |","|---|---:|"]
    report += [f"| {x['score']} | {x['probability']:.2%} |" for x in summary["regulation"]["scorelines"][:10]]
    report += ["","## 分钟区间事件强度","","| 区间 | 英进球 | 阿进球 | 任意射门期望 | 任意黄牌期望 | VAR | 换人期望 |","|---|---:|---:|---:|---:|---:|---:|"]
    for lo,hi in windows:
        block=reg["rows"][lo-1:hi]; sm=lambda k:sum(float(x[k]) for x in block)
        report.append(f"| {lo}–{hi if hi<=90 else '90+5'} | {sm('p_england_goal'):.2%} | {sm('p_argentina_goal'):.2%} | {sm('p_england_shot')+sm('p_argentina_shot'):.2f} | {sm('p_england_yellow')+sm('p_argentina_yellow'):.2f} | {sm('p_var_review'):.2%} | {sm('p_any_substitution'):.2f} |")
    report += ["","## 关键球员事件概率","","| 球员 | 出场 | 预期射门 | 进球 | 首球 | 助攻 | 黄牌 | 被换下 |","|---|---:|---:|---:|---:|---:|---:|---:|"]
    for x in sorted(players,key=lambda z:z["p_anytime_goal_90m"],reverse=True)[:16]:
        report.append(f"| {x['player']} | {x['p_appearance']:.1%} | {x['expected_shots']:.2f} | {x['p_anytime_goal_90m']:.2%} | {x['p_first_goal']:.2%} | {x['p_assist_90m']:.2%} | {x['p_yellow_90m']:.2%} | {x['p_substituted']:.1%} |")
    report += ["","## 压力测试","","| 情景 | 英胜 | 平 | 阿胜 | xG | 大2.5 | BTTS |","|---|---:|---:|---:|---:|---:|---:|"]
    for x in sensitivity: report.append(f"| {x['scenario']} | {x['england_win']:.2%} | {x['draw']:.2%} | {x['argentina_win']:.2%} | {x['england_goals']:.2f}–{x['argentina_goals']:.2f} | {x['over_2_5']:.2%} | {x['btts']:.2%} |")
    report += ["","## 因素如何进入模型","","- 实力底座：2014年至开赛日前的真实国家队赛果，三年半衰期、赛事权重、正则化攻防 Poisson；不用 Elo。",
               "- 当前状态：12份 FIFA 官方赛后报告的 xG/xGA，经每个对手的历史攻防强度校正后收缩；不是简单数进球。",
               "- 逐分钟：2018世界杯拟合、2022世界杯时间外验证的射门、xG、犯规、牌、点球、角球、压迫、伤停、换人分钟曲线；比赛状态和红牌实时改变后续危险率。",
               "- 球员：FIFA 2026真实出场时间、射门、进球、传球、穿线、传中和推进；StatsBomb 2022仅作衰减先验。没有任何游戏属性。",
               f"- 裁判：Elfath职业样本与本届3场样本做经验贝叶斯收缩，得到全场黄牌 {ref['yellow_per_match']:.2f}、红牌 {ref['red_per_match']:.3f}、点球 {ref['penalties_per_match']:.3f}。",
               f"- 负荷：英格兰已赛 {profiles['England']['minutes']} 分钟、阿根廷 {profiles['Argentina']['minutes']} 分钟；路线测得约 {travel['England']:.0f}/{travel['Argentina']:.0f} km。旅行效应没有稳定同口径系数，故只披露、不强塞入基准。",
               "- 环境：闭顶、天然草、约22.2°C，天气和海拔乘数均设为1。阵型影响通过真实推进、压迫、传中、穿线与三区接球实现，不另加主观‘战术加成’。","",
               "## 验证与限制","",f"- 2018→2022留出校准：射门实际/预测 {dynamics['validation']['shots']['calibration_ratio_actual_over_predicted']:.3f}，xG {dynamics['validation']['xg']['calibration_ratio_actual_over_predicted']:.3f}，进球 {dynamics['validation']['goals']['calibration_ratio_actual_over_predicted']:.3f}。换人、伤停和压迫存在明显届次/供应商定义漂移，结果中保留但不让它们决定胜负。",
               "- 首发在截点仍为预测阵容；Rice已由英格兰方面确认可出场，Romero与Paredes的轻微疲劳/碰撞没有被当成伤缺。对应缺阵只保留在压力测试中。官方首发发布后仍应立即重跑。",
               "- 精确到某一分钟的列是危险率，不是断言该分钟一定发生某事。罕见事件（红牌、点球、伤病）的区间远宽于普通 Monte Carlo 抽样误差。","",
               "## 数据来源","","- FIFA Training Centre 2026比赛报告中心：https://www.fifatrainingcentre.com/en/fifa-world-cup-2026/match-report-hub.php",
               "- FIFA淘汰赛报告中心：https://www.fifatrainingcentre.com/en/fifa-world-cup-2026/match-report-hub-knockout-stage.php",
               "- StatsBomb Open Data：https://github.com/statsbomb/open-data",
               "- FIFA阿根廷战术分析：https://www.fifatrainingcentre.com/en/fifa-world-cup-2026/how-argentina-create-the-conditions-for-messi-to-thrive.php",
               "- FIFA英格兰低位组织/凯恩回撤：https://www.fifatrainingcentre.com/en/fifa-world-cup-2026/england-low-build-up-and-kane-dropping-deep.php",
               "- 美国足协裁判指派：https://www.ussoccer.com/stories/2026/07/federation/all-american-referee-crew-argentina-england-fifa-world-cup-semifinal-atlanta"]
    (outdir/"real_data_engine_report.md").write_text("\n".join(report),encoding="utf-8")
    print(json.dumps({"output":str(outdir),"england_win":h90,"draw":draw,"argentina_win":a90,"england_advance":hadv,"xg":[float(np.mean(hg)),float(np.mean(ag))]},ensure_ascii=False))


if __name__=="__main__": main()
