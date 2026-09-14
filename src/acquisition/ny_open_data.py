"""Acquire NY Open Data (Socrata) extracts used in this project.

Extracts are filtered server-side to keep sizes manageable; outputs are parquet under data/raw/ny_open_data/.
Every extract records the SoQL query, source update time, retrieval time and sha256 in
metadata/manifests/ny_open_data.json, and the dataset schema in metadata/schemas/.

Datasets
- w4pv-hbkt  DMV Vehicle, Snowmobile, and Boat Registrations (current, unexpired snapshot)
- s2dd-yksa  DMV Registration Transactions: Two Year Window
- thd2-fu8y  NYSERDA Drive Clean Rebate Data: Beginning 2017
- 9wxk-hakb  Charge Ready NY Programs: Beginning 2018
- bpkx-gmh7  Alternative Fuel Stations in New York (AFDC-derived)
"""
from __future__ import annotations

import argparse

from src.acquisition.socrata import fetch_to_parquet
from src.utils.paths import RAW

OUT = RAW / "ny_open_data"
M = "ny_open_data"

# ZCTAs intersecting Tompkins County (Census 2020 ZCTA-county relationship file) plus Ithaca PO-box ZIPs
TOMPKINS_AREA_ZIPS = ["13045", "13053", "13062", "13068", "13073", "13092", "13102", "13736", "13864",
                      "14817", "14850", "14851", "14852", "14853", "14854", "14867", "14881", "14882",
                      "14883", "14886"]
_zip_in = ",".join(f"'{z}'" for z in TOMPKINS_AREA_ZIPS)

EXTRACTS = {
    # all current vehicle (VEH) registrations for Tompkins residents or Tompkins-area ZIPs (row level; VIN-decodable)
    "dmv_reg_tompkins_area_veh": ("w4pv-hbkt", {
        "$where": f"record_type='VEH' AND (county='TOMPKINS' OR zip in ({_zip_in}))", "$order": ":id"}),
    # all current fuel_type=ELECTRIC registrations statewide (row level)
    "dmv_reg_ny_electric": ("w4pv-hbkt", {"$where": "fuel_type='ELECTRIC'", "$order": ":id"}),
    # statewide aggregate counts for denominators and cross-ZIP comparison
    "dmv_reg_ny_agg_zip_class_fuel": ("w4pv-hbkt", {
        "$select": "record_type, zip, county, state, registration_class, fuel_type, count(*) as n",
        "$group": "record_type, zip, county, state, registration_class, fuel_type",
        "$order": "record_type, zip, county, state, registration_class, fuel_type"}),
    "dmv_reg_ny_agg_county_class_fuel_body": ("w4pv-hbkt", {
        "$select": "record_type, county, registration_class, fuel_type, body_type, count(*) as n",
        "$where": "record_type='VEH'",
        "$group": "record_type, county, registration_class, fuel_type, body_type",
        "$order": "record_type, county, registration_class, fuel_type, body_type"}),
    # registration transactions (two-year window) for Tompkins residents
    "dmv_transactions_tompkins": ("s2dd-yksa", {"$where": "residence_county='TOMPKINS'", "$order": ":id"}),
    # statewide transactions aggregated (origin of new registrations over time)
    "dmv_transactions_ny_agg_month_county_fuel": ("s2dd-yksa", {
        "$select": "date_trunc_ym(effective_date) as month, residence_county, transaction, fuel, registration_class, count(*) as n",
        "$group": "month, residence_county, transaction, fuel, registration_class",
        "$order": "month, residence_county, transaction, fuel, registration_class"}),
    "drive_clean_rebates": ("thd2-fu8y", {"$order": ":id"}),
    "charge_ready_ny": ("9wxk-hakb", {"$order": ":id"}),
    "afdc_stations_ny": ("bpkx-gmh7", {"$order": ":id"}),
}


def main(only: list[str] | None = None, overwrite: bool = False) -> None:
    for name, (dsid, soql) in EXTRACTS.items():
        if only and name not in only:
            continue
        print(f"== {name} ({dsid})")
        fetch_to_parquet(dsid, soql, OUT / f"{name}.parquet", manifest=M, overwrite=overwrite,
                         note=name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    main(a.only, a.overwrite)
