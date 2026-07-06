#!/usr/bin/env python3
"""Freeze executable Polymarket books for the July 5 World Cup matches."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "polymarket_snapshot_0705.json"
GAMMA = "https://gamma-api.polymarket.com/events"
CLOB = "https://clob.polymarket.com/book"
SLUGS = ["fifwc-bra-nor-2026-07-05", "fifwc-mex-eng-2026-07-05"]
SUPPORTED = {"spreads", "totals", "both_teams_to_score", "soccer_team_totals"}


def get_json(url: str) -> object:
    last_error = None
    for attempt in range(5):
        try:
            request = Request(url, headers={"Accept": "application/json", "User-Agent": "wc2026-research/3.0"})
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception as error:  # Network endpoints occasionally reset bursty CLOB reads.
            last_error = error
            time.sleep(0.5 * 2**attempt)
    raise RuntimeError(f"Failed after retries: {url}") from last_error


def event(slug: str) -> dict:
    result = get_json(f"{GAMMA}?{urlencode({'slug': slug})}")
    if not isinstance(result, list) or len(result) != 1:
        raise RuntimeError(f"Expected one Gamma event for {slug}, received {len(result)}")
    return result[0]


def book(token_id: str) -> dict:
    raw = get_json(f"{CLOB}?{urlencode({'token_id': token_id})}")
    bids = sorted(
        ({"price": float(x["price"]), "size": float(x["size"])} for x in raw.get("bids", [])),
        key=lambda x: x["price"],
        reverse=True,
    )
    asks = sorted(
        ({"price": float(x["price"]), "size": float(x["size"])} for x in raw.get("asks", [])),
        key=lambda x: x["price"],
    )
    return {
        "best_bid": bids[0]["price"] if bids else None,
        "best_ask": asks[0]["price"] if asks else None,
        "bids": bids[:10],
        "asks": asks[:10],
        "tick_size": float(raw["tick_size"]),
        "timestamp": raw.get("timestamp"),
    }


def market_record(market: dict, market_type: str) -> dict:
    outcomes = json.loads(market["outcomes"])
    token_ids = json.loads(market["clobTokenIds"])
    outcome_prices = [float(x) for x in json.loads(market["outcomePrices"])]
    books = {outcome: book(token_id) for outcome, token_id in zip(outcomes, token_ids)}
    schedule = market.get("feeSchedule") or {}
    return {
        "id": market["id"],
        "slug": market["slug"],
        "question": market["question"],
        "market_type": market_type,
        "line": float(market["line"]) if market.get("line") is not None else None,
        "outcomes": outcomes,
        "token_ids": token_ids,
        "outcome_prices": outcome_prices,
        "fee_schedule": schedule,
        "books": books,
        "liquidity": float(market.get("liquidityNum") or market.get("liquidity") or 0),
        "volume": float(market.get("volumeNum") or market.get("volume") or 0),
        "updated_at": market.get("updatedAt"),
    }


def is_core_market(market: dict) -> bool:
    market_type = market.get("sportsMarketType")
    line = abs(float(market.get("line") or 0))
    if market_type == "spreads":
        return line <= 2.5
    if market_type == "totals":
        return 1.5 <= line <= 4.5
    return market_type in {"both_teams_to_score", "soccer_team_totals"}


def main() -> None:
    snapshot = {
        "as_of_beijing": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
        "gamma_api": GAMMA,
        "clob_api": CLOB,
        "matches": [],
    }
    for slug in SLUGS:
        main_event = event(slug)
        more_event = event(f"{slug}-more-markets")
        records = []
        for market in main_event["markets"]:
            records.append(market_record(market, "match_1x2"))
        for market in more_event["markets"]:
            market_type = market.get("sportsMarketType")
            if market_type in SUPPORTED and is_core_market(market):
                records.append(market_record(market, market_type))
        snapshot["matches"].append(
            {
                "event_slug": slug,
                "title": main_event["title"],
                "kickoff_utc": main_event["endDate"],
                "event_url": f"https://polymarket.com/sports/world-cup/{slug}",
                "markets": records,
            }
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} at {snapshot['as_of_beijing']}")
    for match in snapshot["matches"]:
        print(match["title"], len(match["markets"]), "supported markets")


if __name__ == "__main__":
    main()
