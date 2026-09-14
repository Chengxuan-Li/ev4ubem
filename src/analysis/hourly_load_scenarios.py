"""Tompkins 2026 hourly EV load: simple formulations compared, with TEMPO as a *model* benchmark (class E).

This is a feasibility demonstration of model families A (count x normalised profile) and a
mixture-of-location-profiles variant; it is not a calibrated final model.

Inputs
- EV stock: data/processed/dmv/tompkins_ev_stock_zip_2026.csv (DMV 2026-09, county=TOMPKINS, VIN-decoded; class A)
- Annual energy per EV (assumptions documented in docs/methodology.md):
    BEV  = miles x kWh/mi / charging efficiency = 10,670 x 0.32 / 0.90   (miles: Drive Clean 2024 ownership survey, class B self-report)
    PHEV = 10,082 x eUF x 0.35 / 0.90 with electric-utility factor eUF = 0.45 (assumption; range 0.3-0.6)
  Low/high: miles x 0.8 / x 1.2 (NHTS diary vs self-report spread) and eUF 0.3 / 0.6.
- Hour-of-day energy shapes (results/tables/sessions_hourly_energy_share.csv, class C, immediate charging):
    home = norway_residential L2_home; public L2 = boulder_public L2; DCFC = dundee_public DCFC (class C)
    work = NYSERDA 22-03 Fig. 18 weekday workplace charging utilisation (2018-19 mean, anchor hours linearly interpolated;
           class B). The open Midwest workplace dataset was rejected for timing: its weekday peak is at 12:00 vs 9-10 in NY
           (r = 0.47, results/tables/ny_vs_open_weekday_shape_metrics.csv), suggesting a timestamp offset or atypical site.
  Location energy mixture (assumption informed by Drive Clean survey frequencies and national studies):
    base home 0.80 / work 0.07 / public L2 0.08 / DCFC 0.05 ; home-heavy 0.90/0.04/0.03/0.03 ; public-heavy 0.65/0.10/0.13/0.12
- Seasonality: detrended monthly daily-energy index (ratio to 2x12 centred MA) from dundee_public L2 + DCFC (cool climate,
  3-4 years per month; class C). Boulder/Palo Alto show ~no seasonality and Norway has only one year -> not used.
- TEMPO 2022 Tompkins hourly (reference 2026; efs_high_ldv 2026) converted from EST to America/New_York local time.
Outputs
  results/tables/hourly_shape_comparison.csv       hour-of-day energy shares (weekday/weekend) by source
  results/tables/tompkins_2026_load_scenarios.csv  annual MWh, kWh/EV, peak hourly MW, peak hour, load factor
  results/figures/hourly_shape_comparison.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.paths import FIGURES, PROCESSED, TABLES, ensure

MIX = {"base": {"home": .80, "work": .07, "public_l2": .08, "dcfc": .05},
       "home_heavy": {"home": .90, "work": .04, "public_l2": .03, "dcfc": .03},
       "public_heavy": {"home": .65, "work": .10, "public_l2": .13, "dcfc": .12}}
SRC_SHAPE = {"home": ("norway_residential", "L2_home"), "work": ("workplace_midwest", "L2"),
             "public_l2": ("boulder_public", "L2"), "dcfc": ("dundee_public", "DCFC")}


def ev_stock() -> pd.Series:
    d = pd.read_csv(PROCESSED / "dmv" / "tompkins_ev_stock_zip_2026.csv", dtype={"zip": str})
    return d[d["drivetrain"].isin(["BEV", "PHEV"])].groupby("drivetrain")["vehicles"].sum()


def annual_kwh(bev: float, phev: float, case: str) -> float:
    mf = {"low": 0.8, "base": 1.0, "high": 1.2}[case]
    euf = {"low": 0.30, "base": 0.45, "high": 0.60}[case]
    return bev * 10670 * mf * 0.32 / 0.90 + phev * 10082 * mf * euf * 0.35 / 0.90


def ny_workplace_shape() -> np.ndarray:
    f = pd.read_csv(PROCESSED / "nyserda_2203" / "fig18_weekday_charging_utilization_anchor_hours.csv", comment="#")
    a = f[f["land_use"] == "workplace"].groupby("hour")["pct_charging"].mean()
    x = np.array(list(a.index) + [24]); y = np.array(list(a.values) + [a.values[0]])
    prof = np.interp(np.arange(24), x, y)
    return prof / prof.sum()


def shapes() -> dict:
    t = pd.read_csv(TABLES / "sessions_hourly_energy_share.csv")
    out = {("work", "weekday"): ny_workplace_shape(), ("work", "weekend"): ny_workplace_shape()}
    for loc, (ds, pt) in SRC_SHAPE.items():
        if loc == "work":
            continue
        for dt in ["weekday", "weekend"]:
            x = t[(t["dataset"] == ds) & (t["port_type"] == pt) & (t["day_type"] == dt)].sort_values("hour")["energy_share"].values
            if len(x) != 24:  # e.g. workplace has almost no weekend sessions -> use weekday shape
                x = t[(t["dataset"] == ds) & (t["port_type"] == pt) & (t["day_type"] == "all")].sort_values("hour")["energy_share"].values
            out[(loc, dt)] = x / x.sum()
    return out


def weekend_energy_ratio() -> dict:
    s = pd.read_csv(TABLES / "sessions_summary.csv")
    r = {}
    for loc, (ds, pt) in SRC_SHAPE.items():
        g = s[(s["dataset"] == ds) & (s["port_type"] == pt)].set_index("day_type")
        if {"weekday", "weekend"} <= set(g.index):
            wd = g.loc["weekday", "n_sessions"] * g.loc["weekday", "kwh_mean"] / 5
            we = g.loc["weekend", "n_sessions"] * g.loc["weekend", "kwh_mean"] / 2
            r[loc] = we / wd
        else:
            r[loc] = 0.2
    r["work"] = 0.25  # NYSERDA 22-03: weekend peak ~1/4 of weekday
    return r


def month_index() -> pd.Series:
    m = pd.read_csv(TABLES / "sessions_monthly_index.csv")
    m = m[(m["dataset"] == "dundee_public") & m["port_type"].isin(["L2", "DCFC"])]
    idx = m.groupby("month")["daily_kwh_index"].mean()
    return idx / idx.mean()


def build_year(total_kwh: float, mix: dict, year: int = 2026) -> pd.Series:
    sh, wr, mi = shapes(), weekend_energy_ratio(), month_index()
    hrs = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="h", inclusive="left")
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    load = np.zeros(len(hrs))
    for loc, w in mix.items():
        dayw = np.array([(wr[loc] if d.dayofweek >= 5 else 1.0) * mi[d.month] for d in days])
        dayw = dayw / dayw.sum() * total_kwh * w
        prof = np.concatenate([dayw[i] * sh[(loc, "weekend" if d.dayofweek >= 5 else "weekday")] for i, d in enumerate(days)])
        load += prof
    return pd.Series(load, index=hrs)


def tempo(scenario: str, year: int) -> pd.Series:
    t = pd.read_parquet(PROCESSED / "tempo" / f"tompkins_hourly_{scenario}_{year}.parquet")
    s = t.groupby("time_est_utc")["mwh"].sum()
    s.index = pd.DatetimeIndex(s.index).tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    return s * 1000  # kWh


def metrics(name: str, s: pd.Series, n_ev: float, evidence: str) -> dict:
    return {"scenario": name, "evidence": evidence, "annual_mwh": s.sum() / 1000, "kwh_per_ev": s.sum() / n_ev,
            "peak_hour_mw": s.max() / 1000, "peak_kw_per_ev": s.max() / n_ev, "peak_timestamp": str(s.idxmax()),
            "mean_weekday_peak_hour": int(s[s.index.dayofweek < 5].groupby(s.index[s.index.dayofweek < 5].hour).mean().idxmax()),
            "load_factor": s.mean() / s.max()}


def main() -> None:
    ensure(TABLES, FIGURES)
    st = ev_stock()
    bev, phev = float(st.get("BEV", 0)), float(st.get("PHEV", 0))
    n = bev + phev
    rows, series = [], {}
    for case in ["low", "base", "high"]:
        tot = annual_kwh(bev, phev, case)
        for mname, mix in MIX.items():
            if case != "base" and mname != "base":
                continue
            s = build_year(tot, mix)
            series[f"A_{mname}_{case}"] = s
            rows.append(metrics(f"A: stock x kWh/EV ({case}) x location mix ({mname})", s, n, "A stock x B/C assumptions"))
    for sc in ["reference", "efs_high_ldv"]:
        s = tempo(sc, 2026)
        series[f"TEMPO_{sc}"] = s
        rows.append(metrics(f"TEMPO 2022 {sc} MY2026 (model)", s, n, "E model output; per-EV uses DMV stock"))
    res = pd.DataFrame(rows)
    res.insert(1, "bev_2026", bev); res.insert(2, "phev_2026", phev)
    res.round(4).to_csv(TABLES / "tompkins_2026_load_scenarios.csv", index=False)

    shp = []
    for k, s in series.items():
        for dt, m in [("weekday", s.index.dayofweek < 5), ("weekend", s.index.dayofweek >= 5)]:
            x = s[m].groupby(s[m].index.hour).sum()
            for h, v in (x / x.sum()).items():
                shp.append({"source": k, "day_type": dt, "hour": h, "energy_share": v})
    shp = pd.DataFrame(shp)
    shp.round(4).to_csv(TABLES / "hourly_shape_comparison.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for ax, dt in zip(axes, ["weekday", "weekend"]):
        for k in ["A_base_base", "A_home_heavy_base", "A_public_heavy_base", "TEMPO_reference", "TEMPO_efs_high_ldv"]:
            g = shp[(shp["source"] == k) & (shp["day_type"] == dt)]
            ax.plot(g["hour"], g["energy_share"], label=k, ls="--" if k.startswith("TEMPO") else "-")
        ax.set_title(f"Tompkins 2026 hour-of-day energy share — {dt}"); ax.set_xlabel("Local hour")
    axes[0].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIGURES / "hourly_shape_comparison.png", dpi=140)
    print(res.round(3).to_string())


if __name__ == "__main__":
    main()
