"""Interactive Streamlit front end for the stablecoin redemption demo."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.engine import (  # noqa: E402
    coverage,
    gap_and_flag,
    load_assets,
    load_portfolios,
    on_time_available,
    on_time_rate,
    portfolio_yield,
    same_day_available,
    validate_weights,
)
from src.rules import allocate  # noqa: E402


st.set_page_config(page_title="稳定币 T+1 兑付模拟", page_icon="💧", layout="wide")
st.title("稳定币储备与 T+1 兑付韧性")
st.caption("交互式 demo：调整资产流动性假设、组合权重和赎回冲击，即时查看兑付与分配结果。")


@st.cache_data
def load_inputs():
    assets = load_assets(ROOT / "data" / "params_assets.csv")
    portfolios = load_portfolios(ROOT / "data" / "portfolios.csv")
    return assets, portfolios


base_assets, base_portfolios = load_inputs()
asset_rows = []
for asset_id, asset in base_assets.items():
    asset_rows.append({"asset_id": asset_id, **asset})
asset_df = pd.DataFrame(asset_rows)
weight_rows = []
for portfolio_id, entry in base_portfolios.items():
    for asset_id, weight in entry["weights"].items():
        weight_rows.append({
            "portfolio_id": portfolio_id,
            "portfolio_name": entry["name"],
            "asset_id": asset_id,
            "weight": weight,
        })
weight_df = pd.DataFrame(weight_rows)

with st.expander("调整资产参数与组合权重", expanded=False):
    st.markdown("SD、T+1、压力扣减和收益率均可编辑；组合权重需要在每个组合内合计为 100%。")
    edited_assets = st.data_editor(
        asset_df,
        hide_index=True,
        width="stretch",
        disabled=["asset_id", "asset_name_cn", "settle_days", "source", "note"],
        column_config={
            "same_day_ratio": st.column_config.NumberColumn("SD 比例", min_value=0.0, max_value=1.0, step=0.01, format="%.2f"),
            "next_day_ratio": st.column_config.NumberColumn("T+1 增量比例", min_value=0.0, max_value=1.0, step=0.01, format="%.2f"),
            "stress_haircut": st.column_config.NumberColumn("压力扣减", min_value=0.0, max_value=1.0, step=0.01, format="%.2f"),
            "annual_yield": st.column_config.NumberColumn("年化收益率", min_value=-1.0, max_value=1.0, step=0.001, format="%.3%"),
        },
        key="asset_parameters",
    )
    edited_weights = st.data_editor(
        weight_df,
        hide_index=True,
        width="stretch",
        disabled=["portfolio_id", "portfolio_name", "asset_id"],
        column_config={
            "weight": st.column_config.NumberColumn("组合权重", min_value=0.0, max_value=1.0, step=0.01, format="%.2f"),
        },
        key="portfolio_weights",
    )

assets = {}
for _, row in edited_assets.iterrows():
    assets[row["asset_id"]] = {
        "asset_name_cn": row["asset_name_cn"],
        "same_day_ratio": float(row["same_day_ratio"]),
        "next_day_ratio": float(row["next_day_ratio"]),
        "settle_days": int(row["settle_days"]),
        "stress_haircut": float(row["stress_haircut"]),
        "annual_yield": float(row["annual_yield"]),
        "source": row["source"],
        "note": row["note"],
    }
portfolios = {pid: {"name": entry["name"], "weights": {}} for pid, entry in base_portfolios.items()}
for _, row in edited_weights.iterrows():
    portfolios[row["portfolio_id"]]["weights"][row["asset_id"]] = float(row["weight"])
try:
    validate_weights(portfolios, assets)
except (ValueError, KeyError) as exc:
    st.error(f"输入未通过校验：{exc}。请检查组合权重总和及资产代码。")
    st.stop()

portfolio_ids = list(portfolios)
name_map = {pid: f"Demo {pid} · {portfolios[pid]['name']}" for pid in portfolio_ids}
with st.sidebar:
    st.header("模拟设置")
    selected = st.selectbox("查看组合", portfolio_ids, format_func=lambda pid: name_map[pid])
    shock = st.slider("赎回请求 / 流通量", min_value=5, max_value=120, value=80, step=5) / 100
    rule = st.radio("同日资金分配规则", ["fcfs", "pro_rata"], format_func=lambda r: "FCFS · 先到先得" if r == "fcfs" else "Pro-rata · 按比例")
    st.caption("持有人请求结构为示例假设，可调整后查看分配变化。")
    h1 = st.slider("H1 请求占比", 0, 100, 50)
    h2 = st.slider("H2 请求占比", 0, 100, 30)
    h3 = st.slider("H3 请求占比", 0, 100, 20)

share_total = h1 + h2 + h3
if share_total == 0:
    st.warning("至少给一位持有人设置正的请求占比。")
    st.stop()
shares = [h1 / share_total, h2 / share_total, h3 / share_total]
entry = portfolios[selected]
same_day = same_day_available(entry["weights"], assets)
on_time = on_time_available(entry["weights"], assets)
yield_rate = portfolio_yield(entry["weights"], assets)
requests = [shock * share for share in shares]
allocations = allocate(rule, same_day, requests)
gap, failed = gap_and_flag(on_time, shock)
timely = on_time_rate(on_time, shock)

metric_cols = st.columns(4)
metric_cols[0].metric("SD 同日可用", f"{same_day:.1%}")
metric_cols[1].metric("SD + T+1 可用", f"{on_time:.1%}")
metric_cols[2].metric("一工作日完成率", f"{timely:.1%}")
metric_cols[3].metric("组合假设年化收益", f"{yield_rate:.2%}")
st.write(f"当前情景：{shock:.0%} 赎回冲击 · {name_map[selected]} · {'未覆盖' if failed else '覆盖'} · SD+T+1 缺口 {gap:.1%}")

allocation_df = pd.DataFrame({
    "持有人": ["H1", "H2", "H3"],
    "请求金额 / 流通量": requests,
    "同日分配": allocations,
    "SD 后延迟": [request - paid for request, paid in zip(requests, allocations)],
})
st.subheader("同日请求分配")
st.dataframe(allocation_df.style.format("{:.1%}", subset=allocation_df.columns[1:]), hide_index=True, width="stretch")
st.caption("分配规则作用于 SD 同日可用金额。SD 后延迟的请求仍可能由 T+1 资金在一个工作日内结算。H1/H2/H3 是模拟持有人，不代表真实用户数据。")

shocks = np.linspace(0.05, 1.20, 24)
curve_data = {}
summary_rows = []
for pid, portfolio in portfolios.items():
    sd_amount = same_day_available(portfolio["weights"], assets)
    t1_amount = on_time_available(portfolio["weights"], assets)
    annual_yield = portfolio_yield(portfolio["weights"], assets)
    curve_data[f"Demo {pid} · SD"] = [on_time_rate(sd_amount, x) for x in shocks]
    curve_data[f"Demo {pid} · SD + T+1"] = [on_time_rate(t1_amount, x) for x in shocks]
    summary_rows.append({
        "组合": name_map[pid],
        "同日可用": sd_amount,
        "SD + T+1 上限": t1_amount,
        "假设年化收益": annual_yield,
    })

chart_cols = st.columns(2)
with chart_cols[0]:
    st.subheader("完成率与赎回冲击")
    curve_df = pd.DataFrame(curve_data, index=(shocks * 100).round(0).astype(int))
    curve_df.index.name = "赎回冲击 (%)"
    st.line_chart(curve_df, y_label="完成率", width="stretch")
with chart_cols[1]:
    st.subheader("收益率—同日流动性")
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for pid, row in zip(portfolio_ids, summary_rows):
        x = row["同日可用"] * 100
        y = row["假设年化收益"] * 100
        ax.scatter(x, y, s=90)
        ax.annotate(f"Demo {pid}", (x, y), xytext=(6, 6), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Same-day liquidity (% of circulation)")
    ax.set_ylabel("Assumed annual yield (%)")
    ax.grid(alpha=0.25)
    st.pyplot(fig, width="stretch")
    plt.close(fig)

st.subheader("组合对照")
st.dataframe(pd.DataFrame(summary_rows).style.format({
    "同日可用": "{:.1%}", "SD + T+1 上限": "{:.1%}", "假设年化收益": "{:.2%}"
}), hide_index=True, width="stretch")
st.info("基础 T+1 梯度是团队假设，可在上方展开编辑。当前 demo 的组合权重与报告 A–E 不同；编辑参数后的结果仅用于情景探索。")
