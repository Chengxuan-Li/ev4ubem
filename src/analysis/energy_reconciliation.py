"""Reconcile annual charging energy per EV and location energy shares across sources (step 4 of the research plan).

Rows (kWh at the plug per EV-year unless stated):
- Drive Clean 2024 ownership survey miles (BEV 10,670; PHEV 10,082) x efficiency (0.31/0.34 kWh/mi at wheel,
  x1.12 mean TMYx temperature multiplier) / 0.90, PHEV eUF 0.45, Tompkins BEV/PHEV mix (B + assumptions)
- NHTS 2022 BEV diary miles (31.9 mi/vehicle-day, n=166) and self-reported annual miles (12,230 mi) (C)
- Norway residential users: median weekly home energy x 52 (C; apartment garages, home energy only)
- Event model 2026 (simulated; library + Tompkins archetype mixture): all locations, by drivetrain (inferred)
- TEMPO 2022 reference MY2026 annual county energy / observed Tompkins EVs (E)
- County ChargePoint ZIP 14850 kWh/port-day (A/B) is compared with simulated public L2 utilisation in the validation.
Location shares: event model vs earlier assumption (80/7/8/5) vs Drive Clean frequency evidence (qualitative).
Outputs: results/tables/energy_reconciliation.csv, results/figures/energy_reconciliation.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.utils.paths import FIGURES, TABLES, ensure


def main() -> None:
    ensure(TABLES, FIGURES)
    v = pd.read_csv(TABLES / "charging_validation_summary.csv").set_index("check")["value"]
    uf = pd.read_csv(TABLES / "sessions_user_frequency.csv")
    nor_week = float(uf[(uf["dataset"] == "norway_residential") & (uf["quantile"] == 0.5)]["kwh_per_week"].iloc[0])
    evd = pd.read_csv(TABLES / "nhts_ev_vehicle_days_small_sample.csv").set_index("vehfuel")
    mult, eta = 1.12, 0.90
    bev_share = 1833 / 3233
    dc_bev = 10670 * 0.31 * mult / eta
    dc_phev = 10082 * 0.45 * 0.34 * mult / eta
    rows = [
        {"source": "Drive Clean miles x efficiency (BEV)", "evidence": "B+assumption", "kwh_per_ev": dc_bev, "scope": "all locations"},
        {"source": "Drive Clean miles x efficiency (PHEV, eUF 0.45)", "evidence": "B+assumption", "kwh_per_ev": dc_phev, "scope": "all locations"},
        {"source": "Drive Clean miles x efficiency (Tompkins mix)", "evidence": "B+assumption", "kwh_per_ev": bev_share * dc_bev + (1 - bev_share) * dc_phev, "scope": "all locations"},
        {"source": "NHTS 2022 BEV diary miles (n=166)", "evidence": "C", "kwh_per_ev": float(evd.loc["BEV", "w_mean_miles"]) * 365 * 0.31 * mult / eta, "scope": "all locations"},
        {"source": "NHTS 2022 BEV self-reported annual miles", "evidence": "C", "kwh_per_ev": float(evd.loc["BEV", "w_mean_annmiles"]) * 0.31 * mult / eta, "scope": "all locations"},
        {"source": "Norway residential median user (home energy only)", "evidence": "C", "kwh_per_ev": nor_week * 52.14, "scope": "home only"},
        {"source": "Event model 2026: BEV", "evidence": "inferred", "kwh_per_ev": float(v["V5 annual plug kWh per BEV (sim)"]), "scope": "all locations"},
        {"source": "Event model 2026: PHEV", "evidence": "inferred", "kwh_per_ev": float(v["V5 annual plug kWh per PHEV (sim)"]), "scope": "all locations"},
        {"source": "Event model 2026: resident EV mix", "evidence": "inferred", "kwh_per_ev": float(v["V5 annual plug kWh per resident EV (sim)"]), "scope": "all locations"},
        {"source": "TEMPO 2022 reference MY2026 / observed EVs", "evidence": "E", "kwh_per_ev": 7421.0, "scope": "all locations"},
    ]
    t = pd.DataFrame(rows)
    shares = pd.DataFrame({
        "location": ["home", "work", "public_l2", "dcfc"],
        "event_model_2026": [v[f"V5 location energy share {k} (sim)"] for k in ["home", "work", "public_l2", "dcfc"]],
        "earlier_assumption": [0.80, 0.07, 0.08, 0.05],
    })
    t.round(1).to_csv(TABLES / "energy_reconciliation.csv", index=False)
    shares.round(3).to_csv(TABLES / "energy_location_shares.csv", index=False)
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.5), gridspec_kw={"width_ratios": [2, 1]})
    colors = {"B+assumption": "tab:blue", "C": "tab:orange", "inferred": "tab:green", "E": "tab:grey"}
    ax[0].barh(range(len(t)), t["kwh_per_ev"], color=[colors[e] for e in t["evidence"]])
    ax[0].set_yticks(range(len(t))); ax[0].set_yticklabels([f"{s} [{e}]" for s, e in zip(t["source"], t["evidence"])], fontsize=8)
    ax[0].set_xlabel("kWh per EV-year at the plug"); ax[0].set_title("Annual charging energy per EV by source")
    x = range(4)
    ax[1].bar([i - 0.2 for i in x], shares["event_model_2026"], width=0.4, label="event model 2026")
    ax[1].bar([i + 0.2 for i in x], shares["earlier_assumption"], width=0.4, label="earlier assumption")
    ax[1].set_xticks(list(x)); ax[1].set_xticklabels(shares["location"]); ax[1].legend(fontsize=8); ax[1].set_title("Energy share by charging location")
    fig.tight_layout(); fig.savefig(FIGURES / "energy_reconciliation.png", dpi=140); plt.close(fig)
    print(t.round(0).to_string()); print(shares.round(3).to_string())


if __name__ == "__main__":
    main()
