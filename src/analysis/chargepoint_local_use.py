"""Observed public charging use in Tompkins-area ZIPs from EValuateNY's ChargePoint ZIP-month table (class B/A).

Source: EValuateNY v11 resources.xlsx sheet 'Charging Use' (ChargePoint network only; aggregated by station ZIP and
month; 2010-12..2022-12), exported to data/processed/evaluateny/chargepoint_use_zip_month.csv.
Metrics per ZIP-month: kWh, sessions, kWh/session, sessions per active port per day, kWh per port per day,
charging hours / connected hours (utilisation of connection time), mean kW while charging.
Outputs: results/tables/chargepoint_local_use_monthly.csv, results/tables/chargepoint_local_use_annual.csv,
         results/figures/chargepoint_local_use.png
Caveats: ChargePoint only (in 2026, 51 of 105 Tompkins AFDC stations are ChargePoint); ends 2022; includes
workplace/MUD ports if networked on ChargePoint; COVID effects 2020-2021.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.utils.paths import FIGURES, PROCESSED, TABLES, ensure

ZIPS = ["14850", "14853", "13053", "13045", "14886", "14882", "13068"]


def main() -> None:
    ensure(TABLES, FIGURES)
    cu = pd.read_csv(PROCESSED / "evaluateny" / "chargepoint_use_zip_month.csv", dtype={"ZIP Code": str}, parse_dates=["Start Date"])
    cu = cu.rename(columns={"Start Date": "month", "ZIP Code": "zip", "Energy (kWh)": "kwh", "Charging Sessions": "sessions",
                            "Charging Time (Hours)": "charge_h", "Total Duration (Hours)": "conn_h",
                            "Active Station Count": "stations", "Active Port Count": "ports"})
    ny = cu.copy()
    t = cu[cu["zip"].isin(ZIPS)].copy()
    t = t.groupby(["zip", "month"], as_index=False)[["kwh", "sessions", "charge_h", "conn_h", "stations", "ports"]].sum()
    days = t["month"].dt.days_in_month
    t["kwh_per_session"] = t["kwh"] / t["sessions"]
    t["sessions_per_port_day"] = t["sessions"] / t["ports"] / days
    t["kwh_per_port_day"] = t["kwh"] / t["ports"] / days
    t["charge_share_of_connection"] = t["charge_h"] / t["conn_h"]
    t["mean_kw_while_charging"] = t["kwh"] / t["charge_h"]
    t.round(3).to_csv(TABLES / "chargepoint_local_use_monthly.csv", index=False)

    def annual(x: pd.DataFrame, label: str) -> pd.DataFrame:
        x = x.assign(year=x["month"].dt.year, days=x["month"].dt.days_in_month)
        x["port_days"] = x["ports"] * x["days"]
        a = x.groupby("year").agg(kwh=("kwh", "sum"), sessions=("sessions", "sum"), charge_h=("charge_h", "sum"), conn_h=("conn_h", "sum"),
                                  port_days=("port_days", "sum"), max_ports=("ports", "max"), months=("month", "nunique")).reset_index()
        a["kwh_per_session"] = a["kwh"] / a["sessions"]
        a["kwh_per_port_day"] = a["kwh"] / a["port_days"]
        a["sessions_per_port_day"] = a["sessions"] / a["port_days"]
        a["charge_share_of_connection"] = a["charge_h"] / a["conn_h"]
        a["mean_kw_while_charging"] = a["kwh"] / a["charge_h"]
        a.insert(0, "geography", label)
        return a

    ann = pd.concat([annual(t[t["zip"] == "14850"], "ZIP 14850 (Ithaca)"),
                     annual(t, "Tompkins-area ZIPs " + "/".join(ZIPS)),
                     annual(ny, "New York State (all ChargePoint ZIPs in table)")])
    ann.round(3).to_csv(TABLES / "chargepoint_local_use_annual.csv", index=False)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    x = t[t["zip"] == "14850"]
    ax[0].plot(x["month"], x["kwh"] / 1000, label="MWh / month")
    ax[0].plot(x["month"], x["ports"], label="active ports")
    ax[0].legend(); ax[0].set_title("ChargePoint, ZIP 14850 (EValuateNY; class A/B)")
    for g, a in ann.groupby("geography"):
        ax[1].plot(a["year"], a["kwh_per_port_day"], marker="o", label=g)
    ax[1].set_title("kWh per port-day"); ax[1].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIGURES / "chargepoint_local_use.png", dpi=140)
    print(ann[ann["year"] >= 2016].round(2).to_string())


if __name__ == "__main__":
    main()
