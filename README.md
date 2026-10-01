# International Match Forecast

Probabilistic forecasting of international football matches and tournaments, built with SQL (DuckDB), statistical goal models and Monte Carlo simulation.

Work in progress. Current state:

- Data pipeline in SQL, from raw results to pre-match features, with an automatic leakage check.
- Models compared on 2022-2023 validation data: Elo logistic baseline, Poisson goal model, Dixon-Coles, gradient boosting and stacking. Poisson is the final model.
- 2026 World Cup backtest: forecast made with data up to 10 June 2026, compared with the actual tournament.
- 2026-27 Nations League: dated forecasts in `reports/forecasts/`, published before the November matches.

## Run

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.download_data
python -m src.database
python -m src.forecast_nations_league
```