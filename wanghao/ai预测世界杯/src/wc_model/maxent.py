from __future__ import annotations

import numpy as np


def common_pace_mixture(matrix_factory, lambda_home: float, lambda_away: float,
                        rho: float, max_goals: int) -> np.ndarray:
    """Small empirical over-dispersion mixture with mean pace fixed at one.

    World Cup total goals since 2014 have variance about 11% above their mean.
    A shared pace scale with roughly 20% standard deviation captures score-state
    dependence without changing the average scoring intensity.
    """
    scales = (0.72, 1.0, 1.28)
    weights = (0.255, 0.49, 0.255)
    out = np.zeros((max_goals + 1, max_goals + 1))
    for w, s in zip(weights, scales):
        out += w * matrix_factory(lambda_home*s, lambda_away*s, rho, max_goals)
    return out / out.sum()


def maxent_tilt(base: np.ndarray, target: dict[str, float], max_iter: int = 100) -> np.ndarray:
    """Minimum-KL tilt matching 1X2 and O2.5 exactly where feasible."""
    n = base.shape[0]
    states = [(h, a) for h in range(n) for a in range(n)]
    q = np.array([max(float(base[h, a]), 1e-15) for h, a in states])
    q /= q.sum()
    features = np.array([[float(h > a), float(h == a), float(h+a >= 3)] for h, a in states])
    wanted = np.array([target["home"], target["draw"], target["over2.5"]], dtype=float)
    theta = np.zeros(3)
    for _ in range(max_iter):
        z = np.log(q) + features @ theta; z -= z.max()
        p = np.exp(z); p /= p.sum()
        mean = p @ features
        err = mean - wanted
        if np.max(np.abs(err)) < 1e-11:
            break
        centered = features - mean
        cov = (centered.T * p) @ centered + np.eye(3)*1e-9
        theta -= np.linalg.solve(cov, err)
    out = np.zeros_like(base, dtype=float)
    for value, (h, a) in zip(p, states): out[h, a] = value
    return out / out.sum()
