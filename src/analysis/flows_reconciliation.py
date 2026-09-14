"""Reconcile Tompkins EV stock growth with registration and rebate flows (A/B observations).

Sources
- Stock: EValuateNY 2023-04 (ZIP-weighted) and DMV 2026-09 (ZIP-weighted and county field) — results/tables/tompkins_ev_stock_timeseries.csv
- DMV Registration Transactions (s2dd-yksa), residence_county = TOMPKINS, effective 2024-09-01..2026-08-31 (full months only),
  VIN-decoded with the same pattern lookup (data/processed/dmv/vin_pattern_drivetrain_lookup.parquet, EValuateNY fallback).
  Transaction types: ORIGINAL (new registration of a vehicle to a registrant: new or used purchase, move-in),
  RENEWAL, RE-REGISTRATION, RENEWAL WITH DIFFERENT VEHICLE, AMENDMENT, DUPLICATE.
- Drive Clean rebates (thd2-fu8y), county = TOMPKINS, same window.
Outputs: results/tables/tompkins_ev_flows_2024_2026.csv (monthly), results/tables/tompkins_ev_flows_summary.csv
Interpretation limits: ORIGINAL includes used-vehicle purchases and vehicles moving into the county; stock also loses
vehicles (scrappage, move-outs), so flows need not equal net stock change.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.paths import PROCESSED, RAW, TABLES, ensure

W0, W1 = "2024-09-01", "2026-09-01"


def main() -> None:
    ensure(TABLES)
    tr = pd.read_parquet(RAW / "ny_open_data" / "dmv_transactions_tompkins.parquet")
    tr = tr[(tr["effective_date"] >= W0) & (tr["effective_date"] < W1)].copy()
    v = tr["vehicle_identification_number"].fillna("")
    tr["vin_key11"] = (v.str[:8] + v.str[9:11]).where(v.str.len() == 17)
    tr["vin_key9"] = (v.str[:8] + v.str[9]).where(v.str.len() == 17)
    lk = pd.read_parquet(PROCESSED / "dmv" / "vin_pattern_drivetrain_lookup.parquet")[["vin_key11", "drivetrain"]]
    tr = tr.merge(lk, on="vin_key11", how="left")
    evny = pd.read_parquet(PROCESSED / "evaluateny" / "vin_key_drivetrain_lookup.parquet")[["VIN_Key", "Drivetrain_Type"]]
    tr = tr.merge(evny.drop_duplicates("VIN_Key").rename(columns={"VIN_Key": "vin_key9", "Drivetrain_Type": "evny"}), on="vin_key9", how="left")
    tr["drivetrain"] = tr["drivetrain"].fillna(tr["evny"])
    tr["decoded"] = tr["drivetrain"].notna()
    tr["month"] = tr["effective_date"].str[:7]
    tr["is_ev"] = tr["drivetrain"].isin(["BEV", "PHEV"])
    tr["fuel_electric"] = tr["fuel"].eq("ELECTRIC")

    m = (tr[tr["transaction"] == "ORIGINAL"].groupby("month")
         .agg(original_all=("transaction", "size"), original_decoded=("decoded", "sum"),
              original_bev=("drivetrain", lambda s: (s == "BEV").sum()), original_phev=("drivetrain", lambda s: (s == "PHEV").sum()),
              original_fuel_electric=("fuel_electric", "sum")).reset_index())
    dc = pd.read_parquet(RAW / "ny_open_data" / "drive_clean_rebates.parquet")
    dc = dc[(dc["county"].str.upper() == "TOMPKINS") & (dc["submitted_date"] >= W0) & (dc["submitted_date"] < W1)]
    dc["month"] = dc["submitted_date"].str[:7]
    m = m.merge(dc.groupby("month").size().rename("rebates").reset_index(), on="month", how="left").fillna({"rebates": 0})
    m.to_csv(TABLES / "tompkins_ev_flows_2024_2026.csv", index=False)

    ts = pd.read_csv(TABLES / "tompkins_ev_stock_timeseries.csv", parse_dates=["snapshot_date"])
    ev23 = ts[ts["snapshot_date"] == "2023-04-02"]["EV"].iloc[0]
    ev26 = ts[ts["source"].str.contains("ZIP pop-share weighted \\(method", regex=True)]["EV"].iloc[0]
    years = (pd.Timestamp("2026-09-02") - pd.Timestamp("2023-04-02")).days / 365.25
    orig_ev = m["original_bev"].sum() + m["original_phev"].sum()
    s = pd.DataFrame([
        {"metric": "EV stock 2023-04 (EValuateNY, ZIP-weighted)", "value": ev23},
        {"metric": "EV stock 2026-09 (DMV, ZIP-weighted)", "value": ev26},
        {"metric": "Net stock growth per year 2023-04..2026-09", "value": (ev26 - ev23) / years},
        {"metric": "CAGR 2023-04..2026-09", "value": (ev26 / ev23) ** (1 / years) - 1},
        {"metric": "ORIGINAL registrations, all vehicles, 24 months", "value": m["original_all"].sum()},
        {"metric": "ORIGINAL registrations decoded share", "value": m["original_decoded"].sum() / m["original_all"].sum()},
        {"metric": "ORIGINAL EV registrations per year (BEV+PHEV, decoded)", "value": orig_ev / 2},
        {"metric": "  of which BEV per year", "value": m["original_bev"].sum() / 2},
        {"metric": "  of which PHEV per year", "value": m["original_phev"].sum() / 2},
        {"metric": "EV share of ORIGINAL registrations", "value": orig_ev / m["original_decoded"].sum()},
        {"metric": "ORIGINAL with DMV fuel=ELECTRIC per year", "value": m["original_fuel_electric"].sum() / 2},
        {"metric": "Drive Clean rebates per year (same window)", "value": m["rebates"].sum() / 2},
        {"metric": "Rebates / ORIGINAL EV registrations", "value": m["rebates"].sum() / max(orig_ev, 1)},
    ])
    s["value"] = s["value"].astype(float).round(4)
    s.to_csv(TABLES / "tompkins_ev_flows_summary.csv", index=False)
    print(s.to_string())


if __name__ == "__main__":
    main()
