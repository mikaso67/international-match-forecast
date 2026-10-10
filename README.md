# International Match Forecast

I estimate the probability of each result in international football matches, then simulate whole tournaments to get the chance of each team reaching each round. The data pipeline is in SQL (DuckDB), the models are statistical goal models compared with machine learning baselines, and every forecast is published before the games so it can be checked afterwards.

Live app: [international-match-forecast.streamlit.app](https://international-match-forecast.streamlit.app/)

This is a sports analytics and statistics project. It uses no betting odds and is not meant for gambling.

## Results

### Match model, test set

2,583 matches played from January 2024 to August 2026, never used to choose or tune a model. Lower is better for all metrics.

| Model | Log loss | Brier | RPS |
|---|---|---|---|
| One third each | 1.0986 | 0.6667 | 0.2372 |
| Past frequencies (home, away, neutral) | 1.0538 | 0.6352 | 0.2256 |
| Elo rating + logistic regression | 0.8649 | 0.5098 | 0.1658 |
| **Poisson goal model (final)** | **0.8448** | **0.4963** | **0.1602** |

Other models tested on the same matches (log loss): gradient boosting 0.8652, Dixon-Coles 0.8432, stacking 0.8478.

The Poisson model beats Elo by 0.020 log loss per match. On paired match-level differences, the standard error is 0.0048, so the gap is about 4 standard errors. Dixon-Coles and stacking are within noise of Poisson, so I kept the simplest model that also gives a full score distribution, which the tournament simulation needs.

### 2026 World Cup backtest

On 10 June 2026, with data up to that day, I simulated the 48-team tournament 10,000 times.

- The final was played by the two teams the model rated most likely to reach it: Argentina (26%) and Spain (21%). Spain won as the second favourite (13%).
- The four semi-finalists all had a higher chance of getting there than the four other quarter-finalists.
- Biggest misses: Uruguay, out in the groups with an 89% chance of going through, and Brazil, beaten by Norway in the last 16.
- The Brier score of the round-by-round probabilities beats a naive forecast at every round.

### 2026-27 Nations League

Forecast published on 8 October 2026 with every result up to 6 October, before matchdays 5 and 6 (12 to 17 November): final standings probabilities for all groups of leagues A to D, and win, draw and loss probabilities for every remaining game. Files: `reports/forecasts/nations_league_2026_*_2026-10-07.csv`.

## What I take from it

- A team strength model built only on past scores already does most of the work. Boosting on the same information did not beat a two-parameter Elo model.
- Modelling goals rather than results is what made the difference, and it gives score probabilities for free.
- The probabilities are well calibrated for home and away wins. Draws are slightly underestimated between evenly matched teams.
- Knockout football is noisy: even a clear favourite rarely has more than 20% chance of winning a World Cup.

## Data

- Results: [martj42/international_results](https://github.com/martj42/international_results), pinned to commit `394fe81`, about 49,000 men's international matches since 1872 with goalscorers.
- I keep FIFA members only (111 regional and non-FIFA sides removed) and rebuild scores at 90 minutes by removing extra-time goals. 47,095 matches remain.
- Nations League fixtures: fixturedownload.com.
- Split by time: train 2000-2021, validation 2022-2023, test 2024 onwards.

## Method

1. **SQL pipeline (DuckDB).** Raw tables, cleaning, then pre-match features with window functions: recent form, Elo rating, strength of recent opponents. Each feature only uses games played before the match.
2. **Leakage check.** I rebuild the features with the data cut at a past date and check that every feature before that date is identical.
3. **Baselines.** Uniform, past frequencies, then Elo with a multinomial logistic regression.
4. **Goal model.** Poisson regression with an attack and a defence strength per team and home advantage, recent games weighted more (half-life two years, eight-year window), refitted every month.
5. **Comparisons.** Dixon-Coles correction, gradient boosting, stacking. Evaluated with log loss, Brier score, ranked probability score and calibration, then once on the test set.
6. **Simulation.** Monte Carlo over the real tournament formats and tie-breakers. Knockout draws go to extra time (expected goals divided by three), then to penalties, treated as 50/50 since the data shows no clear edge for the stronger team.

## Limits

- The model only sees results: no line-ups, injuries, player ratings or travel.
- Friendlies and competitive games get the same weight, although teams do not always play at full strength in friendlies.
- Small teams with few games against strong opponents have uncertain strengths.
- Penalty shootouts are a coin flip in the model.

## Repository

```
configs/            tournament formats (World Cup 2026, Nations League 2026)
sql/                DuckDB pipeline: load, clean, form, opponent strength, features
src/                data download, database build, Elo, evaluation, simulation, forecasts
src/models/         Elo logistic, Poisson, Dixon-Coles, gradient boosting
notebooks/          exploration, features, baselines, goal models, boosting, simulation, test
reports/forecasts/  published forecasts, dated
reports/figures/    calibration plots
app/                Streamlit app and the small CSV files it reads
data/               raw data and DuckDB database (not tracked)
```

## Run

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.download_data
python -m src.database
python -m src.leakage_check
python -m src.forecast_nations_league
```

App:

```
pip install -r app/requirements.txt
python -m src.export_app_data
streamlit run app/app.py
```

## Stack

Python 3.13, DuckDB, pandas, NumPy, SciPy, scikit-learn, Matplotlib, Streamlit, Altair.
