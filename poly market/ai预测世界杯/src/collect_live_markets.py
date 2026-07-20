from __future__ import annotations

import csv,json,time,urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SLUGS={
 "fifwc-nor-eng-2026-07-11":["fifwc-nor-eng-2026-07-11","fifwc-nor-eng-2026-07-11-more-markets","fifwc-nor-eng-2026-07-11-exact-score","fifwc-nor-eng-2026-07-11-first-to-score"],
 "fifwc-arg-che-2026-07-11":["fifwc-arg-che-2026-07-11","fifwc-arg-che-2026-07-11-more-markets","fifwc-arg-che-2026-07-11-exact-score","fifwc-arg-che-2026-07-11-first-to-score"]}

def get_json(url,retries=3):
    for k in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"wc-model-research/2.0"})
            with urllib.request.urlopen(req,timeout=25) as r:return json.loads(r.read().decode())
        except Exception:
            if k+1==retries:raise
            time.sleep(.5*(k+1))

def market_key(m,home,away):
    t=m.get("sportsMarketType",""); q=m["question"]; title=m.get("groupItemTitle","")
    if t=="moneyline":
        if title==home:return "main_90m",f"{home} win"
        if title==away:return "main_90m",f"{away} win"
        return "main_90m","Draw"
    if t=="spreads":return "spread",q.replace("Spread: ","")
    line=q.split("O/U ")[-1]
    if t=="totals":return "totals",f"Total over {line}"
    if t=="soccer_team_totals":
        team=home if f": {home} O/U" in q else away;return "team_total",f"{team} over {line}"
    if t=="first_half_totals":return "half_total",f"First half over {line}"
    if t=="second_half_totals":return "half_total",f"Second half over {line}"
    if t=="soccer_first_half_team_totals":
        team=home if f": {home} 1st" in q else away;return "half_team",f"{team} first half over {line}"
    if t=="soccer_second_half_team_totals":
        team=home if f": {home} 2nd" in q else away;return "half_team",f"{team} second half over {line}"
    if t=="both_teams_to_score":return "btts","Both teams to score"
    if t=="both_teams_to_score_first_half":return "btts","Both teams to score first half"
    if t=="both_teams_to_score_second_half":return "btts","Both teams to score second half"
    if t=="soccer_team_to_advance":return "advance",f"{home} to advance"
    if t=="soccer_extra_time":return "extra_time","Match goes to extra time"
    if t=="soccer_penalty_shootout":return "extra_time","Match goes to penalties"
    if t=="soccer_exact_score":return "exact_score",title.replace(" - ","-")
    if t=="soccer_first_to_score":
        if "Neither team" in q:return "first_score","Neither team to score first"
        if q.startswith(home):return "first_score",f"{home} to score first"
        if q.startswith(away):return "first_score",f"{away} to score first"
        raise ValueError((t,q))
    raise ValueError((t,q))

def book_stats(book):
    asks=sorted((float(x["price"]),float(x["size"])) for x in book.get("asks",[]))
    bids=sorted(((float(x["price"]),float(x["size"])) for x in book.get("bids",[])),reverse=True)
    ask=asks[0][0] if asks else None;bid=bids[0][0] if bids else None
    depth1=sum(p*s for p,s in asks if ask is not None and p<=ask+.01+1e-9)
    depth2=sum(p*s for p,s in asks if ask is not None and p<=ask+.02+1e-9)
    ask_best=sum(p*s for p,s in asks if ask is not None and abs(p-ask)<1e-9)
    bid_depth1=sum(p*s for p,s in bids if bid is not None and p>=bid-.01-1e-9)
    bid_depth2=sum(p*s for p,s in bids if bid is not None and p>=bid-.02-1e-9)
    bid_best=sum(p*s for p,s in bids if bid is not None and abs(p-bid)<1e-9)
    return {"ask":ask,"bid":bid,"spread":None if ask is None or bid is None else ask-bid,
            "ask_depth_1c":depth1,"ask_depth_2c":depth2,
            "ask_depth_at_best":ask_best,
            "bid_depth_1c":bid_depth1,"bid_depth_2c":bid_depth2,
            "bid_depth_at_best":bid_best}

def main():
    events={}; rows=[]; tokens=[]
    for fid,slugs in SLUGS.items():
        evs=[]
        for slug in slugs:
            data=get_json(f"https://gamma-api.polymarket.com/events?slug={slug}")
            if not data:raise RuntimeError(f"event not found: {slug}")
            evs.append(data[0])
        events[fid]=evs
        home,away=evs[0]["teams"][0]["name"],evs[0]["teams"][1]["name"]
        for ev in evs:
            for m in ev["markets"]:
                ids=json.loads(m["clobTokenIds"]);outcomes=json.loads(m["outcomes"])
                if len(ids)!=2:continue
                tokens.extend(ids);group,contract=market_key(m,home,away)
                rows.append({"fixture_id":fid,"home":home,"away":away,"event_slug":ev["slug"],"event_title":ev["title"],
                  "event_liquidity":ev.get("liquidity",0),"event_volume":ev.get("volume",0),"market_id":m["id"],"question":m["question"],
                  "sports_market_type":m.get("sportsMarketType",""),"group":group,"contract":contract,"outcome_yes":outcomes[0],"outcome_no":outcomes[1],
                  "token_yes":ids[0],"token_no":ids[1],"market_liquidity":m.get("liquidityNum",m.get("liquidity",0)),"market_volume":m.get("volumeNum",m.get("volume",0)),
                  "gamma_best_bid":m.get("bestBid"),"gamma_best_ask":m.get("bestAsk"),"fee_rate":m.get("feeSchedule",{}).get("rate",0.05),"tick_size":m.get("orderPriceMinTickSize",.01)})
    books={}
    with ThreadPoolExecutor(max_workers=12) as ex:
        fut={ex.submit(get_json,f"https://clob.polymarket.com/book?token_id={t}"):t for t in set(tokens)}
        for f in as_completed(fut):books[fut[f]]=f.result()
    for r in rows:
        for side in ("yes","no"):
            s=book_stats(books[r[f"token_{side}"]]);
            for k,v in s.items():r[f"{side}_{k}"]=v
    stamp=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ"); outdir=ROOT/"data/raw/polymarket";outdir.mkdir(parents=True,exist_ok=True)
    raw={"captured_at_utc":datetime.now(timezone.utc).isoformat(),"events":events,"books":books}
    (outdir/f"two_matches_live_{stamp}.json").write_text(json.dumps(raw,ensure_ascii=False),encoding="utf-8")
    csvpath=outdir/f"two_matches_normalized_{stamp}.csv"
    with csvpath.open("w",encoding="utf-8-sig",newline="") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (outdir/"LATEST.txt").write_text(str(csvpath.relative_to(ROOT)).replace('\\','/'),encoding="utf-8")
    print(json.dumps({"captured_at_utc":raw["captured_at_utc"],"markets":len(rows),"csv":str(csvpath)},ensure_ascii=False))

if __name__=="__main__":main()
