from __future__ import annotations

import math
from copy import deepcopy

import numpy as np

from .score import core_markets, dc_matrix


def _effective(value: float, availability: float, replacement_level: float = 70.0) -> float:
    return value * availability + replacement_level * (1.0 - availability)


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("empty positional group in projected XI")
    return float(np.mean(values))


def team_profile(players: list[dict]) -> dict:
    """Translate FC-style attributes into comparison scores, not probabilities."""
    by_role: dict[str, list[dict]] = {"GK": [], "DEF": [], "MID": [], "FWD": []}
    for player in players:
        by_role[player["role"]].append(player)

    attack, defense, control, physical = {}, {}, {}, {}
    for role, group in by_role.items():
        if role == "GK":
            attack[role] = _mean([_effective(p["ovr"], p.get("availability", 1.0)) for p in group])
            defense[role] = attack[role]
            control[role] = attack[role]
            physical[role] = attack[role]
            continue
        a_values, d_values, c_values, p_values = [], [], [], []
        for p in group:
            av = float(p.get("availability", 1.0))
            if role == "FWD":
                a = .38*p["sho"] + .23*p["dri"] + .19*p["pas"] + .12*p["pac"] + .08*p["phy"]
                d = .40*p["def"] + .30*p["phy"] + .20*p["pac"] + .10*p["pas"]
            elif role == "MID":
                a = .22*p["sho"] + .30*p["pas"] + .23*p["dri"] + .10*p["pac"] + .15*p["phy"]
                d = .35*p["def"] + .25*p["phy"] + .20*p["pas"] + .20*p["pac"]
            else:
                a = .20*p["pas"] + .15*p["dri"] + .15*p["pac"] + .10*p["sho"] + .40*p["def"]
                d = .50*p["def"] + .25*p["phy"] + .15*p["pac"] + .10*p["pas"]
            c = .40*p["pas"] + .35*p["dri"] + .15*p["phy"] + .10*p["pac"]
            ph = .60*p["phy"] + .40*p["pac"]
            a_values.append(_effective(a, av)); d_values.append(_effective(d, av))
            c_values.append(_effective(c, av)); p_values.append(_effective(ph, av))
        attack[role] = _mean(a_values); defense[role] = _mean(d_values)
        control[role] = _mean(c_values); physical[role] = _mean(p_values)

    team_attack = .45*attack["FWD"] + .35*attack["MID"] + .20*attack["DEF"]
    team_defense = .50*defense["DEF"] + .30*defense["MID"] + .20*defense["GK"]
    team_control = .50*control["MID"] + .25*control["FWD"] + .25*control["DEF"]
    team_physical = .40*physical["MID"] + .30*physical["FWD"] + .30*physical["DEF"]
    strength = .40*team_attack + .40*team_defense + .15*team_control + .05*team_physical
    return {
        "attack": team_attack, "defense": team_defense, "control": team_control,
        "physical": team_physical, "strength": strength,
        "starting_xi_ovr": _mean([float(p["ovr"]) for p in players]),
    }


def apply_game_adjustment(base: dict, fixture: dict, game: dict, ratings: dict,
                          max_goals: int) -> tuple[dict, dict, dict]:
    home, away = fixture["home"], fixture["away"]
    profiles = {team: team_profile(ratings["teams"][team]["players"]) for team in (home, away)}
    method = game["method"]
    home_spec, away_spec = game["teams"][home], game["teams"][away]

    rating_edge = profiles[home]["strength"] - profiles[away]["strength"]
    raw_rating_shift = (float(method["game_rating_reliability"]) *
                        float(method["rating_edge_scale"]) * rating_edge)
    cap = float(method["max_log_lambda_shift"])
    rating_shift = float(np.clip(raw_rating_shift, -cap, cap))

    home_context = (float(home_spec["fitness_multiplier"]) *
                    float(home_spec["formation_attack_multiplier"]) *
                    float(home_spec["bench_depth_multiplier"]) /
                    float(away_spec["formation_defense_multiplier"]))
    away_context = (float(away_spec["fitness_multiplier"]) *
                    float(away_spec["formation_attack_multiplier"]) *
                    float(away_spec["bench_depth_multiplier"]) /
                    float(home_spec["formation_defense_multiplier"]))
    referee = math.sqrt(float(method["referee_total_goal_multiplier"]))

    home_log = float(np.clip(rating_shift + math.log(home_context) + math.log(referee), -cap, cap))
    away_log = float(np.clip(-rating_shift + math.log(away_context) + math.log(referee), -cap, cap))
    lh = float(base["lambda_home"] * math.exp(home_log))
    la = float(base["lambda_away"] * math.exp(away_log))
    matrix = dc_matrix(lh, la, float(base["rho"]), max_goals)

    adjusted = deepcopy(base)
    adjusted.update({
        "lambda_home": lh, "lambda_away": la, "matrix": matrix,
        "markets": core_markets(matrix),
        "pre_game_attribute_lambda_home": float(base["lambda_home"]),
        "pre_game_attribute_lambda_away": float(base["lambda_away"]),
    })
    scenario_cfg = {
        "uncertainty_lambda_pct": float(method.get("base_uncertainty_lambda_pct", 0.15)) +
                                  float(method["referee_uncertainty_extra"]),
        "uncertainty_share_shift": float(method.get("base_uncertainty_share_shift", 0.07)) + 0.01,
    }
    audit = {
        "profiles": profiles,
        "rating_edge_home_minus_away": rating_edge,
        "rating_log_shift": rating_shift,
        "home_context_multiplier": home_context,
        "away_context_multiplier": away_context,
        "referee_total_goal_multiplier": float(method["referee_total_goal_multiplier"]),
        "home_lambda_multiplier": math.exp(home_log),
        "away_lambda_multiplier": math.exp(away_log),
        "projected_formations": {home: home_spec["formation"], away: away_spec["formation"]},
        "starting_xi_status": {home: home_spec["starting_xi_status"], away: away_spec["starting_xi_status"]},
    }
    return adjusted, audit, scenario_cfg
