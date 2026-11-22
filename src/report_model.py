"""Support model for the A–E portfolios in Reserve Portfolio Design."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

REPORT_CASES = ("central", "conservative", "optimistic")

# Values transcribed from Reserve_Portfolio_Design_Group8.docx, Table 4.
TABLE4_EXPECTED = {
    "A": {"cash_ratio_pct": 40.0, "portfolio_yield_pct": 2.38, "central_sd_pct": 84.0, "central_t1_pct": 99.0, "central_later_pct": 1.0, "conservative_sd_pct": 74.0, "conservative_t1_pct": 94.0, "conservative_failure_point_pct": 95.0, "eligibility": "Compliant"},
    "B": {"cash_ratio_pct": 20.0, "portfolio_yield_pct": 2.89, "central_sd_pct": 72.0, "central_t1_pct": 97.0, "central_later_pct": 3.0, "conservative_sd_pct": 57.0, "conservative_t1_pct": 87.0, "conservative_failure_point_pct": 85.0, "eligibility": "Compliant"},
    "C": {"cash_ratio_pct": 12.0, "portfolio_yield_pct": 3.20, "central_sd_pct": 38.4, "central_t1_pct": 82.4, "central_later_pct": 17.6, "conservative_sd_pct": 25.2, "conservative_t1_pct": 56.0, "conservative_failure_point_pct": 55.0, "eligibility": "Compliant"},
    "D": {"cash_ratio_pct": 5.0, "portfolio_yield_pct": 3.38, "central_sd_pct": 59.5, "central_t1_pct": 92.5, "central_later_pct": 7.5, "conservative_sd_pct": 42.3, "conservative_t1_pct": 77.0, "conservative_failure_point_pct": 75.0, "eligibility": "Compliant"},
    "E": {"cash_ratio_pct": 5.0, "portfolio_yield_pct": 3.75, "central_sd_pct": 39.0, "central_t1_pct": 67.5, "central_later_pct": 32.5, "conservative_sd_pct": 27.5, "conservative_t1_pct": 52.5, "conservative_failure_point_pct": 50.0, "eligibility": "Non-compliant; counterfactual only"},
}


def load_report_assets(path: str | Path) -> Dict[str, Dict[str, dict]]:
    """Load asset assumptions as ``{case: {asset_id: parameters}}``."""
    cases: Dict[str, Dict[str, dict]] = {case: {} for case in REPORT_CASES}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            case = row["case"]
            if case not in cases:
                raise ValueError(f"Unknown report parameter case: {case!r}")
            cases[case][row["asset_id"]] = {
                "asset_name_cn": row["asset_name_cn"],
                "eligible": bool(int(row["eligible"])),
                "annual_yield": float(row["annual_yield"]),
                # Table 2 has no stress-haircut dimension; preserve its stated
                # baseline by passing a zero haircut to the shared engine.
                "stress_haircut": 0.0,
                "same_day_ratio": float(row["same_day_ratio"]),
                "next_day_ratio": float(row["next_day_ratio"]),
                "later_ratio": float(row["later_ratio"]),
                "source": row["source"],
                "note": row["note"],
            }
    asset_ids = [set(cases[case]) for case in REPORT_CASES]
    if not asset_ids[0] or any(ids != asset_ids[0] for ids in asset_ids[1:]):
        raise ValueError("Each report case must contain the same non-empty asset set")
    for case, assets in cases.items():
        for aid, asset in assets.items():
            ladder_total = asset["same_day_ratio"] + asset["next_day_ratio"] + asset["later_ratio"]
            if abs(ladder_total - 1.0) > 1e-6:
                raise ValueError(f"{case}/{aid} liquidity ladder sums to {ladder_total:.6f}, expected 1.0")
    return cases


def load_report_portfolios(path: str | Path) -> Dict[str, dict]:
    """Load the report's A–E portfolios without touching demo A/B/C."""
    portfolios: Dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            pid = row["portfolio_id"]
            entry = portfolios.setdefault(pid, {"name": row["portfolio_name"], "weights": {}})
            entry["weights"][row["asset_id"]] = float(row["weight"])
    if set(portfolios) != set(TABLE4_EXPECTED):
        raise ValueError(f"Report portfolio IDs must be A–E; got {sorted(portfolios)}")
    return portfolios


def validate_report_inputs(assets_by_case: dict, portfolios: dict) -> None:
    """Check each weight set against every case and ensure asset flags agree."""
    base_flags = {aid: asset["eligible"] for aid, asset in assets_by_case["central"].items()}
    for case, assets in assets_by_case.items():
        for pid, entry in portfolios.items():
            total = sum(entry["weights"].values())
            if abs(total - 1.0) > 1e-6:
                raise ValueError(f"Report portfolio {pid} weights sum to {total:.6f}")
            missing = set(entry["weights"]) - set(assets)
            if missing:
                raise KeyError(f"Report portfolio {pid} references unknown assets in {case}: {sorted(missing)}")
            if any(assets[aid]["eligible"] != base_flags[aid] for aid in assets):
                raise ValueError(f"Eligibility flags differ across report cases ({case})")


def portfolio_metrics(weights: dict, assets: dict) -> dict:
    """Calculate weighted SD, T+1 cumulative, later, yield, and eligibility."""
    return {
        "cash_ratio_pct": 100 * weights.get("cash", 0.0),
        "same_day_pct": 100 * sum(weights[aid] * asset["same_day_ratio"] for aid, asset in ((aid, assets[aid]) for aid in weights)),
        "t1_cumulative_pct": 100 * sum(weights[aid] * (asset["same_day_ratio"] + asset["next_day_ratio"]) for aid, asset in ((aid, assets[aid]) for aid in weights)),
        "later_pct": 100 * sum(weights[aid] * asset["later_ratio"] for aid, asset in ((aid, assets[aid]) for aid in weights)),
        "portfolio_yield_pct": 100 * sum(weights[aid] * assets[aid]["annual_yield"] for aid in weights),
        "eligibility": "Compliant" if all(assets[aid]["eligible"] for aid, weight in weights.items() if weight > 0) else "Non-compliant; counterfactual only",
    }


def reproduce_table4(assets_by_case: dict, portfolios: dict) -> tuple[list[dict], list[dict]]:
    """Return a wide computed summary and a long comparison to Table 4."""
    wide_rows: list[dict] = []
    comparison_rows: list[dict] = []
    for pid, entry in portfolios.items():
        central = portfolio_metrics(entry["weights"], assets_by_case["central"])
        conservative = portfolio_metrics(entry["weights"], assets_by_case["conservative"])
        computed = {
            "cash_ratio_pct": central["cash_ratio_pct"],
            "portfolio_yield_pct": central["portfolio_yield_pct"],
            "central_sd_pct": central["same_day_pct"],
            "central_t1_pct": central["t1_cumulative_pct"],
            "central_later_pct": central["later_pct"],
            "conservative_sd_pct": conservative["same_day_pct"],
            "conservative_t1_pct": conservative["t1_cumulative_pct"],
            # The report labels this point approximately, to a 5-percentage-point bucket.
            "conservative_failure_point_pct": round(conservative["t1_cumulative_pct"] / 5.0) * 5.0,
            "eligibility": central["eligibility"],
        }
        expected = TABLE4_EXPECTED[pid]
        mismatches = []
        for metric, report_value in expected.items():
            value = computed[metric]
            if isinstance(report_value, str):
                difference = "" if value == report_value else "mismatch"
                matches = value == report_value
                unit = "category"
            else:
                difference = value - report_value
                precision = 0.0051 if metric == "portfolio_yield_pct" else (2.5001 if metric.endswith("failure_point_pct") else 0.051)
                matches = abs(difference) <= precision
                unit = "% p.a." if metric == "portfolio_yield_pct" else "% of circulation"
            if not matches:
                mismatches.append(metric)
            comparison_rows.append({
                "portfolio_id": pid,
                "metric": metric,
                "reported_table4": report_value,
                "computed": value,
                "difference": difference,
                "unit": unit,
                "matches_at_report_precision": int(matches),
            })
        wide_rows.append({"portfolio_id": pid, **computed, "matches_table4": int(not mismatches), "mismatch_metrics": ";".join(mismatches)})
    return wide_rows, comparison_rows
