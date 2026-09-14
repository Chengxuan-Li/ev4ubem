r"""In-commuter EV charging in Tompkins County: how much charging is missing because commuters' EVs are registered elsewhere.

The resident load model (src/model/load_assembly.py) only counts EVs in the Tompkins DMV stock. EVs owned by people
who live elsewhere and work in Tompkins charge at Tompkins workplaces and public chargers, so they are left out.
The resident model has the opposite error too: it places *all* residents' workplace charging at Tompkins sites, but
some residents work in other counties. This module estimates both terms with public data and reports gross and net
effects as low / central / high bounding cases (every parameter set to its low or high value together).

Data
  LEHD LODES8 NY OD 2023 (main + aux, JT00 all jobs and JT01 primary jobs), 2020 blocks   (src.acquisition.lehd_lodes)
  NYS DMV 2026-09 statewide county EV stock (VIN-decoded)       data/processed/dmv/ny_county_ev_2026.csv
  ACS 2020-2024 B08301 means of transportation to work, by county of residence   data/raw/census/acs5_2024/b08301_ny.parquet
  Charging library 2026/2035 archetype means                     data/processed/charging/library_summary_{year}.csv
  Charging parameters (workplace access/use)                     src/model/charging_params.py
  Resident model annual pools (trend/base)                       results/tables/load_scenarios_annual.csv
  Growth trajectory EV_p50(y) by ownership scenario              data/processed/growth/growth_parameters_by_year.csv
  Resident EV expectation by residence BG                        data/processed/model/du_ev_2026.parquet
  Census 2024 Gazetteer county internal points; Tompkins 2024 TIGER BGs  data/processed/geography/tompkins_bg.gpkg

Equations (o = residence county, b = Tompkins workplace block group, y = year, s = scenario)
  Jobs:      J_{o,b} = Σ_{blocks} S000   (LODES h_geocode[:5] = o, w_geocode[:12] = b; JT01 low/central, JT00 high)
  Screen:    keep o if d_o ≤ D_s, where d_o is the great-circle distance between county internal points
             (D = 80 / 100 / 160 km). This drops jobs that are administratively located in Tompkins but held by people
             living in NYC, New Jersey, etc., who are unlikely to commute daily.
  Vehicles per job, from ACS B08301 at origin o:
             veh_o = drove_alone + Σ_k carpool_k / occupancy_k   (occupancy 2, 3, 4, 5.5, 7.5)
             low     v_o = veh_o / workers_o                     (origin average: walking, transit and WFH do not use a car)
             central v_o = (1 − wfh_o) · veh_o / car_commuters_o (every non-WFH in-commuter drives, at origin car occupancy)
             high    v_o = veh_o / car_commuters_o               (no working from home)
             Out-of-state origins take the job-weighted mean v of the screened NY origins.
  EV share:  e_o(y) = min(0.95, e_o(2026) · σ_s · M_s(y)),  M_s(y) = EV_p50(y) / EV_p50(2026)  (Tompkins growth model;
             low slow, central trend, high policy). e_o(2026) is the DMV LDV EV share (low) or the passenger-class EV
             share (central/high). σ_s is a commuter-selection multiplier (1.0 / 1.0 / 1.5). Out-of-state 2026 e is an
             assumption (0.5 % / 1.0 % / 2.0 %).
  In-commuter EVs:   N_o = Σ_b J_{o,b} · v_o · e_o ;   BEV share = 1 − PHEV share of origin EV stock (2026 DMV; later years:
             Tompkins trend BEV share)
  Workplace users:   U_o = N_o · p_access(y) · p_use ,  p_use = 0.65 ; p_access(2026) = 0.17 / 0.23 / 0.30
             (resident model: 0.23; 2035: 0.23 / 0.32 / 0.45)
  Workplace energy:  E^{work}_o = U_o · f_d · k^{work}_{v}(y) ,  where k^{work}_v is the library mean annual workplace kWh of a
             workplace-user EV (single-family owner class, mixture from load_assembly.archetype_probs conditional on
             work = 1). f_d = 0.9 / 1.0 / 1.25 accounts for longer commutes, which leave a larger battery deficit on
             arrival (assumption).
  Public top-up in Tompkins:  E^{pub}_o = N_o · φ · k^{pub}_v(y) , where k^{pub} is the library mean public L2 + DCFC kWh
             per EV (excluding en-route) and φ = 0.15 / 0.30 / 0.60 is the share of that non-home charging done in
             Tompkins (assumption).
  Gross gap:  G = Σ_o (E^{work}_o + E^{pub}_o)
  Out-commuter offsets (the resident model places all resident non-home charging at Tompkins sites):
             R_work = W_res(y) · ω_D
             R_pub  = (P^{L2}_res(y) + P^{DCFC}_res(y) · χ) · ω_D · φ
             W_res, P_res are the resident workplace, public L2 and DCFC pools from load_assembly for the matching
             scenario (ownership = growth scenario of the case; charging = access+ for high, base otherwise).
             χ = non-en-route share of DCFC energy (library; the DCFC pool includes en-route sessions).
             ω_D = Σ_r E_r · out_r / jobs_r / Σ_r E_r is the EV-weighted share of Tompkins residents' LODES primary jobs that
             are outside Tompkins but within D km (r = residence BG, E_r = expected resident EVs, du_ev_2026). Tompkins
             residents' jobs in other states (other states' aux files) are ignored.
  Net:        N = G − R_work − R_pub. Low = G_low − R(D_high, φ_high); high = G_high − R(D_low, φ_low) (bounding).
  BG siting:  E_b ∝ Σ_o J_{o,b} · v_o · e_o · (energy per EV of origin o)

Assumptions and caveats: LODES counts jobs, not workers or cars. Jobs are held at 2023 levels through 2026–2035.
LODES blocks carry noise infusion, so only BG and county totals are reported. Federal jobs are included in JT00/JT01;
self-employed workers are not. ACS mode shares describe all workers living in the origin county, not only those who
commute to Tompkins. Classes: flows A (LODES, administrative with noise); EV shares B/A; per-EV energy E (model
library); energy gap E conditional on assumptions.

Outputs
  results/tables/incommuter_flows_by_origin.csv      origin × jobs, distance, v, e, EVs and MWh (central), screens
  results/tables/incommuter_charging_estimate.csv    low/central/high × 2026/2035 with every parameter value
  results/tables/incommuter_workplace_by_bg.csv      Tompkins workplace BG: jobs, in-commuter share, EVs, MWh
  results/figures/incommuter_charging.png
  data/interim/lehd_lodes/*.parquet                  cached Tompkins-related OD rows (git-ignored)
"""
from __future__ import annotations

import zipfile

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.model.charging_params import value
from src.model.load_assembly import archetype_probs
from src.utils.paths import FIGURES, INTERIM, PROCESSED, RAW, TABLES, ensure

LODES_YEAR = 2023
TOMP = "36109"
RAW_L = RAW / "lehd_lodes"
CACHE = INTERIM / "lehd_lodes"
WORK_GREEN = "#55A868"

SCEN = {
    "low": {"jt": "JT01", "radius_km": 80, "veh_rule": "origin_average", "ev_share_col": "ldv", "selection": 1.0,
            "oos_ev_share_2026": 0.005, "access": {2026: 0.17, 2035: 0.23}, "use": 0.65, "kwh_factor": 0.9,
            "public_in_tompkins": 0.15, "growth_scenario": "slow"},
    "central": {"jt": "JT01", "radius_km": 100, "veh_rule": "non_wfh_drive", "ev_share_col": "pas", "selection": 1.0,
                "oos_ev_share_2026": 0.010, "access": {2026: 0.23, 2035: 0.32}, "use": 0.65, "kwh_factor": 1.0,
                "public_in_tompkins": 0.30, "growth_scenario": "trend"},
    "high": {"jt": "JT00", "radius_km": 160, "veh_rule": "all_drive", "ev_share_col": "pas", "selection": 1.5,
             "oos_ev_share_2026": 0.020, "access": {2026: 0.30, 2035: 0.45}, "use": 0.65, "kwh_factor": 1.25,
             "public_in_tompkins": 0.60, "growth_scenario": "policy"},
}
YEARS = [2026, 2035]


# ---------------------------------------------------------------- data
def od_tompkins(jt: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (jobs with workplace in Tompkins [NY + out-of-state residents], jobs of Tompkins residents), columns w, h, jobs."""
    ensure(CACHE)
    fw, fh = CACHE / f"tompkins_work_{jt}_{LODES_YEAR}.parquet", CACHE / f"tompkins_res_{jt}_{LODES_YEAR}.parquet"
    if fw.exists() and fh.exists():
        return pd.read_parquet(fw), pd.read_parquet(fh)
    dt = {"w_geocode": str, "h_geocode": str}
    w_parts, h_parts = [], []
    for part in ["main", "aux"]:
        src = RAW_L / f"ny_od_{part}_{jt}_{LODES_YEAR}.csv.gz"
        if not src.exists():
            raise FileNotFoundError(f"{src} missing: run python -m src.acquisition.lehd_lodes")
        n = 0
        for ch in pd.read_csv(src, dtype=dt, usecols=["w_geocode", "h_geocode", "S000"], chunksize=2_000_000):
            n += len(ch)
            w_parts.append(ch[ch["w_geocode"].str[:5] == TOMP])
            if part == "main":
                h_parts.append(ch[ch["h_geocode"].str[:5] == TOMP])
        print(f"  {src.name}: {n:,} rows")
    ren = {"w_geocode": "w", "h_geocode": "h", "S000": "jobs"}
    W, H = pd.concat(w_parts).rename(columns=ren), pd.concat(h_parts).rename(columns=ren)
    W.to_parquet(fw, index=False); H.to_parquet(fh, index=False)
    return W, H


def gazetteer() -> pd.DataFrame:
    with zipfile.ZipFile(RAW_L / "2024_Gaz_counties_national.zip") as z:
        g = pd.read_csv(z.open(z.namelist()[0]), sep="\t", dtype={"GEOID": str})
    g.columns = [c.strip() for c in g.columns]
    t = g[g["GEOID"] == TOMP].iloc[0]
    lat1, lon1, lat2, lon2 = map(np.radians, [t["INTPTLAT"], t["INTPTLONG"], g["INTPTLAT"], g["INTPTLONG"]])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    g["distance_km"] = 6371.0 * 2 * np.arcsin(np.sqrt(a))
    return g.rename(columns={"GEOID": "origin", "NAME": "name", "USPS": "state"})[["origin", "name", "state", "distance_km"]]


def acs_vehicles_per_job() -> pd.DataFrame:
    b = pd.read_parquet(RAW / "census" / "acs5_2024" / "b08301_ny.parquet")
    b = b[b["GEO_ID"].str.startswith("0500000US36")].copy()
    e = lambda i: b[f"B08301_E{i:03d}"].astype(float)  # noqa: E731
    veh = e(3) + e(5) / 2 + e(6) / 3 + e(7) / 4 + e(8) / 5.5 + e(9) / 7.5
    return pd.DataFrame({"origin": b["GEO_ID"].str[-5:], "acs_workers": e(1), "acs_drove_alone_share": e(3) / e(1),
                         "acs_wfh_share": e(21) / e(1), "acs_car_share": e(2) / e(1),
                         "v_origin_average": veh / e(1), "v_non_wfh_drive": (1 - e(21) / e(1)) * veh / e(2), "v_all_drive": veh / e(2)})


def dmv_shares(gaz: pd.DataFrame) -> pd.DataFrame:
    c = pd.read_csv(PROCESSED / "dmv" / "ny_county_ev_2026.csv")
    c = c[c["county"] != "OUT-OF-STATE"]
    ny = gaz[gaz["state"] == "NY"].copy()
    ny["county"] = ny["name"].str.replace(" County", "", regex=False).str.upper().str.replace(".", "", regex=False)
    m = ny.merge(c, on="county", how="left")
    if m["ldv"].isna().any():
        raise ValueError(f"unmatched DMV counties: {m.loc[m['ldv'].isna(), 'county'].tolist()}")
    return pd.DataFrame({"origin": m["origin"], "ev_share_ldv_2026": m["ev_share_ldv"], "ev_share_pas_2026": m["pas_ev"] / m["pas_ldv"],
                         "phev_share_of_ev_2026": m["phev_share_of_ev"], "dmv_ev_2026": m["bev"] + m["phev"]})


def growth_multiplier(scenario: str, year: int) -> float:
    g = pd.read_csv(PROCESSED / "growth" / "growth_parameters_by_year.csv")
    g = g[g["scenario"] == scenario].set_index("year")
    return float(g.loc[year, "EV_p50"] / g.loc[2026, "EV_p50"])


def bev_share_trend(year: int) -> float:
    g = pd.read_csv(PROCESSED / "growth" / "growth_parameters_by_year.csv").query("scenario == 'trend'").set_index("year")
    return float(g.loc[year, "BEV_p50"] / (g.loc[year, "BEV_p50"] + g.loc[year, "PHEV_p50"]))


def library_energy(year: int, chg: str = "base") -> dict:
    """Per-EV annual kWh from the charging library: workplace kWh of a workplace user; public L2+DCFC (no en-route) per EV."""
    s = pd.read_csv(PROCESSED / "charging" / f"library_summary_{year}.csv")
    key = ["drivetrain", "access", "level", "freq", "work", "managed"]
    s = s.set_index(key)
    out = {}
    for dt in ["BEV", "PHEV"]:
        pr = archetype_probs("SF", "own", 1, dt, year, chg)
        pr = {a: p for a, p in pr.items() if a in s.index and p > 0}
        pw = sum(p for a, p in pr.items() if a[4] == 1)
        out[f"kwh_work_per_user_{dt}"] = sum(p * s.loc[a, "kwh_work"] for a, p in pr.items() if a[4] == 1) / pw
        tot = sum(pr.values())
        out[f"kwh_public_per_ev_{dt}"] = sum(p * (s.loc[a, "kwh_public_l2"] + s.loc[a, "kwh_dcfc"]) for a, p in pr.items()) / tot
        if dt == "BEV":  # the DCFC site pool includes en-route sessions; library kwh_dcfc excludes them
            dc = sum(p * s.loc[a, "kwh_dcfc"] for a, p in pr.items())
            out["dcfc_nonenroute_share"] = dc / (dc + sum(p * s.loc[a, "kwh_enroute"] for a, p in pr.items()))
    return out


def resident_pools(year: int, own: str = "trend", chg: str = "base") -> dict:
    s = pd.read_csv(TABLES / "load_scenarios_annual.csv")
    r = s[(s["year"] == year) & (s["ownership_scenario"] == own) & (s["charging_scenario"] == chg)].iloc[0]
    return {"resident_work_mwh": float(r["annual_mwh_work"]), "resident_public_l2_mwh": float(r["annual_mwh_public_l2"]),
            "resident_dcfc_mwh": float(r["annual_mwh_dcfc"]), "total_mwh": float(r["annual_mwh_total"])}


def outcommute_share(H: pd.DataFrame, W: pd.DataFrame, gaz: pd.DataFrame, radius_km: float) -> dict:
    """EV-weighted share of Tompkins residents' NY jobs located outside Tompkins within radius_km."""
    dist = gaz.set_index("origin")["distance_km"]
    H = H.assign(wc=H["w"].str[:5], bg=H["h"].str[:12])
    H = H[H["wc"].map(dist).fillna(1e9) <= radius_km]
    H["out"] = np.where(H["wc"] != TOMP, H["jobs"], 0)
    by = H.groupby("bg")[["jobs", "out"]].sum()
    ev = pd.read_parquet(PROCESSED / "model" / "du_ev_2026.parquet").groupby("bg")["E_ev"].sum()
    by = by.join(ev, how="left").fillna({"E_ev": 0})
    by["share"] = by["out"] / by["jobs"].where(by["jobs"] > 0)
    w_ev = float((by["E_ev"] * by["share"].fillna(0)).sum() / by.loc[by["share"].notna(), "E_ev"].sum())
    return {"outcommute_share_jobs": float(by["out"].sum() / by["jobs"].sum()), "outcommute_share_ev_weighted": w_ev,
            "resident_jobs_in_county": float(by["jobs"].sum() - by["out"].sum()), "resident_jobs_out_screened": float(by["out"].sum())}


# ---------------------------------------------------------------- model
def origin_table(sc: str, year: int, W: pd.DataFrame, gaz: pd.DataFrame, acs: pd.DataFrame, dmv: pd.DataFrame, lib: dict) -> pd.DataFrame:
    p = SCEN[sc]
    W = W.assign(origin=W["h"].str[:5])
    o = W[W["origin"] != TOMP].groupby("origin")["jobs"].sum().rename("jobs").reset_index()
    o = o.merge(gaz, on="origin", how="left").merge(acs, on="origin", how="left").merge(dmv, on="origin", how="left")
    o["in_screen"] = o["distance_km"] <= p["radius_km"]
    vcol = {"origin_average": "v_origin_average", "non_wfh_drive": "v_non_wfh_drive", "all_drive": "v_all_drive"}[p["veh_rule"]]
    ny = o["state"] == "NY"
    scr = o[ny & o["in_screen"]]
    v_oos = float(np.average(scr[vcol], weights=scr["jobs"]))
    o["v"] = np.where(ny, o[vcol], v_oos)
    M = growth_multiplier(p["growth_scenario"], year)
    e26 = np.where(ny, o["ev_share_ldv_2026" if p["ev_share_col"] == "ldv" else "ev_share_pas_2026"] * p["selection"], p["oos_ev_share_2026"])
    o["ev_share"] = np.minimum(0.95, e26 * M)
    phev26 = np.where(ny, o["phev_share_of_ev_2026"], float(np.average(scr["phev_share_of_ev_2026"], weights=scr["jobs"])))
    o["bev_share"] = 1 - phev26 if year == 2026 else bev_share_trend(year)
    o["vehicles"] = o["jobs"] * o["v"] * o["in_screen"]
    o["evs"] = o["vehicles"] * o["ev_share"]
    pw = p["access"][year] * p["use"]
    o["workplace_users"] = o["evs"] * pw
    kw = o["bev_share"] * lib["kwh_work_per_user_BEV"] + (1 - o["bev_share"]) * lib["kwh_work_per_user_PHEV"]
    kp = o["bev_share"] * lib["kwh_public_per_ev_BEV"] + (1 - o["bev_share"]) * lib["kwh_public_per_ev_PHEV"]
    o["work_mwh"] = o["workplace_users"] * kw * p["kwh_factor"] / 1000
    o["public_mwh"] = o["evs"] * kp * p["public_in_tompkins"] / 1000
    o["gross_mwh"] = o["work_mwh"] + o["public_mwh"]
    o["kwh_per_job_screened"] = np.where(o["in_screen"], o["gross_mwh"] * 1000 / o["jobs"], 0.0)
    o.attrs.update({"growth_multiplier": M, "v_out_of_state": v_oos, "p_work_user": pw})
    return o


def estimate(W: dict, H: dict, gaz, acs, dmv) -> tuple[pd.DataFrame, dict]:
    rows, origins = [], {}
    libs = {y: library_energy(y) for y in YEARS}
    res_share = {r: outcommute_share(H["JT01"], W["JT01"], gaz, r) for r in sorted({p["radius_km"] for p in SCEN.values()})}
    opposite = {"low": "high", "central": "central", "high": "low"}
    for y in YEARS:
        for sc, p in SCEN.items():
            chg = "access+" if sc == "high" else "base"
            pools = resident_pools(y, p["growth_scenario"], chg)
            o = origin_table(sc, y, W[p["jt"]], gaz, acs, dmv, libs[y])
            origins[(sc, y)] = o
            q = o[o["in_screen"]]
            ny = q["state"] == "NY"
            off = res_share[SCEN[opposite[sc]]["radius_km"]]
            omega = off["outcommute_share_ev_weighted"]
            offset = pools["resident_work_mwh"] * omega
            # symmetric public offset: residents who work outside Tompkins do the same share φ of their non-home, non-en-route
            # public charging near work (outside Tompkins) as in-commuters do inside Tompkins
            pub_base = pools["resident_public_l2_mwh"] + pools["resident_dcfc_mwh"] * libs[y]["dcfc_nonenroute_share"]
            p_off = pub_base * omega * SCEN[opposite[sc]]["public_in_tompkins"]
            gross = q["gross_mwh"].sum()
            tomp_jobs = W[p["jt"]]["jobs"].sum()
            rows.append({
                "year": y, "case": sc, "evidence": "E (A flows x A/B EV shares x E library x assumptions)",
                "lodes_year": LODES_YEAR, "job_type": p["jt"], "radius_km": p["radius_km"], "vehicle_rule": p["veh_rule"],
                "ev_share_basis": p["ev_share_col"], "commuter_selection_multiplier": p["selection"],
                "out_of_state_ev_share_2026": p["oos_ev_share_2026"], "growth_scenario": p["growth_scenario"],
                "origin_ev_growth_multiplier": round(o.attrs["growth_multiplier"], 4),
                "workplace_access_per_worker": p["access"][y], "workplace_use_given_access": p["use"],
                "commute_kwh_factor": p["kwh_factor"], "public_share_in_tompkins": p["public_in_tompkins"],
                "kwh_work_per_user_bev": round(libs[y]["kwh_work_per_user_BEV"], 1), "kwh_work_per_user_phev": round(libs[y]["kwh_work_per_user_PHEV"], 1),
                "kwh_public_per_ev_bev": round(libs[y]["kwh_public_per_ev_BEV"], 1), "kwh_public_per_ev_phev": round(libs[y]["kwh_public_per_ev_PHEV"], 1),
                "jobs_in_tompkins_all_residences": tomp_jobs,
                "jobs_incommuters_all": o["jobs"].sum(), "jobs_incommuters_screened": q["jobs"].sum(),
                "jobs_incommuters_screened_out_of_state": q.loc[~ny, "jobs"].sum(),
                "incommuter_share_of_tompkins_jobs": o["jobs"].sum() / tomp_jobs,
                "incommuter_vehicles": q["vehicles"].sum(), "incommuter_evs": q["evs"].sum(),
                "incommuter_bevs": (q["evs"] * q["bev_share"]).sum(), "incommuter_workplace_users": q["workplace_users"].sum(),
                "mean_ev_share_screened": q["evs"].sum() / q["vehicles"].sum(),
                "workplace_mwh": q["work_mwh"].sum(), "public_topup_mwh": q["public_mwh"].sum(), "gross_mwh": gross,
                "resident_model_scenario": f"{p['growth_scenario']}/{chg}",
                "resident_workplace_mwh_model": pools["resident_work_mwh"], "total_mwh_model": pools["total_mwh"],
                "outcommute_radius_km": SCEN[opposite[sc]]["radius_km"],
                "resident_outcommute_share_jobs": off["outcommute_share_jobs"], "resident_outcommute_share_ev_weighted": omega,
                "outcommuter_workplace_offset_mwh": offset, "outcommuter_public_offset_mwh": p_off,
                "net_workplace_mwh": q["work_mwh"].sum() - offset, "net_mwh": gross - offset - p_off,
                "gross_workplace_over_resident_workplace": q["work_mwh"].sum() / pools["resident_work_mwh"],
                "gross_over_total": gross / pools["total_mwh"], "net_over_total": (gross - offset - p_off) / pools["total_mwh"],
                "gross_kwh_per_incommuter_ev": gross * 1000 / max(q["evs"].sum(), 1e-9),
            })
    return pd.DataFrame(rows), origins, res_share


def bg_table(W: pd.DataFrame, H_unused, o: pd.DataFrame) -> pd.DataFrame:
    W = W.assign(origin=W["h"].str[:5], bg=W["w"].str[:12])
    per = o.set_index("origin")
    W["resident"] = W["origin"] == TOMP
    inc = W[~W["resident"]].copy()
    inc["evs"] = inc["jobs"] * inc["origin"].map(per["v"] * per["ev_share"] * per["in_screen"]).fillna(0)
    inc["mwh"] = inc["jobs"] * inc["origin"].map(per["kwh_per_job_screened"] / 1000).fillna(0)
    inc["jobs_scr"] = inc["jobs"] * inc["origin"].map(per["in_screen"]).fillna(False)
    g = pd.DataFrame({"jobs_total": W.groupby("bg")["jobs"].sum(),
                      "jobs_residents": W[W["resident"]].groupby("bg")["jobs"].sum(),
                      "jobs_incommuters": inc.groupby("bg")["jobs"].sum(),
                      "jobs_incommuters_screened": inc.groupby("bg")["jobs_scr"].sum(),
                      "incommuter_evs_central": inc.groupby("bg")["evs"].sum(),
                      "incommuter_mwh_central": inc.groupby("bg")["mwh"].sum()}).fillna(0)
    g["incommuter_share_of_jobs"] = g["jobs_incommuters"] / g["jobs_total"]
    g["share_of_incommuter_mwh"] = g["incommuter_mwh_central"] / g["incommuter_mwh_central"].sum()
    g = g.sort_values("incommuter_mwh_central", ascending=False)
    g["cumulative_share"] = g["share_of_incommuter_mwh"].cumsum()
    g["rank"] = np.arange(1, len(g) + 1)
    return g.reset_index().rename(columns={"index": "bg"})


# ---------------------------------------------------------------- figure
def figure(est: pd.DataFrame, o: pd.DataFrame, bgt: pd.DataFrame) -> None:
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#555555",
                         "axes.labelcolor": "#222222", "xtick.color": "#444444", "ytick.color": "#444444"})
    fig = plt.figure(figsize=(15.5, 4.8), facecolor="white")
    gs = fig.add_gridspec(1, 3, width_ratios=[0.9, 1.0, 1.0], wspace=0.95)
    # (a) screened in-commuting jobs by origin
    ax = fig.add_subplot(gs[0])
    q = o[o["in_screen"]].copy()
    q["label"] = np.where(q["state"] == "NY", q["name"].str.replace(" County", "", regex=False), q["name"].str.replace(" County", "", regex=False) + ", " + q["state"])
    top = q.sort_values("jobs", ascending=False).head(10).iloc[::-1]
    ax.barh(top["label"], top["jobs"], color=WORK_GREEN, height=0.65)
    for yv, (_, r) in enumerate(top.iterrows()):
        ax.text(r["jobs"] + 40, yv, f"EV {r['ev_share'] * 100:.1f}%", va="center", fontsize=7.5, color="#444444")
    ax.set_xlabel("Primary jobs in Tompkins held by origin residents (LODES 2023)")
    ax.set_xlim(0, top["jobs"].max() * 1.32)
    ax.grid(axis="x", color="#e6e6e6", lw=0.6); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    ax.set_title("(a) In-commuting origins ≤ 100 km\n(label: 2026 passenger EV share of origin)", loc="left", fontsize=9.5)
    # (b) energy comparison 2026 (horizontal bars; offsets drawn as negative)
    ax = fig.add_subplot(gs[1])
    e = est[est["year"] == 2026].set_index("case")
    items = [("Resident EVs: workplace (model)", e.loc["central", "resident_workplace_mwh_model"], None, None, "#B7B7B7"),
             ("In-commuter EVs: workplace", e.loc["central", "workplace_mwh"], e.loc["low", "workplace_mwh"], e.loc["high", "workplace_mwh"], WORK_GREEN),
             ("In-commuter EVs: public top-up", e.loc["central", "public_topup_mwh"], e.loc["low", "public_topup_mwh"], e.loc["high", "public_topup_mwh"], "#A5D2AF"),
             ("Out-commuting residents: workplace", -e.loc["central", "outcommuter_workplace_offset_mwh"], -e.loc["low", "outcommuter_workplace_offset_mwh"],
              -e.loc["high", "outcommuter_workplace_offset_mwh"], "#7F7F7F"),
             ("Out-commuting residents: public", -e.loc["central", "outcommuter_public_offset_mwh"], -e.loc["low", "outcommuter_public_offset_mwh"],
              -e.loc["high", "outcommuter_public_offset_mwh"], "#BDBDBD")]
    ys = np.arange(len(items))[::-1]
    for yv, (lab, c, lo, hi, col) in zip(ys, items):
        ax.barh(yv, c, color=col, height=0.62)
        if lo is not None:
            a, b = min(lo, hi), max(lo, hi)
            ax.plot([a, b], [yv, yv], color="#222222", lw=1.0)
            for xv in (a, b):
                ax.plot([xv, xv], [yv - 0.1, yv + 0.1], color="#222222", lw=1.0)
            edge = b if c >= 0 else a
        else:
            edge = c
        ax.text(edge + (12 if c >= 0 else -12), yv, f"{c:+,.0f}" if lo is not None else f"{c:,.0f}", va="center",
                ha="left" if c >= 0 else "right", fontsize=8, color="#222222")
    ax.set_yticks(ys); ax.set_yticklabels([i[0] for i in items], fontsize=8)
    ax.axvline(0, color="#555555", lw=0.8)
    lo_x = min(min(i[2] or 0, i[3] or 0, i[1]) for i in items)
    ax.set_xlim(lo_x * 1.6, e.loc["central", "resident_workplace_mwh_model"] * 1.18)
    ax.set_xlabel("MWh/yr, 2026 (bar = central, whisker = low–high)")
    ax.grid(axis="x", color="#e6e6e6", lw=0.6); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_title(f"(b) Correction to Tompkins load: net {e.loc['central', 'net_mwh']:+,.0f} MWh/yr\n"
                 f"(range {e.loc['low', 'net_mwh']:+,.0f} to {e.loc['high', 'net_mwh']:+,.0f}; county total {e.loc['central', 'total_mwh_model']:,.0f})",
                 loc="left", fontsize=9.5)
    # (c) BG map
    ax = fig.add_subplot(gs[2])
    bg = gpd.read_file(PROCESSED / "geography" / "tompkins_bg.gpkg").to_crs(32618)
    g = bg.merge(bgt, left_on="GEOID", right_on="bg", how="left").fillna({"incommuter_mwh_central": 0})
    g.plot(column="incommuter_mwh_central", ax=ax, cmap="Greens", edgecolor="white", linewidth=0.3, legend=True,
           vmin=0, legend_kwds={"label": "MWh/yr (2026, central)", "shrink": 0.7})
    top3 = bgt.head(3)["share_of_incommuter_mwh"].sum()
    ax.set_axis_off()
    ax.set_title(f"(c) In-commuter charging by workplace block group\ntop 3 BGs: {top3 * 100:.0f}% of total (EPSG:32618)", loc="left", fontsize=9.5)
    fig.text(0.01, -0.02, "Sources: LEHD LODES8 2023 (A), NYS DMV 2026 (A/B), ACS 2020–24 B08301 (A), charging library (E). "
             "Estimates are model outputs (E) resting on the stated assumptions.", fontsize=7.5, color="#555555")
    fig.savefig(FIGURES / "incommuter_charging.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    ensure(TABLES, FIGURES)
    W, H = {}, {}
    for jt in ["JT00", "JT01"]:
        W[jt], H[jt] = od_tompkins(jt)
    gaz, acs = gazetteer(), acs_vehicles_per_job()
    dmv = dmv_shares(gaz)
    est, origins, res_share = estimate(W, H, gaz, acs, dmv)
    est.round(4).to_csv(TABLES / "incommuter_charging_estimate.csv", index=False)

    # origin table: central 2026 plus job counts for both job types and residents for comparison
    o = origins[("central", 2026)]
    j00 = W["JT00"].assign(origin=W["JT00"]["h"].str[:5]).groupby("origin")["jobs"].sum()
    flows = o.assign(jobs_JT01=o["jobs"], jobs_JT00=o["origin"].map(j00).fillna(0))
    tot01 = W["JT01"]["jobs"].sum()
    flows["share_of_tompkins_jobs_JT01"] = flows["jobs_JT01"] / tot01
    for r in [80, 100, 160]:
        flows[f"within_{r}km"] = flows["distance_km"] <= r
    res = pd.DataFrame([{"origin": TOMP, "name": "Tompkins County (residents)", "state": "NY", "distance_km": 0.0,
                         "jobs_JT01": float(W["JT01"].loc[W["JT01"]["h"].str[:5] == TOMP, "jobs"].sum()),
                         "jobs_JT00": float(W["JT00"].loc[W["JT00"]["h"].str[:5] == TOMP, "jobs"].sum())}])
    res["share_of_tompkins_jobs_JT01"] = res["jobs_JT01"] / tot01
    cols = ["origin", "name", "state", "distance_km", "within_80km", "within_100km", "within_160km", "jobs_JT01", "jobs_JT00",
            "share_of_tompkins_jobs_JT01", "acs_car_share", "acs_wfh_share", "v", "ev_share_ldv_2026", "ev_share_pas_2026", "ev_share",
            "bev_share", "vehicles", "evs", "workplace_users", "work_mwh", "public_mwh", "gross_mwh"]
    flows = pd.concat([res, flows.sort_values("jobs_JT01", ascending=False)], ignore_index=True)[cols]
    flows = flows.rename(columns={"v": "vehicles_per_job_central", "ev_share": "ev_share_used_central_2026", "vehicles": "vehicles_central",
                                  "evs": "evs_central", "workplace_users": "workplace_users_central", "work_mwh": "workplace_mwh_central",
                                  "public_mwh": "public_topup_mwh_central", "gross_mwh": "gross_mwh_central"})
    flows.round(5).to_csv(TABLES / "incommuter_flows_by_origin.csv", index=False)

    bgt = bg_table(W["JT01"], H["JT01"], o)
    bgt.round(4).to_csv(TABLES / "incommuter_workplace_by_bg.csv", index=False)
    figure(est, o, bgt)

    pd.set_option("display.width", 200)
    print(est[["year", "case", "jobs_incommuters_screened", "incommuter_vehicles", "incommuter_evs", "incommuter_workplace_users", "workplace_mwh",
               "public_topup_mwh", "gross_mwh", "outcommuter_workplace_offset_mwh", "outcommuter_public_offset_mwh", "net_mwh",
               "resident_workplace_mwh_model", "total_mwh_model", "gross_over_total", "net_over_total"]].round(3).to_string())
    print({r: {k: round(v, 3) for k, v in s.items()} for r, s in res_share.items()})
    print(flows.head(15)[["name", "state", "distance_km", "jobs_JT01", "jobs_JT00", "ev_share_used_central_2026", "evs_central", "gross_mwh_central"]].round(3).to_string())
    print(bgt.head(10).round(3).to_string())


if __name__ == "__main__":
    main()
