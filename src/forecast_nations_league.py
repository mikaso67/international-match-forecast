import pandas as pd

from src.database import ROOT, query
from src.evaluation import OUTCOMES
from src.fixtures import load_fixtures, played_matches
from src.models.poisson import PoissonModel
from src.tournament import load_config, simulate_league

FORECAST_DIR = ROOT / "reports" / "forecasts"
KEYS = ["date", "home_team", "away_team"]


def training_history(played):
    history = query("""
        SELECT date, home_team, away_team, home_score, away_score, neutral
        FROM clean_results
        ORDER BY date, match_id
    """)
    already_in_history = history.merge(played[KEYS], on=KEYS, how="left", indicator=True)["_merge"] == "both"
    return pd.concat([history[~already_in_history.to_numpy()], played[history.columns]], ignore_index=True)


def forecast(config_name="nations_league_2026", n_sims=10_000, seed=42):
    config = load_config(config_name)
    fixtures = load_fixtures(config)
    played = played_matches(fixtures)
    as_of = played["date"].max() + pd.Timedelta(days=1)
    model = PoissonModel().fit(training_history(played), as_of)

    standings = simulate_league(fixtures, model, n_sims=n_sims, seed=seed)
    remaining = fixtures[fixtures["home_score"].isna()].reset_index(drop=True)
    home_goals, away_goals = model.expected_goals(remaining)
    matches = remaining[["date", "group", "home_team", "away_team"]].assign(
        home_goals=home_goals, away_goals=away_goals,
        **dict(zip([f"p_{outcome}" for outcome in OUTCOMES], model.predict_proba(remaining).T)),
    )

    FORECAST_DIR.mkdir(parents=True, exist_ok=True)
    stamp = as_of.date().isoformat()
    standings.to_csv(FORECAST_DIR / f"{config_name}_standings_{stamp}.csv", index=False, float_format="%.4f")
    matches.to_csv(FORECAST_DIR / f"{config_name}_matches_{stamp}.csv", index=False, float_format="%.4f")
    print(f"Forecast as of {stamp} from {config['fixtures']}: {len(played)} played, {len(remaining)} remaining")
    return standings, matches


if __name__ == "__main__":
    forecast()