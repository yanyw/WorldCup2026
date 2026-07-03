import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIFA_STATS = DATA / "fifa_match_stats_0702.json"
MARKETS = DATA / "market_inputs_0702.json"
OUTPUT = DATA / "model_output_0702.json"
FEE_RATE = 0.03


def score_matrix(home_rate: float, away_rate: float, limit: int = 12) -> np.ndarray:
    home = np.array([math.exp(-home_rate) * home_rate**i / math.factorial(i) for i in range(limit + 1)])
    away = np.array([math.exp(-away_rate) * away_rate**i / math.factorial(i) for i in range(limit + 1)])
    matrix = np.outer(home, away)
    matrix /= matrix.sum()
    return matrix


def probabilities(home_rate: float, away_rate: float, total_line: float, spread_line: float) -> dict:
    matrix = score_matrix(home_rate, away_rate)
    home_win = float(np.tril(matrix, -1).sum())
    draw = float(np.trace(matrix))
    away_win = 1.0 - home_win - draw
    over = sum(
        matrix[home, away]
        for home in range(matrix.shape[0])
        for away in range(matrix.shape[1])
        if home + away > total_line
    )
    if spread_line == -1.5:
        home_spread = sum(
            matrix[home, away]
            for home in range(matrix.shape[0])
            for away in range(matrix.shape[1])
            if home - away >= 2
        )
    elif spread_line == 1.5:
        home_spread = sum(
            matrix[home, away]
            for home in range(matrix.shape[0])
            for away in range(matrix.shape[1])
            if home - away >= -1
        )
    else:
        raise ValueError(f"Unsupported spread line: {spread_line}")
    btts_yes = (1.0 - math.exp(-home_rate)) * (1.0 - math.exp(-away_rate))
    return {
        "home": home_win,
        "draw": draw,
        "away": away_win,
        "home_spread": float(home_spread),
        "away_spread": 1.0 - float(home_spread),
        "over": float(over),
        "under": 1.0 - float(over),
        "btts_yes": btts_yes,
        "btts_no": 1.0 - btts_yes,
    }


def fit_strength_model(matches: list[dict], metric: str) -> tuple[float, dict[str, float], dict[str, float]]:
    teams = sorted({match[side] for match in matches for side in ("home_code", "away_code")})
    index = {team: i for i, team in enumerate(teams)}
    observations = []
    for match in matches:
        weight = 1.25 if match["stage"] == "knockout" else 1.0
        if "M27" in match["filename"]:  # Canada-Qatar was distorted by two red cards.
            weight *= 0.35
        observations.extend([
            (match["home_code"], match["away_code"], match[f"home_{metric}"], weight),
            (match["away_code"], match["home_code"], match[f"away_{metric}"], weight),
        ])
    average = sum(y for _, _, y, _ in observations) / len(observations)
    initial = np.zeros(1 + 2 * len(teams))
    initial[0] = math.log(average)

    def objective(params: np.ndarray) -> float:
        mu = params[0]
        attack = params[1 : 1 + len(teams)]
        vulnerability = params[1 + len(teams) :]
        loss = 0.0
        for team, opponent, observed, weight in observations:
            log_rate = mu + attack[index[team]] + vulnerability[index[opponent]]
            rate = math.exp(max(-3.0, min(2.0, log_rate)))
            loss += weight * (rate - observed * math.log(rate))
        ridge = 1.6 * (float(np.dot(attack, attack)) + float(np.dot(vulnerability, vulnerability)))
        centering = 20.0 * (float(attack.mean()) ** 2 + float(vulnerability.mean()) ** 2)
        return loss + ridge + centering

    result = minimize(objective, initial, method="L-BFGS-B")
    if not result.success:
        raise RuntimeError(result.message)
    params = result.x
    attack = {team: float(params[1 + index[team]]) for team in teams}
    vulnerability = {team: float(params[1 + len(teams) + index[team]]) for team in teams}
    return float(params[0]), attack, vulnerability


def fit_rates(target: dict, total_target: tuple[float, float] | None = None) -> tuple[float, float]:
    def objective(log_rates: np.ndarray) -> float:
        home_rate, away_rate = np.exp(log_rates)
        total_line = total_target[0] if total_target else 2.5
        probs = probabilities(home_rate, away_rate, total_line, -1.5)
        loss = sum((probs[key] - target[key]) ** 2 for key in ("home", "draw", "away"))
        if total_target:
            loss += 1.5 * (probs["over"] - total_target[1]) ** 2
        return loss

    result = minimize(objective, np.log([1.4, 1.0]), method="L-BFGS-B", bounds=[(-2.0, 1.5), (-2.0, 1.5)])
    if not result.success:
        raise RuntimeError(result.message)
    return tuple(float(value) for value in np.exp(result.x))


def normalize(prices: dict, keys: tuple[str, ...]) -> dict:
    total = sum(prices[key] for key in keys)
    return {key: prices[key] / total for key in keys}


def evaluate_market(probability: float, price: float) -> dict:
    fee_per_share = FEE_RATE * price * (1.0 - price)
    return {
        "probability": probability,
        "price": price,
        "maker_edge": probability - price,
        "taker_fee_per_share": fee_per_share,
        "taker_edge": probability - price - fee_per_share,
    }


def main() -> None:
    fifa = json.loads(FIFA_STATS.read_text(encoding="utf-8"))
    market_data = json.loads(MARKETS.read_text(encoding="utf-8"))
    xg_mu, xg_attack, xg_vulnerability = fit_strength_model(fifa, "xg")
    goal_mu, goal_attack, goal_vulnerability = fit_strength_model(fifa, "goals")
    rng = np.random.default_rng(20260702)
    output = {
        "market_snapshot_beijing": market_data["snapshot_beijing"],
        "xg_model": {"mu": xg_mu, "attack": xg_attack, "vulnerability": xg_vulnerability},
        "goal_model": {"mu": goal_mu, "attack": goal_attack, "vulnerability": goal_vulnerability},
        "matches": [],
    }

    for match in market_data["matches"]:
        xg_rates = (
            math.exp(xg_mu + xg_attack[match["home"]] + xg_vulnerability[match["away"]]),
            math.exp(xg_mu + xg_attack[match["away"]] + xg_vulnerability[match["home"]]),
        )
        goal_rates = (
            math.exp(goal_mu + goal_attack[match["home"]] + goal_vulnerability[match["away"]]),
            math.exp(goal_mu + goal_attack[match["away"]] + goal_vulnerability[match["home"]]),
        )
        data_rates = tuple(
            math.exp(0.85 * math.log(xg_rates[i]) + 0.15 * math.log(goal_rates[i]))
            for i in (0, 1)
        )
        moneyline_fair = normalize(match["moneyline"], ("home", "draw", "away"))
        total_fair = normalize(match["total"], ("over", "under"))["over"]
        market_rates = fit_rates(moneyline_fair, (match["total"]["line"], total_fair))
        components = [(data_rates, 0.35 if "opta" in match else 0.55), (market_rates, 0.25 if "opta" in match else 0.45)]
        if "opta" in match:
            opta_rates = fit_rates(match["opta"])
            components.append((opta_rates, 0.40))
        else:
            opta_rates = None
        final_rates = tuple(
            math.exp(sum(weight * math.log(rates[i]) for rates, weight in components))
            for i in (0, 1)
        )
        probs = probabilities(*final_rates, match["total"]["line"], match["spread"]["line"])

        sigma = 0.11 if "opta" in match else 0.17
        samples = {key: [] for key in probs}
        for sampled in rng.normal(np.log(final_rates), sigma, size=(4000, 2)):
            sample_probs = probabilities(*np.exp(sampled), match["total"]["line"], match["spread"]["line"])
            for key, value in sample_probs.items():
                samples[key].append(value)
        intervals = {key: [float(np.quantile(values, 0.10)), float(np.quantile(values, 0.90))] for key, values in samples.items()}

        candidates = {
            "home_ml": evaluate_market(probs["home"], match["moneyline"]["home"]),
            "draw_ml": evaluate_market(probs["draw"], match["moneyline"]["draw"]),
            "away_ml": evaluate_market(probs["away"], match["moneyline"]["away"]),
            "home_spread": evaluate_market(probs["home_spread"], match["spread"]["home"]),
            "away_spread": evaluate_market(probs["away_spread"], match["spread"]["away"]),
            "over": evaluate_market(probs["over"], match["total"]["over"]),
            "under": evaluate_market(probs["under"], match["total"]["under"]),
        }
        for prop, price in match.get("props", {}).items():
            candidates[prop] = evaluate_market(probs[prop], price)
        output["matches"].append({
            **match,
            "rates": {"xg": xg_rates, "goals": goal_rates, "data": data_rates, "market": market_rates, "opta": opta_rates, "final": final_rates},
            "probabilities": probs,
            "interval_10_90": intervals,
            "candidates": candidates,
        })

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    for match in output["matches"]:
        ranked = sorted(match["candidates"].items(), key=lambda item: item[1]["maker_edge"], reverse=True)
        print(match["id"], "rates", [round(value, 2) for value in match["rates"]["final"]])
        for name, candidate in ranked[:3]:
            print(" ", name, "p", round(candidate["probability"], 3), "price", candidate["price"], "maker", round(candidate["maker_edge"], 3), "taker", round(candidate["taker_edge"], 3))


if __name__ == "__main__":
    main()
