#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASE_SCRIPT = REPO / "yanyawei" / "20260711" / "scripts" / "build_models_0711.py"

spec = importlib.util.spec_from_file_location("model0711", BASE_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {BASE_SCRIPT}")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

build.ROOT = ROOT
build.RAW = ROOT / "data" / "raw"
build.GOALSCORERS = build.RAW / "goalscorers.csv"
build.SHOOTOUTS = build.RAW / "shootouts.csv"
build.EXTRA_TIME_VERIFICATION = ROOT / "data" / "extra_time_verification_0719.json"
build.diagnostics = {}
build.original_rows_for_p3 = []
build.extra_time_candidate_keys = set()

build.model.SEED = 20260719
build.model.CUTOFF = date(2026, 7, 19)
build.model.RESULTS_CACHE = build.RAW / "results.csv"
build.model.P3_PATH = REPO / "yanyawei" / "20260709" / "data" / "fifa_match_stats_0709.json"
build.model.OUTPUT_PATH = ROOT / "data" / "model_results_0719.json"
build.model.BACKTEST_PATH = ROOT / "data" / "model_backtest_0719.json"
build.model.TARGETS = [
    {
        "id": "spain_argentina_2026-07-19",
        "home": "Spain",
        "away": "Argentina",
        "neutral": True,
        "venue": "New York New Jersey World Cup final venue",
        "venue_context": "neutral venue; final-match tactical and weather uncertainty",
        "uncertainty_widening": 0.010,
    },
]

_base_uncertainty_intervals = build.model.uncertainty_intervals


def uncertainty_intervals_without_disagreement(
    home_lambda,
    away_lambda,
    _disagreement,
    rng,
    contextual_widening=0.0,
):
    """Keep scenario risk, but do not widen it from model-component disagreement."""
    return _base_uncertainty_intervals(
        home_lambda,
        away_lambda,
        0.0,
        rng,
        contextual_widening=contextual_widening,
    )


build.model.uncertainty_intervals = uncertainty_intervals_without_disagreement


if __name__ == "__main__":
    build.main()
    output = json.loads(build.model.OUTPUT_PATH.read_text(encoding="utf-8"))
    output["metadata"]["model_version"] = "production-light-p1-p2-p3-0719-90m-v1"
    output["metadata"]["p3_freshness_note"] = (
        "P3 FIFA xG reports end on 2026-07-07. Semifinal xG figures found in secondary previews "
        "are not injected into the independent model because no audited FIFA 90-minute report artifact "
        "was available. Recent semifinal scores are included in P1/P2."
    )
    output["metadata"]["disagreement_policy"] = (
        "No internal/external or model-component disagreement measure widens uncertainty or lowers "
        "p_trade. Disagreement is diagnostic only. Scenario ranges retain fixed model-risk and "
        "contextual widening."
    )
    output["metadata"]["limitations"] = [
        item
        for item in output["metadata"]["limitations"]
        if not item.startswith("Azteca altitude")
    ]
    for match in output["matches"]:
        match["uncertainty"]["context_note"] = (
            "Final-match environment and lineup uncertainty widen the diagnostic scenario range only; "
            "no directional goal adjustment is applied."
        )
    build.model.OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
