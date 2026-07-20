"""Build real-data football dynamics from StatsBomb 2018/2022 World Cups.

The model estimates generic minute, score-state, red-card and knockout effects.
2018 is used as the development sample and 2022 as the time-ordered holdout;
pooled estimates are written only after validation metrics are computed.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import unicodedata
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "statsbomb_world_cups"
CURATED = ROOT / "data" / "curated"
OUTPUT = ROOT / "outputs" / "real_data_engine"

TARGETS = [
    "shots", "xg", "goals", "fouls", "yellow_cards", "red_cards",
    "penalties", "corners", "substitutions", "injuries", "pressures",
]
CAT_FEATURES = ["minute_bin", "score_state", "red_diff"]
NUM_FEATURES = ["knockout"]


def clean_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    return "".join(c for c in value if not unicodedata.combining(c)).lower()


def regulation_minute(event: dict) -> int | None:
    period = int(event.get("period", 0))
    minute = int(event.get("minute", 0))
    if period == 1:
        return min(minute + 1, 45)
    if period == 2:
        return min(minute + 1, 95)
    return None


def minute_bin(minute: int) -> str:
    if minute <= 15:
        return "01-15"
    if minute <= 30:
        return "16-30"
    if minute <= 45:
        return "31-45"
    if minute <= 60:
        return "46-60"
    if minute <= 75:
        return "61-75"
    return "76-95"


def card_name(event: dict) -> str:
    for container in ("foul_committed", "bad_behaviour"):
        card = event.get(container, {}).get("card")
        if card:
            return str(card.get("name", ""))
    return ""


def load_match_events(season: str) -> tuple[list[dict], dict[int, list[dict]]]:
    with gzip.open(RAW / f"matches_{season}.json.gz", "rt", encoding="utf-8") as fh:
        matches = json.load(fh)
    events = {}
    for match in matches:
        match_id = int(match["match_id"])
        with gzip.open(RAW / season / "events" / f"{match_id}.json.gz", "rt", encoding="utf-8") as fh:
            events[match_id] = json.load(fh)
    return matches, events


def extra_time_and_shootout_summary(all_event_sets: list[list[dict]]) -> dict:
    """Empirical extra-time rate and shootout conversion from the same Cups."""
    regulation = defaultdict(float)
    extra_time = defaultdict(float)
    et_matches = 0
    shootout_taken = shootout_scored = 0
    shootout_by_team = defaultdict(lambda: {"taken": 0, "scored": 0})
    for events in all_event_sets:
        periods = {int(e.get("period", 0)) for e in events}
        if 3 in periods or 4 in periods:
            et_matches += 1
        for event in events:
            period = int(event.get("period", 0))
            typ = event.get("type", {}).get("name", "")
            bucket = regulation if period in (1, 2) else extra_time if period in (3, 4) else None
            if period == 5 and typ == "Shot":
                shootout_taken += 1
                scored = int(event.get("shot", {}).get("outcome", {}).get("name") == "Goal")
                shootout_scored += scored
                team = event.get("team", {}).get("name", "Unknown")
                shootout_by_team[team]["taken"] += 1
                shootout_by_team[team]["scored"] += scored
            if bucket is None:
                continue
            if typ == "Shot":
                bucket["shots"] += 1
                bucket["xg"] += float(event.get("shot", {}).get("statsbomb_xg", 0.0))
                bucket["goals"] += int(event.get("shot", {}).get("outcome", {}).get("name") == "Goal")
                bucket["penalties"] += int(event.get("shot", {}).get("type", {}).get("name") == "Penalty")
            elif typ == "Foul Committed":
                bucket["fouls"] += 1
            elif typ == "Pass" and event.get("pass", {}).get("type", {}).get("name") == "Corner":
                bucket["corners"] += 1
            elif typ == "Substitution":
                bucket["substitutions"] += 1
            elif typ == "Injury Stoppage":
                bucket["injuries"] += 1
            elif typ == "Pressure":
                bucket["pressures"] += 1
            card = card_name(event)
            bucket["yellow_cards"] += int(card in ("Yellow Card", "Second Yellow"))
            bucket["red_cards"] += int(card in ("Red Card", "Second Yellow"))

    # Only compare regulation and ET within matches that actually reached ET.
    # The event totals above include all regulation matches, so recompute the
    # exposure-adjusted denominator using the pooled regulation base rate.
    pooled_team_minutes = len(all_event_sets) * 2 * 90
    et_team_minutes = et_matches * 2 * 30
    multipliers = {}
    for target in TARGETS:
        reg_rate = regulation[target] / max(pooled_team_minutes, 1)
        et_rate = extra_time[target] / max(et_team_minutes, 1)
        # Rare-event shrinkage: 600 pseudo ET team-minutes at regulation rate.
        shrunk_et = (extra_time[target] + 600 * reg_rate) / max(et_team_minutes + 600, 1)
        multipliers[target] = float(shrunk_et / max(reg_rate, 1e-12))
    return {
        "matches_reaching_extra_time": et_matches,
        "rate_multiplier_vs_regulation": multipliers,
        "shootout_penalties": shootout_taken,
        "shootout_goals": shootout_scored,
        "shootout_conversion": float((shootout_scored + 8.0) / (shootout_taken + 10.0)),
        "shootout_by_team": {
            team: {
                **counts,
                "beta_binomial_posterior": float((counts["scored"] + 8.0) / (counts["taken"] + 10.0)),
            }
            for team, counts in sorted(shootout_by_team.items())
        },
    }


def match_minute_rows(season: str, match: dict, events: list[dict]) -> list[dict]:
    home = match["home_team"]["home_team_name"]
    away = match["away_team"]["away_team_name"]
    teams = (home, away)
    knockout = float(match["competition_stage"]["name"] != "Group Stage")
    counts = defaultdict(lambda: defaultdict(float))
    goal_events = []
    red_events = []

    for event in sorted(events, key=lambda x: int(x.get("index", 0))):
        minute = regulation_minute(event)
        if minute is None:
            continue
        team = event.get("team", {}).get("name")
        event_type = event.get("type", {}).get("name", "")
        if team not in teams:
            continue
        key = (team, minute)
        if event_type == "Shot":
            counts[key]["shots"] += 1
            counts[key]["xg"] += float(event.get("shot", {}).get("statsbomb_xg", 0.0))
            if event.get("shot", {}).get("outcome", {}).get("name") == "Goal":
                counts[key]["goals"] += 1
                goal_events.append((minute, team))
            if event.get("shot", {}).get("type", {}).get("name") == "Penalty":
                counts[key]["penalties"] += 1
        elif event_type == "Foul Committed":
            counts[key]["fouls"] += 1
        elif event_type == "Pass" and event.get("pass", {}).get("type", {}).get("name") == "Corner":
            counts[key]["corners"] += 1
        elif event_type == "Substitution":
            counts[key]["substitutions"] += 1
        elif event_type == "Injury Stoppage":
            counts[key]["injuries"] += 1
        elif event_type == "Pressure":
            counts[key]["pressures"] += 1
        elif event_type == "Own Goal For":
            counts[key]["goals"] += 1
            goal_events.append((minute, team))
        elif event_type == "Own Goal Against":
            beneficiary = away if team == home else home
            counts[(beneficiary, minute)]["goals"] += 1
            goal_events.append((minute, beneficiary))

        card = card_name(event)
        if card in ("Yellow Card", "Second Yellow"):
            counts[key]["yellow_cards"] += 1
        if card in ("Red Card", "Second Yellow"):
            counts[key]["red_cards"] += 1
            red_events.append((minute, team))

    rows = []
    for team in teams:
        opponent = away if team == home else home
        for minute in range(1, 96):
            gf = sum(1 for m, t in goal_events if m < minute and t == team)
            ga = sum(1 for m, t in goal_events if m < minute and t == opponent)
            team_red = sum(1 for m, t in red_events if m < minute and t == team)
            opp_red = sum(1 for m, t in red_events if m < minute and t == opponent)
            row = {
                "season": season,
                "match_id": int(match["match_id"]),
                "team": team,
                "opponent": opponent,
                "minute": minute,
                "minute_bin": minute_bin(minute),
                "score_state": "leading" if gf > ga else "trailing" if gf < ga else "drawing",
                "red_diff": str(max(-1, min(1, opp_red - team_red))),
                "knockout": knockout,
            }
            for target in TARGETS:
                row[target] = float(counts[(team, minute)].get(target, 0.0))
            rows.append(row)
    return rows


def build_player_history(season: str, match: dict, events: list[dict]) -> list[dict]:
    if season != "2022":
        return []
    teams = {match["home_team"]["home_team_name"], match["away_team"]["away_team_name"]}
    wanted = teams & {"England", "Argentina"}
    if not wanted:
        return []
    max_period = max(int(e.get("period", 0)) for e in events)
    end_minute = 120 if max_period >= 4 else 90
    data = defaultdict(lambda: defaultdict(float))
    starts: dict[tuple[str, str], int] = {}
    ends: dict[tuple[str, str], int] = {}
    roles: dict[tuple[str, str], str] = {}

    for event in sorted(events, key=lambda x: int(x.get("index", 0))):
        team = event.get("team", {}).get("name")
        if team not in wanted:
            continue
        typ = event.get("type", {}).get("name", "")
        minute = min(int(event.get("minute", 0)), end_minute)
        if typ == "Starting XI":
            for item in event.get("tactics", {}).get("lineup", []):
                name = item["player"]["name"]
                starts[(team, name)] = 0
                roles[(team, name)] = item["position"]["name"]
        if typ == "Substitution":
            name = event.get("player", {}).get("name")
            replacement = event.get("substitution", {}).get("replacement", {}).get("name")
            if name:
                ends[(team, name)] = minute
            if replacement:
                starts[(team, replacement)] = minute
                roles[(team, replacement)] = event.get("position", {}).get("name", "Substitute")

        player = event.get("player", {}).get("name")
        if not player:
            continue
        key = (team, player)
        if typ == "Shot":
            data[key]["shots"] += 1
            data[key]["xg"] += float(event.get("shot", {}).get("statsbomb_xg", 0.0))
            if event.get("shot", {}).get("outcome", {}).get("name") == "Goal":
                data[key]["goals"] += 1
        elif typ == "Pass":
            data[key]["passes"] += 1
            if event.get("pass", {}).get("shot_assist") or event.get("pass", {}).get("goal_assist"):
                data[key]["key_passes"] += 1
            if event.get("pass", {}).get("cross"):
                data[key]["crosses"] += 1
        elif typ == "Pressure":
            data[key]["pressures"] += 1
        elif typ == "Foul Committed":
            data[key]["fouls"] += 1
        elif typ == "Interception":
            data[key]["interceptions"] += 1
        elif typ == "Duel" and event.get("duel", {}).get("type", {}).get("name") == "Tackle":
            data[key]["tackles"] += 1
        card = card_name(event)
        if card:
            data[key]["cards"] += 1

    rows = []
    for key in set(data) | set(starts):
        team, player = key
        start = starts.get(key, end_minute)
        end = ends.get(key, end_minute)
        minutes = max(0, end - start)
        row = {"season": season, "match_id": int(match["match_id"]), "team": team,
               "player": player, "player_normalized": clean_name(player),
               "position": roles.get(key, ""), "minutes": minutes}
        for metric in ("shots", "xg", "goals", "passes", "key_passes", "crosses",
                       "pressures", "fouls", "interceptions", "tackles", "cards"):
            row[metric] = float(data[key].get(metric, 0.0))
        rows.append(row)
    return rows


class RegularizedPoisson:
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.columns: list[str] = []
        self.beta: np.ndarray | None = None

    def _design(self, frame: pd.DataFrame, fit: bool) -> np.ndarray:
        x = pd.get_dummies(frame[CAT_FEATURES + NUM_FEATURES], columns=CAT_FEATURES, dtype=float)
        if fit:
            self.columns = list(x.columns)
        x = x.reindex(columns=self.columns, fill_value=0.0)
        return np.column_stack([np.ones(len(x)), x.to_numpy(float)])

    def fit(self, frame: pd.DataFrame, y: pd.Series) -> "RegularizedPoisson":
        x = self._design(frame, fit=True)
        target = y.to_numpy(float)
        beta = np.zeros(x.shape[1])
        beta[0] = math.log(max(float(target.mean()), 1e-6))
        m = np.zeros_like(beta)
        v = np.zeros_like(beta)
        lr = 0.04
        for step in range(1, 901):
            z = np.clip(x @ beta, -14, 8)
            mu = np.exp(z)
            grad = x.T @ (mu - target) / len(target)
            grad[1:] += self.alpha * beta[1:] / max(x.shape[1] - 1, 1)
            m = 0.9 * m + 0.1 * grad
            v = 0.999 * v + 0.001 * grad * grad
            mh = m / (1 - 0.9**step)
            vh = v / (1 - 0.999**step)
            beta -= lr * mh / (np.sqrt(vh) + 1e-8)
            if step in (300, 600):
                lr *= 0.55
        self.beta = beta
        return self

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        if self.beta is None:
            raise RuntimeError("model not fitted")
        return np.exp(np.clip(self._design(frame, fit=False) @ self.beta, -14, 8))


def poisson_deviance(y: np.ndarray, pred: np.ndarray) -> float:
    pred = np.clip(pred, 1e-12, None)
    term = np.where(y > 0, y * np.log(np.clip(y / pred, 1e-12, None)), 0.0)
    return float(2 * np.mean(term - (y - pred)))


def validation_and_models(df: pd.DataFrame) -> tuple[dict, dict]:
    train = df[df.season == "2018"]
    test = df[df.season == "2022"]
    validation = {}
    models = {}
    for target in TARGETS:
        alpha = 1.5 if target in {"red_cards", "penalties", "injuries"} else 0.5
        model = RegularizedPoisson(alpha)
        model.fit(train[CAT_FEATURES + NUM_FEATURES], train[target])
        pred = np.clip(model.predict(test[CAT_FEATURES + NUM_FEATURES]), 1e-8, None)
        baseline = np.full(len(test), max(float(train[target].mean()), 1e-8))
        validation[target] = {
            "holdout_actual_total": float(test[target].sum()),
            "holdout_predicted_total": float(pred.sum()),
            "calibration_ratio_actual_over_predicted": float(test[target].sum() / max(pred.sum(), 1e-8)),
            "poisson_deviance": poisson_deviance(test[target].to_numpy(float), pred),
            "null_poisson_deviance": poisson_deviance(test[target].to_numpy(float), baseline),
        }
        pooled = RegularizedPoisson(alpha)
        pooled.fit(df[CAT_FEATURES + NUM_FEATURES], df[target])
        models[target] = pooled
    return validation, models


def factor_tables(df: pd.DataFrame, models: dict) -> dict:
    result = {"minute_multiplier": {}, "score_state_multiplier": {},
              "red_diff_multiplier": {}, "knockout_multiplier": {},
              "base_rate_per_team_minute": {}}
    for target in TARGETS:
        rates = df.groupby("minute")[target].sum() / df.groupby("minute").size()
        smoothed = rates.rolling(7, center=True, min_periods=1).mean()
        smoothed = (smoothed + 0.15 * rates.mean()) / 1.15
        mult = smoothed / max(smoothed.mean(), 1e-12)
        result["minute_multiplier"][target] = {str(int(k)): float(v) for k, v in mult.items()}
        result["base_rate_per_team_minute"][target] = float(df[target].mean())

        model = models[target]
        reference = {"minute_bin": "31-45", "score_state": "drawing", "red_diff": "0", "knockout": 1.0}
        ref_pred = float(model.predict(pd.DataFrame([reference]))[0])
        state_map = {}
        for state in ("leading", "drawing", "trailing"):
            row = dict(reference, score_state=state)
            state_map[state] = float(model.predict(pd.DataFrame([row]))[0] / max(ref_pred, 1e-12))
        result["score_state_multiplier"][target] = state_map
        red_map = {}
        # red_diff is deliberately categorical ("-1", "0", "1").  Comparing
        # it with an integer silently selected an empty reference sample and
        # propagated NaNs into every red-card state multiplier.
        base_red = df[df.red_diff == "0"]
        base_rate = float(base_red[target].mean())
        for red in ("-1", "0", "1"):
            part = df[df.red_diff == red]
            if red == "0":
                red_map[red] = 1.0
            else:
                # Only 182 team-minutes are played at each non-zero red state.
                # Shrink the raw rate ratio toward one with 400 neutral pseudo-minutes.
                n = len(part)
                shrunk_rate = (float(part[target].sum()) + 400 * base_rate) / max(n + 400, 1)
                red_map[red] = float(shrunk_rate / max(base_rate, 1e-12))
        result["red_diff_multiplier"][target] = red_map
        group_row = dict(reference, knockout=0.0)
        result["knockout_multiplier"][target] = float(ref_pred / max(float(model.predict(pd.DataFrame([group_row]))[0]), 1e-12))

    # Empirical shot-quality state effect, shrunk to the pooled mean.
    quality = {}
    overall = float(df.xg.sum() / max(df.shots.sum(), 1.0))
    for state in ("leading", "drawing", "trailing"):
        part = df[df.score_state == state]
        raw = float((part.xg.sum() + 100 * overall) / (part.shots.sum() + 100))
        quality[state] = raw / overall
    result["shot_quality_by_score_state"] = quality
    return result


def main() -> None:
    CURATED.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    minute_rows = []
    player_rows = []
    source_counts = {}
    all_event_sets = []
    for season in ("2018", "2022"):
        matches, event_map = load_match_events(season)
        source_counts[season] = {"matches": len(matches), "events": sum(len(x) for x in event_map.values())}
        all_event_sets.extend(event_map.values())
        for match in matches:
            events = event_map[int(match["match_id"])]
            minute_rows.extend(match_minute_rows(season, match, events))
            player_rows.extend(build_player_history(season, match, events))

    df = pd.DataFrame(minute_rows)
    players = pd.DataFrame(player_rows)
    minute_path = CURATED / "statsbomb_wc2018_2022_team_minute_events.csv.gz"
    player_path = CURATED / "statsbomb_2022_eng_arg_player_history.csv"
    df.to_csv(minute_path, index=False, compression="gzip")
    players.to_csv(player_path, index=False, encoding="utf-8-sig")

    validation, models = validation_and_models(df)
    factors = factor_tables(df, models)
    payload = {
        "method": "Poisson event-rate models; 2018 development, 2022 chronological holdout, pooled refit",
        "source_counts": source_counts,
        "rows": len(df),
        "validation": validation,
        "factors": factors,
        "extra_time_and_shootout": extra_time_and_shootout_summary(all_event_sets),
    }
    out = OUTPUT / "statsbomb_historical_dynamics.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"minute_rows": len(df), "player_rows": len(players), "output": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
