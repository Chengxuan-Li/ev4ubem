# AFDC historical charging-station data (NY / Tompkins): endpoints, access, limitations

Checked 2026-09-14. Acquisition: `python -m src.acquisition.afdc_historical` (raw data goes to `data/raw/afdc_historical/`, manifest to
`metadata/manifests/afdc_historical.json`). Analysis: `python -m src.analysis.infrastructure_history`.

## Why
`data/processed/infrastructure/tompkins_ports_by_open_year.csv` builds growth from the `open_date` of stations
that are **still open** in the 2026 API snapshot. That curve leaves out stations that closed, were removed or were
re-keyed, and it assigns today's port counts to the original opening year. It is survivorship-biased. The sources below
reconstruct what was actually published on past dates.

## Endpoints tested

| # | Endpoint | Access | Result | Used |
|---|---|---|---|---|
| 1 | `https://afdc.energy.gov/data_download` → "Alternative fuel stations", timeframe "Past – historical data … starting in 2014" (Single day / Date range for specific stations) | HTML form that requires **first name, last name, email** (`download[registration][user]…`) and accepting terms. It registers the user for an NLR key. | Not submitted (registration is out of scope under project rules) | No |
| 2 | `https://afdc.energy.gov/data_download/historical_stations_format` | Public docs page | Defines the two download types. The date-range type adds `historical_change_at` (timestamp) and `historical_published` (boolean) to the common station fields. | Schema reference |
| 3 | `https://developer.nlr.gov/api/alt-fuel-stations/v0/historical-date/{YYYY-MM-DD}.json` (also `.csv`, `/ev-charging-units.csv`, `/nearest.csv`) | **Undocumented**. Found in the Station Locator widget bundle `https://widgets.nlr.gov/afdc/station-locator/assets/main-*.js` (used by the "Historical Date" filter). A key is required (no key gives 403 `API_KEY_MISSING`). **DEMO_KEY works.** | 200. Returns full v1-style station records **as published on that date**, with the same filters as v1 (`state`, `fuel_type`, `access`, `status`, `limit=all`). The response also carries `warnings` (PARTIAL_HISTORICAL_DATA for fields introduced later: maximum_vehicle_class 2022-01, power_kw and funding_sources 2024-07, J3271 2025-07). The earliest date allowed by the UI is 2014-01-20. | **Yes**: NY ELEC at 2014–2025-12-31 and 2026-09-01 (13 calls) |
| 4 | `https://developer.nlr.gov/api/alt-fuel-stations/v0/historical-fuel-station-counts.json` / `.csv` (params `frequency`, `start_date`, `end_date`, `fuel_type`, `ev_charging_level`, `access`, `status`, `country`) | Key required; DEMO_KEY accepted | 422 `Invalid 'state' parameter: is not allowed`, so it is national or country-level only | No (NY is not available) |
| 5 | `https://afdc.energy.gov/files/docs/historical-station-counts.xlsx` | Static file, no key | One sheet per year 2007–2025 with late-December counts by state and fuel. Covers public and private non-residential stations, with no access split. | **Yes** (NY 2007–2025) |
| 6 | `https://afdc.energy.gov/stations/states?count={public,private,total}&date=YYYY-MM-DD` | Server-rendered HTML, no key. The date must be 2014-01-20 or later. Temporarily unavailable stations are excluded unless `include_temporarily_unavailable=true`. | 200. State table; the Electric cell reads `stations \| ports` over `L1 \| L2 \| DCFC` | **Yes** (NY public/private/total at the same 13 dates) |
| 7 | `https://afdc.energy.gov/stations/trends` (Analyze Trends charts) | JavaScript front end to #4 | National or country-level | No |
| 8 | Quarterly *EV Charging Infrastructure Trends* PDFs (`afdc.energy.gov/fuels/electricity-infrastructure-trends`, 2020Q1–2024Q2) | Public PDFs | National, with some state tables | Not used (superseded by #3 and #6) |
| 9 | `https://api.github.com/search/code?...repo:NREL/developer.nrel.gov` | Requires GitHub authentication | Not searched. Raw docs (`all.html.md.erb`) contain no `historical` parameter. | No |
| 10 | Internet Archive CDX: `data.ny.gov/api/views/bpkx-gmh7/rows.csv` | Public | 11 captures (2022-12-23, 2023-11-17, 2024-10/12, 2025-02/03, 2026-03/04). These are third-party archives of the NY Open Data AFDC mirror. | Not needed (#3 is official). Kept as a fallback. |
| 11 | EValuateNY v11 `resources.xlsx` (local): sheets `Charging Locations` (3,826 NY stations, `Updated At` ≤ 2023-04-14), `Charging Ports`, `Station Census Blocks Archive` (equipment_id→block only, no dates), `Charging Use` (ChargePoint only, monthly active station/port counts by ZIP 2010-12…2022-12) | Local | A 2023-04 AFDC snapshot. 10 of its 46 Tompkins station IDs no longer appear in the 2026 API (NY: 1,147 of 3,826), which is direct evidence of attrition. `Charging Use` covers ChargePoint only (Tompkins ZIPs: 3 stations / 6 ports throughout), so it is not usable as a total. | Cross-check only |

The NLR domain moved from `developer.nrel.gov`, which was retired on 2026-05-29, to `developer.nlr.gov`.

## Access and rate limits
- On `v0/historical-date`, DEMO_KEY returned `X-Ratelimit-Limit: 10` with a countdown per call, which looks like a rolling hourly window.
  The acquisition script skips files already downloaded, sleeps for 20 min when the limit is hit, and supports `--no-wait`. `NLR_API_KEY` overrides DEMO_KEY.
  The key is never written to the manifest.
- A full NY ELEC snapshot is about 1.3 MB (2014) and grows with station count. One call per date is enough (`limit=all`).

## Schema (v0 historical-date = v1 All Stations fields)
These are the fields used here: `id`, `status_code` (E open / P planned / T temporarily unavailable), `access_code` (public/private),
`ev_level1_evse_num`, `ev_level2_evse_num`, `ev_dc_fast_num` (ports), `ev_charging_units[]` (port groups by level with connectors),
`latitude`, `longitude`, `geocode_status`, `open_date`, `updated_at`, `date_last_confirmed`, `ev_network`, `facility_type`,
`owner_type_code`. Full field docs are at `https://developer.nlr.gov/docs/transportation/alt-fuel-stations-v1/all/` and
`https://afdc.energy.gov/data_download/alt_fuel_stations_format`.

## Processing choices
- Status: only open stations (status E), matching the AFDC state-count default.
- Tompkins: point-in-polygon against the TIGER 2024 county subdivisions of 36109, the same method as the existing processing.
- Level rows: `ports` = ports at that level; `stations` = stations with at least one port at that level.
- Output long table: `results/tables/infrastructure_history_tompkins_ny.csv`, with columns `year, date, geography, access, level, stations, ports, count_basis, source, evidence`.
  The three NY sources (v0 records, states page, xlsx) are kept side by side for cross-checking.

## Limitations
1. **Stations vs ports vs connectors.** Before 2014 the xlsx gives only locations (2007–2010) or outlets (2011–2013).
   In 2021 AFDC moved to OCPI counting. Ports became "vehicles that can charge simultaneously" rather than connectors, and the
   ChargePoint and Greenlots API integrations split single addresses into several stations with distinct coordinates. Changes
   from 2020 to 2021 are therefore partly definitional; CAGRs that span 2021 are flagged.
2. **Status changes and retirements.** A snapshot counts what AFDC *published* as open on that date. It includes stations
   that later closed and excludes stations that were open but not yet reported. Reporting lags (for example, non-networked sites
   added long after opening) push counts downward for recent dates as they stood at the time.
3. **Record identity.** Station `id`s can be retired and re-created when a network re-imports data (OCPI split). A station
   "absent from the latest snapshot" is not necessarily a physical closure.
4. **Geocoding.** Early records are often address-geocoded (`geocode_status` 200-8/200-9, not GPS). Stations near the
   county line may be assigned to the wrong county. Tompkins counts are small, so one or two misplaced sites matter.
5. **Private stations are under-reported.** AFDC covers public stations and *voluntarily reported* private non-residential
   stations (workplace, fleet). Residential chargers are excluded by design. Private series are lower bounds.
6. **Year-end alignment and status basis.** The xlsx uses "near the end of December"; the v0 and page queries use 12-31.
   The final point is 2026-09-01. Cross-check for NY: the v0 records (status E) match the states page exactly for every
   date, and the page matches the xlsx exactly for 2014–2023. From 2024 the xlsx **includes temporarily unavailable (T)
   stations**. The page with `include_temporarily_unavailable=true` reproduces the xlsx exactly (2024: 5,182 stations /
   17,716 ports vs 4,777 / 16,839 for open only; 2025: 5,482 / 20,363 vs 5,331 / 19,882). Use a single status basis
   when fitting trends.
7. **Partial historical fields.** Power (kW), funding sources, maximum vehicle class and J3271 are missing before their introduction dates (see `warnings`).
8. **Undocumented endpoint.** `v0/historical-date` is not in the public API docs and may change without notice. The xlsx and the
   states page give an independent official cross-check at NY level.

## Results
See `results/tables/infrastructure_history_tompkins_ny.csv`, `infrastructure_survivorship_bias.csv`,
`infrastructure_station_persistence.csv`, `infrastructure_growth_metrics.csv`, `infrastructure_evs_per_public_port.csv`
and `results/figures/infrastructure_history.png`. The key numbers are summarised below.
