"""Acceptance checks for the baseline engine."""

import unittest
from pathlib import Path

from src.engine import (
    coverage,
    failure_point,
    gap_and_flag,
    load_assets,
    load_portfolios,
    monte_carlo,
    on_time_rate,
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

    def test_monte_carlo_is_reproducible(self):
        first = monte_carlo(
            self.portfolios, self.assets, (0.80,), n_runs=200, seed=1
        )
        second = monte_carlo(
            self.portfolios, self.assets, (0.80,), n_runs=200, seed=1
        )
        self.assertEqual(first, second)

    def test_failure_probability_rises_with_shock(self):
        rows = monte_carlo(
            self.portfolios, self.assets, (0.20, 0.60, 1.00), n_runs=500, seed=7
        )
        for pid in self.portfolios:
            probs = [
                float(r["failure_prob"])
                for r in rows
                if r["portfolio_id"] == pid
            ]
            self.assertEqual(probs, sorted(probs), msg=pid)

    def test_on_time_rate_is_capped(self):
        cases = {"A": (0.80, 1.00), "C": (0.80, 0.85)}
        for pid, (shock, expected) in cases.items():
            available = same_day_available(
                self.portfolios[pid]["weights"], self.assets
            )
            self.assertAlmostEqual(
                on_time_rate(available, shock), expected, places=6, msg=pid
            )

        available_a = same_day_available(
            self.portfolios["A"]["weights"], self.assets
        )
        self.assertAlmostEqual(on_time_rate(available_a, 1.00), 0.92, places=6)


if __name__ == "__main__":
    unittest.main()
