"""Place the NYSEG planning-forecast EV adoption levels alongside this model's adoption metrics.

Context. Avangrid's 2026-09-14 working document ("Tompkins County Electrification Modeling — Proposed
Near-Term Deliverables for Cornell") asks for county scenario runs at NYSEG forecast adoption levels of
7.02 % EV adoption in 2030 and 39.41 % in 2040, stated "by circuit". The document does not define the
denominator of "EV adoption", and this repository carries four adoption metrics that differ by more than
4x in 2030 (report section 4.6, growth_projection_tompkins.csv). Comparing the wrong pair is the single
easiest way to reach a wrong conclusion about whether the two forecasts agree, so this module tabulates
every candidate basis rather than choosing one.

Metrics (all Tompkins, median of the growth Monte Carlo unless stated):
- fleet_share_pev   EV stock (BEV + PHEV) / light-duty vehicle fleet. The repository headline; denominator
                    F = 59,554 DMV light-duty vehicles, held constant to 2050 (no fleet growth modelled).
- fleet_share_bev   BEV stock only / the same fleet denominator. Tompkins is 44 % PHEV against a New York
                    average of 35 %, so the plug-in/battery-only distinction moves the 2030 level by ~39 %.
- new_share         EV share of new light-duty additions. A flow, not a stock; listed to rule it out.
- hh_with_ev_share  Expected share of the 43,251 synthetic dwelling units with at least one EV (capped).

Growth ratios (2030 -> 2040) are reported because they are denominator-free: rescaling the metric leaves
the ratio unchanged, so a ratio mismatch cannot be explained away by a definitional difference.

The indicative-load table scales county annual energy and peak by the EV-count ratio between the NYSEG
level and the nearest modelled scenario year. It is an interpolation of existing runs, NOT a scenario run
at NYSEG adoption levels; peak scaling in particular is approximate because coincidence changes with fleet
size. It is labelled as such wherever it is used.

Evidence classes: this model's values are "inferred"; the NYSEG levels are class E (external model output)
and agreement with them is a benchmark, never validation.

Outputs: results/tables/avangrid_ev_adoption_metrics.csv
         results/tables/avangrid_ev_growth_ratios.csv
         results/tables/avangrid_ev_indicative_load.csv
"""
from __future__ import annotations

import pandas as pd

from src.utils.paths import TABLES, ensure

# NYSEG planning forecast levels, Avangrid working document 2026-09-14 (class E; denominator unstated).
NYSEG_EV = {2030: 0.0702, 2040: 0.3941}
# Light-duty fleet denominator used throughout the growth model (src/model/growth.py, GEO["tompkins"]["F"]).
FLEET_LDV = 59554.0
ANCHORS = [2026, 2030, 2035, 2040, 2045, 2050]
METRIC_LABEL = {
    "fleet_share_pev": "EV stock (BEV + PHEV) / light-duty fleet",
    "fleet_share_bev": "BEV stock only / light-duty fleet",
    "new_share": "EV share of new light-duty additions (flow)",
    "hh_with_ev_share": "Dwelling units with at least one EV",
}


def adoption_metrics() -> pd.DataFrame:
    g = pd.read_csv(TABLES / "growth_projection_tompkins.csv")
    a = pd.read_csv(TABLES / "allocation_evolution_by_scenario.csv")
    g = g[g["year"].isin(ANCHORS)]
    rows = []
    for _, r in g.iterrows():
        rows += [
            {"scenario": r["scenario"], "year": int(r["year"]), "metric": "fleet_share_pev",
             "value": r["fleet_share_p50"], "low": r["fleet_share_p05"], "high": r["fleet_share_p95"],
             "numerator": r["EV_p50"], "denominator": FLEET_LDV},
            {"scenario": r["scenario"], "year": int(r["year"]), "metric": "fleet_share_bev",
             "value": r["BEV_p50"] / FLEET_LDV, "low": None, "high": None,
             "numerator": r["BEV_p50"], "denominator": FLEET_LDV},
            {"scenario": r["scenario"], "year": int(r["year"]), "metric": "new_share",
             "value": r["new_share_p50"], "low": None, "high": None,
             "numerator": None, "denominator": None},
        ]
    hh = a[a["year"].isin(ANCHORS)]
    for _, r in hh.iterrows():
        rows.append({"scenario": r["scenario"], "year": int(r["year"]), "metric": "hh_with_ev_share",
                     "value": r["hh_with_ev_share_expected"], "low": None, "high": None,
                     "numerator": None, "denominator": 43251.0})
    df = pd.DataFrame(rows)
    df["metric_label"] = df["metric"].map(METRIC_LABEL)
    df["source"] = "inferred"
    ny = pd.DataFrame([{"scenario": "nyseg_forecast", "year": y, "metric": "as_stated", "value": v,
                        "low": None, "high": None, "numerator": None, "denominator": None,
                        "metric_label": "NYSEG planning forecast, denominator unstated", "source": "E"}
                       for y, v in NYSEG_EV.items()])
    return pd.concat([df, ny], ignore_index=True)


def growth_ratios(m: pd.DataFrame) -> pd.DataFrame:
    """2030 -> 2040 growth ratio. Denominator-free: a definitional relabelling cannot change it."""
    w = m[m["year"].isin([2030, 2040])].pivot_table(index=["scenario", "metric"], columns="year", values="value")
    w = w.dropna().reset_index()
    w["ratio_2030_2040"] = w[2040] / w[2030]
    w = w.rename(columns={2030: "value_2030", 2040: "value_2040"})
    w["metric_label"] = w["metric"].map(METRIC_LABEL).fillna("NYSEG planning forecast, denominator unstated")
    return w.sort_values(["metric", "scenario"]).reset_index(drop=True)


def indicative_load(m: pd.DataFrame) -> pd.DataFrame:
    """Scale modelled county load to the NYSEG EV count. Interpolation of existing runs, not a new run."""
    ld = pd.read_csv(TABLES / "load_scenarios_annual.csv")
    ld = ld[(ld["ownership_scenario"] == "trend") & (ld["charging_scenario"] == "base")].set_index("year")
    g = pd.read_csv(TABLES / "growth_projection_tompkins.csv")
    g = g[g["scenario"] == "trend"].set_index("year")
    rows = []
    for basis, col in [("all plug-in (BEV + PHEV)", "EV_p50"), ("BEV only", "BEV_p50")]:
        for y, share in NYSEG_EV.items():
            implied = share * FLEET_LDV
            modelled = float(g.loc[y, col])
            f = implied / modelled
            rows.append({
                "year": y, "nyseg_share": share, "basis": basis,
                "implied_ev_count": round(implied), "trend_ev_count": round(modelled), "scale_factor": round(f, 4),
                "indicative_annual_gwh": round(float(ld.loc[y, "annual_mwh_total"]) * f / 1000.0, 1),
                "indicative_peak_mw": round(float(ld.loc[y, "peak_mw_total"]) * f, 1),
                "reference_annual_gwh": round(float(ld.loc[y, "annual_mwh_total"]) / 1000.0, 1),
                "reference_peak_mw": round(float(ld.loc[y, "peak_mw_total"]), 1),
            })
    out = pd.DataFrame(rows)
    out["note"] = "linear scaling of the trend/base run by EV count; not a scenario run at NYSEG levels"
    return out


def main() -> None:
    ensure(TABLES)
    m = adoption_metrics()
    m.round(6).to_csv(TABLES / "avangrid_ev_adoption_metrics.csv", index=False)
    r = growth_ratios(m)
    r.round(6).to_csv(TABLES / "avangrid_ev_growth_ratios.csv", index=False)
    il = indicative_load(m)
    il.to_csv(TABLES / "avangrid_ev_indicative_load.csv", index=False)

    print("Adoption metrics at the NYSEG comparison years (median):")
    piv = m[m["year"].isin([2030, 2040]) & (m["scenario"] != "nyseg_forecast")]
    print(piv.pivot_table(index=["metric", "scenario"], columns="year", values="value").round(4).to_string())
    print(f"\nNYSEG stated: 2030 {NYSEG_EV[2030]:.4f}, 2040 {NYSEG_EV[2040]:.4f}, "
          f"ratio {NYSEG_EV[2040] / NYSEG_EV[2030]:.2f}x")
    print("\nGrowth ratios 2030->2040 (denominator-free):")
    print(r[["metric", "scenario", "value_2030", "value_2040", "ratio_2030_2040"]].round(4).to_string(index=False))
    print("\nIndicative county load at the NYSEG levels (scaled, not run):")
    print(il.to_string(index=False))


if __name__ == "__main__":
    main()
