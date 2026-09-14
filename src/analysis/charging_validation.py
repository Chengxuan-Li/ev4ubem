"""Validation of the event-based charging model (2026, trend ownership, base charging) against independent evidence.

V1 home charging frequency (sessions/week categories) vs Drive Clean 2024 ownership survey (B, self-report; categories
   among respondents who charge at home: daily / few per week / weekly / few per month or less).
V2 home session energy and connection-duration quantiles vs Norway residential sessions (C; timing source, so connection
   agreement is partly by construction; energy is not).
V3 weekday hourly shapes (peak-normalised, anchor hours) of simulated county pools vs NYSERDA 22-03 Fig. 18: home vs MUD,
   workplace vs workplace, public L2 vs public (B).
V4 public L2 utilisation (kWh per port-day) vs ChargePoint ZIP 14850 (2019, 2022; A/B) and NYSERDA 22-03 mean (B).
V5 annual kWh per EV and PHEV electric-mile share vs bottom-up survey estimate (inferred), Norway home users (C) and TEMPO (E).
V6 monthly energy index vs Dundee detrended index (C).
V7 diversity: per-EV annual-peak hourly kW of N aggregated simulated home profiles vs Norway empirical diversity curve (C).
V8 county hourly vs TEMPO 2022 reference MY2026 (E; benchmark only): annual energy ratio and weekday shape correlation.
Outputs: results/tables/charging_validation_*.csv, results/figures/charging_validation.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.model.load_assembly import FREQS, Library, archetype_probs, class_profiles, load_dus
from src.utils.paths import FIGURES, INTERIM, PROCESSED, TABLES, ensure

ANCH = [0, 3, 6, 9, 12, 15, 18, 21]


def county_mixture_weights(du: pd.DataFrame, year: int, chg: str) -> pd.Series:
    """Expected share of county resident EVs in each archetype (2026 DU expectations)."""
    w = {}
    for (g, t, wk), gg in du.groupby(["g", "tenure", "workers"]):
        for dt, col in [("BEV", "E_bev"), ("PHEV", "E_phev")]:
            n = gg[col].sum()
            for a, p in archetype_probs(g, t, int(wk), dt, year, chg).items():
                w[a] = w.get(a, 0) + n * p
    s = pd.Series(w)
    return s / s.sum()


def main(year: int = 2026, chg: str = "base") -> None:
    ensure(TABLES, FIGURES)
    lib = Library(year)
    du = load_dus()
    mix = county_mixture_weights(du, year, chg)
    meta = lib.meta.copy()
    meta["key"] = list(zip(meta["drivetrain"], meta["access"], meta["level"], meta["freq"], meta["work"], meta["managed"]))
    meta["w"] = meta["key"].map(mix).fillna(0) / meta.groupby("key")["ev"].transform("size")
    rows = []

    # V1 frequency
    acc = meta[meta["access"] == 1].copy()
    acc["per_week"] = acc["n_home"] / 52.14
    # self-reported categories mapped to session rates: daily >= 4.5/wk ("most days"), few/week 1.5-4.5, weekly 0.6-1.5, rare < 0.6
    acc["cat"] = pd.cut(acc["per_week"], [-0.01, 0.6, 1.5, 4.5, 8], labels=["rare", "weekly", "few_week", "daily"])
    survey = {"BEV": {"daily": 34, "few_week": 28, "weekly": 20, "rare": 7}, "PHEV": {"daily": 51, "few_week": 15, "weekly": 4.4, "rare": 10}}
    v1 = []
    for dt in ["BEV", "PHEV"]:
        a = acc[acc["drivetrain"] == dt]
        sim = a.groupby("cat", observed=False)["w"].sum() / a["w"].sum()
        sv = pd.Series(survey[dt]) / sum(survey[dt].values())
        for c in ["daily", "few_week", "weekly", "rare"]:
            v1.append({"drivetrain": dt, "category": c, "simulated_share": float(sim.get(c, 0)), "drive_clean_share": float(sv[c])})
    v1 = pd.DataFrame(v1)
    v1.round(4).to_csv(TABLES / "charging_validation_frequency.csv", index=False)
    for dt in ["BEV", "PHEV"]:
        q = v1[v1["drivetrain"] == dt]
        rows.append({"check": f"V1 home frequency {dt}", "metric": "total variation distance", "value": 0.5 * np.abs(q["simulated_share"] - q["drive_clean_share"]).sum(), "evidence": "B"})

    # V2 session distributions
    ss = pd.read_parquet(INTERIM / "charging_library" / str(year) / "sessions_sample.parquet")
    from src.analysis.charging_sessions import clean, load_norway
    nor, _ = clean(load_norway(3.6))
    h = ss[ss["location"] == "home"]
    qs = [0.1, 0.25, 0.5, 0.75, 0.9]
    v2 = pd.DataFrame({"quantile": qs, "sim_home_kwh": h["kwh"].quantile(qs).values, "norway_kwh": nor["kwh"].quantile(qs).values,
                       "sim_home_conn_h": h["conn_h"].quantile(qs).values, "norway_conn_h": nor["conn_h"].quantile(qs).values})
    v2.round(3).to_csv(TABLES / "charging_validation_sessions.csv", index=False)
    rows.append({"check": "V2 home session kWh median", "metric": "sim / Norway", "value": float(h["kwh"].median() / nor["kwh"].median()), "evidence": "C"})

    # county pools (expected) for shapes, utilisation, energy
    c = pd.read_parquet(PROCESSED / "load" / f"county_hourly_{year}_trend_{chg}.parquet")
    days = pd.date_range(f"{year}-01-01", periods=365, freq="D")
    hours = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    wdmask = hours.dayofweek < 5
    ny = pd.read_csv(PROCESSED / "nyserda_2203" / "fig18_weekday_charging_utilization_anchor_hours.csv", comment="#").groupby(["land_use", "hour"])["pct_charging"].mean()
    v3 = []
    for loc, lu in [("home", "mud"), ("work", "workplace"), ("public_l2", "public")]:
        prof = c.loc[wdmask, loc].groupby(hours[wdmask].hour).mean().values
        a = prof[ANCH] / prof[ANCH].max()
        b = ny[lu].loc[ANCH].values / ny[lu].loc[ANCH].max()
        r = float(np.corrcoef(a, b)[0, 1])
        v3 += [{"location": loc, "ny_land_use": lu, "hour": hh, "sim_peak_norm": x, "ny_peak_norm": y} for hh, x, y in zip(ANCH, a, b)]
        rows.append({"check": f"V3 weekday shape {loc} vs NY {lu}", "metric": "Pearson r (anchor hours)", "value": r, "evidence": "B"})
    pd.DataFrame(v3).round(4).to_csv(TABLES / "charging_validation_shapes.csv", index=False)

    # V4 public L2 utilisation
    st = pd.read_csv(PROCESSED / "infrastructure" / "tompkins_afdc_stations.csv")
    st = st[(st["status_code"] == "E") & (st["access_code"] == "public")]
    l2_ports = st["ev_level2_evse_num"].fillna(0).sum()
    util = c["public_l2"].sum() / l2_ports / 365
    cp = pd.read_csv(TABLES / "chargepoint_local_use_annual.csv")
    cp14850 = cp[cp["geography"].str.startswith("ZIP 14850")].set_index("year")["kwh_per_port_day"]
    rows += [{"check": "V4 public L2 kWh/port-day (sim, residents only)", "metric": "kWh/port-day", "value": float(util), "evidence": "inferred"},
             {"check": "V4 ChargePoint 14850 2019", "metric": "kWh/port-day", "value": float(cp14850.get(2019, np.nan)), "evidence": "A/B"},
             {"check": "V4 ChargePoint 14850 2022", "metric": "kWh/port-day", "value": float(cp14850.get(2022, np.nan)), "evidence": "A/B"},
             {"check": "V4 NYSERDA 22-03 mean 2012-2020", "metric": "kWh/port-day", "value": 3.25, "evidence": "B"}]

    # V5 energy per EV
    n_res = du["E_ev"].sum()
    res_kwh = c[["home", "work", "public_l2", "dcfc"]].sum().sum()
    ph = meta[meta["drivetrain"] == "PHEV"]
    euf = 1 - (ph["gas_miles"] * ph["w"]).sum() / (ph["annual_miles"] * ph["w"]).sum()
    rows += [{"check": "V5 annual plug kWh per resident EV (sim)", "metric": "kWh/EV", "value": float(res_kwh / n_res), "evidence": "inferred"},
             {"check": "V5 bottom-up survey estimate (Drive Clean miles × efficiency)", "metric": "kWh/EV", "value": 2915.0, "evidence": "B+assumption"},
             {"check": "V5 TEMPO reference MY2026 per observed EV", "metric": "kWh/EV", "value": 7421.0, "evidence": "E"},
             {"check": "V5 simulated PHEV electric-mile share", "metric": "share", "value": float(euf), "evidence": "inferred (assumed 0.45 earlier)"}]
    by_dt = meta.groupby("drivetrain").apply(lambda g: (g[["kwh_home", "kwh_work", "kwh_public_l2", "kwh_dcfc", "kwh_enroute"]].sum(axis=1) * g["w"]).sum() / g["w"].sum())
    for dt, v in by_dt.items():
        rows.append({"check": f"V5 annual plug kWh per {dt} (sim)", "metric": "kWh/EV", "value": float(v), "evidence": "inferred"})
    loc_share = c[["home", "work", "public_l2", "dcfc"]].sum() / res_kwh
    for loc, v in loc_share.items():
        rows.append({"check": f"V5 location energy share {loc} (sim)", "metric": "share", "value": float(v), "evidence": "inferred (earlier assumption 80/7/8/5)"})

    # V6 seasonality
    tot = c.sum(axis=1)
    mon = tot.groupby(hours.month).sum() / pd.Series(hours.month).value_counts().sort_index().values * 24
    mon = mon / mon.mean()
    dm = pd.read_csv(TABLES / "sessions_monthly_index.csv")
    dm = dm[(dm["dataset"] == "dundee_public") & dm["port_type"].isin(["L2", "DCFC"])].groupby("month")["daily_kwh_index"].mean()
    dm = dm / dm.mean()
    v6 = pd.DataFrame({"month": range(1, 13), "sim_index": mon.values, "dundee_index": dm.values})
    v6.round(3).to_csv(TABLES / "charging_validation_seasonality.csv", index=False)
    rows.append({"check": "V6 monthly index vs Dundee", "metric": "Pearson r", "value": float(np.corrcoef(v6["sim_index"], v6["dundee_index"])[0, 1]), "evidence": "C"})

    # V7 diversity
    rng = np.random.default_rng(3)
    home_idx = meta[(meta["access"] == 1)].copy()
    p = home_idx["w"].values / home_idx["w"].sum()
    v7 = []
    for n in [1, 2, 5, 10, 20, 50]:
        peaks = []
        for _ in range(100):
            sel = rng.choice(home_idx["ev"].values, size=n, p=p)
            agg = np.asarray(lib.home[sel]).sum(axis=0)
            peaks.append(agg.max() / n)
        v7.append({"n_evs": n, "sim_peak_kw_per_ev": float(np.mean(peaks))})
    v7 = pd.DataFrame(v7)
    dv = pd.read_csv(TABLES / "diversity_norway_residential.csv")
    for P in ["3.6kW", "7.2kW"]:
        v7 = v7.merge(dv[dv["power_assumption"] == P][["n_evs", "peak_kw_per_ev_mean"]].rename(columns={"peak_kw_per_ev_mean": f"norway_{P}"}), on="n_evs", how="left")
    v7.round(3).to_csv(TABLES / "charging_validation_diversity.csv", index=False)

    # V8 TEMPO
    t = pd.read_parquet(PROCESSED / "tempo" / f"tompkins_hourly_reference_{year}.parquet").groupby("time_est_utc")["mwh"].sum() * 1000
    tp = t.values[:8760]
    tw = pd.Series(tp[wdmask]).groupby(hours[wdmask].hour).mean()
    sw = tot[wdmask].groupby(hours[wdmask].hour).mean()
    rows += [{"check": "V8 TEMPO/simulated annual energy", "metric": "ratio", "value": float(tp.sum() / tot.sum()), "evidence": "E vs inferred"},
             {"check": "V8 weekday hour-of-day shape vs TEMPO (EST vs local std)", "metric": "Pearson r", "value": float(np.corrcoef(tw.values, sw.values)[0, 1]), "evidence": "E vs inferred"}]
    summary = pd.DataFrame(rows)
    summary.round(4).to_csv(TABLES / "charging_validation_summary.csv", index=False)

    fig, ax = plt.subplots(2, 4, figsize=(19, 8.5))
    for i, dt in enumerate(["BEV", "PHEV"]):
        q = v1[v1["drivetrain"] == dt]
        x = np.arange(4)
        ax[0, 0].bar(x + (i - 0.5) * 0.2 - 0.1, q["simulated_share"], width=0.18, label=f"sim {dt}")
        ax[0, 0].bar(x + (i - 0.5) * 0.2 + 0.1, q["drive_clean_share"], width=0.18, alpha=0.6, label=f"Drive Clean {dt}")
    ax[0, 0].set_xticks(range(4)); ax[0, 0].set_xticklabels(["daily", "few/wk", "weekly", "rare"]); ax[0, 0].legend(fontsize=7); ax[0, 0].set_title("V1 home charging frequency")
    ax[0, 1].plot(qs, v2["sim_home_kwh"], "o-", label="sim home kWh"); ax[0, 1].plot(qs, v2["norway_kwh"], "s--", label="Norway kWh")
    ax[0, 1].plot(qs, v2["sim_home_conn_h"], "o-", label="sim conn h"); ax[0, 1].plot(qs, v2["norway_conn_h"], "s--", label="Norway conn h")
    ax[0, 1].set_xlabel("quantile"); ax[0, 1].legend(fontsize=7); ax[0, 1].set_title("V2 home sessions")
    v3d = pd.DataFrame(v3)
    for loc, col in [("home", "tab:blue"), ("work", "tab:orange"), ("public_l2", "tab:green")]:
        q = v3d[v3d["location"] == loc]
        ax[0, 2].plot(q["hour"], q["sim_peak_norm"], "-o", color=col, label=f"sim {loc}")
        ax[0, 2].plot(q["hour"], q["ny_peak_norm"], "--s", color=col, alpha=0.6, label=f"NY {q['ny_land_use'].iloc[0]}")
    ax[0, 2].legend(fontsize=6); ax[0, 2].set_title("V3 weekday shapes vs NYSERDA 22-03")
    labels = ["sim public L2", "ChargePoint 14850 2019", "ChargePoint 14850 2022", "NYSERDA 22-03"]
    vals = [util, cp14850.get(2019, np.nan), cp14850.get(2022, np.nan), 3.25]
    ax[0, 3].bar(range(4), vals, color=["tab:blue", "grey", "grey", "grey"]); ax[0, 3].set_xticks(range(4)); ax[0, 3].set_xticklabels(labels, rotation=25, ha="right", fontsize=7)
    ax[0, 3].set_title("V4 public L2 kWh per port-day")
    e = summary[summary["check"].str.startswith("V5 annual plug kWh per resident") | summary["check"].str.contains("bottom-up|TEMPO reference")]
    ax[1, 0].barh(range(len(e)), e["value"]); ax[1, 0].set_yticks(range(len(e))); ax[1, 0].set_yticklabels([s[3:40] for s in e["check"]], fontsize=7)
    ax[1, 0].set_title("V5 annual kWh per EV")
    ax[1, 1].plot(v6["month"], v6["sim_index"], "o-", label="simulated"); ax[1, 1].plot(v6["month"], v6["dundee_index"], "s--", label="Dundee public (detrended)")
    ax[1, 1].legend(fontsize=7); ax[1, 1].set_title("V6 monthly energy index")
    ax[1, 2].plot(v7["n_evs"], v7["sim_peak_kw_per_ev"], "o-", label="simulated (Tompkins mix)")
    for P in ["3.6kW", "7.2kW"]:
        ax[1, 2].plot(v7["n_evs"], v7[f"norway_{P}"], "s--", label=f"Norway empirical {P}")
    ax[1, 2].set_xscale("log"); ax[1, 2].legend(fontsize=7); ax[1, 2].set_title("V7 per-EV annual peak vs N (home)")
    ax[1, 3].plot(sw.index, sw / sw.sum(), label="simulated county (local std time)"); ax[1, 3].plot(tw.index, tw / tw.sum(), "--", label="TEMPO ref (EST, model)")
    ax[1, 3].legend(fontsize=7); ax[1, 3].set_title("V8 weekday shape vs TEMPO (benchmark)")
    fig.suptitle("Charging model validation, Tompkins 2026 (trend ownership, base charging)")
    fig.tight_layout(); fig.savefig(FIGURES / "charging_validation.png", dpi=130); plt.close(fig)
    print(summary.round(3).to_string())
    print(v1.round(3).to_string()); print(v7.round(2).to_string())


if __name__ == "__main__":
    main()
