# Work Division

Two developers, split by module rather than by chapter.

## A — Framework and engine

| Requirement | Deliverable | Definition of done |
|---|---|---|
| Repository and directory structure | This repository | Clones and runs without extra setup |
| Field contract for the three tables | `docs/data_contract.md` | Field names, meanings and units fixed |
| Asset parameters and portfolio configuration | `data/params_assets.csv`, `data/portfolios.csv` | Loadable by the code |
| Asset model and same-day liquidity | `src/engine.py` | Given a portfolio, returns same-day available amount and coverage |
| Gap and failure point | `src/engine.py` | Given a shock rate, returns the gap and the failure point |
| End-to-end minimal case | Run output | 80/20 portfolio at 80% shock, verifiable by hand |
| CLI entry point | `src/run.py` | Runs with no arguments |
| Handover note | `docs/handover.md` | B can continue independently |

After these items are complete, `src/` is handed over to B.

## B — Rules and presentation

| Requirement | Deliverable | Definition of done |
|---|---|---|
| Redemption rules | `src/rules.py` | One result each for `fcfs` and `pro_rata` |
| Batch run | `outputs/results.csv` | Covers 3 portfolios × 5 shock rates × 2 rules |
| Portfolio yield | Same file | Weighted sum of asset yields |
| Charts | `outputs/` | Portfolio comparison, failure-point curve, trade-off frontier |
| Parameter source review | `data/params_assets.csv` | Every parameter has a source or an explicit assumption note |
| README and run instructions | `README.md` | A new member can follow it and run |
| (Optional) Streamlit page | `app.py` | Adjust parameters and see charts update |
