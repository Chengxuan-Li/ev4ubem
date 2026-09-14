"""Tidy ACS 2020-2024 5-year features for NY ZCTAs, counties, and Tompkins tracts/block groups.

Definitions (all from ACS table-based summary files; E=estimate, M=90% MOE):
  pop                 B01003_001
  households          B25003_001 (occupied housing units)
  owner_share         B25003_002 / B25003_001
  sf_detached_share   B25024_002 / B25024_001 (housing units, all occupancy)
  mf5plus_share       B25024_006..009 / B25024_001
  owner_sfd_share     B25032_003 / B25032_001 (occupied units that are owner-occupied 1-unit detached)
  renter_mf5_share    B25032_018..021 / B25032_001
  hh_vehicles         sum over B25044 vehicle-count cells (5+ counted as 5)
  veh_per_hh          hh_vehicles / households
  zero_veh_share      (B25044_003 + B25044_010) / B25044_001
  med_hh_income       B19013_001 (dollars, 2024-inflation adjusted)
  inc100k_share       B19001_014..017 / B19001_001 ;  inc150k_share B19001_016..017 / B19001_001
  ba_plus_share       B15003_022..025 / B15003_001 (population 25+)
  med_age             B01002_001
  drove_alone_share   B08301_003 / B08301_001 (workers 16+) ; transit B08301_010 ; walk B08301_019 ;
  wfh_share           B08301_021 / B08301_001
  commute30plus_share B08303_008..013 / B08303_001 (workers not working at home)
  college_share       (B14007_017 + B14007_018) / B01003_001
  built2000plus_share B25034_002..004 / B25034_001
  elec_heat_share     B25040_004 / B25040_001
  med_home_value      B25077_001
  land_km2, pop_density_km2 (from TIGER/relationship files)
MOEs for shares use the Census proportion formula; aggregated counts use root-sum-of-squares
(an approximation that ignores covariance).
Outputs: data/processed/acs/acs_features_{ny_zcta,ny_county,tompkins_tract,tompkins_bg}.parquet
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.paths import PROCESSED, RAW, ensure

ACS = RAW / "census" / "acs5_2024"
TIGER = RAW / "census" / "tiger"
OUT = PROCESSED / "acs"
TABLES = ["b01003", "b01002", "b25003", "b25024", "b25032", "b25044", "b19013", "b19001", "b15003", "b08301",
          "b08303", "b14007", "b25034", "b25040", "b25077"]


def load() -> pd.DataFrame:
    df = None
    for t in TABLES:
        x = pd.read_parquet(ACS / f"{t}_ny.parquet")
        df = x if df is None else df.merge(x, on="GEO_ID", how="outer")
    num = df.columns.drop("GEO_ID")
    df[num] = df[num].where(df[num] >= 0)  # negative sentinels -> NaN
    return df


def _sum(df, table, lines):
    e = sum(df[f"{table}_E{l:03d}"].fillna(0) for l in lines)
    m = np.sqrt(sum(df[f"{table}_M{l:03d}"].fillna(0) ** 2 for l in lines))
    return e, m


def _share(num_e, num_m, den_e, den_m):
    p = num_e / den_e.replace(0, np.nan)
    rad = num_m ** 2 - p ** 2 * den_m ** 2
    rad = rad.where(rad >= 0, num_m ** 2 + p ** 2 * den_m ** 2)
    return p, np.sqrt(rad) / den_e.replace(0, np.nan)


def features(df: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame({"GEO_ID": df["GEO_ID"]})
    f["pop"], f["pop_moe"] = df["B01003_E001"], df["B01003_M001"]
    f["households"], f["households_moe"] = df["B25003_E001"], df["B25003_M001"]
    specs = {
        "owner_share": (("b25003", [2]), ("b25003", [1])),
        "sf_detached_share": (("b25024", [2]), ("b25024", [1])),
        "sf_attached_share": (("b25024", [3]), ("b25024", [1])),
        "mf2_4_share": (("b25024", [4, 5]), ("b25024", [1])),
        "mf5plus_share": (("b25024", [6, 7, 8, 9]), ("b25024", [1])),
        "mobile_home_share": (("b25024", [10]), ("b25024", [1])),
        "owner_sfd_share": (("b25032", [3]), ("b25032", [1])),
        "renter_sfd_share": (("b25032", [14]), ("b25032", [1])),
        "renter_mf5_share": (("b25032", [18, 19, 20, 21]), ("b25032", [1])),
        "zero_veh_share": (("b25044", [3, 10]), ("b25044", [1])),
        "inc100k_share": (("b19001", [14, 15, 16, 17]), ("b19001", [1])),
        "inc150k_share": (("b19001", [16, 17]), ("b19001", [1])),
        "ba_plus_share": (("b15003", [22, 23, 24, 25]), ("b15003", [1])),
        "drove_alone_share": (("b08301", [3]), ("b08301", [1])),
        "transit_share": (("b08301", [10]), ("b08301", [1])),
        "walk_share": (("b08301", [19]), ("b08301", [1])),
        "wfh_share": (("b08301", [21]), ("b08301", [1])),
        "commute30plus_share": (("b08303", [8, 9, 10, 11, 12, 13]), ("b08303", [1])),
        "college_share": (("b14007", [17, 18]), ("b01003", [1])),
        "built2000plus_share": (("b25034", [2, 3, 4]), ("b25034", [1])),
        "elec_heat_share": (("b25040", [4]), ("b25040", [1])),
    }
    for name, ((tn, ln), (td, ld)) in specs.items():
        ne, nm = _sum(df, tn.upper(), ln)
        de, dm = _sum(df, td.upper(), ld)
        f[name], f[name + "_moe"] = _share(ne, nm, de, dm)
    cells = {3: 0, 4: 1, 5: 2, 6: 3, 7: 4, 8: 5, 10: 0, 11: 1, 12: 2, 13: 3, 14: 4, 15: 5}
    f["hh_vehicles"] = sum(df[f"B25044_E{l:03d}"].fillna(0) * k for l, k in cells.items())
    f["veh_per_hh"] = f["hh_vehicles"] / f["households"].replace(0, np.nan)
    f["med_hh_income"], f["med_hh_income_moe"] = df["B19013_E001"], df["B19013_M001"]
    f["med_age"] = df["B01002_E001"]
    f["med_home_value"] = df["B25077_E001"]
    return f


def land_areas() -> pd.DataFrame:
    import geopandas as gpd
    parts = []
    for name in ["tl_2024_36_bg.zip", "tl_2024_36_tract.zip"]:
        g = gpd.read_file(f"zip://{TIGER / name}", ignore_geometry=True)
        lvl = "1500000US" if "_bg" in name else "1400000US"
        parts.append(pd.DataFrame({"GEO_ID": lvl + g["GEOID"], "land_km2": g["ALAND"].astype(float) / 1e6}))
    rel = pd.read_csv(TIGER / "tab20_zcta520_county20_natl.txt", sep="|", dtype=str, encoding="utf-8-sig")
    z = rel.dropna(subset=["GEOID_ZCTA5_20"]).drop_duplicates("GEOID_ZCTA5_20")
    parts.append(pd.DataFrame({"GEO_ID": "860Z200US" + z["GEOID_ZCTA5_20"], "land_km2": z["AREALAND_ZCTA5_20"].astype(float) / 1e6}))
    c = rel.dropna(subset=["GEOID_COUNTY_20"]).drop_duplicates("GEOID_COUNTY_20")
    parts.append(pd.DataFrame({"GEO_ID": "0500000US" + c["GEOID_COUNTY_20"], "land_km2": c["AREALAND_COUNTY_20"].astype(float) / 1e6}))
    return pd.concat(parts)


def main() -> None:
    ensure(OUT)
    df = load()
    f = features(df).merge(land_areas(), on="GEO_ID", how="left")
    f["pop_density_km2"] = f["pop"] / f["land_km2"]
    f["geoid"] = f["GEO_ID"].str.split("US").str[-1]
    sel = {
        "ny_zcta": f["GEO_ID"].str.startswith("860Z200US"),
        "ny_county": f["GEO_ID"].str.startswith("0500000US36"),
        "tompkins_tract": f["GEO_ID"].str.startswith("1400000US36109"),
        "tompkins_bg": f["GEO_ID"].str.startswith("1500000US36109"),
    }
    for name, m in sel.items():
        out = f[m].reset_index(drop=True)
        out.to_parquet(OUT / f"acs_features_{name}.parquet", index=False)
        print(name, out.shape)


if __name__ == "__main__":
    main()
