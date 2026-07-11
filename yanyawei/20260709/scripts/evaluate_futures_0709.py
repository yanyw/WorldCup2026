#!/usr/bin/env python3
"""Combine independent models, market-informed evidence, and executable books."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "data" / "model_results_0705.json"
EVIDENCE_PATH = ROOT / "data" / "external_evidence_0705.json"
MARKET_PATH = ROOT / "data" / "polymarket_snapshot_0705.json"
OUTPUT_PATH = ROOT / "data" / "candidate_evaluation_0705.json"
BANKROLL = 1000.0


def matrix(home_lambda: float, away_lambda: float, limit: int = 12) -> np.ndarray:
    home = np.array([math.exp(-home_lambda) * home_lambda**i / math.factorial(i) for i in range(limit + 1)])
    away = np.array([math.exp(-away_lambda) * away_lambda**i / math.factorial(i) for i in range(limit + 1)])
    result = np.outer(home, away)
    return result / result.sum()


def score_probabilities(home_lambda: float, away_lambda: float) -> dict:
    scores = matrix(home_lambda, away_lambda)
    result = {
        "1x2.home": float(np.tril(scores, -1).sum()),
        "1x2.draw": float(np.trace(scores)),
        "1x2.away": float(np.triu(scores, 1).sum()),
        "btts.yes": float(scores[1:, 1:].sum()),
    }
    result["btts.no"] = 1.0 - result["btts.yes"]
    for line in (1.5, 2.5, 3.5, 4.5):
        over = sum(scores[h, a] for h in range(13) for a in range(13) if h + a > line)
        result[f"totals.{line}.over"] = float(over)
        result[f"totals.{line}.under"] = 1.0 - float(over)
    for line in (1.5, 2.5):
        threshold = int(line + 0.5)
        home_cover = sum(scores[h, a] for h in range(13) for a in range(13) if h - a >= threshold)
        away_cover = sum(scores[h, a] for h in range(13) for a in range(13) if a - h >= threshold)
        result[f"spread.home-{line}"] = float(home_cover)
        result[f"spread.away-{line}"] = float(away_cover)
    for side, rate in (("home", home_lambda), ("away", away_lambda)):
        for line in (0.5, 1.5, 2.5):
            threshold = int(line + 0.5)
            under = sum(math.exp(-rate) * rate**i / math.factorial(i) for i in range(threshold))
            result[f"team_total.{side}.{line}.under"] = under
            result[f"team_total.{side}.{line}.over"] = 1.0 - under
    return result


def normalize_odds(odds: dict[str, float]) -> dict[str, float]:
    raw = {key: 1.0 / value for key, value in odds.items()}
    total = sum(raw.values())
    return {key: value / total for key, value in raw.items()}


def fit_external(evidence: dict) -> tuple[tuple[float, float], dict]:
    book = normalize_odds(evidence["sportsbook_1x2"]["decimal_odds"])
    opta = evidence["opta_1x2"]
    # Opta and sportsbook prices share substantial information. Use the
    # directly tradable sportsbook benchmark; retain Opta only as sensitivity.
    target_1x2 = dict(book)
    total_fair = normalize_odds(evidence["sportsbook_total_2_5"]["decimal_odds"])
    btts_fair = normalize_odds(evidence["sportsbook_btts"]["decimal_odds"])

    def objective(log_rates: np.ndarray) -> float:
        rates = np.exp(log_rates)
        probs = score_probabilities(*rates)
        error = sum((probs[f"1x2.{key}"] - target_1x2[key]) ** 2 for key in target_1x2)
        error += 1.5 * (probs["totals.2.5.over"] - total_fair["over"]) ** 2
        return error

    fit = minimize(objective, np.log([1.3, 1.1]), method="L-BFGS-B", bounds=[(-3, 2), (-3, 2)])
    rates = tuple(float(x) for x in np.exp(fit.x))
    return rates, {
        "sportsbook_1x2_devig": book,
        "opta_1x2": {key: opta[key] for key in ("home", "draw", "away")},
        "opta_max_abs_gap_vs_sportsbook": max(abs(opta[key] - book[key]) for key in book),
        "cluster_1x2_target": target_1x2,
        "sportsbook_total_2_5_devig": total_fair,
        "sportsbook_btts_devig": btts_fair,
        "fit_objective": float(fit.fun),
    }


def model_value(model: dict, key: str) -> tuple[float, float, float]:
    markets = model["markets"]
    intervals = model["uncertainty"]["market_probability_intervals"]
    if key.startswith("1x2.") or key.startswith("btts.") or key.startswith("totals.") or key.startswith("team_total."):
        if key.startswith("team_total."):
            side, remainder = key.removeprefix("team_total.").split(".", 1)
            line, outcome = remainder.rsplit(".", 1)
            central = markets["team_totals"][side][line][outcome]
            interval_key = f"team_totals.{side}.{line}.{outcome}"
        else:
            parts = key.split(".")
            if parts[0] == "1x2":
                central = markets["1x2"][parts[1]]
            elif parts[0] == "btts":
                central = markets["btts"][parts[1]]
            else:
                line, outcome = key.removeprefix("totals.").rsplit(".", 1)
                central = markets["totals"][line][outcome]
            interval_key = key
        bounds = intervals[interval_key]
        return float(central), float(bounds["p10"]), float(bounds["p90"])
    if key.startswith("spread."):
        side, line_text = key.removeprefix("spread.").split("-", 1)
        line = float(line_text)
        if side == "home":
            model_key = f"home_-{line}"
            interval_key = f"spreads_home_handicap.home_-{line}.win"
            central = markets["spreads_home_handicap"][model_key]["win"]
            bounds = intervals[interval_key]
            return float(central), float(bounds["p10"]), float(bounds["p90"])
        model_key = f"home_+{line}"
        central = markets["spreads_home_handicap"][model_key]["loss"]
        win_bounds = intervals[f"spreads_home_handicap.home_+{line}.win"]
        return float(central), 1.0 - float(win_bounds["p90"]), 1.0 - float(win_bounds["p10"])
    raise KeyError(key)


def outcome_key(match: dict, market: dict, outcome: str) -> str:
    home, away = match["home"], match["away"]
    market_type = market["market_type"]
    if market_type == "match_1x2":
        question = market["question"]
        if "end in a draw" in question:
            base = "1x2.draw"
        elif home in question:
            base = "1x2.home"
        else:
            base = "1x2.away"
        return base if outcome == "Yes" else f"complement:{base}"
    if market_type == "totals":
        return f"totals.{market['line']}.{outcome.lower()}"
    if market_type == "both_teams_to_score":
        return f"btts.{outcome.lower()}"
    if market_type == "soccer_team_totals":
        side = "home" if f": {home} O/U" in market["question"] else "away"
        return f"team_total.{side}.{market['line']}.{outcome.lower()}"
    if market_type == "spreads":
        favorite = home if market["question"].startswith(f"Spread: {home}") else away
        side = "home" if favorite == home else "away"
        base = f"spread.{side}-{abs(market['line'])}"
        return base if outcome == favorite else f"complement:{base}"
    raise KeyError(market_type)


def resolve_probability(model: dict, external: dict, key: str) -> tuple[float, float, float, float]:
    complement = key.startswith("complement:")
    base = key.removeprefix("complement:")
    central, low, high = model_value(model, base)
    ext = external[base]
    if complement:
        central, low, high, ext = 1 - central, 1 - high, 1 - low, 1 - ext
    return central, low, high, ext


def round_down(value: float, tick: float) -> float:
    return max(0.0, math.floor((value + 1e-12) / tick) * tick)


def ask_vwap_for_notional(asks: list[dict], notional_budget: float) -> tuple[float, float] | None:
    remaining_notional = notional_budget
    notional = 0.0
    shares = 0.0
    for level in sorted(asks, key=lambda row: float(row["price"])):
        price = float(level["price"])
        filled = min(float(level["size"]), remaining_notional / price)
        level_notional = filled * price
        notional += level_notional
        shares += filled
        remaining_notional -= level_notional
        if remaining_notional <= 1e-9:
            return notional / shares, shares
    return None


def main() -> None:
    model_data = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    evidence_data = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    market_data = json.loads(MARKET_PATH.read_text(encoding="utf-8"))
    models = {match["id"]: match for match in model_data["matches"]}
    evidence = {match["id"]: match for match in evidence_data["matches"]}
    market_match_map = {
        "Brazil vs. Norway": "brazil_norway_2026-07-05",
        "Mexico vs. England": "mexico_england_2026-07-05",
    }
    output = {
        "as_of_beijing": market_data["as_of_beijing"],
        "bankroll_usdc": BANKROLL,
        "method": {
            "p_center": "p_external + reliability * (p_independent - p_external)",
            "p_trade": "p_external + reliability * (p10_independent - p_external) - external_uncertainty_buffer",
            "maker_rebate_assumption": 0.0,
            "kelly_fraction": 0.05,
            "confidence_multiplier": 0.75,
        },
        "matches": [],
    }
    for market_match in market_data["matches"]:
        match_id = market_match_map[market_match["title"]]
        model = models[match_id]
        info = evidence[match_id]
        external_rates, external_fit = fit_external(info)
        external_probs = score_probabilities(*external_rates)
        # Prefer direct de-vig evidence where it exists; lambda projection is
        # reserved for lines without a directly observed external benchmark.
        for side in ("home", "draw", "away"):
            external_probs[f"1x2.{side}"] = external_fit["cluster_1x2_target"][side]
        external_probs["totals.2.5.over"] = external_fit["sportsbook_total_2_5_devig"]["over"]
        external_probs["totals.2.5.under"] = external_fit["sportsbook_total_2_5_devig"]["under"]
        external_probs["btts.yes"] = external_fit["sportsbook_btts_devig"]["yes"]
        external_probs["btts.no"] = external_fit["sportsbook_btts_devig"]["no"]
        # The combined score model and stress percentiles lack walk-forward
        # coverage validation, so this run uses the documented weak-evidence bar.
        required_edge = 0.05
        evaluations = []
        for market in market_match["markets"]:
            for outcome in market["outcomes"]:
                key = outcome_key(model, market, outcome)
                independent, independent_low, independent_high, external = resolve_probability(
                    model, external_probs, key
                )
                family = "1x2" if key.removeprefix("complement:").startswith("1x2.") else "derived_score_markets"
                reliability = info["reliability"][family]
                buffer = info["external_uncertainty_buffer"][family]
                center = external + reliability * (independent - external)
                trade = external + reliability * (independent_low - external) - buffer
                trade = min(max(trade, 0.001), center)
                book = market["books"][outcome]
                ask = book["best_ask"]
                bid = book["best_bid"]
                if ask is None or bid is None:
                    continue
                fee_rate = float(market["fee_schedule"].get("rate") or 0)
                max_stake = BANKROLL * 0.0075
                depth_fill = ask_vwap_for_notional(book["asks"], max_stake)
                if depth_fill is None:
                    continue
                vwap, planned_shares = depth_fill
                fee = fee_rate * vwap * (1 - vwap)
                effective_cost = vwap + fee
                taker_edge = trade - effective_cost
                tick = float(book["tick_size"])
                maker_max = round_down(trade - required_edge, tick)
                maker_gap_to_bid = bid - maker_max
                status = "SKIP"
                execution_price = None
                if taker_edge >= required_edge:
                    status, execution_price = "TAKER_ACTIONABLE", vwap
                elif maker_max > 0 and maker_max < ask and maker_gap_to_bid <= 0.02 + 1e-12:
                    status, execution_price = "POST_ONLY_CONDITIONAL", maker_max
                stake = 0.0
                full_kelly = 0.0
                kelly_cost = effective_cost if status == "TAKER_ACTIONABLE" else execution_price
                if kelly_cost is not None and trade > kelly_cost:
                    full_kelly = (trade - kelly_cost) / (1 - kelly_cost)
                    stake = BANKROLL * min(0.0075, full_kelly * 0.05 * 0.75)
                evaluations.append(
                    {
                        "market_slug": market["slug"],
                        "question": market["question"],
                        "outcome": outcome,
                        "probability_key": key,
                        "p_independent": independent,
                        "p10_independent": independent_low,
                        "p90_independent": independent_high,
                        "p_external_cluster": external,
                        "reliability": reliability,
                        "uncertainty_buffer": buffer,
                        "p_center": center,
                        "p_trade": trade,
                        "best_bid": bid,
                    "best_ask": ask,
                    "planned_taker_shares_for_depth_check": planned_shares,
                    "planned_taker_vwap": vwap,
                        "fee_rate": fee_rate,
                        "fee_per_share_at_ask": fee,
                        "effective_taker_cost": effective_cost,
                        "taker_robust_edge": taker_edge,
                        "required_edge": required_edge,
                        "maker_max_price": maker_max,
                        "maker_gap_to_current_bid": maker_gap_to_bid,
                        "status": status,
                        "execution_price": execution_price,
                        "full_kelly_at_execution_price": full_kelly,
                        "stake_usdc": round(stake, 2),
                    }
                )
        evaluations.sort(key=lambda row: row["taker_robust_edge"], reverse=True)
        selected = [row for row in evaluations if row["status"] != "SKIP"]
        # One position per match: keep only the strongest robust edge.
        if len(selected) > 1:
            keep = max(selected, key=lambda row: row["taker_robust_edge"])
            for row in selected:
                if row is not keep:
                    row["status"] = "SKIP_CORRELATED_WITH_STRONGER_SAME_MATCH_CANDIDATE"
                    row["execution_price"] = None
                    row["stake_usdc"] = 0.0
            selected = [keep]
        output["matches"].append(
            {
                "id": match_id,
                "title": market_match["title"],
                "kickoff_utc": market_match["kickoff_utc"],
                "external_lambdas": {"home": external_rates[0], "away": external_rates[1]},
                "external_fit": external_fit,
                "required_edge": required_edge,
                "selected": selected,
                "evaluations": evaluations,
            }
        )
    output["selected_positions"] = [row for match in output["matches"] for row in match["selected"]]
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}; selected={len(output['selected_positions'])}")
    for match in output["matches"]:
        print("\n", match["title"])
        for row in match["evaluations"][:8]:
            print(
                f"{row['status']:<24} {row['outcome']:<7} {row['market_slug']:<55} "
                f"p_trade={row['p_trade']:.3f} ask={row['best_ask']:.3f} edge={row['taker_robust_edge']:.3f} "
                f"maker_max={row['maker_max_price']:.3f}"
            )


if __name__ == "__main__":
    main()
