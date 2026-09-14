"""Statewide 2026 EV stock by ZIP and county from the full DMV snapshot with VIN-pattern drivetrain.

Inputs
  data/raw/ny_open_data/dmv_reg_ny_veh_full_compact.parquet  (python -m src.acquisition.dmv_full_snapshot)
  data/raw/vpic/vpic_decoded.parquet                         (python -m src.acquisition.vpic --statewide)
  data/raw/nyserda/evaluateny_v11/Vehicle Description.csv
Classification: same rule as processing/dmv_ev_stock.py (vPIC conclusive, else EValuateNY key, MY<2010 -> ICE).
Outputs (tracked, compact)
  data/processed/dmv/ny_zip_drivetrain_2026.parquet     zip, county, class_group, is_ldv, drivetrain, vehicles
  data/processed/dmv/ny_county_ev_2026.csv              county totals: BEV, PHEV, LDV, PAS LDV, shares
  data/processed/dmv/ny_classification_coverage_2026.csv share of MY>=2011 LDVs classified by source
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.processing.dmv_ev_stock import LDV_BODIES, lookup
from src.utils.paths import PROCESSED, RAW, ensure

OUT = PROCESSED / "dmv"


def main() -> None:
    ensure(OUT)
    f = pd.read_parquet(RAW / "ny_open_data" / "dmv_reg_ny_veh_full_compact.parquet")
    f["vin_key9"] = f["vin_key11"].str[:9]
    vd = pd.read_csv(RAW / "nyserda" / "evaluateny_v11" / "Vehicle Description.csv", dtype=str, low_memory=False,
                     usecols=["VIN_Key", "Drivetrain_Type"]).drop_duplicates("VIN_Key")
    f = f.merge(vd.rename(columns={"VIN_Key": "vin_key9", "Drivetrain_Type": "evny_class"}), on="vin_key9", how="left")
    lk = lookup()[["vin_key11", "vpic_class"]]
    f = f.merge(lk, on="vin_key11", how="left")
    conclusive = f["vpic_class"].isin(["BEV", "PHEV", "HEV", "ICE", "FCV"])
    evny_ok = f["evny_class"].isin(["BEV", "PHEV", "FCV", "ICE"])
    f["drivetrain"] = np.where(conclusive, f["vpic_class"], np.where(evny_ok, f["evny_class"], "UNKNOWN"))
    f.loc[(f["drivetrain"] == "UNKNOWN") & (f["model_year"] < 2010), "drivetrain"] = "ICE"
    f["source"] = np.where(conclusive, "vpic", np.where(evny_ok, "evaluateny", "none"))
    w = f["unladen_weight"]
    f["is_ldv"] = f["body_type"].isin(LDV_BODIES) & (w.isna() | (w <= 8500))
    f["class_group"] = np.select([f["registration_class"].eq("PAS"), f["registration_class"].eq("COM")], ["PAS", "COM"], "OTHER")

    cov = (f[(f["model_year"] >= 2011) & f["is_ldv"]].groupby("source").size() / ((f["model_year"] >= 2011) & f["is_ldv"]).sum())
    cov.rename("share_of_my2011plus_ldv").reset_index().to_csv(OUT / "ny_classification_coverage_2026.csv", index=False)

    z = f.groupby(["zip", "county", "class_group", "is_ldv", "drivetrain"], dropna=False).size().rename("vehicles").reset_index()
    z.to_parquet(OUT / "ny_zip_drivetrain_2026.parquet", index=False)

    ldv = f[f["is_ldv"]]
    c = ldv.groupby("county").agg(ldv=("drivetrain", "size"), bev=("drivetrain", lambda s: (s == "BEV").sum()),
                                  phev=("drivetrain", lambda s: (s == "PHEV").sum()), unknown=("drivetrain", lambda s: (s == "UNKNOWN").sum()))
    pas = ldv[ldv["class_group"] == "PAS"].groupby("county").agg(pas_ldv=("drivetrain", "size"),
                                                                 pas_ev=("drivetrain", lambda s: s.isin(["BEV", "PHEV"]).sum()))
    c = c.join(pas)
    c["ev_share_ldv"] = (c["bev"] + c["phev"]) / c["ldv"]
    c["phev_share_of_ev"] = c["phev"] / (c["bev"] + c["phev"])
    ny = c.index != "OUT-OF-STATE"
    c.loc[ny, "rank_ev_share_among_ny_counties"] = c.loc[ny, "ev_share_ldv"].rank(ascending=False, method="min")
    c.sort_values("ev_share_ldv", ascending=False).round(4).to_csv(OUT / "ny_county_ev_2026.csv")
    print(cov.round(4).to_dict())
    print(c.loc[["TOMPKINS", "WESTCHESTER", "ONONDAGA", "MONROE", "NEW YORK"]].round(4).to_string() if "TOMPKINS" in c.index else c.head())
    print("NY LDV EV:", int(c["bev"].sum()), "BEV,", int(c["phev"].sum()), "PHEV")


if __name__ == "__main__":
    main()
