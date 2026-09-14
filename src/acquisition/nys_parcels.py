"""Tompkins County tax parcels (2025 roll) from the public NYS ITS Tax Parcels service.

Service: https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/MapServer/1
Tompkins is one of 38 counties that permit public redistribution. Owner-name and mailing
fields are deliberately NOT requested (privacy; not needed for building-class analysis).
Output: data/raw/parcels/tompkins_parcels_2025.gpkg (EPSG:4326).
"""
from __future__ import annotations

import datetime as _dt
import json
import time

import geopandas as gpd
import requests

from src.utils.paths import RAW, ensure
from src.utils.provenance import UA, record, rel, sha256

URL = "https://gisservices.its.ny.gov/arcgis/rest/services/NYS_Tax_Parcels_Public/MapServer/1/query"
FIELDS = ["COUNTY_NAME", "MUNI_NAME", "SWIS", "PARCEL_ADDR", "PRINT_KEY", "SBL", "CITYTOWN_NAME", "CITYTOWN_SWIS",
          "LOC_ZIP", "PROP_CLASS", "ROLL_SECTION", "LAND_AV", "TOTAL_AV", "FULL_MARKET_VAL", "YR_BLT", "SQ_FT",
          "ACRES", "BLDG_STYLE", "BLDG_STYLE_DESC", "HEAT_TYPE_DESC", "FUEL_TYPE_DESC", "SQFT_LIVING", "GFA",
          "NBR_KITCHENS", "NBR_BEDROOMS", "USED_AS_CODE", "USED_AS_DESC", "OWNER_TYPE", "ROLL_YR", "SPATIAL_YR",
          "SWIS_SBL_ID", "CALC_ACRES"]
WHERE = "COUNTY_NAME='Tompkins'"


def main(overwrite: bool = False, page: int = 2000) -> None:
    out = RAW / "parcels"
    ensure(out)
    dest = out / "tompkins_parcels_2025.gpkg"
    if dest.exists() and not overwrite:
        print(f"[skip] {rel(dest)}")
    else:
        frames, offset = [], 0
        while True:
            params = {"where": WHERE, "outFields": ",".join(FIELDS), "returnGeometry": "true", "outSR": 4326,
                      "resultOffset": offset, "resultRecordCount": page, "orderByFields": "OBJECTID", "f": "geojson"}
            for attempt in range(5):
                try:
                    r = requests.get(URL, params=params, headers=UA, timeout=300)
                    r.raise_for_status()
                    gj = r.json()
                    break
                except Exception as exc:  # noqa: BLE001
                    print("retry", attempt, exc)
                    time.sleep(5 * (attempt + 1))
            feats = gj.get("features", [])
            if not feats:
                break
            frames.append(gpd.GeoDataFrame.from_features(feats, crs=4326))
            offset += len(feats)
            print(f"  parcels: {offset}")
            if len(feats) < page:
                break
        gdf = gpd.pd.concat(frames, ignore_index=True)
        gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=4326)
        gdf.to_file(dest, driver="GPKG")
        print(f"[ok] {rel(dest)} {len(gdf)} parcels")
    record("nys_parcels", {"local_path": rel(dest), "url": URL, "params": {"where": WHERE, "outFields": FIELDS},
                           "retrieved_utc": _dt.datetime.fromtimestamp(dest.stat().st_mtime, _dt.timezone.utc).isoformat(timespec="seconds"),
                           "bytes": dest.stat().st_size, "sha256": sha256(dest),
                           "note": "NYS ITS public tax parcels, 2025 assessment roll; owner/mailing fields excluded"})


if __name__ == "__main__":
    main()
