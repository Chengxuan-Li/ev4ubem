"""ACS 2020-2024 5-year PUMS (New York households and persons) + 2020 tract-to-PUMA relationship.

Used to build a synthetic household population (joint distribution of structure type, tenure, income,
vehicles, household size, workers, commute) within Tompkins' PUMA, reweighted to block-group ACS marginals.
Source: https://www2.census.gov/programs-surveys/acs/data/pums/2024/5-Year/ (public, no key).
Outputs (git-ignored): data/raw/census/pums_2024_5yr/{psam_h36,psam_p36}_slim.parquet, tract_puma_2020.txt
"""
from __future__ import annotations

import io
import zipfile

import pandas as pd

from src.utils.paths import RAW, ensure
from src.utils.provenance import download, record, rel, sha256

BASE = "https://www2.census.gov/programs-surveys/acs/data/pums/2024/5-Year"
OUT = RAW / "census" / "pums_2024_5yr"

H_COLS = ["SERIALNO", "DIVISION", "PUMA", "ST", "ADJINC", "WGTP", "NP", "TYPEHUGQ", "BLD", "TEN", "VEH", "HINCP", "VALP",
          "YBL", "ACR", "HHT", "NOC", "R65", "WIF", "FES", "HUPAC", "RMSP", "BDSP"] + [f"WGTP{i}" for i in range(1, 81)]
P_COLS = ["SERIALNO", "SPORDER", "PUMA", "ST", "PWGTP", "AGEP", "SEX", "SCHL", "SCHG", "ESR", "WKHP", "JWMNP", "JWTRNS",
          "JWAP", "JWDP", "POWPUMA", "POWSP", "RELSHIPP"]


def _slim(zpath, prefix, cols, dest):
    with zipfile.ZipFile(zpath) as z:
        name = [n for n in z.namelist() if n.lower().startswith(prefix) and n.endswith(".csv")][0]
        with z.open(name) as f:
            header = pd.read_csv(f, nrows=0).columns
        keep = [c for c in cols if c in header]
        with z.open(name) as f:
            df = pd.read_csv(f, usecols=keep, dtype={"SERIALNO": str, "PUMA": str, "POWPUMA": str})
    df.to_parquet(dest, index=False)
    return df


def main() -> None:
    ensure(OUT)
    hz = download(f"{BASE}/csv_hny.zip", OUT / "csv_hny.zip", manifest="acs_pums", note="ACS 2020-2024 5-year PUMS NY housing")
    pz = download(f"{BASE}/csv_pny.zip", OUT / "csv_pny.zip", manifest="acs_pums", note="ACS 2020-2024 5-year PUMS NY person")
    download("https://www2.census.gov/geo/docs/maps-data/data/rel2020/2020_Census_Tract_to_2020_PUMA.txt",
             OUT / "tract_puma_2020.txt", manifest="acs_pums", note="2020 tract to 2020 PUMA relationship")
    for zpath, prefix, cols, name in [(hz, "psam_h36", H_COLS, "psam_h36_slim.parquet"), (pz, "psam_p36", P_COLS, "psam_p36_slim.parquet")]:
        dest = OUT / name
        if not dest.exists():
            df = _slim(zpath, prefix, cols, dest)
            print(f"[ok] {rel(dest)} {df.shape}")
        record("acs_pums", {"local_path": rel(dest), "url": f"{BASE}/{zpath.name}", "params": {"columns": cols},
                            "bytes": dest.stat().st_size, "sha256": sha256(dest), "note": "slim column subset"})
    rel_t = pd.read_csv(OUT / "tract_puma_2020.txt", dtype=str)
    t = rel_t[(rel_t["STATEFP"] == "36") & (rel_t["COUNTYFP"] == "109")]
    print("Tompkins PUMA(s):", sorted(t["PUMA5CE"].unique()))


if __name__ == "__main__":
    main()
