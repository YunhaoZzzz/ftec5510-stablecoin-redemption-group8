"""Acceptance checks for the baseline engine."""

import unittest
from pathlib import Path

from src.engine import (
    coverage,
    failure_point,
    gap_and_flag,
    load_assets,
    load_portfolios,
    same_day_available,
)

ROOT = Path(__file__).resolve().parents[1]


class BaselineEngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = load_assets(ROOT / "data" / "params_assets.csv")
        cls.portfolios = load_portfolios(ROOT / "data" / "portfolios.csv")

    def test_same_day_available(self):
        expected = {"A": 0.92, "B": 0.80, "C": 0.68}
        for pid, exp in expected.items():
            got = same_day_available(self.portfolios[pid]["weights"], self.assets)
            self.assertAlmostEqual(got, exp, places=6, msg=pid)

    def test_failure_point(self):
        for pid, entry in self.portfolios.items():
            available = same_day_available(entry["weights"], self.assets)
            self.assertAlmostEqual(
                failure_point(available), available, places=6, msg=pid
            )

    def test_coverage_at_eighty_percent(self):
        cases = {"A": (1.15, False), "B": (1.00, False), "C": (0.85, True)}
        for pid, (exp_cov, exp_fail) in cases.items():
            available = same_day_available(
                self.portfolios[pid]["weights"], self.assets
            )
            cov = coverage(available, 0.80)
            gap, flag = gap_and_flag(available, 0.80)
            self.assertAlmostEqual(cov, exp_cov, places=6, msg=pid)
            self.assertEqual(bool(flag), exp_fail, msg=pid)
            if exp_fail:
                self.assertAlmostEqual(gap, 0.12, places=6, msg=pid)


if __name__ == "__main__":
    unittest.main()
