from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np


def adam_optimize(objective, x0: np.ndarray, steps: int = 900, lr: float = 0.03) -> tuple[np.ndarray, float]:
    """Small deterministic optimizer to keep the project SciPy-independent."""
    x=x0.copy(); m=np.zeros_like(x); v=np.zeros_like(x); best_x=x.copy(); best=float("inf")
    for t in range(1,steps+1):
        loss,g=objective(x)
        if loss<best: best,best_x=float(loss),x.copy()
        m=.9*m+.1*g; v=.999*v+.001*(g*g)
        mh=m/(1-.9**t); vh=v/(1-.999**t)
        x-=lr*mh/(np.sqrt(vh)+1e-8)
        if t%250==0: lr*=.6
    return best_x,best


def tournament_weight(name: str, cfg: dict) -> float:
    low = name.lower()
    if "fifa world cup" == low:
        return float(cfg["world_cup_weight"])
    if any(x in low for x in ("uefa euro", "copa am", "african cup", "asian cup", "gold cup")):
        return float(cfg["major_tournament_weight"])
    if "friendly" in low:
        return float(cfg["friendly_weight"])
    return 1.0


def load_results(path: Path, start: date, cutoff: date) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            d = date.fromisoformat(raw["date"])
            if d < start or d >= cutoff or raw["home_score"] in ("", "NA") or raw["away_score"] in ("", "NA"):
                continue
            rows.append({
                "date": d, "home": raw["home_team"], "away": raw["away_team"],
                "hg": int(raw["home_score"]), "ag": int(raw["away_score"]),
                "tournament": raw["tournament"], "neutral": raw["neutral"].upper() == "TRUE"
            })
    if not rows or max(r["date"] for r in rows) >= cutoff:
        raise AssertionError("historical cutoff enforcement failed")
    return rows


def load_results_with_overrides(path: Path, start: date, cutoff: date,
                                overrides_path: Path | None = None) -> list[dict]:
    """Load immutable raw results and apply an auditable regulation-score overlay.

    Public result feeds often store an extra-time final score (or leave a newly
    completed match as NA), while 1X2 Polymarket contracts settle on 90 minutes.
    The overlay is therefore kept separate from the raw download.
    """
    rows = load_results(path, start, cutoff)
    if overrides_path is None or not overrides_path.exists():
        return rows
    keyed = {(r["date"], r["home"], r["away"]): r for r in rows}
    with overrides_path.open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            d = date.fromisoformat(raw["date"])
            if d < start or d >= cutoff:
                continue
            key = (d, raw["home_team"], raw["away_team"])
            keyed[key] = {
                "date": d, "home": raw["home_team"], "away": raw["away_team"],
                "hg": int(raw["regulation_home_score"]),
                "ag": int(raw["regulation_away_score"]),
                "tournament": raw["tournament"],
                "neutral": raw["neutral"].upper() == "TRUE",
            }
    out = sorted(keyed.values(), key=lambda r: r["date"])
    if not out or max(r["date"] for r in out) >= cutoff:
        raise AssertionError("historical override cutoff enforcement failed")
    return out


@dataclass
class RidgePoisson:
    half_life_days: float
    ridge: float
    cfg: dict
    teams: list[str] | None = None
    params: np.ndarray | None = None
    fit_info: dict | None = None

    def fit(self, rows: list[dict], reference: date) -> "RidgePoisson":
        self.teams = sorted({r["home"] for r in rows} | {r["away"] for r in rows})
        ix = {t: i for i, t in enumerate(self.teams)}
        h = np.array([ix[r["home"]] for r in rows]); a = np.array([ix[r["away"]] for r in rows])
        hg = np.array([r["hg"] for r in rows], dtype=float); ag = np.array([r["ag"] for r in rows], dtype=float)
        venue = np.array([not r["neutral"] for r in rows], dtype=float)
        age = np.array([(reference - r["date"]).days for r in rows], dtype=float)
        w = np.exp(-math.log(2) * np.maximum(age, 0) / self.half_life_days)
        w *= np.array([tournament_weight(r["tournament"], self.cfg) for r in rows])
        n = len(self.teams)

        def objective(x: np.ndarray):
            mu, home_adv = x[0], x[1]; attack = x[2:2+n]; defence = x[2+n:]
            log_h = np.clip(mu + home_adv * venue + attack[h] - defence[a], -4, 3)
            log_a = np.clip(mu + attack[a] - defence[h], -4, 3)
            lh, la = np.exp(log_h), np.exp(log_a)
            loss = float(np.sum(w * (lh - hg * log_h + la - ag * log_a)))
            loss += 0.5 * self.ridge * float(attack @ attack + defence @ defence)
            rh, ra = w * (lh - hg), w * (la - ag)
            g = np.zeros_like(x); g[0] = np.sum(rh + ra); g[1] = np.sum(rh * venue)
            np.add.at(g[2:2+n], h, rh); np.add.at(g[2:2+n], a, ra)
            np.add.at(g[2+n:], a, -rh); np.add.at(g[2+n:], h, -ra)
            g[2:2+n] += self.ridge * attack; g[2+n:] += self.ridge * defence
            return loss, g

        x0 = np.zeros(2 + 2*n); x0[0] = math.log(1.25); x0[1] = math.log(1.12)
        fitted,best = adam_optimize(objective,x0)
        self.params = fitted
        self.fit_info = {"matches": len(rows), "teams": n, "objective": best,
                         "optimizer":"deterministic_adam", "home_advantage_multiplier": float(math.exp(fitted[1]))}
        return self

    def predict(self, home: str, away: str, neutral: bool) -> tuple[float, float]:
        if self.params is None or self.teams is None:
            raise RuntimeError("model not fitted")
        ix = {t: i for i, t in enumerate(self.teams)}
        if home not in ix or away not in ix:
            raise KeyError(f"unseen team: {home if home not in ix else away}")
        n = len(self.teams); mu, ha = self.params[0], self.params[1]
        att, deff = self.params[2:2+n], self.params[2+n:]
        return (math.exp(mu + ha * (not neutral) + att[ix[home]] - deff[ix[away]]),
                math.exp(mu + att[ix[away]] - deff[ix[home]]))

    def lambdas_for_rows(self, rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
        values = [self.predict(r["home"], r["away"], r["neutral"]) for r in rows]
        return np.array([x[0] for x in values]), np.array([x[1] for x in values])


def estimate_dc_rho(rows: list[dict], lh: np.ndarray, la: np.ndarray, reference: date, half_life: float) -> float:
    age = np.array([(reference-r["date"]).days for r in rows], dtype=float)
    w = np.exp(-math.log(2) * np.maximum(age, 0) / half_life)
    best = (float("inf"), 0.0)
    for rho in np.linspace(-0.15, 0.10, 101):
        loss = 0.0; valid = True
        for k, r in enumerate(rows):
            h, a = r["hg"], r["ag"]
            tau = 1.0
            if h == 0 and a == 0: tau = 1 - lh[k] * la[k] * rho
            elif h == 1 and a == 0: tau = 1 + lh[k] * rho
            elif h == 0 and a == 1: tau = 1 + la[k] * rho
            elif h == 1 and a == 1: tau = 1 - rho
            if tau <= 0: valid = False; break
            loss -= w[k] * math.log(tau)
        if valid and loss < best[0]: best = (loss, float(rho))
    return best[1]


def elo_probabilities(rows: list[dict], home: str, away: str, neutral: bool) -> tuple[dict, dict]:
    ratings: dict[str, float] = {}
    features, outcomes = [], []
    for r in rows:
        rh, ra = ratings.get(r["home"], 1500.0), ratings.get(r["away"], 1500.0)
        home_bonus = 65.0 if not r["neutral"] else 0.0
        diff = rh + home_bonus - ra
        if r["date"] >= date(2014, 1, 1):
            features.append([1.0, diff/400.0]); outcomes.append(0 if r["hg"] > r["ag"] else 1 if r["hg"] == r["ag"] else 2)
        exp_h = 1/(1+10**(-diff/400)); actual = 1.0 if r["hg"] > r["ag"] else 0.5 if r["hg"] == r["ag"] else 0.0
        margin = abs(r["hg"]-r["ag"]); mult = 1.0 if margin <= 1 else 1.5 if margin == 2 else (11+margin)/8
        k = 40.0 if r["tournament"] == "FIFA World Cup" else 25.0 if "Qualifier" in r["tournament"] else 18.0
        delta = k * mult * (actual-exp_h); ratings[r["home"]] = rh+delta; ratings[r["away"]] = ra-delta
    X, y = np.asarray(features), np.asarray(outcomes); ridge = 1.0
    def obj(flat):
        b = flat.reshape(3, 2); z = X @ b.T; z -= z.max(axis=1, keepdims=True)
        p = np.exp(z); p /= p.sum(axis=1, keepdims=True)
        loss = -np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1)).sum() + 0.5*ridge*np.sum(b[:,1:]**2)
        one = np.eye(3)[y]; grad = (p-one).T @ X; grad[:,1:] += ridge*b[:,1:]
        return float(loss), grad.ravel()
    fitted,_ = adam_optimize(obj,np.zeros(6),steps=1200,lr=.02)
    diff = ratings.get(home,1500)+(0 if neutral else 65)-ratings.get(away,1500)
    z = np.array([1.0,diff/400]) @ fitted.reshape(3,2).T; z -= z.max(); p=np.exp(z); p/=p.sum()
    return {"home":float(p[0]),"draw":float(p[1]),"away":float(p[2])}, {"home_elo":ratings.get(home,1500),"away_elo":ratings.get(away,1500)}
