from __future__ import annotations

import math
import numpy as np


def dc_tau(h: int, a: int, lh: float, la: float, rho: float) -> float:
    if h == 0 and a == 0: return 1-lh*la*rho
    if h == 1 and a == 0: return 1+lh*rho
    if h == 0 and a == 1: return 1+la*rho
    if h == 1 and a == 1: return 1-rho
    return 1.0


def dc_matrix(lh: float, la: float, rho: float, max_goals: int = 10) -> np.ndarray:
    m = np.zeros((max_goals+1,max_goals+1))
    for h in range(max_goals+1):
        ph=math.exp(-lh)*lh**h/math.factorial(h)
        for a in range(max_goals+1):
            pa=math.exp(-la)*la**a/math.factorial(a)
            m[h,a]=max(0.0,dc_tau(h,a,lh,la,rho))*ph*pa
    return m/m.sum()


def core_markets(m: np.ndarray) -> dict:
    h=sum(m[i,j] for i in range(m.shape[0]) for j in range(m.shape[1]) if i>j)
    d=float(np.trace(m)); a=1-h-d
    over25=sum(m[i,j] for i in range(m.shape[0]) for j in range(m.shape[1]) if i+j>=3)
    btts=sum(m[i,j] for i in range(1,m.shape[0]) for j in range(1,m.shape[1]))
    return {"home":float(h),"draw":d,"away":float(a),"over2.5":float(over25),"btts":float(btts)}


def de_vig(decimal: dict) -> dict:
    raw={k:1/float(v) for k,v in decimal.items()}; s=sum(raw.values())
    return {k:v/s for k,v in raw.items()}
