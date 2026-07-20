from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from collect_live_markets import book_stats, get_json

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", default="data/inputs/meta_event_slugs_20260715.json")
    args = ap.parse_args()
    doc = json.loads((ROOT / args.events).read_text(encoding="utf-8"))
    rows, tokens, events = [], [], {}
    for slug in doc["event_slugs"]:
        data = get_json(f"https://gamma-api.polymarket.com/events?slug={slug}")
        if not data:
            raise RuntimeError(f"event not found: {slug}")
        event = data[0]; events[slug] = event
        for m in event["markets"]:
            if m.get("closed"):
                continue
            ids = json.loads(m["clobTokenIds"]); outcomes = json.loads(m["outcomes"])
            if len(ids) != 2:
                continue
            tokens.extend(ids)
            rows.append({"event_slug": slug, "event_title": event["title"], "market_id": m["id"],
                         "question": m["question"], "contract": m.get("groupItemTitle") or m["question"],
                         "outcome_yes": outcomes[0], "outcome_no": outcomes[1],
                         "token_yes": ids[0], "token_no": ids[1],
                         "market_liquidity": m.get("liquidityNum", 0), "market_volume": m.get("volumeNum", 0),
                         "fee_rate": m.get("feeSchedule", {}).get("rate", 0.05),
                         "tick_size": m.get("orderPriceMinTickSize", 0.01)})
    books = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        fut = {ex.submit(get_json, f"https://clob.polymarket.com/book?token_id={t}"): t for t in set(tokens)}
        for f in as_completed(fut):
            try:
                books[fut[f]] = f.result()
            except Exception:
                books[fut[f]] = {"bids": [], "asks": []}
    for row in rows:
        for side in ("yes", "no"):
            for k, v in book_stats(books[row[f"token_{side}"]]).items():
                row[f"{side}_{k}"] = v
    now = datetime.now(timezone.utc); stamp = now.strftime("%Y%m%d_%H%M%SZ")
    outdir = ROOT / "data/raw/polymarket"; outdir.mkdir(parents=True, exist_ok=True)
    rawpath = outdir / f"meta_markets_live_{stamp}.json"
    csvpath = outdir / f"meta_markets_normalized_{stamp}.csv"
    rawpath.write_text(json.dumps({"captured_at_utc": now.isoformat(), "events": events, "books": books}, ensure_ascii=False), encoding="utf-8")
    with csvpath.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (outdir / "LATEST_META.txt").write_text(str(csvpath.relative_to(ROOT)).replace("\\", "/"), encoding="utf-8")
    print(json.dumps({"captured_at_utc": now.isoformat(), "markets": len(rows), "csv": str(csvpath)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
