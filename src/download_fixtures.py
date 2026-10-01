from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://fixturedownload.com/download/nations-league-2026-UTC.csv"
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def download_fixtures():
    request = Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    content = urlopen(request).read()
    if content.lstrip().lower().startswith(b"<!doctype html"):
        raise ValueError(f"Expected a CSV file but got an HTML page from {URL}")
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    target = FIXTURES_DIR / f"nations_league_2026_{date.today().isoformat()}.csv"
    target.write_bytes(content)
    print(f"{target.name}: {target.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    download_fixtures()