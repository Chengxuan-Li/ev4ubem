"""Prototype: allocate observed ZIP-level EV stock to Tompkins parcels / block groups under alternative assumptions.

Purpose: quantify how much sub-ZIP EV placement depends on unvalidated allocation assumptions
(hypotheses 2 and 6). Reproducing ZIP totals is guaranteed by construction and validates nothing below ZIP.

Steps
1. Residential parcels (NYS ITS 2025 roll) -> centroid -> Tompkins block group (TIGER 2024) and ZCTA (CB 2020).
2. Initial dwelling-unit estimate by property class (RPS codes): single-unit classes (210, 240-242, 250, 270, 283)
   = 1; 215/220 = 2; 230 = 3; 271/280/281 = 2; 482 = 2; 483 = 3; 411 (apartments) = max(4, GFA / 1,000 ft^2);
   416 (mobile home park) = 10. Seasonal (260), commercial, and college (613) parcels get 0 households.
3. Calibrate within each block group, separately for single-unit and multi-unit structures, to ACS 2020-2024
   occupied housing units by structure type (B25032). Tenure split within structure type from B25032.
4. Household-class weights (relative EV propensity per occupied unit):
   S0 uniform per occupied unit
   S1 vehicles: BG vehicles per household by tenure (B25044)
   S2 home type: NHTS 2022 relative plug-in household propensity (detached/attached vs apartment vs mobile)
   S3 S2 x BG income index: NHTS relative propensity by income band applied to the BG B19001 distribution
      (independence assumption between home type and income — overstates contrasts if they are correlated)
5. Allocate each ZIP's observed EVs (DMV 2026, county=TOMPKINS residents, VIN-decoded) to parcels in that ZCTA
   proportional to weight x units. PO-box ZIPs 14851/14852 fold into 14850.
Outputs
  results/tables/subzip_allocation_bg.csv            BG EVs under S0-S3, households, EV/HH, spread ratios
  results/tables/subzip_allocation_summary.csv       share of EVs in multi-unit housing etc. by scenario
  data/processed/allocation/parcel_ev_allocation.parquet (SWIS_SBL_ID, PROP_CLASS, bg, zcta, units, S0..S3)
  results/maps/subzip_allocation_bg_S0_vs_S3.png     (EPSG:32618 for plotting)
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.paths import MAPS, PROCESSED, RAW, TABLES, ensure

SINGLE = {"210": 1, "240": 1, "241": 1, "242": 1, "250": 1, "270": 1, "283": 1}
MULTI = {"215": 2, "220": 2, "230": 3, "271": 2, "280": 2, "281": 2, "482": 2, "483": 3, "416": 10}
NHTS_HOME_REL = {"single": 1.25, "multi": 0.20, "mobile": 0.35}  # from results/tables/nhts_ev_propensity_by_class.csv (rounded)
NHTS_INC_REL = [0.31, 1.00, 0.94, 2.22, 3.71]  # <50k, 50-100k, 100-125k, 125-150k, 150k+


def parcels() -> gpd.GeoDataFrame:
    p = gpd.read_file(RAW / "parcels" / "tompkins_parcels_2025.gpkg")
    p["PROP_CLASS"] = p["PROP_CLASS"].astype(str).str[:3]
    gfa = pd.to_numeric(p["GFA"], errors="coerce")
    p["units0"] = p["PROP_CLASS"].map({**SINGLE, **MULTI}).astype(float)
    apt = p["PROP_CLASS"] == "411"
    p.loc[apt, "units0"] = np.maximum(4, (gfa[apt].fillna(4000) / 1000).round())
    p["struct"] = np.where(p["PROP_CLASS"].isin(SINGLE), "single", np.where(p["units0"].notna(), "multi", None))
    p.loc[p["PROP_CLASS"] == "270", "struct"] = "mobile"
    p = p[p["units0"].notna()].copy()
    c = p.to_crs(32618).geometry.representative_point().to_crs(4326)
    pts = gpd.GeoDataFrame(p.drop(columns="geometry"), geometry=c, crs=4326)
    bg = gpd.read_file(PROCESSED / "geography" / "tompkins_bg.gpkg")[["GEOID", "geometry"]].rename(columns={"GEOID": "bg"})
    z = gpd.read_file(PROCESSED / "geography" / "tompkins_area_zcta.gpkg")[["ZCTA5CE20", "geometry"]].rename(columns={"ZCTA5CE20": "zcta"})
    pts = gpd.sjoin(pts, bg, how="left", predicate="within").drop(columns="index_right")
    pts = gpd.sjoin(pts, z, how="left", predicate="within").drop(columns="index_right")
    return pts


def acs_bg() -> pd.DataFrame:
    acs = RAW / "census" / "acs5_2024"
    b32 = pd.read_parquet(acs / "b25032_ny.parquet")
    b44 = pd.read_parquet(acs / "b25044_ny.parquet")
    b19 = pd.read_parquet(acs / "b19001_ny.parquet")
    d = b32.merge(b44, on="GEO_ID").merge(b19, on="GEO_ID")
    d = d[d["GEO_ID"].str.startswith("1500000US36109")].copy()
    d["bg"] = d["GEO_ID"].str[-12:]
    e = lambda t, ls: sum(d[f"{t}_E{l:03d}"].clip(lower=0) for l in ls)  # noqa: E731
    out = pd.DataFrame({"bg": d["bg"]})
    out["own_single"] = e("B25032", [3, 4]); out["own_multi"] = e("B25032", [5, 6, 7, 8, 9, 10]); out["own_mobile"] = e("B25032", [11, 12])
    out["rent_single"] = e("B25032", [14, 15]); out["rent_multi"] = e("B25032", [16, 17, 18, 19, 20, 21]); out["rent_mobile"] = e("B25032", [22, 23])
    out["veh_per_owner_hh"] = sum(d[f"B25044_E{l:03d}"] * k for l, k in zip(range(3, 9), range(6))) / d["B25044_E002"].replace(0, np.nan)
    out["veh_per_renter_hh"] = sum(d[f"B25044_E{l:03d}"] * k for l, k in zip(range(10, 16), range(6))) / d["B25044_E009"].replace(0, np.nan)
    tot = d["B19001_E001"].replace(0, np.nan)
    bins = [range(2, 12), range(12, 14), [14], [15], [16, 17]]
    out["income_index"] = sum(sum(d[f"B19001_E{l:03d}"] for l in b) / tot * r for b, r in zip(bins, NHTS_INC_REL))
    return out.fillna({"veh_per_owner_hh": 0, "veh_per_renter_hh": 0, "income_index": 1.0})


def main() -> None:
    ensure(TABLES, MAPS, PROCESSED / "allocation")
    p = parcels()
    a = acs_bg()
    # calibrate units within BG x structure group to ACS occupied units
    grp = p.groupby(["bg", "struct"])["units0"].sum().rename("units0_sum").reset_index()
    rows = []
    for s in ["single", "multi", "mobile"]:
        acs_occ = a[["bg"]].assign(struct=s, acs_occ=a[f"own_{s}"] + a[f"rent_{s}"],
                                   own_frac=a[f"own_{s}"] / (a[f"own_{s}"] + a[f"rent_{s}"]).replace(0, np.nan))
        rows.append(acs_occ)
    acs_long = pd.concat(rows)
    cal = grp.merge(acs_long, on=["bg", "struct"], how="left")
    cal["scale"] = cal["acs_occ"] / cal["units0_sum"]
    unmatched = acs_long.merge(grp, on=["bg", "struct"], how="left")
    unalloc = unmatched[unmatched["units0_sum"].isna()]["acs_occ"].sum()
    p = p.merge(cal[["bg", "struct", "scale", "own_frac"]], on=["bg", "struct"], how="left")
    p["hh"] = p["units0"] * p["scale"].fillna(0)
    p["own_frac"] = p["own_frac"].fillna(0.5)
    p = p.merge(a[["bg", "veh_per_owner_hh", "veh_per_renter_hh", "income_index"]], on="bg", how="left")
    p["w_S0"] = 1.0
    p["w_S1"] = p["own_frac"] * p["veh_per_owner_hh"] + (1 - p["own_frac"]) * p["veh_per_renter_hh"]
    p["w_S2"] = p["struct"].map(NHTS_HOME_REL)
    p["w_S3"] = p["w_S2"] * p["income_index"]

    ev = pd.read_csv(PROCESSED / "dmv" / "tompkins_ev_stock_zip_2026.csv", dtype={"zip": str})
    ev = ev[ev["drivetrain"].isin(["BEV", "PHEV"])].copy()
    ev["zip"] = ev["zip"].replace({"14851": "14850", "14852": "14850"})
    evz = ev.groupby("zip")["vehicles"].sum()
    zips_with_hh = set(p.loc[p["hh"] > 0, "zcta"].dropna())
    fold = {z: "14850" for z in evz.index if z not in zips_with_hh}
    evz = evz.rename(index=fold).groupby(level=0).sum()
    for s in ["S0", "S1", "S2", "S3"]:
        wh = p["hh"] * p[f"w_{s}"]
        p[s] = wh / wh.groupby(p["zcta"]).transform("sum") * p["zcta"].map(evz).fillna(0)
    p[["SWIS_SBL_ID", "PROP_CLASS", "struct", "bg", "zcta", "units0", "hh", "S0", "S1", "S2", "S3"]].to_parquet(
        PROCESSED / "allocation" / "parcel_ev_allocation.parquet", index=False)

    bgt = p.groupby("bg")[["hh", "S0", "S1", "S2", "S3"]].sum().reset_index()
    for s in ["S0", "S1", "S2", "S3"]:
        bgt[f"{s}_per_hh"] = bgt[s] / bgt["hh"].replace(0, np.nan)
    bgt["max_min_ratio"] = bgt[["S0", "S1", "S2", "S3"]].max(axis=1) / bgt[["S0", "S1", "S2", "S3"]].min(axis=1).replace(0, np.nan)
    bgt.round(3).to_csv(TABLES / "subzip_allocation_bg.csv", index=False)

    summ = []
    tot_alloc = p[["S0", "S1", "S2", "S3"]].sum()
    for s in ["S0", "S1", "S2", "S3"]:
        summ.append({"scenario": s, "evs_allocated": tot_alloc[s], "evs_observed_in_zips": evz.sum(),
                     "share_in_multi_unit": p.loc[p["struct"] == "multi", s].sum() / tot_alloc[s],
                     "share_in_single_unit": p.loc[p["struct"] == "single", s].sum() / tot_alloc[s],
                     "bg_ev_per_hh_cv": bgt[f"{s}_per_hh"].std() / bgt[f"{s}_per_hh"].mean(),
                     "median_abs_bg_diff_vs_S0": (bgt[s] - bgt["S0"]).abs().median()})
    summ.append({"scenario": "diagnostic", "unallocated_acs_occupied_units_no_matching_parcels": unalloc,
                 "calibrated_households": p["hh"].sum(), "acs_occupied_units_total": acs_long["acs_occ"].sum(),
                 "evs_in_zips_without_parcels": float(evz[~evz.index.isin(p["zcta"].dropna())].sum())})
    pd.DataFrame(summ).round(4).to_csv(TABLES / "subzip_allocation_summary.csv", index=False)

    bgg = gpd.read_file(PROCESSED / "geography" / "tompkins_bg.gpkg").rename(columns={"GEOID": "bg"}).merge(bgt, on="bg").to_crs(32618)
    fig, ax = plt.subplots(1, 3, figsize=(15, 6))
    vmax = np.nanpercentile(bgg[["S0_per_hh", "S3_per_hh"]].values, 95)
    for i, s in enumerate(["S0", "S3"]):
        bgg.plot(column=f"{s}_per_hh", ax=ax[i], legend=True, vmin=0, vmax=vmax, cmap="viridis", edgecolor="w", linewidth=0.2)
        ax[i].set_title(f"EVs per household by BG, {s}"); ax[i].set_axis_off()
    bgg.plot(column="max_min_ratio", ax=ax[2], legend=True, cmap="magma_r", vmin=1, vmax=3, edgecolor="w", linewidth=0.2)
    ax[2].set_title("max/min BG EVs across S0-S3"); ax[2].set_axis_off()
    fig.suptitle("Tompkins sub-ZIP EV allocation sensitivity (inferred, not observed; EPSG:32618)")
    fig.tight_layout()
    fig.savefig(MAPS / "subzip_allocation_bg_S0_vs_S3.png", dpi=130)
    print(pd.DataFrame(summ).round(3).to_string())


if __name__ == "__main__":
    main()
