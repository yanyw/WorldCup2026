from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]


def fee(price: float, rate: float) -> float:
    return rate * price * (1-price)


def yes_payoff(row: dict, h: int, a: int, home_advances: bool) -> float | None:
    group, contract = row["group"], row["contract"]
    home, away = row["home"], row["away"]
    if group == "main_90m":
        return float(h > a) if contract.startswith(home) else float(a > h) if contract.startswith(away) else float(h == a)
    if group == "advance":
        return float(h > a or (h == a and home_advances))
    if group == "totals":
        return float(h+a >= int(float(contract.split()[-1]) // 1 + 1))
    if group == "team_total":
        threshold = int(float(contract.split()[-1]) // 1 + 1)
        return float((h if contract.startswith(home) else a) >= threshold)
    if group == "btts" and "first half" not in contract.lower() and "second half" not in contract.lower():
        return float(h >= 1 and a >= 1)
    if group == "spread":
        team, handicap = contract.rsplit(" ", 1)
        margin = int(abs(float(handicap.strip("()"))) // 1 + 1)
        return float(h-a >= margin) if team == home else float(a-h >= margin)
    if group == "extra_time" and "extra time" in contract:
        return float(h == a)
    if group == "exact_score":
        if contract.lower() == "any other score": return float(not (h <= 3 and a <= 3))
        score = contract.replace(f"{home} ", "").replace(f" {away}", "")
        sh, sa = map(int, score.split("-")); return float(h == sh and a == sa)
    return None


def solve_fixture(rows: list[dict]) -> dict:
    states = []
    for h in range(12):
        for a in range(12):
            if h == a:
                states.extend([(h, a, False), (h, a, True)])
            else:
                states.append((h, a, h > a))
    securities = []
    for row in rows:
        pay = [yes_payoff(row, *state) for state in states]
        if any(x is None for x in pay):
            continue
        for side in ("yes", "no"):
            raw = row.get(f"{side}_ask")
            if raw in (None, ""): continue
            ask = float(raw); rate = float(row.get("fee_rate") or 0.05)
            vector = np.array(pay if side == "yes" else [1-x for x in pay], dtype=float)
            securities.append({"contract": row["contract"], "side": side.upper(), "ask": ask,
                               "cost": ask+fee(ask, rate), "depth": float(row.get(f"{side}_ask_depth_1c") or 0),
                               "payoff": vector})
    c = np.array([x["cost"] for x in securities])
    payoff = np.vstack([x["payoff"] for x in securities]).T
    result = linprog(c, A_ub=-payoff, b_ub=-np.ones(len(states)), bounds=(0, None), method="highs")
    if not result.success: raise RuntimeError(result.message)
    positions = []
    for qty, sec in zip(result.x, securities):
        if qty > 1e-7:
            positions.append({k: v for k, v in sec.items() if k != "payoff"} | {"shares_per_bundle": float(qty)})
    min_payoff = float(np.min(payoff @ result.x))
    cost = float(result.fun); profit = min_payoff-cost
    capacity_scale = min((p["depth"] / max(p["ask"]*p["shares_per_bundle"], 1e-9) for p in positions), default=0)
    return {"fixture_id": rows[0]["fixture_id"], "states": len(states), "securities": len(securities),
            "minimum_superhedge_cost": cost, "minimum_state_payoff": min_payoff,
            "locked_profit_per_bundle": profit, "roi": profit/cost,
            "is_taker_arbitrage": profit > 1e-9, "estimated_capital_capacity_usd": capacity_scale*cost,
            "positions": positions}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default=None)
    ap.add_argument("--output-dir", default="outputs/model_v5")
    args = ap.parse_args()
    snapshot = ROOT / (args.snapshot or (ROOT / "data/raw/polymarket/LATEST_SEMIFINALS.txt").read_text(encoding="utf-8").strip())
    with snapshot.open(encoding="utf-8-sig", newline="") as f: rows = list(csv.DictReader(f))
    by_fixture = {}
    for row in rows:
        by_fixture.setdefault(row["fixture_id"], []).append(row)
    results = [solve_fixture(group_rows) for group_rows in by_fixture.values()]
    payload = {"snapshot": str(snapshot.relative_to(ROOT)), "fixtures": results,
               "any_taker_arbitrage": any(x["is_taker_arbitrage"] for x in results)}
    outdir = ROOT / args.output_dir; outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "dutch_book_lp.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# 全状态线性规划 Dutch-book 扫描", "", f"快照：`{snapshot.relative_to(ROOT)}`。不同比赛分开求解，禁止把互不相关的赔付状态错误混合。", ""]
    for item in results:
        md += [f"## {item['fixture_id']}", "",
               f"覆盖 {item['states']} 个比分/晋级状态、{item['securities']} 个可买证券。",
               "", f"最小保底组合成本：**{item['minimum_superhedge_cost']:.6f}**；最小状态赔付：{item['minimum_state_payoff']:.6f}；锁定收益：{item['locked_profit_per_bundle']:+.6f}。",
               "", "| 合约 | 方向 | 卖价 | 含费成本 | 每组合份额 |", "|---|---|---:|---:|---:|"]
        for p in item["positions"]:
            md.append(f"| {p['contract']} | {p['side']} | {p['ask']:.4f} | {p['cost']:.4f} | {p['shares_per_bundle']:.4f} |")
        md.append("")
    md += ["", "只有锁定收益大于0且全部交易腿能够同时成交时才属于可执行套利。半场、首个进球和点球市场因无法由最终比分状态完全决定，另行扫描，不在本LP中强行加入。"]
    (outdir / "dutch_book_lp.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"fixtures": len(results), "arbitrages": sum(x["is_taker_arbitrage"] for x in results),
                      "best_locked_profit": max(x["locked_profit_per_bundle"] for x in results)}, ensure_ascii=False))


if __name__ == "__main__": main()
