"""Geographic crosswalks and study-area geometries.

Outputs (tracked, compact):
  data/processed/geography/zcta_county_popshare_ny.csv
      For each NY-range ZCTA x county: estimated population in the part, share of ZCTA population
      in that county. Population = ACS 2020-2024 tract population apportioned to ZCTA parts by
      land-area share (Census 2020 ZCTA-tract relationship file). Area weighting is an approximation.
  data/processed/geography/tompkins_bg.gpkg, tompkins_tract.gpkg, tompkins_area_zcta.gpkg (EPSG:4326)
      Tompkins County block groups/tracts (TIGER 2024) and ZCTAs intersecting the county
      (Census cartographic boundary 2020, 1:500k).
CRS note: stored in EPSG:4326; area/distance computations use EPSG:32618 (UTM 18N).
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from src.utils.paths import PROCESSED, RAW, ensure

OUT = PROCESSED / "geography"
TIGER = RAW / "census" / "tiger"
ACS = RAW / "census" / "acs5_2024"
TOMPKINS = "36109"


def zcta_county_share() -> pd.DataFrame:
    rel = pd.read_csv(TIGER / "tab20_zcta520_tract20_natl.txt", sep="|", dtype=str, encoding="utf-8-sig")
    rel = rel.dropna(subset=["GEOID_ZCTA5_20", "GEOID_TRACT_20"])
    rel = rel[rel["GEOID_TRACT_20"].str.startswith("36")]
    rel["part_land"] = rel["AREALAND_PART"].astype(float)
    rel["tract_land"] = rel["AREALAND_TRACT_20"].astype(float)
    pop = pd.read_parquet(ACS / "b01003_ny.parquet")
    pop = pop[pop["GEO_ID"].str.startswith("1400000US")]
    pop["tract"] = pop["GEO_ID"].str[-11:]
    rel = rel.merge(pop[["tract", "B01003_E001"]], left_on="GEOID_TRACT_20", right_on="tract", how="left")
    # tracts with zero land area (water) get equal split
    rel["w"] = (rel["part_land"] / rel["tract_land"]).where(rel["tract_land"] > 0, 0)
    rel["pop_part"] = rel["B01003_E001"].fillna(0) * rel["w"]
    rel["county"] = rel["GEOID_TRACT_20"].str[:5]
    out = rel.groupby(["GEOID_ZCTA5_20", "county"], as_index=False).agg(pop_part=("pop_part", "sum"), land_part_m2=("part_land", "sum"))
    out = out.rename(columns={"GEOID_ZCTA5_20": "zcta"})
    tot = out.groupby("zcta")["pop_part"].transform("sum")
    out["pop_share_of_zcta"] = (out["pop_part"] / tot).where(tot > 0)
    out["ny_share_of_zcta_land"] = 1.0  # restricted to NY tracts
    return out.sort_values(["zcta", "pop_part"], ascending=[True, False])


def main() -> None:
    ensure(OUT)
    zc = zcta_county_share()
    zc.round({"pop_part": 1, "pop_share_of_zcta": 4}).to_csv(OUT / "zcta_county_popshare_ny.csv", index=False)
    print("zcta-county", zc.shape)

    bg = gpd.read_file(f"zip://{TIGER / 'tl_2024_36_bg.zip'}")
    bg = bg[bg["COUNTYFP"] == "109"].to_crs(4326)
    bg.to_file(OUT / "tompkins_bg.gpkg", driver="GPKG")
    tr = gpd.read_file(f"zip://{TIGER / 'tl_2024_36_tract.zip'}")
    tr = tr[tr["COUNTYFP"] == "109"].to_crs(4326)
    tr.to_file(OUT / "tompkins_tract.gpkg", driver="GPKG")

    tz = zc[zc["county"] == TOMPKINS]["zcta"].unique()
    z = gpd.read_file(f"zip://{TIGER / 'cb_2020_us_zcta520_500k.zip'}")
    z = z[z["ZCTA5CE20"].isin(tz)].to_crs(4326)
    z = z.merge(zc[zc["county"] == TOMPKINS][["zcta", "pop_part", "pop_share_of_zcta"]], left_on="ZCTA5CE20", right_on="zcta")
    z.to_file(OUT / "tompkins_area_zcta.gpkg", driver="GPKG")
    print("tompkins bg/tract/zcta", len(bg), len(tr), len(z))


if __name__ == "__main__":
    main()
