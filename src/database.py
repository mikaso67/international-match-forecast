from pathlib import Path

import duckdb

from src.elo import build_elo

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "matches.duckdb"
SQL_DIR = ROOT / "sql"
STEPS = ["01_load_raw.sql", "02_clean.sql", "03_team_form.sql", build_elo,
         "04_opponent_strength.sql"]
TABLES = ["raw_results", "raw_goalscorers", "excluded_teams", "clean_results",
          "team_matches", "team_form", "elo_ratings", "team_opponent_strength"]


def connect(read_only=False):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=read_only)
    con.execute(f"SET file_search_path = '{ROOT.as_posix()}'")
    return con


def run_sql_file(con, name):
    con.execute((SQL_DIR / name).read_text(encoding="utf-8"))


def query(sql):
    with connect(read_only=True) as con:
        return con.sql(sql).df()


def build_database():
    with connect() as con:
        for step in STEPS:
            if isinstance(step, str):
                run_sql_file(con, step)
                print(f"Ran {step}")
            else:
                step(con)
                print(f"Ran {step.__name__}")
        for table in TABLES:
            n_rows = con.sql(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {n_rows} rows")


if __name__ == "__main__":
    build_database()