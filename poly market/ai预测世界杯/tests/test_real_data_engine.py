import json
import math
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "real_data_engine"


class RealDataEngineOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads((OUT / "real_data_engine_summary.json").read_text(encoding="utf-8"))
        cls.minute = pd.read_csv(OUT / "minute_by_minute_1_95.csv")
        cls.players = pd.read_csv(OUT / "player_event_probabilities.csv")
        cls.fifa = pd.read_csv(ROOT / "data" / "curated" / "fifa_2026_eng_arg_team_match_features.csv")

    def test_probability_mass(self):
        r = self.summary["regulation"]
        self.assertAlmostEqual(r["england_win"] + r["draw"] + r["argentina_win"], 1.0, places=10)
        p = self.summary["progression"]
        self.assertAlmostEqual(p["england_advance"] + p["argentina_advance"], 1.0, places=10)

    def test_minute_probability_bounds(self):
        self.assertEqual(len(self.minute), 95)
        probability_columns = [c for c in self.minute if c.startswith("p_")]
        self.assertTrue((self.minute[probability_columns] >= 0).all().all())
        self.assertTrue((self.minute[probability_columns] <= 1).all().all())
        self.assertEqual(int(self.minute.isna().sum().sum()), 0)

    def test_player_shot_allocation_conserves_team_total(self):
        rates = self.summary["derived_event_rates"]
        totals = self.players.groupby("team").expected_shots.sum().to_dict()
        self.assertAlmostEqual(totals["England"], rates["home_shots"], places=8)
        self.assertAlmostEqual(totals["Argentina"], rates["away_shots"], places=8)

    def test_official_fifa_sample_complete(self):
        self.assertEqual(len(self.fifa), 12)
        self.assertEqual(set(self.fifa.team), {"England", "Argentina"})
        self.assertTrue((self.fifa.attempts_against > 0).all())

    def test_no_nonfinite_summary_numbers(self):
        def walk(value):
            if isinstance(value, dict):
                for x in value.values():
                    walk(x)
            elif isinstance(value, list):
                for x in value:
                    walk(x)
            elif isinstance(value, float):
                self.assertTrue(math.isfinite(value))
        walk(self.summary)

    def test_inputs_are_real_data_only(self):
        cfg = json.loads((ROOT / "config" / "real_data_engine_eng_arg_20260715.json").read_text(encoding="utf-8"))
        inputs = " ".join(cfg["data"].values()).lower()
        for forbidden in ("fc26", "efootball", "pes", "polymarket", "odds"):
            self.assertNotIn(forbidden, inputs)


if __name__ == "__main__":
    unittest.main()
