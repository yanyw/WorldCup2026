"""
World Cup Walk-Forward Backtest
Strict no-look-ahead: model trained ONLY on data available BEFORE each match date.
Reuses Codex v2 model modules from the ai预测世界杯 project.
"""

import csv, json, math, sys
from collections import defaultdict
from datetime import date
from pathlib import Path
import numpy as np

# ── Paths ──
# Resolve repository paths from this file so clones and directory renames work.
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT / "src"))

from wc_model.historical import RidgePoisson, elo_probabilities, estimate_dc_rho, load_results
from wc_model.score import core_markets, dc_matrix
from wc_model.historical import adam_optimize

OUTDIR = PROJECT / "outputs" / "walkforward_output"
OUTDIR.mkdir(parents=True, exist_ok=True)

# ── Data loading ──
def get_wc_matches(rows):
    wc = [r for r in rows if r["tournament"] == "FIFA World Cup"]
    wc.sort(key=lambda r: r["date"])
    return wc

def rows_before(rows, cutoff):
    return [r for r in rows if r["date"] < cutoff]

# ── Calibrated Elo (recalibrates on all history before prediction) ──
class EloTracker:
    def __init__(self, start=1500.0):
        self.ratings = defaultdict(lambda: start)

    def update(self, home, away, hg, ag, neutral, tournament):
        rh = self.ratings[home]; ra = self.ratings[away]
        home_bonus = 65.0 if not neutral else 0.0
        diff = rh + home_bonus - ra
        exp_h = 1.0 / (1 + 10**(-diff / 400))
        actual = 1.0 if hg > ag else (0.5 if hg == ag else 0.0)
        margin = abs(hg - ag)
        mult = 1.0 if margin <= 1 else (1.5 if margin == 2 else (11 + margin) / 8)
        k = 40.0 if tournament == "FIFA World Cup" else (25.0 if "Qualifier" in tournament else 18.0)
        delta = k * mult * (actual - exp_h)
        self.ratings[home] = rh + delta
        self.ratings[away] = ra - delta

    def get(self, team):
        return self.ratings.get(team, 1500.0)

def calibrate_elo_1x2(ratings_dict, home, away, neutral, all_rows):
    """Fit multinomial logistic regression on all historical Elo diffs."""
    features, outcomes = [], []
    temp = defaultdict(lambda: 1500.0)
    for r in sorted(all_rows, key=lambda x: x["date"]):
        rh = temp[r["home"]]; ra = temp[r["away"]]
        hb = 65.0 if not r["neutral"] else 0.0
        diff = rh + hb - ra
        if r["date"] >= date(2000, 1, 1):
            features.append([1.0, diff / 400.0])
            outcomes.append(0 if r["hg"] > r["ag"] else (1 if r["hg"] == r["ag"] else 2))
        exp_h2 = 1/(1+10**(-diff/400))
        act = 1.0 if r["hg"] > r["ag"] else (0.5 if r["hg"] == r["ag"] else 0.0)
        margin = abs(r["hg"]-r["ag"])
        mult = 1.0 if margin <= 1 else (1.5 if margin == 2 else (11+margin)/8)
        k = 40.0 if r["tournament"] == "FIFA World Cup" else (25.0 if "Qualifier" in r["tournament"] else 18.0)
        delta = k*mult*(act-exp_h2)
        temp[r["home"]] = rh+delta; temp[r["away"]] = ra-delta

    if len(features) < 100:
        return {"home": 1/3, "draw": 1/3, "away": 1/3}

    X = np.asarray(features); y = np.asarray(outcomes); ridge_reg = 1.0
    def obj(flat):
        b = flat.reshape(3, 2); z = X @ b.T; z -= z.max(axis=1, keepdims=True)
        p = np.exp(z); p /= p.sum(axis=1, keepdims=True)
        loss = -np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1)).sum() + 0.5*ridge_reg*np.sum(b[:,1:]**2)
        one_hot = np.eye(3)[y]; grad = (p-one_hot).T @ X; grad[:,1:] += ridge_reg*b[:,1:]
        return float(loss), grad.ravel()
    fitted, _ = adam_optimize(obj, np.zeros(6), steps=100, lr=0.02)

    dr = ratings_dict.get(home,1500) + (0 if neutral else 65) - ratings_dict.get(away,1500)
    z = np.array([1.0, dr/400]) @ fitted.reshape(3,2).T; z -= z.max()
    p = np.exp(z); p /= p.sum()
    return {"home": float(p[0]), "draw": float(p[1]), "away": float(p[2])}

# ── Main backtest ──
def main():
    cfg = json.loads((PROJECT / "config/model_config.json").read_text(encoding="utf-8"))
    pcfg = cfg["poisson"]
    cutoff = date.fromisoformat(cfg["data"]["cutoff_exclusive"])
    start = date.fromisoformat(cfg["data"]["training_start"])

    all_rows = load_results(PROJECT / cfg["data"]["historical_results"], start, cutoff)
    wc_matches = get_wc_matches(all_rows)

    print("=" * 60)
    print("WORLD CUP WALK-FORWARD BACKTEST")
    print("Strict no-look-ahead enforcement")
    print("=" * 60)
    print("WC matches:", len(wc_matches))
    print("Date range:", wc_matches[0]["date"], "to", wc_matches[-1]["date"])

    # Group by tournament year
    all_years = sorted(set(m["date"].year for m in wc_matches))
    print("Years:", all_years)

    results = []
    elo_tracker = EloTracker()
    p1_ready = False
    poisson_model = None
    rho = 0.0

    for wc_year in all_years:
        year_matches = [m for m in wc_matches if m["date"].year == wc_year]
        first_date = year_matches[0]["date"]
        print("\n" + "=" * 60)
        print("WC " + str(wc_year) + ": " + str(len(year_matches)) + " matches, first=" + str(first_date))

        # Train on all data strictly before first match
        train_rows = [r for r in all_rows if r["date"] < first_date]
        print("  Train: " + str(len(train_rows)) + " rows")

        if len(train_rows) >= 200:
            try:
                m = RidgePoisson(pcfg["half_life_days"], pcfg["ridge"], pcfg)
                m.fit(train_rows, first_date)
                lh_all, la_all = m.lambdas_for_rows(train_rows)
                rho = estimate_dc_rho(train_rows, lh_all, la_all, first_date, pcfg["half_life_days"])
                poisson_model = m
                p1_ready = True
                print("  Poisson OK: " + str(m.fit_info["teams"]) + " teams, rho=" + str(round(rho, 4)))
            except Exception as e:
                print("  Poisson FAIL: " + str(e))
                p1_ready = False
        else:
            print("  Poisson SKIP: only " + str(len(train_rows)) + " rows")
            p1_ready = False

        # Walk forward
        for match in year_matches:
            md = match["date"]
            home = match["home"]; away = match["away"]; neutral = match["neutral"]
            hg = match["hg"]; ag = match["ag"]

            hist_before = [r for r in all_rows if r["date"] < md]

            # P1: Poisson
            p1_pred = None
            if p1_ready:
                try:
                    lh, la = poisson_model.predict(home, away, neutral)
                    mat = dc_matrix(lh, la, rho, pcfg["max_goals"])
                    mk = core_markets(mat)
                    p1_pred = {"home": mk["home"], "draw": mk["draw"], "away": mk["away"],
                               "over2.5": mk["over2.5"], "btts": mk["btts"]}
                except KeyError:
                    pass

            # P2: Elo
            elo_pred = calibrate_elo_1x2(elo_tracker.ratings, home, away, neutral, hist_before)

            # Ensemble (75% P1, 25% Elo)
            if p1_pred is not None:
                ph = 0.75 * p1_pred["home"] + 0.25 * elo_pred["home"]
                pd = 0.75 * p1_pred["draw"] + 0.25 * elo_pred["draw"]
                pa = 0.75 * p1_pred["away"] + 0.25 * elo_pred["away"]
                po25 = p1_pred["over2.5"]
                pbtts = p1_pred["btts"]
            else:
                ph = elo_pred["home"]; pd = elo_pred["draw"]; pa = elo_pred["away"]
                po25 = 0.5; pbtts = 0.5

            # Normalize
            s = ph + pd + pa
            if s > 0:
                ph /= s; pd /= s; pa /= s

            # Actual
            act_h = 1 if hg > ag else 0
            act_d = 1 if hg == ag else 0
            act_a = 1 if hg < ag else 0
            act_o25 = 1 if hg + ag >= 3 else 0
            act_btts = 1 if (hg >= 1 and ag >= 1) else 0

            pred_vec = np.array([ph, pd, pa])
            act_vec = np.array([act_h, act_d, act_a])

            mc_brier = float(np.sum((pred_vec - act_vec)**2))
            if act_h:
                ll = -math.log(max(ph, 1e-12))
            elif act_d:
                ll = -math.log(max(pd, 1e-12))
            else:
                ll = -math.log(max(pa, 1e-12))

            cp = np.cumsum(pred_vec)[:-1]; ca = np.cumsum(act_vec)[:-1]
            rps_val = float(np.sum((cp - ca)**2) / 2)

            b_o25 = (po25 - act_o25)**2
            b_btts = (pbtts - act_btts)**2

            # Predicted outcome
            pred_out = "H" if ph > pd and ph > pa else ("D" if pd > pa else "A")
            act_out = "H" if hg > ag else ("D" if hg == ag else "A")

            results.append({
                "date": str(md), "year": wc_year,
                "home": home, "away": away, "hg": hg, "ag": ag,
                "p_home": ph, "p_draw": pd, "p_away": pa,
                "p_over25": po25, "p_btts": pbtts,
                "predicted": pred_out, "actual": act_out,
                "correct": 1 if pred_out == act_out else 0,
                "brier_mc": mc_brier, "log_loss": ll, "rps": rps_val,
                "brier_o25": b_o25, "brier_btts": b_btts,
                "p1_ok": p1_pred is not None,
            })

            # Update Elo AFTER prediction
            elo_tracker.update(home, away, hg, ag, neutral, match["tournament"])

    # ═══════════════════════════════════════════════════════════
    # Analysis
    # ═══════════════════════════════════════════════════════════
    n = len(results)
    briers = np.array([r["brier_mc"] for r in results])
    lls = np.array([r["log_loss"] for r in results])
    rps_arr = np.array([r["rps"] for r in results])
    acc = np.mean([r["correct"] for r in results])
    o25_acc = np.mean([1 if (r["p_over25"] > 0.5) == (r["hg"] + r["ag"] >= 3) else 0 for r in results])
    btts_acc = np.mean([1 if (r["p_btts"] > 0.5) == (r["hg"] >= 1 and r["ag"] >= 1) else 0 for r in results])

    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print("Matches:", n)
    print("Brier (multiclass):", round(briers.mean(), 4), "(+/-", round(briers.std(), 4), ")")
    print("Log Loss:", round(lls.mean(), 4), "(+/-", round(lls.std(), 4), ")")
    print("RPS:", round(rps_arr.mean(), 4), "(+/-", round(rps_arr.std(), 4), ")")
    print("1X2 Accuracy:", str(round(acc*100, 1)) + "%")
    print("Over 2.5 Accuracy:", str(round(o25_acc*100, 1)) + "%")
    print("BTTS Accuracy:", str(round(btts_acc*100, 1)) + "%")

    # By year
    by_year = defaultdict(lambda: {"brier": [], "ll": [], "rps": [], "acc": [], "n": 0})
    for r in results:
        y = r["year"]
        by_year[y]["brier"].append(r["brier_mc"])
        by_year[y]["ll"].append(r["log_loss"])
        by_year[y]["rps"].append(r["rps"])
        by_year[y]["acc"].append(r["correct"])
        by_year[y]["n"] += 1

    print("\nBy Tournament:")
    print("  Year    N    Brier   LogLoss  RPS     Acc")
    for y in sorted(by_year):
        d = by_year[y]
        print("  " + str(y) + "  " + str(d["n"]).ljust(5) +
              str(round(np.mean(d["brier"]), 4)).ljust(8) +
              str(round(np.mean(d["ll"]), 4)).ljust(9) +
              str(round(np.mean(d["rps"]), 4)).ljust(8) +
              str(round(np.mean(d["acc"])*100, 1)) + "%")

    # Baselines
    home_rate = sum(1 for r in results if r["actual"] == "H") / n
    draw_rate = sum(1 for r in results if r["actual"] == "D") / n
    away_rate = sum(1 for r in results if r["actual"] == "A") / n
    print("\nActual rates: H=" + str(round(home_rate*100,1)) +
          "% D=" + str(round(draw_rate*100,1)) + "% A=" + str(round(away_rate*100,1)) + "%")

    actuals_oh = np.zeros((n, 3))
    for i, r in enumerate(results):
        if r["actual"] == "H": actuals_oh[i, 0] = 1
        elif r["actual"] == "D": actuals_oh[i, 1] = 1
        else: actuals_oh[i, 2] = 1

    clim_brier = float(np.mean(np.sum(
        (np.tile([home_rate, draw_rate, away_rate], (n, 1)) - actuals_oh)**2, axis=1)))
    print("Climatological Brier:", round(clim_brier, 4))
    print("Model improvement:", round(clim_brier - briers.mean(), 4))

    # Calibration
    print("\nCalibration (Home win probability):")
    print("  Bucket     N     Pred   Actual")
    for lo in np.arange(0, 1.0, 0.1):
        hi = lo + 0.1
        subset = [(r, 1 if r["actual"] == "H" else 0)
                  for r in results if lo <= r["p_home"] < hi]
        if subset:
            p_mean = np.mean([x[0]["p_home"] for x in subset])
            a_mean = np.mean([x[1] for x in subset])
            print("  " + str(round(lo,1)) + "-" + str(round(hi,1)).ljust(7) +
                  str(len(subset)).ljust(6) +
                  str(round(p_mean,3)).ljust(7) +
                  str(round(a_mean,3)))

    # Betting strategy simulation (simple threshold on model-market edge)
    # Using Pinnacle-style "sharp" probabilities as proxy for market
    print("\nBETTING STRATEGY BACKTEST")
    print("-" * 40)
    # Without real market odds, we test: when model is most confident, does it win?
    high_conf = [r for r in results if max(r["p_home"], r["p_draw"], r["p_away"]) > 0.55]
    if high_conf:
        hc_acc = np.mean([r["correct"] for r in high_conf])
        print("High confidence (>55%):", len(high_conf), "matches, Acc=" + str(round(hc_acc*100,1)) + "%")
        # Implied edge at 0.55 threshold at fair 1/0.55 = 1.82 odds
        implied_odds = [1.0 / max(r["p_home"], r["p_draw"], r["p_away"]) for r in high_conf]
        implied_ev = [o * hc_acc - (1 - hc_acc) for o in implied_odds]
        print("Avg implied fair EV (if betting model favorite):", round(np.mean(implied_ev), 4))

    medium_conf = [r for r in results if 0.45 < max(r["p_home"], r["p_draw"], r["p_away"]) <= 0.55]
    if medium_conf:
        mc_acc = np.mean([r["correct"] for r in medium_conf])
        print("Med confidence (45-55%):", len(medium_conf), "matches, Acc=" + str(round(mc_acc*100,1)) + "%")

    low_conf = [r for r in results if max(r["p_home"], r["p_draw"], r["p_away"]) <= 0.45]
    if low_conf:
        lc_acc = np.mean([r["correct"] for r in low_conf])
        print("Low confidence (<45%):", len(low_conf), "matches, Acc=" + str(round(lc_acc*100,1)) + "%")

    # P1 vs Elo-only comparison
    p1_matches = [r for r in results if r["p1_ok"]]
    elo_only = [r for r in results if not r["p1_ok"]]
    print("\n  With P1:", len(p1_matches), "matches, Brier=" +
          str(round(np.mean([r["brier_mc"] for r in p1_matches]), 4)))
    print("  Elo only:", len(elo_only), "matches, Brier=" +
          str(round(np.mean([r["brier_mc"] for r in elo_only]), 4)))

    # Save
    with open(OUTDIR / "predictions.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader(); w.writerows(results)

    metrics = {
        "n": n,
        "brier_mean": float(briers.mean()), "brier_std": float(briers.std()),
        "logloss_mean": float(lls.mean()), "logloss_std": float(lls.std()),
        "rps_mean": float(rps_arr.mean()), "rps_std": float(rps_arr.std()),
        "accuracy": float(acc), "over25_acc": float(o25_acc), "btts_acc": float(btts_acc),
        "clim_brier": float(clim_brier), "brier_improvement": float(clim_brier - briers.mean()),
        "by_year": {str(y): {
            "n": by_year[y]["n"],
            "brier_mean": float(np.mean(by_year[y]["brier"])),
            "logloss_mean": float(np.mean(by_year[y]["ll"])),
            "rps_mean": float(np.mean(by_year[y]["rps"])),
            "accuracy": float(np.mean(by_year[y]["acc"])),
        } for y in sorted(by_year)},
    }
    with open(OUTDIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print("\nOutput: " + str(OUTDIR))

if __name__ == "__main__":
    main()
