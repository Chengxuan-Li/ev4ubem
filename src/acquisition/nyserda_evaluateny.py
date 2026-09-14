"""Download NYSERDA EV registration data and the EValuateNY relational archives.

Source page: https://www.nyserda.ny.gov/All-Programs/Drive-Clean-Rebate-For-Electric-Cars-Program/Rebate-Data/Data-on-Electric-Vehicles-and-Charging-Stations
Files are large (~140 MB CSV, ~700 MB zips); stored under data/raw/nyserda/ (git-ignored).
"""
from __future__ import annotations

import argparse

from src.utils.paths import RAW
from src.utils.provenance import download

BASE = "https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files"
FILES = {
    "ny_ev_registrations.csv": f"{BASE}/Programs/ChargeNY/ny_ev_registrations.csv",
    "EValuateNY-User-Guide.pdf": f"{BASE}/Publications/Research/Transportation/EValuateNY-User-Guide.pdf",
    "EValuateNY_v11_pt1.zip": f"{BASE}/Publications/Research/Transportation/EValuateNY_v11_pt1.zip",
    "EValuateNY_v11_pt2.zip": f"{BASE}/Publications/Research/Transportation/EValuateNY_v11_pt2.zip",
}


def main(only: list[str] | None = None, overwrite: bool = False) -> None:
    out = RAW / "nyserda"
    for name, url in FILES.items():
        if only and name not in only:
            continue
        download(url, out / name, manifest="nyserda_evaluateny", overwrite=overwrite,
                 note="NYSERDA EV registration data / EValuateNY archive")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    main(a.only, a.overwrite)
