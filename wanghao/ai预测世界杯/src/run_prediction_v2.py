from __future__ import annotations

import argparse, csv, json, sys
from datetime import date
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from wc_model.historical import RidgePoisson, elo_probabilities, estimate_dc_rho, load_results
from wc_model.score import core_markets, dc_matrix
from wc_model.ensemble import coherent_fusion, scenario_matrices
from wc_model.valuation import confidence_class, contract_probability


def read_json(path):
    with Path(path).open(encoding="utf-8") as f:return json.load(f)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--fixture",default="data/inputs/norway_england_20260711.json"); ap.add_argument("--config",default="config/model_config.json"); args=ap.parse_args()
    cfg=read_json(ROOT/args.config); fx=read_json(ROOT/args.fixture); cutoff=date.fromisoformat(cfg["data"]["cutoff_exclusive"]); start=date.fromisoformat(cfg["data"]["training_start"])
    rows=load_results(ROOT/cfg["data"]["historical_results"],start,cutoff); pcfg=cfg["poisson"]
    p1m=RidgePoisson(pcfg["half_life_days"],pcfg["ridge"],pcfg).fit(rows,cutoff); p1_lam=p1m.predict(fx["home"],fx["away"],fx["neutral"])
    all_lh,all_la=p1m.lambdas_for_rows(rows); rho=estimate_dc_rho(rows,all_lh,all_la,cutoff,pcfg["half_life_days"])
    p1=core_markets(dc_matrix(*p1_lam,rho,pcfg["max_goals"])); elo,elo_info=elo_probabilities(rows,fx["home"],fx["away"],fx["neutral"])
    fused=coherent_fusion(p1_lam,rho,p1,elo,fx["sharp_benchmark"],cfg["ensemble"],pcfg["max_goals"])
    scenarios=scenario_matrices(fused["lambda_home"],fused["lambda_away"],rho,cfg["ensemble"],pcfg["max_goals"])
    with (ROOT/fx["market_snapshot"]).open(encoding="utf-8",newline="") as f: market_rows=list(csv.DictReader(f))
    out=[]; excfg=cfg["execution"]
    for r in market_rows:
        p=contract_probability(r["group"],r["contract"],fused["matrix"],fx["home"],fx["away"],fx["knockout_assumptions"])
        vals=np.array([contract_probability(r["group"],r["contract"],m,fx["home"],fx["away"],fx["knockout_assumptions"]) for m in scenarios])
        low,high=map(float,np.quantile(vals,[.1,.9])); cls=confidence_class(r["group"],r["contract"]); extra=excfg["low_confidence_extra_buffer"] if cls=="low" else 0
        q=float(r["market_probability"]); buffer=excfg["execution_buffer"]+extra
        yes_edge=low-(q+buffer); no_edge=(1-high)-((1-q)+buffer)
        direction="BUY_YES" if yes_edge>=no_edge else "BUY_NO"; robust=max(yes_edge,no_edge)
        if robust<excfg["required_robust_edge"]: direction="PASS"
        cost=(q+buffer) if direction=="BUY_YES" else ((1-q)+buffer)
        full_k=max(0,robust/max(1e-9,1-cost)) if direction!="PASS" else 0
        stake_frac=min(excfg["max_stake_fraction"],full_k*excfg["kelly_fraction"])
        out.append({**r,"final_probability":f"{p:.6f}","p10":f"{low:.6f}","p90":f"{high:.6f}","confidence":cls,
                    "raw_edge":f"{p-q:.6f}","robust_edge":f"{robust:.6f}","decision":direction,
                    "stake_fraction":f"{stake_frac:.6f}","stake_amount":f"{stake_frac*excfg['bankroll']:.2f}"})
    odir=ROOT/"outputs"/"model_v2"; odir.mkdir(parents=True,exist_ok=True)
    with (odir/"all_market_predictions_v2.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    summary={"fixture":fx,"cutoff_exclusive":cutoff.isoformat(),"no_leakage":max(r["date"] for r in rows)<cutoff,
             "training":{"rows":len(rows),"latest_result":max(r["date"] for r in rows).isoformat(),"p1_fit":p1m.fit_info},
             "p1":{"lambdas":dict(home=p1_lam[0],away=p1_lam[1]),"rho":rho,"markets":p1},"p2_elo":{**elo,**elo_info},
             "fused":{k:v for k,v in fused.items() if k!="matrix"},"signals":[r for r in out if r["decision"]!="PASS"],
             "rules":{"polymarket_used_in_fair_probability":False,**excfg}}
    with (odir/"model_summary_v2.json").open("w",encoding="utf-8") as f:json.dump(summary,f,ensure_ascii=False,indent=2)
    mk=fused["markets"]; eng_adv=1-(mk["home"]+(1-fx["knockout_assumptions"]["away_share_if_90m_draw"])*mk["draw"])
    report=f"""# 世界杯 Polymarket 预测模型 v2 报告\n\n- 比赛：{fx['home']} vs {fx['away']}\n- 截止日（不含）：{cutoff}\n- 历史样本：{len(rows)} 场，最新完成比赛 {max(r['date'] for r in rows)}\n- 信息隔离：Polymarket **未进入**公平概率模型，只用于最后估值\n\n## 模型结果\n\n| 层 | 主胜 | 平 | 客胜 | 大2.5 | BTTS |\n|---|---:|---:|---:|---:|---:|\n| P1 历史DC | {p1['home']:.1%} | {p1['draw']:.1%} | {p1['away']:.1%} | {p1['over2.5']:.1%} | {p1['btts']:.1%} |\n| P2 Elo | {elo['home']:.1%} | {elo['draw']:.1%} | {elo['away']:.1%} | — | — |\n| 融合最终 | {mk['home']:.1%} | {mk['draw']:.1%} | {mk['away']:.1%} | {mk['over2.5']:.1%} | {mk['btts']:.1%} |\n\n最终预期进球：{fx['home']} {fused['lambda_home']:.3f}，{fx['away']} {fused['lambda_away']:.3f}；{fx['away']}晋级约 {eng_adv:.1%}。\n\n## 交易过滤\n\n共评估 {len(out)} 个合约，达到稳健边际阈值的合约：{len(summary['signals'])} 个。稳健边际使用情景分布第10/90百分位，并扣除执行缓冲；低置信度盘口另加缓冲。\n\n## 研究边界\n\nP1使用国家队历史赛果和时间衰减，P2只审核1X2；传统赔率作为独立于Polymarket的市场知情基准。当前没有球员级xG和可成交订单簿深度，因此不会将半场、晋级或正确比分的微小偏差升级为真实交易建议。\n"""
    (odir/"prediction_report_v2.md").write_text(report,encoding="utf-8")
    print(json.dumps({"lambda_home":fused["lambda_home"],"lambda_away":fused["lambda_away"],"markets":mk,"signals":len(summary["signals"])},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
