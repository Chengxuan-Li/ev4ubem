# Source note: NYSERDA Statewide Multifamily Building Study (SMBS) 2022

This note covers multifamily (MF) vehicle and EV ownership, parking, EV-charging access and in-unit electrical capacity. All figures are for New York.

Compiled 2026-09-14. **Evidence class B**: New York observations, self-reported in surveys or recorded by technicians on site visits, collected 2022–2023.

- Acquisition: `python -m src.acquisition.nyserda_smbs`. Files go to `data/raw/nyserda_smbs/` (git-ignored), and the manifest to `metadata/manifests/nyserda_smbs.json`.
- Analysis: `python -m src.analysis.smbs_mud_parking_ev`. Tables are written to `results/tables/smbs_*.csv`, figures to `results/figures/smbs_*.png`, and parameters to `data/processed/smbs/mf_ev_parameters.csv`.

## 1. Datasets and documents

| Asset | ID / URL | Content | Rows in the public release |
|---|---|---|---|
| SMBS 2022 General Survey | `gfhm-wz4s` — <https://data.ny.gov/resource/gfhm-wz4s.csv> | Online/phone survey of building representatives; one row per building; 165 columns | 1,366 (the metadata says 1,337 completes) |
| SMBS 2022 Occupant Survey | `gjv3-iq86` — <https://data.ny.gov/resource/gjv3-iq86.csv> | Online/phone survey of occupants; one row per household; 138 columns | 156 (the metadata says 135) |
| SMBS 2022 Site Visits | `qwyr-7esw` — a file asset `NYSERDA MF Building Study Site Visits 2022 Data.xlsx` (8.7 MB) | 80 sheets. The first sheet is the data dictionary (1,192 variables). 434 buildings and 639 dwelling-unit facilities | see sheets |
| Overview + Data Dictionary PDFs | Attachments on each of the three assets (`/api/views/<id>/files/<assetId>`) | Design summary; question text and response options | — |
| Multifamily Market Assessment Report + Appendix (Cadmus for NYSERDA) | `https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/building-stock-potential-studies/Multifamily-Market-Assessment-{Report,Appendix}.pdf` | Report: the market-actor study (PMO decision-maker surveys and so on). Appendix (597 pp): the building-assessment report (Sections 1–8), Appendix A weighted data tables with error bounds, Appendix B weights and methodology, and the instruments | — |

Other assets:

- **Retrieved:** 2026-09-14 (UTC timestamps are in the manifest). Socrata `rowsUpdatedAt` is 2026-08-21 for `gfhm-wz4s` and 2026-09-08 for `gjv3-iq86`. The catalog `updatedAt` is 2026-09-10 for all three assets. They are marked "Static – Not updated".
- **Manifest caveat:** the `rows` field is 0 for the parquet entries. The shared helper `fetch_to_parquet` counts rows with `read_parquet(columns=[])`, which returns 0 rows in the installed pandas. The actual counts are 1,366 and 156.
- **Catalog search:** "Multifamily Building Study" and "SMBS" on data.ny.gov returned only these three SMBS assets. The older **RSBS** (Residential Statewide Baseline Study, 2014–15) tables also appeared: MOM owner/manager survey `e58s-chjh`/`hc4z-b2p5`, MF on-site `6vh9-pjsr`, and SMO occupant survey `3m6x-h3qa`/`87mp-9bnv`. They were not used here.

## 2. Study design (Appendix B unless noted)

- **Population:** New York MF buildings, defined as ≥5 residential units. A population dataset of about **122,604 buildings** (Appendix B Table 1) was built from assessor, PLUTO, commercial and LiDAR/footprint data. Parcel-level unit counts were apportioned to buildings, and the overview notes this likely introduced error. The metadata cites about 2.6 M MF dwelling units.
- **Sampling:**
  - Stratified by building size (1–3 / 4–7 / 8+ floors), ownership type (affordable subsidized / affordable census block / co-op & condo / market-rate rental) and IOU territory. The plan targeted 2,463 surveys and 745 site visits.
  - The sample frame was initially random, drawn from the population data.
  - **After six months the frame was opened to any building representative who responded**, and incentives were raised.
  - The design was nested: survey respondents made up the site-visit frame, and building representatives recruited occupants.
  - The overview states this "may have led to increased bias ... including self-selection bias."
- **Achieved:**
  - 1,337 building surveys, between 2022-04-04 and 2023-08-15.
  - 434 site visits, between 2022-06-21 and 2023-07-27.
  - Occupant surveys: 135 per the documentation; the public file has 156 rows.
  - Survey completions by climate zone: 4A (NYC) 587, 4B 146, 5 487, **6 117**. Site visits: 173 / 73 / 153 / **35**.
- **Weights:**
  - Cadmus used stratum weights, population N_h / achieved n_h, for ownership, size, climate zone, vintage and DAC (Tables 10–19). A per-metric non-response adjustment was applied on top.
  - Estimates came from SAS SURVEYFREQ/SURVEYMEANS. Error bounds are 90% CI half-widths.
  - Appendix B says site weights are "provided for each observation in the ... datasets", but **the open-data files contain no weight variable**.
- **Geography granularity:**
  - No county, ZIP or tract in the public files.
  - Available instead: electric utility (General Survey `strata4`, Site Visits `electricity_provider`, Occupant `iou`) and, for 48 of 156 occupant rows, `climate_zone`.
  - SMBS reporting zones: 4A = NYC; 4B = Long Island + Westchester; 5; and 6. **Tompkins County is in SMBS Climate Zone 6** (appendix Table 4) and in **NYSEG** territory.
  - Climate Zone 6 holds 8,622 of 122,604 MF buildings (7%, Table 12). By weighted share (App. A Table 66), CZ6 buildings are 61% NYSEG, 22% National Grid and 16% Central Hudson.
- **Data-quality notes in the documentation:** technicians confused 208 V and 240 V panels; below-grade and adjacent wall areas were inconsistent.

## 3. Relevant variables (`results/tables/smbs_variable_inventory.csv`)

| Dataset | Variable | Content / universe | Non-missing |
|---|---|---|---|
| Occupant | `g15` | "How many electric vehicles are owned or leased by people who live in your home?" Only **None / One / Three or more** occur in the data; **no "Two"**. All households. | 156 |
| Occupant | `g16` | Where the household most often charges (public / at home). Asked if G15 > 0. | 8 |
| Occupant | `g17` | How they pay for the building's charger. Asked if G16 = home. | 3 |
| Occupant | `g3`, `g5`, `g6` | Income band, own/rent, rent assistance | 156 |
| Occupant | `building_size`, `ownership_type`, `iou`, `climate_zone` | Strata attached to the household | 140 / 139 / 140 / 48 |
| General | `e14` | Amenities (multi-select), including **Parking areas** and **Electric vehicle charging stations** (also bike storage, carsharing and others). All buildings. | 1,366 |
| General | `e15` + `e15_1..3_text` | Parking type (underground garage, above-ground garage, open lot, street parking only) with space counts. Asked if E14 includes Parking areas. | 717 |
| General | `e16` | % of spaces assigned to specific tenants (same universe) | 687 |
| General | `e17` + `e17_2..5_text` | Number of EV charging stations by L1 / L2 / L3 / unknown. Asked if E14 includes EV charging. | 34 |
| General | `e18` | Whether tenants are charged for EV charging (same universe) | 34 |
| General | `e19` | Electric metering: direct-metered units, master meter, master + submeters | 1,324 |
| General | `e3`, `strata1`, `strata3`, `strata4`, `e9`/`e10` | Units, floors, ownership, utility, year built. `strata1/3/4` are blank in 345 rows. | — |
| Site | `parking_type`, `parking_spaces`, `parking_management` | Parking element per building. `parking_type` is blank for 174 of 434 buildings (131 of them ConEd). | 260 buildings |
| Site | `ev_plugin`, `ev_charging_types`, `ev_charging_stations_l1..l3` | EV plug-ins present: 7 buildings = 1; L2 counts recorded for 3 | 272 recorded |
| Site | `dwlg_parking_spots`, `dwlg_parking_type` | Spots tied to the sampled dwelling unit | 211 units |
| Site | `dwlg_panel_volts`, `dwlg_panel_amps(_other)` | In-unit panel rating | 563 units / 358 buildings with amps |
| Site | `elec_service_equip_type/volts/amps/phase`, `dwlg_service_*` | Building and dwelling service equipment | 902 / 440 rows |

**Not in SMBS:**

- Total (any-fuel) vehicle ownership.
- BEV vs PHEV.
- Garage type per unit, beyond `dwlg_parking_type` for 41 units.
- Charger power or kW, beyond the level.
- Spare electrical capacity or load calculations.
- Stated EV interest or barriers from occupants.
- Any time-of-use or charging-session data.
- The Market Assessment PMO questionnaire lists "Electric vehicle charging stations" and "Upgrading our electrical panel/wiring" as planned-upgrade options (C7), but the extracted report text gives no tabulated result for them.

## 4. Methods used here

- **Weights (approximate, class D construction):** each file is raked to three published building-population margins, with weights trimmed at 5× the mean.
  - Size: 60,659 / 53,032 / 8,913 (Table 11).
  - Ownership: 9,990 / 41,589 / 15,283 / 55,742 (Table 10).
  - Utility group: climate-zone populations (Table 12) × weighted utility share within zone (App. A Table 66), which gives ConEd 73.7k, PSEG-LI 10.2k, CenHud+O&R 11.0k, National Grid 13.9k, NYSEG+RG&E 13.8k.
  - Rows missing a stratum get no weight. They count in unweighted n but not in weighted estimates. Weighted rows: General 1,021 of 1,366; Occupant 139 of 156; Site 409 of 434.
  - These are **not** the Cadmus weights: no vintage, DAC or non-response factors.
  - Household and dwelling-unit estimates reuse the respondent building's weight. For panels, the weight is split across the units sampled in that building.
  - "Unit-weighted" building shares multiply the weight by E3 units.
- **Uncertainty:** every table gives two estimates.
  - The unweighted k/n with a **Wilson 95% CI**.
  - The weighted estimate with a **95% percentile bootstrap**: 1,000 respondent resamples, weights held fixed, raking and design variance not propagated. The bootstrap collapses when k = 0 or k = n.
  - Kish effective n is also reported.
  - In `mf_ev_parameters.csv` the CI is the bootstrap when 0 < k < n, and Wilson otherwise.
- **Definitions (General Survey):**
  - **Off-street parking** = E14 includes "Parking areas" and E15 names a garage or open lot. A type selected with an explicit 0 spaces counts as absent; this pattern occurs in 140 rows that ticked all three types. "Street parking only" and buildings without "Parking areas" count as no off-street parking.
  - **EV charging** = E14 includes "Electric vehicle charging stations".
- **Definitions (Site Visits):** a blank parking record counts as no on-site parking, and a blank `ev_plugin` counts as no plug-in. Both are lower-bound choices.
- **Region labels:**
  - ConEd = NYC + Westchester.
  - PSEG-LI = Long Island.
  - CenHud+O&R = Hudson Valley.
  - NationalGrid = Central, Northern and Western NY.
  - **NYSEG+RG&E = Southern Tier, Finger Lakes and Rochester, including Tompkins.**
  - **Upstate** = National Grid + NYSEG + RG&E.

## 5. Results

### (a) EV ownership per MF household (Occupant Survey; `smbs_occupant_ev_ownership.csv`, Fig. `smbs_occupant_ev_ownership.png`)

| Domain | k/n with ≥1 EV | Unweighted (Wilson 95%) | Weighted (bootstrap 95%) |
|---|---|---|---|
| NY statewide | 8/156 | 5.1% (2.6–9.8) | **2.9% (0.8–5.8)**, Kish n_eff 94 |
| 1–3 floors / 4–7 / 8+ | 2/70, 2/51, 2/19 | 2.9%, 3.9%, 10.5% | 3.2%, 1.8%, 7.8% |
| ConEd | 2/57 | 3.5% | 1.0% (0–2.5) |
| Upstate (NG + NYSEG + RG&E) | 1/60 | 1.7% (0.3–8.9) | 1.4% (0–4.3) |
| NYSEG + RG&E | 0/17 | 0% (0–18.4) | 0% |
| Renters / owners | 6/119, 1/34 | 5.0% / 2.9% | 3.2% / 1.1% |
| Co-op/condo, market-rate, subsidized, NOAH | 2/24, 2/53, 1/25, 1/37 | 8.3%, 3.8%, 4.0%, 2.7% | 4.6%, 2.4%, 5.8%, 2.3% |
| Income <$35k, $35–75k, $75–150k, $150k+ | 3/70, 1/27, 1/23, 1/13 | 4.3%, 3.7%, 4.3%, 7.7% | — (CIs span 0 to ~15–35%) |

- **Published comparison (Cadmus, App. A Table 141; n = 117; 90% error bound):** subsidized 1% (±1), census-block affordable 0% (±0), **co-op/condo 10% (±7)**, market-rate 2% (±1). Report text: "statewide adoption of EVs is well under 1 in 10 multifamily residents."
- **Counts:**
  - Using `ev_count_lb`, where "Three or more" is coded as 3, the 8 EV households hold ≥14 EVs.
  - 3 of the 8 report "Three or more". For renters with incomes of $35–100k in 5+ unit buildings that is implausible, so it is likely a response or coding artefact. **Use only the "≥1 EV" indicator.**
- **Charging location (n = 8 EV households):** public stations 5, at home 3. For G17 (n = 3): 1 "It's free", 1 "Don't know", 1 "My building does not provide EV chargers".
- **Vehicle ownership of any fuel: not collected.**

### (b) Parking availability and type (General Survey unless noted; `smbs_building_parking_ev.csv`, Fig. `smbs_parking_ev_charging_by_region.png`)

**Share of buildings with off-street parking.** Weighted estimate with bootstrap 95% CI, then unweighted k/n.

| Domain | Weighted (95% CI) | Unweighted k/n |
|---|---|---|
| **NY statewide** | **40.1% (36.6–43.7)** | 687/1,366 |
| ConEd | **15.3% (11.8–19.2)** | 87/462 |
| PSEG-LI | 76.4% | 45/56 |
| CenHud+O&R | 87.3% | 74/86 |
| National Grid | 74.1% | 150/204 |
| **NYSEG+RG&E** | **74.1% (68.2–80.5)** | 154/213 |
| **Upstate** | **74.1% (69.3–78.6)** | 304/417 |
| 1–3 floors | 55.4% | n = 514 |
| 4–7 floors | 22.9% | n = 365 |
| 8+ floors | 38.8% | n = 142 |
| Units 5–9 | 34.5% | n = 491 |
| Units 10–19 | 34.2% | n = 223 |
| Units 20–49 | 34.2% | n = 320 |
| Units 50–99 | 48.9% | n = 189 |
| **Units 100+** | **83.3%** | n = 141 |
| Subsidized | 32.7% | — |
| NOAH | 38.5% | — |
| Co-op/condo | 46.9% | — |
| Market-rate | 40.8% | — |
| Built pre-1940 | **21.6%** | — |
| Built 1940–78 | 64.9% | — |
| Built 1979–2006 | 59.1% | — |
| Built 2007+ | 62.0% | — |

**Share of dwelling units** (unit-weighted) in buildings with off-street parking:

| Domain | Weighted (95% CI) |
|---|---|
| NY statewide | **64.2% (56.4–71.2)** |
| Upstate | 80.2% (73.6–85.7) |
| **NYSEG+RG&E** | **83.8% (77.4–88.6)** |

**Parking type**, weighted share of all buildings; a building can have more than one type:

| Type | Statewide | Upstate | ConEd |
|---|---|---|---|
| Garage (underground or above-ground) | 16.4% | 20.1% | 8.6% |
| Open lot | 31.9% | 63.8% | 9.7% |
| Street parking only | 2.0% | 2.8% | — |

**Site visits (field-observed; blank record counts as none).** Weighted share of buildings with on-site parking:

| Domain | Weighted (95% CI) | Unweighted k/n |
|---|---|---|
| Statewide | 45.0% (39.0–51.6) | 260/434 |
| ConEd | 21.2% | — |
| Upstate | 81.6% (74.1–88.2) | — |
| NYSEG+RG&E | 94.2% (87.0–99.6) | 61/68 |

Garages were observed at 9.2% of buildings statewide and 4.8% upstate.

**Published comparison (Cadmus, site visits):**

- Statewide (Table 110, n = 294): open lot 40% (±8), covered lot 2%, above-ground garage 7%, underground 10%, **none 41% (±11)**.
- No on-site parking by zone (Table 107): NYC **67% (±17)**, CZ5 9% (±6), **CZ6 1% (±2, n = 33)**. Open lot is 82% in CZ5 and 90% in CZ6.
- Our site-visit "none" is higher: 55% weighted statewide, 18% upstate. That is because blank parking records are counted as none.

**Assigned spaces (E16; buildings with parking areas; n = 687 unweighted):**

| E16 answer | Unweighted | Weighted |
|---|---|---|
| 76–100% | 34.9% | 39.9% |
| None | 33.8% | 24.7% |
| 51–75% | 11.2% | 16.6% |

For NYSEG+RG&E (n = 154), 30.5% of buildings assign 76–100% of spaces and 34.4% assign none. Cadmus Table 116 (n = 623) gives 36% and 25%.

**Spaces per unit** (buildings with off-street parking and complete counts; `smbs_parking_spaces_per_unit.csv`):

| Domain | Median (IQR) | n |
|---|---|---|
| Statewide | **1.11 (0.72–1.77)** | 683 |
| Upstate | 1.20 (0.83–2.00) | 302 |
| NYSEG+RG&E | 1.20 (0.91–1.79) | — |
| ConEd | 0.58 | — |
| 1–3 floors | 1.33 | — |
| 8+ floors | 0.50 | — |

Complex-wide lots may have been reported against a single building.

- **Unit-level spots (site visits, 211 units with a value):** 1 spot 158, 2 spots 40, 0 spots 12. A blank probably means not recorded.

### (c) EV charging at buildings

**General Survey (E14): share of buildings with EV charging for occupants.** Weighted estimate with bootstrap 95% CI, then unweighted k/n.

| Domain | Weighted (95% CI) | Unweighted k/n |
|---|---|---|
| **NY statewide** | **1.8% (1.0–2.8)** | 34/1,366 |
| ConEd | 1.0% (0.2–2.3) | 5/462 |
| PSEG-LI | 0% | 0/56 |
| CenHud+O&R | 2.6% | — |
| National Grid | 2.4% | — |
| **NYSEG+RG&E** | **5.7% (2.1–10.0)** | 9/213 |
| **Upstate** | **4.0% (2.0–6.5)** | 14/417 |
| 1–3 floors | 1.2% | — |
| 4–7 floors | 2.2% | — |
| 8+ floors | 3.1% | — |
| **Built 2007+** | **11.0% (4.4–19.2)** | 16/155 |
| Built pre-1940 | 0.3% | 2/603 (unweighted) |
| Subsidized | 0.7% | — |

On a unit-weighted basis, **3.5% (1.4–6.6)** of MF units statewide are in buildings with EV charging.

**Ports** (E17, 34 buildings; `smbs_building_ev_charger_ports.csv`):

| Domain | Ports reported | Median per building | Ports per 100 units in those buildings |
|---|---|---|---|
| Statewide (34 buildings) | 578 (L1 139, L2 374, L3 41, unknown 24) | 2 | 19 (a few large sites dominate) |
| NYSEG+RG&E (9 buildings) | 52 | 6 | 16 |

L3/DCFC reports at MF buildings are probably misclassified.

**Tenant fees** (E18, n = 34, unweighted counts):

| E18 answer | Count |
|---|---|
| Charge per kWh | 10 |
| Free | 8 |
| Tenant pays via own electric bill | 6 |
| Monthly charge | 4 |
| Included in rent | 3 |
| Flat fee per session | 2 |
| Don't know | 1 |

Cadmus (Table 140, n = 31) gives per kWh 32%, monthly 26%, on own bill 24%, free 12%.

- **Site visits:**
  - `ev_plugin` = 1 at **7 of 434 buildings**: 1.6% unweighted, 1.8% (0.5–3.6) weighted. Three are NYSEG+RG&E, three ConEd, one O&R.
  - L2 counts were recorded at 3 buildings: 1, 2 and 4.
  - Two ConEd records (facility 45548 and 45921) have identical attributes (31 floors, built 1970) and may be duplicates.
  - Cadmus reports "only three site visits statewide identified EV charging stations" (Tables 128/134: Level 2, mean 3.57 stations).

### Electrical capacity (Site Visits; `smbs_du_electrical_capacity.csv`, Fig. `smbs_du_panel_amps_by_region.png`)

**In-unit panel rating, share of dwelling units** (weighted; 95% CI where estimated).

| Panel rating | Statewide (563 units / 358 bldgs) | ConEd | PSEG-LI | Upstate (212 / 136) | NYSEG+RG&E (89 units) |
|---|---|---|---|---|---|
| ≤60 A | **43.0%** | 55.9% | 63.3% | **11.3%** | 11.6% |
| ≥100 A | **48.9% (43.4–54.9)** | 34.5% | 29.1% | **82.4% (75.8–88.3)** | 78.3% (67.1–87.0) |
| ≥125 A | 18.7% | — | — | 23.6% | 32.0% |
| ≥200 A | 4.9% | — | — | — | — |

Upstate, the modal band is 61–100 A (65% of units). By Cadmus' report text, over two-thirds of dwelling units statewide have "low service amperage".

- **Voltage:**
  - 208 V in-unit panels: 5.2% of units weighted (9.5% unweighted). The recording is unreliable.
  - Building service equipment includes 208 V at 19.8% of buildings weighted (29.7% unweighted, n = 414), and at 53.5% of 8+ floor buildings.
- **Metering (General Survey E19, n = 1,324), weighted:** direct-metered units 66.7%, master meter with submeters 24.4%, master meter only 8.3%.

### (d) Interest and barriers

The SMBS public data hold **no stated-interest or barrier questions about EV charging**. The only related items are E18 (fees), G16 (public vs home charging) and G17.

Cadmus' synthesis:

- "EV infrastructure is close to nonexistent."
- About 90% of buildings outside NYC have on-site parking, and that is the opportunity to install charging.
- In NYC, over two-thirds of buildings have no on-site parking.

These are qualitative, class F.

## 6. Limitations and transferability to Tompkins County

1. **Sample size for EVs is minimal.** Only 8 EV households exist in the whole occupant file, with 0 of 17 in NYSEG+RG&E and 0 of 6 in Climate Zone 6. SMBS cannot estimate a Tompkins or upstate MF EV ownership rate. Wilson upper bounds of 9–18% are uninformative.
2. **Self-selection.** The frame was opened, incentives were raised, and occupants were recruited by building representatives. Buildings with engaged managers, and possibly with amenities, are likely over-represented. The overview itself flags the bias.
3. **Weights.** No weights are in the public data. The raked building weights here approximate Cadmus (weighted statewide parking 40% vs our unweighted 50%). They are building-level, not household- or unit-level.
4. **Timing.** Data are from April 2022 to August 2023. NY EV stock and MF charging (for example Charge Ready NY 2.0 and utility make-ready programs) have grown since. See `docs/findings.md` for 2026 DMV context.
5. **Geography.** Utility territory is only a proxy. NYSEG+RG&E combines Rochester (RG&E) with the Southern Tier and Finger Lakes (NYSEG). The Ithaca MF stock also includes student housing and is not separately identified.
6. **Measurement.**
   - E14/E15 are self-reports. Some complexes report complex-wide lots.
   - Site-visit parking blanks are ambiguous.
   - G15 lacks a "Two" category in the data.
   - Panel voltage was error-prone.
   - "Affordable census block" (Cadmus population) is not the same as self-reported "naturally occurring affordable" (`strata3`).
7. **Row counts.** Public row counts (1,366 and 156) exceed the documented completes (1,337 and 135). 345 General Survey rows lack the strata questions, and the extra rows were not removed.

**Transferability:** the building-stock findings carry over better than the ownership findings.

- **Parking and panels are more transferable.** Upstate figures (off-street parking 74% of buildings and ~80% of units; in-unit panels ≥100 A in ~80% of units) are consistent with Cadmus CZ5/CZ6 results (none at 9% and 1%). They are a reasonable prior for Tompkins MF buildings outside dense downtown/Collegetown blocks.
- **Charging presence (~4–6% of upstate MF buildings in 2022–23) is a dated lower bound.** Local AFDC/ChargePoint data (other repo notes) should be used for 2026.

## 7. Modeling implications (MF allocation and charging access)

1. **Do not take the MF EV rate from SMBS for Tompkins.**
   - Allocate DMV-observed EVs (class A/B, 2026) to dwellings with a housing-type propensity instead. NHTS 2022 apartment households have 0.2× the average plug-in propensity (`results/tables/nhts_ev_propensity_by_class.csv`, class C).
   - SMBS supports that prior qualitatively: MF households are ~3% weighted (95% CI 1–6%) with ≥1 EV in 2022–23, with co-ops/condos higher (Cadmus 10% ±7).
   - Use it only as a sanity bound.
2. **Vehicle ownership per MF household is not available from SMBS.** Use ACS 5-year tenure × vehicles available (B25044) and PUMS (BLD × VEH × TEN) for Tompkins.
3. **Condition MF EV allocation on parking access.**
   - Upstate MF buildings mostly have off-street parking (74% of buildings, 84% of units in NYSEG+RG&E buildings), so assume most Tompkins MF units have a nearby off-street space.
   - Exceptions: pre-1940 and 4–7 floor buildings (22% and 23% statewide) and downtown/Collegetown parcels. Flag these with parcel/lot geometry.
   - Around 1.1–1.2 spaces per unit (median) is a usable default where lots exist.
4. **Home charging for MF EVs should be the exception.**
   - In 2022–23 only ~4–6% of upstate MF buildings (≈6–7% of units) offered occupant EV charging, and 5 of 8 EV-owning MF households charged mainly at public stations.
   - Model MF resident EV energy as mostly public/workplace charging, with a building-level charging option only for buildings known to have ports.
   - Such buildings reported a median of 2–6 ports, mostly L2, and mixed per-kWh or monthly fees. Treat 2026 penetration as a scenario parameter above this 2022–23 baseline.
5. **Metering and assigned spaces shape where the load lands.**
   - About two-thirds of MF buildings have direct-metered units, and 35–40% of buildings with parking assign ≥76% of spaces. In those, a tenant-installed L1/L2 on the unit meter is physically possible.
   - Otherwise charging load should be attributed to the building/common-area meter.
6. **Electrical headroom is limited but less binding upstate.**
   - Upstate, 82% of sampled units have in-unit panels ≥100 A, versus 35% in ConEd. Panel rating is not spare capacity.
   - 7.2 kW L2 per unit generally needs load management or service upgrades.
   - In 208 V buildings (20% of buildings; 54% of 8+ floors), L2 delivers about 5–6 kW.
   - Use these as feasibility flags, not load inputs.
7. **SMBS contains no temporal or charging-session data.** Hourly profiles must come from the session datasets documented elsewhere in this repository.
