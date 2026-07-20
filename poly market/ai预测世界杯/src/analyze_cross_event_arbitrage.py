from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fee(price: float, rate: float) -> float:
    return rate * price * (1-price)


def main() -> None:
    match_path = ROOT / (ROOT / "data/raw/polymarket/LATEST_SEMIFINALS.txt").read_text(encoding="utf-8").strip()
    meta_path = ROOT / (ROOT / "data/raw/polymarket/LATEST_META.txt").read_text(encoding="utf-8").strip()
    with match_path.open(encoding="utf-8-sig", newline="") as f: match = list(csv.DictReader(f))
    with meta_path.open(encoding="utf-8-sig", newline="") as f: meta = list(csv.DictReader(f))
    advance = next(r for r in match if r["group"] == "advance")

    def meta_row(slug: str, contract: str):
        return next(r for r in meta if r["event_slug"] == slug and r["contract"] == contract)

    # Equivalent resolution states after Spain has already reached the final.
    e_candidates = [
        ("England to advance YES", advance, "yes"),
        ("Final ESP-ENG YES", meta_row("world-cup-finals-exact-matchup-20260708195422328", "ESP vs ENG"), "yes"),
        ("Third FRA-ARG YES", meta_row("world-cup-3rd-place-game-exact-matchup-20260708194423346", "FRA vs ARG"), "yes"),
    ]
    a_candidates = [
        ("England to advance NO", advance, "no"),
        ("Final ESP-ARG YES", meta_row("world-cup-finals-exact-matchup-20260708195422328", "ESP vs ARG"), "yes"),
        ("Third FRA-ENG YES", meta_row("world-cup-3rd-place-game-exact-matchup-20260708194423346", "FRA vs ENG"), "yes"),
    ]

    def choices(items, execution: str):
        out = []
        for name, row, side in items:
            price = float(row[f"{side}_{execution}"])
            rate = float(row.get("fee_rate") or 0.05)
            cost = price + (fee(price, rate) if execution == "ask" else 0.0)
            depth = float(row.get(f"{side}_ask_depth_1c") or 0) if execution == "ask" else 0.0
            out.append({"name": name, "price": price, "cost": cost, "depth": depth})
        return sorted(out, key=lambda x: x["cost"])

    taker_e, taker_a = choices(e_candidates, "ask"), choices(a_candidates, "ask")
    maker_e, maker_a = choices(e_candidates, "bid"), choices(a_candidates, "bid")
    taker_cost = taker_e[0]["cost"] + taker_a[0]["cost"]
    maker_cost = maker_e[0]["cost"] + maker_a[0]["cost"]
    payload = {"match_snapshot": str(match_path.relative_to(ROOT)), "meta_snapshot": str(meta_path.relative_to(ROOT)),
               "taker": {"england_state": taker_e, "argentina_state": taker_a, "best_cost": taker_cost,
                         "locked_profit": 1-taker_cost, "executable_arbitrage": taker_cost < 1},
               "maker_indication": {"england_state": maker_e, "argentina_state": maker_a,
                                    "best_combined_bid": maker_cost, "potential_profit_if_both_fill": 1-maker_cost,
                                    "warning": "Not locked: both passive legs may not fill and prices can move."}}
    outdir = ROOT / "outputs/model_v4"; outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "cross_event_arbitrage.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# 世界杯跨事件等价合约套利", "",
          "英格兰晋级、决赛 ESP–ENG、三四名赛 FRA–ARG 是同一状态；另一组三个合约对应阿根廷晋级。",
          "", f"当前最便宜的吃单覆盖成本为 **{taker_cost:.4f}**，锁定收益 **{1-taker_cost:+.4f}**。",
          "" if taker_cost < 1 else "因此当前不存在可立即成交的跨事件套利。",
          "", f"按各市场买盘被动挂单的理论组合成本为 {maker_cost:.4f}，若两腿都成交可得 {1-maker_cost:+.4f}；但这不是锁定套利，存在单腿成交风险。",
          "", "## 最优吃单腿", "",
          f"- 英格兰晋级状态：{taker_e[0]['name']}，报价 {taker_e[0]['price']:.4f}，含费成本 {taker_e[0]['cost']:.4f}。",
          f"- 阿根廷晋级状态：{taker_a[0]['name']}，报价 {taker_a[0]['price']:.4f}，含费成本 {taker_a[0]['cost']:.4f}。"]
    (outdir / "cross_event_arbitrage.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"taker_cost": taker_cost, "locked_profit": 1-taker_cost,
                      "maker_cost": maker_cost, "maker_if_filled": 1-maker_cost}, ensure_ascii=False))


if __name__ == "__main__":
    main()
