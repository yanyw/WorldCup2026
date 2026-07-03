import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODEL = DATA / "model_output_0702.json"
DECISIONS = DATA / "portfolio_decisions_0702.json"
LIVE = DATA / "polymarket_live_0702.json"
TOLERANCE = 0.002


def assert_close(label: str, actual: float, expected: float) -> None:
    if abs(actual - expected) > TOLERANCE:
        raise AssertionError(f"{label}: actual={actual:.6f}, expected={expected:.6f}")


def main() -> None:
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    live = json.loads(LIVE.read_text(encoding="utf-8"))
    if not (model["market_snapshot_beijing"] == decisions["snapshot_beijing"] == live["snapshot_beijing"]):
        raise AssertionError("Model, portfolio, and live market snapshots are not aligned")
    snapshot_time = datetime.fromisoformat(live["snapshot_beijing"])
    age_minutes = (datetime.now(ZoneInfo("Asia/Shanghai")) - snapshot_time).total_seconds() / 60.0
    if age_minutes > 30:
        raise AssertionError(f"Market snapshot is stale ({age_minutes:.0f} minutes); refresh before execution")

    matches = {match["id"]: match for match in model["matches"]}
    live_matches = {match["id"]: match for match in live["matches"]}
    bankroll = decisions["bankroll_usdc"]
    seen = set()
    total_stake = 0.0

    for match in matches.values():
        probabilities = match["probabilities"]
        assert_close(f"{match['id']} moneyline", sum(probabilities[key] for key in ("home", "draw", "away")), 1.0)
        assert_close(f"{match['id']} spread", probabilities["home_spread"] + probabilities["away_spread"], 1.0)
        assert_close(f"{match['id']} total", probabilities["over"] + probabilities["under"], 1.0)
        assert_close(f"{match['id']} btts", probabilities["btts_yes"] + probabilities["btts_no"], 1.0)

    for position in decisions["positions"]:
        match_id = position["match_id"]
        if match_id in seen:
            raise AssertionError(f"More than one position for match {match_id}")
        seen.add(match_id)
        total_stake += position["stake_usdc"]
        probability = position["trade_probability"]
        maximum = position["maximum_price"]
        live_match = live_matches[match_id]
        if position["market"] == "combined_total_under_2_5":
            record, side = live_match["total"], "no"
        elif position["market"] == "combined_total_over_2_5":
            record, side = live_match["total"], "yes"
        elif position["market"] in ("austria_plus_1_5", "paraguay_plus_1_5"):
            record, side = live_match["spread"], "no"
        elif position["market"] == "btts_no":
            record, side = live_match["props"]["btts"], "no"
        else:
            raise AssertionError(f"No live-price mapping for {position['market']}")
        if side not in record.get("clob_quotes", {}):
            raise AssertionError(f"Missing direct CLOB quote for {match_id} {side}")
        quote = record["clob_quotes"][side]
        live_bid = quote["best_bid"]
        live_ask = quote["best_ask"]
        schedule = record.get("fee_schedule")
        if not schedule or schedule.get("rate") is None:
            raise AssertionError(f"Missing fee schedule for {match_id}")
        live_fee_rate = float(schedule["rate"])
        assert_close(f"{match_id} best bid", position["snapshot_best_bid"], live_bid)
        assert_close(f"{match_id} executable ask", position["snapshot_price"], live_ask)
        assert_close(f"{match_id} fee rate", position["fee_rate"], live_fee_rate)
        maker_edge = probability - maximum
        if maker_edge < 0.04 - 1e-9:
            raise AssertionError(f"Maker edge below 4pp for {match_id}: {maker_edge:.4f}")
        if "taker_allowed" in position["execution"]:
            taker_maximum = position.get("maximum_taker_price", maximum)
            if taker_maximum > maximum:
                raise AssertionError(f"Taker maximum exceeds maker maximum for {match_id}")
            fee = live_fee_rate * taker_maximum * (1.0 - taker_maximum)
            taker_edge = probability - taker_maximum - fee
            if taker_edge < 0.04:
                raise AssertionError(f"Taker edge below 4pp for {match_id}: {taker_edge:.4f}")
        taker_maximum = position.get("maximum_taker_price", maximum)
        expected_status = (
            "TAKER_ACTIONABLE"
            if "taker_allowed" in position["execution"] and live_ask <= taker_maximum
            else "MAKER_ORDER"
        )
        if position["status"] != expected_status:
            raise AssertionError(f"Wrong status for {match_id}: {position['status']} != {expected_status}")

        kelly = position["kelly_trace"]
        kelly_price = position.get("maximum_taker_price", maximum) if "taker_allowed" in position["execution"] else maximum
        kelly_fee = live_fee_rate * kelly_price * (1.0 - kelly_price) if "taker_allowed" in position["execution"] else 0.0
        kelly_cost = kelly_price + kelly_fee
        full_kelly = (probability - kelly_cost) / (1.0 - kelly_cost)
        assert_close(f"{match_id} Kelly cost", kelly["fee_adjusted_cost"], kelly_cost)
        assert_close(f"{match_id} full Kelly", kelly["full_kelly"], full_kelly)
        assert_close(f"{match_id} fractional Kelly", kelly["fractional_kelly"], full_kelly * 0.15)
        calculated_stake = bankroll * full_kelly * 0.15 * kelly["confidence_factor"]
        if position["stake_usdc"] > calculated_stake + 0.15:
            raise AssertionError(f"Stake exceeds audited Kelly result for {match_id}")
        print(
            f"OK {match_id}: {position['market']}, stake={position['stake_usdc']:.1f}, "
            f"maker edge at max={maker_edge:.1%}, status={position['status']}"
        )

    maximum_stake = bankroll * decisions["portfolio_limits"]["maximum_total_stake_pct"] / 100.0
    if total_stake > maximum_stake:
        raise AssertionError(f"Portfolio stake {total_stake} exceeds cap {maximum_stake}")
    print(f"OK portfolio: maximum stake={total_stake:.1f} USDC ({total_stake / bankroll:.2%})")


if __name__ == "__main__":
    main()
