# UBEM interface — hourly EV charging load outputs

Last updated: 2026-09-14. For the EnergyAtlas/RC urban building energy model team and utility users.

## Entities and keys
| Entity | Key | Source | Notes |
|---|---|---|---|
| Dwelling unit (DU) | `du_id` (int) | `data/processed/synthetic/dwelling_units.parquet` | Synthetic household placed on a residential tax parcel; attributes: structure, tenure, income band, vehicles, workers. Not a real address-level household. |
| Parcel | `parcel` = NYS `SWIS_SBL_ID` | NYS ITS Tax Parcels 2025 | Building proxy (footprints not used). Join to buildings/RC zones by parcel. |
| Block group | `bg` = 12-digit GEOID (TIGER 2024) | Census | Aggregation / mapping. |
| Charging site | `site_id` (`afdc_<id>`, `chargeready_<id>`, `parcel_<SWIS_SBL_ID>`) | AFDC, Charge Ready NY, parcels | Public L2, DCFC, workplace (listed and unlisted), fleet depots. |

## Time and units
- 8,760 hourly values for a calendar year `year` (2026–2050), hour-beginning index 0 = Jan 1 00:00–01:00,
  **local standard time** (no DST shift), weekday-aligned to that calendar year; weather = TMYx 2011–2025 Ithaca.
- Values are **kWh delivered from the grid in the hour** (numerically equal to average kW over the hour), at the meter
  (charging losses included).

## Files
| File | Content | Tracked |
|---|---|---|
| `data/processed/model/du_ev_2026.parquet` | expected EVs per DU (central `E_ev`, `E_bev`, `E_phev`), probability of ≥1 EV across realizations, structural alternatives | yes |
| `data/processed/model/du_ev_by_year_trend.parquet` | expected EVs per DU for 2026/2030/2035/2040/2045/2050 (trend ownership) | yes |
| `data/processed/model/fleet_ev_sites_2026.csv` | expected fleet/organizational EVs per non-residential parcel | yes |
| `data/processed/load/county_hourly_{year}_{own}_{chg}.parquet` | county hourly kWh by location (home, work, public_l2, dcfc, fleet, passerby) | trend only |
| `data/processed/load/bg_home_hourly_{year}_trend_base.parquet` | expected residential charging per BG (columns = BG GEOID) | yes |
| `data/processed/load/parcel_summary_{2026,2035}_trend_base.csv` | expected EVs, p50/p90 annual peak hourly kW from 30 realizations, probability of any EV | yes |
| `data/processed/load/site_summary_{year}_trend_base.csv` | site annual kWh, peak kW, ports, kWh/port-day | yes |
| `data/processed/load/ubem_export_sample_{2026,2035}.parquet` | 20 example parcels × 8,760 h | yes |
| `data/interim/load/class_profiles_{year}_{chg}.npz` | profile basis Π (dwelling class × drivetrain × location) | no (regenerate) |
| `data/interim/charging_library/{year}/home_kw.npy` | per-EV-year home load realizations (library) | no (regenerate) |

Scenario codes: ownership `own` ∈ {trend, slow, stall, policy}; charging `chg` ∈ {base, access+, managed}.

## Expected hourly load for any DU set, parcel or BG
\[
L_e(t) = \sum_{d \in e} \Big( E^{\mathrm{BEV}}_d(y)\,\Pi_{k(d),\mathrm{BEV}}(t) + E^{\mathrm{PHEV}}_d(y)\,\Pi_{k(d),\mathrm{PHEV}}(t) \Big)
\]
with dwelling class \(k\) = structure group × tenure × workers. Generate with

```bash
python -m src.model.export_ubem --year 2035 --level parcel --own trend --chg managed
```

(writes `data/interim/ubem_export/ev_home_parcel_2035_trend_managed.parquet`; `--level du|parcel|bg`).

## Stochastic realizations (peaks, diversity)
Expected profiles are smooth and understate single-building peaks. For building-level peak or coincidence studies,
use realizations: EV counts per DU ~ Poisson(`E_ev`) capped by vehicles, one library EV-year per EV
(`src.model.load_assembly.assemble(..., realizations=R)`). Parcel p50/p90 peaks are provided for 2026 and 2035.

## Caveats for model users
- Placement of EVs below ZIP code is **inferred** (ensemble of an ecological model and individual-level evidence);
  observed only as ZIP totals. Use block-group or larger aggregates for validation-sensitive analyses.
- Non-residential sites: public/DCFC loads use AFDC port shares; unlisted workplace charging is spread over large
  non-residential parcels by floor area; fleet depot locations are unknown (floor-area placement).
- Students in group quarters (dorms) are not households; their vehicles registered in Tompkins are in ZIP totals.
