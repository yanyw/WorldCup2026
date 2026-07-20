from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fnum(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fee(price: float, rate: float) -> float:
    return rate * price * (1.0 - price)


def leg(row: dict, side: str) -> dict | None:
    ask = fnum(row[f"{side}_ask"], -1)
    if ask < 0:
        return None
    rate = fnum(row.get("fee_rate"), 0.05)
    return {"market_id": row["market_id"], "contract": row["contract"],
            "side": side.upper(), "ask": ask, "fee": fee(ask, rate),
            "unit_cost": ask + fee(ask, rate),
            "depth_usd": fnum(row.get(f"{side}_ask_depth_1c"))}


def package(kind: str, fixture: str, legs: list[dict], guaranteed_payout: float = 1.0) -> dict:
    cost = sum(x["unit_cost"] for x in legs)
    profit = guaranteed_payout - cost
    # Each leg needs the same number of shares; displayed depth is dollar notional.
    share_capacity = min((x["depth_usd"] / max(x["ask"], 1e-9) for x in legs), default=0.0)
    capital_capacity = share_capacity * sum(x["ask"] for x in legs)
    return {"fixture_id": fixture, "type": kind, "legs": legs, "leg_count": len(legs),
            "guaranteed_payout": guaranteed_payout, "all_in_cost": cost,
            "profit_per_bundle": profit, "roi_on_cost": profit / cost if cost > 0 else 0.0,
            "estimated_capital_capacity_usd": capital_capacity,
            "is_arbitrage": profit > 0 and all(x["depth_usd"] > 0 for x in legs)}


def threshold_scope(row: dict) -> tuple[str, float] | None:
    c = row["contract"]
    try:
        line = float(c.split()[-1])
    except ValueError:
        return None
    return " ".join(c.split()[:-1]), line


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default=None)
    ap.add_argument("--output-dir", default="outputs/model_v4")
    ap.add_argument("--prefix", default="upcoming_20260715")
    args = ap.parse_args()
    snapshot = ROOT / (args.snapshot or (ROOT / "data/raw/polymarket/LATEST_SEMIFINALS.txt").read_text(encoding="utf-8").strip())
    with snapshot.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    packages = []

    # Every binary contract: YES + NO pays exactly one dollar.
    for r in rows:
        legs = [leg(r, "yes"), leg(r, "no")]
        if all(legs):
            packages.append(package("binary_complement", r["fixture_id"], legs))

    by_fixture_group = defaultdict(list)
    for r in rows:
        by_fixture_group[(r["fixture_id"], r["group"])].append(r)

    # Mutually exclusive and exhaustive partitions.
    expected_counts = {"main_90m": 3, "first_score": 3, "exact_score": 17}
    for (fixture, group), group_rows in by_fixture_group.items():
        if group in expected_counts and len(group_rows) == expected_counts[group]:
            legs = [leg(r, "yes") for r in group_rows]
            if all(legs):
                packages.append(package(f"partition_{group}", fixture, legs))

    # Nested thresholds: YES(lower) + NO(higher) always pays at least $1 and
    # can pay $2 in the interval between the two lines.
    for (fixture, group), group_rows in by_fixture_group.items():
        if group not in {"totals", "team_total", "half_total", "half_team"}:
            continue
        scopes = defaultdict(list)
        for r in group_rows:
            parsed = threshold_scope(r)
            if parsed:
                scopes[parsed[0]].append((parsed[1], r))
        for scope, values in scopes.items():
            values.sort()
            for i, (low, low_row) in enumerate(values):
                for high, high_row in values[i+1:]:
                    legs = [leg(low_row, "yes"), leg(high_row, "no")]
                    if all(legs):
                        packages.append(package(f"nested_{group}:{scope}:{low:g}<{high:g}", fixture, legs))

    packages.sort(key=lambda x: x["profit_per_bundle"], reverse=True)
    outdir = ROOT / args.output_dir; outdir.mkdir(parents=True, exist_ok=True)
    jsonpath = outdir / f"{args.prefix}_arbitrage_scan.json"
    jsonpath.write_text(json.dumps({"snapshot": str(snapshot.relative_to(ROOT)), "packages_scanned": len(packages),
                                    "arbitrages": [p for p in packages if p["is_arbitrage"]],
                                    "top_near_arbitrages": packages[:20]}, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ["# Polymarket 订单簿套利扫描", "", f"快照：`{snapshot.relative_to(ROOT)}`；扫描组合 {len(packages)} 个。", ""]
    arbs = [p for p in packages if p["is_arbitrage"]]
    if not arbs:
        report.append("没有发现扣除显示费率后、按当前卖一可锁定正收益的套利组合。")
    else:
        report += ["| 类型 | 组合成本 | 保底收益 | ROI | 估算容量 | 交易腿 |", "|---|---:|---:|---:|---:|---|"]
        for p in arbs:
            legs = "; ".join(f"{x['contract']} {x['side']}@{x['ask']:.3f}" for x in p["legs"])
            report.append(f"| {p['type']} | {p['all_in_cost']:.4f} | {p['profit_per_bundle']:.4f} | {p['roi_on_cost']:.2%} | ${p['estimated_capital_capacity_usd']:.0f} | {legs} |")
    report += ["", "## 最接近套利的组合", "", "| 类型 | 全成本 | 距离保本 |", "|---|---:|---:|"]
    for p in packages[:10]:
        report.append(f"| {p['type']} | {p['all_in_cost']:.4f} | {p['profit_per_bundle']:+.4f} |")
    report += ["", "说明：这是静态快照扫描，不保证多腿同时成交。容量按一档卖盘粗估；成交延迟、撤单、部分成交和规则差异会消灭表面套利。"]
    mdpath = outdir / f"{args.prefix}_arbitrage_scan.md"; mdpath.write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"packages": len(packages), "arbitrages": len(arbs), "report": str(mdpath)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
