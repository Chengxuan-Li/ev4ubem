"""Charging infrastructure tables for Tompkins County (AFDC API, AFDC NY Open Data mirror, Charge Ready NY).

Definitions
- station = one AFDC record (a location); ports = ev_level1_evse_num + ev_level2_evse_num + ev_dc_fast_num
  (AFDC "EVSE ports", not connectors).
- status_code: E open, P planned, T temporarily unavailable. access_code: public/private.
- Tompkins membership by point-in-polygon against TIGER 2024 county subdivisions of county 36109
  (not by ZIP or city label, which spill over county lines).
Outputs (tracked):
  data/processed/infrastructure/tompkins_afdc_stations.gpkg / .csv   (API snapshot, all statuses)
  data/processed/infrastructure/afdc_county_summary_ny.csv            (NY counties: stations, ports by level/access)
  data/processed/infrastructure/afdc_source_comparison_tompkins.csv   (API vs NY Open Data mirror)
  data/processed/infrastructure/charge_ready_ny_tompkins.csv
  data/processed/infrastructure/tompkins_ports_by_open_year.csv       (cumulative, surviving stations only)
"""
from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd

from src.utils.paths import PROCESSED, RAW, ensure

OUT = PROCESSED / "infrastructure"


def counties() -> gpd.GeoDataFrame:
    cs = gpd.read_file(f"zip://{RAW / 'census' / 'tiger' / 'tl_2024_36_cousub.zip'}")
    c = cs.dissolve(by="COUNTYFP", as_index=False)[["COUNTYFP", "geometry"]].to_crs(4326)
    return c


def to_points(df: pd.DataFrame) -> gpd.GeoDataFrame:
    df = df.copy()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    for c in ["ev_level1_evse_num", "ev_level2_evse_num", "ev_dc_fast_num"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["ports_total"] = df["ev_level1_evse_num"] + df["ev_level2_evse_num"] + df["ev_dc_fast_num"]
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["longitude"], df["latitude"]), crs=4326)


def main() -> None:
    ensure(OUT)
    cty = counties()
    api = pd.DataFrame(json.load(open(RAW / "afdc" / "afdc_elec_ny_all_status.json", encoding="utf-8"))["fuel_stations"])
    api = to_points(api)
    api = gpd.sjoin(api, cty, how="left", predicate="within").drop(columns="index_right")
    keep = ["id", "station_name", "street_address", "city", "zip", "status_code", "access_code", "access_detail_code",
            "facility_type", "owner_type_code", "ev_network", "ev_level1_evse_num", "ev_level2_evse_num", "ev_dc_fast_num",
            "ports_total", "ev_connector_types", "ev_pricing", "ev_workplace_charging", "open_date", "date_last_confirmed",
            "updated_at", "latitude", "longitude", "COUNTYFP", "geometry"]
    t = api[api["COUNTYFP"] == "109"][keep]
    t.to_file(OUT / "tompkins_afdc_stations.gpkg", driver="GPKG")
    t.drop(columns="geometry").to_csv(OUT / "tompkins_afdc_stations.csv", index=False)

    summ = (api.groupby(["COUNTYFP", "status_code", "access_code"])
            .agg(stations=("id", "size"), l1=("ev_level1_evse_num", "sum"), l2=("ev_level2_evse_num", "sum"),
                 dcfc=("ev_dc_fast_num", "sum"), ports=("ports_total", "sum")).reset_index())
    summ.to_csv(OUT / "afdc_county_summary_ny.csv", index=False)

    od = pd.read_parquet(RAW / "ny_open_data" / "afdc_stations_ny.parquet")
    od = od[od["fuel_type_code"] == "ELEC"].rename(columns={"ev_dc_fast_count": "ev_dc_fast_num"})
    od = to_points(od)
    od = gpd.sjoin(od, cty, how="left", predicate="within").drop(columns="index_right")
    odt = od[od["COUNTYFP"] == "109"]
    comp = pd.DataFrame({
        "source": ["AFDC API (developer.nlr.gov) all statuses", "AFDC API status E", "NY Open Data bpkx-gmh7 (ELEC)"],
        "stations": [len(t), int((t["status_code"] == "E").sum()), len(odt)],
        "l2_ports": [int(t["ev_level2_evse_num"].sum()), int(t.loc[t["status_code"] == "E", "ev_level2_evse_num"].sum()), int(odt["ev_level2_evse_num"].sum())],
        "dcfc_ports": [int(t["ev_dc_fast_num"].sum()), int(t.loc[t["status_code"] == "E", "ev_dc_fast_num"].sum()), int(odt["ev_dc_fast_num"].sum())],
        "public_stations": [int((t["access_code"] == "public").sum()), int(((t["access_code"] == "public") & (t["status_code"] == "E")).sum()),
                            int((odt.get("access_code", pd.Series(dtype=str)) == "public").sum())],
    })
    ids_api, ids_od = set(t["id"].astype(str)), set(odt["id"].astype(str))
    comp["ids_only_in_this_source"] = [len(ids_api - ids_od), None, len(ids_od - ids_api)]
    comp.to_csv(OUT / "afdc_source_comparison_tompkins.csv", index=False)

    cr = pd.read_parquet(RAW / "ny_open_data" / "charge_ready_ny.parquet")
    cr = cr[cr["county"].str.upper().str.contains("TOMPKINS", na=False)]
    cr.drop(columns=[c for c in cr.columns if c.startswith(":@") or c == "georeference"]).to_csv(OUT / "charge_ready_ny_tompkins.csv", index=False)

    e = t[t["status_code"] == "E"].copy()
    e["open_year"] = pd.to_datetime(e["open_date"], errors="coerce").dt.year
    g = e.groupby(["open_year", "access_code"]).agg(stations=("id", "size"), l2=("ev_level2_evse_num", "sum"), dcfc=("ev_dc_fast_num", "sum")).reset_index()
    g[["cum_stations", "cum_l2", "cum_dcfc"]] = g.groupby("access_code")[["stations", "l2", "dcfc"]].cumsum()
    g.to_csv(OUT / "tompkins_ports_by_open_year.csv", index=False)
    print(comp.to_string())


if __name__ == "__main__":
    main()
