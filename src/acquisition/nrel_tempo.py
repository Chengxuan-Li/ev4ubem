"""Extract Tompkins County (FIPS 36109) hourly EV charging load from NREL TEMPO 2022 (dsgrid) on public S3.

Evidence class E (model output / synthetic benchmark) — never empirical validation.
Source: s3://nrel-pds-dsgrid/tempo/tempo-2022/v1.0.0/ (anonymous, us-west-2; OEDI submission 5958, CC-BY-4.0).
The NY partition files are sorted by county, so Tompkins lies in exactly one file per scenario x model year;
exact keys are tracked in metadata/sources/tempo2022_files_county36109.csv (from a footer-statistics scan).
Each file is streamed and filtered in memory; only the Tompkins subset is aggregated and saved.

Units: MWh per hour. Time: `time_est` stored as UTC instants covering weather year 2012; local EST
period-beginning hour = time_est - 5 h (per source note).
Outputs (data/external/tempo/ git-ignored raw subset; compact aggregates tracked):
  data/processed/tempo/tompkins_hourly_<scenario>_<year>.parquet  columns: time_est_utc, hour_est, end_use, mwh
  data/processed/tempo/tompkins_annual_by_segment.csv             scenario, year, powertrain, urbanity, income, drivers, mwh
  data/processed/tempo/tompkins_annual_summary_county.csv         official annual_summary_county subset (all years)
"""
from __future__ import annotations

import argparse
import datetime as _dt

import pandas as pd
import pyarrow.fs as pfs
import pyarrow.parquet as pq

from src.utils.paths import METADATA, PROCESSED, ensure
from src.utils.provenance import record

BUCKET = "nrel-pds-dsgrid"
OUT = PROCESSED / "tempo"
DEFAULT = [("reference", 2024), ("reference", 2026), ("reference", 2030),
           ("efs_high_ldv", 2026), ("efs_high_ldv", 2030), ("ldv_sales_evs_2035", 2030)]
ANNUAL = "tempo/tempo-2022/v1.0.0/annual_summary_county/table.parquet"


def fs() -> pfs.S3FileSystem:
    return pfs.S3FileSystem(anonymous=True, region="us-west-2")


def extract(scenario: str, year: int) -> None:
    files = pd.read_csv(METADATA / "sources" / "tempo2022_files_county36109.csv")
    key = files[files["s3_key"].str.contains(f"scenario={scenario}/tempo_project_model_years={year}/")]["s3_key"]
    if len(key) != 1:
        raise ValueError(f"expected 1 file for {scenario} {year}, got {len(key)}")
    path = f"{BUCKET}/{key.iloc[0]}"
    t = pq.read_table(path, filesystem=fs(), filters=[("county", "=", "36109")],
                      columns=["time_est", "end_use", "household_and_vehicle_type", "value", "county"]).to_pandas()
    hourly = t.groupby(["time_est", "end_use"], as_index=False)["value"].sum().rename(columns={"time_est": "time_est_utc", "value": "mwh"})
    hourly["hour_est"] = hourly["time_est_utc"] - pd.Timedelta(hours=5)
    hourly.to_parquet(OUT / f"tompkins_hourly_{scenario}_{year}.parquet", index=False)
    seg = t.groupby("household_and_vehicle_type", as_index=False)["value"].sum()
    parts = seg["household_and_vehicle_type"].str.split("+", expand=True)
    seg = pd.DataFrame({"scenario": scenario, "year": year, "drivers": parts[0], "income": parts[1], "urbanity": parts[2],
                        "size_class": parts[3], "powertrain": parts[4], "mwh": seg["value"]})
    apath = OUT / "tompkins_annual_by_segment.csv"
    old = pd.read_csv(apath) if apath.exists() else pd.DataFrame()
    if len(old):
        old = old[~((old["scenario"] == scenario) & (old["year"] == year))]
    pd.concat([old, seg]).to_csv(apath, index=False)
    record("nrel_tempo", {"local_path": f"data/processed/tempo/tompkins_hourly_{scenario}_{year}.parquet", "url": f"s3://{path}",
                          "params": {"filter": "county == 36109"}, "rows_source_subset": len(t),
                          "retrieved_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                          "annual_mwh": float(hourly["mwh"].sum()), "note": "TEMPO 2022 v1.0.0 full_dataset; class E model output"})
    print(f"[ok] {scenario} {year}: {hourly['mwh'].sum():,.0f} MWh/yr")


def annual_summary() -> None:
    t = pq.read_table(f"{BUCKET}/{ANNUAL}", filesystem=fs()).to_pandas()
    t = t[t["county"].astype(str) == "36109"]
    t.to_csv(OUT / "tompkins_annual_summary_county.csv", index=False)
    record("nrel_tempo", {"local_path": "data/processed/tempo/tompkins_annual_summary_county.csv", "url": f"s3://{BUCKET}/{ANNUAL}",
                          "params": {"filter": "county == 36109"}, "retrieved_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")})


def main(pairs) -> None:
    ensure(OUT)
    annual_summary()
    for s, y in pairs:
        extract(s, y)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="*", help="scenario:year, e.g. reference:2024")
    a = ap.parse_args()
    pairs = [(p.split(":")[0], int(p.split(":")[1])) for p in a.pairs] if a.pairs else DEFAULT
    main(pairs)
