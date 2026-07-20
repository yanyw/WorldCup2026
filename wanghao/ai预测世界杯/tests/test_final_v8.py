import json
import math
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "world_cup_final_v8"
FIXTURE = "fifwc-esp-arg-2026-07-19"


class FinalV8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        cls.recommendations = pd.read_csv(OUT / "polymarket_recommendations.csv")
        cls.snapshot = pd.read_csv(ROOT / cls.summary["generated_from_snapshot"])

    def test_final_only_and_probability_mass(self):
        self.assertEqual(set(self.summary["summaries"]), {FIXTURE})
        match = self.summary["summaries"][FIXTURE]
        core = match["core"]
        self.assertAlmostEqual(core["home_win"] + core["draw"] + core["away_win"], 1.0)
        self.assertAlmostEqual(match["progression"]["home"] + match["progression"]["away"], 1.0)

    def test_snapshot_join_is_final_only_and_complete(self):
        expected = self.snapshot[self.snapshot["fixture_id"] == FIXTURE]
        self.assertEqual(len(self.recommendations), len(expected))
        self.assertEqual(set(self.recommendations["market_id"].astype(str)),
                         set(expected["market_id"].astype(str)))

    def test_no_bet_bypasses_filters(self):
        bets = self.recommendations[self.recommendations["decision"] == "BET"]
        for _, row in bets.iterrows():
            self.assertGreaterEqual(float(row["robust_edge"]), float(row["required_edge"]))
            self.assertLessEqual(float(row["ask"]), float(row["max_entry"]))
            self.assertGreaterEqual(float(row["depth_2c_usd"]), 500.0)

    def test_minute_state_probabilities(self):
        frame = pd.read_csv(OUT / f"{FIXTURE}_minute_hazards.csv")
        self.assertEqual(len(frame), 102)
        for column in [x for x in frame if x.startswith("p_")]:
            self.assertTrue(((frame[column] >= 0) & (frame[column] <= 1)).all())
        self.assertAlmostEqual(frame.iloc[-1]["p_scoreless_after"],
                               self.summary["summaries"][FIXTURE]["first_goal"]["none"], places=12)

    def test_no_nonfinite_summary_numbers(self):
        def walk(value):
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)
            elif isinstance(value, float):
                self.assertTrue(math.isfinite(value))
        walk(self.summary)


if __name__ == "__main__":
    unittest.main()
