from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "matches.duckdb"
SQL_DIR = ROOT / "sql"
RAW_TABLES = ["raw_results", "raw_shootouts", "raw_former_names"]


def connect(read_only=False):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH), read_only=read_only)
    con.execute(f"SET file_search_path = '{ROOT.as_posix()}'")
    return con


def run_sql_file(con, name):
    con.execute((SQL_DIR / name).read_text(encoding="utf-8"))


if __name__ == "__main__":
    with connect() as con:
        run_sql_file(con, "01_load_raw.sql")
        for table in RAW_TABLES:
            n_rows = con.sql(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {n_rows} rows")