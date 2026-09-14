# Data source inventory

Last updated: 2026-09-14 (statuses revised after first analyses). Availability classes follow the brief:
**ACQ** = publicly available and acquired · **PUB** = public but not (yet) acquired/processed ·
**SUM** = public summary only / raw data unavailable · **NP** = nonpublic or restricted.
Evidence classes: A local observation · B New York observation · C national/nonlocal observation ·
D derived/processed observation · E model output · F qualitative/contextual.

Acquisition scripts live in `src/acquisition/`; provenance (URL/query, retrieval time, sha256, rows) in
`metadata/manifests/`. Detailed reading notes for reports are in `docs/source_notes/`.

## 1. EV ownership / stock

| Source | ID / URL | Avail. | Evid. | Resolution / period | Script | Notes |
|---|---|---|---|---|---|---|
| NYS DMV Vehicle, Snowmobile & Boat Registrations | data.ny.gov `w4pv-hbkt` | ACQ | A/B | Row-level, ZIP + county, current unexpired snapshot (rows updated 2026-09-02) | `ny_open_data.py`, `dmv_full_snapshot.py` | Full VINs, no model name. `fuel_type=ELECTRIC` ≈ BEV only; PHEVs coded GAS → VIN decoding required (decision 0002). One row per registered vehicle (no duplicate VINs in Tompkins EV rows). Moving snapshot: no history in this endpoint. |
| DMV Registration Transactions (two-year window) | data.ny.gov `s2dd-yksa` | ACQ | A/B | Row-level transactions (ORIGINAL, RENEWAL, …) 2024-08 → 2026-09 effective dates, residence county, ZIP | `ny_open_data.py` | Flows (new registrations), not stock. Full VINs → can be decoded. |
| NYSERDA EValuateNY v11 archive | nyserda.ny.gov `EValuateNY_v11_pt{1,2}.zip` | ACQ | D (from DMV) | ZIP × DMV snapshot, monthly 2017-07 → 2023-04 (annual 2011–2016); VIN-decoded drivetrain for all vehicles | `nyserda_evaluateny.py`, `processing/evaluateny.py` | **Stale**: last snapshot 2023-04-02. Contains all-vehicle denominators, EV first appearances, a VIN_Key → drivetrain table, ChargePoint ZIP-month usage (to 2022-12), census inputs (2021 refresh). |
| NYSERDA `ny_ev_registrations.csv` | nyserda.ny.gov ChargeNY | ACQ | D | EV registration events (Original/Renewal) by ZIP, VIN prefix; 2011-01 → 2022-03 | `nyserda_evaluateny.py` | Labelled "regularly updated" but ends 2022-03. |
| NYSERDA Drive Clean Rebate applications | data.ny.gov `thd2-fu8y` | ACQ | B/A | Row-level rebates (county, ZIP, make/model, BEV/PHEV, purchase/lease), 2017-03 → 2026-07-31 | `ny_open_data.py`, `processing/drive_clean.py` | New-vehicle rebate flow only; not stock. Tompkins: 2,017 rebates. |
| Electric Vehicles per County (DMV view) | data.ny.gov `uu25-czyc` | PUB (redundant) | A/B | County × fuel_type | — | Filtered view of `w4pv-hbkt`; same PHEV limitation. |
| NHTSA vPIC VIN decoder | vpic.nhtsa.dot.gov API | ACQ | D | Per VIN pattern | `vpic.py` | Used to classify MY2023+ patterns absent from EValuateNY. Wildcard partial VINs decode. |
| Tompkins County EV plan (2017), GHG inventories (2019, 2024) | county PDFs (see 24-06 note) | SUM | F/D | County totals (e.g., 644 EVs end-2019) | — | Historical context only. |

## 2. Population, housing, travel

| Source | ID / URL | Avail. | Evid. | Resolution | Script | Notes |
|---|---|---|---|---|---|---|
| ACS 2020–2024 5-year | www2.census.gov table-based summary files | ACQ | A/B (survey est.) | State, county, cousub, place, tract, **block group**, ZCTA | `census.py`, `processing/acs_features.py` | Census API now needs a key → summary files used (decision 0001). 24 tables incl. tenure × units, tenure × vehicles, income, education, commute. Some tables tract-only. |
| TIGER/Line 2024 tracts, BGs, county subdivisions, places; CB 2020 ZCTAs; 2020 ZCTA relationship files | www2.census.gov | ACQ | — | Geometries | `census.py`, `processing/geography.py` | ZCTA→county population shares via tract apportionment. |
| NYS ITS Tax Parcels (2025 roll) | gisservices.its.ny.gov NYS_Tax_Parcels_Public | ACQ | A | 35,369 Tompkins parcels with property class, year built, living area, GFA | `nys_parcels.py` | Owner/mail fields excluded. Unit counts not given for apartments (GFA only). |
| NHTS 2022 (v2) public use | nhts.ornl.gov | ACQ | C | Household/person/vehicle/trip microdata; census division × MSA size; **no state** | `nhts.py`, `analysis/nhts_*.py` | 7,893 HH, 14,684 vehicles, only 186 BEV + 80 PHEV. Diary miles undercount (non-reporting members). |
| NYSERDA Statewide Multifamily Building Study 2022 (occupant/general survey) | data.ny.gov `gjv3-iq86`, `gfhm-wz4s` | PUB | B | Survey microdata | — | Lead for MUD parking/charging access; not yet examined. |

## 3. Charging infrastructure

| Source | ID / URL | Avail. | Evid. | Notes |
|---|---|---|---|---|
| AFDC station locator API | developer.nlr.gov `alt-fuel-stations/v1` (DEMO_KEY) | ACQ | A | NY ELEC, all statuses (6,061 stations). Station ≠ port. `developer.nrel.gov` no longer resolves. |
| AFDC NY mirror | data.ny.gov `bpkx-gmh7` / `7rrd-248n` | ACQ | A | Cross-check: Tompkins 99 stations vs 105 in API (6 newer IDs only in API). |
| AFDC historical station counts | afdc.energy.gov/data_download (historical format) | PUB | A | Not yet acquired; open_date in current data used for growth (survivorship bias). |
| Charge Ready NY program sites | data.ny.gov `9wxk-hakb` | ACQ | A/B | Funded L2 ports with location type (Public / Workplace / MUD). 12 Tompkins-labelled projects. |
| EValuateNY "Charging Locations/Ports" | EValuateNY resources.xlsx | ACQ | D | AFDC-derived snapshot (2023). |

## 4. Charging behaviour

| Source | Avail. | Evid. | Role | Notes |
|---|---|---|---|---|
| NYSERDA 22-03 Cost & Usage Trends (1,288 stations, 434,578 sessions, 2012–2020) | SUM | B | NY public/workplace/MUD L2 utilisation, duration, hourly occupancy shapes | No session data public. Fig. 18 weekday anchors transcribed to `data/processed/nyserda_2203/` (figure-read ±1–2 pp) and used as the NY shape check and workplace shape. Note: `source_notes/nyserda_22-03_charging_usage.md`. |
| NYSERDA EVSE Use Reports 2013–2017 | SUM | B | Older NY L2 utilisation | PDFs only. |
| EValuateNY ChargePoint "Charging Use" by ZIP-month (2010-12 → 2022-12) | ACQ, analysed | B/A | Monthly kWh, sessions, active ports by ZIP (incl. 14850, 13053, 13045) | Aggregated; ChargePoint network only (~6 ports in 14850). `analysis/chargepoint_local_use.py`. |
| Drive Clean Ownership Survey 2023/2024, Adoption Survey 2024/2025 | SUM | B (self-report, rebate recipients) | Home/work/public charging frequency, L1/L2 at home, annual miles | No microdata; strong selection (new-car buyers, 85% owners). Note: `source_notes/nyserda_drive_clean_surveys.md`. |
| Con Edison SmartCharge NY evaluation; NYSEG/RG&E managed charging plans; NYSEG–Cornell OptimizEV pilot | SUM / NP | B | Average charging kW (BEV ~4.0, PHEV ~1.3), pilot summaries | OptimizEV minute data is nonpublic. |
| Norway residential charging (Zenodo 13896176) | ACQ | C | Home charging sessions (apartment garages, cold climate) | CC-BY-4.0. |
| City of Boulder public charging sessions 2018–2023 | ACQ | C | Public L2 sessions | CC0. |
| Workplace charging, one US employer 2014–2015 (Harvard Dataverse QF1PMO) | ACQ | C | Workplace sessions — **timing rejected** (weekday peak 12:00 vs NY 9–10 am, r = 0.47); energy/duration still usable | CC0. |
| Dundee public charge points 2021–2025; Palo Alto 2011–2020 | ACQ | C | Public L2/DCFC sessions | OGL / open. |
| Caltech ACN-Data; EV WATTS (Livewire); Pecan Street Dataport | NP (account/login) | C | — | Not used (no account creation). |
| ElaadNL | SUM | C | Aggregated distributions only | — |
| UK DfT Electric Chargepoint Analysis 2017 domestics | SUM (main raw file not reachable) | C | Summary tables (median 7.5 kWh/event) | — |

## 5. Model outputs / benchmarks (class E)

| Source | Avail. | Notes |
|---|---|---|
| NREL TEMPO 2022 via dsgrid (`s3://nrel-pds-dsgrid/tempo/tempo-2022/v1.0.0/`) | ACQ (Tompkins subset) | County × hourly × 720 household/vehicle segments, L1L2 vs DCFC, 3 scenarios, MY2024–2050, weather 2012. Assumes immediate charging after trips. `nrel_tempo.py`. |
| NREL ResStock 2025 release 1 EV upgrades (OEDI) | PUB | Per-building EV charging for home charging shape; 173 Tompkins samples (2 with EVs in baseline). |
| NREL Electrification Futures Study load profiles | PUB (state-level, 300 MB zips) | `data.nlr.gov/submissions/126`. |
| NLR forward-looking managed-charging county profiles (announced 2025) | not found | Watch OEDI. |
