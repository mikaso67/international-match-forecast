import numpy as np
import pandas as pd

from src.database import ROOT, query
from src.evaluation import OUTCOMES, calibration_table, evaluate
from src.models.elo_logistic import EloLogistic
from src.models.poisson import PoissonModel, rolling_predict
from src.splits import load_matches
from src.tournament import actual_progress, load_config, simulate_tournament

APP_DATA_DIR = ROOT / "app" / "data"


def match_history():
    return query("""
        SELECT date, home_team, away_team, home_score, away_score, neutral
        FROM clean_results
        ORDER BY date, match_id
    """)


def world_cup_backtest(history):
    config = load_config("world_cup_2026")
    model = PoissonModel().fit(history, config["start_date"])
    forecast = simulate_tournament(config, model, n_sims=10_000, seed=42)
    actual = actual_progress(config, "2026-07-19")
    return forecast.join(actual.add_prefix("reached_")).rename_axis("team").reset_index()


def test_scores(history):
    matches = load_matches()
    fit_set = matches[matches["split"] != "test"]
    test = matches[matches["split"] == "test"]
    frequencies = fit_set.groupby("neutral")["result"].value_counts(normalize=True).unstack()[OUTCOMES]
    probs = {
        "uniform": np.full((len(test), 3), 1 / 3),
        "frequency_by_venue": frequencies.reindex(test["neutral"]).to_numpy(),
        "elo_logistic": EloLogistic().fit(fit_set).predict_proba(test),
        "poisson": rolling_predict(lambda: PoissonModel(), history, test),
    }
    scores = pd.DataFrame({name: evaluate(p, test["result"]) for name, p in probs.items()}).T
    scores["n_matches"] = len(test)
    calibration = pd.concat(
        [calibration_table(probs["poisson"], test["result"], outcome).assign(outcome=outcome) for outcome in OUTCOMES]
    )
    predictions = test[["date", "home_team", "away_team", "tournament", "result"]].reset_index(drop=True)
    for name in ["frequency_by_venue", "elo_logistic", "poisson"]:
        for k, outcome in enumerate(OUTCOMES):
            predictions[f"{name}_{outcome}"] = probs[name][:, k]
    return scores.rename_axis("model").reset_index(), calibration, predictions


def export():
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    history = match_history()
    world_cup_backtest(history).to_csv(APP_DATA_DIR / "world_cup_2026_backtest.csv", index=False, float_format="%.4f")
    scores, calibration, predictions = test_scores(history)
    scores.to_csv(APP_DATA_DIR / "test_scores.csv", index=False, float_format="%.4f")
    calibration.to_csv(APP_DATA_DIR / "test_calibration.csv", index=False, float_format="%.4f")
    predictions.to_csv(APP_DATA_DIR / "test_predictions.csv", index=False, float_format="%.4f")
    print(f"App data written to {APP_DATA_DIR}")


if __name__ == "__main__":
    export()
