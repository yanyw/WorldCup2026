from __future__ import annotations

import argparse
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
    return rate*price*(1-price)


def target_for(p1: dict, elo: dict, sharp1: dict, sharpt: dict, rel: float) -> dict:
    independent = {key: .75*p1[key]+.25*elo[key] for key in ("home", "draw", "away")}
    return {
        "home": sharp1["home"]+rel*(independent["home"]-sharp1["home"]),
        "draw": sharp1["draw"]+rel*(independent["draw"]-sharp1["draw"]),
        "away": sharp1["away"]+rel*(independent["away"]-sharp1["away"]),
        "over2.5": sharpt["over"]+rel*(p1["over2.5"]-sharpt["over"]),
    }


def max_entry(conservative: float, rate: float, buffer: float, required: float) -> float:
    feasible = [q/10000 for q in range(1, 10000)
                if conservative-q/10000-fee(q/10000, rate)-buffer >= required]
    return max(feasible, default=0.0)


def fit_fixture_models(cfg: dict, fixtures: list[dict]) -> tuple[dict, dict]:
    cutoff = date.fromisoformat(cfg["data"]["cutoff_exclusive"])
    rows = load_results_with_overrides(
        ROOT/cfg["data"]["historical_results"],
        date.fromisoformat(cfg["data"]["training_start"]), cutoff,
        ROOT/cfg["data"]["regulation_overrides"],
    )
    pcfg = cfg["poisson"]
    pmodel = RidgePoisson(pcfg["half_life_days"], pcfg["ridge"], pcfg).fit(rows, cutoff)
    all_lh, all_la = pmodel.lambdas_for_rows(rows)
    rho = estimate_dc_rho(rows, all_lh, all_la, cutoff, pcfg["half_life_days"])
    fitted = {}
    for fx in fixtures:
        raw_lam = pmodel.predict(fx["home"], fx["away"], fx["neutral"])
        stage_mult = float(fx.get("stage_goal_multiplier", 1.0))
        lam = (raw_lam[0]*stage_mult, raw_lam[1]*stage_mult)
        dc = dc_matrix(*lam, rho, pcfg["max_goals"])
        pace = common_pace_mixture(dc_matrix, *lam, rho, pcfg["max_goals"])
        p1 = core_markets(dc)
        elo, elo_info = elo_probabilities(rows, fx["home"], fx["away"], fx["neutral"])
        sharp1, sharpt = sharp_consensus(fx["sharp_benchmarks"])
        central_rel = float(fx.get("independent_reliability_vs_sharp", .20))
        central_target = target_for(p1, elo, sharp1, sharpt, central_rel)
        specs = []
        for rel in (max(.05, central_rel-.05), central_rel, min(.40, central_rel+.05)):
            specs.append((f"consensus_rel_{rel:.2f}", target_for(p1, elo, sharp1, sharpt, rel)))
        for i, book in enumerate(fx["sharp_benchmarks"]):
            specs.append((f"book_{i+1}_rel_{central_rel:.2f}",
                          target_for(p1, elo, de_vig(book["decimal_1x2"]),
                                     de_vig(book["decimal_total_2_5"]), central_rel)))
        uncertainty = fx.get("target_uncertainty", {})
        share_shift = float(uncertainty.get("one_x_two_share_shift", .02))
        total_shift = float(uncertainty.get("over2_5_pp", .025))
        specs.extend([
            ("home_share_up", {**central_target, "home": central_target["home"]+share_shift,
                               "away": central_target["away"]-share_shift}),
            ("away_share_up", {**central_target, "home": central_target["home"]-share_shift,
                               "away": central_target["away"]+share_shift}),
            ("total_low", {**central_target, "over2.5": max(.05, central_target["over2.5"]-total_shift)}),
            ("total_high", {**central_target, "over2.5": min(.95, central_target["over2.5"]+total_shift)}),
        ])
        models = []
        for name, target in specs:
            for base_name, base in (("dc", dc), ("pace_mixture", pace)):
                models.append({"name": f"{name}_{base_name}", "matrix": maxent_tilt(base, target)})
        central = [x["matrix"] for x in models
                   if x["name"] in {f"consensus_rel_{central_rel:.2f}_dc",
                                     f"consensus_rel_{central_rel:.2f}_pace_mixture"}]
        central_matrix = sum(central)/len(central)
        fitted[fx["fixture_id"]] = {
            "fixture": fx, "raw_lambdas": raw_lam, "stage_lambdas": lam,
            "stage_multiplier": stage_mult, "p1": p1, "elo": {**elo, **elo_info},
            "sharp_1x2": sharp1, "sharp_total": sharpt, "rho": rho,
            "models": models, "central_matrix": central_matrix,
        }
    return fitted, {"training_rows": len(rows), "cutoff_exclusive": cutoff.isoformat(),
                    "latest_result": max(row["date"] for row in rows).isoformat(), "rho": rho}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/model_config_v3.json")
    ap.add_argument("--fixtures", default="data/inputs/remaining_20260716.json")
    ap.add_argument("--snapshot", default=None)
    ap.add_argument("--output-dir", default="outputs/model_v6")
    args = ap.parse_args()
    cfg = json.loads((ROOT/args.config).read_text(encoding="utf-8"))
    doc = json.loads((ROOT/args.fixtures).read_text(encoding="utf-8"))
    fixtures = doc["fixtures"]
    fitted, audit = fit_fixture_models(cfg, fixtures)
    snapshot = ROOT/(args.snapshot or (ROOT/"data/raw/polymarket/LATEST_SEMIFINALS.txt").read_text(encoding="utf-8").strip())
    with snapshot.open(encoding="utf-8-sig", newline="") as handle:
        market_rows = list(csv.DictReader(handle))

    base_thresholds = {"standard": (.020, .005), "medium": (.030, .0075), "low": (.040, .010)}
    out = []
    for row in market_rows:
        fit = fitted.get(row["fixture_id"])
        if fit is None:
            continue
        fx = fit["fixture"]
        assumptions = fx["knockout_assumptions"]
        probs = np.array([contract_probability(row["group"], row["contract"], model["matrix"],
                                                fx["home"], fx["away"], assumptions)
                          for model in fit["models"]])
        central_yes = contract_probability(row["group"], row["contract"], fit["central_matrix"],
                                           fx["home"], fx["away"], assumptions)
        p10, p90 = map(float, np.quantile(probs, [.10, .90]))
        cls = confidence_class(row["group"], row["contract"])
        required, buffer = base_thresholds[cls]
        if "third-place" in fx["stage"].lower():
            required += .010
            buffer += .005
        candidates = []
        for side in ("yes", "no"):
            if row.get(f"{side}_ask") in (None, "") or row.get(f"{side}_bid") in (None, ""):
                continue
            ask, bid = float(row[f"{side}_ask"]), float(row[f"{side}_bid"])
            prob = central_yes if side == "yes" else 1-central_yes
            conservative = p10 if side == "yes" else 1-p90
            rate = float(row.get("fee_rate") or .05)
            taker_fee = fee(ask, rate)
            candidates.append({
                "side": side.upper(), "prob": prob, "conservative": conservative,
                "ask": ask, "bid": bid, "fee": taker_fee,
                "central_net": prob-ask-taker_fee,
                "robust": conservative-ask-taker_fee-buffer,
                "maker_robust": conservative-bid-buffer,
                "ask_depth": float(row.get(f"{side}_ask_depth_1c") or 0),
                "maker_queue": float(row.get(f"{side}_bid_depth_at_best") or 0),
            })
        if not candidates:
            continue
        best = max(candidates, key=lambda x: x["robust"])
        spread = best["ask"]-best["bid"]
        volume = float(row.get("market_volume") or 0)
        liquid = spread <= .02 and best["ask_depth"] >= 500 and volume >= 1000
        decision = "BET_CANDIDATE" if best["robust"] >= required and liquid else "PASS"
        maker = "MAKER_VALUE" if best["maker_robust"] >= required and spread <= .02 and volume >= 1000 else "PASS"
        limit = max_entry(best["conservative"], float(row.get("fee_rate") or .05), buffer, required)
        if decision == "PASS" and best["central_net"] > .01:
            decision = "WATCH"
        out.append({
            "fixture_id": row["fixture_id"], "stage": fx["stage"], "group": row["group"],
            "contract": row["contract"], "side": best["side"],
            "central_probability": round(best["prob"], 6), "spec_p10": round(best["conservative"], 6),
            "confidence_class": cls, "ask": best["ask"], "bid": best["bid"],
            "spread": round(spread, 6), "fee": round(best["fee"], 6),
            "central_net_edge": round(best["central_net"], 6), "robust_edge": round(best["robust"], 6),
            "required_edge": round(required, 6), "max_taker_entry": round(limit, 4),
            "ask_depth_1c_usd": round(best["ask_depth"], 2), "market_volume": round(volume, 2),
            "decision": decision, "recommended_amount_10k": 50.0 if decision == "BET_CANDIDATE" else 0.0,
            "maker_robust_edge": round(best["maker_robust"], 6), "maker_decision": maker,
            "maker_queue_depth_at_price_usd": round(best["maker_queue"], 2),
            "maker_recommended_amount_10k": 20.0 if maker == "MAKER_VALUE" else 0.0,
        })

    # One taker position per fixture: other qualifying contracts are correlated manifestations.
    for fixture_id in fitted:
        choices = sorted([x for x in out if x["fixture_id"] == fixture_id and x["decision"] == "BET_CANDIDATE"],
                         key=lambda x: x["robust_edge"], reverse=True)
        if choices:
            choices[0]["decision"] = "BET"
            for item in choices[1:]:
                item["decision"] = "CORRELATED_PASS"; item["recommended_amount_10k"] = 0.0
        maker_choices = sorted([x for x in out if x["fixture_id"] == fixture_id and x["maker_decision"] == "MAKER_VALUE"],
                               key=lambda x: x["maker_robust_edge"], reverse=True)
        if maker_choices:
            maker_choices[0]["maker_decision"] = "MAKER_PRIMARY"
            for item in maker_choices[1:]:
                item["maker_decision"] = "MAKER_ALTERNATIVE"; item["maker_recommended_amount_10k"] = 0.0

    outdir = ROOT/args.output_dir; outdir.mkdir(parents=True, exist_ok=True)
    with (outdir/"all_market_recommendations_v6.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0])); writer.writeheader(); writer.writerows(out)

    fixture_summaries = []
    for fixture_id, fit in fitted.items():
        fx = fit["fixture"]; core = core_markets(fit["central_matrix"])
        draw = core["draw"]
        home_adv = core["home"]+(1-float(fx["knockout_assumptions"]["away_share_if_90m_draw"]))*draw
        scores = []
        matrix = fit["central_matrix"]
        expected_home = float(sum(h*matrix[h, a] for h in range(matrix.shape[0]) for a in range(matrix.shape[1])))
        expected_away = float(sum(a*matrix[h, a] for h in range(matrix.shape[0]) for a in range(matrix.shape[1])))
        scoreless = float(matrix[0, 0])
        first_home = (1-scoreless)*expected_home/max(expected_home+expected_away, 1e-12)
        first_away = (1-scoreless)*expected_away/max(expected_home+expected_away, 1e-12)
        over15 = float(sum(matrix[h, a] for h in range(matrix.shape[0]) for a in range(matrix.shape[1]) if h+a >= 2))
        over35 = float(sum(matrix[h, a] for h in range(matrix.shape[0]) for a in range(matrix.shape[1]) if h+a >= 4))
        model_cores = [core_markets(model["matrix"]) for model in fit["models"]]
        spec_ranges = {key: {"p10": float(np.quantile([x[key] for x in model_cores], .10)),
                             "p90": float(np.quantile([x[key] for x in model_cores], .90))}
                       for key in ("home", "draw", "away", "over2.5", "btts")}
        for h in range(matrix.shape[0]):
            for a in range(matrix.shape[1]): scores.append({"score": f"{h}-{a}", "probability": float(matrix[h, a])})
        scores.sort(key=lambda x: x["probability"], reverse=True)
        fixture_summaries.append({
            "fixture_id": fixture_id, "home": fx["home"], "away": fx["away"], "stage": fx["stage"],
            "kickoff_beijing": fx["kickoff_beijing"], "raw_lambdas": fit["raw_lambdas"],
            "stage_lambdas": fit["stage_lambdas"], "stage_goal_multiplier": fit["stage_multiplier"],
            "sharp_1x2": fit["sharp_1x2"], "sharp_total": fit["sharp_total"],
            "independent": fit["p1"], "elo": fit["elo"], "central": core,
            "specification_ranges": spec_ranges,
            "home_win_including_tiebreak": home_adv, "away_win_including_tiebreak": 1-home_adv,
            "derived": {"expected_goals_home": expected_home, "expected_goals_away": expected_away,
                        "over1.5": over15, "over3.5": over35, "scoreless": scoreless,
                        "first_goal_home": first_home, "first_goal_away": first_away,
                        "penalties": draw*float(fx["knockout_assumptions"]["penalties_given_90m_draw"])},
            "top_scores": scores[:12],
            "bets": [x for x in out if x["fixture_id"] == fixture_id and x["decision"] == "BET"],
            "maker_value": [x for x in out if x["fixture_id"] == fixture_id and x["maker_decision"] in {"MAKER_PRIMARY", "MAKER_ALTERNATIVE"}],
            "top_watch": sorted([x for x in out if x["fixture_id"] == fixture_id and x["decision"] == "WATCH"],
                                key=lambda x: x["robust_edge"], reverse=True)[:10],
        })
    payload = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "snapshot": str(snapshot.relative_to(ROOT)), "audit": audit,
               "construct": "v6 postmortem update: actual semifinal override, 20% independent-data weight, stage-specific pace, max-entropy coherent score matrix, specification ensemble",
               "fixtures": fixture_summaries}
    (outdir/"summary_v6.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = ["# 世界杯剩余两场模型 v6", "", f"盘口快照：`{snapshot.relative_to(ROOT)}`；训练截止：{audit['cutoff_exclusive']}（不含）。", ""]
    for item in fixture_summaries:
        c = item["central"]
        d = item["derived"]
        report += [f"## {item['home']} vs {item['away']}", "",
                   f"- 90分钟：{item['home']} {c['home']:.2%} / 平 {c['draw']:.2%} / {item['away']} {c['away']:.2%}",
                   f"- 最终胜者：{item['home']} {item['home_win_including_tiebreak']:.2%} / {item['away']} {item['away_win_including_tiebreak']:.2%}",
                   f"- 期望进球：{d['expected_goals_home']:.2f}–{d['expected_goals_away']:.2f}",
                   f"- 大1.5 {d['over1.5']:.2%}；大2.5 {c['over2.5']:.2%}；大3.5 {d['over3.5']:.2%}；BTTS {c['btts']:.2%}",
                   f"- 加时 {c['draw']:.2%}；点球大战 {d['penalties']:.2%}；首球 {item['home']} {d['first_goal_home']:.2%} / {item['away']} {d['first_goal_away']:.2%} / 无进球 {d['scoreless']:.2%}",
                   f"- 最可能比分："+"、".join(f"{x['score']} {x['probability']:.1%}" for x in item['top_scores'][:5]), "",
                   "### 吃单", ""]
        if not item["bets"]: report.append("没有通过稳健边际、手续费与流动性过滤的吃单。")
        for bet in item["bets"]:
            report.append(f"- {bet['contract']} {bet['side']} @ {bet['ask']:.3f}，稳健边际 {bet['robust_edge']:+.2%}，每$10k建议 ${bet['recommended_amount_10k']:.0f}。")
        report += ["", "### Maker-only", ""]
        if not item["maker_value"]: report.append("没有通过阈值的被动挂单。")
        for bet in item["maker_value"]:
            label = "首选" if bet["maker_decision"] == "MAKER_PRIMARY" else "备选（与首选二选一）"
            amount = bet["maker_recommended_amount_10k"] if bet["maker_decision"] == "MAKER_PRIMARY" else 20.0
            report.append(f"- {label}：{bet['contract']} {bet['side']} 限价 {bet['bid']:.3f}，稳健maker边际 {bet['maker_robust_edge']:+.2%}，若选择该项每$10k不超过 ${amount:.0f}。")
        report.append("")
    (outdir/"prediction_and_betting_report_v6.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"fixtures": len(fixture_summaries), "markets": len(out),
                      "bets": sum(len(x["bets"]) for x in fixture_summaries),
                      "maker_value": sum(len(x["maker_value"]) for x in fixture_summaries),
                      "report": str(outdir/"prediction_and_betting_report_v6.md")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
