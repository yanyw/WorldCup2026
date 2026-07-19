#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "data" / "model_results_0719.json"
EVIDENCE_PATH = ROOT / "data" / "external_evidence_0719.json"
MARKET_PATH = ROOT / "data" / "polymarket_snapshot_0719.json"
POLICY_PATH = ROOT.parent / "workflow_policy.json"
OUTPUT_PATH = ROOT / "data" / "candidate_evaluation_0719.json"
BANKROLL = 1000.0


def american_decimal(value: float) -> float:
    return 1.0 + value / 100.0 if value > 0 else 1.0 + 100.0 / abs(value)


def devig(american: dict) -> dict:
    raw = {key: 1.0 / american_decimal(float(value)) for key, value in american.items()}
    total = sum(raw.values())
    return {key: value / total for key, value in raw.items()}


def consensus(source_probabilities: list[dict]) -> tuple[dict, dict]:
    if not source_probabilities:
        raise ValueError("At least one complete sportsbook source is required")
    keys = source_probabilities[0].keys()
    center = {
        key: sum(source[key] for source in source_probabilities) / len(source_probabilities)
        for key in keys
    }
    dispersion = {
        key: max(source[key] for source in source_probabilities)
        - min(source[key] for source in source_probabilities)
        for key in keys
    }
    return center, dispersion


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


def taker_max_single_level_price(
    p_trade: float,
    required_edge: float,
    fee_rate: float,
    fee_exponent: float,
    tick: float,
) -> float:
    target_cost = p_trade - required_edge
    if target_cost <= 0.0:
        return 0.0
    low, high = 0.0, min(1.0, target_cost)
    for _ in range(80):
        mid = (low + high) / 2.0
        cost = mid + fee_rate * (mid * (1.0 - mid)) ** fee_exponent
        if cost <= target_cost:
            low = mid
        else:
            high = mid
    return round_down(low, tick)


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
    market_ids = {
        "fifwc-esp-arg-2026-07-19": "spain_argentina_2026-07-19",
    }
    params = evidence["decision_parameters"]
    opta_weight = float(params["opta_weight_within_external_1x2"])
    internal_weight = float(params["internal_weight"])
    dispersion_coefficient = float(params["sportsbook_dispersion_coefficient"])
    base_data_quality_penalty = float(params["data_quality_penalty"])
    minimum_uncertainty = float(params["minimum_uncertainty"])
    output_matches = []
    all_evaluations = []
    ineligible_markets = []

    for market_match in snapshot["matches"]:
        match_id = market_ids[market_match["event_slug"]]
        model_match = model_by_id[match_id]
        info = evidence_by_id[match_id]
        sportsbook_1x2_sources = [
            devig(source["american_odds_1x2"])
            for source in info["sportsbook_sources"]
            if "american_odds_1x2" in source
        ]
        sportsbook_total_sources = [
            devig(source["american_odds_total_2_5"])
            for source in info["sportsbook_sources"]
            if "american_odds_total_2_5" in source
        ]
        consensus_1x2, dispersion_1x2 = consensus(sportsbook_1x2_sources)
        consensus_total, dispersion_total = consensus(sportsbook_total_sources)
        sportsbook_consensus = {
            **{f"1x2.{key}": value for key, value in consensus_1x2.items()},
            **{f"totals.2.5.{key}": value for key, value in consensus_total.items()},
        }
        sportsbook_dispersion = {
            **{f"1x2.{key}": value for key, value in dispersion_1x2.items()},
            **{f"totals.2.5.{key}": value for key, value in dispersion_total.items()},
        }
        opta_1x2 = {key: float(value) for key, value in info["opta_1x2"].items() if key in {"home", "draw", "away"}}
        external_center = {
            **{
                f"1x2.{key}": (1.0 - opta_weight) * sportsbook_consensus[f"1x2.{key}"] + opta_weight * opta_1x2[key]
                for key in consensus_1x2
            },
            **{f"totals.2.5.{key}": sportsbook_consensus[f"totals.2.5.{key}"] for key in consensus_total},
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
                source_dispersion = sportsbook_dispersion[base_key]
                model_disagreement = abs(internal - p_external)
                family = "1x2" if base_key.startswith("1x2") else "totals.2.5"
                stage_applicability = info.get("stage_applicability", {})
                family_internal_weight = float(
                    stage_applicability.get("internal_weight_override", {}).get(
                        family,
                        internal_weight,
                    )
                )
                p_center = p_external + family_internal_weight * (internal - p_external)
                data_quality_penalty = base_data_quality_penalty + float(
                    info.get("additional_data_quality_penalty", {}).get(family, 0.0)
                )
                uncertainty = max(
                    minimum_uncertainty,
                    dispersion_coefficient * source_dispersion
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
                fee_exponent = float(market["fee_schedule"].get("exponent") or 1.0)
                fee_per_share = fee_rate * (vwap * (1.0 - vwap)) ** fee_exponent
                taker_cost = vwap + fee_per_share
                taker_edge = p_trade - taker_cost
                tick = float(order_book["tick_size"])
                maker_max = round_down(p_trade - required_edge, tick)
                taker_max_price = taker_max_single_level_price(
                    p_trade,
                    required_edge,
                    fee_rate,
                    fee_exponent,
                    tick,
                )
                maker_price = min(maker_max, round_down(ask - tick, tick))
                maker_edge = p_trade - maker_price
                maker_gap_to_bid = bid - maker_price
                status = "SKIP_EDGE"
                maker_order_class = "CONDITIONAL_LIMIT_BELOW_BID"
                execution_price = None
                execution_mode = "no_bet"
                if taker_edge >= required_edge:
                    status = "TAKER_ACTIONABLE"
                    maker_order_class = None
                    execution_price = vwap
                    execution_mode = "taker"
                elif maker_price >= bid:
                    status = "POST_ONLY_ACTIONABLE"
                    maker_order_class = "TOP_OF_BOOK_ACTIONABLE"
                    execution_price = maker_price
                    execution_mode = "post_only"
                elif maker_price > 0:
                    status = "CONDITIONAL_LIMIT_BELOW_BID"
                evidence_gate_reason = info.get("evidence_gate_blocked_families", {}).get(family)
                if evidence_gate_reason:
                    status = "SKIP_EVIDENCE_GATE_STAGE_OOD"
                    maker_order_class = None
                    execution_price = None
                    execution_mode = "no_bet"

                full_kelly = 0.0
                stake = 0.0
                execution_cost = None
                if execution_price is not None:
                    execution_cost = taker_cost if execution_mode == "taker" else execution_price
                if execution_cost is not None and p_trade > execution_cost:
                    full_kelly = (p_trade - execution_cost) / (1.0 - execution_cost)
                    stake = BANKROLL * min(0.0075, full_kelly * 0.05 * 0.75)
                executable = evidence_gate_reason is None
                if not executable:
                    maker_max_output = None
                    maker_post_output = None
                    maker_edge_output = None
                    maker_gap_output = None
                    full_kelly_output = None
                else:
                    maker_max_output = maker_max
                    maker_post_output = maker_price
                    maker_edge_output = maker_edge
                    maker_gap_output = maker_gap_to_bid
                    full_kelly_output = full_kelly

                row = {
                    "match_id": match_id,
                    "event_cluster": match_id + "_90m_score",
                    "market_slug": market["slug"],
                    "question": market["question"],
                    "outcome": outcome,
                    "probability_key": key,
                    "benchmark_quality": (
                        "DIRECT_LINE_EXTERNAL_ONLY_PARTIAL_OOD"
                        if family_internal_weight == 0.0
                        else "DIRECT_LINE"
                    ),
                    "stage_applicability": stage_applicability.get("classification", "IN_DOMAIN"),
                    "internal_model_role": (
                        "diagnostic_only"
                        if family_internal_weight == 0.0
                        else "directional_fusion"
                    ),
                    "p_internal": internal,
                    "scenario_p10": scenario_p10,
                    "scenario_p90": scenario_p90,
                    "scenario_p10_calibrated": False,
                    "p_sportsbook_consensus": p_sportsbook,
                    "p_external": p_external,
                    "opta_weight_within_external": opta_weight if base_key.startswith("1x2") else 0.0,
                    "internal_weight": family_internal_weight,
                    "p_center": p_center,
                    "sportsbook_source_dispersion": source_dispersion,
                    "model_disagreement": model_disagreement,
                    "dispersion_penalty": dispersion_coefficient * source_dispersion,
                    "data_quality_penalty": data_quality_penalty,
                    "minimum_uncertainty": minimum_uncertainty,
                    "decision_uncertainty": uncertainty,
                    "p_trade": p_trade,
                    "best_bid": bid,
                    "best_ask": ask,
                    "planned_taker_vwap": vwap,
                    "planned_shares": shares,
                    "fee_rate": fee_rate,
                    "fee_exponent": fee_exponent,
                    "fee_per_share": fee_per_share,
                    "effective_taker_cost": taker_cost,
                    "taker_robust_edge": taker_edge,
                    "required_edge": required_edge,
                    "taker_max_single_level_price": taker_max_price,
                    "maker_max_price": maker_max_output,
                    "maker_post_price": maker_post_output,
                    "maker_robust_edge": maker_edge_output,
                    "maker_gap_to_current_bid": maker_gap_output,
                    "maker_order_class": maker_order_class,
                    "status": status,
                    "evidence_gate_reason": evidence_gate_reason,
                    "executable": executable,
                    "evidence_eligible": executable,
                    "internal_model_diagnostic_only": family_internal_weight == 0.0,
                    "outcome_execution_diagnostic_only": not executable,
                    "execution_mode": execution_mode,
                    "execution_price": execution_price,
                    "execution_cost_for_kelly": execution_cost,
                    "full_kelly": full_kelly_output,
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
                "sportsbook_1x2_sources_devig": sportsbook_1x2_sources,
                "sportsbook_total_2_5_sources_devig": sportsbook_total_sources,
                "sportsbook_consensus_1x2": consensus_1x2,
                "p_external_center_1x2": {key: external_center[f"1x2.{key}"] for key in consensus_1x2},
                "sportsbook_consensus_total_2_5": consensus_total,
                "p_external_center_total_2_5": {key: external_center[f"totals.2.5.{key}"] for key in consensus_total},
                "opta_1x2_same_cluster": info["opta_1x2"],
                "stage_applicability": info.get("stage_applicability", {}),
                "evaluations": evaluations,
            }
        )

    selected = [row for row in all_evaluations if row["status"] in {"TAKER_ACTIONABLE", "POST_ONLY_ACTIONABLE"}]
    conditional = [
        row for row in all_evaluations
        if row["status"] == "CONDITIONAL_LIMIT_BELOW_BID"
    ]
    output = {
        "as_of_beijing": snapshot["as_of_beijing"],
        "policy_version": policy["policy_version"],
        "robust_edge_threshold": required_edge,
        "bankroll_usdc": BANKROLL,
        "p_trade_method": params["p_trade_rule"],
        "evidence_gate": "Only direct 1X2 and direct O/U 2.5 are eligible. Other scanned markets are excluded until a direct benchmark or validated projection model exists.",
        "matches": output_matches,
        "selected_positions": selected,
        "conditional_limit_positions": conditional,
        "scanned_markets": sum(len(match["markets"]) for match in snapshot["matches"]),
        "evaluated_outcomes": len(all_evaluations),
        "executable_eligible_outcomes": sum(row["executable"] for row in all_evaluations),
        "stage_ood_outcomes": sum(
            row["stage_applicability"] != "IN_DOMAIN"
            for row in all_evaluations
        ),
        "partial_ood_eligible_outcomes": sum(
            row["stage_applicability"].startswith("PARTIAL_OOD")
            and row["evidence_eligible"]
            for row in all_evaluations
        ),
        "hard_ood_blocked_outcomes": sum(
            row["stage_applicability"].startswith("HARD_OOD")
            and not row["evidence_eligible"]
            for row in all_evaluations
        ),
        "non_stage_evidence_gate_blocked_outcomes": sum(
            not row["stage_applicability"].startswith("HARD_OOD")
            and not row["evidence_eligible"]
            for row in all_evaluations
        ),
        "other_ineligible_outcomes": ineligible_markets,
    }
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}; selected={len(selected)}")
    for row in sorted(all_evaluations, key=lambda item: item["taker_robust_edge"], reverse=True):
        maker = "N/A" if row["maker_max_price"] is None else f"{row['maker_max_price']:.4f}"
        print(row["status"], row["match_id"], row["outcome"], row["probability_key"], f"trade={row['p_trade']:.4f}", f"ask={row['best_ask']:.4f}", f"edge={row['taker_robust_edge']:.4f}", f"maker={maker}")


if __name__ == "__main__":
    main()
