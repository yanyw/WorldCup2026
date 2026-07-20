import json
import math
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "remaining_matches_v6"


class RemainingMatchesV6Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))

    def test_two_fixtures_and_probability_mass(self):
        self.assertEqual(len(self.summary["summaries"]), 2)
        for match in self.summary["summaries"].values():
            core = match["core"]
            self.assertAlmostEqual(core["home_win"] + core["draw"] + core["away_win"], 1.0, places=10)
            prog = match["progression"]
            self.assertAlmostEqual(prog["home"] + prog["away"], 1.0, places=10)

    def test_fifa_sample_has_seven_matches_per_team(self):
        frame = pd.read_csv(ROOT / "data" / "curated" / "fifa_2026_final_four_team_match_features.csv")
        self.assertEqual(frame.groupby("team").size().to_dict(),
                         {"Argentina": 7, "England": 7, "France": 7, "Spain": 7})

    def test_minute_hazards_and_stochastic_stoppage(self):
        for fixture in self.summary["summaries"]:
            frame = pd.read_csv(OUT / f"{fixture}_minute_hazards.csv")
            self.assertEqual(len(frame), 102)
            self.assertEqual(frame.loc[89, "p_active"], 1.0)
            self.assertLess(frame.loc[101, "p_active"], 1.0)
            for col in [x for x in frame if x.startswith("p_")]:
                self.assertTrue(((frame[col] >= 0) & (frame[col] <= 1)).all())

    def test_no_nonfinite_summary_numbers(self):
        def walk(value):
            if isinstance(value, dict):
                for item in value.values(): walk(item)
            elif isinstance(value, list):
                for item in value: walk(item)
            elif isinstance(value, float):
                self.assertTrue(math.isfinite(value))
        walk(self.summary)

    def test_no_strict_arbitrage_claim_without_locked_book(self):
        for item in self.summary["strict_arbitrage"]:
            self.assertLess(item["cost"], 1.0)
            self.assertGreater(item["locked_profit"], 0.0)


if __name__ == "__main__":
    unittest.main()
