from __future__ import annotations

import math
import numpy as np


def poisson_over(line: float, lam: float) -> float:
    threshold=int(math.floor(line))+1
    return 1-sum(math.exp(-lam)*lam**k/math.factorial(k) for k in range(threshold))


def contract_probability(group: str, contract: str, m: np.ndarray, home: str, away: str, assumptions: dict) -> float:
    n=m.shape[0]; lh=sum(i*m[i,j] for i in range(n) for j in range(n)); la=sum(j*m[i,j] for i in range(n) for j in range(n))
    ph=sum(m[i,j] for i in range(n) for j in range(n) if i>j); pd=float(np.trace(m)); pa=1-ph-pd
    if group=="main_90m": return ph if contract.startswith(home) else pa if contract.startswith(away) else pd
    if group=="advance": return ph+(1-float(assumptions["away_share_if_90m_draw"]))*pd
    if group=="totals":
        threshold=int(math.floor(float(contract.split()[-1])))+1
        return float(sum(m[i,j] for i in range(n) for j in range(n) if i+j>=threshold))
    if group=="team_total":
        threshold=int(math.floor(float(contract.split()[-1])))+1
        return float(sum(m[i,j] for i in range(n) for j in range(n) if (i>=threshold if contract.startswith(home) else j>=threshold)))
    if group in ("half_total","half_team","btts"):
        share=float(assumptions["first_half_goal_share"])
        if "Second" in contract or "second" in contract: share=1-share
        elif "First" not in contract and "first" not in contract and group=="btts": return float(m[1:,1:].sum())
        x=lh*share; y=la*share
        if group=="half_total": return poisson_over(float(contract.split()[-1]),x+y)
        if group=="half_team": return poisson_over(float(contract.split()[-1]),x if contract.startswith(home) else y)
        return (1-math.exp(-x))*(1-math.exp(-y))
    if group=="spread":
        team,handicap=contract.split(); margin=int(abs(float(handicap.strip("()"))))+1
        return float(sum(m[i,j] for i in range(n) for j in range(n) if (i-j>=margin if team==home else j-i>=margin)))
    if group=="extra_time": return pd if "extra time" in contract else pd*float(assumptions["penalties_given_90m_draw"])
    if group=="first_score":
        scoreless=float(m[0,0])
        if contract=="Neither team to score first": return scoreless
        if contract.startswith(home): return (1-scoreless)*lh/max(1e-12,lh+la)
        return (1-scoreless)*la/max(1e-12,lh+la)
    if group=="exact_score":
        if contract.lower()=="any other score": return 1-float(m[:4,:4].sum())
        score=contract.replace(f"{home} ","").replace(f" {away}",""); h,a=map(int,score.split("-")); return float(m[h,a])
    raise ValueError((group,contract))


def confidence_class(group: str, contract: str = "") -> str:
    contract_lower = contract.lower()
    if group == "btts" and ("first half" in contract_lower or "second half" in contract_lower):
        return "low"
    if group in {"half_total","half_team","extra_time","advance","first_score"}: return "low"
    if group=="exact_score": return "medium"
    return "standard"
