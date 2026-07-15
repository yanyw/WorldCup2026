#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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
build.EXTRA_TIME_VERIFICATION = ROOT / "data" / "extra_time_verification_0715.json"
build.diagnostics = {}
build.original_rows_for_p3 = []
build.extra_time_candidate_keys = set()

build.model.SEED = 20260715
build.model.CUTOFF = date(2026, 7, 15)
build.model.RESULTS_CACHE = build.RAW / "results.csv"
build.model.P3_PATH = REPO / "yanyawei" / "20260709" / "data" / "fifa_match_stats_0709.json"
build.model.OUTPUT_PATH = ROOT / "data" / "model_results_0715.json"
build.model.BACKTEST_PATH = ROOT / "data" / "model_backtest_0715.json"
build.model.TARGETS = [
    {
        "id": "england_argentina_2026-07-15",
        "home": "England",
        "away": "Argentina",
        "neutral": True,
        "venue": "Atlanta World Cup semi-final venue",
        "venue_context": "neutral venue; both teams played 120 minutes on 11 July",
        "uncertainty_widening": 0.015,
    }
]


if __name__ == "__main__":
    build.main()
