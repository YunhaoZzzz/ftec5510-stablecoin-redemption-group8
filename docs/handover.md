# Handover Note / 交接说明

> English version first, Chinese version follows. 英文版在前，中文版在后。

---

# English

Written for the second developer taking over `src/` after the baseline engine is complete.

## 1. What each file does

| File | Responsibility |
|---|---|
| `data/params_assets.csv` | Asset parameters: same-day realisable share, settlement days, stress haircut, annual yield, source |
| `data/portfolios.csv` | Portfolio weights, one row per (portfolio, asset) pair |
| `src/engine.py` | Loading, same-day liquidity, coverage, gap, failure point, Monte Carlo |
| `src/run.py` | Runs the scenario matrix and writes `outputs/results.csv` |
| `tests/test_engine.py` | Acceptance tests for the baseline numbers |
| `outputs/results.csv` | Generated output; not committed (see `.gitignore`) |
| `outputs/mc_results.csv` | Monte Carlo summary: coverage percentiles and failure probability |

## 2. What the result fields mean

| Field | Meaning |
|---|---|
| `portfolio_id` | Portfolio code: A / B / C |
| `shock_rate` | Redemption shock as a share of circulation |
| `rule` | Redemption rule. Currently `baseline`; the rules module will add `fcfs` and `pro_rata` |
| `same_day_available` | Same-day realisable amount, as a share of circulation |
| `coverage_ratio` | `same_day_available / shock_rate` |
| `on_time_rate` | `min(1, coverage_ratio)`; the share of requested value settled within the day |
| `gap` | `max(0, shock_rate - same_day_available)` |
| `failure_flag` | 1 when coverage is below 100% |
| `portfolio_yield` | Weighted annualised yield of the portfolio |

A redemption rule changes **who** receives the available liquidity, not the total. The aggregate columns above are therefore already valid and do not need to be recomputed when rules are added.

## 3. How to add an asset class

1. Add a row to `data/params_assets.csv` with a new `asset_id`.
2. Add its weight to each relevant portfolio in `data/portfolios.csv`.
3. Make sure the weights still sum to 1 for every portfolio.
4. Run `python -m src.run` and `python -m unittest discover -s tests -v`.

No code change is needed: the engine sums over whatever assets a portfolio references.

## 4. How to add a redemption rule

1. Create `src/rules.py` with one function per rule.
2. The function takes the same-day available amount and the list of requests, and returns the allocated amount per holder.
3. Aggregate the deferred amount by holder type.
4. Write the rule name into the `rule` column of `outputs/results.csv`.
5. Add a test asserting that total allocated equals `min(available, total_requests)`.

Suggested first two rules:

- `fcfs`: sort requests by submission time and fill until the available amount is exhausted.
- `pro_rata`: allocate `available / total_requests` of each request.

## 5. Known limitations

- All amounts are normalised so that circulation equals 1.0.
- `annual_yield` for `gov_bond_1y` is a placeholder based on the HIBOR 1M fixing; replace it with the 364-day Exchange Fund Bill tender yield when available.
- Same-day ratios for deposits, bonds and reverse repo are team assumptions, not regulatory values.
- The model works at the level of one business day; there is no intraday timing yet.
- `src/rules.py` does not exist yet.

## 6. Commands

```bash
python -m src.run
python -m unittest discover -s tests -v
```

## 7. Next steps for the receiving developer

Work in this order. Detailed requirements are in `docs/work_division.md`.

1. `src/rules.py` — implement `fcfs` and `pro_rata`, and add a test asserting that total allocation equals `min(available, total_requests)`.
2. Batch run — extend `src/run.py` to loop over both rules; `results.csv` grows from 15 rows to 30.
3. Charts — three figures: portfolio comparison, failure-point curve, and the yield-liquidity frontier.
4. Parameter review — replace the placeholder yield for `gov_bond_1y` with the 364-day Exchange Fund Bill tender yield.
5. (Optional) Streamlit page.

**Ownership.** From this point `src/` belongs to the receiving developer. The handover author should stop committing to `src/` and work on docs and screenshots only.

---

# 中文版

本说明写给接手 `src/` 的第二位开发同学。基线引擎已经完成，可以独立往下做。

## 1. 每个文件负责什么

| 文件 | 负责内容 |
|---|---|
| `data/params_assets.csv` | 资产参数：同日可动用比例、变现结算天数、压力扣减、年化收益率、来源 |
| `data/portfolios.csv` | 组合权重，一行代表「某组合持有某资产的权重」 |
| `src/engine.py` | 读取数据、同日流动性、覆盖率、缺口、失败点、蒙特卡洛 |
| `src/run.py` | 跑情景矩阵，输出 `outputs/results.csv` |
| `tests/test_engine.py` | 基线数字的验收测试 |
| `outputs/results.csv` | 生成的结果，不提交到仓库（见 `.gitignore`） |
| `outputs/mc_results.csv` | 蒙特卡洛汇总：覆盖率分位数与失败概率 |

## 2. 结果字段的含义

| 字段 | 含义 |
|---|---|
| `portfolio_id` | 组合代码：A / B / C |
| `shock_rate` | 赎回冲击率，占流通量的比例 |
| `rule` | 兑付规则。目前是 `baseline`，规则模块会加入 `fcfs` 与 `pro_rata` |
| `same_day_available` | 同日可变现金额，占流通量的比例 |
| `coverage_ratio` | `same_day_available / shock_rate` |
| `on_time_rate` | `min(1, coverage_ratio)`，即当日完成兑付的比例 |
| `gap` | `max(0, shock_rate - same_day_available)` |
| `failure_flag` | 覆盖率低于 100% 时为 1 |
| `portfolio_yield` | 组合加权年化收益率 |

兑付规则改变的是**谁**拿到这笔流动性，不改变可兑付总额。所以上面这些总量字段在加入规则后不需要重算。

## 3. 怎么新增一种资产

1. 在 `data/params_assets.csv` 里新增一行，给一个新的 `asset_id`。
2. 在 `data/portfolios.csv` 里给相关组合加上它的权重。
3. 确认每个组合的权重加总仍然是 1。
4. 运行 `python -m src.run` 和 `python -m unittest discover -s tests -v`。

不需要改代码：引擎是对组合里出现的资产求和。

## 4. 怎么新增一种兑付规则

1. 新建 `src/rules.py`，每种规则写一个函数。
2. 函数接收「同日可用金额」与「请求列表」，返回每个持有人分到的金额。
3. 按持有人类型汇总被延后的金额。
4. 把规则名写进 `outputs/results.csv` 的 `rule` 列。
5. 加一个测试，断言分配总额等于 `min(available, total_requests)`。

建议先做两种规则：

- `fcfs`：按提交时间排序，依次满足，直到可用金额用完。
- `pro_rata`：每笔请求按 `available / total_requests` 的比例分配。

## 5. 已知限制

- 所有金额都按流通量等于 1.0 做归一化。
- `gov_bond_1y` 的年化收益率是基于 HIBOR 1M 的占位值，拿到 364 天外汇基金票据中标收益率后应替换。
- 存款、债券与逆回购的同日可动用比例都是团队假设，不是监管规定。
- 模型以一个工作日为单位，暂时没有日内时序。
- `src/rules.py` 尚未创建。

## 6. 常用命令

```bash
python -m src.run
python -m unittest discover -s tests -v
```

## 7. 接手后的执行顺序

按这个顺序做。详细要求见 `docs/work_division.md`。

1. `src/rules.py` —— 实现 `fcfs` 与 `pro_rata`，并加一个测试，断言分配总额等于 `min(available, total_requests)`。
2. 批量运行 —— 扩展 `src/run.py`，循环两种规则；`results.csv` 从 15 行变成 30 行。
3. 图表 —— 三张图：组合对照、失败点曲线、收益率—流动性前沿。
4. 参数复核 —— 把 `gov_bond_1y` 的占位收益率换成 364 天外汇基金票据的中标收益率。
5. （选做）Streamlit 页面。

**归属**：从这一刻起 `src/` 归接手方维护。交接人不再向 `src/` 提交，只负责文档与截图。
