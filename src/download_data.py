from pathlib import Path
from urllib.request import urlretrieve

DATA_COMMIT = "394fe81893b062fbc2cf6257e988ac7cc4c039a1"
BASE_URL = f"https://raw.githubusercontent.com/martj42/international_results/{DATA_COMMIT}"
FILES = ["results.csv", "shootouts.csv", "former_names.csv"]
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def download_all():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = RAW_DIR / name
        urlretrieve(f"{BASE_URL}/{name}", target)
        print(f"{name}: {target.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    download_all()