# 稳定币储备与 T+1 兑付韧性

FTEC5510 Advanced Financial Infrastructure · Group 8

本项目用可复现的情景分析和蒙特卡洛模拟，比较 demo 储备组合在赎回冲击下的同日流动性、一个工作日内兑付能力与收益率，并展示 FCFS 和 pro-rata 如何分配有限的同日资金。

> **组合标签说明：** 本仓库 demo 的 A/B/C 是现金与一年内政府债券的 80/20、50/50、20/80 配置；它们与《Reserve Portfolio Design》报告中的 A–E 完全不同。下文结果只针对 demo A/B/C。

## 本轮完成内容

- 将 on-time 口径改为 SD（同日）+ T+1（下一个工作日）累计可变现能力；同日金额仍单独保留作诊断。
- 实现 FCFS（先到先得）和 pro-rata（按请求比例分配）规则。规则分配同日流动性，SD 后尚未支付的请求仍可能在 T+1 内完成。
- 扩展情景矩阵至 3 个组合 × 5 档冲击 × 2 种规则，共 30 行；另输出 90 行示例持有人分配明细。
- 生成 4 张结果图；运行测试套件，9 项测试全部通过。
- 用金管局 2026 年 11 月 17 日 Y2697（364 天）外汇基金票据招标的平均中标收益率 3.31% 更新国债收益率代理值。
- 新增 Streamlit 交互页面，可调整流动性参数、组合权重、冲击规模和分配规则并即时查看结果。

## 当前 demo 结果

| Demo 组合 | 现金 / 一年内国债 | SD 可用 | SD + T+1 上限 | 假设年化收益 | 80% 冲击下 MC 失败概率* |
|---|---:|---:|---:|---:|---:|
| A · 保守 | 80% / 20% | 92% | 100% | 0.66% | 17.5% |
| B · 中性 | 50% / 50% | 80% | 100% | 1.66% | 19.5% |
| C · 收益导向 | 20% / 80% | 68% | 100% | 2.65% | 20.9% |

确定性情景下，三个 demo 组合都能覆盖最多 100% 流通量的请求；超过同日可用额的部分依赖 T+1。*失败概率是给定名义冲击后的条件概率，使用每情景 1,000 次对数正态抽样（`sigma = 0.25`、固定随机种子），不是无条件违约概率。

## 结果图表

> 本仓库也包含报告专用模型 A–E，和本节 demo A/B/C 是两套独立输入。报告模型结果见后文“报告组合复现”。

### 同日流动性与一工作日上限

![Demo A/B/C 的同日可用额与 SD+T+1 上限](outputs/portfolio_liquidity_comparison.png)

### 赎回冲击下的完成率与失败点

虚线显示同日完成率，实线显示 SD+T+1 完成率。当前 T+1 参数假设使三个组合的一工作日上限均为 100%；组合间的差异主要体现在同日流动性。

![赎回冲击与 SD、SD+T+1 完成率曲线](outputs/failure_point_curves.png)

### 收益率—流动性权衡

横轴使用**同日**可变现比例，以保留组合之间的即时流动性差异；点旁标注的一工作日上限均为 100%。

![Demo 组合收益率与同日流动性](outputs/yield_liquidity_frontier.png)

### 蒙特卡洛失败概率

![各组合在不同名义冲击下的条件失败概率](outputs/failure_probability_heatmap.png)

## 报告组合复现（A–E）

按《Reserve Portfolio Design》表 2–3 独立录入九类资产、central / conservative / optimistic 三套 SD / T+1 / later 阶梯，以及报告 A–E 权重。该模型与 demo 的 A/B/C 分开保存，不会覆盖 demo 数据。报告表 4 中组合收益率、Central 流动性、Conservative 流动性和资格分类均按报告显示精度复现；五个组合均匹配。近似失败点按报告的 5 个百分点档位复现。

| 报告组合 | 现金占比 | 年化收益率 | Central SD | Central SD+T+1 | Conservative SD | Conservative SD+T+1 | 资格 |
|---|---:|---:|---:|---:|---:|---:|---|
| A | 40% | 2.38% | 84.0% | 99.0% | 74.0% | 94.0% | 合规 |
| B | 20% | 2.89% | 72.0% | 97.0% | 57.0% | 87.0% | 合规 |
| C | 12% | 3.20% | 38.4% | 82.4% | 25.2% | 56.0% | 合规 |
| D | 5% | 3.38% | 59.5% | 92.5% | 42.3% | 77.0% | 合规 |
| E | 5% | 3.75% | 39.0% | 67.5% | 27.5% | 52.5% | 不合规反事实 |

![报告组合 A–E 的流动性与收益率](outputs/report_portfolio_liquidity.png)

`outputs/report_table4_comparison.csv` 提供表 4 每项指标的报告值、复算值及差异；`outputs/report_scenario_results.csv` 是三套情形 × 五组合 × 四档赎回冲击（5/20/50/80%）的确定性结果；`outputs/report_mc_results.csv` 对同一情景矩阵给出每个格子 1,000 次蒙特卡洛结果。Table 2 没有压力折扣参数，复现时不额外加入折扣。表 4 的 Conservative failure point 是报告近似值，按 5 个百分点档位记录；例如 E 的 52.5% T+1 累计值对应报告约 50%。

## 运行方法

在仓库根目录运行：

```bash
pip install -r requirements.txt
python -m src.run
python -m src.plot_results
python -m src.run_report
python -m src.plot_report_results
python -m unittest discover -s tests -v
```

`src.run` 和 `src.plot_results` 更新 demo 结果；`src.run_report` 与 `src.plot_report_results` 更新报告 A–E 结果及图表。测试目前共 12 项。

### Streamlit 交互页面

```bash
pip install -r requirements-app.txt
streamlit run app.py
```

页面可编辑 SD/T+1 比例、压力扣减、年化收益率和组合权重，设置赎回冲击、FCFS/pro-rata 规则及示例持有人占比，并即时查看同日分配、完成率曲线和收益率—同日流动性图。

## 输入与假设

- `data/portfolios.csv` 保存 demo A/B/C 的权重；每个组合权重和必须为 1。
- `data/params_assets.csv` 保存同日比例、T+1 比例、压力扣减、收益率、来源和说明。
- `data/report_params_assets.csv` 保存报告九类资产在三种情形下的 SD/T+1/later 阶梯、收益率及资格；`data/report_portfolios.csv` 保存报告 A–E 权重。
- 原 demo 参数没有 T+1 梯度。本轮把存款和一年内国债未能同日变现的部分，以及隔夜逆回购剩余部分假设为 T+1 可用；这些是团队假设，不是监管参数或实测结算数据。当前每类资产的 SD + T+1 比例合计为 100%，所以三个组合的 T+1 上限均为 100%。
- 持有人结构 H1/H2/H3 分别占总请求的 50%/30%/20%，只用于展示规则分配差别，不代表真实用户数据。
- `gov_bond_1y` 的收益率使用金管局 2026-11-17 招标、Y2697（364 天）的平均中标收益率 3.31% 作代理值；[金管局招标结果](https://www.hkma.gov.hk/eng/news-and-media/press-releases/2026/11/20261117-4/)。这替代了此前 HIBOR 1M 占位值。债券/票据收益率只是简化代理，不能视作任一具体持仓的实际回报。

## 建议的后续工作

1. 用可核查的数据或团队校准依据验证 T+1 比例，并至少比较保守、中央、乐观情形；当前所有组合 T+1 上限都是 100%，使一工作日确定性失败点无法区分组合。
2. 如果报告需要统一结果，再单独扩展报告 A–E、九类资产和三套参数情形；不要把报告 A–E 与 demo A/B/C 混为一套。
3. 若要研究队列公平性或 run dynamics，可增加真实或明确假设的持有人请求分布、到达顺序和逐日结算过程。当前规则模块只分配给定时点的同日可用资金。
4. 后续每次更新外汇基金票据或利率参数时，记录招标/观察日期并重新生成 `outputs/` 结果与图表。

## 项目边界

这是基于公开材料和明示假设的研究模拟，不连接实时数据或银行系统，不代表任何具名发行人的实际储备组合，也不能据此推断真实发行人的违约概率。
