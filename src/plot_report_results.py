"""Plot report A–E central liquidity, yield, and conservative T+1 capacity."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "outputs" / "report_portfolio_summary.csv"
    with source.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit("Run python -m src.run_report before plotting report results")

    labels = [row["portfolio_id"] for row in rows]
    x = np.arange(len(labels))
    width = 0.23
    central_sd = [float(row["central_sd_pct"]) for row in rows]
    central_t1 = [float(row["central_t1_pct"]) for row in rows]
    conservative_sd = [float(row["conservative_sd_pct"]) for row in rows]
    conservative_t1 = [float(row["conservative_t1_pct"]) for row in rows]
    yields = [float(row["portfolio_yield_pct"]) for row in rows]
    colors = ["#3b82f6" if row["eligibility"] == "Compliant" else "#d97706" for row in rows]

    fig, (ax, ax_yield) = plt.subplots(2, 1, figsize=(10.5, 8.0), sharex=True,
                                       gridspec_kw={"height_ratios": [2.1, 1]})
    ax.bar(x - width / 2, central_sd, width, label="Central · SD", color="#60a5fa")
    ax.bar(x + width / 2, central_t1, width, label="Central · SD + T+1", color="#1d4ed8")
    ax.scatter(x, conservative_t1, marker="D", s=60, color="#dc2626",
               label="Conservative · SD + T+1", zorder=4)
    for index, (sd, t1, cons) in enumerate(zip(central_sd, central_t1, conservative_t1)):
        ax.text(index - width / 2, sd + 1.2, f"{sd:g}%", ha="center", fontsize=8)
        ax.text(index + width / 2, t1 + 1.2, f"{t1:g}%", ha="center", fontsize=8)
        ax.text(index, cons - 5.0, f"{cons:g}%", ha="center", va="top", fontsize=8, color="#991b1b")
    ax.set_ylabel("Available reserves (% of circulation)")
    ax.set_ylim(0, 108)
    ax.set_title("Report portfolios A–E: same-day and T+1 liquidity")
    ax.grid(axis="y", alpha=0.22)
    ax.legend(ncol=3, loc="upper right", fontsize=8)

    ax_yield.bar(x, yields, color=colors, width=0.52)
    for index, value in enumerate(yields):
        ax_yield.text(index, value + 0.06, f"{value:.2f}%", ha="center", fontsize=9)
    ax_yield.set_ylabel("Portfolio yield (% p.a.)")
    ax_yield.set_xticks(x, labels)
    ax_yield.set_xlabel("Report portfolio (orange E is a non-compliant counterfactual)")
    ax_yield.set_ylim(0, max(yields) + 0.5)
    ax_yield.grid(axis="y", alpha=0.22)

    fig.text(0.01, 0.01, "Inputs are assumptions from Reserve Portfolio Design Tables 2–3; results reproduce the report, not observed redemption performance.", fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = root / "outputs" / "report_portfolio_liquidity.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out.relative_to(root)}")


if __name__ == "__main__":
    main()
