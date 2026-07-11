#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import io
import json
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASE_SCRIPT = REPO / "yanyawei" / "20260709" / "scripts" / "build_models_0709.py"
BASE_P3 = REPO / "yanyawei" / "20260709" / "data" / "fifa_match_stats_0709.json"
RAW = ROOT / "data" / "raw"
GOALSCORERS = RAW / "goalscorers.csv"
SHOOTOUTS = RAW / "shootouts.csv"
EXTRA_TIME_VERIFICATION = ROOT / "data" / "extra_time_verification_0711.json"
GOALSCORERS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/goalscorers.csv"
SHOOTOUTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv"

spec = importlib.util.spec_from_file_location("model0709", BASE_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {BASE_SCRIPT}")
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)

model.SEED = 20260711
model.CUTOFF = date(2026, 7, 11)
model.RESULTS_CACHE = RAW / "results.csv"
model.P3_PATH = BASE_P3
model.OUTPUT_PATH = ROOT / "data" / "model_results_0711.json"
model.BACKTEST_PATH = ROOT / "data" / "model_backtest_0711.json"
model.TARGETS = [
    {
        "id": "norway_england_2026-07-11",
        "home": "Norway",
        "away": "England",
        "neutral": True,
        "venue": "Miami World Cup quarter-final venue",
        "venue_context": "neutral venue; heat and humidity treated as uncertainty only",
        "uncertainty_widening": 0.02,
    },
    {
        "id": "argentina_switzerland_2026-07-11",
        "home": "Argentina",
        "away": "Switzerland",
        "neutral": True,
        "venue": "Kansas City World Cup quarter-final venue",
        "venue_context": "neutral venue; weather and lineup uncertainty treated as uncertainty only",
        "uncertainty_widening": 0.015,
    },
]

diagnostics: dict = {}
original_rows_for_p3: list[dict] = []
extra_time_candidate_keys: set[tuple[str, str, str]] = set()


def download(path: Path, url: str) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 10_000:
        return path.read_bytes()
    request = urllib.request.Request(url, headers={"User-Agent": "WorldCup2026-90m-canonical/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read()
    path.write_bytes(payload)
    return payload


def key(date_text: str, home: str, away: str) -> tuple[str, str, str]:
    return date_text, home, away


def minute_value(value: str) -> int | None:
    value = (value or "").strip()
    if not value or value.upper() == "NA":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


original_load_results = model.load_results


def load_results_90(payload: bytes):
    global original_rows_for_p3, extra_time_candidate_keys
    rows, rejected = original_load_results(payload)
    original_rows_for_p3 = rows
    goals_payload = download(GOALSCORERS, GOALSCORERS_URL)
    shootouts_payload = download(SHOOTOUTS, SHOOTOUTS_URL)

    goal_map: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in csv.DictReader(io.StringIO(goals_payload.decode("utf-8-sig"))):
        goal_map[key(row["date"], row["home_team"], row["away_team"])].append(row)
    shootout_keys = {
        key(row["date"], row["home_team"], row["away_team"])
        for row in csv.DictReader(io.StringIO(shootouts_payload.decode("utf-8-sig")))
    }
    extra_time_candidate_keys = set(shootout_keys)
    verification = json.loads(EXTRA_TIME_VERIFICATION.read_text(encoding="utf-8"))
    verified = {
        key(row["date"], row["home"], row["away"]): row
        for row in verification["matches"]
        if row["verification_status"] == "VERIFIED"
    }
    extra_time_candidate_keys.update(verified)

    corrected = []
    correction_count = 0
    verified_count = 0
    excluded_scope_uncertain = 0
    extra_time_goals_removed = 0
    for row in rows:
        match_key = key(row["date"].isoformat(), row["home"], row["away"])
        goals = goal_map.get(match_key, [])
        minutes = [minute_value(goal["minute"]) for goal in goals]
        total_score = row["home_goals"] + row["away_goals"]
        complete = len(goals) == total_score and all(value is not None for value in minutes)
        known_extra_time = any(value is not None and value > 90 for value in minutes)

        verified_row = verified.get(match_key)
        if verified_row is not None:
            revised = dict(row)
            revised["home_goals"], revised["away_goals"] = verified_row["score_90"]
            corrected.append(revised)
            verified_count += 1
            if (revised["home_goals"], revised["away_goals"]) != (row["home_goals"], row["away_goals"]):
                correction_count += 1
                extra_time_goals_removed += total_score - revised["home_goals"] - revised["away_goals"]
            continue

        if match_key in shootout_keys or known_extra_time:
            extra_time_candidate_keys.add(match_key)
            excluded_scope_uncertain += 1
            continue

        if complete:
            home_90 = sum(1 for goal, minute in zip(goals, minutes) if minute <= 90 and goal["team"] == row["home"])
            away_90 = sum(1 for goal, minute in zip(goals, minutes) if minute <= 90 and goal["team"] == row["away"])
            if home_90 + away_90 != sum(1 for minute in minutes if minute <= 90):
                excluded_scope_uncertain += 1
                continue
            revised = dict(row)
            revised["home_goals"] = home_90
            revised["away_goals"] = away_90
            corrected.append(revised)
            verified_count += 1
        else:
            corrected.append(row)

    diagnostics.update(
        {
            "method": "Use independently verified score_90 for known extra-time matches; exclude unverified shootout/extra-time-risk rows. Goalscorer minutes are a detection and consistency check, not sole settlement evidence.",
            "rows_before": len(rows),
            "rows_after": len(corrected),
            "scope_verified_rows": verified_count,
            "score_rows_corrected": correction_count,
            "extra_time_goals_removed": extra_time_goals_removed,
            "scope_uncertain_rows_excluded": excluded_scope_uncertain,
            "goalscorers_source": GOALSCORERS_URL,
            "shootouts_source": SHOOTOUTS_URL,
            "external_verification_ledger": str(EXTRA_TIME_VERIFICATION),
            "externally_verified_extra_time_matches": len(verified),
        }
    )
    rejected = dict(rejected)
    rejected["scope_uncertain_rows_excluded"] = excluded_scope_uncertain
    return corrected, rejected


original_load_p3 = model.load_p3
P3_RESULT_NAME = {
    "USA": "United States",
    "Türkiye": "Turkey",
    "Cabo Verde": "Cape Verde",
    "Congo DR": "DR Congo",
    "Korea Republic": "South Korea",
    "Czechia": "Czech Republic",
    "IR Iran": "Iran",
    "Côte d'Ivoire": "Ivory Coast",
}


def load_p3_per90(all_results):
    rows = original_load_p3(original_rows_for_p3)
    kept = []
    excluded = 0
    for row in rows:
        row_key = (
            row["matched_completed_date"],
            P3_RESULT_NAME.get(row["home"], row["home"]),
            P3_RESULT_NAME.get(row["away"], row["away"]),
        )
        reverse_key = (row_key[0], row_key[2], row_key[1])
        if row_key in extra_time_candidate_keys or reverse_key in extra_time_candidate_keys:
            excluded += 1
            continue
        kept.append(row)
    diagnostics["p3_extra_time_reports_excluded"] = excluded
    diagnostics["p3_extra_time_policy"] = "Exclude 120-minute aggregate xG unless a verified 90-minute xG split is available."
    return kept


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    model.load_results = load_results_90
    model.load_p3 = load_p3_per90
    model.main()

    output = json.loads(model.OUTPUT_PATH.read_text(encoding="utf-8"))
    output["metadata"]["model_version"] = "production-light-p1-p2-p3-0711-90m-v2"
    output["metadata"]["canonical_90_minute"] = diagnostics
    output["metadata"]["scenario_p10_calibrated"] = False
    output["metadata"]["scenario_p10_label"] = "heuristic scenario percentile; not a calibrated lower bound"
    model.OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    backtest = json.loads(model.BACKTEST_PATH.read_text(encoding="utf-8"))
    backtest["canonical_90_minute"] = diagnostics
    backtest["selection_bias_note"] = "The current validation remains a single temporal holdout; nested walk-forward is not yet complete. Metrics are research diagnostics, not final production estimates."
    model.BACKTEST_PATH.write_text(json.dumps(backtest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(diagnostics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
