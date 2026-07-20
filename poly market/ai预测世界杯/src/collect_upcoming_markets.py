from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from collect_live_markets import book_stats, get_json, market_key

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", default="data/inputs/semifinals_20260712.json")
    args = ap.parse_args()
    fixture_doc = json.loads((ROOT / args.fixtures).read_text(encoding="utf-8"))
    events, rows, tokens = {}, [], []
    for fx in fixture_doc["fixtures"]:
        evs = []
        for slug in fx["event_slugs"]:
            data = get_json(f"https://gamma-api.polymarket.com/events?slug={slug}")
            if not data:
                raise RuntimeError(f"event not found: {slug}")
            evs.append(data[0])
        events[fx["fixture_id"]] = evs
        for ev in evs:
            for m in ev["markets"]:
                ids = json.loads(m["clobTokenIds"])
                outcomes = json.loads(m["outcomes"])
                if len(ids) != 2:
                    continue
                tokens.extend(ids)
                group, contract = market_key(m, fx["home"], fx["away"])
                rows.append({
                    "fixture_id": fx["fixture_id"], "home": fx["home"], "away": fx["away"],
                    "event_slug": ev["slug"], "event_title": ev["title"],
                    "event_liquidity": ev.get("liquidity", 0), "event_volume": ev.get("volume", 0),
                    "market_id": m["id"], "question": m["question"],
                    "sports_market_type": m.get("sportsMarketType", ""), "group": group,
                    "contract": contract, "outcome_yes": outcomes[0], "outcome_no": outcomes[1],
                    "token_yes": ids[0], "token_no": ids[1],
                    "market_liquidity": m.get("liquidityNum", m.get("liquidity", 0)),
                    "market_volume": m.get("volumeNum", m.get("volume", 0)),
                    "gamma_best_bid": m.get("bestBid"), "gamma_best_ask": m.get("bestAsk"),
                    "fee_rate": m.get("feeSchedule", {}).get("rate", 0.05),
                    "tick_size": m.get("orderPriceMinTickSize", 0.01),
                })
    books, book_errors = {}, {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        fut = {ex.submit(get_json, f"https://clob.polymarket.com/book?token_id={t}"): t for t in set(tokens)}
        for f in as_completed(fut):
            token = fut[f]
            try:
                books[token] = f.result()
            except Exception as exc:
                # A resolved/temporarily unavailable contract can return 404 while
                # the event payload still lists it. Preserve the rest of the live
                # snapshot and leave this token explicitly unquoted.
                books[token] = {"asks": [], "bids": []}
                book_errors[token] = f"{type(exc).__name__}: {exc}"
    for row in rows:
        for side in ("yes", "no"):
            stats = book_stats(books[row[f"token_{side}"]])
            for k, v in stats.items():
                row[f"{side}_{k}"] = v
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d_%H%M%SZ")
    outdir = ROOT / "data/raw/polymarket"
    outdir.mkdir(parents=True, exist_ok=True)
    rawpath = outdir / f"semifinals_live_{stamp}.json"
    csvpath = outdir / f"semifinals_normalized_{stamp}.csv"
    rawpath.write_text(json.dumps({"captured_at_utc": now.isoformat(), "events": events,
                                   "books": books, "book_errors": book_errors}, ensure_ascii=False), encoding="utf-8")
    with csvpath.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (outdir / "LATEST_SEMIFINALS.txt").write_text(str(csvpath.relative_to(ROOT)).replace("\\", "/"), encoding="utf-8")
    print(json.dumps({"captured_at_utc": now.isoformat(), "markets": len(rows),
                      "book_errors": len(book_errors), "csv": str(csvpath)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
