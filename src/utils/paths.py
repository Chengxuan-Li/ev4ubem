"""Repository-relative paths. Import these instead of hard-coding absolute paths."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
EXTERNAL = DATA / "external"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
SAMPLES = DATA / "samples"
METADATA = ROOT / "metadata"
MANIFESTS = METADATA / "manifests"
SCHEMAS = METADATA / "schemas"
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"
MAPS = RESULTS / "maps"

# Study-area constants
NY_STATE_FIPS = "36"
TOMPKINS_COUNTY_FIPS = "109"  # full GEOID 36109
TOMPKINS_COUNTY_NAME = "TOMPKINS"


def ensure(*dirs: Path) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
