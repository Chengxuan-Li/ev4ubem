"""Synthetic dwelling units (DU) with household attributes for Tompkins County (model basic unit).

Pipeline (seeded, reproducible):
1. Parcels (NYS ITS 2025 roll) -> representative point -> block group (TIGER 2024) and ZCTA (CB 2020).
2. Initial DU estimate and structure class per residential parcel from RPS property class:
     210 (1-family) SFD; 215/220 2-family, 230 3-family, 280/281 multiple residences -> MF2_4;
     411 apartments -> MF5_19 or MF20P with units = max(5, GFA / 900 ft²); 482/483 converted/row with apts -> MF2_4 (3 units);
     240-242/250/283 rural/estate/residence-with-use -> SFD; 270 mobile home -> MOBILE; 271 multiple mobile homes and
     416 mobile-home parks -> MOBILE (2 and 20 units).
   Townhouse building style on 210 parcels -> SFA.
3. Calibration: within each BG, DU counts per structure class are scaled to ACS 2020-2024 occupied housing units by
   structure (B25032, owner+renter; SFD=1 detached, SFA=1 attached, MF2_4=2 and 3-4 units, MF5_19=5-9 and 10-19,
   MF20P=20+, MOBILE=mobile+boat/RV) and stochastically rounded. ACS units whose structure class has no parcels in the
   BG are placed on the BG's parcels of the nearest class (MF20P<->MF5_19<->MF2_4<->SFA<->SFD; MOBILE->SFD) and logged.
4. Household attributes: each DU draws tenure from the BG's B25032 tenure split for its structure class, then a PUMS
   household (ACS 2020-2024 5-year, PUMA 02300 = Tompkins County, occupied units) matching structure group and tenure,
   with probability proportional to PUMS weight raked (IPF) to the BG marginals: tenure x vehicles (B25044) and income
   bands (B19001: <50k, 50-100k, 100-150k, 150k+).
Outputs
  data/processed/synthetic/dwelling_units.parquet  du_id, parcel (SWIS_SBL_ID), bg, zcta, structure, tenure, hincp,
      income_band, veh, np, wif (workers), noc, pums_serialno, x_utm, y_utm (EPSG:32618 representative point of parcel)
  results/tables/synthetic_dwellings_validation_bg.csv   ACS vs synthetic BG marginals
  results/tables/synthetic_dwellings_summary.csv
Limitations: group quarters (dorms, ~Cornell/Ithaca College students) are not households and are excluded; parcel
unit counts for apartments are approximate; one PUMA pool for all BGs (joint structure within PUMA assumed uniform).
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from src.utils.paths import PROCESSED, RAW, TABLES, ensure

SEED = 20260914
OUT = PROCESSED / "synthetic"
CLASSES = ["SFD", "SFA", "MF2_4", "MF5_19", "MF20P", "MOBILE"]
NEAREST = {"MF20P": ["MF5_19", "MF2_4", "SFA", "SFD"], "MF5_19": ["MF20P", "MF2_4", "SFA", "SFD"],
           "MF2_4": ["MF5_19", "SFA", "SFD", "MF20P"], "SFA": ["SFD", "MF2_4", "MF5_19"], "SFD": ["SFA", "MF2_4", "MOBILE"],
           "MOBILE": ["SFD", "SFA", "MF2_4"]}
INC_BANDS = ["<50k", "50-100k", "100-150k", "150k+"]
# PUMS BLD codes: 1 mobile, 2 1-detached, 3 1-attached, 4 2 units, 5 3-4, 6 5-9, 7 10-19, 8 20-49, 9 50+, 10 boat/RV
BLD_CLASS = {1: "MOBILE", 2: "SFD", 3: "SFA", 4: "MF2_4", 5: "MF2_4", 6: "MF5_19", 7: "MF5_19", 8: "MF20P", 9: "MF20P", 10: "MOBILE"}


def parcel_units() -> gpd.GeoDataFrame:
    p = gpd.read_file(RAW / "parcels" / "tompkins_parcels_2025.gpkg")
    pc = p["PROP_CLASS"].astype(str).str[:3]
    gfa = pd.to_numeric(p["GFA"], errors="coerce")
    cls = pd.Series(None, index=p.index, dtype=object)
    units = pd.Series(np.nan, index=p.index)
    cls[pc.isin(["210", "240", "241", "242", "250", "283"])] = "SFD"
    units[cls == "SFD"] = 1
    town = pc.eq("210") & p["BLDG_STYLE_DESC"].fillna("").str.contains("Townhouse|Row", case=False)
    cls[town] = "SFA"
    cls[pc.isin(["215", "220"])] = "MF2_4"; units[pc.isin(["215", "220"])] = 2
    cls[pc.eq("230")] = "MF2_4"; units[pc.eq("230")] = 3
    cls[pc.isin(["280", "281"])] = "MF2_4"; units[pc.isin(["280", "281"])] = 2
    cls[pc.isin(["482", "483"])] = "MF2_4"; units[pc.isin(["482", "483"])] = 3
    apt = pc.eq("411")
    au = np.maximum(5, (gfa.fillna(4500) / 900).round())
    units[apt] = au[apt]
    cls[apt] = np.where(au[apt] >= 20, "MF20P", "MF5_19")
    cls[pc.eq("270")] = "MOBILE"; units[pc.eq("270")] = 1
    cls[pc.eq("271")] = "MOBILE"; units[pc.eq("271")] = 2
    cls[pc.eq("416")] = "MOBILE"; units[pc.eq("416")] = 20
    p["structure"], p["units0"] = cls, units
    p = p[p["units0"].notna()].copy()
    pts = p.to_crs(32618).geometry.representative_point()
    p["x_utm"], p["y_utm"] = pts.x.values, pts.y.values
    g = gpd.GeoDataFrame(p[["SWIS_SBL_ID", "PROP_CLASS", "structure", "units0", "x_utm", "y_utm"]], geometry=pts.to_crs(4326).values, crs=4326)
    bg = gpd.read_file(PROCESSED / "geography" / "tompkins_bg.gpkg")[["GEOID", "geometry"]].rename(columns={"GEOID": "bg"})
    z = gpd.read_file(PROCESSED / "geography" / "tompkins_area_zcta.gpkg")[["ZCTA5CE20", "geometry"]].rename(columns={"ZCTA5CE20": "zcta"})
    g = gpd.sjoin(g, bg, how="left", predicate="within").drop(columns="index_right")
    g = gpd.sjoin(g, z, how="left", predicate="within").drop(columns="index_right")
    return g[g["bg"].notna()]


def acs_bg() -> dict[str, pd.DataFrame]:
    acs = RAW / "census" / "acs5_2024"
    sel = lambda t: pd.read_parquet(acs / f"{t}_ny.parquet").query("GEO_ID.str.startswith('1500000US36109')", engine="python").assign(bg=lambda d: d["GEO_ID"].str[-12:]).set_index("bg")  # noqa: E731
    b32, b44, b19 = sel("b25032"), sel("b25044"), sel("b19001")
    e = lambda d, ls: sum(d[f"{d.columns[1][:6]}_E{l:03d}"].clip(lower=0) for l in ls)  # noqa: E731
    lines = {"SFD": ([3], [14]), "SFA": ([4], [15]), "MF2_4": ([5, 6], [16, 17]), "MF5_19": ([7, 8], [18, 19]),
             "MF20P": ([9, 10], [20, 21]), "MOBILE": ([11, 12], [22, 23])}
    struct = pd.DataFrame({(c, t): e(b32, l[i]) for c, l in lines.items() for i, t in enumerate(["own", "rent"])})
    veh = pd.DataFrame({(t, k): b44[f"B25044_E{base + k:03d}"].clip(lower=0) for t, base in [("own", 3), ("rent", 10)] for k in range(6)})
    inc = pd.DataFrame({"<50k": e(b19, range(2, 12)), "50-100k": e(b19, [12, 13]), "100-150k": e(b19, [14, 15]), "150k+": e(b19, [16, 17])})
    return {"struct": struct, "veh": veh, "inc": inc}


def pums_pool() -> pd.DataFrame:
    h = pd.read_parquet(RAW / "census" / "pums_2024_5yr" / "psam_h36_slim.parquet")
    h = h[(h["PUMA"] == "02300") & (h["TYPEHUGQ"] == 1) & (h["WGTP"] > 0) & h["TEN"].notna()].copy()
    h["structure"] = h["BLD"].map(BLD_CLASS)
    h["tenure"] = np.where(h["TEN"].isin([1, 2]), "own", "rent")
    h["veh"] = h["VEH"].fillna(0).clip(upper=5).astype(int)
    inc = h["HINCP"] * h["ADJINC"] / 1e6
    h["hincp_adj"] = inc
    h["income_band"] = pd.cut(inc, [-np.inf, 50000, 100000, 150000, np.inf], labels=INC_BANDS, right=False).astype(str)
    return h.reset_index(drop=True)


def rake(w0: np.ndarray, pool: pd.DataFrame, bg_row: dict, iters: int = 30) -> np.ndarray:
    w = w0.astype(float).copy()
    tv_key = pool["tenure"] + "|" + pool["veh"].astype(str)
    for _ in range(iters):
        for key_series, targets in [(pool["tenure"] + "|" + pool["structure"], bg_row["struct"]), (tv_key, bg_row["veh"]),
                                    (pool["income_band"], bg_row["inc"])]:
            tot = pd.Series(w).groupby(key_series.values).sum()
            for k, tgt in targets.items():
                if k in tot.index and tot[k] > 0:
                    w[(key_series == k).values] *= tgt / tot[k]
    return w


def main() -> None:
    ensure(OUT, TABLES)
    rng = np.random.default_rng(SEED)
    par = parcel_units()
    acs = acs_bg()
    pool = pums_pool()
    rows, logs = [], []
    for bg, pb in par.groupby("bg"):
        s = acs["struct"].loc[bg] if bg in acs["struct"].index else None
        if s is None:
            continue
        targets = {c: float(s[(c, "own")] + s[(c, "rent")]) for c in CLASSES}
        # DU counts per (parcel, ACS structure class), with nearest-class spill for classes lacking parcels;
        # DUs inherit the ACS structure class so that BG tenure x structure marginals are preserved.
        alloc = {}
        for c in CLASSES:
            t = targets[c]
            if t <= 0:
                continue
            cand = pb[pb["structure"] == c]
            used = c
            if cand.empty:
                for alt in NEAREST[c]:
                    cand = pb[pb["structure"] == alt]
                    if not cand.empty:
                        used = alt
                        break
            if cand.empty:
                logs.append({"bg": bg, "class": c, "acs_units": t, "placed_on": None})
                continue
            if used != c:
                logs.append({"bg": bg, "class": c, "acs_units": t, "placed_on": used})
            share = cand["units0"] / cand["units0"].sum()
            for idx, v in (t * share).items():
                alloc[(idx, c)] = alloc.get((idx, c), 0.0) + v
        keys = list(alloc)
        vals = np.array([alloc[k] for k in keys])
        n = np.floor(vals) + (rng.random(len(vals)) < (vals - np.floor(vals)))
        bg_row = {"struct": {f"{t}|{c}": float(s[(c, t)]) for c in CLASSES for t in ["own", "rent"]},
                  "veh": {f"{t}|{k}": float(acs["veh"].loc[bg, (t, k)]) for t in ["own", "rent"] for k in range(6)},
                  "inc": acs["inc"].loc[bg].to_dict()}
        w = rake(pool["WGTP"].values, pool, bg_row)
        for (idx, c), cnt in zip(keys, n.astype(int)):
            if cnt <= 0:
                continue
            prow = pb.loc[idx]
            own_t, rent_t = float(s[(c, "own")]), float(s[(c, "rent")])
            p_own = own_t / (own_t + rent_t) if own_t + rent_t > 0 else 0.5
            ten = np.where(rng.random(cnt) < p_own, "own", "rent")
            for tval in ["own", "rent"]:
                k = int((ten == tval).sum())
                if k == 0:
                    continue
                pw = None
                for m in [(pool["tenure"] == tval) & (pool["structure"] == c), pool["tenure"] == tval]:
                    cand_w = w * m.values
                    if m.sum() >= 5 and cand_w.sum() > 0:
                        pw = cand_w
                        break
                if pw is None:
                    pw = pool["WGTP"].values * ((pool["tenure"] == tval).values)
                pick = rng.choice(len(pool), size=k, p=pw / pw.sum())
                for j in pick:
                    hh = pool.iloc[j]
                    rows.append((prow["SWIS_SBL_ID"], bg, prow["zcta"], c, tval, hh["hincp_adj"], hh["income_band"], int(hh["veh"]),
                                 int(hh["NP"]), hh["WIF"], hh["NOC"], hh["SERIALNO"], prow["x_utm"], prow["y_utm"]))
    du = pd.DataFrame(rows, columns=["parcel", "bg", "zcta", "structure", "tenure", "hincp", "income_band", "veh", "np", "wif", "noc",
                                     "pums_serialno", "x_utm", "y_utm"])
    du.insert(0, "du_id", np.arange(len(du)))
    du.to_parquet(OUT / "dwelling_units.parquet", index=False)

    # validation: BG marginals ACS vs synthetic
    val = []
    for bg, d in du.groupby("bg"):
        s = acs["struct"].loc[bg]
        for c in CLASSES:
            for t in ["own", "rent"]:
                val.append({"bg": bg, "margin": "tenure_structure", "cell": f"{t}|{c}", "acs": float(s[(c, t)]),
                            "synthetic": int(((d["structure"] == c) & (d["tenure"] == t)).sum())})
        for t in ["own", "rent"]:
            for k in range(6):
                val.append({"bg": bg, "margin": "tenure_vehicles", "cell": f"{t}|{k}", "acs": float(acs["veh"].loc[bg, (t, k)]),
                            "synthetic": int(((d["tenure"] == t) & (d["veh"] == k)).sum())})
        for b in INC_BANDS:
            val.append({"bg": bg, "margin": "income", "cell": b, "acs": float(acs["inc"].loc[bg, b]), "synthetic": int((d["income_band"] == b).sum())})
    val = pd.DataFrame(val)
    val.to_csv(TABLES / "synthetic_dwellings_validation_bg.csv", index=False)
    summ = []
    for mg, v in val.groupby("margin"):
        tot = v["acs"].sum()
        summ.append({"metric": f"SRMSE {mg} (BG cells)", "value": float(np.sqrt(((v["acs"] - v["synthetic"]) ** 2).mean()) / v["acs"].mean())})
        summ.append({"metric": f"R2 {mg} (BG cells)", "value": float(1 - ((v["acs"] - v["synthetic"]) ** 2).sum() / ((v["acs"] - v["acs"].mean()) ** 2).sum())})
        summ.append({"metric": f"total ACS {mg}", "value": tot})
    summ += [{"metric": "synthetic DUs", "value": len(du)}, {"metric": "BGs", "value": du["bg"].nunique()},
             {"metric": "ACS units placed on other structure class", "value": float(sum(l["acs_units"] for l in logs if l["placed_on"]))},
             {"metric": "ACS units not placed (no parcels)", "value": float(sum(l["acs_units"] for l in logs if not l["placed_on"]))},
             {"metric": "synthetic household vehicles", "value": int(du["veh"].sum())}]
    pd.DataFrame(summ).round(4).to_csv(TABLES / "synthetic_dwellings_summary.csv", index=False)
    print(pd.DataFrame(summ).round(3).to_string())
    print(du.groupby(["structure", "tenure"]).size().unstack())


if __name__ == "__main__":
    main()
