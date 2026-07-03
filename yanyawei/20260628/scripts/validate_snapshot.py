import json
import math
from pathlib import Path


SNAPSHOT = Path(__file__).resolve().parents[1] / "data" / "market_model_snapshot_0629.json"
TOLERANCE = 0.002


def poisson(k: int, rate: float) -> float:
    return math.exp(-rate) * rate**k / math.factorial(k)


def model_probabilities(home_rate: float, away_rate: float) -> dict[str, float]:
    matrix = {
        (home, away): poisson(home, home_rate) * poisson(away, away_rate)
        for home in range(13)
        for away in range(13)
    }
    home_win = sum(value for (home, away), value in matrix.items() if home > away)
    draw = sum(matrix[(score, score)] for score in range(13))
    away_win = 1.0 - home_win - draw
    total_rate = home_rate + away_rate
    under_2_5 = math.exp(-total_rate) * (1.0 + total_rate + total_rate**2 / 2.0)
    return {
        "home": home_win,
        "draw": draw,
        "away": away_win,
        "under_2_5": under_2_5,
    }


def assert_close(label: str, actual: float, expected: float) -> None:
    if abs(actual - expected) > TOLERANCE:
        raise AssertionError(f"{label}: calculated={actual:.4f}, snapshot={expected:.4f}")


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    for match in snapshot["matches"]:
        internal = match["internal"]
        calculated = model_probabilities(internal["lambda_home"], internal["lambda_away"])
        stored_moneyline = internal["moneyline"]

        for outcome in ("home", "draw", "away"):
            assert_close(
                f"{match['match']} {outcome}",
                calculated[outcome],
                stored_moneyline[outcome],
            )
        assert_close(
            f"{match['match']} under_2_5",
            calculated["under_2_5"],
            internal["under_2_5"],
        )
        assert_close(
            f"{match['match']} moneyline sum",
            sum(stored_moneyline.values()),
            1.0,
        )
        print(f"OK {match['match']}: 1X2 and under 2.5 are consistent")


if __name__ == "__main__":
    main()
