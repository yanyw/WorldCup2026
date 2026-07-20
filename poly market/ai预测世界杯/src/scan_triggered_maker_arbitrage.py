from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fee(price: float, rate: float) -> float:
    return rate * price * (1-price)


def read_latest(pointer: str) -> tuple[Path, list[dict]]:
    path = ROOT / (ROOT / pointer).read_text(encoding="utf-8").strip()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return path, list(csv.DictReader(handle))


def max_raw_hedge_ask(maker_price: float, rate: float) -> float:
    feasible = [q/10000 for q in range(1, 10000)
                if maker_price + q/10000 + fee(q/10000, rate) <= 1]
    return max(feasible, default=0.0)


def main() -> None:
    match_path, match = read_latest("data/raw/polymarket/LATEST_SEMIFINALS.txt")
    meta_path, meta = read_latest("data/raw/polymarket/LATEST_META.txt")
    advance = next(row for row in match if row["group"] == "advance")

    def meta_row(slug: str, contract: str) -> dict:
        return next(row for row in meta if row["event_slug"] == slug and row["contract"] == contract)

    england_state = [
        ("England to advance YES", advance, "yes"),
        ("Final ESP-ENG YES", meta_row("world-cup-finals-exact-matchup-20260708195422328", "ESP vs ENG"), "yes"),
        ("Third FRA-ARG YES", meta_row("world-cup-3rd-place-game-exact-matchup-20260708194423346", "FRA vs ARG"), "yes"),
    ]
    argentina_state = [
        ("England to advance NO", advance, "no"),
        ("Final ESP-ARG YES", meta_row("world-cup-finals-exact-matchup-20260708195422328", "ESP vs ARG"), "yes"),
        ("Third FRA-ENG YES", meta_row("world-cup-3rd-place-game-exact-matchup-20260708194423346", "FRA vs ENG"), "yes"),
    ]

    scans = []
    for maker_state, hedge_state in ((england_state, argentina_state), (argentina_state, england_state)):
        for maker_name, maker_row, maker_side in maker_state:
            maker_bid = float(maker_row[f"{maker_side}_bid"])
            maker_queue = float(maker_row.get(f"{maker_side}_bid_depth_at_best") or 0)
            for hedge_name, hedge_row, hedge_side in hedge_state:
                hedge_ask = float(hedge_row[f"{hedge_side}_ask"])
                hedge_depth = float(hedge_row.get(f"{hedge_side}_ask_depth_at_best") or 0)
                rate = float(hedge_row.get("fee_rate") or 0.05)
                hedge_all_in = hedge_ask + fee(hedge_ask, rate)
                profit = 1-maker_bid-hedge_all_in
                scans.append({
                    "maker_leg": maker_name,
                    "maker_bid": maker_bid,
                    "maker_queue_depth_at_price_usd": round(maker_queue, 2),
                    "hedge_leg": hedge_name,
                    "hedge_ask": hedge_ask,
                    "hedge_depth_at_best_usd": round(hedge_depth, 2),
                    "hedge_taker_fee": round(fee(hedge_ask, rate), 8),
                    "combined_cost_if_hedged_now": round(maker_bid+hedge_all_in, 8),
                    "locked_profit_if_hedged_now": round(profit, 8),
                    "maximum_raw_hedge_ask": max_raw_hedge_ask(maker_bid, rate),
                    "positive_at_snapshot": profit > 0,
                })
    scans.sort(key=lambda row: row["locked_profit_if_hedged_now"], reverse=True)
    positive = [row for row in scans if row["positive_at_snapshot"]]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "match_snapshot": str(match_path.relative_to(ROOT)),
        "meta_snapshot": str(meta_path.relative_to(ROOT)),
        "mechanism": "A passive maker buy is not an arbitrage before it fills. If it fills, immediately buy a mutually exclusive equivalent state as taker, subject to the stated maximum hedge ask.",
        "maker_fee_assumption": "zero because the captured Polymarket feeSchedule is takerOnly=true; verify immediately before trading",
        "positive_triggers": positive,
        "all_pairs": scans,
    }
    outdir = ROOT / "outputs/model_v5"; outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "triggered_maker_arbitrage.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# 触发式做市准套利扫描", "",
             "被动单成交前不构成套利；成交后，只有在对冲盘口仍不高于上限时，才可转化为锁定收益。", "",
             "| 被动腿 | 挂单价 | 对冲腿 | 当前对冲价 | 含费总成本 | 快照锁定收益 | 对冲价上限 | 同价已有买盘 | 最优对冲深度 |",
             "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for row in positive:
        lines.append(f"| {row['maker_leg']} | {row['maker_bid']:.2%} | {row['hedge_leg']} | "
                     f"{row['hedge_ask']:.2%} | {row['combined_cost_if_hedged_now']:.3%} | "
                     f"{row['locked_profit_if_hedged_now']:+.3%} | {row['maximum_raw_hedge_ask']:.2%} | "
                     f"${row['maker_queue_depth_at_price_usd']:,.0f} | ${row['hedge_depth_at_best_usd']:,.0f} |")
    lines += ["", "风险：非原子成交、信息型成交导致对冲价同步跳动、排队优先级和接口延迟。任何一项越过对冲上限，都不能称为套利。"]
    (outdir / "triggered_maker_arbitrage.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"positive_triggers": len(positive),
                      "best_snapshot_profit": positive[0]["locked_profit_if_hedged_now"] if positive else None},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
