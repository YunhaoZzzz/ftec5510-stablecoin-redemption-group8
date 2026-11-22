"""Create presentation-ready PNG charts from generated result CSV files."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "outputs"
    out.mkdir(exist_ok=True)
    rows = read_csv(out / "results.csv")
    mc = read_csv(out / "mc_results.csv")
    portfolios = list(dict.fromkeys(r["portfolio_id"] for r in rows))
    colors = dict(zip(portfolios, ("#2563eb", "#0f766e", "#d97706")))
    labels = {"A": "Demo A · Conservative", "B": "Demo B · Balanced", "C": "Demo C · Yield-focused"}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    # Same-day vs regulatory T+1 ceiling portfolio comparison.
    base = {r["portfolio_id"]: r for r in rows if r["shock_rate"] == "0.20" and r["rule"] == "fcfs"}
    fig, ax = plt.subplots(figsize=(9.4, 5.1))
    x = np.arange(len(portfolios)); width = .34
    ax.bar(x-width/2, [float(base[p]["same_day_available"]) * 100 for p in portfolios], width, label="Same-day (SD)", color="#94a3b8")
    ax.bar(x+width/2, [float(base[p]["on_time_available"]) * 100 for p in portfolios], width, label="On-time ceiling (SD + T+1)", color="#2563eb")
    ax.set_xticks(x, [labels[p] for p in portfolios]); ax.set_ylabel("Share of circulation (%)"); ax.set_ylim(0, 110)
    ax.set_title("Demo portfolio liquidity: same-day and within one business day")
    ax.legend(frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(.5, -0.27))
    ax.grid(axis="y", alpha=.2); fig.tight_layout()
    fig.savefig(out/"portfolio_liquidity_comparison.png", dpi=180, bbox_inches="tight"); plt.close(fig)

    # On-time rate against redemption shocks, showing SD diagnostic and SD+T+1 measure.
    fig, ax = plt.subplots(figsize=(9.4, 5.1))
    for p in portfolios:
        rr = [r for r in rows if r["portfolio_id"] == p and r["rule"] == "fcfs"]
        rr.sort(key=lambda r: float(r["shock_rate"]))
        shocks = [float(r["shock_rate"]) * 100 for r in rr]
        sd = np.minimum(1, np.array([float(r["same_day_available"]) / float(r["shock_rate"]) for r in rr])) * 100
        t1 = [float(r["on_time_rate"]) * 100 for r in rr]
        ax.plot(shocks, sd, marker="o", linestyle="--", color=colors[p], alpha=.58, label=f"{labels[p]} · SD")
        ax.plot(shocks, t1, marker="o", color=colors[p], label=f"{labels[p]} · SD + T+1")
    ax.axhline(100, color="#111827", linewidth=1, alpha=.5)
    ax.set(xlabel="Redemption shock (% of circulation)", ylabel="Requests completed within timing window (%)", ylim=(-3, 106), title="Redemption completion vs shock size")
    ax.grid(alpha=.2); ax.legend(frameon=False, fontsize=8, ncol=2); fig.tight_layout()
    fig.savefig(out/"failure_point_curves.png", dpi=180, bbox_inches="tight"); plt.close(fig)

    # Yield vs same-day liquidity frontier. Annotate the T+1 ceiling separately.
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    for p in portfolios:
        row = base[p]
        xx = float(row["same_day_available"]) * 100; yy = float(row["portfolio_yield"]) * 100
        ax.scatter(xx, yy, s=115, color=colors[p], edgecolor="white", linewidth=1.2, zorder=3)
        ax.annotate(f"{labels[p]}\nT+1 ceiling {float(row['on_time_available']):.0%}", (xx, yy), xytext=(8, 8), textcoords="offset points", fontsize=8)
    ax.set(xlabel="Same-day realisable reserve (% of circulation)", ylabel="Assumed annual portfolio yield (%)", title="Yield and immediate liquidity trade-off · demo A/B/C")
    ax.grid(alpha=.22); fig.tight_layout()
    fig.savefig(out/"yield_liquidity_frontier.png", dpi=180, bbox_inches="tight"); plt.close(fig)

    # Monte Carlo conditional failure-probability heatmap.
    shocks = list(dict.fromkeys(r["shock_rate"] for r in mc))
    matrix = np.array([[float(next(r["failure_prob"] for r in mc if r["portfolio_id"] == p and r["shock_rate"] == s)) for s in shocks] for p in portfolios])
    fig, ax = plt.subplots(figsize=(8.3, 4.2))
    image = ax.imshow(matrix*100, cmap="YlOrRd", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(shocks)), [f"{float(s):.0%}" for s in shocks]); ax.set_yticks(range(len(portfolios)), [labels[p] for p in portfolios])
    ax.set(xlabel="Nominal redemption shock", title="Conditional failure probability · Monte Carlo")
    for i in range(len(portfolios)):
        for j in range(len(shocks)):
            ax.text(j, i, f"{matrix[i,j]:.0%}", ha="center", va="center", color="black", fontsize=9)
    fig.colorbar(image, ax=ax, label="Failure probability (%)", fraction=.045); fig.tight_layout()
    fig.savefig(out/"failure_probability_heatmap.png", dpi=180, bbox_inches="tight"); plt.close(fig)

    print("Created 4 charts in outputs/")


if __name__ == "__main__":
    main()
