"""Capture immutable Gamma metadata and live CLOB books for the last two matches."""

from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = {
    "fifwc-fra-eng-2026-07-18": [
        "fifwc-fra-eng-2026-07-18",
        "fifwc-fra-eng-2026-07-18-halftime-result",
        "fifwc-fra-eng-2026-07-18-second-half-result",
        "fifwc-fra-eng-2026-07-18-exact-score",
        "fifwc-fra-eng-2026-07-18-first-to-score",
        "fifwc-fra-eng-2026-07-18-more-markets",
        "fifwc-fra-eng-2026-07-18-total-corners",
        "fifwc-fra-eng-2026-07-18-player-props",
    ],
    "fifwc-esp-arg-2026-07-19": [
        "fifwc-esp-arg-2026-07-19",
        "fifwc-esp-arg-2026-07-19-halftime-result",
        "fifwc-esp-arg-2026-07-19-second-half-result",
        "fifwc-esp-arg-2026-07-19-exact-score",
        "fifwc-esp-arg-2026-07-19-first-to-score",
        "fifwc-esp-arg-2026-07-19-more-markets",
        "fifwc-esp-arg-2026-07-19-total-corners",
        "fifwc-esp-arg-2026-07-19-player-props",
    ],
}


def get_json(url: str, retries: int = 4, timeout: float = 40):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "wc-model-research/6.0"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode())
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(0.75 * (attempt + 1))
    raise RuntimeError(url) from last


def book_stats(book: dict) -> dict:
    asks = sorted((float(x["price"]), float(x["size"])) for x in book.get("asks", []))
    bids = sorted(((float(x["price"]), float(x["size"])) for x in book.get("bids", [])), reverse=True)
    ask = asks[0][0] if asks else None
    bid = bids[0][0] if bids else None
    return {
        "ask": ask,
        "bid": bid,
        "spread": None if ask is None or bid is None else ask - bid,
        "ask_depth_best_usd": sum(p*s for p, s in asks if ask is not None and abs(p-ask) < 1e-10),
        "ask_depth_2c_usd": sum(p*s for p, s in asks if ask is not None and p <= ask + .02 + 1e-10),
        "bid_depth_best_usd": sum(p*s for p, s in bids if bid is not None and abs(p-bid) < 1e-10),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", choices=["all", *FIXTURES], default="all")
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--book-retries", type=int, default=2)
    parser.add_argument("--book-timeout", type=float, default=12.0)
    args = parser.parse_args()

    events: dict[str, dict] = {}
    rows: list[dict] = []
    tokens: set[str] = set()
    selected = FIXTURES.items() if args.fixture == "all" else [(args.fixture, FIXTURES[args.fixture])]
    for fixture, slugs in selected:
        for slug in slugs:
            payload = get_json(f"https://gamma-api.polymarket.com/events?slug={slug}")
            if not payload:
                continue
            event = payload[0]
            events[slug] = event
            for market in event.get("markets", []):
                ids = json.loads(market["clobTokenIds"])
                outcomes = json.loads(market["outcomes"])
                if len(ids) != 2 or len(outcomes) != 2:
                    continue
                if market.get("acceptingOrders", False):
                    tokens.update(ids)
                rows.append({
                    "fixture_id": fixture,
                    "event_slug": slug,
                    "event_title": event["title"],
                    "market_id": market["id"],
                    "sports_market_type": market.get("sportsMarketType", ""),
                    "group_item_title": market.get("groupItemTitle", ""),
                    "question": market["question"],
                    "outcome_0": outcomes[0], "outcome_1": outcomes[1],
                    "token_0": ids[0], "token_1": ids[1],
                    "market_volume": market.get("volumeNum", market.get("volume", 0)) or 0,
                    "market_liquidity": market.get("liquidityNum", market.get("liquidity", 0)) or 0,
                    "gamma_best_bid": market.get("bestBid"),
                    "gamma_best_ask": market.get("bestAsk"),
                    "fee_rate": market.get("feeSchedule", {}).get("rate", .05),
                    "tick_size": market.get("orderPriceMinTickSize", .01),
                    "accepting_orders": market.get("acceptingOrders", False),
                })
    books: dict[str, dict] = {}
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                get_json,
                f"https://clob.polymarket.com/book?token_id={token}",
                args.book_retries,
                args.book_timeout,
            ): token
            for token in tokens
        }
        for future in as_completed(futures):
            token = futures[future]
            try:
                books[token] = future.result()
            except Exception as exc:
                books[token] = {"asks": [], "bids": []}
                errors[token] = f"{type(exc).__name__}: {exc}"
    for row in rows:
        for idx in (0, 1):
            for key, value in book_stats(books.get(row[f"token_{idx}"], {})).items():
                row[f"outcome_{idx}_{key}"] = value
    captured = datetime.now(timezone.utc)
    stamp = captured.strftime("%Y%m%d_%H%M%SZ")
    outdir = ROOT / "data" / "raw" / "polymarket"
    outdir.mkdir(parents=True, exist_ok=True)
    raw_path = outdir / f"remaining_matches_live_{stamp}.json"
    csv_path = outdir / f"remaining_matches_normalized_{stamp}.csv"
    raw_path.write_text(json.dumps({"captured_at_utc": captured.isoformat(), "events": events,
                                    "books": books, "book_errors": errors}, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (outdir / "LATEST_REMAINING.txt").write_text(str(csv_path.relative_to(ROOT)).replace("\\", "/"), encoding="utf-8")
    print(json.dumps({"captured_at_utc": captured.isoformat(), "markets": len(rows),
                      "book_errors": len(errors), "csv": str(csv_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
