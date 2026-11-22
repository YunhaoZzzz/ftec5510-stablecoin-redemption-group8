# 数据契约

本文件定义四张表的字段、含义与单位。代码严格按此实现，两人不得单方面改动字段名。

## 1. `data/params_assets.csv`

储备资产的参数表，一行代表一类资产。

| 字段 | 类型 | 含义 | 单位 |
|---|---|---|---|
| `asset_id` | 字符串 | 资产代码，供 `portfolios.csv` 引用 | — |
| `asset_name_cn` | 字符串 | 资产中文名称 | — |
| `same_day_ratio` | 浮点 | 团队假设的 SD 可变现比例 | 0–1 |
| `next_day_ratio` | 浮点 | 团队假设的额外 T+1 可变现比例 | 0–1 |
| `settle_days` | 整数 | 变现并完成结算所需天数 | 天 |
| `stress_haircut` | 浮点 | 压力情形下的额外扣减，默认 0 | 0–1 |
| `annual_yield` | 浮点 | 年化收益率 | 小数，0.04 表示 4% |
| `source` | 字符串 | 参数来源，写具体出处或「团队假设」 | — |
| `note` | 字符串 | 备注 | — |

同日有效可动用比例 = `max(0, same_day_ratio - stress_haircut)`。
一工作日有效可动用比例 = `max(0, min(1, same_day_ratio + next_day_ratio) - stress_haircut)`。

## 2. `data/portfolios.csv`

组合权重表，一行代表「某组合持有某类资产的权重」。

| 字段 | 类型 | 含义 | 单位 |
|---|---|---|---|
| `portfolio_id` | 字符串 | 组合代码：A / B / C | — |
| `portfolio_name` | 字符串 | 组合名称 | — |
| `asset_id` | 字符串 | 资产代码 | — |
| `weight` | 浮点 | 该资产在组合中的权重 | 0–1 |

同一个 `portfolio_id` 下的权重之和必须为 1。

## 3. `outputs/results.csv`（由 `run.py` 生成）

一行代表「某组合 × 某冲击档位 × 某兑付规则」的确定性结果。

| 字段 | 类型 | 含义 |
|---|---|---|
| `portfolio_id` | 字符串 | 组合代码 |
| `shock_rate` | 浮点 | 赎回冲击率，占流通量的比例 |
| `rule` | 字符串 | 兑付规则：`fcfs` 或 `pro_rata` |
| `same_day_available` | 浮点 | 同日可变现金额，占流通量的比例 |
| `on_time_available` | 浮点 | SD + T+1 累计可变现额，占流通量比例 |
| `coverage_ratio` | 浮点 | 一工作日覆盖率 = `on_time_available / shock_rate` |
| `on_time_rate` | 浮点 | SD+T+1 内完成兑付的比例，上限为 1.0 |
| `gap` | 浮点 | 覆盖率不足 100% 时的缺口 |
| `failure_flag` | 整数 | 覆盖率低于 100% 时为 1 |
| `portfolio_yield` | 浮点 | 组合年化收益率 |

## 4. `outputs/mc_results.csv`（由 `run.py` 生成）

蒙特卡洛汇总。一行代表「某组合 × 某名义冲击档位」，汇总 1000 次抽样。流动性分母使用 SD+T+1 cumulative。

抽样方式：对数正态分布，中位数等于名义冲击率，`sigma = 0.25`。

| 字段 | 类型 | 含义 |
|---|---|---|
| `portfolio_id` | 字符串 | 组合代码 |
| `shock_rate` | 浮点 | 名义赎回冲击率 |
| `n_runs` | 整数 | 每个情景的抽样次数 |
| `sigma` | 浮点 | 对数正态分布的标准差参数 |
| `coverage_mean` | 浮点 | 覆盖率的均值 |
| `coverage_p05` | 浮点 | 覆盖率的 5% 分位数 |
| `coverage_p50` | 浮点 | 覆盖率的中位数 |
| `coverage_p95` | 浮点 | 覆盖率的 95% 分位数 |
| `failure_prob` | 浮点 | 覆盖率低于 100% 的抽样比例 |
| `gap_mean` | 浮点 | 平均缺口 |
| `on_time_mean` | 浮点 | 一个工作日内完成兑付比例的平均值 |

## 与 Basel III LCR 的对应关系

| 本项目 | Basel III LCR |
|---|---|
| `same_day_ratio` | SD 流动性比例（团队假设） |
| `same_day_available` | SD 可动用金额 |
| `coverage_ratio` | SD+T+1 可动用金额 ÷ 赎回请求 |
| 期限为一个工作日 | 期限为 30 天 |
| 主体为持牌稳定币发行人 | 主体为银行 |

本项目的加权思路与 LCR 有相似处，但时间窗口、参数及主体均不同，不直接自称 LCR。

## 5. 报告专用输入与输出（A–E）

报告模型和 demo 使用不同文件，避免相同的 A/B/C 代码产生歧义。

### `data/report_params_assets.csv`

每行是一个「参数情形 × 资产」组合，共 central / conservative / optimistic 三种情形、九类资产。`annual_yield` 为小数；`same_day_ratio`、`next_day_ratio`、`later_ratio` 均为 0–1 比例，三者之和必须为 1。`eligible` 是报告的资格假设（1 合规，0 不合规或仅作反事实）。报告未提供压力折扣，此模型不加折扣。

### `data/report_portfolios.csv`

报告 A–E 持仓权重；字段形式与 demo 权重表相同，但 ID 只在报告模型中解释。每个组合权重合计为 1。不要把本表替代 `data/portfolios.csv`。

### 报告输出

| 文件 | 内容 |
|---|---|
| `outputs/report_portfolio_summary.csv` | 五个组合的表 4 主要汇总值及是否匹配标记 |
| `outputs/report_table4_comparison.csv` | 表 4 每项报告值、复算值、差异及报告精度匹配标记 |
| `outputs/report_scenario_results.csv` | 3 情形 × 5 组合 × 4 冲击档位的确定性结果；金额比例以流通量为基准 |
| `outputs/report_mc_results.csv` | 同一情景网格的蒙特卡洛汇总；每格 1,000 次，固定种子 42、sigma=0.25 |
| `outputs/report_portfolio_liquidity.png` | 报告 A–E central 与 conservative 流动性、收益率图 |

使用 `python -m src.run_report` 生成 CSV，再用 `python -m src.plot_report_results` 生成图。该模型的失败概率仍是设定分布下的模拟结果，不是实际违约概率。
