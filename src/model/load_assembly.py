r"""Assemble hourly EV charging load for dwelling units, parcels, block groups and charging sites (2026-2050).

Expected load (profile-basis formulation, exact for expectations):
  L_d(t) = E^{BEV}_d(y) · Π_{k(d),BEV}(t) + E^{PHEV}_d(y) · Π_{k(d),PHEV}(t)
  Π_{k,v}(t) = Σ_a P(a | k, v, y, c) · h̄_a(t)          mean home-charging profile of archetype a (library, anchor year)
  dwelling class k = structure group × tenure × workers (0/1/2/3+); archetype a = (access, level, frequency, workplace, managed)
  P(access | k) = home_access(class, y, c);  P(L2 | access, v) = home_l2_share_v (MF5+: 0.8);  P(freq | v) from Drive Clean;
  P(workplace user | k) = 1 − (1 − access_per_worker · use)^{workers};  P(managed | L2) = managed_share_home_l2
Non-home energy of resident EVs (same mixture, library site profiles) forms county pools that are allocated to sites:
  public L2 -> AFDC open public L2 ports (proportional to ports); DCFC (+ en-route + passers-by share) -> AFDC DCFC ports;
  workplace -> 50 % AFDC private/workplace-flagged stations and Charge Ready workplace sites (by ports), 50 % large
  non-residential parcels (RPS 4xx/6xx/7xx, GFA-weighted) representing unlisted workplace chargers (low confidence);
  fleet EVs -> fleet depot parcels (ownership allocation) with overnight L2 charging (plug-in uniform 16:00-20:00, 7.2 kW),
  fleet_miles_per_year × 0.40 kWh/mi / 0.90.
Future years: DU expectations from the ownership evolution (trend saved per DU; other ownership scenarios scaled by the
ratio of county personal EVs); ports scale with EVs/port parameter (new ports proportional to existing distribution).
Realizations (building peaks): EV counts per DU ~ Poisson(E_d) capped at vehicles; each EV draws drivetrain, archetype
and one library EV-year; parcel hourly = sum; R realizations.
Calendar: target year days aligned by weekday; TMYx weather; local standard clock hours (hour-beginning index 0..8759).
Outputs
  data/processed/load/county_hourly_{year}_{own}_{chg}.parquet   location columns (home, work, public_l2, dcfc, fleet, passerby) kWh/h
  data/processed/load/bg_home_hourly_{year}_trend_base.parquet   65 BG columns × 8760 (expected home charging kWh/h)
  data/processed/load/parcel_summary_{year}.csv                 parcel expected annual kWh, expected peak-hour kW, realization p50/p90 peak
  data/processed/load/site_summary_{year}.csv                   site annual kWh and peak (public, DCFC, workplace, fleet)
  data/processed/load/class_profiles_{year}_{chg}.npz (interim)  Π_{k,v}(t) basis for exact DU reconstruction
  results/tables/load_scenarios_annual.csv                       county annual MWh, peak MW by location, year, scenario
"""
from __future__ import annotations

import argparse
import itertools
import json

import geopandas as gpd
import numpy as np
import pandas as pd

from src.model.charging_params import value
from src.utils.paths import INTERIM, PROCESSED, RAW, TABLES, ensure

ANCHORS = [2026, 2030, 2035, 2040, 2050]
OUT = PROCESSED / "load"
G5 = {"SFD": "SF", "SFA": "SF", "MF2_4": "MF2_4", "MF5_19": "MF5P", "MF20P": "MF5P", "MOBILE": "MOBILE"}
ACCESS_PARAM = {("SF", "own"): "home_access_sf_own", ("SF", "rent"): "home_access_sf_rent", ("MF2_4", "own"): "home_access_mf2_4",
                ("MF2_4", "rent"): "home_access_mf2_4", ("MF5P", "own"): "home_access_mf5p", ("MF5P", "rent"): "home_access_mf5p",
                ("MOBILE", "own"): "home_access_mobile", ("MOBILE", "rent"): "home_access_mobile"}
FREQS = ["daily", "few_week", "weekly", "rare"]
LOCS = ["home", "work", "public_l2", "dcfc"]


class Library:
    def __init__(self, year: int):
        d = INTERIM / "charging_library" / str(year)
        self.year = year
        self.meta = pd.read_parquet(d / "meta.parquet")
        self.home = np.load(d / "home_kw.npy", mmap_mode="r")
        z = np.load(d / "site_kwh.npz")
        self.site = {"work": z["work"], "public_l2": z["public_l2"], "dcfc": z["dcfc"]}
        key = ["drivetrain", "access", "level", "freq", "work", "managed"]
        self.groups = {k: g["ev"].values for k, g in self.meta.groupby(key)}
        self.mean = {}
        for k, idx in self.groups.items():
            self.mean[k] = {"home": np.asarray(self.home[idx]).mean(axis=0), **{loc: self.site[loc][idx].mean(axis=0) for loc in ["work", "public_l2", "dcfc"]}}


def nearest_anchor(y: int) -> int:
    return min(ANCHORS, key=lambda a: abs(a - y))


def archetype_probs(struct_g: str, tenure: str, workers: int, dt: str, y: int, chg: str) -> dict:
    pa = value(ACCESS_PARAM[(struct_g, tenure)], chg, y)
    pl2 = 0.8 if struct_g == "MF5P" else value("home_l2_share_bev" if dt == "BEV" else "home_l2_share_phev", chg, y)
    fq = np.array([value(f"freq_{f}_{dt.lower()}", chg, y) for f in FREQS])
    fq = fq / fq.sum()
    pw = 1 - (1 - value("workplace_access_per_worker", chg, y) * value("workplace_use_given_access", chg, y)) ** max(workers, 0)
    pm = value("managed_share_home_l2", chg, y)
    out = {}
    for work in [0, 1]:
        wprob = pw if work else 1 - pw
        out[(dt, 0, "none", "none", work, 0)] = (1 - pa) * wprob
        for f, pf in zip(FREQS, fq):
            out[(dt, 1, "L1", f, work, 0)] = out.get((dt, 1, "L1", f, work, 0), 0) + pa * (1 - pl2) * pf * wprob
            out[(dt, 1, "L2", f, work, 0)] = pa * pl2 * pf * wprob * (1 - pm)
            out[(dt, 1, "L2", f, work, 1)] = pa * pl2 * pf * wprob * pm
    return out


def class_profiles(lib: Library, y: int, chg: str) -> dict:
    """Π_{k,v}: expected per-EV hourly kWh by location for each dwelling class k and drivetrain v."""
    prof = {}
    for g, t, w, dt in itertools.product(["SF", "MF2_4", "MF5P", "MOBILE"], ["own", "rent"], [0, 1, 2, 3], ["BEV", "PHEV"]):
        acc = {loc: np.zeros(8760) for loc in LOCS}
        for arch, p in archetype_probs(g, t, w, dt, y, chg).items():
            if p <= 0 or arch not in lib.mean:
                continue
            for loc in LOCS:
                acc[loc] += p * lib.mean[arch][loc]
        prof[(g, t, w, dt)] = acc
    return prof


def load_dus() -> pd.DataFrame:
    du = pd.read_parquet(PROCESSED / "model" / "du_ev_2026.parquet")
    syn = pd.read_parquet(PROCESSED / "synthetic" / "dwelling_units.parquet")[["du_id", "wif", "x_utm", "y_utm"]]
    du = du.merge(syn, on="du_id")
    du["g"] = du["structure"].map(G5)
    du["workers"] = pd.to_numeric(du["wif"], errors="coerce").fillna(1).clip(0, 3).astype(int)
    ev_y = pd.read_parquet(PROCESSED / "model" / "du_ev_by_year_trend.parquet")
    return du.merge(ev_y, on="du_id")


def du_expectations(du: pd.DataFrame, y: int, own: str) -> tuple[np.ndarray, np.ndarray]:
    gp = pd.read_csv(PROCESSED / "growth" / "growth_parameters_by_year.csv")
    ycol = [c for c in du.columns if c.startswith("E_ev_20")]
    years = sorted(int(c[-4:]) for c in ycol)
    # interpolate DU expectations between saved years (trend)
    lo = max([a for a in years if a <= y], default=years[0]); hi = min([a for a in years if a >= y], default=years[-1])
    wgt = 0 if hi == lo else (y - lo) / (hi - lo)
    E = (1 - wgt) * du[f"E_ev_{lo}"].values + wgt * du[f"E_ev_{hi}"].values
    if own != "trend":
        s_own = gp[(gp["scenario"] == own) & (gp["year"] == y)]["EV_p50"].iloc[0]
        s_tr = gp[(gp["scenario"] == "trend") & (gp["year"] == y)]["EV_p50"].iloc[0]
        E = E * s_own / s_tr
    if y == 2026:
        E = du["E_ev"].values
        bev_share = np.where(du["E_ev"].values > 0, du["E_bev"].values / np.maximum(du["E_ev"].values, 1e-12), 0.57)
    else:
        r = gp[(gp["scenario"] == own) & (gp["year"] == y)].iloc[0]
        bev_share = np.full(len(du), r["BEV_p50"] / (r["BEV_p50"] + r["PHEV_p50"]))
    return E * bev_share, E * (1 - bev_share)


def stations() -> tuple[pd.DataFrame, pd.DataFrame]:
    st = pd.read_csv(PROCESSED / "infrastructure" / "tompkins_afdc_stations.csv")
    st = st[st["status_code"] == "E"]
    pub = st[st["access_code"] == "public"]
    wk = st[(st["access_code"] == "private") | st["ev_workplace_charging"].fillna(False).astype(bool)]
    cr = pd.read_csv(PROCESSED / "infrastructure" / "charge_ready_ny_tompkins.csv")
    cr = cr[cr["location_type"] == "Workplace"]
    work_sites = pd.concat([pd.DataFrame({"site_id": "afdc_" + wk["id"].astype(str), "name": wk["station_name"], "lat": wk["latitude"], "lon": wk["longitude"],
                                          "ports": wk["ev_level2_evse_num"].fillna(0) + wk["ev_level1_evse_num"].fillna(0)}),
                            pd.DataFrame({"site_id": "chargeready_" + cr["anonymized_project_id"].astype(str), "name": cr["site_name"], "lat": np.nan, "lon": np.nan,
                                          "ports": pd.to_numeric(cr["of_l2_ports"], errors="coerce").fillna(0)})])
    return pub, work_sites


def nonres_parcels() -> pd.DataFrame:
    p = gpd.read_file(RAW / "parcels" / "tompkins_parcels_2025.gpkg")
    pc = p["PROP_CLASS"].astype(str).str[:3]
    q = p[pc.str[0].isin(["4", "6", "7"]) & ~pc.isin(["411", "416", "418"])].copy()
    q["gfa"] = pd.to_numeric(q["GFA"], errors="coerce").fillna(0)
    q = q[q["gfa"] >= 20000]
    pts = q.to_crs(4326).geometry.representative_point()
    return pd.DataFrame({"parcel": q["SWIS_SBL_ID"].values, "prop_class": pc[q.index].values, "gfa": q["gfa"].values, "lat": pts.y.values, "lon": pts.x.values})


def fleet_profile(year: int, chg: str) -> np.ndarray:
    """Per-fleet-EV hourly kWh: weekday overnight depot charging."""
    kwh_year = value("fleet_miles_per_year", chg, year) * 0.40 / 0.90
    days = pd.date_range(f"{year}-01-01", periods=365, freq="D")
    wd = days.dayofweek < 5
    per_day = kwh_year / wd.sum()
    prof = np.zeros(8760)
    offsets = np.linspace(16.0, 20.0, 9)  # fleet return times spread uniformly 16:00-20:00 (expected profile)
    for i, is_wd in enumerate(wd):
        if not is_wd:
            continue
        for off in offsets:
            start = i * 24 + off
            dur = per_day / 7.2
            for k in range(int(start), int(np.ceil(start + dur))):
                ov = min(start + dur, k + 1) - max(start, k)
                prof[k % 8760] += 7.2 * ov / len(offsets)
    return prof


def assemble(year: int, own: str, chg: str, realizations: int = 0, seed: int = 5) -> dict:
    ensure(OUT, INTERIM / "load")
    lib = Library(nearest_anchor(year))
    prof = class_profiles(lib, year, chg)
    du = load_dus()
    Eb, Ep = du_expectations(du, year, own)
    # expected county pools and BG home profiles
    keys = list(zip(du["g"], du["tenure"], du["workers"]))
    cls = pd.Series(keys).astype(str)
    pools = {loc: np.zeros(8760) for loc in LOCS}
    bg_home = {}
    kdf = pd.DataFrame({"k": cls, "bg": du["bg"].values, "parcel": du["parcel"].values, "Eb": Eb, "Ep": Ep})
    by_k = kdf.groupby("k")[["Eb", "Ep"]].sum()
    key_of = dict(zip(cls, keys))
    for k, row in by_k.iterrows():
        g, t, w = key_of[k]
        for loc in LOCS:
            pools[loc] += row["Eb"] * prof[(g, t, w, "BEV")][loc] + row["Ep"] * prof[(g, t, w, "PHEV")][loc]
    by_bgk = kdf.groupby(["bg", "k"])[["Eb", "Ep"]].sum().reset_index()
    for bg, gg in by_bgk.groupby("bg"):
        acc = np.zeros(8760)
        for _, r in gg.iterrows():
            g, t, w = key_of[r["k"]]
            acc += r["Eb"] * prof[(g, t, w, "BEV")]["home"] + r["Ep"] * prof[(g, t, w, "PHEV")]["home"]
        bg_home[bg] = acc
    # fleet and passers-by
    gp = pd.read_csv(PROCESSED / "growth" / "growth_parameters_by_year.csv")
    ev_y = gp[(gp["scenario"] == own) & (gp["year"] == year)]["EV_p50"].iloc[0]
    ev_26 = gp[(gp["scenario"] == own) & (gp["year"] == 2026)]["EV_p50"].iloc[0]
    fleet_sites = pd.read_csv(PROCESSED / "model" / "fleet_ev_sites_2026.csv")
    n_fleet = fleet_sites["E_fleet_ev"].sum() * ev_y / ev_26
    fp = fleet_profile(year, chg)
    pools["fleet"] = n_fleet * fp
    pb_share = value("passerby_dcfc_share", chg, year)
    pools["passerby"] = pools["dcfc"] * pb_share / (1 - pb_share)
    county = pd.DataFrame(pools)
    county.index.name = "hour"
    county.astype("float32").to_parquet(OUT / f"county_hourly_{year}_{own}_{chg}.parquet")

    # sites
    pub, work_sites = stations()
    scale_ports = max(ev_y / ev_26 * value("evs_per_public_port", chg, 2026) / value("evs_per_public_port", chg, year), 1.0)
    l2p = pub["ev_level2_evse_num"].fillna(0)
    dcp = pub["ev_dc_fast_num"].fillna(0)
    site_rows = []
    for (sid, name, ports, pool) in [("public_l2", pub, l2p, pools["public_l2"]), ("dcfc", pub, dcp, pools["dcfc"] + pools["passerby"])]:
        share = ports / ports.sum()
        for (_, r), sh in zip(name.iterrows(), share):
            if sh <= 0:
                continue
            ser = pool * sh
            site_rows.append({"site_type": sid, "site_id": f"afdc_{r['id']}", "name": r["station_name"], "lat": r["latitude"], "lon": r["longitude"],
                              "ports_2026": int(ports.loc[_]), "ports_scaled": float(ports.loc[_] * scale_ports), "annual_kwh": float(ser.sum()),
                              "peak_kw": float(ser.max()), "kwh_per_port_day": float(ser.sum() / (ports.loc[_] * scale_ports) / 365)})
    nr = nonres_parcels()
    wshare_sites = work_sites["ports"] / work_sites["ports"].sum()
    for (_, r), sh in zip(work_sites.iterrows(), wshare_sites):
        ser = 0.5 * pools["work"] * sh
        site_rows.append({"site_type": "workplace_listed", "site_id": r["site_id"], "name": r["name"], "lat": r["lat"], "lon": r["lon"],
                          "ports_2026": float(r["ports"]), "annual_kwh": float(ser.sum()), "peak_kw": float(ser.max())})
    for _, r in nr.iterrows():
        ser = 0.5 * pools["work"] * r["gfa"] / nr["gfa"].sum()
        site_rows.append({"site_type": "workplace_unlisted_parcel", "site_id": f"parcel_{r['parcel']}", "name": r["prop_class"], "lat": r["lat"], "lon": r["lon"],
                          "annual_kwh": float(ser.sum()), "peak_kw": float(ser.max())})
    for _, r in fleet_sites.iterrows():
        ser = fp * r["E_fleet_ev"] * ev_y / ev_26
        site_rows.append({"site_type": "fleet_depot", "site_id": f"parcel_{r['SWIS_SBL_ID']}", "name": r["PROP_CLASS"], "annual_kwh": float(ser.sum()), "peak_kw": float(ser.max())})
    sites = pd.DataFrame(site_rows)
    sites.round(3).to_csv(OUT / f"site_summary_{year}_{own}_{chg}.csv", index=False)

    res = {"county": county, "bg_home": bg_home, "sites": sites}
    if own == "trend" and chg == "base":
        pd.DataFrame(bg_home).astype("float32").to_parquet(OUT / f"bg_home_hourly_{year}_trend_base.parquet")
        np.savez_compressed(INTERIM / "load" / f"class_profiles_{year}_{chg}.npz", **{"|".join(map(str, k)) + "|" + loc: v[loc].astype("float32")
                                                                                       for k, v in prof.items() for loc in LOCS})

    # parcel expected annual & expected peak (expectation of load, not expected peak)
    kdf["annual"] = 0.0
    parcel_rows = []
    if realizations:
        rng = np.random.default_rng(seed + year)
        meta = lib.meta
        cap = du["veh"].values
        E = Eb + Ep
        peak_samples = {}
        prob_cache = {}
        for (g, t, w) in set(keys):
            for dt in ["BEV", "PHEV"]:
                pr = archetype_probs(g, t, w, dt, year, chg)
                ak = [a for a in pr if a in lib.groups and pr[a] > 0]
                pv = np.array([pr[a] for a in ak]); prob_cache[(g, t, w, dt)] = (ak, np.cumsum(pv / pv.sum()))
        for r in range(realizations):
            n_ev = np.minimum(rng.poisson(E), cap)
            idx = np.where(n_ev > 0)[0]
            parcel_load = {}
            for i in idx:
                g, t, w = keys[i]
                for _ in range(int(n_ev[i])):
                    dt = "BEV" if rng.random() < Eb[i] / max(E[i], 1e-12) else "PHEV"
                    ak, cum = prob_cache[(g, t, w, dt)]
                    a = ak[min(int(np.searchsorted(cum, rng.random())), len(ak) - 1)]
                    evs = lib.groups[a]
                    prof_ev = np.asarray(lib.home[evs[rng.integers(len(evs))]])
                    pid = du["parcel"].values[i]
                    parcel_load[pid] = parcel_load.get(pid, 0) + prof_ev
            for pid, ld in parcel_load.items():
                peak_samples.setdefault(pid, []).append(float(ld.max()))
            print(f"  realization {r + 1}/{realizations}: parcels with EVs {len(parcel_load)}")
        pe = kdf.groupby("parcel")[["Eb", "Ep"]].sum()
        for pid, row in pe.iterrows():
            s = peak_samples.get(pid, [])
            s = s + [0.0] * (realizations - len(s))
            parcel_rows.append({"parcel": pid, "E_ev": row["Eb"] + row["Ep"], "peak_kw_p50": float(np.percentile(s, 50)), "peak_kw_p90": float(np.percentile(s, 90)),
                                "prob_any_ev_charging": float(np.mean(np.array(s) > 0))})
        pd.DataFrame(parcel_rows).round(3).to_csv(OUT / f"parcel_summary_{year}_{own}_{chg}.csv", index=False)
    return res


def main(years, owns, chgs, realizations):
    ensure(TABLES)
    rows = []
    for y in years:
        for own in owns:
            for chg in chgs:
                r = assemble(y, own, chg, realizations if (own == "trend" and chg == "base" and y in (2026, 2035)) else 0)
                c = r["county"]
                tot = c.sum(axis=1)
                rows.append({"year": y, "ownership_scenario": own, "charging_scenario": chg, "annual_mwh_total": tot.sum() / 1000,
                             **{f"annual_mwh_{loc}": c[loc].sum() / 1000 for loc in c.columns},
                             "peak_mw_total": tot.max() / 1000, "peak_hour_of_year": int(tot.idxmax()),
                             "home_peak_mw": c["home"].max() / 1000, "load_factor": tot.mean() / tot.max()})
                print(rows[-1])
    out = pd.DataFrame(rows)
    path = TABLES / "load_scenarios_annual.csv"
    if path.exists():
        old = pd.read_csv(path)
        out = pd.concat([old, out]).drop_duplicates(["year", "ownership_scenario", "charging_scenario"], keep="last")
    out.sort_values(["ownership_scenario", "charging_scenario", "year"]).round(4).to_csv(path, index=False)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="*", type=int, default=[2026, 2030, 2035, 2040, 2050])
    ap.add_argument("--own", nargs="*", default=["trend", "slow", "stall", "policy"])
    ap.add_argument("--chg", nargs="*", default=["base", "access+", "managed"])
    ap.add_argument("--realizations", type=int, default=30)
    a = ap.parse_args()
    main(a.years, a.own, a.chg, a.realizations)
