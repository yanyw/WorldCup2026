import json
import math
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "remaining_matches_v7"


class RemainingMatchesV7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
        cls.recommendations = pd.read_csv(OUT / "polymarket_recommendations.csv")
        # Historical outputs must validate against their frozen source rather
        # than a mutable LATEST pointer.
        pointer = cls.summary["generated_from_snapshot"]
        cls.snapshot = pd.read_csv(ROOT / pointer)

    def test_two_fixtures_and_probability_mass(self):
        self.assertEqual(len(self.summary["summaries"]), 2)
        for match in self.summary["summaries"].values():
            core = match["core"]
            self.assertAlmostEqual(core["home_win"] + core["draw"] + core["away_win"], 1.0, places=10)
            progression = match["progression"]
            self.assertAlmostEqual(progression["home"] + progression["away"], 1.0, places=10)

    def test_every_snapshot_market_is_classified_once(self):
        self.assertEqual(len(self.recommendations), len(self.snapshot))
        self.assertEqual(set(self.recommendations["market_id"].astype(str)),
                         set(self.snapshot["market_id"].astype(str)))
        self.assertFalse(self.recommendations["market_id"].duplicated().any())

    def test_executable_bets_clear_robust_threshold(self):
        bets = self.recommendations[self.recommendations["decision"] == "BET"]
        for _, row in bets.iterrows():
            self.assertGreaterEqual(float(row["robust_edge"]), float(row["required_edge"]))
            self.assertLessEqual(float(row["ask"]), float(row["max_entry"]))
            self.assertGreaterEqual(float(row["depth_2c_usd"]), 500.0)

    def test_missing_player_samples_are_never_bets(self):
        bad = self.recommendations[
            self.recommendations["player_data_quality_reason"].fillna("").str.len() > 0
        ]
        self.assertFalse(bad["decision"].isin(["BET", "BET_CANDIDATE"]).any())

    def test_minute_hazards_are_probabilities(self):
        for fixture in self.summary["summaries"]:
            frame = pd.read_csv(OUT / f"{fixture}_minute_hazards.csv")
            self.assertEqual(len(frame), 102)
            for column in [x for x in frame if x.startswith("p_")]:
                self.assertTrue(((frame[column] >= 0) & (frame[column] <= 1)).all())

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

    def test_strict_arbitrage_claims_have_positive_locked_profit(self):
        for item in self.summary["strict_arbitrage"]:
            self.assertLess(item["cost"], 1.0)
            self.assertGreater(item["locked_profit"], 0.0)


if __name__ == "__main__":
    unittest.main()
