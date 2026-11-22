"""Core engine for the stablecoin T+1 redemption resilience demo.

The model converts reserve assets into same-day and cumulative SD + T+1
realisable amounts, then compares those amounts with redemption requests.

All amounts are expressed as a share of outstanding circulation, so a
portfolio with 100% book coverage has reserves equal to ``CIRCULATION``.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Mapping

import numpy as np

CIRCULATION = 1.0


def load_assets(path: str | Path) -> Dict[str, dict]:
    """Read the asset parameter table, keyed by ``asset_id``."""
    assets: Dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            assets[row["asset_id"]] = {
                "asset_name_cn": row["asset_name_cn"],
                "same_day_ratio": float(row["same_day_ratio"]),
                "next_day_ratio": float(row.get("next_day_ratio", 0) or 0),
                "settle_days": int(float(row["settle_days"])),
                "stress_haircut": float(row["stress_haircut"]),
                "annual_yield": float(row["annual_yield"]),
                "source": row["source"],
                "note": row["note"],
            }
    return assets


def load_portfolios(path: str | Path) -> Dict[str, dict]:
    """Read the portfolio table into ``{id: {"name": str, "weights": {...}}}``."""
    portfolios: Dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            pid = row["portfolio_id"]
            entry = portfolios.setdefault(
                pid, {"name": row["portfolio_name"], "weights": {}}
            )
            entry["weights"][row["asset_id"]] = float(row["weight"])
    return portfolios


def effective_ratio(asset: Mapping[str, float]) -> float:
    """Same-day realisable share, net of the stress haircut."""
    return asset["same_day_ratio"] - asset["stress_haircut"]


def same_day_available(
    weights: Mapping[str, float],
    assets: Mapping[str, dict],
    circulation: float = CIRCULATION,
) -> float:
    """Weighted same-day realisable amount for one portfolio."""
    total = sum(weight * effective_ratio(assets[aid]) for aid, weight in weights.items())
    return total * circulation


def on_time_available(
    weights: Mapping[str, float],
    assets: Mapping[str, dict],
    circulation: float = CIRCULATION,
) -> float:
    """Cumulative same-day plus next-business-day realisable amount."""
    total = sum(
        weight
        * max(
            0.0,
            min(1.0, asset["same_day_ratio"] + asset.get("next_day_ratio", 0.0))
            - asset["stress_haircut"],
        )
        for aid, weight in weights.items()
        for asset in (assets[aid],)
    )
    return total * circulation


def portfolio_yield(
    weights: Mapping[str, float], assets: Mapping[str, dict]
) -> float:
    """Weighted annualised yield of the portfolio."""
    return sum(
        weight * assets[aid]["annual_yield"] for aid, weight in weights.items()
    )


def coverage(
    available: float, shock_rate: float, circulation: float = CIRCULATION
) -> float:
    """Requests covered by the supplied liquidity amount per shock unit."""
    requested = shock_rate * circulation
    if requested <= 0:
        return float("inf")
    return available / requested


def on_time_rate(
    on_time: float, shock_rate: float, circulation: float = CIRCULATION
) -> float:
    """Share of requested value settled by the end of the next business day.

    Unlike ``coverage``, this is capped at 1.0: paying more than was
    requested is not "more on time".
    """
    requested = shock_rate * circulation
    if requested <= 0:
        return 1.0
    return min(1.0, on_time / requested)


def gap_and_flag(
    available: float, shock_rate: float, circulation: float = CIRCULATION
) -> tuple[float, int]:
    """Return the SD+T+1 shortfall and breach flag for one shock level."""
    requested = shock_rate * circulation
    gap = max(0.0, requested - available)
    return gap, int(gap > 1e-12)


def failure_point(on_time: float, circulation: float = CIRCULATION) -> float:
    """Redemption rate at which SD+T+1 coverage falls to 100%."""
    return on_time / circulation


def validate_weights(
    portfolios: Mapping[str, dict], assets: Mapping[str, dict]
) -> None:
    """Raise if weights do not sum to 1 or reference an unknown asset."""
    for pid, entry in portfolios.items():
        total = sum(entry["weights"].values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Portfolio {pid!r} weights sum to {total:.6f}, expected 1.0"
            )
        for aid in entry["weights"]:
            if aid not in assets:
                raise KeyError(
                    f"Portfolio {pid!r} references unknown asset {aid!r}"
                )


def draw_shock(nominal: float, sigma: float, size: int, rng) -> np.ndarray:
    """Draw realised redemption shocks around a nominal level.

    A lognormal draw is used so that shocks stay positive and are
    right-skewed. The median of the draw equals ``nominal``.
    """
    return nominal * rng.lognormal(mean=0.0, sigma=sigma, size=size)


def monte_carlo(
    portfolios: Mapping[str, dict],
    assets: Mapping[str, dict],
    shock_rates,
    n_runs: int = 1000,
    sigma: float = 0.25,
    seed: int = 42,
) -> list[dict]:
    """Run each (portfolio, nominal shock) pair across ``n_runs`` draws.

    Returns one summary row per pair, with the coverage distribution and
    the probability that coverage falls below 100%.
    """
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    for pid, entry in portfolios.items():
        available = on_time_available(entry["weights"], assets)
        for nominal in shock_rates:
            draws = draw_shock(nominal, sigma, n_runs, rng)
            coverage_draws = available / draws
            gap_draws = np.maximum(0.0, draws - available)
            on_time_draws = np.minimum(1.0, coverage_draws)
            rows.append(
                {
                    "portfolio_id": pid,
                    "shock_rate": f"{nominal:.2f}",
                    "n_runs": n_runs,
                    "sigma": f"{sigma:.2f}",
                    "coverage_mean": f"{coverage_draws.mean():.4f}",
                    "coverage_p05": f"{np.percentile(coverage_draws, 5):.4f}",
                    "coverage_p50": f"{np.percentile(coverage_draws, 50):.4f}",
                    "coverage_p95": f"{np.percentile(coverage_draws, 95):.4f}",
                    "failure_prob": f"{(coverage_draws < 1.0).mean():.4f}",
                    "gap_mean": f"{gap_draws.mean():.4f}",
                    "on_time_mean": f"{on_time_draws.mean():.4f}",
                }
            )
    return rows
