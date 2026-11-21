# Handover Note

Written for the second developer taking over `src/` after the baseline engine is complete.

## 1. What each file does

| File | Responsibility |
|---|---|
| `data/params_assets.csv` | Asset parameters: same-day realisable share, settlement days, stress haircut, annual yield, source |
| `data/portfolios.csv` | Portfolio weights, one row per (portfolio, asset) pair |
| `src/engine.py` | Loading, same-day liquidity, coverage, gap, failure point |
| `src/run.py` | Runs the scenario matrix and writes `outputs/results.csv` |
| `tests/test_engine.py` | Acceptance tests for the baseline numbers |
| `outputs/results.csv` | Generated output; not committed (see `.gitignore`) |

## 2. What the result fields mean

| Field | Meaning |
|---|---|
| `portfolio_id` | Portfolio code: A / B / C |
| `shock_rate` | Redemption shock as a share of circulation |
| `rule` | Redemption rule. Currently `baseline`; the rules module will add `fcfs` and `pro_rata` |
| `same_day_available` | Same-day realisable amount, expressed as a share of circulation |
| `coverage_ratio` | `same_day_available / shock_rate` |
| `gap` | `max(0, shock_rate - same_day_available)` |
| `failure_flag` | 1 when coverage is below 100% |
| `portfolio_yield` | Weighted annualised yield of the portfolio |

Note on the `rule` column: a redemption rule changes **who** receives the available liquidity, not the total. The aggregate columns above are therefore already valid and do not need to be recomputed when rules are added.

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
