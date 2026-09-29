import duckdb
import pandas as pd

from src.database import ROOT, SQL_DIR, run_sql_file
from src.elo import build_elo

CUTOFF = "2026-06-11"
FEATURE_STEPS = ["03_team_form.sql", build_elo, "04_opponent_strength.sql", "05_match_features.sql"]


def build_features(con):
    for step in FEATURE_STEPS:
        if isinstance(step, str):
            run_sql_file(con, step)
        else:
            step(con)
    return con.sql("SELECT * FROM match_features ORDER BY match_id").df()


def features_with_cutoff(cutoff):
    con = duckdb.connect()
    con.execute(f"SET file_search_path = '{ROOT.as_posix()}'")
    run_sql_file(con, "01_load_raw.sql")
    run_sql_file(con, "02_clean.sql")
    if cutoff is not None:
        con.execute(f"DELETE FROM clean_results WHERE date >= '{cutoff}'")
    return build_features(con)


if __name__ == "__main__":
    full = features_with_cutoff(None)
    truncated = features_with_cutoff(CUTOFF)
    full_before = full[full["date"] < pd.Timestamp(CUTOFF)].reset_index(drop=True)
    pd.testing.assert_frame_equal(full_before, truncated)
    print(f"No leakage: {len(truncated)} matches before {CUTOFF} have identical features.")