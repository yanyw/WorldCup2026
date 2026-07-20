"""Reproducible Norway-England Polymarket probability model (90 minutes unless noted)."""
from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "raw" / "polymarket_snapshot_20260711_2033.csv"
OUTPUT = ROOT / "outputs" / "all_market_predictions.csv"

LAMBDA_NORWAY = 1.20
LAMBDA_ENGLAND = 1.75
# 40% is used for this match: the late-scoring knockout regime is consistent
# with the observed half-market no-goal prices (not the generic 45% prior).
FIRST_HALF_SHARE = 0.40
ENGLAND_SHARE_IF_90M_DRAW = 0.60
PENALTY_REACH_GIVEN_90M_DRAW = 0.55
MAX_GOALS = 16


def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def poisson_over(line: float, lam: float) -> float:
    threshold = int(math.floor(line)) + 1
    return 1.0 - sum(poisson_pmf(k, lam) for k in range(threshold))


def score_matrix(lam_n: float, lam_e: float):
    return [[poisson_pmf(n, lam_n) * poisson_pmf(e, lam_e)
             for e in range(MAX_GOALS + 1)] for n in range(MAX_GOALS + 1)]


M = score_matrix(LAMBDA_NORWAY, LAMBDA_ENGLAND)


def p_score(n: int, e: int) -> float:
    return M[n][e]


def p_result(which: str) -> float:
    if which == "Norway":
        return sum(M[n][e] for n in range(MAX_GOALS + 1) for e in range(MAX_GOALS + 1) if n > e)
    if which == "England":
        return sum(M[n][e] for n in range(MAX_GOALS + 1) for e in range(MAX_GOALS + 1) if e > n)
    return sum(M[k][k] for k in range(MAX_GOALS + 1))


def model_probability(group: str, contract: str) -> float:
    if group == "main_90m":
        return p_result("Norway" if contract.startswith("Norway") else "England" if contract.startswith("England") else "Draw")
    if group == "advance":
        return p_result("Norway") + (1 - ENGLAND_SHARE_IF_90M_DRAW) * p_result("Draw")
    if group == "totals":
        return poisson_over(float(contract.split()[-1]), LAMBDA_NORWAY + LAMBDA_ENGLAND)
    if group == "team_total":
        team, line = contract.split()[0], float(contract.split()[-1])
        return poisson_over(line, LAMBDA_NORWAY if team == "Norway" else LAMBDA_ENGLAND)
    if group == "half_total":
        share = FIRST_HALF_SHARE if contract.startswith("First") else 1 - FIRST_HALF_SHARE
        return poisson_over(float(contract.split()[-1]), (LAMBDA_NORWAY + LAMBDA_ENGLAND) * share)
    if group == "half_team":
        team, half, line = contract.split()[0], contract.split()[1], float(contract.split()[-1])
        share = FIRST_HALF_SHARE if half == "first" else 1 - FIRST_HALF_SHARE
        return poisson_over(line, (LAMBDA_NORWAY if team == "Norway" else LAMBDA_ENGLAND) * share)
    if group == "btts":
        if "first half" in contract:
            share = FIRST_HALF_SHARE
        elif "second half" in contract:
            share = 1 - FIRST_HALF_SHARE
        else:
            share = 1.0
        return (1 - math.exp(-LAMBDA_NORWAY * share)) * (1 - math.exp(-LAMBDA_ENGLAND * share))
    if group == "spread":
        team, handicap = contract.split()
        margin = int(abs(float(handicap)))
        if team == "England":
            return sum(M[n][e] for n in range(MAX_GOALS + 1) for e in range(MAX_GOALS + 1) if e - n >= margin + 1)
        return sum(M[n][e] for n in range(MAX_GOALS + 1) for e in range(MAX_GOALS + 1) if n - e >= margin + 1)
    if group == "extra_time":
        return p_result("Draw") if "extra time" in contract else p_result("Draw") * PENALTY_REACH_GIVEN_90M_DRAW
    if group == "exact_score":
        if contract == "Any other score":
            return 1 - sum(p_score(n, e) for n in range(4) for e in range(4))
        score = contract.replace("Norway ", "").replace(" England", "")
        n, e = map(int, score.split("-"))
        return p_score(n, e)
    raise ValueError((group, contract))


def uncertainty_band(group: str, contract: str) -> tuple[float, float]:
    vals = []
    global M, LAMBDA_NORWAY, LAMBDA_ENGLAND
    base_n, base_e, base_m = LAMBDA_NORWAY, LAMBDA_ENGLAND, M
    for dn, de in [(-0.15, -0.15), (-0.15, 0.15), (0.15, -0.15), (0.15, 0.15)]:
        LAMBDA_NORWAY, LAMBDA_ENGLAND = base_n + dn, base_e + de
        M = score_matrix(LAMBDA_NORWAY, LAMBDA_ENGLAND)
        vals.append(model_probability(group, contract))
    LAMBDA_NORWAY, LAMBDA_ENGLAND, M = base_n, base_e, base_m
    return min(vals), max(vals)


def main() -> None:
    rows = []
    with SNAPSHOT.open(encoding="utf-8", newline="") as f:
        raw_rows = list(csv.DictReader(f))
        exact_sum = sum(float(r["market_probability"]) for r in raw_rows if r["group"] == "exact_score")
        for row in raw_rows:
            market_p = float(row["market_probability"])
            normalized_p = market_p / exact_sum if row["group"] == "exact_score" else market_p
            model_p = model_probability(row["group"], row["contract"])
            low, high = uncertainty_band(row["group"], row["contract"])
            edge = model_p - market_p
            action = "YES候选" if edge >= 0.04 and model_p >= 0.08 else "NO候选" if edge <= -0.04 and market_p >= 0.08 else "观望"
            rows.append({**row, "market_probability_normalized": f"{normalized_p:.6f}",
                         "model_probability": f"{model_p:.6f}", "edge": f"{edge:.6f}",
                         "scenario_low": f"{low:.6f}", "scenario_high": f"{high:.6f}", "signal": action})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    chart_dir = ROOT / "outputs" / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    cell, left, top = 72, 105, 75
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="650" height="590" viewBox="0 0 650 590">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<text x="325" y="30" text-anchor="middle" font-family="Arial" font-size="20">Norway vs England: score probability (%)</text>']
    for n in range(6):
        for e in range(6):
            value = 100 * p_score(n, e); shade = int(245 - min(value / 12, 1) * 150)
            svg.append(f'<rect x="{left+e*cell}" y="{top+n*cell}" width="{cell}" height="{cell}" fill="rgb({shade},{shade+5},245)" stroke="white"/>')
            svg.append(f'<text x="{left+e*cell+cell/2}" y="{top+n*cell+cell/2+6}" text-anchor="middle" font-family="Arial" font-size="15">{value:.1f}</text>')
    for k in range(6):
        svg.append(f'<text x="{left+k*cell+cell/2}" y="{top-12}" text-anchor="middle" font-family="Arial" font-size="14">{k}</text>')
        svg.append(f'<text x="{left-18}" y="{top+k*cell+cell/2+5}" text-anchor="middle" font-family="Arial" font-size="14">{k}</text>')
    svg += ['<text x="321" y="545" text-anchor="middle" font-family="Arial" font-size="16">England goals</text>',
            '<text x="25" y="290" text-anchor="middle" font-family="Arial" font-size="16" transform="rotate(-90 25 290)">Norway goals</text>', '</svg>']
    (chart_dir / "score_probability_heatmap.svg").write_text("\n".join(svg), encoding="utf-8")
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        shown = np.array([[p_score(n, e) for e in range(6)] for n in range(6)]) * 100
        fig, ax = plt.subplots(figsize=(7.2, 6.2))
        im = ax.imshow(shown, cmap="Blues", vmin=0, vmax=12)
        ax.set_xticks(range(6), labels=range(6)); ax.set_yticks(range(6), labels=range(6))
        ax.set_xlabel("England goals"); ax.set_ylabel("Norway goals")
        ax.set_title("Norway vs England: 90-minute score probability (%)")
        for n in range(6):
            for e in range(6):
                ax.text(e, n, f"{shown[n, e]:.1f}", ha="center", va="center",
                        color="white" if shown[n, e] > 6 else "black", fontsize=9)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()
        chart = chart_dir / "score_probability_heatmap.png"
        chart.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(chart, dpi=180); plt.close(fig)
    except ImportError:
        pass
    print(f"wrote {len(rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
