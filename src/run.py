"""Run the demo portfolio matrix for both allocation rules."""

from __future__ import annotations

import csv
from pathlib import Path

if __package__ in (None, ""):
    # Executed as a script (e.g. right-click Run in an IDE).
    import sys
    from pathlib import Path as _Path

    sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
    from src.engine import (
        coverage,
        failure_point,
        gap_and_flag,
        load_assets,
        load_portfolios,
        monte_carlo,
        on_time_rate,
        on_time_available,
        portfolio_yield,
        same_day_available,
        validate_weights,
    )
else:
    # Executed as a module: python -m src.run
    from .engine import (
        coverage,
        failure_point,
        gap_and_flag,
        load_assets,
        load_portfolios,
        monte_carlo,
        on_time_rate,
        on_time_available,
        portfolio_yield,
        same_day_available,
        validate_weights,
    )

SHOCK_RATES = (0.20, 0.40, 0.60, 0.80, 1.00)
RULES = ("fcfs", "pro_rata")
N_RUNS = 1000
SIGMA = 0.25
SEED = 42
FIELDS = [
    "portfolio_id",
    "shock_rate",
    "rule",
    "same_day_available",
    "on_time_available",
    "coverage_ratio",
    "on_time_rate",
    "gap",
    "failure_flag",
    "portfolio_yield",
]
ALLOCATION_FIELDS = ["portfolio_id", "shock_rate", "rule", "holder_id", "requested", "same_day_allocated", "deferred_after_sd"]
MC_FIELDS = [
    "portfolio_id",
    "shock_rate",
    "n_runs",
    "sigma",
    "coverage_mean",
    "coverage_p05",
    "coverage_p50",
    "coverage_p95",
    "failure_prob",
    "gap_mean",
    "on_time_mean",
]


def build_rows(assets: dict, portfolios: dict) -> list[dict]:
    """Build one row per (portfolio, shock rate, allocation rule)."""
    try:
        from .rules import allocate
    except ImportError:
        from src.rules import allocate
    rows: list[dict] = []
    allocation_rows: list[dict] = []
    for pid, entry in portfolios.items():
        same_day = same_day_available(entry["weights"], assets)
        available = on_time_available(entry["weights"], assets)
        annual_yield = portfolio_yield(entry["weights"], assets)
        for shock in SHOCK_RATES:
            gap, flag = gap_and_flag(available, shock)
            requests = [shock * share for share in (0.50, 0.30, 0.20)]
            for rule in RULES:
                # Allocation rules act on today's liquidity; remaining requests
                # may still be settled from the T+1 ladder within the on-time window.
                allocations = allocate(rule, same_day, requests)
                rows.append({
                    "portfolio_id": pid,
                    "shock_rate": f"{shock:.2f}",
                    "rule": rule,
                    "same_day_available": f"{same_day:.4f}",
                    "on_time_available": f"{available:.4f}",
                    "coverage_ratio": f"{coverage(available, shock):.4f}",
                    "on_time_rate": f"{on_time_rate(available, shock):.4f}",
                    "gap": f"{gap:.4f}",
                    "failure_flag": flag,
                    "portfolio_yield": f"{annual_yield:.4f}",
                })
                for index, (request, paid) in enumerate(zip(requests, allocations), 1):
                    allocation_rows.append({
                        "portfolio_id": pid, "shock_rate": f"{shock:.2f}", "rule": rule,
                        "holder_id": f"H{index}", "requested": f"{request:.4f}",
                        "same_day_allocated": f"{paid:.4f}", "deferred_after_sd": f"{request-paid:.4f}",
                    })
    return rows, allocation_rows


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    assets = load_assets(root / "data" / "params_assets.csv")
    portfolios = load_portfolios(root / "data" / "portfolios.csv")
    validate_weights(portfolios, assets)

    rows, allocation_rows = build_rows(assets, portfolios)
    out = root / "outputs" / "results.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with open(root / "outputs" / "allocation_results.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ALLOCATION_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(allocation_rows)

    mc_rows = monte_carlo(
        portfolios, assets, SHOCK_RATES, n_runs=N_RUNS, sigma=SIGMA, seed=SEED
    )
    out_mc = root / "outputs" / "mc_results.csv"
    with open(out_mc, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MC_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(mc_rows)

    print(f"Wrote {len(rows)} rows to {out.relative_to(root)}")
    print(
        f"Wrote {len(mc_rows)} rows to {out_mc.relative_to(root)} "
        f"({N_RUNS} runs per scenario, sigma={SIGMA})"
    )
    print(f"Wrote {len(allocation_rows)} holder allocations to outputs/allocation_results.csv")
    print()
    print("Portfolio summary")
    for pid, entry in portfolios.items():
        available = on_time_available(entry["weights"], assets)
        annual_yield = portfolio_yield(entry["weights"], assets)
        print(
            f"{pid}  {entry['name']}  "
            f"on-time ceiling {available:.1%}  "
            f"failure at {failure_point(available):.1%}  "
            f"yield {annual_yield:.2%}"
        )
    print()
    print("At a 80% redemption shock")
    for pid, entry in portfolios.items():
        available = on_time_available(entry["weights"], assets)
        cov = coverage(available, 0.80)
        gap, flag = gap_and_flag(available, 0.80)
        print(
            f"{pid}  {entry['name']}  "
            f"coverage {cov:.1%}  "
            f"gap {gap:.1%}  "
            f"{'FAIL' if flag else 'ok'}"
        )

    print()
    print(f"Failure probability (Monte Carlo, {N_RUNS} runs, sigma={SIGMA})")
    header = "     " + "".join(f"{s:>9.0%}" for s in SHOCK_RATES)
    print(header)
    by_key = {(r["portfolio_id"], r["shock_rate"]): r for r in mc_rows}
    for pid, entry in portfolios.items():
        cells = "".join(
            f"{float(by_key[(pid, f'{s:.2f}')]['failure_prob']):>9.0%}"
            for s in SHOCK_RATES
        )
        print(f"{pid}    {cells}")


if __name__ == "__main__":
    main()
