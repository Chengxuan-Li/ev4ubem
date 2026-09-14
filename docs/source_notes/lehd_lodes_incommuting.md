# LEHD LODES in-commuting to Tompkins County and the in-commuter EV charging gap; student/visitor vehicle sources

Checked 2026-09-14. Acquisition: `python -m src.acquisition.lehd_lodes` (raw files in `data/raw/lehd_lodes/`, git-ignored;
manifest in `metadata/manifests/lehd_lodes.json`). Analysis: `python -m src.analysis.incommuter_charging`. The analysis
docstring gives every equation.
Outputs: `results/tables/incommuter_flows_by_origin.csv`, `incommuter_charging_estimate.csv`, `incommuter_workplace_by_bg.csv`,
`results/figures/incommuter_charging.png`.

## Why
The load model counts only EVs in the Tompkins DMV stock. EVs that belong to people living elsewhere and working in
Tompkins are not in that stock, but they charge at Tompkins workplaces and public chargers. The model has the opposite
error too: `load_assembly.py` places *all* resident workplace and public charging at Tompkins sites, even for residents
who work in another county. This note quantifies both effects.

## Source

| Item | Value |
|---|---|
| Dataset | U.S. Census Bureau, LEHD Origin-Destination Employment Statistics (LODES), version 8 (2020 census blocks) |
| Files | `ny_od_main_JT00_2023.csv.gz` (7,720,403 rows), `ny_od_aux_JT00_2023.csv.gz` (809,356), `ny_od_main_JT01_2023.csv.gz` (7,055,595), `ny_od_aux_JT01_2023.csv.gz` (745,983) |
| URL | https://lehd.ces.census.gov/data/lodes/LODES8/ny/od/ (latest year **2023**, posted 2025-12-03) |
| Documentation | https://lehd.ces.census.gov/data/lodes/LODES8/LODESTechDoc8.4.pdf (downloaded next to the data) |
| Access | Public, no key or registration |
| Auxiliary | Census 2024 Gazetteer counties (internal points) for distances; ACS 2020–2024 B08301 (already acquired) for commute mode |
| Evidence class | **A** for flows (administrative, with noise infusion). **D** once aggregated to county/BG and distance-screened. The energy estimate is **E**. |

## Definitions and caveats
- **Jobs, not workers or vehicles.** LODES counts jobs from state unemployment-insurance wage records, plus OPM federal
  civilian jobs from 2010 on. A person with two jobs appears twice in JT00. **JT01 "primary jobs"** keeps one job per
  worker (the highest-paying), so it is closer to a count of workers.
  - Jobs in Tompkins in 2023: JT00 46,926; JT01 43,563.
  - Low and central cases use JT01; the high case uses JT00.
- **main vs aux.** `main` covers jobs whose workplace and residence are both in NY. `aux` covers jobs with a NY workplace
  and an out-of-state residence. Tompkins residents' jobs in other states would be in those states' aux files; they were
  not downloaded and are ignored (small).
- **Coverage.** The following are not covered:
  - self-employed people, informal work, and most uniformed military;
  - student workers only when they are on UI-covered payroll (university student employment usually is covered);
  - graduate stipends that are not wages;
  - students who do not work.

  Federal jobs are included in JT00/JT01; JT04/JT05 isolate them.
- **Multi-establishment employers.** When an employer does not report worksite locations, LODES imputes them. A
  residence or workplace far from the true one is also possible: the 267 Kings County and 240 New York County
  residents with primary jobs in Tompkins are more likely remote or administrative records than daily commuters. That
  is why a **distance screen** is applied: origin-county internal point within 80 / 100 / 160 km of the Tompkins
  internal point.
- **Noise infusion.** Block-level OD cells are perturbed to protect confidentiality and small cells are synthetic, so
  only BG and county aggregates are reported. Individual block pairs should not be interpreted.
- **Commuting ≠ driving ≠ charging.** Place of work is not presence at work (hybrid or remote work), and a commute is
  not necessarily by car. Vehicles per job use ACS B08301 at the origin county (drove alone plus carpoolers ÷
  occupancy), which describes all workers living there, not only those commuting to Tompkins.
- **Time mismatch.** LODES 2023 jobs are assumed unchanged for 2026 and 2035.

## Key flows (JT01 primary jobs, 2023) — class A/D
- **Jobs in Tompkins:** 43,563.
  - Held by Tompkins residents: 23,155 (53 %).
  - Held by residents of other NY counties: 18,156.
  - Held by out-of-state residents: 2,252 (PA 792, NJ 399, MA 146).
  - **In-commuters fill 46.8 % of Tompkins jobs.**
- **Within 100 km:** 14,112 in-commuting jobs (13,870 NY + 242 out-of-state, mainly Bradford County, PA).
- **Top origins:**

  | Origin county | Primary jobs in Tompkins |
  |---|---|
  | Cortland | 2,810 |
  | Tioga | 2,324 |
  | Cayuga | 1,740 |
  | Chemung | 1,408 |
  | Schuyler | 1,289 |
  | Broome | 1,090 |
  | Onondaga | 1,016 |
  | Seneca | 972 |
  | Monroe (134 km, outside central screen) | 773 |
  | Steuben | 401 |

- **Out-commuting:** of Tompkins residents' NY primary jobs, 6,981 are outside the county within 100 km. That is 23.2 %
  of jobs, or **21.8 % weighted by resident EVs** (residence BG × expected EVs from `du_ev_2026`). The shares are
  21.3 % / 20.0 % within 80 km and 27.0 % / 25.6 % within 160 km.
- **EV shares:** origin counties are far below Tompkins.
  - Passenger-class EV share, DMV 2026: Cortland 1.5 %, Tioga 1.1 %, Cayuga 1.4 %, Chemung 1.3 %, Schuyler 1.6 %,
    Broome 1.8 %, Onondaga 2.6 %, against Tompkins 5.6 %.
  - The job-weighted mean over screened origins is 1.5 %.
- **Where in-commuters work:** workplace BGs are concentrated.
  - 361090013021 (Cornell central campus) holds 14 % of in-commuter charging energy; the top 3 BGs hold 31 %.
  - 7 BGs account for 50 % and 20 BGs for 80 %.

## Estimate (details and parameter values in `incommuter_charging_estimate.csv`) — class E
Low / central / high are bounding cases: every parameter is set to its low or high value together.

| 2026 | low | central | high |
|---|---|---|---|
| Screened in-commuting jobs | 13,584 (JT01, 80 km) | 14,112 (JT01, 100 km) | 16,734 (JT00, 160 km) |
| In-commuter vehicles | 10,861 | 12,081 | 15,783 |
| In-commuter EVs | 147 | 181 | 376 |
| Workplace-charging users (access × use) | 16 | 27 | 73 |
| Workplace MWh/yr | 10 | 19 | 63 |
| Public top-up in Tompkins MWh/yr | 6 | 14 | 60 |
| **Gross addition MWh/yr** | **16** | **33** | **123** |
| Gross workplace ÷ resident workplace (447 MWh) | 2 % | 4 % | 14 % |
| Gross ÷ county total (10,851 MWh) | 0.15 % | 0.30 % | 1.1 % |
| Out-commuting residents: workplace offset | −114 | −98 | −89 |
| Out-commuting residents: public offset (symmetric assumption) | −190 | −81 | −37 |
| Net workplace (in − out) | −104 | −79 | −26 |
| Net all | −288 | −146 | −3 |

**2035:**
- In-commuter EVs: 367 / 705 / 2,620. Origin EV shares are scaled by the Tompkins growth-model multiplier (slow 2.50,
  trend 3.90, policy 6.96). Workplace access rises to 0.23 / 0.32 / 0.45.
- Gross addition: 54 / 172 / 1,176 MWh/yr. That is 0.17 % / 0.34 % / 1.3 % of the matching-scenario county total
  (31.8 / 50.5 / 90.6 GWh).
- The workplace offset grows with the resident pool: −449 / −607 / −1,318 MWh.

**Interpretation:**
- **Gross addition is small.** In-commuter charging in Tompkins is ≈ 0.3 % of the modelled load, with an upper bound
  of ≈ 1 %. In-commuters fill almost half of Tompkins jobs, but the counties they live in have EV shares of 1–2.6 %,
  against 5.6 % in Tompkins.
- **The net correction is negative.** The resident model's larger error is that it places the workplace charging of
  resident EV owners who work elsewhere (≈ 22 % EV-weighted) at Tompkins sites.
- **This is not an empirical finding.** Both terms are small next to the uncertainty in the DCFC and fleet pools.

**Assumptions** (all stated in code):
- Commute kWh factor 0.9 / 1.0 / 1.25.
- Share of non-home public charging done in Tompkins φ = 0.15 / 0.30 / 0.60. The same φ is used for the symmetric
  resident public offset, applied to public L2 plus the non-en-route share of DCFC (26 % in the 2026 library).
- Commuter-selection multiplier on origin EV share 1.0 / 1.0 / 1.5.
- Out-of-state EV share 0.5 / 1.0 / 2.0 %.
- Per-user workplace energy (library 2026, single-family-owner mixture): BEV 916 kWh/yr, PHEV 453 kWh/yr.

## Student and visitor vehicles: public-source search (2026-09-14)
The NYS DMV stock covers NY registrations only. Out-of-state students are normally not NY residents, and nonresidents
may keep their home-state registration. A local EV registered in another state is therefore invisible to the DMV
data. No public, login-free source counts such vehicles or EV parking permits.

| Source | URL | Access | Contents | Usable? |
|---|---|---|---|---|
| Cornell FCS, Electric & Green Vehicle Parking | https://fcs.cornell.edu/departments/transportation-delivery-services/parking/electric-green-vehicle-parking | public | 10 dual-port L2 ChargePoint stations (20 ports) and their locations; fees from 2025-07-01; no usage or permit counts | supply only (A) |
| Cornell Chronicle, first Level-3 charger (2025-03-11) | https://news.cornell.edu/stories/2025/03/first-level-3-ev-fast-charging-station-opens-campus | public | one 180 kW DCFC, Cornell fleet vehicles only | qualitative (F) |
| Cornell FCS, Parking for Students | https://fcs.cornell.edu/departments/transportation-delivery-services/parking-campus/parking-students | public | permit prices; plates must be registered with Transportation, but no counts are published | qualitative (F) |
| Sustainable Cornell, Commute Mode | https://sustainable.cornell.edu/commute-mode | public | qualitative: undergraduates mostly walk, staff mostly drive; commuter survey under way | qualitative (F) |
| Cornell Chronicle 2007 travel survey | https://www.news.cornell.edu/stories/2007/03/survey-shows-fewer-cu-employees-drive-solo-work-average | public | drive-alone shares: employees 55 %, graduate students 19 %, undergraduates 5 % (2007) | dated, context (F) |
| Cornell Student Assembly Res. 54 (2025) | https://assembly.cornell.edu/sites/default/files/SAR54ExpandingFreeAndSubsidizedStudentParkingAtCornellUniversity.pdf | public | permit costs; > 55 % of undergraduates live off campus; no permit totals | qualitative (F) |
| AASHE STARS reports (Cornell 2019/2023/2024, Ithaca College) | https://reports.aashe.org/ | **login required** for credit detail | The Cornell 2024 scorecard summary is visible (commute modal split 3.84/5). A search snippet of the 2023 page cites about 1,586 student permits (Fall 2022); this was **not verified** and would need an account. | not used |
| Ithaca College Sustainability: Transportation | https://www.ithaca.edu/sustainability-ithaca/resources/transportation | public | "Recharge at IC": 26 + 2 L2 and 2 dual-port DCFC; public fees $0.15 / $0.30 per kWh; no usage or permits | supply only (A) |
| Ithaca College Parking Services | https://www.ithaca.edu/public-safety-and-emergency-management/parking-services | public | permit prices only | qualitative (F) |
| Tompkins Cortland CC transportation | https://www.tompkinscortland.edu/transportation-options | public | shuttle/TCAT only | not usable |
| Tompkins County 2024 Visitor Profile (Future Partners, Feb 2025) | https://www.tompkinscountyny.gov/files/assets/county/v/1/planning-amp-sustainability/documents/tourism/tompkins-county-2024-visitor-profile-study.pdf | public | 757.5 k visitors, 2.0 M visitor-days, party size 2.8, 54.4 % NY residents, 10.1 % came mainly for a college visit | **quantitative for visitors (B/A survey)** |
| Visit Ithaca 2024 Annual Report | https://assets.simpleviewinc.com/simpleview/image/upload/v1/clients/ithacany/VisitIthaca_2024_Annual_Report_ad8f5a17-ff8b-4e40-9667-2535a55decd7.pdf | public | tourism spending | context (F) |
| NYS DMV out-of-state registration and residency pages | https://dmv.ny.gov/registration/register-an-out-of-state-vehicle ; https://dmv.ny.gov/more-info/moving-to-or-from-new-york-state | public | out-of-state students are not residents; home-state registration remains valid | legal basis for the gap (F) |
| ITCTC 2045 Long Range Transportation Plan (adopted 2024-12-17) | https://www.tompkinscountyny.gov/All-Departments/Ithaca-Tompkins-County-Transportation-Council/2045-Long-Range-Transportation-Plan | public (13 MB PDF, not reviewed) | has a transportation-demand chapter; may contain commuting and inbound-trip data | to review |
| City of Ithaca garages | https://www.cityofithacany.gov/709/Garage-Parking | public | chargers in Green, Seneca and Cayuga St garages; no session data | qualitative (F) |
| Unreachable | Cornell FCS "New EV charging plan" announcement (403); *The Ithacan* EV-charger articles (403); NYSTIA Tompkins PDF (404) | — | — | — |

**Indicative magnitudes only, not added to the model.** These are E/F arithmetic on stated assumptions.
- **Visitors.**
  - 2.0 M visitor-days ÷ 2.8 per party ≈ 0.71 M party-days.
  - × 0.8 arriving by car (assumption) × 2–5 % EVs × 5–15 kWh charged in Tompkins per EV-day ≈ **60–430 MWh/yr**
    (≈ 170 MWh at 3 % and 10 kWh).
  - That is the same order as the model's existing passer-by DCFC term (523 MWh, 25 % of DCFC energy). The passer-by
    term already stands in for visitors and should not be supplemented without better data.
- **Students.**
  - An unverified ≈ 1,600 Cornell student permits × 30–60 % out-of-state-registered (assumption) × 3–6 % EVs gives
    ≈ 15–60 EVs.
  - At ≈ 1,500 kWh/yr each, that is ≈ 20–90 MWh/yr, mostly at residential chargers already modelled for dwellings, or
    at the 20 campus L2 ports.
  - Getting a real count would require Cornell or IC plate-registry or ChargePoint session data, obtained through a
    data request, not a public page.

## Limitations
- Workplace access for in-commuters is taken to equal residents' (Drive Clean 23 %, B); the actual campus supply is
  small (Cornell 20 L2 ports).
- EV shares at the origin describe everyone living there, not people who hold Tompkins jobs (ecological inference);
  the high case applies ×1.5 for selection.
- The resident offsets assume out-commuting resident EV owners would otherwise have been assigned workplace charging
  in Tompkins, which is how `load_assembly` works.
- The public offset rests on a symmetry assumption (φ) and is the least supported term.
- LODES imputation and noise, the 2023 → 2026 time gap, and hybrid work are not modelled beyond the library's 80 %
  attendance and the WFH term.
