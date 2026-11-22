# 交接说明

本说明写给接手 `src/` 的第二位开发同学。基线引擎与蒙特卡洛已经完成，可以独立往下做。

## 1. 每个文件负责什么

| 文件 | 负责内容 |
|---|---|
| `data/params_assets.csv` | 资产参数：SD/T+1 可动用比例、变现结算天数、压力扣减、年化收益率、来源 |
| `data/portfolios.csv` | 组合权重，一行代表「某组合持有某资产的权重」 |
| `src/engine.py` | 读取数据、SD 与 SD+T+1 流动性、覆盖率、缺口、失败点、蒙特卡洛 |
| `src/rules.py` | FCFS 与 pro-rata 请求分配 |
| `src/run.py` | 跑情景矩阵，输出确定性、分配明细与蒙特卡洛 CSV |
| `src/plot_results.py` | 从 CSV 生成四张 PNG 图 |
| `tests/test_engine.py` | 9 项验收测试 |
| `outputs/results.csv` | 30 行确定性结果 |
| `outputs/allocation_results.csv` | 90 行示例持有人分配结果 |
| `outputs/mc_results.csv` | 蒙特卡洛汇总：覆盖率分位数、失败概率、T+1 内完成率 |

## 2. 结果字段的含义

| 字段 | 含义 |
|---|---|
| `portfolio_id` | 组合代码：A / B / C |
| `shock_rate` | 赎回冲击率，占流通量的比例 |
| `rule` | 兑付规则：`fcfs` 或 `pro_rata` |
| `same_day_available` | 同日可变现金额，占流通量的比例 |
| `on_time_available` | SD + T+1 累计可变现金额，占流通量的比例 |
| `coverage_ratio` | `on_time_available / shock_rate` |
| `on_time_rate` | `min(1, coverage_ratio)`，即一个工作日内完成的比例 |
| `gap` | `max(0, shock_rate - on_time_available)` |
| `failure_flag` | 覆盖率低于 100% 时为 1 |
| `portfolio_yield` | 组合加权年化收益率 |

兑付规则改变的是**谁**拿到同日流动性，不改变 SD+T+1 总可兑付额。`allocation_results.csv` 用示例持有人请求（H1/H2/H3 分别占冲击额 50%/30%/20%）展示同日分配与 SD 后延迟金额；延迟金额仍可能在 T+1 内完成。该持有人结构是示例假设，不是观察数据。确定性总量表会在两种规则下重复相同的 SD+T+1 总量。

## 3. 怎么新增一种资产

1. 在 `data/params_assets.csv` 里新增一行，给一个新的 `asset_id`。
2. 在 `data/portfolios.csv` 里给相关组合加上它的权重。
3. 确认每个组合的权重加总仍然是 1。
4. 运行 `python -m src.run` 和 `python -m unittest discover -s tests -v`。

不需要改代码：引擎是对组合里出现的资产求和。

## 4. 怎么新增一种兑付规则

1. 在 `src/rules.py` 中为每种规则实现一个函数。
2. 函数接收「同日可用金额」与「请求列表」，返回每个持有人分到的金额。
3. 按持有人类型汇总被延后的金额。
4. 把规则名写进 `outputs/results.csv` 的 `rule` 列。
5. 加一个测试，断言分配总额等于 `min(available, total_requests)`。

建议先做两种规则：

- `fcfs`：按提交时间排序，依次满足，直到可用金额用完。
- `pro_rata`：每笔请求按 `available / total_requests` 的比例分配。

## 5. 已知限制

- 所有金额都按流通量等于 1.0 做归一化。
- `gov_bond_1y` 的年化收益率已替换为 HKMA 2026-11-17 招标、Y2697（364 天）外汇基金票据的平均中标收益率 3.31% p.a.；来源与代理说明见 `data/params_assets.csv`。
- 存款、债券与逆回购的同日可动用比例都是团队假设，不是监管规定。
- 模型以一个工作日为单位，暂时没有日内时序。
- 当前 demo 的 T+1 ladder 是团队假设：存款与一年内国债的未变现部分假设在 T+1 到账；隔夜逆回购剩余部分假设最迟在下一个工作日到账。详见 `data/params_assets.csv`。
- 报告组合 A–E 的参数与权重未移植到 demo；demo A/B/C 仍指原现金/国债 80/20、50/50、20/80 组合。

## 6. 常用命令

```bash
python -m src.run
python -m unittest discover -s tests -v
```

Streamlit 页面（先安装 `requirements-app.txt`）：

```bash
streamlit run app.py
```

## 7. 接手后的执行顺序

按这个顺序做。详细要求见 `docs/work_division.md`。

1. `src/rules.py` —— 已实现并测试 `fcfs` 与 `pro_rata`，断言分配总额等于 `min(available, total_requests)`。
2. 批量运行 —— 已覆盖三组合 × 五档冲击 × 两种规则，共 30 行；持有人分配明细另存为 90 行。
3. 图表 —— 已生成组合流动性对照、SD 与 SD+T+1 完成率曲线、收益率—同日流动性图，以及蒙特卡洛失败概率热力图。
4. 参数复核 —— 已换成 2026-11-17 Y2697 364 天外汇基金票据平均中标收益率（3.31% p.a.）。
5. （选做）Streamlit 页面 —— 已新增 `app.py`，可编辑参数和组合权重并即时查看结果；依赖见 `requirements-app.txt`。

**归属**：从这一刻起 `src/` 归接手方维护。交接人不再向 `src/` 提交，只负责文档与截图。

## 8. 与《Reserve Portfolio Design》的差异（优先处理）

`Reserve_Portfolio_Design_Group8.docx` 是储备组合的支撑报告。它规定的是**组合怎么设计**，不是分配规则的回测——分配规则在第 5 节只作为正交维度被提及一次。

当前代码只实现了这份报告的一小部分，两者有四处实质差异：

| 项目 | 支撑报告 | 当前代码 |
|---|---|---|
| 组合数量 | 5 组（A–E） | 3 组（A–C） |
| 资产类别 | 9 类 | 4 类 |
| 参数情形 | central / conservative / optimistic | 只有一套 |
| 流动性阶梯 | SD / T+1 / later 三档，三套情形 | demo 输入 SD / T+1 两档、单套假设 |
| on-time 口径 | SD + T+1 累计 | SD + T+1 累计（新增） |
| 冲击档位 | 5 / 20 / 50 / 80 | 20 / 40 / 60 / 80 / 100 |

### 最需要先处理的一处：on-time 的口径

指引第 3.3.3 段要求「收到请求后的一个工作日内处理」。今天收到的请求，最晚可以在下一个工作日完成结算。

支撑报告据此把一工作日内可兑付能力定义为 **SD + T+1 累计**（见表 4 的 "T+1 cumulative (on-time ceiling)"）。当前引擎已按此口径处理 on-time rate、coverage、gap、failure point 和 Monte Carlo；同日金额仍作为诊断字段单独输出。

demo 原参数没有 T+1 ladder，因此新增的未变现部分是团队假设，见 `data/params_assets.csv`，不是从报告表 2 直接导入。按当前假设，demo A/B/C 的 SD+T+1 ceiling 均为 100%；报告 A–E 的表 4 结果不会与 demo 直接对应。

### 建议的改动顺序

1. `data/params_assets.csv`：已为现有四类 demo 资产增加 `next_day_ratio`；未移植报告中的九类资产和三套参数情形。
2. `data/portfolios.csv`：保留 demo 的 A/B/C 权重，没有替换成报告 A–E。
3. `src/engine.py`：已新增 `on_time_available = Σ w × (SD + T+1)`，原 `same_day_available` 保留做诊断指标。
4. 报告要求的 A–E、central/conservative/optimistic 全量组合模型仍未纳入本次前三项范围。
5. 当前 demo 组合的 T+1 ceiling 在本组假设下均为 100%，因此 T+1 失败点相同；SD 诊断仍呈现组合差异。

### 一个提醒

口径更新后，92% / 80% / 68% 的同日可用比例和组合收益率保持不变；一工作日可用上限、覆盖率、缺口、失败标记及 Monte Carlo 结果则按 SD+T+1 重新计算。若同日比例仍显示这三个旧值，这是诊断字段，不是口径遗漏。

本轮前三项已完成。后续如需让 demo 与支撑报告的组合分析一致，应另行扩充资产、组合和参数情形；参数扩充后应同步重跑结果并更新图表。
