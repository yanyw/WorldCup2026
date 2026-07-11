#!/usr/bin/env python3
from __future__ import annotations
import json, time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'polymarket_snapshot_0709.json'
G='https://gamma-api.polymarket.com/events'
C='https://clob.polymarket.com/book'
SLUG='fifwc-fra-mar-2026-07-09'
SUPPORTED={'spreads','totals','both_teams_to_score','soccer_team_totals'}
def get(url):
    last=None
    for i in range(5):
        try:
            with urlopen(Request(url,headers={'User-Agent':'wc2026-0709/1.0','Accept':'application/json'}),timeout=30) as r:
                return json.load(r)
        except Exception as e:
            last=e; time.sleep(.5*2**i)
    raise RuntimeError(url) from last
def event(slug):
    d=get(G+'?'+urlencode({'slug':slug}))
    if not isinstance(d,list) or len(d)!=1: raise RuntimeError(f'{slug} -> {len(d) if isinstance(d,list) else type(d)}')
    return d[0]
def book(token):
    raw=get(C+'?'+urlencode({'token_id':token}))
    bids=sorted(([{'price':float(x['price']),'size':float(x['size'])} for x in raw.get('bids',[])]), key=lambda x:x['price'], reverse=True)
    asks=sorted(([{'price':float(x['price']),'size':float(x['size'])} for x in raw.get('asks',[])]), key=lambda x:x['price'])
    return {'best_bid':bids[0]['price'] if bids else None,'best_ask':asks[0]['price'] if asks else None,'bids':bids[:10],'asks':asks[:10],'tick_size':float(raw.get('tick_size') or 0.01),'timestamp':raw.get('timestamp')}
def rec(m,typ):
    outcomes=json.loads(m['outcomes']); tokens=json.loads(m['clobTokenIds']); prices=[float(x) for x in json.loads(m['outcomePrices'])]
    return {'id':m['id'],'slug':m['slug'],'question':m['question'],'market_type':typ,'line':float(m['line']) if m.get('line') is not None else None,'outcomes':outcomes,'token_ids':tokens,'outcome_prices':prices,'fee_schedule':m.get('feeSchedule') or {},'liquidity':float(m.get('liquidityNum') or m.get('liquidity') or 0),'volume':float(m.get('volumeNum') or m.get('volume') or 0),'updated_at':m.get('updatedAt'),'books':{o:book(t) for o,t in zip(outcomes,tokens)}}
def core(m):
    typ=m.get('sportsMarketType')
    line=abs(float(m.get('line') or 0))
    if typ=='spreads': return line<=2.5
    if typ=='totals': return 1.5<=line<=4.5
    return typ in SUPPORTED
main=event(SLUG); more=event(SLUG+'-more-markets')
markets=[]
for m in main['markets']: markets.append(rec(m,'match_1x2'))
for m in more['markets']:
    typ=m.get('sportsMarketType')
    if typ in SUPPORTED and core(m): markets.append(rec(m,typ))
snap={'as_of_beijing':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'),'gamma_api':G,'clob_api':C,'corner_market_search':'searched France Morocco corners / corner kicks; no open corner event found through Gamma query','matches':[{'event_slug':SLUG,'title':main['title'],'kickoff_utc':main['endDate'],'event_url':f'https://polymarket.com/sports/world-cup/{SLUG}','markets':markets}]}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(snap,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('wrote',OUT,snap['as_of_beijing'],len(markets))
for m in markets:
    print(m['question'], m['outcomes'], {o:(b['best_bid'],b['best_ask']) for o,b in m['books'].items()})
