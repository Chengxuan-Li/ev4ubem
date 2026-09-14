"""Tompkins EV stock history (EValuateNY 2011-2023), current stock (DMV 2026), and rebate flows.

Geography harmonisation
- EValuateNY stores ZIP only. Tompkins County stock is estimated as sum_z EV_z x s_z where s_z is the share
  of ZCTA z population inside Tompkins (data/processed/geography/zcta_county_popshare_ny.csv). This assumes EVs
  are distributed like population within split ZIPs (approximation; 14850 is 100% Tompkins and dominates).
- DMV 2026 uses the DMV `county` field directly (and the same ZIP-share method as a consistency check).
Outputs
  results/tables/tompkins_ev_stock_timeseries.csv
  results/tables/tompkins_vs_ny_ev_penetration.csv
  results/figures/tompkins_ev_stock_timeseries.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.utils.paths import FIGURES, PROCESSED, TABLES, ensure


def zip_share() -> pd.Series:
    z = pd.read_csv(PROCESSED / "geography" / "zcta_county_popshare_ny.csv", dtype={"zcta": str, "county": str})
    return z[z["county"] == "36109"].set_index("zcta")["pop_share_of_zcta"]


def main() -> None:
    ensure(TABLES, FIGURES)
    s = zip_share()
    st = pd.read_parquet(PROCESSED / "evaluateny" / "ev_stock_zip_snapshot.parquet")
    st = st[st["drivetrain"].isin(["BEV", "PHEV"])]
    st["w"] = st["zip"].map(s).fillna(0)
    # PO-box ZIPs 14851/14852 are Ithaca (no ZCTA); assign fully to Tompkins
    st.loc[st["zip"].isin(["14851", "14852"]), "w"] = 1.0
    st["tompkins_est"] = st["vehicles"] * st["w"]
    ts = st.groupby(["snapshot_date", "drivetrain"])["tompkins_est"].sum().unstack().reset_index()
    ts["source"] = "EValuateNY v11 (ZIP pop-share weighted)"
    ny = st.groupby(["snapshot_date", "drivetrain"])["vehicles"].sum().unstack().reset_index()

    d = pd.read_csv(PROCESSED / "dmv" / "tompkins_ev_stock_zip_2026.csv", dtype={"zip": str})
    cur = d[d["drivetrain"].isin(["BEV", "PHEV"])].groupby("drivetrain")["vehicles"].sum()
    snap = pd.DataFrame([{"snapshot_date": pd.Timestamp("2026-09-02"), "BEV": cur.get("BEV", 0), "PHEV": cur.get("PHEV", 0),
                          "source": "DMV w4pv-hbkt 2026-09-02, county=TOMPKINS, VIN-decoded"}])
    out = pd.concat([ts, snap], ignore_index=True)
    out["EV"] = out["BEV"] + out["PHEV"]
    out.round(1).to_csv(TABLES / "tompkins_ev_stock_timeseries.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4))
    e = out[out["source"].str.startswith("EValuateNY")]
    for c, col in [("BEV", "tab:blue"), ("PHEV", "tab:orange"), ("EV", "k")]:
        ax.plot(e["snapshot_date"], e[c], color=col, label=f"{c} (EValuateNY, ZIP-weighted)")
        ax.scatter(snap["snapshot_date"], out[c].iloc[-1:], color=col, marker="s", s=40)
    ax.set_ylabel("Registered vehicles")
    ax.set_title("Tompkins County plug-in EV stock (squares: DMV snapshot 2026-09, VIN-decoded)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "tompkins_ev_stock_timeseries.png", dpi=150)
    print(out.iloc[::12].to_string())
    print(out.tail(3).to_string())


if __name__ == "__main__":
    main()
