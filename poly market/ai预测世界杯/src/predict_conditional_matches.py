from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from wc_model.ensemble import coherent_fusion_consensus
from wc_model.historical import (RidgePoisson, elo_probabilities,
                                 estimate_dc_rho, load_results_with_overrides)
from wc_model.score import core_markets, dc_matrix

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cfg = json.loads((ROOT / "config/model_config_v3.json").read_text(encoding="utf-8"))
    start = date.fromisoformat(cfg["data"]["training_start"])
    cutoff = date.fromisoformat(cfg["data"]["cutoff_exclusive"])
    rows = load_results_with_overrides(ROOT / cfg["data"]["historical_results"], start, cutoff,
                                       ROOT / cfg["data"]["regulation_overrides"])
    pcfg = cfg["poisson"]
    model = RidgePoisson(pcfg["half_life_days"], pcfg["ridge"], pcfg).fit(rows, cutoff)
    lhs, las = model.lambdas_for_rows(rows)
    historical_rho = estimate_dc_rho(rows, lhs, las, cutoff, pcfg["half_life_days"])
    fixtures = [
        {"scenario": "若英格兰晋级：决赛", "home": "Spain", "away": "England", "kickoff_beijing": "2026-07-20T03:00:00+08:00"},
        {"scenario": "若阿根廷晋级：决赛", "home": "Spain", "away": "Argentina", "kickoff_beijing": "2026-07-20T03:00:00+08:00"},
        {"scenario": "若英格兰失利：三四名赛", "home": "France", "away": "England", "kickoff_beijing": "2026-07-19T05:00:00+08:00"},
        {"scenario": "若阿根廷失利：三四名赛", "home": "France", "away": "Argentina", "kickoff_beijing": "2026-07-19T05:00:00+08:00"},
    ]
    out = []
    for fx in fixtures:
        lam = model.predict(fx["home"], fx["away"], True)
        p1 = core_markets(dc_matrix(*lam, historical_rho, pcfg["max_goals"]))
        elo, info = elo_probabilities(rows, fx["home"], fx["away"], True)
        target = {k: 0.75*p1[k] + 0.25*elo[k] for k in ("home", "draw", "away")}
        # No future sportsbook quote exists yet.  Use the independent target as a
        # synthetic zero-vig reference solely to obtain a coherent score matrix.
        benchmark = {"decimal_1x2": {k: 1/target[k] for k in target},
                     "decimal_total_2_5": {"over": 1/p1["over2.5"], "under": 1/(1-p1["over2.5"])}}
        local_cfg = dict(cfg["ensemble"]); local_cfg["independent_reliability_vs_sharp"] = 1.0
        fused = coherent_fusion_consensus(lam, historical_rho, p1, elo, [benchmark], local_cfg, pcfg["max_goals"])
        mk = fused["markets"]
        home_share_draw = elo["home"] / max(1e-12, elo["home"] + elo["away"])
        home_advance = mk["home"] + mk["draw"] * home_share_draw
        out.append({**fx, "lambda_home": fused["lambda_home"], "lambda_away": fused["lambda_away"],
                    "home_90m": mk["home"], "draw_90m": mk["draw"], "away_90m": mk["away"],
                    "over2_5": mk["over2.5"], "btts": mk["btts"],
                    "home_advance": home_advance, "away_advance": 1-home_advance,
                    "basis": "independent Ridge-Poisson + pre-warmed Elo; no future market prior",
                    "home_elo": info["home_elo"], "away_elo": info["away_elo"]})
    outdir = ROOT / "outputs/model_v4"; outdir.mkdir(parents=True, exist_ok=True)
    payload = {"as_of": "2026-07-15", "training_rows": len(rows), "conditional_only": True,
               "warning": "Re-run after England-Argentina and after final/third-place sportsbook markets open.",
               "fixtures": out}
    (outdir / "conditional_match_predictions.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ["# 世界杯决赛与三四名赛条件预测", "",
              "以下概率不含尚未开出的未来尖锐赔率，只用于提前情景规划；英格兰–阿根廷结束后必须重跑。", "",
              "| 情景 | 90分钟主胜 | 平 | 客胜 | 主队晋级/夺冠 | 大2.5 | BTTS |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for x in out:
        report.append(f"| {x['scenario']}：{x['home']}–{x['away']} | {x['home_90m']:.1%} | {x['draw_90m']:.1%} | {x['away_90m']:.1%} | {x['home_advance']:.1%} | {x['over2_5']:.1%} | {x['btts']:.1%} |")
    (outdir / "conditional_match_predictions.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"fixtures": len(out), "output": str(outdir / 'conditional_match_predictions.md')}, ensure_ascii=False))


if __name__ == "__main__":
    main()
