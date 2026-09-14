# Methodology, definitions, and pipeline

Last updated: 2026-09-14. Companion to `docs/data_sources.md` (what) and `docs/findings.md` (results).

## 1. Pipeline (run from repository root)

```bash
# acquisition (git-ignored outputs in data/raw/, provenance in metadata/manifests/)
python -m src.acquisition.nyserda_evaluateny      # ~840 MB; then unzip both archives into data/raw/nyserda/evaluateny_v11/
python -m src.acquisition.ny_open_data            # DMV extracts, transactions, rebates, Charge Ready, AFDC mirror
python -m src.acquisition.dmv_full_snapshot       # ~2.5 GB stream -> 68 MB compact parquet
python -m src.acquisition.census                  # ACS 2020-2024 summary files (NY subset) + TIGER
python -m src.acquisition.nhts
python -m src.acquisition.nys_parcels
python -m src.acquisition.afdc                    # developer.nlr.gov, DEMO_KEY or NLR_API_KEY
python -m src.acquisition.vpic [--statewide]      # resumable; ~20 min Tompkins, longer statewide
python -m src.acquisition.charging_sessions
python -m src.acquisition.nrel_tempo              # streams ~0.5 GB from public S3, keeps Tompkins subset
# processing (tracked compact outputs in data/processed/)
python -m src.processing.evaluateny
python -m src.processing.geography
python -m src.processing.acs_features
python -m src.processing.infrastructure
python -m src.processing.drive_clean
python -m src.processing.dmv_ev_stock
# analysis (results/tables, results/figures, results/maps)
python -m src.analysis.ownership_trends
python -m src.analysis.zip_ev_penetration
python -m src.analysis.nhts_vehicle_days
python -m src.analysis.nhts_ev_propensity
python -m src.analysis.subzip_allocation
python -m src.analysis.charging_sessions
python -m src.analysis.diversity
python -m src.analysis.hourly_load_scenarios
```

Unzip step (not scripted because of archive size; any unzip tool):
`unzip EValuateNY_v11_pt1.zip -d evaluateny_v11 && unzip EValuateNY_v11_pt2.zip -d evaluateny_v11`.

DMV, AFDC, Drive Clean and transaction endpoints are **moving snapshots**. Re-running acquisition later
yields newer data; manifests record `source_rows_updated_utc` so results can be tied to a snapshot.
Results in `docs/findings.md` use the DMV snapshot with rows updated 2026-09-02 (retrieved 2026-09-14).

## 2. Key definitions

| Term | Definition used |
|---|---|
| Registered vehicle | One row in DMV `w4pv-hbkt` with `record_type = VEH` (unexpired registration at snapshot). Tompkins EV VINs are unique (no duplicate renewals in the snapshot). |
| Tompkins resident vehicle | DMV `county == 'TOMPKINS'` (registration address county). ZIP-based totals differ because several ZIPs straddle the county line (see `zcta_county_popshare_ny.csv`). |
| EV | BEV + PHEV. FCVs and HEVs excluded. Low-speed vehicles/motorcycles appear as BEVs in VIN decoding; tables keep `class_group`/`is_ldv` to filter. |
| Drivetrain | VIN pattern decoding (decision 0002): NHTSA vPIC `ElectrificationLevel` (conclusive) else EValuateNY VIN_Key lookup; DMV `fuel_type` used only as a diagnostic. |
| LDV | `body_type` in {SUBN, 4DSD, 2DSD, PICK, VAN, CONV, SEDN, H/WH, WAGN, 3DSD, 5DSD, HRSE, LIMO, UTIL} and unladen weight ≤ 8,500 lb (or missing). |
| Station / port | AFDC station = location record; ports = L1 + L2 EVSE ports + DC fast ports (not connectors). |
| Households | ACS occupied housing units (B25003_001). |
| ZIP vs ZCTA | DMV/EValuateNY ZIP codes are matched to 2020 ZCTAs by code; PO-box ZIPs (14851, 14852) have no ZCTA and are folded into 14850 where spatial units are needed. |
| Hour | Local prevailing time (America/New_York) unless noted; TEMPO EST hours converted. Session datasets are in their own local time. |

## 3. Geography
- County share of ZIP populations: ACS tract population apportioned to ZCTA parts by land area (2020 relationship file).
- Spatial joins: parcels → representative point → BG/ZCTA in EPSG:4326 after projection to EPSG:32618 for point generation; maps plotted in EPSG:32618 (UTM 18N).
- Counties for AFDC stations by point-in-polygon against TIGER county subdivisions (not ZIP/city labels).

## 4. Statistical approach
- ZIP-level adoption (ecological): negative-binomial GLM with `log(households)` offset; standardized predictors; VIFs; 10-fold
  **county-grouped** CV; Tompkins held out entirely. Gradient boosting (Poisson loss) as a predictive benchmark only.
  Interpretation limited to area-level association; no causal or individual-level inference.
- Household propensity: NHTS 2022 weighted shares with household bootstrap intervals and a weighted logit (n = 5,748 HH with
  complete covariates, 219 plug-in households). Used only as *relative* priors.
- Sub-ZIP allocation: deterministic proportional allocation under four explicit weighting scenarios; spread across scenarios
  is reported as structural uncertainty. ZIP totals are preserved by construction (not validation).
- Charging sessions: uniform cleaning rules; imputed charging durations where not observed (documented per dataset); hourly
  energy under immediate charging.

## 5. Assumptions register (current)

| ID | Assumption | Value / range | Basis | Validated? |
|---|---|---|---|---|
| A1 | BEV annual miles | 10,670 (±20 %) | Drive Clean 2024 ownership survey (self-report, rebate recipients) | No (NHTS diary lower, NHTS self-report higher) |
| A2 | PHEV annual miles; electric utility factor | 10,082; eUF 0.45 (0.30–0.60) | Drive Clean 2024; eUF assumed | No |
| A3 | Vehicle efficiency at wheel/plug | BEV 0.32 kWh/mi, PHEV 0.35 kWh/mi, charging efficiency 0.90 | typical values | No |
| A4 | Energy by charging location | home 0.80 / work 0.07 / public L2 0.08 / DCFC 0.05 (sensitivities 0.90 and 0.65 home) | Drive Clean frequencies (home access high, 23 % workplace access) + national studies | No |
| A5 | Home charging timing | Norway residential plug-in times, immediate charging at 3.6 kW (7.2 kW sensitivity) | class C | Shape only vs NYSERDA/TEMPO |
| A6 | Workplace timing | Midwest employer sessions at 3.3 kW | class C; NYSERDA 22-03 workplace occupancy peak 9–10 am (class B) | Partially (timing) |
| A7 | Sub-ZIP propensity by home type / income | NHTS relative propensities | class C | No (not observable below ZIP) |
| A8 | Seasonality | mean of Boulder L2 and Norway monthly daily-energy index | class C | No local data |
