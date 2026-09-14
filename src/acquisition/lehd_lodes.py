"""LEHD LODES8 origin-destination (OD) files for New York plus a county gazetteer, for in-commuting analysis. No key needed.

Source: U.S. Census Bureau, LEHD Origin-Destination Employment Statistics (LODES) version 8 (2020 census blocks).
  https://lehd.ces.census.gov/data/lodes/LODES8/ny/od/ny_od_{part}_{JT}_{year}.csv.gz
    part = main  jobs with workplace AND residence in NY
         = aux   jobs with workplace in NY and residence in another state
    JT00 = all jobs; JT01 = primary jobs (one job per worker: the highest-paying job)
  Columns: w_geocode, h_geocode (15-digit 2020 block GEOIDs), S000 (total jobs), SA01-SA03 (age), SE01-SE03 (earnings),
  SI01-SI03 (industry), createdate. Block GEOID[:5] = state+county, [:12] = block group, so no crosswalk is needed.
  Technical document: https://lehd.ces.census.gov/data/lodes/LODES8/LODESTechDoc8.4.pdf
County internal points (origin-distance screen): Census 2024 Gazetteer counties
  https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_counties_national.zip

Latest LODES year checked on 2026-09-14 is 2023; files were posted 2025-12-03. Each file is downloaded once and never
modified; filtering happens in src/analysis/incommuter_charging.py.
Output: data/raw/lehd_lodes/ (git-ignored); manifest: metadata/manifests/lehd_lodes.json
Sizes: main JT00 ~45 MB, main JT01 ~41 MB, aux ~5 MB each, gazetteer 0.14 MB, tech doc 0.6 MB.
"""
from __future__ import annotations

import argparse

from src.utils.paths import RAW
from src.utils.provenance import download

BASE = "https://lehd.ces.census.gov/data/lodes/LODES8"
YEAR = 2023
OUT = RAW / "lehd_lodes"
GAZ = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_counties_national.zip"
TECHDOC = f"{BASE}/LODESTechDoc8.4.pdf"


def od_path(part: str, jt: str, year: int = YEAR):
    return OUT / f"ny_od_{part}_{jt}_{year}.csv.gz"


def main(year: int = YEAR, job_types: tuple[str, ...] = ("JT00", "JT01"), overwrite: bool = False) -> None:
    for jt in job_types:
        for part in ["main", "aux"]:
            url = f"{BASE}/ny/od/ny_od_{part}_{jt}_{year}.csv.gz"
            note = (f"LODES8 NY OD {part} {jt} {year}: " +
                    ("workplace and residence in NY" if part == "main" else "workplace in NY, residence out of state"))
            download(url, od_path(part, jt, year), "lehd_lodes", overwrite=overwrite, note=note)
    download(GAZ, OUT / "2024_Gaz_counties_national.zip", "lehd_lodes", overwrite=overwrite,
             note="Census 2024 Gazetteer counties (internal point lat/lon) for the origin-distance screen")
    download(TECHDOC, OUT / "LODESTechDoc8.4.pdf", "lehd_lodes", overwrite=overwrite, note="LODES 8.4 technical documentation")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=YEAR)
    ap.add_argument("--jt", nargs="*", default=["JT00", "JT01"])
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    main(a.year, tuple(a.jt), a.overwrite)
