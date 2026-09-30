import pandas as pd

from src.database import query

TRAIN_START = pd.Timestamp("2000-01-01")
VALID_START = pd.Timestamp("2022-01-01")
TEST_START = pd.Timestamp("2024-01-01")


def load_matches():
    matches = query(f"""
        SELECT * FROM match_features
        WHERE date >= '{TRAIN_START.date()}'
        ORDER BY date, match_id
    """)
    matches["split"] = "train"
    matches.loc[matches["date"] >= VALID_START, "split"] = "valid"
    matches.loc[matches["date"] >= TEST_START, "split"] = "test"
    return matches