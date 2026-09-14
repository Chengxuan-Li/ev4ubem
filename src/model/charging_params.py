r"""Time-varying charging-model parameters by year (2026-2050) and charging scenario, with sources.

Each parameter has a 2026 value (evidence-based) and a 2035/2050 target per scenario; values are linearly interpolated
between anchor years. Scenario axes (independent of the ownership growth scenario):
  base      – modest efficiency gains, rising home L2 share, gradual MF access and workplace growth, no managed charging
  access+   – faster multifamily/renter home-charging access and workplace charging buildout
  managed   – base + growing share of home L2 sessions shifted to the utility off-peak window (TOU/managed)
Outputs: data/processed/charging/parameters_by_year.csv (tracked) and a parameter-source table.

Energy per mile (at the wheel -> at the plug):
  kWh/mi_plug(T) = e_wheel(y) · m(T) / η_charge(level)
  m(T) = 1 + 0.0110·max(0, 20 − T_daily) + 0.0060·max(0, T_daily − 25)    (T in °C; cold penalty ≈ +30 % at −7 °C)
  (assumption informed by published fleet telematics studies of range loss vs temperature; stated as assumption A3/A9)
  η_charge: L1 0.83, L2 0.90, DCFC 0.92
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.paths import PROCESSED, ensure

YEARS = list(range(2026, 2051))

# parameter: (unit, source/evidence, {scenario: {year: value}})
P = {
    "e_wheel_bev_kwh_per_mi": ("kWh/mi", "EPA-label-like fleet mix incl. SUVs/pickups (assumption); -0.7%/yr improvement to 2035",
                               {"base": {2026: 0.31, 2035: 0.29, 2050: 0.27}}),
    "e_wheel_phev_kwh_per_mi": ("kWh/mi", "PHEV electric-mode consumption (assumption)", {"base": {2026: 0.34, 2035: 0.32, 2050: 0.30}}),
    "annual_miles_bev": ("mi/yr", "Drive Clean 2024 ownership survey mean 10,670 (B, self-report); held constant",
                         {"base": {2026: 10670, 2050: 10670}}),
    "annual_miles_phev": ("mi/yr", "Drive Clean 2024 ownership survey mean 10,082 (B)", {"base": {2026: 10082, 2050: 10082}}),
    "annual_miles_lognorm_sigma": ("-", "dispersion of annual miles across vehicles (assumption; NHTS ANNMILES dispersion)",
                                   {"base": {2026: 0.55, 2050: 0.55}}),
    "phev_electric_range_mi": ("mi", "RAV4 Prime ~42, Prius Prime ~39-44, Volt 53, Pacifica 32 (fleet mix, assumption)",
                               {"base": {2026: 35, 2035: 45, 2050: 50}}),
    "home_access_sf_own": ("prob", "Drive Clean: 89% BEV / 81% PHEV charge at home; detached owners assumed higher (0.95)",
                           {"base": {2026: 0.95, 2050: 0.97}}),
    "home_access_sf_rent": ("prob", "assumption: driveway outlets but landlord permission limits", {"base": {2026: 0.75, 2035: 0.80, 2050: 0.85},
                                                                                               "access+": {2026: 0.75, 2035: 0.88, 2050: 0.95}}),
    "home_access_mf2_4": ("prob", "SMBS upstate: 84% of MF units have off-street parking; outlet access assumed 0.55",
                          {"base": {2026: 0.55, 2035: 0.62, 2050: 0.70}, "access+": {2026: 0.55, 2035: 0.75, 2050: 0.90}}),
    "home_access_mf5p": ("prob", "SMBS upstate: 5.7% of MF buildings with EV charging (2022-23); EV owners self-select -> 0.35",
                         {"base": {2026: 0.35, 2035: 0.45, 2050: 0.60}, "access+": {2026: 0.35, 2035: 0.65, 2050: 0.85}}),
    "home_access_mobile": ("prob", "assumption", {"base": {2026: 0.70, 2050: 0.80}}),
    "home_l2_share_bev": ("prob", "Drive Clean 2024 actual: 58% L2 station + 27% 240V outlet -> 0.80 L2-capable (B)",
                          {"base": {2026: 0.80, 2035: 0.88, 2050: 0.92}}),
    "home_l2_share_phev": ("prob", "Drive Clean 2024 actual: 24% L2 station, 68% 120V (B)", {"base": {2026: 0.28, 2035: 0.40, 2050: 0.50}}),
    "l1_kw": ("kW", "120 V 12 A", {"base": {2026: 1.4, 2050: 1.4}}),
    "l2_kw_bev": ("kW", "min(EVSE 7.2-9.6, onboard charger 7.2-11) (assumption)", {"base": {2026: 7.2, 2035: 8.0, 2050: 8.5}}),
    "l2_kw_phev": ("kW", "PHEV onboard chargers 3.3-6.6 kW", {"base": {2026: 3.6, 2035: 5.0, 2050: 6.0}}),
    "freq_daily_bev": ("prob", "Drive Clean 2024 BEV home charging frequency: daily 34%", {"base": {2026: 0.34, 2050: 0.30}}),
    "freq_few_week_bev": ("prob", "few times/week 28%", {"base": {2026: 0.28, 2050: 0.30}}),
    "freq_weekly_bev": ("prob", "weekly 20%", {"base": {2026: 0.20, 2050: 0.22}}),
    "freq_rare_bev": ("prob", "few/month or less 7% (never 11% handled via access)", {"base": {2026: 0.07, 2050: 0.08}}),
    "freq_daily_phev": ("prob", "Drive Clean 2024 PHEV: daily 51%", {"base": {2026: 0.51, 2050: 0.51}}),
    "freq_few_week_phev": ("prob", "few/week 15%", {"base": {2026: 0.15, 2050: 0.15}}),
    "freq_weekly_phev": ("prob", "weekly 4.4%", {"base": {2026: 0.044, 2050: 0.044}}),
    "freq_rare_phev": ("prob", "few/month or less 10%", {"base": {2026: 0.10, 2050: 0.10}}),
    "workplace_access_per_worker": ("prob", "Drive Clean 2024: 23% of working respondents have access (B)",
                                    {"base": {2026: 0.23, 2035: 0.32, 2050: 0.40}, "access+": {2026: 0.23, 2035: 0.45, 2050: 0.60}}),
    "workplace_use_given_access": ("prob", "Drive Clean 2024: ~2/3 of those with access use it", {"base": {2026: 0.65, 2050: 0.65}}),
    "public_l2_energy_share_no_home": ("share", "energy share from public L2 for EVs without home access (rest DCFC) (assumption)",
                                       {"base": {2026: 0.55, 2050: 0.45}}),
    "public_topup_share_with_home": ("share", "non-home top-up energy share for EVs with home access (Drive Clean: 73% BEV use public at all) (assumption)",
                                     {"base": {2026: 0.08, 2050: 0.06}}),
    "dcfc_share_of_public": ("share", "DCFC share of public energy for home-access EVs (assumption)", {"base": {2026: 0.45, 2050: 0.55}}),
    "managed_share_home_l2": ("share", "share of home L2 sessions delayed to off-peak start (23:00); NYSEG managed-charging programs",
                              {"base": {2026: 0.0, 2050: 0.0}, "managed": {2026: 0.05, 2035: 0.35, 2050: 0.60}}),
    "passerby_dcfc_share": ("share", "share of DCFC energy from non-resident vehicles (visitors, through traffic) (assumption)",
                            {"base": {2026: 0.25, 2050: 0.25}}),
    "fleet_miles_per_year": ("mi/yr", "light commercial fleet vehicles (assumption)", {"base": {2026: 14000, 2050: 14000}}),
    "evs_per_public_port": ("EVs/port", "Tompkins 2026: 3,233 EVs / 277 public L2+DCFC ports (A); held ~constant", {"base": {2026: 11.7, 2050: 15.0}}),
}


def value(param: str, scenario: str, year: int) -> float:
    spec = P[param][2]
    anchors = spec.get(scenario, spec["base"])
    ys = sorted(anchors)
    return float(np.interp(year, ys, [anchors[k] for k in ys]))


def table() -> pd.DataFrame:
    rows = []
    for sc in ["base", "access+", "managed"]:
        for y in YEARS:
            rows.append({"charging_scenario": sc, "year": y, **{k: value(k, sc, y) for k in P}})
    return pd.DataFrame(rows)


def main() -> None:
    out = PROCESSED / "charging"
    ensure(out)
    table().round(5).to_csv(out / "parameters_by_year.csv", index=False)
    pd.DataFrame([{"parameter": k, "unit": v[0], "source_or_assumption": v[1],
                   "anchors": "; ".join(f"{sc}: " + ", ".join(f"{y}={x}" for y, x in a.items()) for sc, a in v[2].items())}
                  for k, v in P.items()]).to_csv(out / "parameter_sources.csv", index=False)
    print(table().query("year in [2026, 2035, 2050]").T.head(12))


if __name__ == "__main__":
    main()
