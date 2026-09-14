r"""Event-based EV charging simulation: a library of synthetic EV-years per archetype and anchor year.

Each simulated EV-year (calendar of the target year, TMYx Ithaca temperatures) tracks a minimal energy ledger:
  D_t  = battery energy deficit (kWh at the wheel) relative to full, 0 <= D_t <= C (usable capacity)
  daily driving energy  E_t = d_t · e_wheel(y) · m(T_t),   m(T) = 1 + 0.011·max(0, 20−T) + 0.006·max(0, T−25)
  daily miles d_t: P(no driving) = 0.15 weekday / 0.25 weekend; otherwise Gamma(k=1.3) scaled so that the annual
    total equals the vehicle's annual miles A ~ LogNormal(mean = annual_miles(drivetrain), σ).
  BEV: C = 70 kWh; if D would exceed 0.95 C, an en-route DCFC session restores to 0.3 C (away from home).
  Annual miles are multiplied by a frequency-type factor (daily 1.15, few/week 1.0, weekly 0.8, rare 0.6; assumption).
  PHEV: C = range · e_wheel; electric miles limited by battery (D capped at C; remaining miles on gasoline).
Charging opportunities (in order within a day):
  workplace (weekday, worker with access & use, attends 80 % of weekdays, plugs in on 40 % of attended days when
    D > 8 kWh): arrival hour ~ NHTS 2022 work arrival distribution, dwell ~ NHTS work dwell (median 8.2 h), L2 6.6 kW.
  public top-up (home-access EVs): daily probability = share · expected annual plug energy / mean session kWh / 365;
    location L2 (Boulder start-hour/energy distributions) or DCFC (Dundee).
  home (if home access): plug-in with probability by frequency type (daily .92, few/week .45, weekly .16, rare .05),
    forced if D > 0.60 C (BEV only; PHEVs fall back to gasoline); plug-in hour and connection duration sampled jointly from Norway
    residential sessions with the same day type (weekday/weekend); energy at the plug = min(D/η, P·conn_h);
    managed EVs (L2) start at max(plug-in, 23:00) when the connection window allows full delivery, else immediately.
  no home access: public L2 / DCFC sessions when D > 0.5 C (BEV) or D > 0.6 C (PHEV, 60 % of days), public_l2 share parameter.
  PHEVs use public L2 only (most PHEVs cannot DC fast charge).
Hourly energy: each session delivers constant power P from its charging start; hours are local clock hours of the
target calendar year (no DST shift modelled).
Archetypes: drivetrain × home access × home level (L1/L2) × frequency type × workplace user × managed (L2 only).
Outputs (per anchor year Y):
  data/interim/charging_library/Y/home_kw.npy        float32 [n_ev, 8760] home charging kWh per hour
  data/interim/charging_library/Y/site_kwh.npz        float32 [n_ev, 8760] workplace, public L2, DCFC (resident vehicles)
  data/interim/charging_library/Y/meta.parquet        archetype fields, annual kWh by location, sessions by location
  data/interim/charging_library/Y/sessions_sample.parquet   up to 60k sessions for validation
  data/processed/charging/library_summary_Y.csv       archetype means (tracked)
"""
from __future__ import annotations

import argparse
import itertools

import numpy as np
import pandas as pd

from src.analysis.charging_sessions import clean, load_boulder, load_dundee, load_norway
from src.model.charging_params import value
from src.utils.paths import INTERIM, PROCESSED, RAW, ensure

N_PER_ARCH = 60
BEV_CAP = 70.0
ETA = {"L1": 0.83, "L2": 0.90, "DCFC": 0.92}
FREQ_P = {"daily": 0.92, "few_week": 0.45, "weekly": 0.16, "rare": 0.05}
WORK_KW = 6.6
WORK_USE_DAY = 0.40  # share of attended workdays a workplace-charging user plugs in (assumption; checked vs NYSERDA 22-03)
FORCE_BEV = 0.60
ENROUTE_BEV = 0.95
# frequency types correlate with mileage (low-mileage owners charge less often); multipliers keep the survey-weighted mean ~1
FREQ_MILES = {"daily": 1.15, "few_week": 1.0, "weekly": 0.80, "rare": 0.60, "none": 1.0}


def empirical():
    nor, _ = clean(load_norway(3.6))
    nor = nor[nor["conn_h"] <= 48]
    home = {dt: nor[nor["weekend"] == (dt == "we")][["start", "conn_h"]].assign(h=lambda x: x["start"].dt.hour + x["start"].dt.minute / 60)[["h", "conn_h"]].values
            for dt in ["wd", "we"]}
    b, _ = clean(load_boulder())
    b = b[b["port_type"] == "L2"]
    pub = b.assign(h=b["start"].dt.hour + b["start"].dt.minute / 60)[["h", "kwh", "conn_h"]].values
    dn, _ = clean(load_dundee())
    dn = dn[dn["port_type"] == "DCFC"]
    dcfc = dn.assign(h=dn["start"].dt.hour + dn["start"].dt.minute / 60)[["h", "kwh"]].values
    t = pd.read_csv(RAW / "nhts2022" / "tripv2pub.csv", usecols=["WHYTO", "ENDTIME", "DRVR_FLG", "TRPHHVEH", "WTTRDFIN", "DWELTIME"])
    w = t[(t["WHYTO"] == 3) & (t["DRVR_FLG"] == 1) & (t["TRPHHVEH"] == 1) & (t["ENDTIME"] >= 0) & (t["DWELTIME"] > 60)]
    work = np.column_stack([(w["ENDTIME"] // 100 + (w["ENDTIME"] % 100) / 60).values, (w["DWELTIME"] / 60).clip(upper=12).values,
                            np.cumsum(w["WTTRDFIN"].values) / w["WTTRDFIN"].values.sum()])
    return home, pub, dcfc, work


def weather(year: int) -> tuple[np.ndarray, np.ndarray]:
    w = pd.read_csv(PROCESSED / "weather" / "ithaca_tmyx_2011-2025_hourly.csv")
    tday = w.groupby(["month", "day"])["t_drybulb_c"].mean().values  # 365 days (TMY has no Feb 29)
    days = pd.date_range(f"{year}-01-01", periods=365, freq="D")
    return tday, (days.dayofweek >= 5)


def add_session(prof: np.ndarray, start_h: float, kwh: float, kw: float) -> None:
    if kwh <= 0:
        return
    dur = kwh / kw
    s, e = start_h, start_h + dur
    k0, k1 = int(np.floor(s)), int(np.ceil(e))
    for k in range(k0, k1):
        ov = min(e, k + 1) - max(s, k)
        if ov > 0 and 0 <= k < 8760:
            prof[k] += kw * ov
        elif ov > 0 and k >= 8760:
            prof[k - 8760] += kw * ov  # year-end wrap


def simulate_ev(arch: dict, year: int, rng, emp, tday, weekend, sessions: list, ev_id: int):
    home_emp, pub_emp, dcfc_emp, work_emp = emp
    dt = arch["drivetrain"]
    e_wheel = value("e_wheel_bev_kwh_per_mi" if dt == "BEV" else "e_wheel_phev_kwh_per_mi", "base", year)
    miles_mean = value("annual_miles_bev" if dt == "BEV" else "annual_miles_phev", "base", year)
    sig = value("annual_miles_lognorm_sigma", "base", year)
    A = rng.lognormal(np.log(miles_mean) - sig ** 2 / 2, sig) * FREQ_MILES[arch["freq"]]
    cap = BEV_CAP if dt == "BEV" else value("phev_electric_range_mi", "base", year) * e_wheel
    home_kw = (value("l1_kw", "base", year) if arch["level"] == "L1" else value("l2_kw_bev" if dt == "BEV" else "l2_kw_phev", "base", year))
    drive = rng.random(365) > np.where(weekend, 0.25, 0.15)
    raw = rng.gamma(1.3, 1.0, 365) * drive
    miles = raw / raw.sum() * A
    pub_share = value("public_topup_share_with_home", arch["scenario"], year)
    dcfc_of_pub = value("dcfc_share_of_public", arch["scenario"], year)
    pub_l2_noaccess = value("public_l2_energy_share_no_home", arch["scenario"], year)
    home = np.zeros(8760, np.float32)
    work = np.zeros(8760, np.float32)
    publ2 = np.zeros(8760, np.float32)
    dcfc = np.zeros(8760, np.float32)
    D = cap * 0.2
    tot = {"home": 0.0, "work": 0.0, "public_l2": 0.0, "dcfc": 0.0, "enroute": 0.0}
    n = {"home": 0, "work": 0, "public_l2": 0, "dcfc": 0}
    gas_miles = 0.0
    need_wheel = 0.0
    exp_plug = A * e_wheel * 1.12 / 0.9  # expected annual energy at the plug (mean temperature multiplier ~1.12)
    mean_pub_session = dcfc_of_pub * 19.0 + (1 - dcfc_of_pub) * 9.7  # Dundee DCFC / Boulder L2 mean kWh
    p_pub_day = min(1.0, pub_share * exp_plug / mean_pub_session / 365.0)
    for day in range(365):
        h0 = day * 24
        mult = 1 + 0.011 * max(0.0, 20 - tday[day]) + 0.006 * max(0.0, tday[day] - 25)
        need = miles[day] * e_wheel * mult
        need_wheel += need
        # morning half of driving
        half = need / 2
        if dt == "PHEV":
            use = min(half, cap - D); gas_miles += (half - use) / (e_wheel * mult); D += use
        else:
            D += half
            if D > ENROUTE_BEV * cap:
                k = D - 0.3 * cap; D = 0.3 * cap; tot["enroute"] += k / ETA["DCFC"]
                add_session(dcfc, h0 + 12 + rng.random() * 6, k / ETA["DCFC"], 50.0); n["dcfc"] += 1
        # workplace
        if arch["work"] and not weekend[day] and drive[day] and rng.random() < 0.8 * WORK_USE_DAY and D > 8.0:
            wi = min(int(np.searchsorted(work_emp[:, 2], rng.random())), len(work_emp) - 1)
            arr, dwell = work_emp[wi, 0], work_emp[wi, 1]
            deliver = min(D / ETA["L2"], WORK_KW * dwell)
            if deliver > 0.5:
                add_session(work, h0 + arr, deliver, WORK_KW); D -= deliver * ETA["L2"]; tot["work"] += deliver; n["work"] += 1
                sessions.append((ev_id, "work", day, arr, deliver, dwell))
        # afternoon half
        half = need - need / 2
        if dt == "PHEV":
            use = min(half, cap - D); gas_miles += (half - use) / (e_wheel * mult); D += use
        else:
            D += half
            if D > ENROUTE_BEV * cap:
                k = D - 0.3 * cap; D = 0.3 * cap; tot["enroute"] += k / ETA["DCFC"]
                add_session(dcfc, h0 + 15 + rng.random() * 5, k / ETA["DCFC"], 50.0); n["dcfc"] += 1
        wk = "we" if weekend[day] else "wd"
        if arch["access"]:
            # public top-up
            if rng.random() < p_pub_day and D > 3:
                if dt == "BEV" and rng.random() < dcfc_of_pub:
                    r = dcfc_emp[rng.integers(len(dcfc_emp))]
                    k = min(D / ETA["DCFC"], r[1]); add_session(dcfc, h0 + r[0], k, 45.0); tot["dcfc"] += k; n["dcfc"] += 1
                    sessions.append((ev_id, "dcfc", day, r[0], k, k / 45.0))
                else:
                    r = pub_emp[rng.integers(len(pub_emp))]
                    k = min(D / ETA["L2"], r[1], 6.6 * r[2]); add_session(publ2, h0 + r[0], k, 6.6); tot["public_l2"] += k; n["public_l2"] += 1
                    sessions.append((ev_id, "public_l2", day, r[0], k, r[2]))
                D -= k * (ETA["DCFC"] if sessions[-1][1] == "dcfc" else ETA["L2"])
                D = max(D, 0.0)
            force = (dt == "BEV") and D > FORCE_BEV * cap
            if D > 0.3 and (force or rng.random() < FREQ_P[arch["freq"]]):
                hs = home_emp[wk][rng.integers(len(home_emp[wk]))]
                plug, conn = hs[0], hs[1]
                eta = ETA[arch["level"]]
                deliver = min(D / eta, home_kw * conn)
                start = plug
                if arch["managed"] and arch["level"] == "L2":
                    off = 23.0 if plug < 23.0 else plug
                    if plug + conn >= off + deliver / home_kw:
                        start = off
                add_session(home, h0 + start, deliver, home_kw)
                D -= deliver * eta; tot["home"] += deliver; n["home"] += 1
                sessions.append((ev_id, "home", day, plug, deliver, conn))
        else:
            thr = 0.5 if dt == "BEV" else 0.6
            if D > thr * cap and (dt == "BEV" or rng.random() < 0.6):
                if dt == "PHEV" or rng.random() < pub_l2_noaccess:
                    r = pub_emp[rng.integers(len(pub_emp))]
                    k = min(D / ETA["L2"], max(r[1], 0.5 * D / ETA["L2"]), 6.6 * max(r[2], 1.0))
                    add_session(publ2, h0 + r[0], k, 6.6); tot["public_l2"] += k; n["public_l2"] += 1; D -= k * ETA["L2"]
                    sessions.append((ev_id, "public_l2", day, r[0], k, r[2]))
                else:
                    r = dcfc_emp[rng.integers(len(dcfc_emp))]
                    k = min(D / ETA["DCFC"], max(r[1], 0.6 * D / ETA["DCFC"])); add_session(dcfc, h0 + r[0], k, 45.0)
                    tot["dcfc"] += k; n["dcfc"] += 1; D -= k * ETA["DCFC"]
                    sessions.append((ev_id, "dcfc", day, r[0], k, k / 45.0))
        D = min(max(D, 0.0), cap)
    meta = {**arch, "annual_miles": A, "gas_miles": gas_miles, "need_wheel_kwh": need_wheel, "end_deficit": D, **{f"kwh_{k}": v for k, v in tot.items()}, **{f"n_{k}": v for k, v in n.items()}}
    return home, work, publ2, dcfc, meta


def archetypes(scenario: str = "base"):
    out = []
    for dt, access, level, freq, work, managed in itertools.product(["BEV", "PHEV"], [1, 0], ["L1", "L2"], ["daily", "few_week", "weekly", "rare"], [0, 1], [0, 1]):
        if not access and (level == "L2" or freq != "daily" or managed):
            continue  # no-home-access archetype has no level/frequency/managed dimension (kept once)
        if managed and level == "L1":
            continue
        out.append({"drivetrain": dt, "access": access, "level": level if access else "none", "freq": freq if access else "none",
                    "work": work, "managed": managed, "scenario": scenario})
    return out


def build(year: int, seed: int = 11, n_per_arch: int = N_PER_ARCH) -> None:
    rng = np.random.default_rng(seed + year)
    emp = empirical()
    tday, weekend = weather(year)
    archs = archetypes()
    out = INTERIM / "charging_library" / str(year)
    ensure(out, PROCESSED / "charging")
    n_total = len(archs) * n_per_arch
    H = np.zeros((n_total, 8760), np.float32)
    W = np.zeros((n_total, 8760), np.float32)
    PL = np.zeros((n_total, 8760), np.float32)
    DC = np.zeros((n_total, 8760), np.float32)
    metas, sessions = [], []
    i = 0
    for ai, a in enumerate(archs):
        for _ in range(n_per_arch):
            h, w, pl, dc, m = simulate_ev(a, year, rng, emp, tday, weekend, sessions, i)
            H[i], W[i], PL[i], DC[i] = h, w, pl, dc
            metas.append({"ev": i, "arch_id": ai, **m})
            i += 1
        print(f"  {year}: archetype {ai + 1}/{len(archs)}")
    np.save(out / "home_kw.npy", H)
    np.savez_compressed(out / "site_kwh.npz", work=W, public_l2=PL, dcfc=DC)
    meta = pd.DataFrame(metas)
    meta.to_parquet(out / "meta.parquet", index=False)
    s = pd.DataFrame(sessions, columns=["ev", "location", "day", "start_h", "kwh", "conn_h"])
    s.sample(min(60000, len(s)), random_state=1).to_parquet(out / "sessions_sample.parquet", index=False)
    summ = meta.groupby(["arch_id", "drivetrain", "access", "level", "freq", "work", "managed"]).agg(
        n=("ev", "size"), annual_miles=("annual_miles", "mean"), kwh_home=("kwh_home", "mean"), kwh_work=("kwh_work", "mean"),
        kwh_public_l2=("kwh_public_l2", "mean"), kwh_dcfc=("kwh_dcfc", "mean"), kwh_enroute=("kwh_enroute", "mean"),
        n_home=("n_home", "mean"), gas_miles=("gas_miles", "mean"), need_wheel=("need_wheel_kwh", "mean")).reset_index()
    summ.round(3).to_csv(PROCESSED / "charging" / f"library_summary_{year}.csv", index=False)
    print(summ[["drivetrain", "access", "level", "freq", "work", "managed", "kwh_home", "kwh_work", "kwh_public_l2", "kwh_dcfc", "kwh_enroute", "n_home"]].round(0).head(30).to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="*", type=int, default=[2026])
    ap.add_argument("--n", type=int, default=N_PER_ARCH)
    a = ap.parse_args()
    for y in a.years:
        build(y, n_per_arch=a.n)
