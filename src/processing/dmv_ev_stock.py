"""Current (2026) Tompkins County EV stock from the NYS DMV registration snapshot with VIN-based drivetrain.

Inputs
  data/raw/ny_open_data/dmv_reg_tompkins_area_veh.parquet  (w4pv-hbkt, record_type VEH, full VINs)
  data/raw/vpic/vpic_decoded.parquet                        (NHTSA vPIC decode per VIN[:8]+VIN[9:11])
  data/raw/nyserda/evaluateny_v11/Vehicle Description.csv   (EValuateNY VIN_Key = VIN[:8]+VIN[9] -> drivetrain)
Classification (decision 0002)
  vpic_class: BEV / PHEV / HEV / ICE from ElectrificationLevel; blank level -> BEV if FuelTypePrimary Electric
              and no secondary fuel, else ICE if FuelTypePrimary known; else unknown.
  evny_class: EValuateNY lookup (BEV/PHEV/FCV/ICE) where the key exists.
  drivetrain: vPIC if conclusive, else EValuateNY, else 'UNKNOWN' (pre-2010 vehicles are not decoded -> ICE
              by construction, since no mass-market plug-ins predate MY2010).
Scope definitions
  Tompkins resident = DMV `county` == TOMPKINS (county of the registration address as recorded by DMV).
  LDV (light-duty vehicle) = body_type in LDV_BODIES and unladen_weight <= 8,500 lb (or missing).
  Personal LDV = LDV with registration_class PAS.
Outputs (tracked)
  data/processed/dmv/tompkins_ev_stock_zip_2026.csv          ZIP x drivetrain x class group counts + LDV denominators
  data/processed/dmv/tompkins_ev_make_model_2026.csv         make/model/drivetrain counts
  data/processed/dmv/tompkins_ev_model_year_2026.csv         model-year x drivetrain
  data/processed/dmv/classification_diagnostics_tompkins.csv DMV fuel_type x vPIC x EValuateNY agreement
  data/processed/dmv/vin_pattern_drivetrain_lookup.parquet   compact key -> class lookup (no full VINs)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.paths import PROCESSED, RAW, ensure

OUT = PROCESSED / "dmv"
LDV_BODIES = {"SUBN", "4DSD", "2DSD", "PICK", "VAN", "CONV", "SEDN", "H/WH", "WAGN", "3DSD", "5DSD", "HRSE", "LIMO", "UTIL"}


def vpic_class(v: pd.DataFrame) -> pd.Series:
    lvl = v["ElectrificationLevel"].fillna("")
    fp = v["FuelTypePrimary"].fillna("")
    fs = v["FuelTypeSecondary"].fillna("")
    out = pd.Series("UNKNOWN", index=v.index)
    out[fp.ne("")] = "ICE"
    out[lvl.str.contains("HEV") & ~lvl.str.startswith("PHEV")] = "HEV"
    out[(lvl.eq("") | lvl.eq("Not Applicable")) & fp.eq("Electric") & fs.eq("")] = "BEV"
    out[lvl.str.startswith("BEV")] = "BEV"
    out[lvl.str.startswith("PHEV")] = "PHEV"
    out[fp.str.contains("Fuel Cell") | lvl.str.contains("FCEV")] = "FCV"
    return out


def lookup() -> pd.DataFrame:
    v = pd.read_parquet(RAW / "vpic" / "vpic_decoded.parquet")
    v["vpic_class"] = vpic_class(v)
    v = v.drop_duplicates("vin_key11")[["vin_key11", "vpic_class", "Make", "Model", "ModelYear", "BatteryKWh", "BodyClass"]]
    return v


def classify(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    vin = df["vin"].fillna("")
    ok = vin.str.len() == 17
    df["vin_key11"] = (vin.str[:8] + vin.str[9:11]).where(ok)
    df["vin_key9"] = (vin.str[:8] + vin.str[9]).where(ok)
    vd = pd.read_csv(RAW / "nyserda" / "evaluateny_v11" / "Vehicle Description.csv", dtype=str, low_memory=False,
                     usecols=["VIN_Key", "Drivetrain_Type"]).drop_duplicates("VIN_Key")
    df = df.merge(vd.rename(columns={"VIN_Key": "vin_key9", "Drivetrain_Type": "evny_class"}), on="vin_key9", how="left")
    df = df.merge(lookup(), on="vin_key11", how="left")
    df["model_year_n"] = pd.to_numeric(df["model_year"], errors="coerce")
    conclusive = df["vpic_class"].isin(["BEV", "PHEV", "HEV", "ICE", "FCV"])
    df["drivetrain"] = np.where(conclusive, df["vpic_class"],
                                np.where(df["evny_class"].isin(["BEV", "PHEV", "FCV", "ICE"]), df["evny_class"], "UNKNOWN"))
    df.loc[(df["drivetrain"] == "UNKNOWN") & (df["model_year_n"] < 2010), "drivetrain"] = "ICE"
    df["source_of_class"] = np.where(conclusive, "vpic", np.where(df["evny_class"].isin(["BEV", "PHEV", "FCV", "ICE"]), "evaluateny", "none"))
    w = pd.to_numeric(df["unladen_weight"], errors="coerce")
    df["is_ldv"] = df["body_type"].isin(LDV_BODIES) & (w.isna() | (w <= 8500))
    df["class_group"] = np.select([df["registration_class"].eq("PAS"), df["registration_class"].isin(["COM"])],
                                  ["PAS", "COM"], "OTHER")
    return df


def main() -> None:
    ensure(OUT)
    raw = pd.read_parquet(RAW / "ny_open_data" / "dmv_reg_tompkins_area_veh.parquet")
    df = classify(raw)
    t = df[df["county"] == "TOMPKINS"]
    t_ldv = t[t["is_ldv"]]

    g = (t.assign(ev=t["drivetrain"].isin(["BEV", "PHEV"]))
         .groupby(["zip", "class_group", "is_ldv", "drivetrain"]).size().rename("vehicles").reset_index())
    g.to_csv(OUT / "tompkins_ev_stock_zip_2026.csv", index=False)

    ev = t[t["drivetrain"].isin(["BEV", "PHEV"])]
    (ev.groupby(["drivetrain", "Make", "Model"], dropna=False).size().rename("vehicles").reset_index()
     .sort_values("vehicles", ascending=False).to_csv(OUT / "tompkins_ev_make_model_2026.csv", index=False))
    (ev.groupby(["model_year_n", "drivetrain"]).size().unstack(fill_value=0).to_csv(OUT / "tompkins_ev_model_year_2026.csv"))

    diag = (t[t["model_year_n"] >= 2010].groupby(["fuel_type", "vpic_class", "evny_class"], dropna=False).size()
            .rename("vehicles").reset_index())
    diag.to_csv(OUT / "classification_diagnostics_tompkins.csv", index=False)

    lk = df.dropna(subset=["vin_key11"]).drop_duplicates("vin_key11")[["vin_key11", "vin_key9", "vpic_class", "evny_class", "drivetrain", "Make", "Model", "ModelYear"]]
    lk.to_parquet(OUT / "vin_pattern_drivetrain_lookup.parquet", index=False)

    s = t_ldv["drivetrain"].value_counts()
    print("Tompkins residents, all VEH:", len(t), "LDV:", len(t_ldv))
    print(s.to_string())
    print("PAS LDV EV share:", round(t_ldv[t_ldv["class_group"] == "PAS"]["drivetrain"].isin(["BEV", "PHEV"]).mean(), 4))
    print("class source:", t[t["model_year_n"] >= 2010]["source_of_class"].value_counts().to_dict())


if __name__ == "__main__":
    main()
