"""Process NYSERDA EValuateNY v11 archive into compact, tracked tables.

Inputs (data/raw/nyserda/evaluateny_v11/, from src.acquisition.nyserda_evaluateny + unzip):
  All EV Registrations.csv  one row per (EV, snapshot); DMV_ID = snapshot id (see DMV Snapshots.csv)
  Current Registrations.csv all vehicles in the latest snapshot (DMV_ID 73 = 2023-04-02), VIN-decoded
  New Registrations.csv     first appearance of each vehicle (First DMV ID)
  Vehicle Description.csv   Vehicle_Index -> drivetrain (BEV/PHEV/ICE), make, model, class, range
  resources.xlsx            ChargePoint 'Charging Use' by ZIP-month, AFDC charging locations, ZIP table
Outputs (data/processed/evaluateny/):
  ev_stock_zip_snapshot.parquet     ZIP x snapshot x drivetrain EV counts (NY ZIPs)
  fleet_zip_2023-04.parquet         ZIP x drivetrain x vehicle category counts, all vehicles, Apr-2023
  ev_new_regs_zip_snapshot.parquet  ZIP x first-snapshot x drivetrain (first appearance of EVs)
  ev_models_tompkins_2023-04.csv    make/model/drivetrain composition for Tompkins-area ZIPs, Apr-2023
  chargepoint_use_zip_month.csv     ChargePoint monthly usage by ZIP (as published by EValuateNY)
  vin_key_drivetrain_lookup.parquet VIN_Key (VIN[:8]+VIN[9]) -> drivetrain for EV/PHEV keys
  dmv_snapshots.csv
"""
from __future__ import annotations

import pandas as pd

from src.utils.paths import PROCESSED, RAW, ensure

SRC = RAW / "nyserda" / "evaluateny_v11"
OUT = PROCESSED / "evaluateny"

TOMPKINS_AREA_ZIPS = ["13045", "13053", "13062", "13068", "13073", "13092", "13102", "13736", "13864", "14817", "14850",
                      "14851", "14852", "14853", "14854", "14867", "14881", "14882", "14883", "14886"]


def vehicle_description() -> pd.DataFrame:
    vd = pd.read_csv(SRC / "Vehicle Description.csv", dtype=str, low_memory=False)
    vd["Vehicle_Index"] = vd["Vehicle_Index"].astype("int64")
    return vd


def main() -> None:
    ensure(OUT)
    snaps = pd.read_csv(SRC / "DMV Snapshots.csv", parse_dates=["DMV Snapshot Date"])
    snaps = snaps[["DMV ID", "DMV Snapshot Date"]].rename(columns={"DMV ID": "dmv_id", "DMV Snapshot Date": "snapshot_date"}).sort_values("dmv_id")
    snaps.to_csv(OUT / "dmv_snapshots.csv", index=False)

    vd = vehicle_description()
    vmap = vd.set_index("Vehicle_Index")[["Drivetrain_Type", "Vehicle_Category", "NHTSA_Make_Name", "NHTSA_Model_Name",
                                          "EV_Atlas_Vehicle_Name", "Year", "Average_Electric_Range"]]

    ev = vd[vd["Drivetrain_Type"].isin(["BEV", "PHEV", "FCV"])][["VIN_Key", "Drivetrain_Type", "NHTSA_Make_Name", "NHTSA_Model_Name",
                                                                   "EV_Atlas_Vehicle_Name", "Year", "Vehicle_Category"]]
    ev.to_parquet(OUT / "vin_key_drivetrain_lookup.parquet", index=False)

    # EV stock by ZIP x snapshot x drivetrain
    a = pd.read_csv(SRC / "All EV Registrations.csv", dtype={"ZIP Code": str, "County_GEOID": str})
    a = a.join(vmap[["Drivetrain_Type", "Vehicle_Category"]], on="Vehicle_Index")
    stock = (a.groupby(["DMV_ID", "ZIP Code", "Drivetrain_Type", "Vehicle_Category"], dropna=False)["Vehicle Count"].sum()
             .rename("vehicles").reset_index()
             .rename(columns={"DMV_ID": "dmv_id", "ZIP Code": "zip", "Drivetrain_Type": "drivetrain", "Vehicle_Category": "vehicle_category"}))
    stock = stock.merge(snaps, on="dmv_id", how="left")
    stock.to_parquet(OUT / "ev_stock_zip_snapshot.parquet", index=False)
    print("ev_stock_zip_snapshot", stock.shape)

    tomp = a[(a["DMV_ID"] == 73) & a["ZIP Code"].isin(TOMPKINS_AREA_ZIPS)].join(
        vmap[["NHTSA_Make_Name", "NHTSA_Model_Name", "EV_Atlas_Vehicle_Name", "Year"]], on="Vehicle_Index")
    (tomp.groupby(["ZIP Code", "Drivetrain_Type", "EV_Atlas_Vehicle_Name"])["Vehicle Count"].sum().rename("vehicles")
     .reset_index().sort_values(["ZIP Code", "vehicles"], ascending=[True, False])
     .to_csv(OUT / "ev_models_tompkins_2023-04.csv", index=False))
    del a

    # Fleet (all vehicles) by ZIP x drivetrain x category, latest snapshot
    parts = []
    for ch in pd.read_csv(SRC / "Current Registrations.csv", chunksize=4_000_000, dtype={"ZIP Code": str},
                          usecols=["Vehicle Count", "ZIP Code", "Vehicle_Index", "DMV_ID"]):
        ch = ch.join(vmap[["Drivetrain_Type", "Vehicle_Category"]], on="Vehicle_Index")
        parts.append(ch.groupby(["DMV_ID", "ZIP Code", "Drivetrain_Type", "Vehicle_Category"], dropna=False)["Vehicle Count"].sum())
    fleet = (pd.concat(parts).groupby(level=[0, 1, 2, 3], dropna=False).sum().rename("vehicles").reset_index()
             .rename(columns={"DMV_ID": "dmv_id", "ZIP Code": "zip", "Drivetrain_Type": "drivetrain", "Vehicle_Category": "vehicle_category"}))
    fleet.to_parquet(OUT / "fleet_zip_2023-04.parquet", index=False)
    print("fleet_zip", fleet.shape)

    # New EV registrations (first appearance) by ZIP x snapshot
    parts = []
    for ch in pd.read_csv(SRC / "New Registrations.csv", chunksize=4_000_000, dtype={"ZIP Code": str}):
        ch = ch.join(vmap[["Drivetrain_Type"]], on="Vehicle_Index")
        ch = ch[ch["Drivetrain_Type"].isin(["BEV", "PHEV", "FCV"])]
        parts.append(ch.groupby(["First DMV ID", "ZIP Code", "Drivetrain_Type"])["Vehicle Count"].sum())
    new = (pd.concat(parts).groupby(level=[0, 1, 2]).sum().rename("vehicles").reset_index()
           .rename(columns={"First DMV ID": "dmv_id", "ZIP Code": "zip", "Drivetrain_Type": "drivetrain"}))
    new = new.merge(snaps, on="dmv_id", how="left")
    new.to_parquet(OUT / "ev_new_regs_zip_snapshot.parquet", index=False)
    print("ev_new_regs", new.shape)

    cu = pd.read_excel(SRC / "resources.xlsx", sheet_name="Charging Use", dtype={"ZIP Code": str})
    cu.to_csv(OUT / "chargepoint_use_zip_month.csv", index=False)
    print("charging use", cu.shape)


if __name__ == "__main__":
    main()
