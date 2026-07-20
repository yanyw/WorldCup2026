from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

from wc_model.ensemble import sharp_consensus
from wc_model.historical import (RidgePoisson, elo_probabilities, estimate_dc_rho,
                                 load_results_with_overrides)
from wc_model.maxent import common_pace_mixture, maxent_tilt
from wc_model.score import core_markets, dc_matrix, de_vig
from wc_model.valuation import confidence_class, contract_probability

ROOT = Path(__file__).resolve().parents[1]


def fee(price: float, rate: float) -> float:
    return rate * price * (1-price)


def target_for(p1: dict, elo: dict, sharp1: dict, sharpt: dict, rel: float) -> dict:
    independent = {k: 0.75*p1[k] + 0.25*elo[k] for k in ("home", "draw", "away")}
    return {"home": sharp1["home"] + rel*(independent["home"]-sharp1["home"]),
            "draw": sharp1["draw"] + rel*(independent["draw"]-sharp1["draw"]),
            "away": sharp1["away"] + rel*(independent["away"]-sharp1["away"]),
            "over2.5": sharpt["over"] + rel*(p1["over2.5"]-sharpt["over"])}


def main() -> None:
    cfg = json.loads((ROOT / "config/model_config_v3.json").read_text(encoding="utf-8"))
    doc = json.loads((ROOT / "data/inputs/upcoming_20260715.json").read_text(encoding="utf-8"))
    fx = doc["fixtures"][0]; pcfg = cfg["poisson"]
    cutoff = date.fromisoformat(cfg["data"]["cutoff_exclusive"])
    rows = load_results_with_overrides(ROOT / cfg["data"]["historical_results"],
                                       date.fromisoformat(cfg["data"]["training_start"]), cutoff,
                                       ROOT / cfg["data"]["regulation_overrides"])
    pmodel = RidgePoisson(pcfg["half_life_days"], pcfg["ridge"], pcfg).fit(rows, cutoff)
    lam = pmodel.predict(fx["home"], fx["away"], True)
    all_lh, all_la = pmodel.lambdas_for_rows(rows)
    rho = estimate_dc_rho(rows, all_lh, all_la, cutoff, pcfg["half_life_days"])
    standard_base = dc_matrix(*lam, rho, pcfg["max_goals"])
    mixture_base = common_pace_mixture(dc_matrix, *lam, rho, pcfg["max_goals"])
    p1 = core_markets(standard_base); elo, elo_info = elo_probabilities(rows, fx["home"], fx["away"], True)
    consensus1, consensust = sharp_consensus(fx["sharp_benchmarks"])
    target_specs = []
    for rel in (0.05, 0.10, 0.15): target_specs.append((f"consensus_rel_{rel:.2f}", target_for(p1, elo, consensus1, consensust, rel)))
    for i, book in enumerate(fx["sharp_benchmarks"]):
        target_specs.append((f"book_{i+1}_rel_0.10", target_for(p1, elo, de_vig(book["decimal_1x2"]), de_vig(book["decimal_total_2_5"]), 0.10)))
    models = []
    for name, target in target_specs:
        for base_name, base in (("dc", standard_base), ("pace_mixture", mixture_base)):
            matrix = maxent_tilt(base, target)
            models.append({"name": f"{name}_{base_name}", "target": target, "matrix": matrix})
    central_models = [m["matrix"] for m in models if m["name"] in {"consensus_rel_0.10_dc", "consensus_rel_0.10_pace_mixture"}]
    central_matrix = sum(central_models) / len(central_models)
    snapshot = ROOT / (ROOT / "data/raw/polymarket/LATEST_SEMIFINALS.txt").read_text(encoding="utf-8").strip()
    with snapshot.open(encoding="utf-8-sig", newline="") as f: market_rows = list(csv.DictReader(f))
    out = []
    derivative_benchmarks = fx.get("derivative_benchmarks", {})
    derivative_weight = 0.90
    thresholds = {"standard": (0.020, 0.005), "medium": (0.030, 0.0075), "low": (0.040, 0.010)}
    for r in market_rows:
        probs = np.array([contract_probability(r["group"], r["contract"], m, fx["home"], fx["away"], fx["knockout_assumptions"]) for m in [x["matrix"] for x in models]])
        central_yes = contract_probability(r["group"], r["contract"], central_matrix, fx["home"], fx["away"], fx["knockout_assumptions"])
        p10, p90 = map(float, np.quantile(probs, [0.10, 0.90]))
        cls = confidence_class(r["group"], r["contract"]); required, buffer = thresholds[cls]
        derivative = derivative_benchmarks.get(f'{r["group"]}|{r["contract"]}')
        candidates = []
        for side in ("yes", "no"):
            if r[f"{side}_ask"] in (None, "") or r[f"{side}_bid"] in (None, ""): continue
            ask, bid = float(r[f"{side}_ask"]), float(r[f"{side}_bid"])
            model_prob = central_yes if side == "yes" else 1-central_yes
            model_conservative = p10 if side == "yes" else 1-p90
            if derivative:
                external_prob = float(derivative[side])
                prob = derivative_weight*external_prob + (1-derivative_weight)*model_prob
                conservative = derivative_weight*external_prob + (1-derivative_weight)*model_conservative
            else:
                external_prob = None
                prob = model_prob
                conservative = model_conservative
            rate = float(r.get("fee_rate") or 0.05); trading_fee = fee(ask, rate)
            robust = conservative-ask-trading_fee-buffer
            candidates.append({"side": side.upper(), "ask": ask, "bid": bid, "prob": prob,
                               "conservative": conservative, "fee": trading_fee, "robust": robust,
                               "central_net": prob-ask-trading_fee,
                               "external_prob": external_prob,
                               "depth": float(r.get(f"{side}_ask_depth_1c") or 0)})
        if not candidates:
            continue
        best = max(candidates, key=lambda x: x["robust"])
        spread = best["ask"]-best["bid"]; volume = float(r.get("market_volume") or 0)
        tradable = spread <= 0.02 and best["depth"] >= 500 and volume >= 1000
        decision = "BET_CANDIDATE" if best["robust"] >= required and tradable else "PASS"
        maker_robust = best["conservative"]-best["bid"]-buffer
        maker_decision = "MAKER_VALUE" if maker_robust >= required and spread <= 0.02 and volume >= 1000 else "PASS"
        maker_queue = float(r.get(f'{best["side"].lower()}_bid_depth_at_best') or 0)
        # Price ceiling solved on the market tick grid.
        feasible = [q/10000 for q in range(1, 10000) if best["conservative"]-q/10000-fee(q/10000, float(r.get("fee_rate") or 0.05))-buffer >= required]
        limit = max(feasible, default=0.0)
        if decision == "PASS" and best["central_net"] > 0.01 and limit < best["ask"]: decision = "WATCH"
        full_kelly = max(0.0, best["robust"]/max(1e-9, 1-best["ask"]-best["fee"]))
        amount = min(50.0, 10000*0.025*full_kelly, best["depth"]*0.005) if decision == "BET_CANDIDATE" else 0.0
        out.append({"group": r["group"], "contract": r["contract"], "side": best["side"],
                    "central_probability": round(best["prob"], 6), "spec_p10": round(best["conservative"], 6),
                    "confidence_class": cls,
                    "external_benchmark_probability": "" if best["external_prob"] is None else round(best["external_prob"], 6),
                    "external_benchmark_source": "" if derivative is None else derivative["source"],
                    "ask": best["ask"], "bid": best["bid"], "spread": round(spread, 6),
                    "fee": round(best["fee"], 6), "central_net_edge": round(best["central_net"], 6),
                    "robust_edge": round(best["robust"], 6), "required_edge": required,
                    "maker_robust_edge": round(maker_robust, 6), "maker_decision": maker_decision,
                    "maker_queue_depth_at_price_usd": round(maker_queue, 2),
                    "maker_recommended_amount_10k": 20.0 if maker_decision == "MAKER_VALUE" else 0.0,
                    "max_entry": round(limit, 4), "depth_1c_usd": round(best["depth"], 2),
                    "market_volume": round(volume, 2), "decision": decision,
                    "recommended_amount_10k": round(amount, 2)})
    candidates = sorted([x for x in out if x["decision"] == "BET_CANDIDATE"], key=lambda x: x["robust_edge"], reverse=True)
    if candidates:
        candidates[0]["decision"] = "BET"
        for x in candidates[1:]: x["decision"] = "CORRELATED_PASS"; x["recommended_amount_10k"] = 0.0
    outdir = ROOT / "outputs/model_v5"; outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "all_market_recommendations_v5.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    central_core = core_markets(central_matrix)
    payload = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "snapshot": str(snapshot.relative_to(ROOT)),
               "construct": "minimum-KL maximum-entropy tilt; standard DC and shared-pace mixture; book/weight specification ensemble; derivative-specific sharp benchmark anchoring",
               "models": len(models), "training_rows": len(rows), "p1_lambdas": lam, "elo": {**elo, **elo_info},
               "central": central_core, "bets": [x for x in out if x["decision"] == "BET"],
               "maker_value": [x for x in out if x["maker_decision"] == "MAKER_VALUE"],
               "top_watch": sorted([x for x in out if x["decision"] == "WATCH"], key=lambda x: x["robust_edge"], reverse=True)[:15]}
    (outdir / "summary_v5.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ["# 最大熵 + 节奏混合模型 v5", "",
              f"模型规格数：{len(models)}；快照：`{snapshot.relative_to(ROOT)}`。", "",
              f"核心概率：英格兰胜 {central_core['home']:.1%}，平 {central_core['draw']:.1%}，阿根廷胜 {central_core['away']:.1%}，大2.5 {central_core['over2.5']:.1%}，BTTS {central_core['btts']:.1%}。",
              "", "## 可执行信号", ""]
    bets = [x for x in out if x["decision"] == "BET"]
    if not bets: report.append("没有通过分盘口阈值、模型规格稳健性和外部同类盘口复核的即时吃单。")
    else:
        for x in bets: report.append(f"- {x['contract']} {x['side']}：现价{x['ask']:.2%}，稳健边际{x['robust_edge']:+.2%}，建议${x['recommended_amount_10k']:.2f}/$10k。")
    report += ["", "## Maker-only 价值挂单", ""]
    maker_value = [x for x in out if x["maker_decision"] == "MAKER_VALUE"]
    if not maker_value: report.append("没有通过稳健阈值的被动挂单。")
    for x in maker_value:
        report.append(f"- {x['contract']} {x['side']} 限价 {x['bid']:.2%}：不付 taker fee 时稳健边际 {x['maker_robust_edge']:+.2%}；建议不超过 ${x['maker_recommended_amount_10k']:.2f}/$10k。")
    report += ["", "## 最接近的观察项", "", "| 合约 | 方向 | 现价 | 中心净边际 | 规格稳健边际 | 入场上限 |", "|---|---|---:|---:|---:|---:|"]
    for x in sorted(out, key=lambda x: x["robust_edge"], reverse=True)[:12]:
        report.append(f"| {x['contract']} | {x['side']} | {x['ask']:.2%} | {x['central_net_edge']:+.2%} | {x['robust_edge']:+.2%} | {x['max_entry']:.2%} |")
    (outdir / "report_v5.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"models": len(models), "bets": len(bets), "report": str(outdir/'report_v5.md')}, ensure_ascii=False))


if __name__ == "__main__": main()
