#!/usr/bin/env python3
"""Build independent P1/P2/P3 forecasts for the 2026-07-05 quarter-finals.

The script deliberately excludes market prices, betting odds, and Opta inputs.
All completed-result rows must be dated strictly before CUTOFF.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import gammaln, logsumexp
from scipy.stats import poisson


SEED = 20260705
CUTOFF = date(2026, 7, 5)
RECENT_START = date(2016, 1, 1)
ELO_START = date(2000, 1, 1)
VALIDATION_START = date(2024, 1, 1)
RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
RESULTS_REPO_URL = "https://github.com/martj42/international_results"
FIFA_TRAINING_URL = "https://www.fifatrainingcentre.com/en/fwc2026/post-match-summary-reports/"
MAX_GOALS = 12

SCRIPT_DIR = Path(__file__).resolve().parent
RUN_DIR = SCRIPT_DIR.parent
DATA_DIR = RUN_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
RESULTS_CACHE = RAW_DIR / "results.csv"
P3_PATH = RUN_DIR.parent / "20260703" / "data" / "fifa_match_stats_0702.json"
OUTPUT_PATH = DATA_DIR / "model_results_0705.json"
BACKTEST_PATH = DATA_DIR / "model_backtest_0705.json"

TARGETS = [
    {
        "id": "brazil_norway_2026-07-05",
        "home": "Brazil",
        "away": "Norway",
        "neutral": True,
        "venue": "MetLife Stadium, East Rutherford, New Jersey, United States",
        "venue_context": "neutral venue",
        "uncertainty_widening": 0.0,
    },
    {
        "id": "mexico_england_2026-07-05",
        "home": "Mexico",
        "away": "England",
        "neutral": False,
        "venue": "Estadio Azteca, Mexico City, Mexico",
        "venue_context": "Mexico true home venue; approximately 2240m altitude",
        "uncertainty_widening": 0.04,
    },
]


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def download_or_read_cache() -> tuple[bytes, str]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if RESULTS_CACHE.exists() and RESULTS_CACHE.stat().st_size > 100_000:
        return RESULTS_CACHE.read_bytes(), "cache"
    request = urllib.request.Request(RESULTS_URL, headers={"User-Agent": "WorldCup2026-independent-model/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    if len(payload) < 100_000:
        raise RuntimeError("Downloaded results.csv is unexpectedly small")
    RESULTS_CACHE.write_bytes(payload)
    return payload, "download"


def load_results(payload: bytes) -> tuple[list[dict], dict]:
    rows = []
    rejected = defaultdict(int)
    for raw in csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))):
        try:
            match_date = date.fromisoformat(raw["date"])
        except (ValueError, TypeError):
            rejected["invalid_date"] += 1
            continue
        if match_date >= CUTOFF:
            rejected["at_or_after_cutoff"] += 1
            continue
        try:
            home_goals = int(raw["home_score"])
            away_goals = int(raw["away_score"])
        except (ValueError, TypeError):
            rejected["missing_or_invalid_score"] += 1
            continue
        if home_goals < 0 or away_goals < 0:
            rejected["negative_score"] += 1
            continue
        rows.append(
            {
                "date": match_date,
                "home": raw["home_team"].strip(),
                "away": raw["away_team"].strip(),
                "home_goals": home_goals,
                "away_goals": away_goals,
                "tournament": raw["tournament"].strip(),
                "neutral": raw["neutral"].strip().upper() == "TRUE",
            }
        )
    rows.sort(key=lambda row: row["date"])
    if not rows or rows[-1]["date"] >= CUTOFF:
        raise AssertionError("Cutoff enforcement failed")
    return rows, dict(rejected)


def importance(tournament: str) -> float:
    name = tournament.lower()
    if "fifa world cup" in name and "qualification" not in name:
        return 1.25
    if "qualification" in name or "qualifier" in name:
        return 1.10
    if any(token in name for token in ("copa america", "uefa euro", "african cup", "asian cup", "gold cup")):
        return 1.15
    if "friendly" in name:
        return 0.75
    return 1.0


def score_matrix(home_lambda: float, away_lambda: float, max_goals: int = MAX_GOALS) -> tuple[np.ndarray, float]:
    grid = np.arange(max_goals + 1)
    home_p = poisson.pmf(grid, home_lambda)
    away_p = poisson.pmf(grid, away_lambda)
    matrix = np.outer(home_p, away_p)
    retained = float(matrix.sum())
    matrix /= retained
    return matrix, 1.0 - retained


def outcome_probs(home_lambda: float, away_lambda: float) -> np.ndarray:
    matrix, _ = score_matrix(home_lambda, away_lambda)
    return np.array([np.tril(matrix, -1).sum(), np.trace(matrix), np.triu(matrix, 1).sum()])


class RidgePoisson:
    """Time-decayed independent Poisson attack/defence model with ridge shrinkage."""

    def __init__(self, half_life_days: float, ridge: float):
        self.half_life_days = float(half_life_days)
        self.ridge = float(ridge)
        self.teams: list[str] = []
        self.team_index: dict[str, int] = {}
        self.params: np.ndarray | None = None
        self.fit_info: dict = {}

    def fit(self, matches: list[dict], reference_date: date) -> "RidgePoisson":
        self.teams = sorted({row["home"] for row in matches} | {row["away"] for row in matches})
        self.team_index = {team: idx for idx, team in enumerate(self.teams)}
        n = len(self.teams)
        hi = np.array([self.team_index[row["home"]] for row in matches], dtype=int)
        ai = np.array([self.team_index[row["away"]] for row in matches], dtype=int)
        hg = np.array([row["home_goals"] for row in matches], dtype=float)
        ag = np.array([row["away_goals"] for row in matches], dtype=float)
        venue = np.array([not row["neutral"] for row in matches], dtype=float)
        age = np.array([(reference_date - row["date"]).days for row in matches], dtype=float)
        weights = np.exp(-math.log(2.0) * np.maximum(age, 0.0) / self.half_life_days)
        weights *= np.array([importance(row["tournament"]) for row in matches])

        def objective(x: np.ndarray) -> tuple[float, np.ndarray]:
            mu, home_adv = x[0], x[1]
            attack = x[2 : 2 + n]
            defence = x[2 + n :]
            eta_h = mu + home_adv * venue + attack[hi] - defence[ai]
            eta_a = mu + attack[ai] - defence[hi]
            lam_h = np.exp(np.clip(eta_h, -5.0, 4.0))
            lam_a = np.exp(np.clip(eta_a, -5.0, 4.0))
            loss = np.sum(weights * (lam_h - hg * eta_h + gammaln(hg + 1.0)))
            loss += np.sum(weights * (lam_a - ag * eta_a + gammaln(ag + 1.0)))
            loss += 0.5 * self.ridge * (np.dot(attack, attack) + np.dot(defence, defence))
            loss += 0.5 * 0.5 * home_adv * home_adv

            rh = weights * (lam_h - hg)
            ra = weights * (lam_a - ag)
            grad = np.zeros_like(x)
            grad[0] = np.sum(rh + ra)
            grad[1] = np.sum(rh * venue) + 0.5 * home_adv
            np.add.at(grad[2 : 2 + n], hi, rh)
            np.add.at(grad[2 : 2 + n], ai, ra)
            np.add.at(grad[2 + n :], ai, -rh)
            np.add.at(grad[2 + n :], hi, -ra)
            grad[2 : 2 + n] += self.ridge * attack
            grad[2 + n :] += self.ridge * defence
            return float(loss), grad

        mean_goals = (hg.sum() + ag.sum()) / (2.0 * len(matches))
        initial = np.zeros(2 + 2 * n)
        initial[0] = math.log(max(mean_goals, 0.2))
        result = minimize(objective, initial, method="L-BFGS-B", jac=True, options={"maxiter": 500, "ftol": 1e-10})
        if not result.success:
            raise RuntimeError(f"P1 optimization failed: {result.message}")
        self.params = result.x
        self.fit_info = {
            "matches": len(matches),
            "teams": n,
            "effective_match_weight": round(float(weights.sum()), 3),
            "converged": bool(result.success),
            "iterations": int(result.nit),
            "objective": round(float(result.fun), 6),
            "home_advantage_log": round(float(result.x[1]), 6),
            "home_advantage_goal_multiplier": round(float(math.exp(result.x[1])), 6),
        }
        return self

    def predict(self, home: str, away: str, neutral: bool) -> tuple[float, float]:
        if self.params is None:
            raise RuntimeError("Model is not fitted")
        n = len(self.teams)
        mu, home_adv = self.params[0], self.params[1]
        attack = self.params[2 : 2 + n]
        defence = self.params[2 + n :]
        h = self.team_index.get(home)
        a = self.team_index.get(away)
        h_attack = 0.0 if h is None else attack[h]
        h_defence = 0.0 if h is None else defence[h]
        a_attack = 0.0 if a is None else attack[a]
        a_defence = 0.0 if a is None else defence[a]
        lh = math.exp(mu + home_adv * (not neutral) + h_attack - a_defence)
        la = math.exp(mu + a_attack - h_defence)
        return float(lh), float(la)


def multiclass_metrics(probabilities: np.ndarray, outcomes: np.ndarray) -> dict:
    eps = 1e-12
    chosen = probabilities[np.arange(len(outcomes)), outcomes]
    one_hot = np.eye(3)[outcomes]
    cdf_p = np.cumsum(probabilities, axis=1)[:, :2]
    cdf_y = np.cumsum(one_hot, axis=1)[:, :2]
    return {
        "n": int(len(outcomes)),
        "log_loss": round(float(-np.mean(np.log(np.clip(chosen, eps, 1.0)))), 6),
        "brier": round(float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1))), 6),
        "rps": round(float(np.mean(np.sum((cdf_p - cdf_y) ** 2, axis=1) / 2.0)), 6),
    }


def observed_outcome(row: dict) -> int:
    if row["home_goals"] > row["away_goals"]:
        return 0
    if row["home_goals"] == row["away_goals"]:
        return 1
    return 2


def validate_p1(all_recent: list[dict]) -> tuple[dict, list[dict]]:
    train = [row for row in all_recent if row["date"] < VALIDATION_START]
    valid = [row for row in all_recent if row["date"] >= VALIDATION_START]
    candidates = []
    for half_life in (730.0, 1095.0, 1460.0):
        for ridge in (2.0, 8.0, 20.0):
            model = RidgePoisson(half_life, ridge).fit(train, VALIDATION_START)
            probs = np.array([outcome_probs(*model.predict(row["home"], row["away"], row["neutral"])) for row in valid])
            metrics = multiclass_metrics(probs, np.array([observed_outcome(row) for row in valid]))
            candidates.append({"half_life_days": half_life, "ridge": ridge, **metrics})
    candidates.sort(key=lambda item: (item["log_loss"], item["rps"]))
    return candidates[0], candidates


def elo_multiplier(tournament: str) -> float:
    name = tournament.lower()
    if "fifa world cup" in name and "qualification" not in name:
        return 1.35
    if "qualification" in name or "qualifier" in name:
        return 1.15
    if "friendly" in name:
        return 0.75
    return 1.0


def build_sequential_elo(matches: list[dict], k_factor: float = 24.0) -> tuple[list[dict], dict, dict]:
    ratings = defaultdict(lambda: 1500.0)
    trends = defaultdict(float)
    feature_rows = []
    for row in matches:
        home, away = row["home"], row["away"]
        diff = ratings[home] - ratings[away]
        feature_rows.append(
            {
                "date": row["date"],
                "base": [1.0, diff / 400.0, float(not row["neutral"])],
                "trajectory": (trends[home] - trends[away]) / 50.0,
                "outcome": observed_outcome(row),
            }
        )
        # Keep Elo ratings venue-neutral; the calibrated outcome layer estimates home effect.
        expected = 1.0 / (1.0 + 10.0 ** (-diff / 400.0))
        actual = 1.0 if row["home_goals"] > row["away_goals"] else 0.5 if row["home_goals"] == row["away_goals"] else 0.0
        delta = k_factor * elo_multiplier(row["tournament"]) * (actual - expected)
        ratings[home] += delta
        ratings[away] -= delta
        trends[home] = 0.82 * trends[home] + delta
        trends[away] = 0.82 * trends[away] - delta
    return feature_rows, dict(ratings), dict(trends)


class SoftmaxCalibrator:
    """Ridge multinomial logistic calibration with away as the reference class."""

    def __init__(self, ridge: float = 1.0):
        self.ridge = ridge
        self.coef: np.ndarray | None = None

    def fit(self, x: np.ndarray, y: np.ndarray) -> "SoftmaxCalibrator":
        n_features = x.shape[1]

        def objective(flat: np.ndarray) -> tuple[float, np.ndarray]:
            coef = flat.reshape(2, n_features)
            logits = np.column_stack((x @ coef[0], x @ coef[1], np.zeros(len(x))))
            log_probs = logits - logsumexp(logits, axis=1, keepdims=True)
            loss = -float(log_probs[np.arange(len(y)), y].sum())
            loss += 0.5 * self.ridge * float(np.sum(coef[:, 1:] ** 2))
            probs = np.exp(log_probs)
            residual = probs - np.eye(3)[y]
            grad = np.vstack((residual[:, 0] @ x, residual[:, 1] @ x))
            grad[:, 1:] += self.ridge * coef[:, 1:]
            return loss, grad.ravel()

        result = minimize(objective, np.zeros(2 * n_features), method="L-BFGS-B", jac=True, options={"maxiter": 300})
        if not result.success:
            raise RuntimeError(f"P2 calibration failed: {result.message}")
        self.coef = result.x.reshape(2, n_features)
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        if self.coef is None:
            raise RuntimeError("Calibrator is not fitted")
        logits = np.column_stack((x @ self.coef[0], x @ self.coef[1], np.zeros(len(x))))
        return np.exp(logits - logsumexp(logits, axis=1, keepdims=True))


def p2_features(rows: list[dict], variant: str) -> tuple[np.ndarray, np.ndarray]:
    if variant == "current_elo":
        x = np.array([row["base"] for row in rows], dtype=float)
    else:
        x = np.array([row["base"] + [row["trajectory"]] for row in rows], dtype=float)
    y = np.array([row["outcome"] for row in rows], dtype=int)
    return x, y


def validate_p2(feature_rows: list[dict]) -> tuple[str, dict]:
    calibration_rows = [row for row in feature_rows if RECENT_START <= row["date"] < VALIDATION_START]
    validation_rows = [row for row in feature_rows if row["date"] >= VALIDATION_START]
    report = {}
    for variant in ("current_elo", "current_elo_plus_recent_trajectory"):
        train_x, train_y = p2_features(calibration_rows, variant)
        valid_x, valid_y = p2_features(validation_rows, variant)
        model = SoftmaxCalibrator(ridge=1.0).fit(train_x, train_y)
        report[variant] = multiclass_metrics(model.predict(valid_x), valid_y)
    chosen = min(report, key=lambda key: (report[key]["log_loss"], report[key]["rps"]))
    return chosen, report


class TournamentXG:
    """Opponent-adjusted log-link xG model with strong ridge shrinkage."""

    def __init__(self, ridge: float = 8.0):
        self.ridge = ridge
        self.teams: list[str] = []
        self.index: dict[str, int] = {}
        self.params: np.ndarray | None = None
        self.fit_info: dict = {}

    def fit(self, rows: list[dict]) -> "TournamentXG":
        self.teams = sorted({row["home"] for row in rows} | {row["away"] for row in rows})
        self.index = {team: idx for idx, team in enumerate(self.teams)}
        n = len(self.teams)
        hi = np.array([self.index[row["home"]] for row in rows])
        ai = np.array([self.index[row["away"]] for row in rows])
        hx = np.array([float(row["home_xg"]) for row in rows])
        ax = np.array([float(row["away_xg"]) for row in rows])

        def objective(x: np.ndarray) -> tuple[float, np.ndarray]:
            mu = x[0]
            attack = x[1 : 1 + n]
            defence = x[1 + n :]
            eh = mu + attack[hi] - defence[ai]
            ea = mu + attack[ai] - defence[hi]
            lh, la = np.exp(np.clip(eh, -5.0, 4.0)), np.exp(np.clip(ea, -5.0, 4.0))
            loss = float(np.sum(lh - hx * eh) + np.sum(la - ax * ea))
            loss += 0.5 * self.ridge * float(np.dot(attack, attack) + np.dot(defence, defence))
            rh, ra = lh - hx, la - ax
            grad = np.zeros_like(x)
            grad[0] = np.sum(rh + ra)
            np.add.at(grad[1 : 1 + n], hi, rh)
            np.add.at(grad[1 : 1 + n], ai, ra)
            np.add.at(grad[1 + n :], ai, -rh)
            np.add.at(grad[1 + n :], hi, -ra)
            grad[1 : 1 + n] += self.ridge * attack
            grad[1 + n :] += self.ridge * defence
            return loss, grad

        initial = np.zeros(1 + 2 * n)
        initial[0] = math.log(max(float(np.mean(np.r_[hx, ax])), 0.2))
        result = minimize(objective, initial, method="L-BFGS-B", jac=True, options={"maxiter": 500, "ftol": 1e-11})
        if not result.success:
            raise RuntimeError(f"P3 optimization failed: {result.message}")
        self.params = result.x
        self.fit_info = {
            "matches": len(rows),
            "teams": n,
            "ridge": self.ridge,
            "converged": bool(result.success),
            "iterations": int(result.nit),
            "global_xg_per_team": round(float(math.exp(result.x[0])), 6),
        }
        return self

    def predict_neutral(self, home: str, away: str) -> tuple[float, float]:
        if self.params is None:
            raise RuntimeError("P3 is not fitted")
        n = len(self.teams)
        attack = self.params[1 : 1 + n]
        defence = self.params[1 + n :]
        h, a = self.index[home], self.index[away]
        return (
            float(math.exp(self.params[0] + attack[h] - defence[a])),
            float(math.exp(self.params[0] + attack[a] - defence[h])),
        )


def load_p3(completed_results: list[dict]) -> list[dict]:
    with P3_PATH.open("r", encoding="utf-8-sig") as handle:
        rows = json.load(handle)
    required = {"home", "away", "home_xg", "away_xg", "home_goals", "away_goals"}
    clean = []
    target_pairs = {frozenset((target["home"], target["away"])) for target in TARGETS}
    result_name = {
        "USA": "United States",
        "T\u00fcrkiye": "Turkey",
        "Cabo Verde": "Cape Verde",
        "Congo DR": "DR Congo",
        "Korea Republic": "South Korea",
        "Czechia": "Czech Republic",
        "IR Iran": "Iran",
        "C\u00f4te d'Ivoire": "Ivory Coast",
    }
    for row in rows:
        if not required.issubset(row) or row["home_xg"] is None or row["away_xg"] is None:
            continue
        if frozenset((row["home"], row["away"])) in target_pairs:
            raise AssertionError(f"Target fixture leaked into P3 artifact: {row['home']} vs {row['away']}")
        matches = [
            result for result in completed_results
            if result["tournament"] == "FIFA World Cup"
            and result["date"] >= date(2026, 6, 1)
            and (
                (
                    result["home"] == result_name.get(row["home"], row["home"])
                    and result["away"] == result_name.get(row["away"], row["away"])
                    and result["home_goals"] == row["home_goals"]
                    and result["away_goals"] == row["away_goals"]
                )
                or (
                    result["home"] == result_name.get(row["away"], row["away"])
                    and result["away"] == result_name.get(row["home"], row["home"])
                    and result["home_goals"] == row["away_goals"]
                    and result["away_goals"] == row["home_goals"]
                )
            )
        ]
        if len(matches) != 1:
            raise AssertionError(f"P3 row does not have one exact pre-cutoff match: {row['filename']}")
        audited = dict(row)
        audited["matched_completed_date"] = max(match["date"] for match in matches).isoformat()
        clean.append(audited)
    if not clean or any(date.fromisoformat(row["matched_completed_date"]) >= CUTOFF for row in clean):
        raise AssertionError("P3 cutoff enforcement failed")
    return clean


def team_xg_aggregates(rows: list[dict], teams: list[str], elo: dict[str, float]) -> dict:
    out = {}
    for team in teams:
        games = []
        for row in rows:
            if row["home"] == team:
                games.append((row["away"], float(row["home_xg"]), float(row["away_xg"]), row["home_goals"], row["away_goals"]))
            elif row["away"] == team:
                games.append((row["home"], float(row["away_xg"]), float(row["home_xg"]), row["away_goals"], row["home_goals"]))
        out[team] = {
            "games": len(games),
            "xg_for": round(sum(item[1] for item in games), 3),
            "xg_against": round(sum(item[2] for item in games), 3),
            "xg_for_per_match": round(float(np.mean([item[1] for item in games])), 3),
            "xg_against_per_match": round(float(np.mean([item[2] for item in games])), 3),
            "goals_for": int(sum(item[3] for item in games)),
            "goals_against": int(sum(item[4] for item in games)),
            "opponents": [item[0] for item in games],
            "mean_opponent_pre_cutoff_elo": round(float(np.mean([elo.get(item[0], 1500.0) for item in games])), 2),
        }
    return out


def round_prob(value: float) -> float:
    return round(float(value), 8)


def markets_from_matrix(matrix: np.ndarray) -> dict:
    h_grid, a_grid = np.indices(matrix.shape)
    diff = h_grid - a_grid
    total = h_grid + a_grid
    one_x_two = {
        "home": round_prob(matrix[diff > 0].sum()),
        "draw": round_prob(matrix[diff == 0].sum()),
        "away": round_prob(matrix[diff < 0].sum()),
    }
    spreads = {}
    for handicap in (-2.5, -1.5, -0.5, 0.0, 0.5, 1.5, 2.5):
        adjusted = diff + handicap
        key = f"home_{handicap:+.1f}"
        spreads[key] = {
            "win": round_prob(matrix[adjusted > 0].sum()),
            "push": round_prob(matrix[adjusted == 0].sum()),
            "loss": round_prob(matrix[adjusted < 0].sum()),
        }
    totals = {}
    for line in (1.5, 2.5, 3.5, 4.5):
        totals[f"{line:.1f}"] = {
            "over": round_prob(matrix[total > line].sum()),
            "under": round_prob(matrix[total < line].sum()),
        }
    btts_yes = float(matrix[(h_grid > 0) & (a_grid > 0)].sum())
    team_totals = {"home": {}, "away": {}}
    for line in (0.5, 1.5, 2.5):
        team_totals["home"][f"{line:.1f}"] = {
            "over": round_prob(matrix[h_grid > line].sum()),
            "under": round_prob(matrix[h_grid < line].sum()),
        }
        team_totals["away"][f"{line:.1f}"] = {
            "over": round_prob(matrix[a_grid > line].sum()),
            "under": round_prob(matrix[a_grid < line].sum()),
        }
    return {
        "1x2": one_x_two,
        "spreads_home_handicap": spreads,
        "totals": totals,
        "btts": {"yes": round_prob(btts_yes), "no": round_prob(1.0 - btts_yes)},
        "team_totals": team_totals,
    }


def top_scores(matrix: np.ndarray, count: int = 10) -> list[dict]:
    flat_order = np.argsort(matrix.ravel())[::-1][:count]
    return [
        {
            "home_goals": int(index // matrix.shape[1]),
            "away_goals": int(index % matrix.shape[1]),
            "probability": round_prob(matrix.ravel()[index]),
        }
        for index in flat_order
    ]


def flatten_markets(markets: dict) -> dict[str, float]:
    flat = {}

    def walk(value, prefix=""):
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{prefix}.{key}" if prefix else key)
        elif isinstance(value, (float, int)):
            flat[prefix] = float(value)

    walk(markets)
    return flat


def uncertainty_intervals(
    home_lambda: float,
    away_lambda: float,
    disagreement: float,
    rng: np.random.Generator,
    contextual_widening: float = 0.0,
) -> tuple[dict, dict]:
    total = home_lambda + away_lambda
    log_ratio = math.log(home_lambda / away_lambda)
    total_sd = 0.11 + min(0.08, 0.20 * disagreement) + contextual_widening
    ratio_sd = 0.14 + min(0.10, 0.25 * disagreement) + contextual_widening
    values = defaultdict(list)
    lambda_draws = []
    for _ in range(500):
        draw_total = total * math.exp(rng.normal(-0.5 * total_sd**2, total_sd))
        draw_ratio = log_ratio + rng.normal(0.0, ratio_sd)
        draw_home = draw_total / (1.0 + math.exp(-draw_ratio))
        draw_away = draw_total - draw_home
        lambda_draws.append((draw_home, draw_away))
        matrix, _ = score_matrix(draw_home, draw_away)
        for key, value in flatten_markets(markets_from_matrix(matrix)).items():
            values[key].append(value)
    intervals = {
        key: {"p10": round_prob(np.quantile(sample, 0.10)), "p90": round_prob(np.quantile(sample, 0.90))}
        for key, sample in sorted(values.items())
    }
    lambda_array = np.array(lambda_draws)
    lambda_intervals = {
        "home": {"p10": round_prob(np.quantile(lambda_array[:, 0], 0.10)), "p90": round_prob(np.quantile(lambda_array[:, 0], 0.90))},
        "away": {"p10": round_prob(np.quantile(lambda_array[:, 1], 0.10)), "p90": round_prob(np.quantile(lambda_array[:, 1], 0.90))},
        "total": {"p10": round_prob(np.quantile(lambda_array.sum(axis=1), 0.10)), "p90": round_prob(np.quantile(lambda_array.sum(axis=1), 0.90))},
    }
    return lambda_intervals, intervals


def implied_log_ratio(total: float, p2_probs: np.ndarray) -> float:
    target_contrast = float(p2_probs[0] - p2_probs[2])

    def loss(log_ratio: float) -> float:
        home_lambda = total / (1.0 + math.exp(-log_ratio))
        away_lambda = total - home_lambda
        probs = outcome_probs(home_lambda, away_lambda)
        return (float(probs[0] - probs[2]) - target_contrast) ** 2

    result = minimize_scalar(loss, bounds=(-3.0, 3.0), method="bounded")
    return float(result.x)


def validate_probabilities(result: dict) -> list[dict]:
    checks = []
    for match in result["matches"]:
        markets = match["markets"]
        sums = {"1x2": sum(markets["1x2"].values()), "btts": sum(markets["btts"].values())}
        for line, values in markets["totals"].items():
            sums[f"total_{line}"] = sum(values.values())
        for side, lines in markets["team_totals"].items():
            for line, values in lines.items():
                sums[f"team_total_{side}_{line}"] = sum(values.values())
        for line, values in markets["spreads_home_handicap"].items():
            sums[f"spread_{line}"] = sum(values.values())
        max_error = max(abs(value - 1.0) for value in sums.values())
        if max_error > 2e-7:
            raise AssertionError(f"Probability complement failure for {match['id']}: {max_error}")
        checks.append({"match_id": match["id"], "families_checked": len(sums), "max_sum_error": max_error})
    return checks


def main() -> None:
    np.random.seed(SEED)
    rng = np.random.default_rng(SEED)
    payload, cache_status = download_or_read_cache()
    all_results, rejected = load_results(payload)
    recent = [row for row in all_results if row["date"] >= RECENT_START]
    elo_matches = [row for row in all_results if row["date"] >= ELO_START]

    best_p1, p1_candidates = validate_p1(recent)
    p1 = RidgePoisson(best_p1["half_life_days"], best_p1["ridge"]).fit(recent, CUTOFF)

    elo_features, current_elo, current_trends = build_sequential_elo(elo_matches)
    p2_variant, p2_validation = validate_p2(elo_features)
    final_calibration_rows = [row for row in elo_features if row["date"] >= RECENT_START]
    p2_x, p2_y = p2_features(final_calibration_rows, p2_variant)
    p2_calibrator = SoftmaxCalibrator(ridge=1.0).fit(p2_x, p2_y)

    p3_rows = load_p3(all_results)
    p3 = TournamentXG(ridge=8.0).fit(p3_rows)
    target_teams = sorted({team for target in TARGETS for team in (target["home"], target["away"])})
    p3_aggregates = team_xg_aggregates(p3_rows, target_teams, current_elo)

    match_outputs = []
    for target in TARGETS:
        home, away, neutral = target["home"], target["away"], target["neutral"]
        p1_lh, p1_la = p1.predict(home, away, neutral)
        p1_neutral_lh, p1_neutral_la = p1.predict(home, away, True)
        p3_lh, p3_la = p3.predict_neutral(home, away)
        if not neutral:
            p3_lh *= math.exp(float(p1.params[1]))
        sample_n = min(p3_aggregates[home]["games"], p3_aggregates[away]["games"])
        p3_weight = min(0.25, sample_n / (sample_n + 16.0))
        blend_lh = (1.0 - p3_weight) * p1_lh + p3_weight * p3_lh
        blend_la = (1.0 - p3_weight) * p1_la + p3_weight * p3_la

        base_features = [1.0, (current_elo.get(home, 1500.0) - current_elo.get(away, 1500.0)) / 400.0, float(not neutral)]
        if p2_variant == "current_elo_plus_recent_trajectory":
            base_features.append((current_trends.get(home, 0.0) - current_trends.get(away, 0.0)) / 50.0)
        p2_probs = p2_calibrator.predict(np.array([base_features]))[0]
        neutral_features = [1.0, (current_elo.get(home, 1500.0) - current_elo.get(away, 1500.0)) / 400.0, 0.0]
        if p2_variant == "current_elo_plus_recent_trajectory":
            neutral_features.append((current_trends.get(home, 0.0) - current_trends.get(away, 0.0)) / 50.0)
        p2_neutral_probs = p2_calibrator.predict(np.array([neutral_features]))[0]

        total_lambda = blend_lh + blend_la
        base_log_ratio = math.log(blend_lh / blend_la)
        p2_log_ratio = implied_log_ratio(total_lambda, p2_probs)
        capped_gap = float(np.clip(p2_log_ratio - base_log_ratio, -math.log(1.15), math.log(1.15)))
        ratio_adjustment_weight = 0.20
        final_log_ratio = base_log_ratio + ratio_adjustment_weight * capped_gap
        final_lh = total_lambda / (1.0 + math.exp(-final_log_ratio))
        final_la = total_lambda - final_lh
        matrix, truncated_mass = score_matrix(final_lh, final_la)
        markets = markets_from_matrix(matrix)
        disagreement = abs(math.log(max(p1_lh, 1e-6) / max(p3_lh, 1e-6))) + abs(math.log(max(p1_la, 1e-6) / max(p3_la, 1e-6)))
        lambda_intervals, market_intervals = uncertainty_intervals(
            final_lh,
            final_la,
            disagreement,
            rng,
            contextual_widening=float(target["uncertainty_widening"]),
        )

        match_outputs.append(
            {
                **target,
                "settlement_scope": "90_minutes_including_stoppage_time",
                "p1": {
                    "home_lambda": round_prob(p1_lh),
                    "away_lambda": round_prob(p1_la),
                    "1x2": dict(zip(("home", "draw", "away"), map(round_prob, outcome_probs(p1_lh, p1_la)))),
                    "home_effect_contribution": {
                        "applied": not neutral,
                        "fitted_log_effect": round_prob(float(p1.params[1]) if not neutral else 0.0),
                        "home_goal_multiplier": round_prob(math.exp(float(p1.params[1])) if not neutral else 1.0),
                        "home_lambda_delta_vs_neutral": round_prob(p1_lh - p1_neutral_lh),
                        "neutral_counterfactual_lambdas": {"home": round_prob(p1_neutral_lh), "away": round_prob(p1_neutral_la)},
                    },
                },
                "p2": {
                    "chosen_variant": p2_variant,
                    "home_elo": round(current_elo.get(home, 1500.0), 3),
                    "away_elo": round(current_elo.get(away, 1500.0), 3),
                    "home_recent_trajectory": round(current_trends.get(home, 0.0), 3),
                    "away_recent_trajectory": round(current_trends.get(away, 0.0), 3),
                    "1x2": dict(zip(("home", "draw", "away"), map(round_prob, p2_probs))),
                    "home_effect_contribution": {
                        "applied": not neutral,
                        "estimated_in_calibrated_outcome_layer": True,
                        "neutral_counterfactual_1x2": dict(zip(("home", "draw", "away"), map(round_prob, p2_neutral_probs))),
                        "home_win_probability_delta_vs_neutral": round_prob(float(p2_probs[0] - p2_neutral_probs[0])),
                    },
                    "role": "relative-strength ratio check only; does not set total goals or directly price totals/BTTS",
                },
                "p3": {
                    "home_lambda": round_prob(p3_lh),
                    "away_lambda": round_prob(p3_la),
                    "sample_games_minimum": sample_n,
                    "blend_weight": round_prob(p3_weight),
                    "cap": 0.25,
                },
                "combination": {
                    "pre_p2_home_lambda": round_prob(blend_lh),
                    "pre_p2_away_lambda": round_prob(blend_la),
                    "p2_ratio_adjustment_weight": ratio_adjustment_weight,
                    "p2_log_ratio_gap_before_cap": round_prob(p2_log_ratio - base_log_ratio),
                    "p2_log_ratio_gap_after_cap": round_prob(capped_gap),
                    "total_lambda_preserved_by_p2": True,
                },
                "final_lambdas": {"home": round_prob(final_lh), "away": round_prob(final_la), "total": round_prob(final_lh + final_la)},
                "markets": markets,
                "score_matrix": {
                    "support": f"0..{MAX_GOALS} goals per team",
                    "renormalized": True,
                    "pre_normalization_truncated_mass": truncated_mass,
                    "top_scores": top_scores(matrix),
                    "probabilities": [[round_prob(value) for value in row] for row in matrix],
                },
                "uncertainty": {
                    "method": "reproducible 500-draw lognormal total-goals and log-ratio scenario simulation",
                    "interpretation": "10th-90th scenario percentiles; heuristic model-risk range, not a frequentist confidence interval",
                    "contextual_widening": round_prob(float(target["uncertainty_widening"])),
                    "context_note": "Altitude and lineup uncertainty widen dispersion only; no arbitrary altitude xG coefficient or directional goal adjustment is applied.",
                    "lambda_intervals": lambda_intervals,
                    "market_probability_intervals": market_intervals,
                },
            }
        )

    result = {
        "metadata": {
            "model_version": "production-light-p1-p2-p3-0705-v1",
            "generated_at_utc": iso_now(),
            "random_seed": SEED,
            "cutoff_exclusive": CUTOFF.isoformat(),
            "latest_completed_result_used": max(row["date"] for row in all_results).isoformat(),
            "independence_statement": "No Polymarket prices, betting odds, bookmaker consensus, or Opta predictions are read or used.",
            "p1_method": "Penalized time-decayed independent Poisson attack-defense model. The penalty is ridge/MAP-like shrinkage; this is explicitly not a fully Bayesian posterior model.",
            "p2_method": "Venue-neutral sequential Elo plus ridge multinomial-logistic 1X2 calibration with an empirically fitted home indicator; temporal validation selects whether recent Elo trajectory is retained.",
            "p3_method": "Opponent-adjusted log-link tournament xG attack-defense model with strong ridge shrinkage; P3 enters lambdas with a hard weight cap of 25%.",
            "limitations": [
                "Independent Poisson omits within-match score correlation, red-card timing, lineups, injuries, rest, weather, and tactical matchup effects.",
                "Historical international results mix competition strength and may include scores after extra time depending on source conventions.",
                "Ridge shrinkage is not full Bayesian uncertainty propagation; interval outputs are model-risk scenarios rather than posterior credible intervals.",
                "P3 uses only a small current-tournament snapshot and has no explicit venue field; its home adjustment, when applicable, is borrowed from P1.",
                "P2 is validated only as a 1X2 strength model and is deliberately prevented from independently setting totals, BTTS, or score probabilities.",
                "No player availability or confirmed starting XI information is included.",
                "Azteca altitude is treated as added uncertainty, not as a directional xG coefficient; the Mexico home effect comes from the fitted historical home indicator.",
            ],
        },
        "sources": {
            "international_results_csv": RESULTS_URL,
            "international_results_repository": RESULTS_REPO_URL,
            "international_results_sha256": hashlib.sha256(payload).hexdigest(),
            "cache_status": cache_status,
            "fifa_xg_local_artifact": str(P3_PATH),
            "fifa_training_centre": FIFA_TRAINING_URL,
            "fifa_match_report_urls_in_artifact": sorted({row.get("url") for row in p3_rows if row.get("url")}),
        },
        "data_audit": {
            "completed_results_before_cutoff": len(all_results),
            "p1_recent_results": len(recent),
            "p2_elo_results": len(elo_matches),
            "p3_tournament_matches": len(p3_rows),
            "p3_latest_matched_completed_date": max(row["matched_completed_date"] for row in p3_rows),
            "p3_cutoff_assertion_passed": all(
                date.fromisoformat(row["matched_completed_date"]) < CUTOFF for row in p3_rows
            ),
            "excluded_rows": rejected,
            "cutoff_assertion_passed": all(row["date"] < CUTOFF for row in all_results),
        },
        "validation": {
            "protocol": {
                "training": f"{RECENT_START.isoformat()} through {VALIDATION_START.isoformat()} exclusive",
                "holdout": f"{VALIDATION_START.isoformat()} through {CUTOFF.isoformat()} exclusive",
                "temporal_ordering": True,
            },
            "p1_selected": best_p1,
            "p2_variants": p2_validation,
            "p2_selected": p2_variant,
        },
        "fitted_models": {"p1": p1.fit_info, "p3": p3.fit_info},
        "p3_team_sample_aggregates": p3_aggregates,
        "matches": match_outputs,
    }
    result["probability_validation"] = validate_probabilities(result)

    backtest = {
        "metadata": {
            "generated_at_utc": result["metadata"]["generated_at_utc"],
            "cutoff_exclusive": CUTOFF.isoformat(),
            "random_seed": SEED,
            "note": "All validation predictions are made on matches chronologically after the calibration/training window.",
        },
        "p1_hyperparameter_candidates": p1_candidates,
        "p1_selected": best_p1,
        "p2_variant_comparison": p2_validation,
        "p2_selected": p2_variant,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    BACKTEST_PATH.write_text(json.dumps(backtest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT_PATH), "backtest": str(BACKTEST_PATH), "matches": [{"id": m["id"], "lambdas": m["final_lambdas"], "1x2": m["markets"]["1x2"]} for m in match_outputs]}, indent=2))


if __name__ == "__main__":
    main()
