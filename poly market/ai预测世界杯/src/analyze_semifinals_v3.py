from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

from wc_model.ensemble import coherent_fusion_consensus, scenario_matrices
from wc_model.historical import (RidgePoisson, elo_probabilities,
                                 estimate_dc_rho, load_results_with_overrides)
from wc_model.score import core_markets, dc_matrix
from wc_model.valuation import confidence_class, contract_probability
from wc_model.game_attributes import apply_game_adjustment

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fee_per_share(price: float, rate: float) -> float:
    return rate * price * (1.0 - price)


def liquidity_grade(depth: float) -> str:
    return "A" if depth >= 7500 else "B" if depth >= 2500 else "C" if depth >= 500 else "D"


def max_entry(conservative: float, rate: float, buffers: float, required: float) -> float:
    feasible = [q / 10000 for q in range(1, 10000)
                if conservative - q / 10000 - fee_per_share(q / 10000, rate) - buffers >= required]
    return max(feasible, default=0.0)


def fit_models(cfg: dict, fixtures: list[dict]) -> tuple[dict, dict]:
    cutoff = date.fromisoformat(cfg["data"]["cutoff_exclusive"])
    start = date.fromisoformat(cfg["data"]["training_start"])
    rows = load_results_with_overrides(
        ROOT / cfg["data"]["historical_results"], start, cutoff,
        ROOT / cfg["data"]["regulation_overrides"],
    )
    pcfg = cfg["poisson"]
    p1m = RidgePoisson(pcfg["half_life_days"], pcfg["ridge"], pcfg).fit(rows, cutoff)
    all_lh, all_la = p1m.lambdas_for_rows(rows)
    rho = estimate_dc_rho(rows, all_lh, all_la, cutoff, pcfg["half_life_days"])
    out = {}
    for fx in fixtures:
        lam = p1m.predict(fx["home"], fx["away"], fx["neutral"])
        p1 = core_markets(dc_matrix(*lam, rho, pcfg["max_goals"]))
        elo, elo_info = elo_probabilities(rows, fx["home"], fx["away"], fx["neutral"])
        fused = coherent_fusion_consensus(lam, rho, p1, elo, fx["sharp_benchmarks"], cfg["ensemble"], pcfg["max_goals"])
        game_audit = None
        scenario_cfg = cfg["ensemble"]
        if fx.get("game_model") and fx.get("fc26_ratings"):
            game = read_json(ROOT / fx["game_model"])
            ratings = read_json(ROOT / fx["fc26_ratings"])
            game["method"].setdefault("base_uncertainty_lambda_pct", cfg["ensemble"]["uncertainty_lambda_pct"])
            game["method"].setdefault("base_uncertainty_share_shift", cfg["ensemble"]["uncertainty_share_shift"])
            fused, game_audit, scenario_cfg = apply_game_adjustment(
                fused, fx, game, ratings, pcfg["max_goals"]
            )
        scenarios = scenario_matrices(fused["lambda_home"], fused["lambda_away"], fused["rho"], scenario_cfg, pcfg["max_goals"])
        out[fx["fixture_id"]] = {"fixture": fx, "p1": p1, "p1_lambdas": lam,
                                 "elo": {**elo, **elo_info}, "fused": fused, "scenarios": scenarios,
                                 "game_model": game_audit}
    audit = {"training_rows": len(rows), "latest_result": max(r["date"] for r in rows).isoformat(),
             "cutoff_exclusive": cutoff.isoformat(), "rho": rho,
             "regulation_overrides": cfg["data"]["regulation_overrides"]}
    return out, audit


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/model_config_v3.json")
    ap.add_argument("--fixtures", default="data/inputs/semifinals_20260712.json")
    ap.add_argument("--snapshot", default=None)
    ap.add_argument("--output-dir", default="outputs/model_v3")
    ap.add_argument("--prefix", default="semifinal")
    args = ap.parse_args()
    cfg = read_json(ROOT / args.config)
    fixture_doc = read_json(ROOT / args.fixtures)
    fixtures = fixture_doc["fixtures"]
    snapshot = ROOT / (args.snapshot or (ROOT / "data/raw/polymarket/LATEST_SEMIFINALS.txt").read_text(encoding="utf-8").strip())
    models, audit = fit_models(cfg, fixtures)
    fx_by_id = {x["fixture_id"]: x for x in fixtures}
    excfg = cfg["execution"]
    bankroll = float(excfg["bankroll"])
    now = datetime.now(timezone.utc)
    rows = []
    with snapshot.open(encoding="utf-8-sig", newline="") as f:
        market_rows = list(csv.DictReader(f))
    for raw in market_rows:
        model = models[raw["fixture_id"]]
        fx = fx_by_id[raw["fixture_id"]]
        assumptions = fx["knockout_assumptions"]
        vals = np.array([contract_probability(raw["group"], raw["contract"], m,
                                               fx["home"], fx["away"], assumptions)
                         for m in model["scenarios"]])
        central = contract_probability(raw["group"], raw["contract"], model["fused"]["matrix"],
                                       fx["home"], fx["away"], assumptions)
        p10, p90 = map(float, np.quantile(vals, [0.10, 0.90]))
        conf = confidence_class(raw["group"], raw["contract"])
        confidence_buffer = float(excfg["low_confidence_extra_buffer"]) if conf == "low" else 0.0
        hours = (datetime.fromisoformat(fx["kickoff_utc"].replace("Z", "+00:00")) - now).total_seconds() / 3600
        early = hours > float(excfg["early_hours"])
        candidates = []
        for side in ("yes", "no"):
            ask_raw, bid_raw = raw[f"{side}_ask"], raw[f"{side}_bid"]
            if ask_raw in ("", None) or bid_raw in ("", None):
                continue
            ask, bid = float(ask_raw), float(bid_raw)
            prob = central if side == "yes" else 1.0 - central
            conservative = p10 if side == "yes" else 1.0 - p90
            depth = float(raw[f"{side}_ask_depth_1c"] or 0)
            rate = float(raw["fee_rate"] or 0.05)
            fee = fee_per_share(ask, rate)
            buffers = float(excfg["execution_buffer"]) + confidence_buffer
            robust = conservative - ask - fee - buffers
            candidates.append({"side": side.upper(), "prob": prob, "conservative": conservative,
                               "ask": ask, "bid": bid, "spread": ask - bid, "depth": depth,
                               "fee": fee, "central_net": prob - ask - fee, "robust": robust,
                               "buffers": buffers, "rate": rate})
        if not candidates:
            continue
        best = max(candidates, key=lambda x: x["robust"])
        volume = float(raw["market_volume"] or 0)
        grade = liquidity_grade(best["depth"])
        max_spread = float(excfg["early_max_spread"] if early else excfg["normal_max_spread"])
        tradable = (grade in ("A", "B") and best["spread"] <= max_spread and
                    (not early or volume >= float(excfg["early_min_volume"])))
        required = float(excfg["required_robust_edge"])
        decision = "BET_CANDIDATE" if best["robust"] >= required and tradable else "PASS"
        limit = max_entry(best["conservative"], best["rate"], best["buffers"], required)
        if decision == "PASS" and limit > 0 and limit < best["ask"] and best["central_net"] > 0:
            decision = "LIMIT_WATCH"
        full_kelly = max(0.0, best["robust"] / max(1e-9, 1.0 - best["ask"] - best["fee"]))
        amount = min(bankroll * float(excfg["max_stake_fraction"]),
                     bankroll * float(excfg["kelly_fraction"]) * full_kelly,
                     best["depth"] * float(excfg["max_orderbook_fraction"]))
        rows.append({
            "fixture_id": raw["fixture_id"], "home": fx["home"], "away": fx["away"],
            "kickoff_beijing": fx["kickoff_beijing"], "hours_to_kickoff": round(hours, 2),
            "early_regime": early, "group": raw["group"], "contract": raw["contract"],
            "side": best["side"], "model_probability": round(best["prob"], 6),
            "conservative_probability": round(best["conservative"], 6),
            "ask": round(best["ask"], 6), "bid": round(best["bid"], 6),
            "spread": round(best["spread"], 6), "fee_per_share": round(best["fee"], 6),
            "depth_within_1c_usd": round(best["depth"], 2), "market_volume": round(volume, 2),
            "liquidity_grade": grade, "central_net_edge": round(best["central_net"], 6),
            "robust_edge": round(best["robust"], 6), "max_entry_for_5pp": round(limit, 4),
            "recommended_amount_10k": round(amount, 2), "decision": decision,
        })

    # Correlated contracts are not separate bankroll opportunities: keep only the
    # strongest executable candidate per match and downgrade the rest.
    for fid in models:
        candidates = [r for r in rows if r["fixture_id"] == fid and r["decision"] == "BET_CANDIDATE"]
        candidates.sort(key=lambda r: r["robust_edge"], reverse=True)
        if candidates:
            candidates[0]["decision"] = "BET"
            for r in candidates[1:]:
                r["decision"] = "CORRELATED_PASS"
                r["recommended_amount_10k"] = 0.0

    outdir = ROOT / args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)
    csvpath = outdir / f"{args.prefix}_all_market_recommendations.csv"
    with csvpath.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    summaries = {}
    for fid, model in models.items():
        mk = model["fused"]["markets"]
        fx = model["fixture"]
        summaries[fid] = {
            "home": fx["home"], "away": fx["away"], "kickoff_beijing": fx["kickoff_beijing"],
            "lambda_home": model["fused"]["lambda_home"], "lambda_away": model["fused"]["lambda_away"],
            "home_90m": mk["home"], "draw_90m": mk["draw"], "away_90m": mk["away"],
            "over2_5": mk["over2.5"], "btts": mk["btts"],
            "sharp_1x2": model["fused"]["sharp_1x2"], "independent_1x2": model["fused"]["independent_1x2"],
            "game_model": model["game_model"],
            "bets": [r for r in rows if r["fixture_id"] == fid and r["decision"] == "BET"],
            "watches": sorted([r for r in rows if r["fixture_id"] == fid and r["decision"] == "LIMIT_WATCH"],
                              key=lambda r: r["central_net_edge"], reverse=True)[:10],
        }
    payload = {"generated_at_utc": now.isoformat(), "snapshot": str(snapshot.relative_to(ROOT)),
               "audit": audit, "configuration": args.config, "fixtures": summaries,
               "contracts_evaluated": len(rows), "bet_count": sum(r["decision"] == "BET" for r in rows)}
    (outdir / f"{args.prefix}_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ["# 世界杯后续比赛 Polymarket 预测与交易报告（v4）", "",
              f"生成时间（UTC）：{now.isoformat()}；盘口快照：`{snapshot.relative_to(ROOT)}`。", "",
              "## 核心预测", "",
              "| 比赛（北京时间） | 主胜 | 平 | 客胜 | 大2.5 | BTTS | 预期进球 |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for s in summaries.values():
        report.append(f"| {s['home']}–{s['away']}（{s['kickoff_beijing']}） | {s['home_90m']:.1%} | {s['draw_90m']:.1%} | {s['away_90m']:.1%} | {s['over2_5']:.1%} | {s['btts']:.1%} | {s['lambda_home']:.2f}–{s['lambda_away']:.2f} |")
    if any(s["game_model"] for s in summaries.values()):
        report += ["", "## 游戏属性与临场因素审计", "",
                   "| 比赛 | FC26首发均值 | 综合属性差（主-客） | 阵型 | 主/客λ乘数 |",
                   "|---|---:|---:|---|---:|"]
        for s in summaries.values():
            gm = s["game_model"]
            if not gm:
                continue
            hp, ap = gm["profiles"][s["home"]], gm["profiles"][s["away"]]
            forms = gm["projected_formations"]
            report.append(
                f"| {s['home']}–{s['away']} | {hp['starting_xi_ovr']:.1f}–{ap['starting_xi_ovr']:.1f} | "
                f"{gm['rating_edge_home_minus_away']:+.2f} | {forms[s['home']]} vs {forms[s['away']]} | "
                f"{gm['home_lambda_multiplier']:.3f}/{gm['away_lambda_multiplier']:.3f} |"
            )
        report += ["", "FC 26 属性只以12%可靠度修正尖锐赔率/Elo/Poisson基线；裁判不做方向性偏置，只提高总进球尾部与情景不确定性。"]
    report += ["", "## 可执行建议", ""]
    bets = [r for r in rows if r["decision"] == "BET"]
    if not bets:
        report.append("当前没有合约同时通过 5pp 稳健边际、订单簿深度、成交量和价差过滤；建议不追价。")
    else:
        report += ["| 比赛 | 合约与方向 | 限价/当前卖价 | 稳健边际 | 建议金额（$10k本金） |",
                   "|---|---|---:|---:|---:|"]
        for r in bets:
            report.append(f"| {r['home']}–{r['away']} | {r['contract']} {r['side']} | {r['max_entry_for_5pp']:.2%}/{r['ask']:.2%} | {r['robust_edge']:+.1%} | ${r['recommended_amount_10k']:.2f} |")
    report += ["", "## 条件限价观察单（不按当前卖价追单）", "",
               "| 比赛 | 合约与方向 | 当前卖价 | 5pp最高入场价 | 中心净边际 | 流动性 |",
               "|---|---|---:|---:|---:|---:|"]
    watches = sorted([r for r in rows if r["decision"] == "LIMIT_WATCH"], key=lambda r: r["central_net_edge"], reverse=True)[:15]
    for r in watches:
        report.append(f"| {r['home']}–{r['away']} | {r['contract']} {r['side']} | {r['ask']:.2%} | {r['max_entry_for_5pp']:.2%} | {r['central_net_edge']:+.1%} | {r['liquidity_grade']} |")
    report += ["", "## 风险纪律", "",
               "早盘允许观察 3c 价差，但不会降低 5pp 稳健边际；成交量不足 $1,000 的盘口不执行。高度相关盘口每场只保留一个下注，单场上限为本金 0.5%，并以 2.5% Kelly 和一档深度 0.5% 进一步压缩。赛前首发、伤病和尖锐赔率变化后必须重跑。",
               "", "该报告是量化研究输出，不保证盈利，也不自动下单。"]
    report_path = outdir / f"{args.prefix}_prediction_report.md"
    report_path.write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"contracts": len(rows), "bets": len(bets), "watches": len(watches),
                      "report": str(report_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
