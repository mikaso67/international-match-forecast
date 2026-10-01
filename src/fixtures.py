import pandas as pd

from src.database import ROOT

FIXTURES_DIR = ROOT / "data" / "fixtures"


def load_fixtures(config):
    fixtures = pd.read_csv(FIXTURES_DIR / config["fixtures"])
    fixtures = fixtures.replace({"Home Team": config["team_names"], "Away Team": config["team_names"]})
    scores = fixtures["Result"].str.split(" - ", expand=True).astype(float)
    return pd.DataFrame({
        "date": pd.to_datetime(fixtures["Date"], format="%d/%m/%Y %H:%M").dt.normalize(),
        "home_team": fixtures["Home Team"],
        "away_team": fixtures["Away Team"],
        "group": fixtures["Group"].str.replace("Group ", ""),
        "home_score": scores[0],
        "away_score": scores[1],
        "neutral": False,
    }).sort_values("date").reset_index(drop=True)


def played_matches(fixtures):
    played = fixtures.dropna(subset=["home_score"])
    return played.assign(home_score=played["home_score"].astype(int), away_score=played["away_score"].astype(int))