#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
ROOT=Path(__file__).resolve().parents[1]
MODEL_PATH=ROOT/'data'/'model_results_0709.json'
EVIDENCE_PATH=ROOT/'data'/'external_evidence_0709.json'
MARKET_PATH=ROOT/'data'/'polymarket_snapshot_0709.json'
OUTPUT_PATH=ROOT/'data'/'candidate_evaluation_0709.json'
BANKROLL=1000.0

def matrix(h,a,limit=12):
    hp=np.array([math.exp(-h)*h**i/math.factorial(i) for i in range(limit+1)])
    ap=np.array([math.exp(-a)*a**i/math.factorial(i) for i in range(limit+1)])
    m=np.outer(hp,ap); return m/m.sum()
def score_probs(h,a):
    s=matrix(h,a); r={'1x2.home':float(np.tril(s,-1).sum()),'1x2.draw':float(np.trace(s)),'1x2.away':float(np.triu(s,1).sum()),'btts.yes':float(s[1:,1:].sum())}
    r['btts.no']=1-r['btts.yes']
    for line in (1.5,2.5,3.5,4.5):
        over=sum(s[i,j] for i in range(13) for j in range(13) if i+j>line); r[f'totals.{line}.over']=float(over); r[f'totals.{line}.under']=1-float(over)
    for line in (1.5,2.5):
        th=int(line+.5); hc=sum(s[i,j] for i in range(13) for j in range(13) if i-j>=th); ac=sum(s[i,j] for i in range(13) for j in range(13) if j-i>=th)
        r[f'spread.home-{line}']=float(hc); r[f'spread.away-{line}']=float(ac)
    for side,rate in (('home',h),('away',a)):
        for line in (.5,1.5,2.5):
            th=int(line+.5); under=sum(math.exp(-rate)*rate**i/math.factorial(i) for i in range(th)); r[f'team_total.{side}.{line}.under']=under; r[f'team_total.{side}.{line}.over']=1-under
    return r
def norm_odds(odds):
    raw={k:1/v for k,v in odds.items()}; total=sum(raw.values()); return {k:v/total for k,v in raw.items()}
def fit_external(e):
    book=norm_odds(e['sportsbook_1x2']['decimal_odds'])
    def obj(log_rates):
        p=score_probs(*np.exp(log_rates)); return sum((p[f'1x2.{k}']-book[k])**2 for k in book)
    fit=minimize(obj,np.log([1.5,.8]),method='L-BFGS-B',bounds=[(-3,2),(-3,2)])
    rates=tuple(float(x) for x in np.exp(fit.x))
    probs=score_probs(*rates)
    for side in ('home','draw','away'): probs[f'1x2.{side}']=book[side]
    direct_totals={}
    for line, payload in e.get('sportsbook_totals',{}).items():
        fair=norm_odds(payload['decimal_odds'])
        direct_totals[line]=fair
        probs[f'totals.{line}.over']=fair['over']
        probs[f'totals.{line}.under']=fair['under']
    direct_btts=None
    if e.get('sportsbook_btts'):
        direct_btts=norm_odds(e['sportsbook_btts']['decimal_odds'])
        probs['btts.yes']=direct_btts['yes']
        probs['btts.no']=direct_btts['no']
    return rates, probs, {'sportsbook_1x2_devig':book,'sportsbook_totals_devig':direct_totals,'sportsbook_btts_devig':direct_btts,'opta_1x2':{k:e['opta_1x2'][k] for k in ('home','draw','away')},'opta_max_abs_gap_vs_sportsbook':max(abs(e['opta_1x2'][k]-book[k]) for k in book),'fit_objective':float(fit.fun),'direct_total_benchmark':bool(direct_totals),'direct_btts_benchmark':direct_btts is not None}
def model_value(model,key):
    mk=model['markets']; iv=model['uncertainty']['market_probability_intervals']
    if key.startswith('1x2.'):
        b=iv[key]; return mk['1x2'][key.split('.')[1]],b['p10'],b['p90']
    if key.startswith('btts.'):
        b=iv[key]; return mk['btts'][key.split('.')[1]],b['p10'],b['p90']
    if key.startswith('totals.'):
        line,out=key.removeprefix('totals.').rsplit('.',1); b=iv[key]; return mk['totals'][line][out],b['p10'],b['p90']
    if key.startswith('team_total.'):
        side,rest=key.removeprefix('team_total.').split('.',1); line,out=rest.rsplit('.',1); ik=f'team_totals.{side}.{line}.{out}'; b=iv[ik]; return mk['team_totals'][side][line][out],b['p10'],b['p90']
    if key.startswith('spread.'):
        side,line_txt=key.removeprefix('spread.').split('-',1); line=float(line_txt)
        if side=='home':
            model_key=f'home_-{line}'; ik=f'spreads_home_handicap.home_-{line}.win'; b=iv[ik]; return mk['spreads_home_handicap'][model_key]['win'],b['p10'],b['p90']
        model_key=f'home_+{line}'; central=mk['spreads_home_handicap'][model_key]['loss']; wb=iv[f'spreads_home_handicap.home_+{line}.win']; return central,1-wb['p90'],1-wb['p10']
    raise KeyError(key)
def outcome_key(match,market,outcome):
    home,away=match['home'],match['away']; typ=market['market_type']; q=market['question']
    if typ=='match_1x2':
        if 'end in a draw' in q: base='1x2.draw'
        elif home in q: base='1x2.home'
        else: base='1x2.away'
        return base if outcome=='Yes' else 'complement:'+base
    if typ=='totals': return f"totals.{market['line']}.{outcome.lower()}"
    if typ=='both_teams_to_score': return f'btts.{outcome.lower()}'
    if typ=='soccer_team_totals':
        side='home' if f': {home} O/U' in q else 'away'; return f"team_total.{side}.{market['line']}.{outcome.lower()}"
    if typ=='spreads':
        fav=home if q.startswith(f'Spread: {home}') else away; side='home' if fav==home else 'away'; base=f"spread.{side}-{abs(market['line'])}"
        return base if outcome==fav else 'complement:'+base
    raise KeyError(typ)
def resolve(model,external,key):
    comp=key.startswith('complement:'); base=key.removeprefix('complement:')
    c,l,h=model_value(model,base); e=external[base]
    if comp: c,l,h,e=1-c,1-h,1-l,1-e
    return c,l,h,e
def round_down(v,tick): return max(0.0,math.floor((v+1e-12)/tick)*tick)
def ask_vwap(asks,budget):
    rem=budget; notional=shares=0.0
    for lvl in sorted(asks,key=lambda x:float(x['price'])):
        price=float(lvl['price']); fill=min(float(lvl['size']),rem/price); n=fill*price; notional+=n; shares+=fill; rem-=n
        if rem<=1e-9: return notional/shares,shares
    return None

def main():
    md=json.loads(MODEL_PATH.read_text(encoding='utf-8')); evd=json.loads(EVIDENCE_PATH.read_text(encoding='utf-8-sig')); mkt=json.loads(MARKET_PATH.read_text(encoding='utf-8'))
    model={m['id']:m for m in md['matches']}['france_morocco_2026-07-09']; info=evd['matches'][0]
    rates,ext_probs,ext_fit=fit_external(info); required=info['required_edge']; out={'as_of_beijing':mkt['as_of_beijing'],'bankroll_usdc':BANKROLL,'method':{'p_center':'p_external + reliability*(p_independent-p_external)','p_trade':'p_external + reliability*(p10_independent-p_external)-buffer','required_edge':required,'corner_markets':'not_found'},'matches':[]}
    match=mkt['matches'][0]; evals=[]
    for market in match['markets']:
        for outcome in market['outcomes']:
            key=outcome_key({'home':'France','away':'Morocco'},market,outcome)
            try: ind,low,high,ext=resolve(model,ext_probs,key)
            except KeyError: continue
            family='1x2' if key.removeprefix('complement:').startswith('1x2.') else 'derived_score_markets'
            base_key=key.removeprefix('complement:')
            benchmark_quality='direct_or_accepted'
            has_required_benchmark=True
            if base_key.startswith('team_total.') and not info.get('sportsbook_team_totals'):
                benchmark_quality='NO_DIRECT_TEAM_TOTAL_BENCHMARK'
                has_required_benchmark=False
            rel=info['reliability'][family]; buf=info['external_uncertainty_buffer'][family]
            center=ext+rel*(ind-ext); trade=ext+rel*(low-ext)-buf; trade=min(max(trade,.001),center)
            b=market['books'][outcome]; ask=b['best_ask']; bid=b['best_bid']
            if ask is None or bid is None: continue
            fill=ask_vwap(b['asks'],BANKROLL*.0075)
            if fill is None: continue
            vwap,shares=fill; fee_rate=float(market['fee_schedule'].get('rate') or 0); fee=fee_rate*vwap*(1-vwap); cost=vwap+fee; edge=trade-cost; tick=float(b['tick_size']); maker=round_down(trade-required,tick); gap=bid-maker
            status='SKIP'; exec_price=None; kcost=None
            if not has_required_benchmark:
                status='SKIP_NO_DIRECT_TEAM_TOTAL_BENCHMARK'
            elif edge>=required:
                status='TAKER_ACTIONABLE'; exec_price=vwap; kcost=cost
            elif maker>0 and maker<ask and gap<=0.02+1e-12:
                status='POST_ONLY_CONDITIONAL'; exec_price=maker; kcost=maker
            fk=stake=0.0
            if kcost is not None and trade>kcost:
                fk=(trade-kcost)/(1-kcost); stake=BANKROLL*min(.0075,fk*.05*.75)
            evals.append({'market_slug':market['slug'],'question':market['question'],'outcome':outcome,'probability_key':key,'benchmark_quality':benchmark_quality,'p_independent':ind,'p10_independent':low,'p90_independent':high,'p_external_cluster':ext,'reliability':rel,'uncertainty_buffer':buf,'p_center':center,'p_trade':trade,'best_bid':bid,'best_ask':ask,'planned_taker_vwap':vwap,'fee_rate':fee_rate,'fee_per_share_at_vwap':fee,'effective_taker_cost':cost,'taker_robust_edge':edge,'required_edge':required,'maker_max_price':maker,'maker_gap_to_current_bid':gap,'status':status,'execution_price':exec_price,'full_kelly_at_execution_price':fk,'stake_usdc':stake})
    evals.sort(key=lambda r:r['taker_robust_edge'],reverse=True)
    actionable_statuses={'TAKER_ACTIONABLE','POST_ONLY_CONDITIONAL'}
    selected=[r for r in evals if r['status'] in actionable_statuses]
    if len(selected)>1:
        keep=max(selected,key=lambda r:r['taker_robust_edge'])
        for r in selected:
            if r is not keep:
                r['status']='SKIP_CORRELATED_WITH_STRONGER_SAME_MATCH_CANDIDATE'; r['execution_price']=None; r['stake_usdc']=0
        selected=[keep]
    out['matches'].append({'id':'france_morocco_2026-07-09','title':match['title'],'kickoff_utc':match['kickoff_utc'],'external_lambdas':{'home':rates[0],'away':rates[1]},'external_fit':ext_fit,'required_edge':required,'selected':selected,'evaluations':evals})
    out['selected_positions']=[r for m in out['matches'] for r in m['selected']]
    OUTPUT_PATH.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('wrote',OUTPUT_PATH,'selected',len(out['selected_positions']))
    for r in evals[:10]: print(r['status'],r['outcome'],r['question'],f"p_trade={r['p_trade']:.3f}",f"ask={r['best_ask']:.3f}",f"edge={r['taker_robust_edge']:.3f}",f"maker={r['maker_max_price']:.3f}")
if __name__=='__main__': main()
