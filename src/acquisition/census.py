"""Census ACS 5-year (2020-2024) tables and TIGER/Line geometries — no API key required.

The Census API now requires a key (registration), so this project uses the public
ACS *table-based summary files* (pipe-delimited, all geographies nationwide) and filters
them to New York geographies while streaming:

  https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-<table>.dat
  https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/documentation/Geos20245YR.txt

Kept summary levels (GEO_ID prefixes): 040 state, 050 county, 060 county subdivision,
140 tract, 150 block group, 160 place, 860 ZCTA (NY-range ZCTAs 10001-14999 kept).
Output: data/raw/census/acs5_2024/<table>_ny.parquet, geos_ny.parquet; TIGER zips in data/raw/census/tiger/.
"""
from __future__ import annotations

import argparse
import io

import pandas as pd
import requests

from src.utils.paths import RAW, ensure
from src.utils.provenance import UA, download, record, rel, sha256

ACS_BASE = "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF"
ACS_YEAR = "2024"

TABLES = {
    "b01003": "Total population",
    "b01002": "Median age by sex",
    "b11001": "Household type",
    "b11016": "Household type by household size",
    "b19001": "Household income in past 12 months (bins)",
    "b19013": "Median household income",
    "b25003": "Tenure",
    "b25024": "Units in structure",
    "b25032": "Tenure by units in structure",
    "b25044": "Tenure by vehicles available",
    "b08201": "Household size by vehicles available",
    "b25034": "Year structure built",
    "b25040": "House heating fuel",
    "b25077": "Median value (owner-occupied)",
    "b25118": "Tenure by household income",
    "b15003": "Educational attainment 25+",
    "b08301": "Means of transportation to work",
    "b08303": "Travel time to work",
    "b08302": "Time leaving home to go to work",
    "b08006": "Sex of workers by means of transportation (incl. worked from home)",
    "b25046": "Aggregate vehicles available by tenure",
    "b23025": "Employment status",
    "b14007": "School enrollment by level (college students)",
    "b26001": "Group quarters population",
}

KEEP_SUMLEVELS = ("0400000US36", "0500000US36", "0600000US36", "1400000US36", "1500000US36", "1600000US36")

TIGER = {
    "tl_2024_36_tract.zip": "https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_36_tract.zip",
    "tl_2024_36_bg.zip": "https://www2.census.gov/geo/tiger/TIGER2024/BG/tl_2024_36_bg.zip",
    "tl_2024_36_cousub.zip": "https://www2.census.gov/geo/tiger/TIGER2024/COUSUB/tl_2024_36_cousub.zip",
    "tl_2024_36_place.zip": "https://www2.census.gov/geo/tiger/TIGER2024/PLACE/tl_2024_36_place.zip",
    "cb_2020_us_zcta520_500k.zip": "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip",
    "tab20_zcta520_county20_natl.txt": "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt",
    "tab20_zcta520_tract20_natl.txt": "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_tract20_natl.txt",
}


def _keep(geo: pd.Series) -> pd.Series:
    ny = geo.str.startswith(KEEP_SUMLEVELS)
    z = geo.str.startswith("860Z200US")
    zc = geo.str[-5:]
    return ny | (z & (zc >= "10001") & (zc <= "14999"))


def fetch_table(table: str, overwrite: bool = False) -> None:
    out = RAW / "census" / f"acs5_{ACS_YEAR}"
    ensure(out)
    dest = out / f"{table}_ny.parquet"
    url = f"{ACS_BASE}/data/5YRData/acsdt5y{ACS_YEAR}-{table}.dat"
    if dest.exists() and not overwrite:
        print(f"[skip] {rel(dest)}")
    else:
        r = requests.get(url, headers=UA, timeout=900)
        r.raise_for_status()
        df = pd.read_csv(io.BytesIO(r.content), sep="|", dtype=str)
        df = df[_keep(df["GEO_ID"])]
        for c in df.columns[1:]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df.to_parquet(dest, index=False)
        print(f"[ok] {rel(dest)} {df.shape}")
    record("census_acs5_2024", {"local_path": rel(dest), "url": url, "table": table, "title": TABLES.get(table, ""),
                                "filter": "NY state/county/cousub/tract/bg/place + ZCTAs 10001-14999",
                                "bytes": dest.stat().st_size, "sha256_parquet": sha256(dest),
                                "note": "negative/sentinel values (e.g. -666666666) denote unavailable estimates"})


def fetch_geos(overwrite: bool = False) -> None:
    out = RAW / "census" / f"acs5_{ACS_YEAR}"
    raw = download(f"{ACS_BASE}/documentation/Geos{ACS_YEAR}5YR.txt", out / f"Geos{ACS_YEAR}5YR.txt",
                   manifest="census_acs5_2024", overwrite=overwrite, note="ACS geography file (national)")
    g = pd.read_csv(raw, sep="|", dtype=str, encoding="latin-1")
    g = g[_keep(g["GEO_ID"])]
    g.to_parquet(out / "geos_ny.parquet", index=False)
    download(f"{ACS_BASE}/documentation/ACS{ACS_YEAR}5YR_Table_Shells.txt", out / f"ACS{ACS_YEAR}5YR_Table_Shells.txt",
             manifest="census_acs5_2024", overwrite=overwrite, note="table shells (variable labels)")


def fetch_tiger(overwrite: bool = False) -> None:
    for name, url in TIGER.items():
        download(url, RAW / "census" / "tiger" / name, manifest="census_tiger", overwrite=overwrite)


def main(only_tables: list[str] | None = None, overwrite: bool = False) -> None:
    fetch_geos(overwrite)
    for t in TABLES:
        if only_tables and t not in only_tables:
            continue
        fetch_table(t, overwrite)
    fetch_tiger(overwrite)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", nargs="*")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    main(a.tables, a.overwrite)
