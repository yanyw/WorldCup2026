#!/usr/bin/env python3
"""Price an equal-share basket of four 2026 World Cup winner contracts."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "data" / "model_output_0702.json"
OUTPUT_PATH = ROOT / "data" / "winner_basket_model_0702.json"
TEAMS = ("FRA", "ARG", "ESP", "ENG")
FEE_RATE = 0.03
OPTA_TMCL = "873cbl9cd9butm4air0mugxzo"
OPTA_AUTH = "1luxdlbb08vww1ba5zbk8jht5l"

NAME_TO_CODE = {
    "France": "FRA", "Argentina": "ARG", "Spain": "ESP", "England": "ENG",
    "Brazil": "BRA", "Portugal": "POR", "Mexico": "MEX", "USA": "USA",
    "Morocco": "MAR", "Colombia": "COL", "Norway": "NOR", "Belgium": "BEL",
    "Switzerland": "SUI", "Croatia": "CRO", "Canada": "CAN", "Paraguay": "PAR",
    "Australia": "AUS", "Egypt": "EGY", "Austria": "AUT", "Ghana": "GHA",
    "Algeria": "ALG", "Cape Verde": "CPV",
}


def poisson(rate: float, goals: int) -> float:
    return math.exp(-rate) * rate**goals / math.factorial(goals)


def result_probabilities(rate_a: float, rate_b: float, limit: int = 12) -> tuple[float, float, float]:
    win_a = draw = win_b = 0.0
    for goals_a in range(limit + 1):
        for goals_b in range(limit + 1):
            probability = poisson(rate_a, goals_a) * poisson(rate_b, goals_b)
            if goals_a > goals_b:
                win_a += probability
            elif goals_a == goals_b:
                draw += probability
            else:
                win_b += probability
    total = win_a + draw + win_b
    return win_a / total, draw / total, win_b / total


def strength_rates(model: dict, team_a: str, team_b: str) -> tuple[float, float]:
    rates = []
    for key in ("xg_model", "goal_model"):
        component = model[key]
        rates.append((
            math.exp(component["mu"] + component["attack"][team_a] + component["vulnerability"][team_b]),
            math.exp(component["mu"] + component["attack"][team_b] + component["vulnerability"][team_a]),
        ))
    return tuple(
        math.exp(0.85 * math.log(rates[0][side]) + 0.15 * math.log(rates[1][side]))
        for side in (0, 1)
    )


def advance_probability(model: dict, team_a: str, team_b: str) -> float:
    rate_a, rate_b = strength_rates(model, team_a, team_b)
    win_90, draw_90, _ = result_probabilities(rate_a, rate_b)
    win_et, draw_et, _ = result_probabilities(rate_a / 3.0, rate_b / 3.0)
    return win_90 + draw_90 * (win_et + 0.5 * draw_et)


def team(team_code: str) -> dict[str, float]:
    return {team_code: 1.0}


def match(model: dict, side_a: dict[str, float], side_b: dict[str, float]) -> dict[str, float]:
    winners: dict[str, float] = {}
    for team_a, probability_a in side_a.items():
        for team_b, probability_b in side_b.items():
            meeting_probability = probability_a * probability_b
            advance_a = advance_probability(model, team_a, team_b)
            winners[team_a] = winners.get(team_a, 0.0) + meeting_probability * advance_a
            winners[team_b] = winners.get(team_b, 0.0) + meeting_probability * (1.0 - advance_a)
    return winners


def tournament(model: dict) -> dict[str, float]:
    # Remaining round-of-32 matches, in official match-number order M83-M88.
    m83 = match(model, team("ESP"), team("AUT"))
    m84 = match(model, team("POR"), team("CRO"))
    m85 = match(model, team("SUI"), team("ALG"))
    m86 = match(model, team("AUS"), team("EGY"))
    m87 = match(model, team("ARG"), team("CPV"))
    m88 = match(model, team("COL"), team("GHA"))

    # Round of 16. M89-M92 and M94 participants are already known.
    m89 = match(model, team("PAR"), team("FRA"))
    m90 = match(model, team("CAN"), team("MAR"))
    m91 = match(model, team("BRA"), team("NOR"))
    m92 = match(model, team("MEX"), team("ENG"))
    m93 = match(model, m83, m84)
    m94 = match(model, team("BEL"), team("USA"))
    m95 = match(model, m86, m88)
    m96 = match(model, m85, m87)

    qf_1 = match(model, m89, m90)
    qf_2 = match(model, m93, m94)
    qf_3 = match(model, m91, m92)
    qf_4 = match(model, m95, m96)
    semifinal_1 = match(model, qf_1, qf_2)
    semifinal_2 = match(model, qf_3, qf_4)
    return match(model, semifinal_1, semifinal_2)


def fetch_json(url: str) -> object:
    for attempt in range(5):
        try:
            request = Request(url, headers={"Accept": "application/json", "User-Agent": "wc2026-research/2.0"})
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2)


def market_snapshot() -> dict:
    event = fetch_json("https://gamma-api.polymarket.com/events?slug=world-cup-winner")[0]
    probabilities = {}
    selected_quotes = {}
    active_sum = 0.0
    for market in event["markets"]:
        if not market.get("active") or market.get("closed"):
            continue
        outcomes = json.loads(market["outcomes"])
        outcome_prices = [float(value) for value in json.loads(market["outcomePrices"])]
        yes_index = outcomes.index("Yes")
        midpoint = outcome_prices[yes_index]
        active_sum += midpoint
        question = market["question"]
        country = question.removeprefix("Will ").removesuffix(" win the 2026 FIFA World Cup?")
        code = NAME_TO_CODE[country]
        probabilities[code] = midpoint
        if code in TEAMS:
            token_id = json.loads(market["clobTokenIds"])[yes_index]
            book = fetch_json("https://clob.polymarket.com/book?" + urlencode({"token_id": token_id}))
            bid = max(float(level["price"]) for level in book["bids"])
            ask = min(float(level["price"]) for level in book["asks"])
            fee_rate = float(market["feeSchedule"]["rate"])
            selected_quotes[code] = {
                "midpoint": midpoint,
                "best_bid": bid,
                "best_ask": ask,
                "fee_rate": fee_rate,
                "fee_per_share": fee_rate * ask * (1.0 - ask),
            }
    normalized = {code: value / active_sum for code, value in probabilities.items()}
    return {
        "event_updated_at": event["updatedAt"],
        "active_yes_midpoint_sum": active_sum,
        "normalized_probabilities": normalized,
        "selected_quotes": selected_quotes,
    }


def opta_snapshot() -> dict:
    callback = f"TM18_{OPTA_TMCL}"
    url = (
        f"https://api.performfeeds.com/soccerdata/seasonandtournamentsimulations/{OPTA_AUTH}?"
        + urlencode({"tmcl": OPTA_TMCL, "_rt": "c", "_fmt": "jsonp", "_clbk": callback})
    )
    request = Request(url, headers={"User-Agent": "wc2026-research/2.0", "Referer": "https://dataviz.theanalyst.com/"})
    with urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8")
    data = json.loads(payload[payload.find("(") + 1 : payload.rfind(")")])
    final_stage = next(stage for stage in data["stages"]["stage"] if stage["name"] == "Final")
    probabilities = {}
    for contestant in final_stage["contestants"]["contestant"]:
        prediction = {item["typeId"]: item["value"] for item in contestant["predictions"][0]["predicted"]}
        probabilities[contestant["name"]] = float(prediction["2"].rstrip("%")) / 100.0
    selected = {code: probabilities[name] for name, code in NAME_TO_CODE.items() if code in TEAMS}
    return {
        "last_updated": data["lastUpdated"],
        "source": "https://dataviz.theanalyst.com/ad-hoc/pmk-wc-bracket-2026-07-01/",
        "champion_probabilities": probabilities,
        "selected_probabilities": selected,
        "basket_probability": sum(selected.values()),
    }


def main() -> None:
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    internal = tournament(model)
    market = market_snapshot()
    opta = opta_snapshot()
    basket_internal_probability = sum(internal[code] for code in TEAMS)
    basket_market_probability = sum(market["normalized_probabilities"][code] for code in TEAMS)
    quotes = market["selected_quotes"]
    contract_cost = sum(quotes[code]["best_ask"] for code in TEAMS)
    taker_fees = sum(quotes[code]["fee_per_share"] for code in TEAMS)
    total_cost = contract_cost + taker_fees
    opta_probability = opta["basket_probability"]
    individual_pnl = {}
    for code in TEAMS:
        quote = quotes[code]
        cost = quote["best_ask"] + quote["fee_per_share"]
        fair_probability = opta["selected_probabilities"][code]
        individual_pnl[code] = {
            "opta_probability": fair_probability,
            "taker_cost": cost,
            "expected_profit": fair_probability - cost,
            "expected_roi": (fair_probability - cost) / cost,
            "maker_expected_profit_at_current_bid": fair_probability - quote["best_bid"],
        }
    output = {
        "assumptions": {
            "basket": "one YES share each for France, Argentina, Spain, and England",
            "regular_time": "independent Poisson from FIFA-only 85/15 xG-goals strength model",
            "extra_time": "same scoring rates scaled to 30/90",
            "penalties": "50/50 after an extra-time draw",
            "bracket": "current bracket after matches M73-M82",
        },
        "internal_champion_probabilities": dict(sorted(internal.items(), key=lambda item: item[1], reverse=True)),
        "market": market,
        "opta_current": opta,
        "individual_pnl_using_opta": individual_pnl,
        "basket": {
            "internal_probability": basket_internal_probability,
            "market_normalized_probability": basket_market_probability,
            "contract_ask_cost": contract_cost,
            "taker_fees": taker_fees,
            "total_taker_cost": total_cost,
            "profit_if_one_wins": 1.0 - total_cost,
            "loss_if_none_wins": -total_cost,
            "expected_profit_internal": basket_internal_probability - total_cost,
            "expected_profit_market": basket_market_probability - total_cost,
            "expected_profit_opta": opta_probability - total_cost,
            "roi_internal": (basket_internal_probability - total_cost) / total_cost,
            "roi_market": (basket_market_probability - total_cost) / total_cost,
            "roi_opta": (opta_probability - total_cost) / total_cost,
        },
    }
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Internal top teams")
    for code, probability in list(output["internal_champion_probabilities"].items())[:12]:
        print(f"{code}: {probability:.2%}")
    print("Basket", json.dumps(output["basket"], indent=2))


if __name__ == "__main__":
    main()
