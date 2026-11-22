"""Checks for the separate report A–E model and Table 4 reproduction."""

import unittest
from pathlib import Path

from src.report_model import (
    REPORT_CASES,
    load_report_assets,
    load_report_portfolios,
    reproduce_table4,
    validate_report_inputs,
)

ROOT = Path(__file__).resolve().parents[1]


class ReportPortfolioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = load_report_assets(ROOT / "data" / "report_params_assets.csv")
        cls.portfolios = load_report_portfolios(ROOT / "data" / "report_portfolios.csv")

    def test_report_inputs_cover_three_cases_nine_assets_and_five_portfolios(self):
        self.assertEqual(set(self.assets), set(REPORT_CASES))
        self.assertTrue(all(len(case_assets) == 9 for case_assets in self.assets.values()))
        self.assertEqual(set(self.portfolios), set("ABCDE"))
        validate_report_inputs(self.assets, self.portfolios)

    def test_table4_reproduction_matches_at_report_precision(self):
        summary, comparison = reproduce_table4(self.assets, self.portfolios)
        self.assertEqual(len(summary), 5)
        self.assertTrue(all(row["matches_table4"] == 1 for row in summary), summary)
        self.assertTrue(all(row["matches_at_report_precision"] == 1 for row in comparison))

    def test_report_portfolios_remain_separate_from_demo_portfolios(self):
        demo_ids = {"A", "B", "C"}
        self.assertEqual(set(self.portfolios), {"A", "B", "C", "D", "E"})
        self.assertEqual(self.portfolios["A"]["weights"]["cash"], 0.40)
        self.assertNotEqual(self.portfolios["A"]["weights"], {"cash": 0.8, "gov_bond_1y": 0.2})
        self.assertTrue(demo_ids.issubset(self.portfolios))


if __name__ == "__main__":
    unittest.main()
