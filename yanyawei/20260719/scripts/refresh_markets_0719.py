#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
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
refresh.OUTPUT = ROOT / "data" / "polymarket_snapshot_0719.json"
refresh.EVENTS = [
    "fifwc-esp-arg-2026-07-19",
]

_base_record = refresh.record


def record_with_audit_fields(market: dict, market_type: str) -> dict:
    item = _base_record(market, market_type)
    condition_id = market.get("conditionId")
    clob_info = (
        refresh.get(f"https://clob.polymarket.com/clob-markets/{condition_id}")
        if condition_id
        else {}
    )
    item.update(
        {
            "description": market.get("description"),
            "resolution_source": market.get("resolutionSource"),
            "condition_id": condition_id,
            "fees_enabled": market.get("feesEnabled"),
            "clob_market_info": {
                "game_start_time": clob_info.get("gst"),
                "minimum_order_size": clob_info.get("mos"),
                "minimum_tick_size": clob_info.get("mts"),
                "maker_base_fee_bps": clob_info.get("mbf"),
                "taker_base_fee_bps": clob_info.get("tbf"),
                "fee_details": clob_info.get("fd") or {},
            },
        }
    )
    return item


refresh.record = record_with_audit_fields


if __name__ == "__main__":
    refresh.main()
    snapshot = json.loads(refresh.OUTPUT.read_text(encoding="utf-8"))
    if not snapshot["corner_market_search"]["market_slugs"]:
        snapshot["corner_market_search"]["result"] = (
            "no executable corner market found in the event market set"
        )
    refresh.OUTPUT.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
