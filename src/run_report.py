"""Reproduce Reserve Portfolio Design report portfolios A–E and Table 4."""

from __future__ import annotations

import csv
from pathlib import Path

from .engine import gap_and_flag, on_time_rate, monte_carlo
from .report_model import (
    REPORT_CASES,
    load_report_assets,
    load_report_portfolios,
    portfolio_metrics,
    reproduce_table4,
    validate_report_inputs,
)

SHOCK_RATES = (0.05, 0.20, 0.50, 0.80)
N_RUNS = 1000
SIGMA = 0.25
SEED = 42


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Refusing to write empty results: {path}")
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_scenario_rows(assets_by_case: dict, portfolios: dict) -> list[dict]:
    rows = []
    for case in REPORT_CASES:
        assets = assets_by_case[case]
        for pid, entry in portfolios.items():
            metrics = portfolio_metrics(entry["weights"], assets)
            sd = metrics["same_day_pct"] / 100
            t1 = metrics["t1_cumulative_pct"] / 100
            later = metrics["later_pct"] / 100
            for shock in SHOCK_RATES:
                gap, breached = gap_and_flag(t1, shock)
                rows.append({
                    "case": case,
                    "portfolio_id": pid,
                    "shock_rate": f"{shock:.2f}",
                    "same_day_available": f"{sd:.4f}",
                    "t1_cumulative_available": f"{t1:.4f}",
                    "later_available": f"{later:.4f}",
                    "on_time_rate": f"{on_time_rate(t1, shock):.4f}",
                    "gap_at_t1": f"{gap:.4f}",
                    "failure_flag_at_t1": breached,
                    "portfolio_yield": f"{metrics['portfolio_yield_pct'] / 100:.5f}",
                    "eligibility": metrics["eligibility"],
                })
    return rows


def build_mc_rows(assets_by_case: dict, portfolios: dict) -> list[dict]:
    rows = []
    for case in REPORT_CASES:
        mc = monte_carlo(
            portfolios, assets_by_case[case], SHOCK_RATES,
            n_runs=N_RUNS, sigma=SIGMA, seed=SEED,
        )
        for row in mc:
            rows.append({"case": case, **row})
    return rows


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    assets_by_case = load_report_assets(root / "data" / "report_params_assets.csv")
    portfolios = load_report_portfolios(root / "data" / "report_portfolios.csv")
    validate_report_inputs(assets_by_case, portfolios)
    summary, comparison = reproduce_table4(assets_by_case, portfolios)
    write_csv(root / "outputs" / "report_portfolio_summary.csv", summary)
    write_csv(root / "outputs" / "report_table4_comparison.csv", comparison)
    scenarios = build_scenario_rows(assets_by_case, portfolios)
    write_csv(root / "outputs" / "report_scenario_results.csv", scenarios)
    mc_rows = build_mc_rows(assets_by_case, portfolios)
    write_csv(root / "outputs" / "report_mc_results.csv", mc_rows)

    mismatches = sum(not row["matches_table4"] for row in summary)
    print(f"Wrote {len(summary)} Table 4 portfolio summaries; mismatching portfolios: {mismatches}")
    print(f"Wrote {len(comparison)} Table 4 metric comparisons")
    print(f"Wrote {len(scenarios)} deterministic report scenarios")
    print(f"Wrote {len(mc_rows)} Monte Carlo summaries ({N_RUNS} draws per case/portfolio/shock)")
    if mismatches:
        raise SystemExit("Computed values do not all match report Table 4 at reported precision")


if __name__ == "__main__":
    main()
