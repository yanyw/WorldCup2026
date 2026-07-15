#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "data" / "model_results_0715.json"
EVIDENCE_PATH = ROOT / "data" / "external_evidence_0715.json"
MARKET_PATH = ROOT / "data" / "polymarket_snapshot_0715.json"
POLICY_PATH = ROOT.parent / "workflow_policy.json"
OUTPUT_PATH = ROOT / "data" / "candidate_evaluation_0715.json"
BANKROLL = 1000.0


def american_decimal(value: float) -> float:
    return 1.0 + value / 100.0 if value > 0 else 1.0 + 100.0 / abs(value)


def devig(american: dict) -> dict:
    raw = {key: 1.0 / american_decimal(float(value)) for key, value in american.items()}
    total = sum(raw.values())
    return {key: value / total for key, value in raw.items()}


def ask_vwap(asks: list[dict], budget: float) -> tuple[float, float] | None:
    remaining = budget
    notional = 0.0
    shares = 0.0
    for level in sorted(asks, key=lambda row: float(row["price"])):
        price = float(level["price"])
        fill = min(float(level["size"]), remaining / price)
        notional += fill * price
        shares += fill
        remaining -= fill * price
        if remaining <= 1e-9:
            return notional / shares, shares
    return None


def model_probability(match: dict, key: str) -> tuple[float, float, float]:
    complement = key.startswith("complement:")
    base_key = key.removeprefix("complement:")
    intervals = match["uncertainty"]["market_probability_intervals"]
    if base_key.startswith("1x2."):
        outcome = base_key.split(".")[1]
        center = float(match["markets"]["1x2"][outcome])
    elif base_key.startswith("totals.2.5."):
        outcome = base_key.rsplit(".", 1)[1]
        center = float(match["markets"]["totals"]["2.5"][outcome])
    else:
        raise KeyError(key)
    interval = intervals[base_key]
    low, high = float(interval["p10"]), float(interval["p90"])
    if complement:
        return 1.0 - center, 1.0 - high, 1.0 - low
    return center, low, high


def market_key(match: dict, market: dict, outcome: str) -> str | None:
    if market["market_type"] == "match_1x2":
        question = market["question"]
        if "end in a draw" in question:
            base = "1x2.draw"
        elif match["home"] in question:
            base = "1x2.home"
        else:
            base = "1x2.away"
        return base if outcome == "Yes" else "complement:" + base
    if market["market_type"] == "totals" and float(market["line"]) == 2.5:
        return f"totals.2.5.{outcome.lower()}"
    return None


def round_down(value: float, tick: float) -> float:
    return max(0.0, math.floor((value + 1e-12) / tick) * tick)


def main() -> None:
    models = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    snapshot = json.loads(MARKET_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    required_edge = float(policy["robust_edge_threshold"])
    if abs(required_edge - 0.015) > 1e-12:
        raise AssertionError("Persistent workflow policy must be 1.5pp")

    model_by_id = {item["id"]: item for item in models["matches"]}
    evidence_by_id = {item["id"]: item for item in evidence["matches"]}
    market_ids = {"fifwc-eng-arg-2026-07-15": "england_argentina_2026-07-15"}
    params = evidence["decision_parameters"]
    opta_weight = float(params["opta_weight_within_external_1x2"])
    internal_weight = float(params["internal_weight"])
    dispersion_coefficient = float(params["sportsbook_dispersion_coefficient"])
    disagreement_coefficient = float(params["model_disagreement_coefficient"])
    base_data_quality_penalty = float(params["data_quality_penalty"])
    minimum_uncertainty = float(params["minimum_uncertainty"])
    output_matches = []
    all_evaluations = []
    ineligible_markets = []

    for market_match in snapshot["matches"]:
        match_id = market_ids[market_match["event_slug"]]
        model_match = model_by_id[match_id]
        info = evidence_by_id[match_id]
        betmgm_1x2 = devig(info["sportsbook_1x2"]["american_odds"])
        betmgm_total = devig(info["sportsbook_total_2_5"]["american_odds"])
        oddschecker_1x2 = devig(info["oddschecker_cross_check"]["american_odds_1x2"])
        oddschecker_total = devig(info["oddschecker_cross_check"]["american_odds_total_2_5"])
        sportsbook_consensus = {
            **{f"1x2.{key}": (betmgm_1x2[key] + oddschecker_1x2[key]) / 2.0 for key in betmgm_1x2},
            **{f"totals.2.5.{key}": (betmgm_total[key] + oddschecker_total[key]) / 2.0 for key in betmgm_total},
        }
        sportsbook_dispersion = {
            **{f"1x2.{key}": abs(betmgm_1x2[key] - oddschecker_1x2[key]) for key in betmgm_1x2},
            **{f"totals.2.5.{key}": abs(betmgm_total[key] - oddschecker_total[key]) for key in betmgm_total},
        }
        opta_1x2 = {key: float(value) for key, value in info["opta_1x2"].items() if key in {"home", "draw", "away"}}
        external_center = {
            **{
                f"1x2.{key}": (1.0 - opta_weight) * sportsbook_consensus[f"1x2.{key}"] + opta_weight * opta_1x2[key]
                for key in betmgm_1x2
            },
            **{f"totals.2.5.{key}": sportsbook_consensus[f"totals.2.5.{key}"] for key in betmgm_total},
        }
        match_identity = {"home": info["home"], "away": info["away"]}
        evaluations = []

        for market in market_match["markets"]:
            for outcome in market["outcomes"]:
                key = market_key(match_identity, market, outcome)
                if key is None:
                    if market["market_type"] == "totals":
                        reason = "SKIP_UNVALIDATED_ADJACENT_LINE_PROJECTION"
                    elif market["market_type"] == "spreads":
                        reason = "SKIP_NO_DIRECT_SPREAD_BENCHMARK"
                    elif market["market_type"] == "soccer_team_totals":
                        reason = "SKIP_NO_DIRECT_TEAM_TOTAL_BENCHMARK"
                    elif market["market_type"] == "both_teams_to_score":
                        reason = "SKIP_NO_DIRECT_BTTS_BENCHMARK"
                    else:
                        reason = "SKIP_EVIDENCE_GATE"
                    ineligible_markets.append(
                        {
                            "match_id": match_id,
                            "market_slug": market["slug"],
                            "question": market["question"],
                            "market_type": market["market_type"],
                            "outcome": outcome,
                            "status": reason,
                        }
                    )
                    continue
                internal, scenario_p10, scenario_p90 = model_probability(model_match, key)
                complement = key.startswith("complement:")
                base_key = key.removeprefix("complement:")
                if complement:
                    p_external = 1.0 - external_center[base_key]
                    p_sportsbook = 1.0 - sportsbook_consensus[base_key]
                else:
                    p_external = external_center[base_key]
                    p_sportsbook = sportsbook_consensus[base_key]
                p_center = p_external + internal_weight * (internal - p_external)
                source_dispersion = sportsbook_dispersion[base_key]
                model_disagreement = abs(internal - p_external)
                family = "1x2" if base_key.startswith("1x2") else "totals.2.5"
                data_quality_penalty = base_data_quality_penalty + float(
                    info.get("additional_data_quality_penalty", {}).get(family, 0.0)
                )
                uncertainty = max(
                    minimum_uncertainty,
                    dispersion_coefficient * source_dispersion
                    + disagreement_coefficient * model_disagreement
                    + data_quality_penalty,
                )
                p_trade = max(0.001, p_center - uncertainty)

                order_book = market["books"][outcome]
                bid = order_book["best_bid"]
                ask = order_book["best_ask"]
                if bid is None or ask is None:
                    continue
                fill = ask_vwap(order_book["asks"], BANKROLL * 0.0075)
                if fill is None:
                    continue
                vwap, shares = fill
                fee_rate = float(market["fee_schedule"].get("rate") or 0.0)
                fee_per_share = fee_rate * vwap * (1.0 - vwap)
                taker_cost = vwap + fee_per_share
                taker_edge = p_trade - taker_cost
                tick = float(order_book["tick_size"])
                maker_max = round_down(p_trade - required_edge, tick)
                maker_price = min(maker_max, round_down(ask - tick, tick))
                maker_edge = p_trade - maker_price
                maker_gap_to_bid = bid - maker_price
                status = "SKIP_EDGE"
                execution_price = None
                execution_mode = "no_bet"
                if taker_edge >= required_edge:
                    status = "TAKER_ACTIONABLE"
                    execution_price = vwap
                    execution_mode = "taker"
                elif maker_price >= bid:
                    status = "POST_ONLY_ACTIONABLE"
                    execution_price = maker_price
                    execution_mode = "post_only"

                full_kelly = 0.0
                stake = 0.0
                execution_cost = None
                if execution_price is not None:
                    execution_cost = taker_cost if execution_mode == "taker" else execution_price
                if execution_cost is not None and p_trade > execution_cost:
                    full_kelly = (p_trade - execution_cost) / (1.0 - execution_cost)
                    stake = BANKROLL * min(0.0075, full_kelly * 0.05 * 0.75)

                row = {
                    "match_id": match_id,
                    "event_cluster": match_id + "_90m_score",
                    "market_slug": market["slug"],
                    "question": market["question"],
                    "outcome": outcome,
                    "probability_key": key,
                    "benchmark_quality": "DIRECT_LINE",
                    "p_internal": internal,
                    "scenario_p10": scenario_p10,
                    "scenario_p90": scenario_p90,
                    "scenario_p10_calibrated": False,
                    "p_sportsbook_consensus": p_sportsbook,
                    "p_external": p_external,
                    "opta_weight_within_external": opta_weight if base_key.startswith("1x2") else 0.0,
                    "internal_weight": internal_weight,
                    "p_center": p_center,
                    "sportsbook_source_dispersion": source_dispersion,
                    "model_disagreement": model_disagreement,
                    "dispersion_penalty": dispersion_coefficient * source_dispersion,
                    "model_disagreement_penalty": disagreement_coefficient * model_disagreement,
                    "data_quality_penalty": data_quality_penalty,
                    "minimum_uncertainty": minimum_uncertainty,
                    "decision_uncertainty": uncertainty,
                    "p_trade": p_trade,
                    "best_bid": bid,
                    "best_ask": ask,
                    "planned_taker_vwap": vwap,
                    "planned_shares": shares,
                    "fee_rate": fee_rate,
                    "fee_per_share": fee_per_share,
                    "effective_taker_cost": taker_cost,
                    "taker_robust_edge": taker_edge,
                    "required_edge": required_edge,
                    "maker_max_price": maker_max,
                    "maker_post_price": maker_price,
                    "maker_robust_edge": maker_edge,
                    "maker_gap_to_current_bid": maker_gap_to_bid,
                    "status": status,
                    "execution_mode": execution_mode,
                    "execution_price": execution_price,
                    "execution_cost_for_kelly": execution_cost,
                    "full_kelly": full_kelly,
                    "stake_usdc": stake,
                }
                evaluations.append(row)
                all_evaluations.append(row)

        evaluations.sort(key=lambda row: row["taker_robust_edge"], reverse=True)
        output_matches.append(
            {
                "id": match_id,
                "title": market_match["title"],
                "kickoff_utc": market_match["kickoff_utc"],
                "betmgm_1x2_devig": betmgm_1x2,
                "oddschecker_1x2_devig": oddschecker_1x2,
                "sportsbook_consensus_1x2": {key: sportsbook_consensus[f"1x2.{key}"] for key in betmgm_1x2},
                "p_external_center_1x2": {key: external_center[f"1x2.{key}"] for key in betmgm_1x2},
                "betmgm_total_2_5_devig": betmgm_total,
                "oddschecker_total_2_5_devig": oddschecker_total,
                "sportsbook_consensus_total_2_5": {key: sportsbook_consensus[f"totals.2.5.{key}"] for key in betmgm_total},
                "p_external_center_total_2_5": {key: external_center[f"totals.2.5.{key}"] for key in betmgm_total},
                "opta_1x2_same_cluster": info["opta_1x2"],
                "evaluations": evaluations,
            }
        )

    selected = [row for row in all_evaluations if row["status"] in {"TAKER_ACTIONABLE", "POST_ONLY_ACTIONABLE"}]
    output = {
        "as_of_beijing": snapshot["as_of_beijing"],
        "policy_version": policy["policy_version"],
        "robust_edge_threshold": required_edge,
        "bankroll_usdc": BANKROLL,
        "p_trade_method": params["p_trade_rule"],
        "evidence_gate": "Only direct 1X2 and direct O/U 2.5 are eligible. Other scanned markets are excluded until a direct benchmark or validated projection model exists.",
        "matches": output_matches,
        "selected_positions": selected,
        "scanned_markets": sum(len(match["markets"]) for match in snapshot["matches"]),
        "eligible_outcomes": len(all_evaluations),
        "ineligible_outcomes": ineligible_markets,
    }
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}; selected={len(selected)}")
    for row in sorted(all_evaluations, key=lambda item: item["taker_robust_edge"], reverse=True):
        print(row["status"], row["match_id"], row["outcome"], row["probability_key"], f"trade={row['p_trade']:.4f}", f"ask={row['best_ask']:.4f}", f"edge={row['taker_robust_edge']:.4f}", f"maker={row['maker_max_price']:.4f}")


if __name__ == "__main__":
    main()
