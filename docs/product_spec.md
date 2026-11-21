# Product Specification

## What this is

A stress-testing tool for comparing the reserve portfolios and redemption rules of stablecoin issuers. It answers one question:

> With 100% book reserve coverage, how much can an issuer realise on the same day under different portfolio mixes, and at what redemption pressure does settlement start to fall short?

## What it does

| Capability | Description |
|---|---|
| Portfolio same-day liquidity | Weights each asset by its realisable share to compute the same-day available amount and coverage |
| Failure-point analysis | Finds the redemption rate at which coverage falls below 100% |
| Portfolio comparison | Compares three portfolios with different risk appetites side by side |
| Rule comparison | First-come-first-served versus pro-rata, comparing the amount deferred |
| Yield trade-off | Portfolio annualised yield against same-day liquidity, forming a frontier |

## What it does not do

| Not included | Reason |
|---|---|
| Real-time monitoring | Issuer disclosure is weekly; access to real-time data is not assumed |
| Issuer API integration | The data is not available and it is out of scope |
| Prediction about a named institution | The tool compares rules and parameters, not institutions |
| Machine learning or model training | No training data; this is a parameterised simulation |
| Equity allocation analysis | Equities are not eligible reserve assets |

## Users

| User | Purpose |
|---|---|
| Issuer's ALM and risk team | Assess whether the reserve portfolio can meet redemption under stress |
| Regulatory researchers | Compare how different redemption rules allocate a liquidity shortfall |

## Typical workflow

1. Select a portfolio (A / B / C)
2. Select a redemption shock (20%–100%)
3. Select a redemption rule (FCFS / pro rata)
4. Read the result: same-day available amount, coverage, gap, failure flag
5. Switch one input and run again to compare

## Boundary statement

The tool is based on public regulatory text, public interest rates and team assumptions. It does not represent the actual reserve composition of any named issuer.
