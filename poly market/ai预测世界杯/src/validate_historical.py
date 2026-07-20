from __future__ import annotations
import json,sys
from datetime import date
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"src"))
from wc_model.historical import RidgePoisson,load_results
from wc_model.score import core_markets,dc_matrix

cfg=json.loads((ROOT/"config/model_config.json").read_text(encoding="utf-8")); dcfg=cfg["data"]; pcfg=cfg["poisson"]
start=date.fromisoformat(dcfg["training_start"]); split=date.fromisoformat(dcfg["validation_start"]); cutoff=date.fromisoformat(dcfg["cutoff_exclusive"])
train=load_results(ROOT/dcfg["historical_results"],start,split); valid=load_results(ROOT/dcfg["historical_results"],split,cutoff)
model=RidgePoisson(pcfg["half_life_days"],pcfg["ridge"],pcfg).fit(train,split); probs=[]; y=[]; skipped=0
for r in valid:
    try: lh,la=model.predict(r["home"],r["away"],r["neutral"])
    except KeyError: skipped+=1;continue
    m=core_markets(dc_matrix(lh,la,0.0,pcfg["max_goals"])); probs.append([m["home"],m["draw"],m["away"]]);y.append(0 if r["hg"]>r["ag"] else 1 if r["hg"]==r["ag"] else 2)
p=np.asarray(probs); y=np.asarray(y); one=np.eye(3)[y]
metrics={"protocol":"fixed temporal holdout; not rolling walk-forward and not an untouched final test","train_end_exclusive":split.isoformat(),
         "validation_end_exclusive":cutoff.isoformat(),"n":len(y),"skipped_unseen":skipped,
         "log_loss":float(-np.log(np.clip(p[np.arange(len(y)),y],1e-12,1)).mean()),"multiclass_brier":float(np.mean(np.sum((p-one)**2,axis=1))),
         "rps":float(np.mean(np.sum((np.cumsum(p,axis=1)[:,:-1]-np.cumsum(one,axis=1)[:,:-1])**2,axis=1)/2))}
(ROOT/"outputs/model_v2/validation_metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8");print(json.dumps(metrics,indent=2))
