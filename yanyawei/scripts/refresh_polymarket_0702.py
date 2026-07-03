#!/usr/bin/env python3
"""Refresh the July 2 World Cup market snapshot from Polymarket Gamma API."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "market_inputs_0702.json"
LIVE_PATH = ROOT / "data" / "polymarket_live_0702.json"
DECISIONS_PATH = ROOT / "data" / "portfolio_decisions_0702.json"
API = "https://gamma-api.polymarket.com/events"
CLOB_BOOK_API = "https://clob.polymarket.com/book"

SLUGS = {
    "esp_aut": "fifwc-esp-aut-2026-07-02",
    "por_cro": "fifwc-prt-hrv-2026-07-02",
    "sui_alg": "fifwc-che-alg-2026-07-02",
    "aus_egy": "fifwc-aus-egy-2026-07-03",
    "arg_cpv": "fifwc-arg-cvi-2026-07-03",
    "col_gha": "fifwc-col-gha-2026-07-03",
    "can_mar": "fifwc-can-mar-2026-07-04",
    "par_fra": "fifwc-par-fra-2026-07-04",
    "bra_nor": "fifwc-bra-nor-2026-07-05",
    "mex_eng": "fifwc-mex-eng-2026-07-05",
}


def fetch_event(slug: str) -> dict:
    url = f"{API}?{urlencode({'slug': slug})}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "wc2026-research/2.0"})
    with urlopen(request, timeout=30) as response:
        events = json.load(response)
    if len(events) != 1:
        raise RuntimeError(f"Expected one event for {slug}, received {len(events)}")
    return events[0]


def prices(market: dict) -> dict:
    midpoint = [float(value) for value in json.loads(market["outcomePrices"])]
    yes_bid = float(market["bestBid"]) if market.get("bestBid") is not None else None
    yes_ask = float(market["bestAsk"]) if market.get("bestAsk") is not None else None
    return {
        "yes_mid": midpoint[0],
        "no_mid": midpoint[1],
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": None if yes_ask is None else round(1.0 - yes_ask, 6),
        "no_ask": None if yes_bid is None else round(1.0 - yes_bid, 6),
    }


def select(markets: list[dict], market_type: str, line: float | None = None, team: str | None = None) -> dict:
    candidates = [market for market in markets if market.get("sportsMarketType") == market_type]
    if line is not None:
        candidates = [market for market in candidates if abs(float(market.get("line"))) == abs(float(line))]
    if team is not None:
        candidates = [market for market in candidates if market["question"].startswith(f"Spread: {team} ")]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one {market_type=} {line=} {team=}; received {len(candidates)}")
    return candidates[0]


def market_record(market: dict) -> dict:
    return {
        "market_id": market["id"],
        "question": market["question"],
        "slug": market["slug"],
        "outcomes": json.loads(market["outcomes"]),
        "token_ids": json.loads(market["clobTokenIds"]),
        "prices": prices(market),
        "fee_schedule": market.get("feeSchedule"),
        "updated_at": market.get("updatedAt"),
    }


def execution_record(live_match: dict, market_name: str) -> tuple[dict, str]:
    if market_name == "combined_total_under_2_5":
        record, side = live_match["total"], "no"
    elif market_name == "combined_total_over_2_5":
        record, side = live_match["total"], "yes"
    elif market_name in ("austria_plus_1_5", "paraguay_plus_1_5"):
        record, side = live_match["spread"], "no"
    elif market_name == "btts_no":
        record, side = live_match["props"]["btts"], "no"
    else:
        raise RuntimeError(f"No executable-price mapping for {market_name}")
    return record, side


def fetch_clob_quote(record: dict, side: str) -> tuple[float, float, float]:
    index = 0 if side == "yes" else 1
    token_id = record["token_ids"][index]
    url = f"{CLOB_BOOK_API}?{urlencode({'token_id': token_id})}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "wc2026-research/2.0"})
    with urlopen(request, timeout=30) as response:
        book = json.load(response)
    if not book.get("bids") or not book.get("asks"):
        raise RuntimeError(f"Incomplete CLOB book for {record['slug']} {side}")
    bid = max(float(level["price"]) for level in book["bids"])
    ask = min(float(level["price"]) for level in book["asks"])
    schedule = record.get("fee_schedule")
    if not schedule or schedule.get("rate") is None:
        raise RuntimeError(f"Missing fee schedule for {record['slug']}")
    record.setdefault("clob_quotes", {})[side] = {
        "token_id": token_id,
        "best_bid": bid,
        "best_ask": ask,
        "tick_size": float(book["tick_size"]),
        "book_timestamp": book.get("timestamp"),
    }
    return bid, ask, float(schedule["rate"])


def main() -> None:
    inputs = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    live_matches = []

    for match in inputs["matches"]:
        slug = SLUGS[match["id"]]
        main_event = fetch_event(slug)
        more_event = fetch_event(f"{slug}-more-markets")
        main_markets = main_event["markets"]
        more_markets = more_event["markets"]

        moneyline = {}
        for side, team in (("home", match["home"]), ("away", match["away"])):
            market = next(m for m in main_markets if m["question"].startswith("Will ") and " end in a draw" not in m["question"] and m["marketMetadata"]["opticOddsSelectionLine"] == side)
            moneyline[side] = market_record(market)
        moneyline["draw"] = market_record(next(m for m in main_markets if " end in a draw" in m["question"]))

        total_market = select(more_markets, "totals", match["total"]["line"])
        spread_line = float(match["spread"]["line"])
        favorite_side = "home" if spread_line < 0 else "away"
        favorite_name = main_event["teams"][0 if favorite_side == "home" else 1]["name"]
        spread_market = select(more_markets, "spreads", 1.5, favorite_name)

        total = market_record(total_market)
        spread = market_record(spread_market)
        total["line"] = float(match["total"]["line"])
        spread["home_line"] = spread_line
        spread["favorite_side"] = favorite_side

        # Model inputs use midpoints; execution decisions should use the ask fields in LIVE_PATH.
        match["moneyline"] = {
            "home": moneyline["home"]["prices"]["yes_mid"],
            "draw": moneyline["draw"]["prices"]["yes_mid"],
            "away": moneyline["away"]["prices"]["yes_mid"],
        }
        match["total"] = {
            "line": total["line"],
            "over": total["prices"]["yes_mid"],
            "under": total["prices"]["no_mid"],
        }
        if favorite_side == "home":
            match["spread"] = {"line": spread_line, "home": spread["prices"]["yes_mid"], "away": spread["prices"]["no_mid"]}
        else:
            match["spread"] = {"line": spread_line, "home": spread["prices"]["no_mid"], "away": spread["prices"]["yes_mid"]}

        props = {}
        if "props" in match:
            btts = select(more_markets, "both_teams_to_score")
            props["btts"] = market_record(btts)
            match["props"] = {"btts_yes": props["btts"]["prices"]["yes_mid"], "btts_no": props["btts"]["prices"]["no_mid"]}

        live_matches.append({
            "id": match["id"],
            "event_url": f"https://polymarket.com/sports/world-cup/{slug}",
            "moneyline": moneyline,
            "spread": spread,
            "total": total,
            "props": props,
        })

    now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
    inputs["snapshot_beijing"] = now
    inputs["source"] = "https://gamma-api.polymarket.com/events"
    live = {"snapshot_beijing": now, "source": API, "matches": live_matches}
    INPUT_PATH.write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    decisions = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
    live_by_id = {match["id"]: match for match in live_matches}
    for position in decisions["positions"]:
        live_match = live_by_id[position["match_id"]]
        record, side = execution_record(live_match, position["market"])
        bid, ask, fee_rate = fetch_clob_quote(record, side)
        position["snapshot_best_bid"] = bid
        position["snapshot_price"] = ask
        position["fee_rate"] = fee_rate
        taker_maximum = position.get("maximum_taker_price", position["maximum_price"])
        position["status"] = (
            "TAKER_ACTIONABLE"
            if "taker_allowed" in position["execution"] and ask <= taker_maximum
            else "MAKER_ORDER"
        )
    decisions["snapshot_beijing"] = now
    LIVE_PATH.write_text(json.dumps(live, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DECISIONS_PATH.write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Updated {len(live_matches)} matches at {now}")
    for position in decisions["positions"]:
        print(
            f"{position['status']:<18} {position['match_id']:<8} {position['market']:<32} "
            f"bid={position['snapshot_best_bid']:.4f} ask={position['snapshot_price']:.4f} "
            f"max={position['maximum_price']:.4f} "
            f"stake={position['stake_usdc']:.1f}"
        )


if __name__ == "__main__":
    main()
