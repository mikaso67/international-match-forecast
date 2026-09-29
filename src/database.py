from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "processed" / "matches.duckdb"
SQL_DIR = ROOT / "sql"


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


if __name__ == "__main__":
    with connect() as con:
        for path in sorted(SQL_DIR.glob("*.sql")):
            run_sql_file(con, path.name)
            print(f"Ran {path.name}")
        for table in ["raw_results", "excluded_teams", "clean_results"]:
            n_rows = con.sql(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {n_rows} rows")
