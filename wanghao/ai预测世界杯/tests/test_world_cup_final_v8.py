import json
import math
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "world_cup_final_v8"


class WorldCupFinalV8Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        cls.recommendations = pd.read_csv(OUT / "polymarket_recommendations.csv")
        cls.snapshot = pd.read_csv(ROOT / cls.summary["generated_from_snapshot"])

    def test_single_final_and_probability_mass(self):
        self.assertEqual(set(self.summary["summaries"]), {"fifwc-esp-arg-2026-07-19"})
        match = self.summary["summaries"]["fifwc-esp-arg-2026-07-19"]
        core = match["core"]
        progression = match["progression"]
        self.assertAlmostEqual(core["home_win"] + core["draw"] + core["away_win"], 1.0, places=10)
        self.assertAlmostEqual(progression["home"] + progression["away"], 1.0, places=10)

    def test_frozen_snapshot_is_fully_classified(self):
        snapshot = self.snapshot[
            self.snapshot["fixture_id"] == "fifwc-esp-arg-2026-07-19"
        ]
        self.assertEqual(len(self.recommendations), len(snapshot))
        self.assertEqual(set(self.recommendations["market_id"].astype(str)),
                         set(snapshot["market_id"].astype(str)))

    def test_corner_family_kill_switch(self):
        corners = self.recommendations[
            self.recommendations["sports_market_type"].fillna("").str.contains("corner")
        ]
        self.assertFalse(corners["decision"].isin(["BET", "BET_CANDIDATE"]).any())
        self.assertTrue((corners["required_edge"].dropna().astype(float) >= 0.08).all())

    def test_shootout_small_sample_is_strongly_shrunk(self):
        progression = self.summary["summaries"]["fifwc-esp-arg-2026-07-19"]["progression"]
        self.assertGreater(progression["shootout_home_win"], 0.40)
        self.assertLess(progression["shootout_home_win"], 0.60)

    def test_no_unfiltered_taker_recommendation(self):
        self.assertFalse(self.recommendations["decision"].isin(["BET", "BET_CANDIDATE"]).any())
        self.assertEqual(self.summary["strict_arbitrage"], [])

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
