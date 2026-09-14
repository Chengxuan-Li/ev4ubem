# Findings — EV ownership and charging evidence for Tompkins County / Ithaca

Last updated: 2026-09-14 (DMV snapshot rows updated 2026-09-02; AFDC retrieved 2026-09-14).
Every quantitative statement carries an evidence label:
**[A]** local observation · **[B]** New York observation · **[C]** national/nonlocal observation ·
**[D]** derived/processed observation · **[E]** model output · **[F]** qualitative ·
and a status: *observed*, *inferred* (derived with stated assumptions), or *simulated*.
Tables/figures cited are in `results/` and reproducible via `docs/methodology.md`.

---

## 0. Answer to the phase question (short)

> *Given only public data, what do we know, what can we infer at building/site scale, what complexity is justified, and how can it be validated?*

1. **EV stock is observed, not predicted**, at county and ZIP level with BEV/PHEV, make/model and model year,
   provided PHEVs are identified by VIN decoding (DMV's fuel field misses them). Tompkins: **3,233 plug-in EVs**
   (1,833 BEV, 1,400 PHEV) in Sep 2026 [A, observed], roughly doubling since Apr 2023.
2. **Nothing public observes EVs below ZIP.** Building/parcel placement is inference; plausible assumptions move the
   share of EVs in multi-unit housing between ~38 % and ~8 % [inferred]. This is the dominant ownership uncertainty
   for a building-level model.
3. **No public New York session-level charging data exist.** NY evidence is summary-level (NYSERDA 22-03 utilisation
   shapes, Drive Clean surveys) [B]; distributions must be borrowed from open non-NY session data [C], which match NY
   weekday *shapes* well for public L2 and residential/MUD (r ≈ 0.91–0.97) but not for the one open workplace dataset.
4. **Justified complexity now:** observed ZIP stock by BEV/PHEV × scenario-based within-ZIP allocation × location-mixture
   of hourly charging shapes (home / workplace / public L2 / DCFC), with explicit annual-energy assumptions. A stochastic
   event model is supportable for *home* charging (open Norway sessions provide per-user frequency, plug-in time,
   duration, energy) and is needed for building-level peaks because diversity is strong (per-EV peak falls ~4× from 1 to
   ~60 EVs). SOC/trip-chain models are not justified by available data for present-day load.
5. **Validation:** stock is validated by observation; area-level adoption predictors can be validated out-of-sample
   across NY ZIPs; hourly *magnitudes* cannot be validated with public observations (TEMPO is a model and is ~2.5× higher
   than bottom-up energy for the observed stock).

---

## 1. EV ownership / stock

### 1.1 Current stock (DMV snapshot 2026-09-02) [A, observed; drivetrain by VIN decoding = D]
| Scope | BEV | PHEV | EV | Denominator | EV share |
|---|---:|---:|---:|---:|---:|
| Tompkins residents (`county=TOMPKINS`), all vehicle classes | 1,833 | 1,400 | 3,233 | 64,027 VEH | 5.0 % |
| … light-duty vehicles (LDV) | 1,793 | 1,400 | 3,193 | 59,554 LDV | 5.4 % |
| … passenger-class (PAS) LDV | 1,621 | 1,315 | 2,936 | — | 5.6 % of PAS LDV |
| Tompkins by ZIP population share (method used for history) | 1,757 | 1,366 | 3,123 | — | — |

Source tables: `data/processed/dmv/tompkins_ev_stock_zip_2026.csv`, `results/tables/tompkins_ev_stock_timeseries.csv`.

- **PHEVs are 44 % of Tompkins LDV EVs and are coded `fuel_type = GAS` in DMV** (983 of 1,400 matched both vPIC and
  EValuateNY; only 4 PHEVs are coded ELECTRIC). DMV `ELECTRIC` ≈ BEV. Using the fuel field alone halves the EV count
  (decision 0002). 10 `ELECTRIC` rows decode as ICE/HEV (data-entry conflicts, <1 %).
- **ZIP 14850 (Ithaca)** holds 2,199 of the county's LDV EVs; EV share of LDVs by ZIP (county=TOMPKINS residents):
  14850 7.3 %, 14886 Trumansburg 5.4 %, 14817 Brooktondale 5.3 %, 13068 Freeville 3.7 %, 14882 Lansing 3.3 %,
  13053 Dryden 2.6 %, 14867 Newfield 2.3 %, 13073 Groton 1.5 % [A].
- **Fleet/organizational registrations:** 297 Tompkins EVs are non-PAS or non-LDV; ZIP 12449 (Lake Katrine, Ulster
  County) carries 731 vehicles coded `county=TOMPKINS` (75 % commercial) including 56 EVs — a fleet address, not a
  household location [A]. These belong to depot/workplace charging, not residential buildings.
- **Models:** Toyota RAV4 Prime 321, Prius Prime 289, Tesla Model Y 217, Chevrolet Bolt EV 176, Tesla Model 3 165,
  Nissan Leaf 127, Chevrolet Volt 105, Hyundai Ioniq 5 94 [A/D]. BEVs skew new (MY2023+ = 1,196 of 1,833 BEVs);
  PHEVs older (MY2023+ = 578 of 1,400).

### 1.2 Growth [D/A, observed]
EValuateNY (ZIP-weighted to Tompkins): 335 EVs (Apr 2018) → 736 (Apr 2020) → 1,294 (Apr 2022) → 1,655 (Apr 2023);
DMV (same method) 3,123 (Sep 2026). **CAGR 2023→2026 ≈ 20 %/yr; net growth ≈ 430 EVs/yr.**
Flows (Sep 2024–Aug 2026, `results/tables/tompkins_ev_flows_summary.csv`) [A]: ~530 ORIGINAL registrations of EVs per year
(≈366 BEV, 164 PHEV; 5.9 % of decoded original registrations), 260 Drive Clean rebates per year (≈49 % of EV original
registrations). Originals exceed net growth as expected (used-vehicle transfers, move-ins, scrappage/move-outs).
Decoding covered 82 % of all original registrations in the first pass (to be updated after statewide VIN decoding).

### 1.3 Cross-source reconciliation
| Comparison | Result | Explanation |
|---|---|---|
| DMV county field vs ZIP-population-share geography (2026) | 3,233 vs 3,123 (−3.5 %) | split ZIPs (13045 Cortland, 14886, 14883, 13736…) and out-of-area fleet ZIPs |
| DMV `ELECTRIC` vs VIN-decoded BEV (Tompkins) | 1,853 vs 1,833 BEV | ELECTRIC includes a few HEV/ICE conflicts; excludes PHEVs entirely |
| EValuateNY Apr 2023 NY total | 139,222 EVs (All EV Registrations) = BEV 82 k + PHEV 57 k (Current Registrations) | internal consistency of EValuateNY tables |
| Drive Clean rebates (Tompkins 2017-03 → 2026-07) vs stock | 2,017 rebates (1,091 BEV, 926 PHEV) vs 3,233 stock | rebates are new-vehicle flows incl. vehicles since scrapped/moved; stock includes used/non-rebated EVs |
| Historical county docs | 136 EVs (2014/15, dates conflict), 644 (end-2019) [F/D] | EValuateNY Apr 2020 ZIP-weighted 736 — same order |
| `ny_ev_registrations.csv` "regularly updated" | ends 2022-03 | stale; EValuateNY v11 ends 2023-04 |

### 1.4 Spatial resolution
Directly observable: county, ZIP (and DMV city label) [A]. Not observable: census tract/BG, parcel, building, tenure,
housing type of the registrant. DMV transactions' `georeference` is a ZIP centroid, not an address.

---

## 2. Population, housing and EV adoption correlates

### 2.1 NY ZIP cross-section (ecological) [B/D, inferred]
2023 (EValuateNY, 1,356 ZIPs, 132,485 EVs) vs ACS 2020–2024 (`results/tables/zip_ev_model_*_2023.csv`):
- Negative-binomial GLM with household offset: **72 % of Poisson deviance explained out-of-county** (10-fold county-grouped CV),
  gradient boosting 71 %, 7-variable model 61 %, constant EVs/household 0 %.
- Adjusted incidence-rate ratios per SD (full model): median home value **1.56**, bachelor's+ share **1.35**, zero-vehicle
  household share **0.62**, share commuting ≥30 min 0.92, density 0.91 (conditional), built-2000+ 1.05; income,
  owner-occupied-detached share and college enrolment not significant once home value/education are included
  (collinearity; VIFs in `zip_ev_model_vif_2023.csv`).
- **Tompkins held out:** 14850 observed 1,210 vs predicted 1,105 (constant-rate 497); Trumansburg 127 vs 61; Freeville 79 vs 37;
  Brooktondale 56 vs 25; Dryden 34 vs 38; Groton 30 vs 30. Area-level ACS variables capture Ithaca's high adoption but
  **under-predict several rural Tompkins ZIPs by ~2×** — a local effect not explained by ACS composition.
- Ecological caveat: these are ZIP associations, not household probabilities; they inform which *area* attributes carry
  information, not how EVs distribute among buildings within a ZIP.
- 2026 statewide replication: **pending statewide VIN decoding** (see §6).

### 2.2 Household-level propensity (NHTS 2022) [C, inferred]
7,893 households, 241 with a plug-in vehicle (`results/tables/nhts_ev_propensity_by_class.csv`):
relative to all households, detached 1.29×, attached 1.09×, **apartment (2+ units) 0.20×**, mobile home 0.35×; owners 1.46×,
renters 1.14×; income <$50k 0.31×, $125–150k 2.2×, ≥$150k 3.7×; rural 0.71×. Weighted logit: income (OR 6.7 for ≥$150k vs
<$50k), ≥2 vehicles (2.4) and urban (1.9) significant; tenure and detached not significant after income.
Drive Clean 2024 recipients [B, self-report, selected]: 85 % own, 78 % detached, 77 % income ≥$100k.
**Consistent direction:** EV ownership concentrates in high-income, multi-vehicle, owner/detached households; apartment
households are strongly under-represented. Magnitudes are national 2022 values with n = 241 and cannot be localised.

### 2.3 Sub-ZIP allocation sensitivity (Tompkins) [inferred]
2,875 PAS LDV EVs allocated to 43,128 calibrated households on 2025 parcels (`results/tables/subzip_allocation_*.csv`,
`results/maps/subzip_allocation_bg_S0_vs_S3.png`):

| Scenario | Weight per occupied unit | EVs in multi-unit housing | BG EVs/HH coefficient of variation |
|---|---|---:|---:|
| S0 | uniform | 38 % | 0.23 |
| S1 | ACS vehicles/household by tenure | 29 % | 0.35 |
| S2 | NHTS home-type propensity | 10 % | 0.38 |
| S3 | S2 × BG income index | 8 % | 0.62 |

BG totals differ by >2× across scenarios in many central-Ithaca block groups. **ZIP totals are matched by construction —
this validates nothing below ZIP.** Recommendation: carry S1–S3 as an ensemble; S0 is implausible given all individual-level
evidence (NHTS, Drive Clean).

Available local building attributes that align with the propensity evidence: parcel property class (1-family, 2–3 family,
apartments, mobile homes), year built, living area, assessed/full-market value (proxy for home value) [A]; ACS BG tenure ×
units, vehicles, income [A, survey]. Student concentration (Cornell) is visible in ACS college share but its EV effect is
unobserved.

---

## 3. Charging infrastructure [A, observed]
AFDC (2026-09-14), Tompkins by point-in-polygon: **105 stations (104 open), 248 L2 ports, 42 DC fast ports; 100 public
stations** (NY Open Data mirror: 99 stations/237 L2/40 DCFC; the 6 API-only stations are recent). Networks: ChargePoint 51
stations, then VIALYNK, FLIPTURN, ChargeSmart, EV Connect, SWTCH, EVOKE, Tesla. Surviving public ports by open year: L2 33 (2020) →
59 (2022) → 91 (2023) → 187 (2024) → 237 (2026); DCFC 9 (2019) → 17 (2023) → 40 (2026) (survivorship-biased growth).
≈ 11.7 EVs per public port (3,233 / 277). Charge Ready NY-funded Tompkins sites: MUD 38 ports (Ecovillage 20, Longhouse 6,
Summerhill 8, Springwater Inn 4), workplace 12, public 12 (incl. 6 at NYS Grange, Cortland ZIP 13045) [A/B]. Facility type is missing for 82 of 105 AFDC stations,
so charger→land-use classification needs parcel joins.

---

## 4. Charging behaviour

### 4.1 New York evidence [B]
- **NYSERDA 22-03** (1,288 networked L2 stations, 434,578 sessions, 2012–2020; summary only): mean 3.25 kWh and 0.32
  sessions per port-day; mean charging 2.4 h + idle 2.3 h per session (median 2.0 h + 0.5 h); implied ≈9.7 kWh/session,
  ≈4.2 kW. Weekday charging utilisation peaks at 9–10 am: workplace ~21 %, public ~15 %; MUD peaks ~9 % at 9 pm–midnight;
  weekend peak ≈¼ of weekday. Idle time is longest for evening/overnight plug-ins.
- **Local ChargePoint use, ZIP 14850** (EValuateNY, ~6 ports): 2019 15.8 MWh, 7.6 kWh/session, 7.3 kWh/port-day, 0.96
  sessions/port-day; 2022 25.0 MWh, 11.5 kWh/session, **16.5 kWh/port-day** (NY ChargePoint average 6.1), charging 59 % of
  connected time, 4.7 kW while charging [A/B]. Ithaca public ports were well above state-average utilisation before 2023.
- **Drive Clean 2024 ownership survey** (4,869 responses, 10.6 %; rebate recipients; self-report): BEV 10,670 mi/yr, PHEV
  10,082; charge at home daily BEV 34 % / PHEV 51 %, never at home 11 % / 19 %; BEV home L2 58 % (+27 % 240 V outlet), PHEV
  120 V 68 %; workplace access 23 % (≈⅔ use it); ever public BEV 73 % / PHEV 32 %. No time-of-day or energy data.
- Con Edison SmartCharge evaluation: average active charging ≈4.0 kW BEV, 1.3 kW PHEV [B, telematics summary].

### 4.2 Open session datasets [C] (`results/tables/sessions_*.csv`)
| Dataset | Site | Sessions | Median kWh | Median connection | Median charging | Plug-in mode |
|---|---|---:|---:|---:|---:|---|
| Norway (267 users, 2018–21) | home, apartment garages | 34,611 | 9.2 | 11.2 h | imputed | 16 h (52 % start 16–22 h) |
| Boulder CO 2018–23 | public L2 | 121,459 | 7.2 | 1.8 h | 1.6 h (5.6 kW) | 8 h |
| Palo Alto 2011–20 | public L2 | 248,579 | 7.1 | 2.1 h | 1.9 h (3.8 kW) | 11 h |
| Dundee UK 2021–25 | public DCFC | 290,132 | 16.6 | 0.6 h | — (≈31 kW) | 14 h |
| Midwest employer 2014–15 | workplace | 3,296 | 6.3 | 2.8 h | imputed | 11 h (suspect) |

- Home users: median 2.4 sessions/week, 35 kWh/week (Norway) → ≈1,800 kWh/yr per user at the median.
- **Shape check vs NY (peak-normalised weekday charging, 8 anchor hours):** public L2 Boulder r = 0.91, Palo Alto r = 0.91
  (open peaks 1–3 h later than NY 9–10 am); Norway home vs NY MUD r = 0.97; **Midwest workplace r = 0.47 (rejected; NY
  workplace shape used instead)** [B vs C].
- **Seasonality** (detrended): Dundee public L2/DCFC daily energy +10–30 % Nov–Feb vs summer; Boulder and Palo Alto ≈ flat
  [C]. No NY monthly session data beyond ChargePoint ZIP-month totals.
- **Diversity** (Norway home, 61 full-year users, immediate charging at 3.6 kW): annual-peak hourly kW per EV 4.7 (N=1),
  3.0 (N=5), 2.2 (N=10), 1.3 (N=50), 1.2 (N=61); at 7.2 kW: 7.6 → 1.6. Mean 0.29 kW/EV [C, inferred].
- **NHTS 2022 vehicle-days** [C]: last arrival home median ≈16:30–17:00 weekdays; work arrival median 8:00, dwell 8.5 h;
  diary miles ≈15 mi/vehicle-day (undercount) vs self-reported annual miles ≈19 mi/day median.

### 4.3 What is measured vs not
Measured publicly for NY: port utilisation shapes by land use (summary), session means, survey frequencies, local
ChargePoint monthly totals to 2022. **Not measured publicly for NY:** home charging timing/energy, per-EV annual kWh,
location energy shares, session-level distributions, charging power distribution, managed/TOU charging uptake in Tompkins
(NYSEG OptimizEV data nonpublic).

---

## 5. Aggregate hourly load (feasibility demonstration)

`results/tables/tompkins_2026_load_scenarios.csv`, `results/figures/hourly_shape_comparison.png`:

| Formulation | Annual MWh | kWh per observed EV | Peak hourly MW | Peak kW/EV | Weekday peak hour | Status |
|---|---:|---:|---:|---:|---:|---|
| A: stock × kWh/EV (base) × location mix 80/7/8/5 | 9,424 | 2,915 | 2.11 | 0.65 | 17 | inferred |
| … low / high energy | 6,881 / 12,297 | 2,128 / 3,804 | 1.54 / 2.75 | 0.48 / 0.85 | 17 | inferred |
| … home-heavy mix 90/4/3/3 | 9,424 | 2,915 | 2.26 | 0.70 | 21 | inferred |
| TEMPO 2022 reference MY2026 | 23,992 | (7,421) | 6.70 | (2.07) | 18 | **simulated [E]** |
| TEMPO 2022 efs_high_ldv MY2026 | 19,209 | (5,942) | 4.99 | (1.54) | 17 | **simulated [E]** |

- Bottom-up annual energy (Drive Clean mileage × efficiency) and Norway home energy (~1,800–2,500 kWh/user) bracket
  2,100–3,800 kWh/EV; **TEMPO implies ~2.5× more energy per observed EV** (its stock and/or VMT assumptions exceed
  Tompkins' observed fleet) and assumes immediate charging after every trip (morning 8 am bump). TEMPO is usable for
  scenario *growth* and shape comparison only.
- Home-dominated mixtures peak 17–21 h; public/workplace shares add a 9 am–3 pm plateau. County peak per EV (0.5–0.85 kW)
  is far below single-building per-EV peaks (≈4–7 kW at N=1), so **building-level loads require event-based sampling or
  diversity-aware profiles, not a scaled county profile.**
- **Event-based home library prototype** (`src/analysis/home_event_library.py`, `results/tables/home_event_library_*.csv`)
  [C timing + B power shares, inferred]: 400 synthetic EV-years from Norway user-years scaled to Tompkins home energy
  (BEV ≈2,330, PHEV ≈1,410 kWh/yr) with Drive Clean L1/L2 shares. Median annual-peak hourly load: 1 EV 7.2 kW (L2 cap),
  2 EVs 8.6 kW, 6 EVs 19 kW, 12 EVs 29 kW (2.4 kW/EV), 24 EVs 43 kW, 48 EVs 71 kW (1.5 kW/EV); single-EV peak/mean ≈27.
  BEVs on L1 deliver only 76 % of target energy within the observed connection windows → L1 households must plug in
  more often/longer than the source users; L1 behaviour is a data gap.

---

## 6. Hypotheses from the brief — status

| # | Hypothesis | Status | Evidence |
|---|---|---|---|
| 1 | Tompkins stock and ZIP distribution observable directly | **Supported** (requires VIN decoding for PHEVs) | §1 |
| 2 | Main ownership problem is sub-ZIP allocation | **Supported** | §2.3 |
| 3 | Housing type, tenure, income, vehicles, density, commute explain spatial variation | **Partly**: at ZIP level home value, education, zero-vehicle share dominate; household-level income/multi-vehicle/home type matter; tenure weak after income | §2.1–2.2 |
| 4 | Residential, workplace, MUD, public need distinct temporal distributions | **Supported** (NY 22-03 and open data agree) | §4 |
| 5 | Stochastic event formulation adequate without full transport model | **Plausible, not yet tested against observed load** (no public observed aggregate EV load) | §4.2, §5 |
| 6 | Parcel-level ownership cannot be validated | **Supported** | §2.3, validation matrix |
| 7 | NY session evidence constrains several distributions without raw data | **Partly**: shapes, means, duration-by-start-hour yes; energy and arrival distributions no | §4.1 |
| 8 | Present-day model simpler than managed-charging model | **Supported**: no SOC/TOU data needed for present load; flexibility work would need connection-time distributions (available: Norway 11 h median home connection vs ~2 h public) | §4.2 |

---

## 7. Recommended model structure (preliminary)

1. **Stock layer (observed):** DMV snapshot → VIN decode → ZIP × {BEV, PHEV} × {personal, fleet}; refresh by rerunning acquisition.
2. **Allocation layer (inferred, ensemble):** ZIP personal EVs → residential parcels/buildings with weights from home type
   (parcel class), BG income and vehicles (S1–S3), calibrated to ACS households; fleet EVs → organisational/commercial sites
   (unallocated until a site list exists). Report BG-level spread.
3. **Energy layer:** annual kWh per EV by drivetrain from mileage × efficiency (range), seasonal index (cool-climate, winter +10–30 %).
4. **Timing layer:** location mixture — home (stochastic sessions sampled from Norway per-user frequency/plug-in/energy,
   L1/L2 power split from Drive Clean), workplace (NY 22-03 shape), public L2 (Boulder/Palo Alto, NY-checked), DCFC (Dundee)
   → hourly kWh per entity; public/workplace energy assigned to AFDC station parcels.
5. **Aggregation checks:** conserve county annual energy; compare shapes with NY 22-03 and TEMPO (benchmark only).

## 8. Remaining uncertainties that matter most for hourly building/site load
1. Within-ZIP placement of EVs (multi-unit vs single-family) — unobservable; largest effect on building loads.
2. Home charging power mix (L1 vs L2) and plug-in timing in upstate NY — drives building peaks; only non-NY data.
3. Location energy shares (home vs work vs public) — assumption; affects workplace/public site loads.
4. Annual kWh per EV (±30 %) and winter penalty magnitude.
5. Fleet EV charging locations (≈300 EVs, depot sites unknown).
6. Cornell/student vehicles and the 14850/14853 campus split.
7. Managed-charging/TOU participation (NYSEG programs) — would shift evening peaks; no public local data.
