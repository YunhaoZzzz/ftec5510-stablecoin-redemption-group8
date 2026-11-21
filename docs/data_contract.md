# Data Contract

This file defines the three tables, their fields, meanings and units. The implementation in step 2 follows this contract exactly. Field names may not be changed unilaterally.

## 1. `data/params_assets.csv`

Parameters for reserve assets. One row per asset class.

| Field | Type | Meaning | Unit |
|---|---|---|---|
| `asset_id` | string | Asset code, referenced by `portfolios.csv` | — |
| `asset_name_cn` | string | Asset name | — |
| `same_day_ratio` | float | Share realisable same-day under normal conditions; the liquidity factor analogous to an LCR haircut | 0–1 |
| `settle_days` | int | Days required to realise and settle | days |
| `stress_haircut` | float | Additional deduction under stress, default 0 | 0–1 |
| `annual_yield` | float | Annualised yield | decimal, 0.04 = 4% |
| `source` | string | "Team assumption" or a specific source | — |
| `note` | string | Free-form note | — |

Effective ratio = `same_day_ratio - stress_haircut`.

## 2. `data/portfolios.csv`

Portfolio weights. One row per (portfolio, asset) pair.

| Field | Type | Meaning | Unit |
|---|---|---|---|
| `portfolio_id` | string | Portfolio code: A / B / C | — |
| `portfolio_name` | string | Display name | — |
| `asset_id` | string | Asset code | — |
| `weight` | float | Weight of the asset in the portfolio | 0–1 |

Weights for the same `portfolio_id` must sum to 1.

## 3. `outputs/results.csv` (generated in step 2)

One row per (portfolio, shock rate, rule).

| Field | Type | Meaning | Unit |
|---|---|---|---|
| `portfolio_id` | string | Portfolio code | — |
| `shock_rate` | float | Redemption shock as a share of circulation | 0–1 |
| `rule` | string | Redemption rule: `fcfs` or `pro_rata` | — |
| `same_day_available` | float | Liquidity available on the day | same unit as circulation |
| `coverage_ratio` | float | Coverage = same-day available / redemption requests | — |
| `gap` | float | Shortfall when coverage is below 100% | same unit as circulation |
| `failure_flag` | int | 1 if coverage is below 100%, otherwise 0 | — |
| `portfolio_yield` | float | Portfolio annualised yield | decimal |

## 4. `outputs/mc_results.csv` (generated in step 2)

Monte Carlo summary. One row per (portfolio, nominal shock rate). Each row
summarises 1000 draws of the realised redemption shock around the nominal
level, using a lognormal distribution with median equal to the nominal rate
and `sigma = 0.25`.

| Field | Type | Meaning |
|---|---|---|
| `portfolio_id` | string | Portfolio code |
| `shock_rate` | float | Nominal redemption shock |
| `n_runs` | int | Number of draws per scenario |
| `sigma` | float | Standard deviation parameter of the lognormal draw |
| `coverage_mean` | float | Mean coverage across draws |
| `coverage_p05` | float | 5th percentile of coverage |
| `coverage_p50` | float | Median coverage |
| `coverage_p95` | float | 95th percentile of coverage |
| `failure_prob` | float | Share of draws with coverage below 100% |
| `gap_mean` | float | Mean shortfall across draws |

## Mapping to the Basel III LCR

| This project | Basel III LCR |
|---|---|
| `same_day_ratio` | Liquidity factor applied to HQLA (the complement of the haircut) |
| `same_day_available` | HQLA after haircuts |
| `coverage_ratio` | LCR numerator / denominator |
| One business day horizon | 30-day horizon |
| Licensed stablecoin issuer | Bank |

The structure is analogous, but the horizon and the reporting entity differ. This project therefore calls its metric an "intraday liquidity coverage ratio" rather than LCR.
