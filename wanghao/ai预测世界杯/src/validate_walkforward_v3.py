from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np

from wc_model.historical import (RidgePoisson, adam_optimize, estimate_dc_rho,
                                 load_results_with_overrides)
from wc_model.score import core_markets, dc_matrix

ROOT = Path(__file__).resolve().parents[1]


def elo_update(ratings: dict[str, float], r: dict) -> None:
    rh, ra = ratings.get(r["home"], 1500.0), ratings.get(r["away"], 1500.0)
    diff = rh + (0.0 if r["neutral"] else 65.0) - ra
    expected = 1.0 / (1.0 + 10 ** (-diff / 400.0))
    actual = 1.0 if r["hg"] > r["ag"] else 0.5 if r["hg"] == r["ag"] else 0.0
    margin = abs(r["hg"] - r["ag"])
    mult = 1.0 if margin <= 1 else 1.5 if margin == 2 else (11.0 + margin) / 8.0
    k = 40.0 if r["tournament"] == "FIFA World Cup" else 25.0 if "Qualifier" in r["tournament"] else 18.0
    delta = k * mult * (actual - expected)
    ratings[r["home"]], ratings[r["away"]] = rh + delta, ra - delta


def fit_elo_state(rows: list[dict]) -> tuple[dict[str, float], np.ndarray]:
    ratings: dict[str, float] = {}
    features, outcomes = [], []
    for r in sorted(rows, key=lambda x: x["date"]):
        rh, ra = ratings.get(r["home"], 1500.0), ratings.get(r["away"], 1500.0)
        diff = rh + (0.0 if r["neutral"] else 65.0) - ra
        features.append([1.0, diff / 400.0])
        outcomes.append(0 if r["hg"] > r["ag"] else 1 if r["hg"] == r["ag"] else 2)
        elo_update(ratings, r)
    X, y = np.asarray(features), np.asarray(outcomes)

    def objective(flat: np.ndarray):
        b = flat.reshape(3, 2); z = X @ b.T; z -= z.max(axis=1, keepdims=True)
        p = np.exp(z); p /= p.sum(axis=1, keepdims=True)
        loss = -np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1)).sum() + 0.5*np.sum(b[:, 1:]**2)
        grad = (p - np.eye(3)[y]).T @ X; grad[:, 1:] += b[:, 1:]
        return float(loss), grad.ravel()
    fitted, _ = adam_optimize(objective, np.zeros(6), steps=500, lr=0.02)
    return ratings, fitted.reshape(3, 2)


def elo_predict(ratings: dict[str, float], coef: np.ndarray, home: str, away: str, neutral: bool) -> np.ndarray:
    diff = ratings.get(home, 1500.0) + (0.0 if neutral else 65.0) - ratings.get(away, 1500.0)
    z = np.array([1.0, diff / 400.0]) @ coef.T; z -= z.max()
    p = np.exp(z); return p / p.sum()


def metrics(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    brier = np.mean([r["brier"] for r in rows]); logloss = np.mean([r["logloss"] for r in rows])
    rps = np.mean([r["rps"] for r in rows]); acc = np.mean([r["correct"] for r in rows])
    return {"n": len(rows), "brier": float(brier), "logloss": float(logloss),
            "rps": float(rps), "accuracy": float(acc)}


def main() -> None:
    cfg = json.loads((ROOT / "config/model_config_v3.json").read_text(encoding="utf-8"))
    pcfg = cfg["poisson"]
    cutoff = date.fromisoformat(cfg["data"]["cutoff_exclusive"])
    all_rows = load_results_with_overrides(ROOT / cfg["data"]["historical_results"], date(2000, 1, 1), cutoff,
                                           ROOT / cfg["data"]["regulation_overrides"])
    wc = [r for r in all_rows if r["tournament"] == "FIFA World Cup" and r["date"].year >= 2014]
    results = []
    for year in sorted({r["date"].year for r in wc}):
        matches = sorted([r for r in wc if r["date"].year == year], key=lambda r: r["date"])
        train = [r for r in all_rows if r["date"] < matches[0]["date"]]
        p1m = RidgePoisson(pcfg["half_life_days"], pcfg["ridge"], pcfg).fit(train, matches[0]["date"])
        lh_all, la_all = p1m.lambdas_for_rows(train)
        rho = estimate_dc_rho(train, lh_all, la_all, matches[0]["date"], pcfg["half_life_days"])
        ratings, coef = fit_elo_state(train)  # critical: pre-warm from all prior matches
        for r in matches:
            lh, la = p1m.predict(r["home"], r["away"], r["neutral"])
            mk = core_markets(dc_matrix(lh, la, rho, pcfg["max_goals"]))
            p1 = np.array([mk["home"], mk["draw"], mk["away"]])
            p2 = elo_predict(ratings, coef, r["home"], r["away"], r["neutral"])
            p = 0.75*p1 + 0.25*p2; p /= p.sum()
            actual_ix = 0 if r["hg"] > r["ag"] else 1 if r["hg"] == r["ag"] else 2
            y = np.eye(3)[actual_ix]
            cp, cy = np.cumsum(p)[:-1], np.cumsum(y)[:-1]
            results.append({"date": r["date"].isoformat(), "year": year, "home": r["home"], "away": r["away"],
                            "hg": r["hg"], "ag": r["ag"], "p_home": p[0], "p_draw": p[1], "p_away": p[2],
                            "actual": "HDA"[actual_ix], "correct": int(np.argmax(p) == actual_ix),
                            "brier": float(np.sum((p-y)**2)), "logloss": float(-math.log(max(p[actual_ix], 1e-12))),
                            "rps": float(np.mean((cp-cy)**2))})
            elo_update(ratings, r)  # only after prediction
    outdir = ROOT / "outputs/model_v3"; outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "walkforward_predictions_v3.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0])); w.writeheader(); w.writerows(results)
    payload = {"protocol": "Poisson frozen pre-tournament; Elo pre-warmed on all prior matches and updated after prediction",
               "sealed_historical_2014_2022": metrics([r for r in results if r["year"] <= 2022]),
               "retrospective_monitor_2026": metrics([r for r in results if r["year"] == 2026]),
               "by_year": {str(y): metrics([r for r in results if r["year"] == y]) for y in sorted({r["year"] for r in results})},
               "warning": "2026 is retrospective monitoring, not an untouched final test; no historical Polymarket odds are used."}
    (outdir / "walkforward_metrics_v3.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
