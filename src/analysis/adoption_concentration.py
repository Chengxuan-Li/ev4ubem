"""How concentrated is EV adoption across NY ZIPs as statewide penetration rises? (evidence for propensity convergence)

Data: EValuateNY ZIP x snapshot EV stock (2011-2023, VIN-decoded) and DMV 2026 statewide ZIP table; ACS 2020-2024 ZCTA
households as a fixed denominator (composition drift over 2011-2026 ignored). ZIPs with >= 500 households.
Metrics per snapshot (last snapshot of each year + 2026):
  statewide EVs per 100 households (penetration)
  Gini coefficient of EVs across households (ZIP-level Lorenz curve, household-weighted)
  share of EVs in the top-decile ZIPs by EV/household
  elasticity: slope of log(EV/HH) on log(median home value) and on bachelor's+ share (household-weighted OLS, ZIPs with EV>0)
  concentration exponent φ: ZIP EV/HH rate r_z(t) regressed as log r_z(t) = a_t + φ_t log r_z(2023) (fixed reference);
  φ < 1 over time means relative differences shrink.
Outputs: results/tables/adoption_concentration_ny.csv, results/figures/adoption_concentration_ny.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.paths import FIGURES, PROCESSED, TABLES, ensure


def gini(x, w):
    o = np.argsort(x / w)
    x, w = x[o], w[o]
    cw, cx = np.cumsum(w) / w.sum(), np.cumsum(x) / x.sum()
    cw, cx = np.concatenate([[0], cw]), np.concatenate([[0], cx])
    return 1 - np.sum((cw[1:] - cw[:-1]) * (cx[1:] + cx[:-1]))


def wls_slope(y, x, w):
    X = np.column_stack([np.ones_like(x), x])
    W = np.sqrt(w)
    b = np.linalg.lstsq(X * W[:, None], y * W, rcond=None)[0]
    return b[1]


def main() -> None:
    ensure(TABLES, FIGURES)
    a = pd.read_parquet(PROCESSED / "acs" / "acs_features_ny_zcta.parquet")[["geoid", "households", "med_home_value", "ba_plus_share"]]
    a = a[a["households"] >= 500].rename(columns={"geoid": "zip"})
    s = pd.read_parquet(PROCESSED / "evaluateny" / "ev_stock_zip_snapshot.parquet")
    s = s[s["drivetrain"].isin(["BEV", "PHEV"])]
    last = s.groupby(s["snapshot_date"].dt.year)["snapshot_date"].max()
    s = s[s["snapshot_date"].isin(last)]
    panel = s.groupby(["snapshot_date", "zip"])["vehicles"].sum().rename("ev").reset_index()
    d26 = pd.read_parquet(PROCESSED / "dmv" / "ny_zip_drivetrain_2026.parquet")
    d26 = d26[d26["drivetrain"].isin(["BEV", "PHEV"]) & d26["county"].ne("OUT-OF-STATE")].groupby("zip")["vehicles"].sum().rename("ev").reset_index()
    d26["snapshot_date"] = pd.Timestamp("2026-09-02")
    panel = pd.concat([panel, d26])
    ref = panel[panel["snapshot_date"].dt.year == 2023].set_index("zip")["ev"]
    rows = []
    for t, g in panel.groupby("snapshot_date"):
        m = a.merge(g, on="zip", how="left").fillna({"ev": 0})
        if m["ev"].sum() < 500:
            continue
        rate = m["ev"] / m["households"]
        top = m.assign(rate=rate).sort_values("rate", ascending=False)
        cut = top["households"].cumsum() <= 0.1 * top["households"].sum()
        pos = m[(m["ev"] > 0) & m["med_home_value"].notna() & m["ba_plus_share"].notna()]
        lr = np.log(pos["ev"] / pos["households"])
        mm = m.merge(ref.rename("ev_ref"), left_on="zip", right_index=True)
        mm = mm[(mm["ev"] > 0) & (mm["ev_ref"] > 0)]
        phi = wls_slope(np.log(mm["ev"] / mm["households"]).values, np.log(mm["ev_ref"] / mm["households"]).values, mm["households"].values)
        rows.append({"snapshot": t.date(), "zips": len(m), "evs": int(m["ev"].sum()), "ev_per_100hh": 100 * m["ev"].sum() / m["households"].sum(),
                     "gini_households": gini(m["ev"].values.astype(float), m["households"].values.astype(float)),
                     "top_decile_hh_share_of_evs": top.loc[cut, "ev"].sum() / m["ev"].sum(),
                     "zero_ev_zip_share": float((m["ev"] == 0).mean()),
                     "elasticity_home_value": wls_slope(lr.values, np.log(pos["med_home_value"]).values, pos["households"].values),
                     "slope_ba_share": wls_slope(lr.values, pos["ba_plus_share"].values, pos["households"].values),
                     "phi_vs_2023": phi})
    r = pd.DataFrame(rows)
    r.round(4).to_csv(TABLES / "adoption_concentration_ny.csv", index=False)
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    ax[0].plot(r["ev_per_100hh"], r["gini_households"], marker="o")
    for _, q in r.iterrows():
        ax[0].annotate(str(q["snapshot"])[:4], (q["ev_per_100hh"], q["gini_households"]), fontsize=7)
    ax[0].set_xscale("log"); ax[0].set_xlabel("NY EVs per 100 households"); ax[0].set_ylabel("Gini across households (ZIP level)")
    ax[1].plot(r["ev_per_100hh"], r["top_decile_hh_share_of_evs"], marker="o"); ax[1].set_xscale("log")
    ax[1].set_xlabel("NY EVs per 100 households"); ax[1].set_ylabel("EV share in top-decile ZIPs (by households)")
    ax[2].plot(r["ev_per_100hh"], r["elasticity_home_value"], marker="o", label="elasticity to median home value")
    ax[2].plot(r["ev_per_100hh"], r["phi_vs_2023"], marker="s", label="φ: slope on 2023 log rate")
    ax[2].set_xscale("log"); ax[2].axhline(1, color="grey", lw=0.6); ax[2].legend(fontsize=8); ax[2].set_xlabel("NY EVs per 100 households")
    fig.suptitle("Concentration of EV adoption across NY ZIPs vs penetration (EValuateNY 2011-2023, DMV 2026; class D/A)")
    fig.tight_layout(); fig.savefig(FIGURES / "adoption_concentration_ny.png", dpi=140)
    print(r.round(3).to_string())


if __name__ == "__main__":
    main()
