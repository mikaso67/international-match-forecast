# International Match Forecast

Probabilistic forecasting of international football matches and tournaments, built with SQL (DuckDB), statistical goal models and Monte Carlo simulation.

Work in progress. Current state:

- Data pipeline in SQL, from raw results to pre-match features, with an automatic leakage check.
- Models compared on 2022-2023 validation data: Elo logistic baseline, Poisson goal model, Dixon-Coles, gradient boosting and stacking. Poisson is the final model.
- 2026 World Cup backtest: forecast made with data up to 10 June 2026, compared with the actual tournament.
- 2026-27 Nations League: final forecast made on 8 October 2026 with results up to 6 October, before matchdays 5 and 6 (12-17 November). See `reports/forecasts/nations_league_2026_*_2026-10-07.csv`.

## Run

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.download_data
python -m src.database
python -m src.forecast_nations_league
```