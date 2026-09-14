"""Household-level EV ownership propensity by housing/household class from NHTS 2022 (evidence class C).

Why: ZIP-level (ecological) regressions cannot tell how EVs are distributed among household types
inside a ZIP. NHTS is the only public, nationally representative *household-level* microdata here
that links vehicle drivetrain (VEHFUEL 4 = PHEV, 5 = BEV) to home type, tenure, income and area type.
Limitations: 266 EVs nationally (no state identifier); 2022 national adoption differs from 2026 Ithaca;
estimates are relative propensities for downscaling priors, not local rates.

Outputs
  results/tables/nhts_ev_propensity_by_class.csv  weighted share of households with >=1 plug-in vehicle,
      and plug-in share of household vehicles, by HOMETYPE, HOMEOWN, income band, URBRUR, and
      home type x tenure; with unweighted n and bootstrap 90% intervals (household resampling).
  results/tables/nhts_ev_propensity_logit.csv     weighted logit (freq weights normalised to n) of
      household owns plug-in ~ owner + detached + income band + urban + vehicles>=2 ; odds ratios.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.utils.paths import RAW, TABLES, ensure

SRC = RAW / "nhts2022"
RNG = np.random.default_rng(20260914)


def load() -> pd.DataFrame:
    h = pd.read_csv(SRC / "hhv2pub.csv")
    v = pd.read_csv(SRC / "vehv2pub.csv")
    v["plugin"] = v["VEHFUEL"].isin([4, 5])
    hv = v.groupby("HOUSEID").agg(n_veh=("VEHID", "size"), n_plugin=("plugin", "sum"))
    h = h.join(hv, on="HOUSEID")
    h["n_veh"] = h["n_veh"].fillna(0)
    h["n_plugin"] = h["n_plugin"].fillna(0)
    h["has_plugin"] = h["n_plugin"] > 0
    h["home"] = h["HOMETYPE"].map({1: "detached", 2: "attached", 3: "apartment_2plus", 4: "mobile", 5: "other"})
    h["tenure"] = h["HOMEOWN"].map({1: "own", 2: "rent", 97: "other"})
    h["inc"] = pd.cut(h["HHFAMINC"].where(h["HHFAMINC"] > 0), [0, 6, 8, 9, 10, 11],
                      labels=["<50k", "50-100k", "100-125k", "125-150k", "150k+"])
    h["urban"] = h["URBRUR"].map({1: "urban", 2: "rural"})
    h["home_tenure"] = h["home"].astype(str) + "_" + h["tenure"].astype(str)
    return h


def wshare(df, col, w="WTHHFIN"):
    return float(np.average(df[col], weights=df[w])) if len(df) else np.nan


def boot_ci(df, col, reps=400):
    idx = np.arange(len(df))
    vals = []
    for _ in range(reps):
        s = df.iloc[RNG.choice(idx, len(idx))]
        vals.append(wshare(s, col))
    return np.nanpercentile(vals, [5, 95])


def main() -> None:
    ensure(TABLES)
    h = load()
    h_veh = h[h["n_veh"] > 0].copy()
    h_veh["plugin_veh_share"] = h_veh["n_plugin"] / h_veh["n_veh"]
    base = wshare(h, "has_plugin")
    rows = []
    for dim in ["home", "tenure", "inc", "urban", "home_tenure"]:
        for lvl, g in h.groupby(dim, observed=True):
            if len(g) < 30:
                continue
            lo, hi = boot_ci(g, "has_plugin")
            gv = h_veh[h_veh[dim] == lvl]
            rows.append({"dimension": dim, "level": lvl, "n_households": len(g), "n_hh_with_plugin": int(g["has_plugin"].sum()),
                         "w_share_hh_with_plugin": wshare(g, "has_plugin"), "ci90_lo": lo, "ci90_hi": hi,
                         "relative_to_all_hh": wshare(g, "has_plugin") / base,
                         "w_plugin_share_of_hh_vehicles": float(np.average(gv["plugin_veh_share"], weights=gv["WTHHFIN"] * gv["n_veh"])) if len(gv) else np.nan})
    rows.append({"dimension": "all", "level": "all", "n_households": len(h), "n_hh_with_plugin": int(h["has_plugin"].sum()),
                 "w_share_hh_with_plugin": base, "relative_to_all_hh": 1.0})
    pd.DataFrame(rows).round(4).to_csv(TABLES / "nhts_ev_propensity_by_class.csv", index=False)

    d = h.dropna(subset=["inc", "home", "tenure", "urban"]).copy()
    X = pd.DataFrame({
        "owner": (d["tenure"] == "own").astype(float),
        "detached_or_attached": d["home"].isin(["detached", "attached"]).astype(float),
        "inc_100_150k": d["inc"].isin(["100-125k", "125-150k"]).astype(float),
        "inc_150k_plus": (d["inc"] == "150k+").astype(float),
        "inc_50_100k": (d["inc"] == "50-100k").astype(float),
        "urban": (d["urban"] == "urban").astype(float),
        "veh2plus": (d["n_veh"] >= 2).astype(float),
    })
    X = sm.add_constant(X)
    w = d["WTHHFIN"] / d["WTHHFIN"].mean()
    m = sm.GLM(d["has_plugin"].astype(float), X, family=sm.families.Binomial(), var_weights=w).fit(cov_type="HC1")
    ci = m.conf_int()
    out = pd.DataFrame({"term": m.params.index, "odds_ratio": np.exp(m.params.values), "or_lo": np.exp(ci[0].values),
                        "or_hi": np.exp(ci[1].values), "p": m.pvalues.values, "n": len(d), "n_events": int(d["has_plugin"].sum())})
    out.round(4).to_csv(TABLES / "nhts_ev_propensity_logit.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string())
    print(out.round(3).to_string())


if __name__ == "__main__":
    main()
