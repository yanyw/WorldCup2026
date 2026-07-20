import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wc_model.game_attributes import apply_game_adjustment, team_profile


class TestGameAttributes(unittest.TestCase):
    def test_profile_uses_goalkeeper_overall_and_is_finite(self):
        players = [
            {"role": "GK", "ovr": 82, "pac": 1, "sho": 1, "pas": 1, "dri": 1, "def": 1, "phy": 1},
            *[{"role": "DEF", "ovr": 80, "pac": 75, "sho": 50, "pas": 70, "dri": 70, "def": 82, "phy": 80} for _ in range(4)],
            *[{"role": "MID", "ovr": 80, "pac": 75, "sho": 75, "pas": 82, "dri": 82, "def": 75, "phy": 78} for _ in range(4)],
            *[{"role": "FWD", "ovr": 85, "pac": 85, "sho": 86, "pas": 80, "dri": 85, "def": 40, "phy": 75} for _ in range(2)],
        ]
        profile = team_profile(players)
        self.assertGreater(profile["defense"], 70)
        self.assertEqual(profile["starting_xi_ovr"], sum(p["ovr"] for p in players) / 11)

    def test_adjustments_are_capped(self):
        players = [{"role": "GK", "ovr": 99, "pac": 99, "sho": 99, "pas": 99, "dri": 99, "def": 99, "phy": 99}]
        for role, count in (("DEF", 4), ("MID", 4), ("FWD", 2)):
            players += [{"role": role, "ovr": 99, "pac": 99, "sho": 99, "pas": 99, "dri": 99, "def": 99, "phy": 99} for _ in range(count)]
        weak = [{**p, **{k: 40 for k in ("ovr", "pac", "sho", "pas", "dri", "def", "phy")}} for p in players]
        base = {"lambda_home": 1.2, "lambda_away": 1.2, "rho": 0.0}
        fixture = {"home": "H", "away": "A"}
        method = {"game_rating_reliability": 1, "rating_edge_scale": 1,
                  "max_log_lambda_shift": .04, "referee_total_goal_multiplier": 1,
                  "referee_uncertainty_extra": .02}
        spec = {"formation": "x", "starting_xi_status": "projected", "fitness_multiplier": 1,
                "formation_attack_multiplier": 1, "formation_defense_multiplier": 1,
                "bench_depth_multiplier": 1}
        adjusted, audit, _ = apply_game_adjustment(
            base, fixture, {"method": method, "teams": {"H": spec, "A": spec}},
            {"teams": {"H": {"players": players}, "A": {"players": weak}}}, 10,
        )
        self.assertLessEqual(audit["home_lambda_multiplier"], 1.041)
        self.assertGreaterEqual(audit["away_lambda_multiplier"], .960)
        self.assertAlmostEqual(adjusted["matrix"].sum(), 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
