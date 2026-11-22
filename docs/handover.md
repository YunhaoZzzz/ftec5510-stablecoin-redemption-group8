# 交接说明

本说明写给接手 `src/` 的第二位开发同学。基线引擎与蒙特卡洛已经完成，可以独立往下做。

## 1. 每个文件负责什么

| 文件 | 负责内容 |
|---|---|
| `data/params_assets.csv` | 资产参数：同日可动用比例、变现结算天数、压力扣减、年化收益率、来源 |
| `data/portfolios.csv` | 组合权重，一行代表「某组合持有某资产的权重」 |
| `src/engine.py` | 读取数据、同日流动性、覆盖率、当日完成率、缺口、失败点、蒙特卡洛 |
| `src/run.py` | 跑情景矩阵，输出 `outputs/results.csv` 与 `outputs/mc_results.csv` |
| `tests/test_engine.py` | 验收测试，目前 6 个 |
| `outputs/results.csv` | 确定性结果，不提交到仓库（见 `.gitignore`） |
| `outputs/mc_results.csv` | 蒙特卡洛汇总：覆盖率分位数、失败概率、当日完成率 |

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
3. 图表 —— 三张图：组合对照、失败点曲线、收益率—流动性前沿；另建议加一张失败概率热力图。
4. 参数复核 —— 把 `gov_bond_1y` 的占位收益率换成 364 天外汇基金票据的中标收益率。
5. （选做）Streamlit 页面。

**归属**：从这一刻起 `src/` 归接手方维护。交接人不再向 `src/` 提交，只负责文档与截图。

## 8. 与《Reserve Portfolio Design》的差异（交接时需知）

`Reserve_Portfolio_Design_Group8.docx` 是储备组合的支撑报告。它规定的是**组合怎么设计**，不是分配规则的回测——分配规则在第 5 节只作为正交维度被提及一次。

当前代码只实现了这份报告的一小部分，两者有四处实质差异：

| 项目 | 支撑报告 | 当前代码 |
|---|---|---|
| 组合数量 | 5 组（A–E） | 3 组（A–C） |
| 资产类别 | 9 类 | 4 类 |
| 参数情形 | central / conservative / optimistic | 只有一套 |
| 流动性阶梯 | SD / T+1 / later 三档 | 只有同日比例 |
| on-time 口径 | SD + T+1 累计 | 仅同日 |
| 冲击档位 | 5 / 20 / 50 / 80 | 20 / 40 / 60 / 80 / 100 |

### 需要知道的一处：on-time 的口径

指引第 3.3.3 段要求「收到请求后的一个工作日内处理」。今天收到的请求，最晚可以在下一个工作日完成结算。

支撑报告据此把当日可兑付能力定义为 **SD + T+1 累计**（见表 4 的 "T+1 cumulative (on-time ceiling)"），而当前代码只用了同日比例。

也就是说，**现在的模型偏严格**——它假设所有兑付都必须在当天完成。改过来之后，同样组合的覆盖率会变高。

### demo 阶段：不需要改数据

当前的三组组合、四类资产、单一参数已经足够支撑一次完整的演示：能对比、能算失败点、能出分布。把数据扩到九类资产、五组组合、三套参数属于**报告阶段的完整化工作**，demo 不做也不影响讲述。

如果演示时被问到口径，可以这样回答：

> 我们采用的是更严格的口径，只计当日可成交的部分，所以数字低于支撑报告中 T+1 累计的口径。

### 如果要与支撑报告完全对齐（报告阶段）

按这个顺序做：

1. `src/engine.py`：新增 `on_time_available = Σ w × (same_day_ratio + next_day_ratio)`，原 `same_day_available` 保留做诊断指标。
2. `data/params_assets.csv`：扩到支撑报告表 2 的 9 类资产，每类加入 `next_day_ratio` 与 `later_ratio`，并按 central / conservative / optimistic 三套取值。
3. `data/portfolios.csv`：换成支撑报告表 3 的五组权重（A–E）。
4. `src/run.py`：增加「参数情形」维度，循环三个 case。
5. `tests/test_engine.py`：92 / 80 / 68 这些断言会失效，按新口径重算。

### 一个提醒

如果执行上面的对齐，现在文档和截图里的 92% / 80% / 68%、失败概率矩阵、收益率数值**全部会变**。这是口径变化导致的，不是算出错。
