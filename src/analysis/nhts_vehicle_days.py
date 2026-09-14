"""NHTS 2022 vehicle-day travel metrics as behavioural priors for EV charging demand (evidence class C).

NHTS 2022 public files contain no state identifier and only 186 BEVs + 80 PHEVs nationally, so this
analysis characterises *all household light-duty vehicles*, stratified by geography classes relevant
to Ithaca (Mid-Atlantic, MSA < 1 million = CDIVMSAR 23; urban/rural) and by weekday/weekend.

Vehicle-day construction
- Universe: household vehicles (vehv2pub) of types car/van/SUV/pickup (VEHTYPE 1-4) in households with a
  complete travel day. Each vehicle contributes one vehicle-day (the household's assigned travel day).
- Driven miles: sum of TRPMILES over trips where TRPHHVEH == 1 (household vehicle), DRVR_FLG == 1 (the
  respondent drove) and VEHID matches. Vehicles with no such trips have 0 miles.
- Last arrival home: ENDTIME of the last driver trip of the vehicle-day whose WHYTO is 1 or 2 (home).
- First departure: STRTTIME of the first driver trip.
- Work arrival/dwell: first driver trip with WHYTO == 3 (work at non-home location), its ENDTIME and DWELTIME.
Weights: WTHHFIN (household weight) applied to vehicles; weighted quantiles reported, with unweighted n.
Known limitation (diagnosed 2026-09-14): trip-diary vehicle-day miles average ~16 mi/day for all LDVs,
while self-reported ANNMILES/365 averages ~37 (median ~19). Only 10,592 of 16,997 persons report any trip
and trips by non-responding household members are missing, so diary miles are a lower bound and
self-reported annual miles likely an upper bound. Both are reported (see ann_miles_* columns).
Energy translation (illustrative, not NHTS data): kWh = miles x 0.30 kWh/mi (assumption, see findings).
Outputs: results/tables/nhts_vehicle_day_summary.csv, nhts_hourly_arrival_home_share.csv,
         nhts_daily_miles_quantiles.csv ; results/figures/nhts_arrival_home_hour.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.paths import FIGURES, RAW, TABLES, ensure

SRC = RAW / "nhts2022"


def wquantile(x, w, qs):
    x, w = np.asarray(x, float), np.asarray(w, float)
    m = ~np.isnan(x)
    x, w = x[m], w[m]
    if len(x) == 0:
        return [np.nan] * len(qs)
    o = np.argsort(x)
    x, w = x[o], w[o]
    c = np.cumsum(w) / w.sum()
    return [float(np.interp(q, c, x)) for q in qs]


def hhmm_to_hour(v):
    v = pd.to_numeric(v, errors="coerce")
    v = v.where(v >= 0)
    return (v // 100) + (v % 100) / 60


def build() -> pd.DataFrame:
    veh = pd.read_csv(SRC / "vehv2pub.csv")
    trip = pd.read_csv(SRC / "tripv2pub.csv")
    veh = veh[veh["VEHTYPE"].isin([1, 2, 3, 4])].copy()
    d = trip[(trip["TRPHHVEH"] == 1) & (trip["DRVR_FLG"] == 1) & (trip["VEHID"] > 0)].copy()
    d["start_h"] = hhmm_to_hour(d["STRTTIME"])
    d["end_h"] = hhmm_to_hour(d["ENDTIME"])
    d["miles"] = d["TRPMILES"].where(d["TRPMILES"] >= 0)
    d = d.sort_values(["HOUSEID", "VEHID", "start_h"])
    agg = d.groupby(["HOUSEID", "VEHID"]).agg(miles=("miles", "sum"), trips=("miles", "size"), first_dep_h=("start_h", "min"))
    home = d[d["WHYTO"].isin([1, 2])].groupby(["HOUSEID", "VEHID"])["end_h"].max().rename("last_home_arr_h")
    work = d[d["WHYTO"] == 3].groupby(["HOUSEID", "VEHID"]).agg(work_arr_h=("end_h", "min"), work_dwell_min=("DWELTIME", "max"))
    vd = veh.set_index(["HOUSEID", "VEHID"]).join(agg).join(home).join(work).reset_index()
    vd["miles"] = vd["miles"].fillna(0)
    vd["trips"] = vd["trips"].fillna(0)
    vd["weekend"] = vd["TRAVDAY"].isin([1, 7])
    vd["used"] = vd["trips"] > 0
    vd["work_dwell_min"] = vd["work_dwell_min"].where(vd["work_dwell_min"] >= 0)
    vd["geo"] = np.select([vd["CDIVMSAR"] == 23, vd["CDIVMSAR"] == 24, vd["CENSUS_D"] == 2],
                          ["MidAtl_MSA<1M", "MidAtl_nonMSA", "MidAtl_other"], "US_other")
    return vd


def summarise(vd: pd.DataFrame) -> pd.DataFrame:
    rows = []
    groups = {
        "US_all": vd,
        "MidAtlantic_all": vd[vd["CENSUS_D"] == 2],
        "MidAtl_MSA<1M (CDIVMSAR 23)": vd[vd["CDIVMSAR"] == 23],
        "US_urban": vd[vd["URBRUR"] == 1],
        "US_rural": vd[vd["URBRUR"] == 2],
        "US_MSA<1M_or_nonMSA": vd[vd["MSASIZE"].isin([1, 2, 6])] if "MSASIZE" in vd else vd.iloc[0:0],
    }
    for gname, g in groups.items():
        for wk, gg in [("weekday", g[~g["weekend"]]), ("weekend", g[g["weekend"]]), ("all", g)]:
            if len(gg) == 0:
                continue
            w = gg["WTHHFIN"]
            q = wquantile(gg["miles"], w, [0.1, 0.25, 0.5, 0.75, 0.9, 0.95])
            arr = gg[gg["last_home_arr_h"].notna()]
            wrk = gg[gg["work_arr_h"].notna()]
            rows.append({
                "group": gname, "day_type": wk, "n_vehicle_days": len(gg),
                "w_share_used": float(np.average(gg["used"], weights=w)),
                "w_mean_miles": float(np.average(gg["miles"], weights=w)),
                "miles_p10": q[0], "miles_p25": q[1], "miles_p50": q[2], "miles_p75": q[3], "miles_p90": q[4], "miles_p95": q[5],
                "n_home_arrivals": len(arr),
                "last_home_arr_h_p25": wquantile(arr["last_home_arr_h"], arr["WTHHFIN"], [0.25])[0],
                "last_home_arr_h_p50": wquantile(arr["last_home_arr_h"], arr["WTHHFIN"], [0.5])[0],
                "last_home_arr_h_p75": wquantile(arr["last_home_arr_h"], arr["WTHHFIN"], [0.75])[0],
                "n_work_arrivals": len(wrk),
                "work_arr_h_p50": wquantile(wrk["work_arr_h"], wrk["WTHHFIN"], [0.5])[0],
                "work_dwell_h_p50": wquantile(wrk["work_dwell_min"] / 60, wrk["WTHHFIN"], [0.5])[0],
                "w_mean_kwh_at_0.30kwh_per_mi": float(np.average(gg["miles"], weights=w)) * 0.30,
                "ann_miles_per_day_w_mean": float(np.average((gg["ANNMILES"].where(gg["ANNMILES"] >= 0) / 365).fillna(0),
                                                             weights=w * gg["ANNMILES"].ge(0))),
                "ann_miles_per_day_p50": wquantile(gg["ANNMILES"].where(gg["ANNMILES"] >= 0) / 365, w, [0.5])[0],
            })
    return pd.DataFrame(rows)


def main() -> None:
    ensure(TABLES, FIGURES)
    vd = build()
    s = summarise(vd)
    s.round(3).to_csv(TABLES / "nhts_vehicle_day_summary.csv", index=False)

    ev = vd[vd["VEHFUEL"].isin([4, 5])]
    evs = pd.DataFrame([{"vehfuel": k, "n_vehicles": len(g), "w_mean_miles": float(np.average(g["miles"], weights=g["WTHHFIN"])),
                         "w_median_miles": wquantile(g["miles"], g["WTHHFIN"], [0.5])[0],
                         "w_mean_annmiles": float(np.average(g["ANNMILES"].where(g["ANNMILES"] >= 0).fillna(g["ANNMILES"].median()), weights=g["WTHHFIN"]))}
                        for k, g in ev.groupby(ev["VEHFUEL"].map({4: "PHEV", 5: "BEV"}))])
    evs.round(2).to_csv(TABLES / "nhts_ev_vehicle_days_small_sample.csv", index=False)

    rows = []
    for gname, g in {"US_all": vd, "MidAtl_MSA<1M": vd[vd["CDIVMSAR"] == 23], "US_rural": vd[vd["URBRUR"] == 2]}.items():
        for wk, gg in [("weekday", g[~g["weekend"]]), ("weekend", g[g["weekend"]])]:
            a = gg[gg["last_home_arr_h"].notna()]
            h = np.floor(a["last_home_arr_h"]).clip(0, 23).astype(int)
            share = a.groupby(h)["WTHHFIN"].sum() / a["WTHHFIN"].sum()
            for hr in range(24):
                rows.append({"group": gname, "day_type": wk, "hour": hr, "w_share_last_home_arrival": float(share.get(hr, 0.0)), "n": len(a)})
    hh = pd.DataFrame(rows)
    hh.round(4).to_csv(TABLES / "nhts_hourly_arrival_home_share.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4))
    for (gname, wk), g in hh.groupby(["group", "day_type"]):
        ax.plot(g["hour"], g["w_share_last_home_arrival"], label=f"{gname} {wk} (n={g['n'].iloc[0]})",
                ls="-" if wk == "weekday" else "--")
    ax.set_xlabel("Hour of last arrival home (local)")
    ax.set_ylabel("Weighted share of vehicle-days")
    ax.set_title("NHTS 2022: last driver arrival home by hour (all household LDVs; class C evidence)")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIGURES / "nhts_arrival_home_hour.png", dpi=150)
    print(s[["group", "day_type", "n_vehicle_days", "w_share_used", "w_mean_miles", "miles_p50", "last_home_arr_h_p50", "work_arr_h_p50", "work_dwell_h_p50"]].round(2).to_string())
    print(evs.round(1).to_string())


if __name__ == "__main__":
    main()
