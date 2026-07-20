from __future__ import annotations

import numpy as np

from .score import core_markets, dc_matrix, de_vig


def sharp_consensus(benchmarks: list[dict]) -> tuple[dict, dict]:
    """Equal-source consensus after removing each book's overround first."""
    if not benchmarks:
        raise ValueError("at least one sharp benchmark is required")
    one = [de_vig(x["decimal_1x2"]) for x in benchmarks]
    totals = [de_vig(x["decimal_total_2_5"]) for x in benchmarks]
    p1 = {k: float(np.mean([p[k] for p in one])) for k in ("home", "draw", "away")}
    pt = {k: float(np.mean([p[k] for p in totals])) for k in ("over", "under")}
    return p1, pt


def coherent_fusion(p1_lambdas: tuple[float,float], rho: float, p1: dict, elo: dict,
                    sharp: dict, cfg: dict, max_goals: int) -> dict:
    ew=float(cfg["elo_weight_inside_independent"]); rel=float(cfg["independent_reliability_vs_sharp"])
    independent={k:(1-ew)*p1[k]+ew*elo[k] for k in ("home","draw","away")}
    independent["over2.5"]=p1["over2.5"]
    sharp1=de_vig(sharp["decimal_1x2"]); sharpt=de_vig(sharp["decimal_total_2_5"])
    target={k:sharp1[k]+rel*(independent[k]-sharp1[k]) for k in ("home","draw","away")}
    target["over2.5"]=sharpt["over"]+rel*(independent["over2.5"]-sharpt["over"])
    def loss(x):
        mk=core_markets(dc_matrix(float(x[0]),float(x[1]),rho,max_goals))
        return sum((mk[k]-target[k])**2 for k in ("home","draw","away"))+2*(mk["over2.5"]-target["over2.5"])**2
    best=(float("inf"),p1_lambdas)
    for span,steps in ((1.0,35),(.12,25)):
        center=best[1]
        for lh0 in np.linspace(max(.2,center[0]-span),min(3.5,center[0]+span),steps):
            for la0 in np.linspace(max(.2,center[1]-span),min(3.5,center[1]+span),steps):
                value=loss((lh0,la0))
                if value<best[0]:best=(value,(float(lh0),float(la0)))
    lh,la=best[1]; matrix=dc_matrix(lh,la,rho,max_goals)
    return {"lambda_home":lh,"lambda_away":la,"rho":rho,"matrix":matrix,"markets":core_markets(matrix),
            "p1":p1,"elo":elo,"independent_1x2":independent,"sharp_1x2":sharp1,
            "sharp_total_2_5":sharpt,"fusion_target":target,"fit_loss":float(best[0])}


def coherent_fusion_consensus(p1_lambdas: tuple[float, float], rho: float, p1: dict,
                              elo: dict, benchmarks: list[dict], cfg: dict,
                              max_goals: int) -> dict:
    """Coherent score-matrix fusion using multiple independent sportsbook quotes.

    A fixed historical DC rho can force a material mismatch between the quoted
    draw and total.  Fit rho together with both scoring intensities so the three
    independent market constraints (two 1X2 degrees + total) can be represented
    by one internally consistent score matrix.
    """
    sharp1, sharpt = sharp_consensus(benchmarks)
    ew = float(cfg["elo_weight_inside_independent"])
    rel = float(cfg["independent_reliability_vs_sharp"])
    independent = {k: (1-ew)*p1[k] + ew*elo[k] for k in ("home", "draw", "away")}
    independent["over2.5"] = p1["over2.5"]
    target = {k: sharp1[k] + rel*(independent[k]-sharp1[k]) for k in ("home", "draw", "away")}
    target["over2.5"] = sharpt["over"] + rel*(independent["over2.5"]-sharpt["over"])

    def loss(x: tuple[float, float, float]) -> float:
        mk = core_markets(dc_matrix(x[0], x[1], x[2], max_goals))
        return sum((mk[k]-target[k])**2 for k in ("home", "draw", "away", "over2.5"))

    best = (float("inf"), (p1_lambdas[0], p1_lambdas[1], rho))
    for lspan, rspan, steps in ((1.0, 0.20, 23), (0.15, 0.04, 17)):
        center = best[1]
        lhs = np.linspace(max(0.2, center[0]-lspan), min(3.5, center[0]+lspan), steps)
        las = np.linspace(max(0.2, center[1]-lspan), min(3.5, center[1]+lspan), steps)
        rhos = np.linspace(max(-0.20, center[2]-rspan), min(0.20, center[2]+rspan), steps)
        for lh in lhs:
            for la in las:
                for rr in rhos:
                    value = loss((float(lh), float(la), float(rr)))
                    if value < best[0]:
                        best = (value, (float(lh), float(la), float(rr)))
    lh, la, fitted_rho = best[1]
    matrix = dc_matrix(lh, la, fitted_rho, max_goals)
    return {"lambda_home": lh, "lambda_away": la, "rho": fitted_rho, "matrix": matrix,
            "markets": core_markets(matrix), "p1": p1, "elo": elo,
            "independent_1x2": independent, "sharp_1x2": sharp1,
            "sharp_total_2_5": sharpt, "fusion_target": target,
            "fit_loss": float(best[0]), "sharp_sources": len(benchmarks),
            "historical_rho": rho}


def scenario_matrices(lh: float,la: float,rho: float,cfg: dict,max_goals: int) -> list[np.ndarray]:
    pct=float(cfg["uncertainty_lambda_pct"]); shift=float(cfg["uncertainty_share_shift"])
    total=lh+la; share=lh/total; out=[]
    for scale in np.linspace(1-pct,1+pct,5):
        for ds in np.linspace(-shift,shift,5):
            s=min(0.85,max(0.15,share+ds))
            for dr in (-0.03,0,0.03): out.append(dc_matrix(total*scale*s,total*scale*(1-s),rho+dr,max_goals))
    return out
