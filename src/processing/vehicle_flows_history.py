"""Historical vehicle inflows to the Tompkins-area fleet by year, drivetrain and vehicle age (growth-model calibration).

Sources
- EValuateNY v11 `New Registrations.csv`: first appearance of each vehicle (all drivetrains) in a DMV snapshot
  (First DMV ID -> snapshot date), by ZIP; joined to `Vehicle Description.csv` (drivetrain, model year, category).
  Snapshots are annual before 2017-07 and ~monthly after, so first appearances are aggregated to calendar years of the
  snapshot date; the first snapshot (2011-03) contains the whole fleet and is excluded as an inflow.
- DMV Registration Transactions (s2dd-yksa) Tompkins residents, ORIGINAL transactions 2024-09..2026-08, VIN-decoded.
Geography: Tompkins County estimate = sum over ZIPs x ZCTA population share in Tompkins (as elsewhere).
"New" vehicle = model year >= calendar year - 1; otherwise "used".
Outputs: data/processed/growth/tompkins_inflows_by_year.csv, ny_inflows_by_year.csv
Caveats: first appearance includes move-ins and re-registrations after lapses; snapshot cadence changes in 2017
(annual -> monthly) affect how lapsed registrations re-appear; 2023 covers Jan-Apr only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.paths import PROCESSED, RAW, ensure

SRC = RAW / "nyserda" / "evaluateny_v11"
OUT = PROCESSED / "growth"


def zip_share() -> pd.Series:
    z = pd.read_csv(PROCESSED / "geography" / "zcta_county_popshare_ny.csv", dtype={"zcta": str, "county": str})
    s = z[z["county"] == "36109"].set_index("zcta")["pop_share_of_zcta"]
    return pd.concat([s, pd.Series({"14851": 1.0, "14852": 1.0})])


def main() -> None:
    ensure(OUT)
    snaps = pd.read_csv(SRC / "DMV Snapshots.csv", parse_dates=["DMV Snapshot Date"]).rename(columns={"DMV ID": "dmv_id", "DMV Snapshot Date": "date"})
    year_of = snaps.set_index("dmv_id")["date"].dt.year
    vd = pd.read_csv(SRC / "Vehicle Description.csv", dtype=str, low_memory=False, usecols=["Vehicle_Index", "Drivetrain_Type", "Year", "Vehicle_Category"])
    vd["Vehicle_Index"] = vd["Vehicle_Index"].astype("int64")
    vd["my"] = pd.to_numeric(vd["Year"], errors="coerce")
    vmap = vd.set_index("Vehicle_Index")
    w = zip_share()
    parts_t, parts_ny = [], []
    for ch in pd.read_csv(SRC / "New Registrations.csv", chunksize=4_000_000, dtype={"ZIP Code": str}):
        ch = ch[ch["First DMV ID"] != 1]
        ch = ch.join(vmap[["Drivetrain_Type", "my", "Vehicle_Category"]], on="Vehicle_Index")
        ch["year"] = ch["First DMV ID"].map(year_of)
        ch["age_class"] = np.where(ch["my"] >= ch["year"] - 1, "new", "used")
        ch["dt"] = ch["Drivetrain_Type"].where(ch["Drivetrain_Type"].isin(["BEV", "PHEV"]), "nonEV")
        ch["light_duty"] = ch["Vehicle_Category"].eq("Light-Duty (Class 1-2A)") | ch["Vehicle_Category"].isna()
        parts_ny.append(ch.groupby(["year", "dt", "age_class", "light_duty"])["Vehicle Count"].sum())
        t = ch[ch["ZIP Code"].isin(w.index)].copy()
        t["w"] = t["ZIP Code"].map(w) * t["Vehicle Count"]
        parts_t.append(t.groupby(["year", "dt", "age_class", "light_duty"])["w"].sum())
    ny = pd.concat(parts_ny).groupby(level=[0, 1, 2, 3]).sum().rename("vehicles").reset_index()
    tp = pd.concat(parts_t).groupby(level=[0, 1, 2, 3]).sum().rename("vehicles").reset_index()
    tp["source"] = "EValuateNY first appearances (ZIP-weighted)"
    ny["source"] = "EValuateNY first appearances"

    tr = pd.read_parquet(RAW / "ny_open_data" / "dmv_transactions_tompkins.parquet")
    tr = tr[(tr["effective_date"] >= "2024-09-01") & (tr["effective_date"] < "2026-09-01") & (tr["transaction"] == "ORIGINAL")].copy()
    v = tr["vehicle_identification_number"].fillna("")
    tr["vin_key11"] = (v.str[:8] + v.str[9:11]).where(v.str.len() == 17)
    from src.processing.dmv_ev_stock import lookup
    lk = lookup()[["vin_key11", "vpic_class"]]
    tr = tr.merge(lk, on="vin_key11", how="left")
    tr["dt"] = tr["vpic_class"].where(tr["vpic_class"].isin(["BEV", "PHEV"]), "nonEV")
    tr["eff_year"] = tr["effective_date"].str[:4].astype(int)
    tr["my"] = pd.to_numeric(tr["model_year"], errors="coerce")
    tr["age_class"] = np.where(tr["my"] >= tr["eff_year"] - 1, "new", "used")
    tr["light_duty"] = tr["registration_class"].isin(["PASSENGER", "COMMERCIAL"]) | tr["body_type"].isin(["SUBURBAN", "4 DOOR SEDAN", "PICKUP", "VAN"])
    # annualise the 24-month window as two 12-month periods labelled by their ending year
    tr["year"] = np.where(tr["effective_date"] < "2025-09-01", 2025, 2026)
    d = tr.groupby(["year", "dt", "age_class"]).size().rename("vehicles").reset_index()
    d["light_duty"] = True
    d["source"] = "DMV transactions ORIGINAL (12 months ending Aug)"
    out_t = pd.concat([tp, d], ignore_index=True)
    out_t.round(2).to_csv(OUT / "tompkins_inflows_by_year.csv", index=False)
    ny.to_csv(OUT / "ny_inflows_by_year.csv", index=False)
    piv = out_t[out_t["light_duty"]].pivot_table(index=["source", "year"], columns=["dt", "age_class"], values="vehicles", aggfunc="sum").fillna(0)
    piv["ev_share_all"] = (piv.get(("BEV", "new"), 0) + piv.get(("BEV", "used"), 0) + piv.get(("PHEV", "new"), 0) + piv.get(("PHEV", "used"), 0)) / piv.sum(axis=1)
    print(piv.round(3).to_string())


if __name__ == "__main__":
    main()
