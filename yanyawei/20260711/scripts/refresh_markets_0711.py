#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "polymarket_snapshot_0711.json"
GAMMA = "https://gamma-api.polymarket.com/events"
CLOB = "https://clob.polymarket.com/book"
EVENTS = [
    "fifwc-nor-eng-2026-07-11",
    "fifwc-arg-che-2026-07-11",
]
SUPPORTED = {
    "spreads",
    "totals",
    "both_teams_to_score",
    "soccer_team_totals",
    "corners",
    "soccer_corners",
    "corner_spread",
    "corner_totals",
}


def get(url: str):
    error = None
    for attempt in range(5):
        try:
            request = Request(url, headers={"User-Agent": "wc2026-0711/1.0", "Accept": "application/json"})
            with urlopen(request, timeout=20) as response:
                return json.load(response)
        except Exception as exc:
            error = exc
            time.sleep(0.5 * 2**attempt)
    raise RuntimeError(url) from error


def event(slug: str) -> dict:
    payload = get(GAMMA + "?" + urlencode({"slug": slug}))
    if not isinstance(payload, list) or len(payload) != 1:
        raise RuntimeError(f"{slug}: expected one event, got {len(payload) if isinstance(payload, list) else type(payload)}")
    return payload[0]


def book(token_id: str) -> dict:
    raw = get(CLOB + "?" + urlencode({"token_id": token_id}))
    bids = sorted(
        ({"price": float(row["price"]), "size": float(row["size"])} for row in raw.get("bids", [])),
        key=lambda row: row["price"],
        reverse=True,
    )
    asks = sorted(
        ({"price": float(row["price"]), "size": float(row["size"])} for row in raw.get("asks", [])),
        key=lambda row: row["price"],
    )
    return {
        "best_bid": bids[0]["price"] if bids else None,
        "best_ask": asks[0]["price"] if asks else None,
        "bids": bids[:20],
        "asks": asks[:20],
        "tick_size": float(raw.get("tick_size") or 0.01),
        "timestamp": raw.get("timestamp"),
    }


def record(market: dict, market_type: str) -> dict:
    outcomes = json.loads(market["outcomes"])
    tokens = json.loads(market["clobTokenIds"])
    prices = [float(value) for value in json.loads(market["outcomePrices"])]
    return {
        "id": market["id"],
        "slug": market["slug"],
        "question": market["question"],
        "market_type": market_type,
        "line": float(market["line"]) if market.get("line") is not None else None,
        "outcomes": outcomes,
        "token_ids": tokens,
        "outcome_prices": prices,
        "fee_schedule": market.get("feeSchedule") or {},
        "liquidity": float(market.get("liquidityNum") or market.get("liquidity") or 0),
        "volume": float(market.get("volumeNum") or market.get("volume") or 0),
        "updated_at": market.get("updatedAt"),
        "books": {outcome: book(token) for outcome, token in zip(outcomes, tokens)},
    }


def keep(market: dict) -> bool:
    market_type = market.get("sportsMarketType") or ""
    question = (market.get("question") or "").casefold()
    line = abs(float(market.get("line") or 0))
    if "corner" in market_type.casefold() or "corner" in question:
        return True
    if market_type == "spreads":
        return line <= 2.5
    if market_type == "totals":
        return 0.5 <= line <= 5.5
    return market_type in SUPPORTED


def main() -> None:
    matches = []
    corner_markets = []
    for slug in EVENTS:
        main_event = event(slug)
        more_event = event(slug + "-more-markets")
        pending = [(market, "match_1x2") for market in main_event["markets"]]
        for market in more_event["markets"]:
            if keep(market):
                market_type = market.get("sportsMarketType") or "unknown"
                pending.append((market, market_type))
        with ThreadPoolExecutor(max_workers=12) as executor:
            markets = list(executor.map(lambda item: record(*item), pending))
        for item in markets:
            if "corner" in item["market_type"].casefold() or "corner" in item["question"].casefold():
                corner_markets.append(item["slug"])
        matches.append(
            {
                "event_slug": slug,
                "title": main_event["title"],
                "kickoff_utc": main_event["endDate"],
                "event_url": f"https://polymarket.com/sports/world-cup/{slug}",
                "markets": markets,
            }
        )

    snapshot = {
        "as_of_beijing": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
        "gamma_api": GAMMA,
        "clob_api": CLOB,
        "corner_market_search": {
            "searched": True,
            "market_slugs": corner_markets,
            "result": "found" if corner_markets else "no executable corner market found in the two event market sets",
        },
        "matches": matches,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT} at {snapshot['as_of_beijing']}")
    for match in matches:
        print(match["title"], match["kickoff_utc"], len(match["markets"]), "markets")
        for market in match["markets"]:
            quotes = {name: (book_["best_bid"], book_["best_ask"]) for name, book_ in market["books"].items()}
            print(" ", market["market_type"], market["question"], quotes)


if __name__ == "__main__":
    main()
