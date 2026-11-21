"""Run the baseline scenario matrix and write ``outputs/results.csv``.

This stage covers the portfolio-level aggregates: same-day available
amount, coverage, gap and failure flag. Redemption rules are added later;
the ``rule`` column is therefore written as ``baseline`` for now.
"""

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
        portfolio_yield,
        same_day_available,
        validate_weights,
    )

SHOCK_RATES = (0.20, 0.40, 0.60, 0.80, 1.00)
RULE = "baseline"
FIELDS = [
    "portfolio_id",
    "shock_rate",
    "rule",
    "same_day_available",
    "coverage_ratio",
    "gap",
    "failure_flag",
    "portfolio_yield",
]


def build_rows(assets: dict, portfolios: dict) -> list[dict]:
    """Build one row per (portfolio, shock rate)."""
    rows: list[dict] = []
    for pid, entry in portfolios.items():
        available = same_day_available(entry["weights"], assets)
        annual_yield = portfolio_yield(entry["weights"], assets)
        for shock in SHOCK_RATES:
            gap, flag = gap_and_flag(available, shock)
            rows.append(
                {
                    "portfolio_id": pid,
                    "shock_rate": f"{shock:.2f}",
                    "rule": RULE,
                    "same_day_available": f"{available:.4f}",
                    "coverage_ratio": f"{coverage(available, shock):.4f}",
                    "gap": f"{gap:.4f}",
                    "failure_flag": flag,
                    "portfolio_yield": f"{annual_yield:.4f}",
                }
            )
    return rows


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    assets = load_assets(root / "data" / "params_assets.csv")
    portfolios = load_portfolios(root / "data" / "portfolios.csv")
    validate_weights(portfolios, assets)

    rows = build_rows(assets, portfolios)
    out = root / "outputs" / "results.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out.relative_to(root)}")
    print()
    print("Portfolio summary")
    for pid, entry in portfolios.items():
        available = same_day_available(entry["weights"], assets)
        annual_yield = portfolio_yield(entry["weights"], assets)
        print(
            f"{pid}  {entry['name']}  "
            f"same-day {available:.1%}  "
            f"failure at {failure_point(available):.1%}  "
            f"yield {annual_yield:.2%}"
        )
    print()
    print("At a 80% redemption shock")
    for pid, entry in portfolios.items():
        available = same_day_available(entry["weights"], assets)
        cov = coverage(available, 0.80)
        gap, flag = gap_and_flag(available, 0.80)
        print(
            f"{pid}  {entry['name']}  "
            f"coverage {cov:.1%}  "
            f"gap {gap:.1%}  "
            f"{'FAIL' if flag else 'ok'}"
        )


if __name__ == "__main__":
    main()
