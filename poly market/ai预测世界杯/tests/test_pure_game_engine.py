import json
import unittest
from pathlib import Path

from simulate_match_game_engine import (derive_match_rates, derive_team_engine,
                                        minute_tempo, score_state_multiplier)


ROOT = Path(__file__).resolve().parents[1]


class TestPureGameEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((ROOT/"config/pure_game_engine_eng_arg_20260715.json").read_text(encoding="utf-8"))
        cls.ratings = json.loads((ROOT/"data/curated/fc26_eng_arg_20260715.json").read_text(encoding="utf-8"))

    def test_derived_rates_are_physical(self):
        home = derive_team_engine("England", "Argentina", self.ratings, self.cfg)
        away = derive_team_engine("Argentina", "England", self.ratings, self.cfg)
        rates = derive_match_rates(home, away, self.cfg)
        self.assertGreater(rates["shots_home"], 5)
        self.assertGreater(rates["shots_away"], 5)
        self.assertLess(rates["shots_home"]+rates["shots_away"], 40)
        for key in ("sot_rate_home", "sot_rate_away", "sot_conversion_home",
                    "sot_conversion_away", "possession_home"):
            self.assertGreater(rates[key], 0)
            self.assertLess(rates[key], 1)

    def test_late_minutes_have_higher_tempo(self):
        self.assertLess(minute_tempo(5), minute_tempo(85))
        self.assertLess(minute_tempo(85), minute_tempo(93))


if __name__ == "__main__":
    unittest.main()
