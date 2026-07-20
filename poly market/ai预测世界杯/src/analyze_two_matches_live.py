from __future__ import annotations

import csv,json,math,sys
from datetime import date
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"src"))
from wc_model.historical import RidgePoisson,elo_probabilities,estimate_dc_rho,load_results
from wc_model.score import core_markets,dc_matrix
from wc_model.ensemble import coherent_fusion,scenario_matrices
from wc_model.valuation import confidence_class,contract_probability

FIXTURES=[ROOT/"data/inputs/norway_england_20260711.json",ROOT/"data/inputs/argentina_switzerland_20260711.json"]

def read_json(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def fee_per_share(price,rate):return float(rate)*price*(1-price)
def grade(depth):return "A" if depth>=7500 else "B" if depth>=2500 else "C" if depth>=500 else "D"
def max_entry(conservative,rate,risk_buffer,required=.05):
    feasible=[q/10000 for q in range(1,10000) if conservative-q/10000-fee_per_share(q/10000,rate)-risk_buffer>=required]
    return max(feasible) if feasible else 0.0

def fit_models(cfg,fixtures):
    cutoff=date.fromisoformat(cfg["data"]["cutoff_exclusive"]);start=date.fromisoformat(cfg["data"]["training_start"]);pcfg=cfg["poisson"]
    rows=load_results(ROOT/cfg["data"]["historical_results"],start,cutoff)
    p1m=RidgePoisson(pcfg["half_life_days"],pcfg["ridge"],pcfg).fit(rows,cutoff)
    lh_all,la_all=p1m.lambdas_for_rows(rows);rho=estimate_dc_rho(rows,lh_all,la_all,cutoff,pcfg["half_life_days"])
    fitted={}
    for fx in fixtures:
        lam=p1m.predict(fx["home"],fx["away"],fx["neutral"]);p1=core_markets(dc_matrix(*lam,rho,pcfg["max_goals"]));elo,ei=elo_probabilities(rows,fx["home"],fx["away"],fx["neutral"])
        fused=coherent_fusion(lam,rho,p1,elo,fx["sharp_benchmark"],cfg["ensemble"],pcfg["max_goals"])
        scenarios=scenario_matrices(fused["lambda_home"],fused["lambda_away"],rho,cfg["ensemble"],pcfg["max_goals"])
        fitted[fx["fixture_id"]]={"fixture":fx,"p1":p1,"p1_lambdas":lam,"elo":{**elo,**ei},"fused":fused,"scenarios":scenarios}
    return fitted,{"training_rows":len(rows),"latest_result":max(r["date"] for r in rows).isoformat(),"rho":rho,"cutoff":cutoff.isoformat()}

def main():
    cfg=read_json(ROOT/"config/model_config.json");fixtures=[read_json(x) for x in FIXTURES]; models,audit=fit_models(cfg,fixtures)
    latest=(ROOT/"data/raw/polymarket/LATEST.txt").read_text(encoding="utf-8").strip(); snap=ROOT/latest
    with snap.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    bankroll=float(cfg["execution"]["bankroll"]);results=[]
    for r in rows:
        model=models[r["fixture_id"]];fx=model["fixture"];ass=fx["knockout_assumptions"]
        p=contract_probability(r["group"],r["contract"],model["fused"]["matrix"],fx["home"],fx["away"],ass)
        vals=np.array([contract_probability(r["group"],r["contract"],m,fx["home"],fx["away"],ass) for m in model["scenarios"]])
        p10,p90=map(float,np.quantile(vals,[.1,.9]));conf=confidence_class(r["group"],r["contract"]);risk_buffer={"standard":.01,"medium":.02,"low":.03}[conf]
        candidates=[]
        for side,prob,conservative in (("YES",p,p10),("NO",1-p,1-p90)):
            ask=float(r[f"{side.lower()}_ask"] or 1);bid=float(r[f"{side.lower()}_bid"] or 0);depth=float(r[f"{side.lower()}_ask_depth_1c"] or 0)
            fee=fee_per_share(ask,float(r["fee_rate"] or .05));central=prob-ask-fee;robust=conservative-ask-fee-risk_buffer
            candidates.append({"side":side,"prob":prob,"conservative":conservative,"ask":ask,"bid":bid,"spread":ask-bid,"depth":depth,"fee":fee,"central":central,"robust":robust})
        best=max(candidates,key=lambda x:x["robust"]);liq=grade(best["depth"])
        full_k=max(0,best["robust"]/max(1e-9,1-best["ask"]-best["fee"]));kelly=bankroll*.05*full_k
        amount=min(75.0,.01*best["depth"],kelly)
        if best["robust"]>=.05 and liq in ("A","B") and best["spread"]<=.02 and amount>=5:decision="BET"
        elif best["robust"]>=.05 and liq=="C" and amount>=5:decision="SMALL_ONLY"
        elif best["central"]>=.03 or best["robust"]>=.02:decision="WATCH"
        else:decision="PASS"
        if decision not in ("BET","SMALL_ONLY"):amount=0
        limit=max_entry(best["conservative"],float(r["fee_rate"] or .05),risk_buffer)
        results.append({**r,"model_yes":f"{p:.6f}","p10_yes":f"{p10:.6f}","p90_yes":f"{p90:.6f}","confidence":conf,
          "best_side":best["side"],"side_model_probability":f"{best['prob']:.6f}","side_conservative_probability":f"{best['conservative']:.6f}",
          "entry_ask":f"{best['ask']:.6f}","entry_bid":f"{best['bid']:.6f}","book_spread":f"{best['spread']:.6f}","fee_per_share":f"{best['fee']:.6f}",
          "depth_within_1c_usd":f"{best['depth']:.2f}","liquidity_grade":liq,"central_net_edge":f"{best['central']:.6f}","robust_edge":f"{best['robust']:.6f}",
          "max_entry_for_5pp":f"{limit:.6f}","decision":decision,"recommended_amount_10k":f"{amount:.2f}"})
    outdir=ROOT/"outputs/two_matches_live";outdir.mkdir(parents=True,exist_ok=True);csvout=outdir/"all_136_market_recommendations.csv"
    with csvout.open("w",encoding="utf-8-sig",newline="") as f:w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    summary={"snapshot":latest,"audit":audit,"models":{},"counts":{}}
    report=["# 2026-07-12 两场世界杯 Polymarket 全盘口建议","",f"盘口快照：`{latest}`（订单簿实时抓取）  ","资金假设：10,000 USDC；仅研究建议，不自动下单。","","## 模型总览","","| 比赛 | P1预期进球 | 最终预期进球 | 主胜 | 平 | 客胜 | 大2.5 | BTTS |","|---|---:|---:|---:|---:|---:|---:|---:|"]
    for fid,model in models.items():
        fx=model["fixture"];mk=model["fused"]["markets"];lh,la=model["fused"]["lambda_home"],model["fused"]["lambda_away"]
        report.append(f"| {fx['home']}–{fx['away']} | {model['p1_lambdas'][0]:.2f}–{model['p1_lambdas'][1]:.2f} | {lh:.2f}–{la:.2f} | {mk['home']:.1%} | {mk['draw']:.1%} | {mk['away']:.1%} | {mk['over2.5']:.1%} | {mk['btts']:.1%} |")
        scores=[];m=model["fused"]["matrix"]
        for h in range(5):
            for a in range(5):scores.append((float(m[h,a]),f"{h}-{a}"))
        scores.sort(reverse=True);summary["models"][fid]={"lambda_home":lh,"lambda_away":la,"markets":mk,"top_scores":scores[:5],"elo":model["elo"]}
    bets=[r for r in results if r["decision"] in ("BET","SMALL_ONLY")];watches=[r for r in results if r["decision"]=="WATCH"]
    report += ["","## 可执行建议","",f"达到5pp稳健优势并通过订单簿过滤：**{len(bets)}个**。",""]
    if bets:
        report += ["| 比赛 | 盘口 | 方向 | 模型保守概率 | Ask+费前 | 稳健优势 | 深度等级 | 建议金额 |","|---|---|---:|---:|---:|---:|---:|---:|"]
        for r in sorted(bets,key=lambda x:float(x["robust_edge"]),reverse=True):report.append(f"| {r['home']}–{r['away']} | {r['contract']} | {r['best_side']} | {float(r['side_conservative_probability']):.1%} | {float(r['entry_ask']):.2%} | {float(r['robust_edge']):+.1%} | {r['liquidity_grade']} | ${r['recommended_amount_10k']} |")
    else:report.append("没有合约同时满足模型下界、费用、模型风险缓冲、价差和深度约束；不应为了必须下注而降低阈值。")
    report += ["","## 观察名单（不建议立即成交）","","| 比赛 | 盘口 | 倾向 | 中央净优势 | 稳健优势 | 当前Ask | 达到5pp所需最高价 | 深度等级 |","|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in sorted(watches,key=lambda x:float(x["central_net_edge"]),reverse=True)[:20]:report.append(f"| {r['home']}–{r['away']} | {r['contract']} | {r['best_side']} | {float(r['central_net_edge']):+.1%} | {float(r['robust_edge']):+.1%} | {float(r['entry_ask']):.2%} | {float(r['max_entry_for_5pp']):.2%} | {r['liquidity_grade']} |")
    report += ["","## 盘口特性与资金规则","","- 主胜平负、主流大小球：优先级最高，通常点差和深度最好。","- 半场、加时、点球、晋级：结构假设较强，额外扣3pp模型风险缓冲。","- 正确比分：尾部误差和多重筛选最严重，即使盘口组总流动性高，也必须查看单个YES/NO token深度。","- 首个进球队伍：事件总流动性最低，模型也只使用竞争风险近似，默认低置信度。","- 金额上限为10,000 USDC资金的0.75%，同时不超过订单簿最佳价1美分范围深度的1%。","- 所有BET都必须使用限价单；首发公布、价格变化超过2pp或订单簿深度骤降时取消。","","完整136个合约见 `all_136_market_recommendations.csv`。"]
    (outdir/"recommendation_report.md").write_text("\n".join(report),encoding="utf-8")
    summary["counts"]={"markets":len(results),"bets":len(bets),"watch":len(watches),"pass":sum(r["decision"]=="PASS" for r in results)}
    (outdir/"analysis_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary["counts"],ensure_ascii=False));print("BET",[(r["fixture_id"],r["contract"],r["best_side"],r["robust_edge"],r["recommended_amount_10k"]) for r in bets])

if __name__=="__main__":main()
