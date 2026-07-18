#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASE_SCRIPT = REPO / "yanyawei" / "20260711" / "scripts" / "refresh_markets_0711.py"

spec = importlib.util.spec_from_file_location("refresh0711", BASE_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load {BASE_SCRIPT}")
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)

refresh.ROOT = ROOT
refresh.OUTPUT = ROOT / "data" / "polymarket_snapshot_0718.json"
refresh.EVENTS = [
    "fifwc-fra-eng-2026-07-18",
    "fifwc-esp-arg-2026-07-19",
]


if __name__ == "__main__":
    refresh.main()
