"""Harmonise open charging-session datasets and derive behavioural distributions (evidence class C).

None of these datasets is from New York; they are behavioural priors / shape references only. NY-specific
summaries (NYSERDA 22-03, Drive Clean surveys) are compared in docs/findings.md.

Harmonised session schema: dataset, site_type, port_type, start, end, conn_h, charge_h (observed or NaN), kwh, user, station
Datasets and parsing
- norway_residential (home, apartment/co-op garages, Norway, 2018-12..2020-01): `;` + decimal comma; plugin/plugout local.
  No observed charging duration -> charge_h imputed as min(conn_h, kwh / P_home), P_home = 3.6 kW (assumption;
  sensitivity 7.2 kW reported in shape table as 'norway_residential_7kW').
- workplace_midwest (workplace, US Midwest employer, 2014-11..2015-10): created/ended local; chargeTimeHrs equals
  created->ended (connection) in the source; charge_h imputed with P_work = 3.3 kW (typical 2014-15 onboard chargers; assumption).
- boulder_public (public, Boulder CO, 2018-01..2023-09): Start/End local strings; Total_Duration = connection,
  Charging_Time = observed charging; Port_Type Level 2 / DC Fast.
- palo_alto_public (public, Palo Alto CA, 2011-07..2020-12): Start/End Date local; Total Duration, Charging Time observed.
- dundee_public (public, Dundee UK, 2021-07..2025-08): Start/End dd/mm/yyyy; Duration (hh:mm:ss) treated as connection;
  Connector Type ac/fast/rapid. Rapid = DCFC.
Cleaning (applied uniformly): 0.5 <= kwh <= 150; 5 min <= conn_h*60; conn_h <= 72; charge_h <= conn_h + 1 min;
implied average power (kwh / charge_h) <= 350 kW. Sessions dropped are counted per dataset.
Hourly energy allocation: immediate charging from plug-in at constant power kwh/charge_h over charge_h.
Outputs
  results/tables/sessions_summary.csv                  per dataset x site/port x day type
  results/tables/sessions_start_hour_share.csv          plug-in hour shares
  results/tables/sessions_hourly_energy_share.csv       share of daily energy by hour (immediate charging)
  results/tables/sessions_energy_by_start_period.csv    conditional energy/duration by plug-in period
  results/tables/sessions_monthly_index.csv             monthly kWh index (full calendar years only)
  results/tables/sessions_user_frequency.csv            sessions per user-week (datasets with user ids)
  results/figures/sessions_start_hour.png, sessions_hourly_energy_share.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.paths import FIGURES, RAW, TABLES, ensure

SRC = RAW / "charging_sessions"


def _hms(s: pd.Series) -> pd.Series:
    t = s.astype(str).str.strip().str.split(":", expand=True)
    t = t.apply(pd.to_numeric, errors="coerce")
    return t[0] + t[1] / 60 + (t[2] if 2 in t else 0) / 3600


def load_norway(p_home=3.6, tag="norway_residential") -> pd.DataFrame:
    d = pd.read_csv(SRC / "norway_residential" / "Dataset1_charging_reports.csv", sep=";", decimal=",", na_values=["NA"])
    out = pd.DataFrame({"dataset": tag, "site_type": "home", "port_type": "L2_home",
                        "start": pd.to_datetime(d["plugin_time"], errors="coerce"),
                        "end": pd.to_datetime(d["plugout_time"], errors="coerce"),
                        "kwh": d["energy_session"], "user": d["user_id"], "station": d["location"]})
    out["conn_h"] = (out["end"] - out["start"]).dt.total_seconds() / 3600
    out["charge_h"] = np.minimum(out["conn_h"], out["kwh"] / p_home)
    out["charge_h_observed"] = False
    return out


def load_workplace(p_work=3.3) -> pd.DataFrame:
    d = pd.read_csv(SRC / "workplace_midwest" / "ev_workplace_charging_data.tsv", sep="\t")
    out = pd.DataFrame({"dataset": "workplace_midwest", "site_type": "workplace", "port_type": "L2",
                        "start": pd.to_datetime(d["created"], errors="coerce"), "end": pd.to_datetime(d["ended"], errors="coerce"),
                        "kwh": d["kwhTotal"], "user": d["userId"].astype(str), "station": d["stationId"].astype(str)})
    out["conn_h"] = (out["end"] - out["start"]).dt.total_seconds() / 3600
    out["charge_h"] = np.minimum(out["conn_h"], out["kwh"] / p_work)
    out["charge_h_observed"] = False
    return out


def load_boulder() -> pd.DataFrame:
    d = pd.read_parquet(SRC / "boulder_public_l2" / "boulder_sessions.parquet")
    out = pd.DataFrame({"dataset": "boulder_public", "site_type": "public",
                        "port_type": d["Port_Type"].map({"Level 2": "L2", "DC Fast": "DCFC"}).fillna(d["Port_Type"]),
                        "start": pd.to_datetime(d["Start_Date___Time"], format="%m/%d/%Y %H:%M", errors="coerce"),
                        "end": pd.to_datetime(d["End_Date___Time"], format="%m/%d/%Y %H:%M", errors="coerce"),
                        "kwh": pd.to_numeric(d["Energy__kWh_"], errors="coerce"), "user": np.nan, "station": d["Station_Name"]})
    out["conn_h"] = _hms(d["Total_Duration__hh_mm_ss_"])
    out["charge_h"] = _hms(d["Charging_Time__hh_mm_ss_"])
    out["charge_h_observed"] = True
    return out


def load_palo_alto() -> pd.DataFrame:
    d = pd.read_csv(SRC / "palo_alto_public" / "palo_alto_2011_2020.csv", low_memory=False, encoding="utf-8-sig")
    out = pd.DataFrame({"dataset": "palo_alto_public", "site_type": "public",
                        "port_type": d["Port Type"].map({"Level 2": "L2", "Level 1": "L1"}).fillna(d["Port Type"]),
                        "start": pd.to_datetime(d["Start Date"], format="%m/%d/%Y %H:%M", errors="coerce"),
                        "end": pd.to_datetime(d["End Date"], format="%m/%d/%Y %H:%M", errors="coerce"),
                        "kwh": pd.to_numeric(d["Energy (kWh)"], errors="coerce"), "user": d["User ID"].astype(str),
                        "station": d["Station Name"]})
    out["conn_h"] = _hms(d["Total Duration (hh:mm:ss)"])
    out["charge_h"] = _hms(d["Charging Time (hh:mm:ss)"])
    out["charge_h_observed"] = True
    out.loc[out["user"].isin(["nan", ""]), "user"] = np.nan
    return out


def load_dundee() -> pd.DataFrame:
    fr = []
    for f in sorted((SRC / "dundee_public").glob("dundee_*.csv")):
        d = pd.read_csv(f, encoding="latin-1")
        fr.append(pd.DataFrame({"dataset": "dundee_public", "site_type": "public",
                                "port_type": d["Connector Type"].str.lower().map({"rapid": "DCFC", "fast": "L2_fast_AC", "ac": "L2"}).fillna("other"),
                                "start": pd.to_datetime(d["Start"], format="%d/%m/%Y %H:%M", errors="coerce"),
                                "end": pd.to_datetime(d["End"], format="%d/%m/%Y %H:%M", errors="coerce"),
                                "kwh": pd.to_numeric(d["Consum(kWh)"], errors="coerce"), "user": np.nan,
                                "station": d["CP ID"].astype(str), "conn_h": _hms(d["Duration"])}))
    out = pd.concat(fr, ignore_index=True).drop_duplicates()
    out["charge_h"] = np.nan  # not observed; energy allocation uses conn_h for DCFC-dominated data (documented)
    out["charge_h_observed"] = False
    return out


def clean(d: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    n0 = len(d)
    ch = d["charge_h"].where(d["charge_h"].notna() & (d["charge_h"] > 0), d["conn_h"])
    d = d.assign(charge_h=ch)
    ok = (d["kwh"].between(0.5, 150) & (d["conn_h"] * 60 >= 5) & (d["conn_h"] <= 72) & d["start"].notna()
          & (d["charge_h"] <= d["conn_h"] + 1 / 60) & ((d["kwh"] / d["charge_h"]) <= 350))
    d = d[ok].copy()
    d["power_kw"] = d["kwh"] / d["charge_h"]
    d["weekend"] = d["start"].dt.dayofweek >= 5
    d["start_hour"] = d["start"].dt.hour
    return d, n0 - len(d)


def hourly_energy_share(d: pd.DataFrame) -> np.ndarray:
    """Energy by hour-of-day assuming constant power from plug-in for charge_h (immediate charging)."""
    s = d["start"].dt.hour.values + d["start"].dt.minute.values / 60
    e = s + d["charge_h"].values
    p = d["power_kw"].values
    acc = np.zeros(24)
    for k in range(0, 73):
        overlap = np.clip(np.minimum(e, k + 1) - np.maximum(s, k), 0, 1)
        acc[k % 24] += np.sum(overlap * p)
    return acc / acc.sum()


def main() -> None:
    ensure(TABLES, FIGURES)
    loaders = [load_norway, lambda: load_norway(7.2, "norway_residential_7kW"), load_workplace, load_boulder, load_palo_alto, load_dundee]
    frames, dropped = [], {}
    for fn in loaders:
        raw = fn()
        c, nd = clean(raw)
        dropped[c["dataset"].iloc[0]] = (len(raw), nd)
        frames.append(c)
    s = pd.concat(frames, ignore_index=True)
    s["group"] = s["dataset"] + "|" + s["port_type"]
    s = s[s.groupby("group")["kwh"].transform("size") >= 500]

    rows, starts, shapes, cond = [], [], [], []
    for (g, wk), x in list(s.groupby(["group", "weekend"])) + [((g, "all"), x) for g, x in s.groupby("group")]:
        ds, pt = g.split("|")
        daytype = "all" if wk == "all" else ("weekend" if wk else "weekday")
        rows.append({"dataset": ds, "port_type": pt, "site_type": x["site_type"].iloc[0], "day_type": daytype,
                     "n_sessions": len(x), "n_users": x["user"].nunique() if x["user"].notna().any() else np.nan,
                     "period": f"{x['start'].min():%Y-%m}..{x['start'].max():%Y-%m}",
                     "kwh_mean": x["kwh"].mean(), "kwh_p10": x["kwh"].quantile(.1), "kwh_p50": x["kwh"].median(), "kwh_p90": x["kwh"].quantile(.9),
                     "conn_h_p50": x["conn_h"].median(), "conn_h_mean": x["conn_h"].mean(), "conn_h_p90": x["conn_h"].quantile(.9),
                     "charge_h_p50": x["charge_h"].median(), "charge_h_observed": bool(x["charge_h_observed"].iloc[0]),
                     "idle_share_of_conn_mean": 1 - (x["charge_h"].sum() / x["conn_h"].sum()),
                     "power_kw_p50": x["power_kw"].median(), "start_hour_mode": int(x["start_hour"].mode().iloc[0]),
                     "share_start_16_22": x["start_hour"].between(16, 21).mean(), "share_start_06_10": x["start_hour"].between(6, 9).mean(),
                     "spearman_start_hour_vs_conn_h": x["start_hour"].corr(x["conn_h"], method="spearman"),
                     "spearman_conn_h_vs_kwh": x["conn_h"].corr(x["kwh"], method="spearman")})
        sh = x["start_hour"].value_counts(normalize=True).reindex(range(24), fill_value=0)
        starts += [{"dataset": ds, "port_type": pt, "day_type": daytype, "hour": h, "share": v} for h, v in sh.items()]
        es = hourly_energy_share(x)
        shapes += [{"dataset": ds, "port_type": pt, "day_type": daytype, "hour": h, "energy_share": v} for h, v in enumerate(es)]
        if daytype == "all":
            per = pd.cut(x["start_hour"], [-1, 5, 9, 15, 21, 23], labels=["00-06", "06-10", "10-16", "16-22", "22-24"])
            c = x.groupby(per, observed=True).agg(n=("kwh", "size"), kwh_p50=("kwh", "median"), conn_h_p50=("conn_h", "median"), power_kw_p50=("power_kw", "median")).reset_index()
            c.insert(0, "port_type", pt); c.insert(0, "dataset", ds)
            cond.append(c.rename(columns={"start_hour": "start_period"}))
    summ = pd.DataFrame(rows)
    summ["n_raw"] = summ["dataset"].map(lambda k: dropped.get(k, (np.nan,))[0])
    summ["n_dropped_cleaning"] = summ["dataset"].map(lambda k: dropped.get(k, (np.nan, np.nan))[1])
    summ.round(3).to_csv(TABLES / "sessions_summary.csv", index=False)
    pd.DataFrame(starts).round(4).to_csv(TABLES / "sessions_start_hour_share.csv", index=False)
    shp = pd.DataFrame(shapes)
    shp.round(4).to_csv(TABLES / "sessions_hourly_energy_share.csv", index=False)
    pd.concat(cond).round(3).to_csv(TABLES / "sessions_energy_by_start_period.csv", index=False)

    mon = []
    for g, x in s.groupby("group"):
        yrs = x["start"].dt.year
        full = [y for y in yrs.unique() if x.loc[yrs == y, "start"].dt.month.nunique() == 12 and y != 2020]
        if not full:
            continue
        xx = x[yrs.isin(full)]
        m = xx.groupby(xx["start"].dt.month)["kwh"].sum() / len(full)
        dpm = pd.Series([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], index=range(1, 13))
        idx = (m / dpm) / (m.sum() / dpm.sum())
        mon += [{"dataset": g.split("|")[0], "port_type": g.split("|")[1], "years": ",".join(map(str, sorted(full))), "month": k, "daily_kwh_index": v} for k, v in idx.items()]
    pd.DataFrame(mon).round(3).to_csv(TABLES / "sessions_monthly_index.csv", index=False)

    uf = []
    for g, x in s[s["user"].notna()].groupby("group"):
        w = x.assign(week=x["start"].dt.to_period("W"))
        per_user = w.groupby("user").agg(sessions=("kwh", "size"), weeks_active=("week", lambda v: (v.max() - v.min()).n + 1), kwh=("kwh", "sum"))
        per_user = per_user[per_user["weeks_active"] >= 8]
        per_user["sessions_per_week"] = per_user["sessions"] / per_user["weeks_active"]
        per_user["kwh_per_week"] = per_user["kwh"] / per_user["weeks_active"]
        q = per_user[["sessions_per_week", "kwh_per_week"]].quantile([.1, .25, .5, .75, .9])
        for qq, r in q.iterrows():
            uf.append({"dataset": g.split("|")[0], "port_type": g.split("|")[1], "n_users_8wk_plus": len(per_user), "quantile": qq,
                       "sessions_per_week": r["sessions_per_week"], "kwh_per_week": r["kwh_per_week"]})
    pd.DataFrame(uf).round(3).to_csv(TABLES / "sessions_user_frequency.csv", index=False)

    st = pd.DataFrame(starts)
    for tbl, col, fname, ttl in [(st, "share", "sessions_start_hour.png", "Plug-in hour share"),
                                 (shp, "energy_share", "sessions_hourly_energy_share.png", "Share of energy by hour (immediate charging)")]:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
        for ax, dt in zip(axes, ["weekday", "weekend"]):
            for (ds, pt), g in tbl[tbl["day_type"] == dt].groupby(["dataset", "port_type"]):
                ax.plot(g["hour"], g[col], label=f"{ds} {pt}")
            ax.set_title(f"{ttl} — {dt}"); ax.set_xlabel("Local hour")
        axes[0].legend(fontsize=7)
        fig.suptitle("Open charging-session datasets (non-NY; class C behavioural priors)")
        fig.tight_layout(); fig.savefig(FIGURES / fname, dpi=140); plt.close(fig)
    print(summ[summ["day_type"] == "all"][["dataset", "port_type", "n_sessions", "n_users", "period", "kwh_p50", "kwh_mean", "conn_h_p50", "charge_h_p50", "power_kw_p50", "start_hour_mode", "share_start_16_22"]].round(2).to_string())
    print(dropped)


if __name__ == "__main__":
    main()
