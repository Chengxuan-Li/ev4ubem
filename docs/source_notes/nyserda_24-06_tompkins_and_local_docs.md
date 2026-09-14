# Source note: NYSERDA Report 24-06 (Tompkins County used-EV / LMI project) and other local EV documents

Retrieval date: 2026-09-14
Prepared for: ev4ubem (building x hour EV load model, Ithaca / Tompkins County NY)

Evidence classes used in this note (as defined for this note):
- **A**: a statistically representative measurement or a complete administrative census of the target population (e.g., DMV registration counts).
- **F**: qualitative or contextual evidence. This covers interviews, anecdotes, outreach tallies, single-pilot logs, non-representative surveys, and generic national talking points.
- Items that are measured but cover only one site or pilot are labelled "F for population inference" and flagged as such.

---

## 1. Citation, URL, retrieval

**Preferred citation (as printed, PDF p.2):** New York State Energy Research and Development Authority (NYSERDA). 2023. "Facilitating EV Adoption among Used Car Buyers and LMI Community Members in Tompkins County," NYSERDA Report Number 24-06. Prepared by Energetics, Clinton, NY. nyserda.ny.gov/publications

- Full title: *Facilitating Electric Vehicle Adoption among Used Car Buyers and Low- to Middle-Income Community Members in Tompkins County*. Final Report, October 2023. NYSERDA Contract 138145. PDF metadata creation date is 2024-03-28.
- URL: https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/Research/Transportation/2406Facilitating-EV-Adoption-Among-Used-Car-Buyers-and-LMI-Community-Members-in-Tompkins-Countyacc.pdf
- Local copy (git-ignored): `E:\Coding\ev4ubem\data\raw\reports\nyserda_24-06_tompkins_ev_lmi.pdf` (9,505,825 bytes, 78 pages).
- Authors: Energetics (Bryan Roy, Program Director; Victoria McGarril, Principal Analyst; Katherine Bannor, Program Supervisor). NYSERDA project manager: David S. McCabe.
- **How it was read:** the PDF has permission-restrictions encryption, so the Read tool refused it. All 78 pages were extracted with `pdftotext -layout` and rendered to PNG with `pdftoppm`. Pages whose tables extract badly were checked visually: Table 1 (PDF p.15), Table 2 (p.16), Figure 1 (p.17), Table 3 (p.19), Table 4 (p.20), carshare pp.26 and 28, appendix p.41, and slides pp.55, 56 and 71.
- **Page convention:** "p. N (PDF M)". In the main body, PDF page = printed page + 8. The appendices have their own internal page numbers, so only PDF pages are given for them.

---

## 2. Study design

| Item | What the report says | Where |
|---|---|---|
| Type | A demonstration and outreach project, **not** a research study. It had no sampling design, control group, or statistical analysis. | whole report |
| Objectives | (1) Understand barriers to LMI EV purchase. (2) Develop solutions: loans, charging access, extended warranties. (3) Create a used-EV market with one local used-car dealership. (4) Enable EV use through carshare and transit for people without cars. | p.1-2 (PDF 9-10) |
| Team | Energetics (prime). Cornell Cooperative Extension of Tompkins County (CCETC) led outreach, interviews and surveys. Center for Community Transportation (Ithaca Carshare). Clean Communities of Central NY. Ridge Road Imports (used-car dealer). | ES-1 (PDF 8); p.2 (PDF 10) |
| Predecessor | EVTompkins / "EV Accelerator Community" under a prior NYSERDA agreement, focused on new-car buyers. | p.1 (PDF 9) |
| Period | Began November 2020. Nine tasks over 36 months. Heavily affected by COVID-19 (little in-person outreach; low used-EV inventory). | p.1-2, p.4 (PDF 9-10, 12) |
| Barrier interviews | CCETC "interviews and discussions with community members and leaders". Interviewees represented community action groups, advocacy groups, food pantries, and the local housing authority. **Number of interviews and interview dates are not reported.** | p.5 (PDF 13) |
| Outreach events | 24 events, 6/12/2021 to June-Aug 2023, listed in Table 1 with dates and partners. Text claims "engaged with an estimated 11,000 individuals". | p.7 (PDF 15) |
| Outreach metrics | Table 2 covers only the 15 of 24 events that tracked LMI attendance (see section 3.5). | p.8 (PDF 16) |
| Car-buyer classes | "TuneMeUp" two-part class run by CCETC, Alternatives Federal Credit Union (AFCU) and Ridge Road. Offered 5 times with about 30 attendees each. | p.8 (PDF 16) |
| Dealership pilot | Ridge Road Imports sourced and sold 23 used plug-in vehicles (Table 3). It also got a website EV page, sales/technician training (webinar 2/4/2022), and an on-site EV charger. | p.10-17 (PDF 18-25); App. A, D |
| Financing research | Desk review of green loans plus local lender outreach. AFCU could not offer an EV-specific loan; it has a no-credit-score loan with 6-month refinancing. | p.11-12 (PDF 19-20); App. B (PDF 46-48) |
| Warranty research | Three EV extended-warranty products identified. No contract was signed with EFG because the warranty company stopped responding. | p.13 (PDF 21); App. C (PDF 49-51) |
| Carshare pilot | Ithaca Carshare bought two 2021 Chevy Bolts ("Amp", "Joule") and placed them at LMI-serving sites. It tracked booking data and ran a member survey. **Survey sample size, response rate, dates and results tables are not reported. Booking counts are not reported.** | p.18-21 (PDF 26-29) |

**Bottom line:** the report contains **no statistically representative survey, no household sample, and no measured charging data.**

---

## 3. Tompkins-specific quantitative content (with pages)

### 3.1 EV counts / penetration
- **None given.** The report cites no Tompkins EV registration count or penetration rate.

### 3.2 Local charger counts and charger status
- "In Tompkins County, there are over 85 ports available" (App. A Marketing Plan, internal p.8, **PDF 41**, dated 9/26/2023). Same page: "In New York, there are over 7,000 charging ports." The superscript 3 points to a footnote, but **the footnote text is not present on the page** (checked visually), so the source cannot be recovered. The context suggests the AFDC locator. Evidence class F (unsourced snapshot).
- Rack card (PDF 42): "New York State has over 2,700 public charging stations". Statewide context only.
- Downtown DC fast charger at Diane's Automotive (West State / MLK Jr. at Corn St.): "broke and did not operate during the project" despite repair attempts (p.18, PDF 26).
- Level 2 charging existed at 210 Hancock Street Apartments (p.18, PDF 26) and at the 1st & Adams Street carshare location (Fig. 9, p.21, PDF 29).
- Ridge Road Imports installed one EV charging station at the dealership (p.16, PDF 24).

### 3.3 Barriers (interviews; qualitative, no counts)
All from p.5-6 (PDF 13-14):
- "Charging access is a major issue, especially for those who do not have access to home charging."
- In rural areas it is "common for the nearest bus stop to be more than five miles away", and bus schedules often don't fit residents' needs. This is an interview claim, not a measurement.
- Other barriers: low EV awareness; few local EVs, especially used; worry about maintenance (rural LMI owners do their own repairs); unaffordable dependable cars; the need for lender programs.
- The LMI population is "not a monolithic demographic". Many people cannot buy a vehicle, but often someone in the family can.
- Dealer-side barriers (p.10, PDF 18): little auction inventory, high upfront cost, buyer uncertainty about batteries and chargers, unfamiliar staff, and repair risk.
- Carshare members' most common concerns were lack of charging knowledge and range anxiety (p.20, PDF 28). No percentages given.

### 3.4 Charging access, home charging, renters and multifamily
- **No quantitative data** on home-charging availability, renter share, or multifamily charging.
- The only housing detail is the 210 Hancock Street Apartments host site (Ithaca Neighborhood Housing Services; mixed-income rental plus for-purchase) (p.18, PDF 26):
  - Rentals for households at 30% of Area Median Income (AMI), i.e. $24,600 for a family of four, up to 100% AMI ($75,600).
  - Seven for-sale townhomes limited to households at or below 80% AMI ($60,500 for a family of four).

### 3.5 Outreach tallies (Table 2, p.8, PDF 16; verified from page image)
These are not a population measure. Class F.

| Metric | Total (15 events) | Estimated LMI reach |
|---|---|---|
| Events | 15 | 14 |
| People exposed (indirect) | 338,230 | 3,000 |
| People engaged | 11,000 | 1,725 |
| Follow-ups | 90 | 75 |
| Media coverage | 9 | 4 |

The text says 11,000 people were engaged across all 24 events, but Table 2 gives 11,000 for the 15 tracked events. The method behind "estimated LMI reach" is not described.

### 3.6 Commute distances
- **No local commute data.** One dealer-webinar slide (PDF 71) says "The average daily commute in the U.S. is ONLY 30 miles" and that cars spend 95% of the time parked. These are generic national talking points with no source. Class F.

### 3.7 Income segments
- 30%, 80% and 100% AMI thresholds at 210 Hancock (see 3.4).
- Ithaca Carshare "Easy Access" membership: income up to 150% of the Federal Poverty Guideline (p.20, PDF 28).
- AFCU used-vehicle loan rate table by credit tier for 2014-2021 models (App. B, PDF 46). Example: 2.99% at 740+ and 0-36 months, up to 14.99% at ≤549. AFCU says it had earlier offered a discounted EV rate but dropped it for low enrollment (PDF 46).
- AFCU service area: Chemung, Steuben, Schuyler, Seneca, Cayuga, Cortland, Tioga, Tompkins (PDF 47).

### 3.8 Used-EV market observations (Table 3, p.11, PDF 19; verified from page image; pdftotext misaligns this table)
- **23 used plug-in vehicles**, acquired 5/21/2021 to 5/19/2023, all with sold dates (last sold 9/25/2023).
- Model mix, counted from the table: Nissan Leaf 10; Toyota Prius Prime 6; Honda Clarity PHEV 3; Toyota Prius Plug-in 1; Chevy Bolt 1; Kia Soul (listed as "Soul") 1; BMW i3 1. Model years 2013-2022.
- Days on lot ranged 5-148. My calculation from the 23 rows: median 38, mean about 52.7.
- Context (p.4, p.10, PDF 12, 18): pandemic chip shortage and supply problems; "many EVs at auctions were priced too high for the local market."
- Extended-warranty providers "may not find it advantageous to work with smaller sized dealerships" (p.13, PDF 21).
- Federal EV tax credit now covers used vehicles (p.23, PDF 31).
- Class: a complete log of **one** dealership's pilot inventory. It is F for any market-level inference.

### 3.9 Carshare EV operations (p.18-21, PDF 26-29)
- Two 2021 Bolts. Home bases: 210 Hancock St (had a charger) and downtown W State/MLK at Corn (DCFC broken). Staff swapped the vehicles between sites to keep them charged.
- Bookings: "no significant trend in bookings for the EVs"; most months were "on trend with the rest of the fleet". No numbers.
- Use: "most of the EVs were used for around-town driving"; BEV vs PHEV choice "did not seem to impact the driving distance"; members booked EVs "out of sheer convenience". No numbers.
- Two carshare open-house events at 1st & Adams St.

### 3.10 Data sources cited in 24-06 (leads)
| Source cited | Where | Lead value |
|---|---|---|
| Ithaca Carshare booking data by location (unpublished) | p.20 (PDF 28) | Nonpublic. Could hold trip-distance and duration data for EVs vs fleet. Would require a data request. |
| Ithaca Carshare EV member survey (unpublished) | p.20 (PDF 28) | Nonpublic. Small, self-selected sample. |
| CCETC community interviews (unpublished) | p.5 (PDF 13) | Nonpublic, qualitative. |
| Ridge Road Imports sales log | Table 3 (PDF 19) | Published in full. |
| Ithaca Neighborhood Housing Services AMI limits | p.18 (PDF 26) | Public. |
| AFCU rate sheet | App. B (PDF 46) | Public, dated. |
| "Over 85 ports" (footnote 3; text missing) | PDF 41 | Probably AFDC Station Locator. Public and acquirable via NREL API with dated snapshots. |
| U.S. DOE Alternative Fuels Data Center (AFDC) station map (embedded on dealer website) | p.15 (PDF 23); PDF 41 | Public. |
| Exner 2017 (battery degradation warranties) | Table 4 (PDF 20) | Not local. |
| ABC News / T. Krisher (chip shortage) | fn.1, p.4 (PDF 12) | Not local. |
| Consumer Reports & UCS 2019 "Rev Up EVs"; "Electric Vehicle Ownership: Cost, Attitudes and Behaviors"; Consumer Reports fuel savings ($800-$1,000/yr) | App. D slides (PDF 52-78); App. A EV page text (PDF 40) | National, not local. |
| NYSERDA "Charge Ready NY" publications; U.S. DOE consumer handbooks | p.16 (PDF 24) | Educational. |

---

## 4. Population segmentation and charging access for allocating EVs to buildings

What 24-06 supports (all qualitative, class F):
1. **Home-charging access is the key divider.** People without home charging (implicitly renters and multifamily residents) face a "major" barrier (PDF 14). This supports lower EV propensity and/or more non-home charging for renter and multifamily buildings, but **gives no parameter**.
2. **LMI households are heterogeneous** (PDF 13). Many have no vehicle at all, so vehicle ownership must be modelled before EV share. Carless LMI households reach EVs through carshare and transit, not ownership.
3. **Rural vs City of Ithaca.**
   - Rural LMI residents are car-dependent: nearest bus stop is often more than 5 miles away (interview claim). They do their own maintenance, which makes them wary of EVs, and they have less access to public charging.
   - The downtown DCFC was broken for the whole project, so City-core public fast charging was effectively absent in 2021-2023.
4. **Subsidized / mixed-income multifamily** (INHS 210 Hancock) was chosen to host a carshare EV plus charger. This is a real non-household EV load at a specific residential building.
5. **Students / Cornell.** Only mentioned as outreach venues (Hasbrook Grad Student Resource Fair with Cornell University, 8/23/2022, Table 1; Cornell Cooperative Extension as a partner). **No data on student vehicles or campus charging.**

Relevant context from the other local documents (section 6):
- **Ithaca concentration.**
  - 2015: "70% list Ithaca as the owner's city of residence" (2017 Existing Conditions, PDF 8).
  - 2026 DMV snapshot: ZIP 14850 holds 1,118 of 1,630 Tompkins passenger-class records with fuel_type ELECTRIC (about 69%; see section 6).
  - Caveat: ZIP 14850 covers the City of Ithaca plus much of the Town of Ithaca and nearby areas, so it is not a City boundary.
- **Early multifamily and rental charging existed:** Three Hills Properties rentals at 7 Pheasant Walk, 317 South Aurora St, and Emma's Acres (882 West Dryden Rd, Freeville) had AC Level 2 chargers "primarily for residents" (2017 Existing Conditions, PDF 19). Ithaca College Circle Apartments had a charger that was never activated (PDF 18).
- **Newer multifamily charging:** NYSEG make-ready reportedly funded 24 chargers ($144,000) at an Arnot Realty multifamily building in Ithaca (July 2024). This comes from a search-result snippet; the NYSEG page timed out and was not verified.
- **Cornell campus chargers are permit/paid-parking gated.** 2017: 3 Level 2 at Forest Home garage (permit), 2 at Hoy Road garage (paid) (Existing Conditions, PDF 15). 2025: 10 Level 2 ChargePoint chargers plus one Level 3 at Fleet Services, and a $3.50/hour charging fee from July 1, 2025. The 2025 figures are unverified search snippets; the FCS page returned "Restricted access" to scripted fetch.
- **Student vehicles** registered out of state or at a parental address are not in NYS DMV Tompkins counts. The campus ZIP 14853 shows only 6 passenger EV records. This is an undercount risk for student-heavy buildings (inference, not measured).

---

## 5. Representative measurements (A) vs qualitative/contextual (F)

| Evidence | Source | Class | Note |
|---|---|---|---|
| Barrier list (charging access, awareness, cost, maintenance, rural transit gaps) | 24-06 PDF 13-14 | F | Unreported number of stakeholder interviews |
| Outreach tallies (338,230 exposed; 11,000 engaged; LMI reach estimates) | 24-06 PDF 15-16 | F | Estimates; method unstated; internal inconsistency |
| Used-EV sales log (23 vehicles, days on lot) | 24-06 PDF 19 | F for population inference | Complete, but one dealership |
| Carshare bookings "on trend"; survey feedback | 24-06 PDF 28 | F | No n, no numbers |
| "Over 85 ports" in Tompkins (c. Sept 2023) | 24-06 PDF 41 | F | Footnote source missing; use AFDC directly instead |
| AMI / FPL thresholds; AFCU loan rates | 24-06 PDF 26, 28, 46 | Program parameters (not population measurements) | Accurate as program definitions |
| National commute 30 mi; 95% parked | 24-06 PDF 71 | F | Generic, unsourced, not local |
| Tompkins PEV registrations 2015-2019 (136; 186; 202; 644 = 1.3%) | 2017 ITCTC docs; 2019 GHG inventory | A (administrative census, VIN-decoded) with definitional caveats | Figures conflict (see section 6) |
| NYS DMV open data EV registrations by ZIP (2026) | data.ny.gov 3vp6-cxmr | A for fuel_type=ELECTRIC records | Probable PHEV under-coding; includes registrations expired <2 years |
| 2017 resident survey (n=26) | 2017 Existing Conditions PDF 10, 21-22 | F | Authors state n=26 "prohibits any statistically relevant conclusions" |
| 2015-2016 usage charts for 3 NYSERDA-funded Ithaca stations | 2017 Existing Conditions PDF 16-17 (Figs. 14-15) | Measured, but chart-only and 3 sites: F for population inference | No tabulated values |
| County-fleet separately metered chargers at Whole Health, Brown Rd: 75,760 kWh (2024) | 2024 GHG inventory PDF 12 | Measured annual total, one site: F for population inference | No hourly profile |
| OptimizEV smart-charging pilot (35 Tompkins participants, minute-level data) | Cornell Chronicle 2019; CCE page | Summary only; data nonpublic | Best local residential load-shape lead |

---

## 6. Other local documents found

Classification key:
- **Acquired**: public, downloaded to `data/raw/reports/` or queried and recorded here.
- **Public, not acquired**
- **Public summary only**: underlying data not published.
- **Nonpublic**

| # | Document / dataset | URL | Local quantitative data? | Availability |
|---|---|---|---|---|
| 1 | ITCTC / Energetics / CCCNY, *Tompkins County PEV Infrastructure Plan: Existing Conditions and Best Practices* (June 2017; 34 pp.) | https://www.tompkinscountyny.gov/files/assets/county/v/1/itctc/documents/completed-projects-studies-and-maps/tompkins-evse-existing-conditions-and-best-practices-final.pdf | **Yes** (details after table) | Acquired (`tompkins_evse_existing_conditions_2017.pdf`) |
| 2 | *EV Infrastructure Plan Executive Summary* (June 2017; 8 pp.) | https://www.tompkinscountyny.gov/files/assets/county/v/1/itctc/documents/completed-projects-studies-and-maps/tompkins-county-evse-infrastructure-plan-executive-summary.pdf | **Yes** (details after table) | Acquired (`tompkins_evse_plan_executive_summary_2017.pdf`) |
| 3 | *Charging Station Implementation Strategies* (June 2017; 15 pp.) | https://www.tompkinscountyny.gov/files/assets/county/v/1/itctc/documents/completed-projects-studies-and-maps/tompkins-county-evse-implementation-strategies.pdf | **Some** (details after table) | Acquired (`tompkins_evse_implementation_strategies.pdf`) |
| 4 | *EV Charging Station Site Suitability* (2017) and *Preliminary Engineering and Cost Analysis* (2017); 2-page overview | Links on https://www.tompkinscountyny.gov/All-Departments/Ithaca-Tompkins-County-Transportation-Council/Completed-Projects-Studies-and-Maps (e.g., `.../tompkins-evse-site-suitability-final.pdf`, `.../tompkins-evse-installation-analysis-final.pdf`) | Probably site scores and install costs for 7 sites; not reviewed | Public, not acquired |
| 5 | Tompkins County *2019 Community GHG Emissions and Energy Use Inventory* | https://www.tompkinscountyny.gov/files/assets/county/v/1/planning-amp-sustainability/documents/2019_community_ghg_inventory_report_final.pdf | **Yes** (details after table) | Acquired (`tompkins_2019_community_ghg_inventory.pdf`) |
| 6 | Tompkins County *Government Operations and Community GHG Inventory* (2024 inventory year; PDF created Apr 2026) | https://www.tompkinscountyny.gov/files/assets/county/v/1/planning-amp-sustainability/documents/2024-tompkins-county-ghg-inventory-report_v.final.pdf | **Some** (details after table) | Acquired (`tompkins_2024_ghg_inventory.pdf`) |
| 7 | Earlier County GHG inventory (CCP) | https://www.tompkinscountyny.gov/files/assets/county/v/1/planning-amp-sustainability/documents/5_ccp_emissions_inventory.pdf | Unknown | Public, not acquired |
| 8 | NYS DMV "Electric Vehicle Registrations" open data | https://data.ny.gov/Transportation/Electric-Vehicle-Registrations/3vp6-cxmr (also c9sv-3xr2, without VIN) | **Yes** (details after table) | Acquired (API query results recorded here, not saved as file) |
| 9 | NYSERDA EV Registration Map / EValuateNY | https://www.nyserda.ny.gov/All-Programs/Drive-Clean-Rebate-For-Electric-Cars-Program/Rebate-Data/Map-of-EV-Registrations | County/ZIP EV registrations (derived from DMV) | Public, not acquired |
| 10 | NYSEG + Cornell (Bitar) **OptimizEV** managed-charging pilot, Energy Smart Community | https://news.cornell.edu/stories/2019/11/cornell-research-drives-nyseg-electric-car-charging-pilot ; https://ccetompkins.org/energy/energy-smart-community-tompkins/optimizev | 35 Tompkins participants for one year; smart chargers reported usage "minute by minute" (per Cornell Chronicle summary). No data or report linked. | Public summary only (data nonpublic) |
| 11 | NYSEG/RG&E EV Managed Charging Implementation Plan (NY DPS filing) | https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B60EEB894-0000-CB12-883C-4C3E5137E61C%7D | Utility-wide program design; Tompkins-specific data unknown | Public, not acquired |
| 12 | NYSEG EV Make-Ready Program; Arnot Realty multifamily project | https://www.nyseg.com/w/nyseg-helps-multi-family-building-install-ev-chargers ; https://jointutilitiesofny.org/ev/make-ready | Snippet only: 24 chargers, $144,000, multifamily building in Ithaca, July 2024 (unverified, page timed out). Snippet also says NYSEG stops taking new make-ready applications after April 22, 2026 under a March 23, 2026 PSC order (unverified). | Public summary only |
| 13 | Cornell FCS "Electric and Green Vehicle Parking" and "New EV charging plan" (May 2025) | https://fcs.cornell.edu/departments/transportation-delivery-services/parking/electric-green-vehicle-parking ; https://fcs.cornell.edu/announcements/2025-05-16/new-ev-charging-plan-campus | Charger count by location and fee (snippets only; pages returned 403 / "Restricted access"). No session or kWh data found. | Public summary only; ChargePoint session data nonpublic |
| 14 | Cornell Chronicle: first Level 3 fast charger on campus (Mar 2025); Abruña Energy Initiative EV fleet page | https://news.cornell.edu/stories/2025/03/first-level-3-ev-fast-charging-station-opens-campus ; https://abrunainitiative.cornell.edu/projects/fleet/ | No quantitative data on the fleet page (fetched) | Public summary only |
| 15 | City of Ithaca Green New Deal resolution (2019) and GND page | https://www.cityofithacany.gov/DocumentCenter/View/11052/Ithaca-Green-New-Deal-Resolution-FINAL-cert ; https://www.cityofithacany.gov/827/Green-New-Deal | Goals only: carbon neutrality by 2030; reduce city fleet emissions 50% by 2025. No EV or charger usage data found. | Public (goals); no data found |
| 16 | City of Ithaca garage chargers (Seneca, Green, Cayuga St garages) | https://www.cityofithacany.gov/708/Parking-News ; https://www.14850.com/083037862-ev-charging-ithaca/ | Locations only; **no published usage report found** | Public summary only |
| 17 | Tompkins Weekly: county federal earmark for solar portable EV chargers | https://tompkinsweekly.com/articles/county-receives-federal-grant-for-electric-vehicle-charging-stations/ | Snippet: $128,000; candidate sites 779 Warren Rd (Sheriff), airport, 170 Bostwick Rd (page 403; unverified) | Public summary only |
| 18 | Ithaca Carshare EV pages (grant for EVs) | https://www.ithacacarshare.org/ithaca-carshare-wins-grant-to-purchase-electric-vehicles/ ; https://www.ithacacarshare.org/cars-locations/ | Snippet: 9 EVs and 9 chargers via a shared NYSERDA grant. Vehicle home locations are listed on the site. Booking data nonpublic. | Public summary only |
| 19 | 2018 press: NYSERDA completion of 11 charging stations in Tompkins ("EV Model County") | https://ithacavoice.org/2018/07/nyserda-announces-completion-11-electric-vehicle-charging-stations-tompkins/ ; https://www.ithaca.com/news/tompkins_county/tompkins-county-now-hosting-electric-vehicle-charging-stations/article_80df14aa-83a5-11e8-a1f2-2f058b1d9980.html | Station count (11) | Public summary only |
| 20 | Tompkins County Energy Roadmap (2015 presentation) | https://nysacc.org/wp-content/uploads/Tompkins-County-Energy-Roadmap-Katie-Borgella.pdf | 2050 **scenario assumptions** (e.g., "Mixed" scenario with 50% EV/alt-mode chance per search snippet), not measurements | Public, not acquired |
| 21 | ITCTC 2045 Long Range Transportation Plan | https://www.tompkinscountyny.gov/All-Departments/Ithaca-Tompkins-County-Transportation-Council/2045-Long-Range-Transportation-Plan | Not reviewed for EV/commute data (LRTPs typically carry commute-mode / travel data) | Public, not acquired |
| 22 | AFDC Station Locator (NREL API) | https://afdc.energy.gov/stations | Current and historical public charger inventory by site, ports and network | Public, acquirable (not acquired here) |
| 23 | NYSERDA statewide EVSE usage reports (2014 Q1 EVSE Use Report; 2016 EVSE annual report; Report 22-03 *Cost and Usage Trends for EV Chargers*) | https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/EV-Charging-Station-Data/2014-EVSE-Use-Report-Q1.pdf ; https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/Research/Transportation/22-03-Cost-and-Usage-Trends-for-EV-Chargers.pdf | Statewide. The early reports **may** contain per-site data for the 2014 NYSERDA-funded Ithaca stations (Ithaca Yards, Taitem, Cayuga Medical Center). Not verified. | `nyserda_22-03.pdf` and `nyserda_2016_EVSE_annual_report.pdf` already present in `data/raw/reports/` (placed by other work; not reviewed here); 2014 Q1 not acquired |
| 24 | CCE Tompkins EV page; Get Your GreenBack "EV Tompkins" | https://energy.ccetompkins.org/energy-solutions/electric-vehicles/ ; https://www.getyourgreenbacktompkins.org/ev-tompkins | None (fetched CCE page: no numbers) | Public, no data |
| 25 | Third-party locators (Felt map "30 stations"; evstationslocal "67 within 10 mi") | https://felt.com/explore/electric-vehicle-charging-stations-tompkins-county-new-york ; https://evstationslocal.com/states/new-york/ithaca/ | Counts in snippets; undated, unknown method | Public; low reliability (do not use) |

**Details for rows 1-3, 5, 6 and 8 (Yes / Some):**

**1. Existing Conditions and Best Practices (2017)**
- 136 PEVs registered as of 12/31/2015, 0.27% of registered vehicles (NYS 0.16%). Method: VIN-decoded DMV data (PDF 7-8).
- 70% list Ithaca as city of residence (PDF 8).
- Make/model and model-year splits (PDF 7).
- Charger inventory Table 1: 1 DCFC port, 1 Tesla Level 2, 20 AC Level 2 ports, 11 AC Level 1 ports (PDF 13-14).
- Cumulative new-user and monthly kWh charts for 3 NYSERDA stations, Jan 2015-Mar 2016. Chart-only, no values (PDF 16-17).
- Tesla charger at William Henry Miller Inn: "5 to 10 users per month" per staff (PDF 17).
- Survey n=26: venue rankings and concerns (PDF 10, 21-22).
- Also cites "130 PEVs" (PDF 21).

**2. Executive Summary (2017)**
- "202 EVs registered in Tompkins County as of March 31, 2017", 0.42% of vehicles, second highest in the state; PHEVs outnumber BEVs more than 2:1 (PDF 3).
- Statewide context: about 7.7 kWh per public charge event and 2.5 events per port per week (fn., PDF 6).

**3. Implementation Strategies (2017)**
- "As of January 2017 there were 186 registered EVs and 10 public AC Level 2 charging stations" (p.9, PDF 12).
- Average port has "about 100 charge events per year" (NYSERDA program context; p.2, PDF 5).
- Proposed new sites map, mostly downtown garages (p.11, PDF 14).

**5. 2019 Community GHG Inventory**
- "644 EVs registered in the County as of December 31, 2019, which represents 1.3% of all registered vehicles" (PDF 16).
- "136 EVs registered in 2014" (PDF 32).
- About 673 million vehicle-miles traveled in 2019, partly based on 2014 estimates (PDF 16).
- Transportation is 34% of community GHG emissions (PDF 16).

**6. 2024 GHG Inventory (Government Operations and Community)**
- County government fleet: "just over a quarter ... electrified". Most County chargers are not separately metered; Whole Health (Brown Rd) chargers are separately metered at 75,760 kWh in 2024 (PDF 12).
- Community transportation energy excludes EV electricity: "no sources found that show electricity consumed by electric vehicle chargers separate from building consumption" (PDF 31).

**8. NYS DMV EV registrations (queried 2026-09-14; dataset rowsUpdatedAt 2026-09-02 UTC)**
- county='TOMPKINS', fuel_type ELECTRIC (the only fuel type in this dataset):
  - PAS (passenger) = **1,630**
  - PSD = 66, SRF = 48, COM = 44, others small
- PAS by ZIP:
  - 14850 = 1,118
  - 14886 (Trumansburg) = 102
  - 13068 (Freeville) = 80
  - 14882 (Lansing) = 60
  - 14817 (Brooktondale) = 58
  - 14867 (Newfield) = 52
  - 13073 (Groton) = 40
  - 13053 (Dryden) = 36
  - 12449 = 35 (a non-Tompkins ZIP; data-quality flag)
  - 14853 (Cornell) = 6
  - remainder small
- Query: `https://data.ny.gov/resource/3vp6-cxmr.json?$select=zip,count(*)&$where=county='TOMPKINS' AND registration_class='PAS'&$group=zip`

**Inconsistencies to flag across local docs:**
- 136 PEVs is dated 12/31/2015 in the 2017 Existing Conditions report but "2014" in the 2019 GHG inventory.
- The 2017 documents give 130 (Existing Conditions PDF 21), 136 (12/2015), 186 (1/2017) and 202 (3/2017).
- The 2017 report warns that DMV "fuel type designation is not accurate" and used VIN decoding instead (PDF 7). The 2026 open-data "ELECTRIC" count therefore likely undercounts PHEVs and is **not directly comparable** to the 2015-2019 VIN-decoded PEV counts. This is an inference that needs checking against VIN decoding or NYSERDA EValuateNY.

---

## 7. Modeling implications for a building x hour EV load model (Ithaca)

1. **Do not take any numeric parameters from 24-06.** It has no EV stock, home-charging share, charging profiles, trip distances, or representative survey results. Use it only as qualitative support for model structure.
2. **Stock control totals should come from DMV registration data (class A)**, not from 24-06.
   - Use ZIP-level counts from data.ny.gov (2026 snapshot: 1,630 passenger EV-coded records countywide, 1,118 in ZIP 14850).
   - Harmonize with VIN decoding to add PHEVs, or with NYSERDA EValuateNY.
   - Build a ZIP-to-parcel/building crosswalk; 14850 is not the City boundary.
   - Records whose registrations expired within the last 2 years must be filtered out using `reg_expiration_date`.
3. **Segment buildings by home-charging access**: single-family owner-occupied, small rental, large multifamily, subsidized/LMI multifamily, and student housing.
   - 24-06 and the 2017 documents support the direction of the effect: limited home charging suppresses EV ownership and moves charging to public or workplace sites.
   - The size of the effect must come from elsewhere: ACS tenure/structure-type data, NY Drive Clean Rebate surveys already in `data/raw/reports/`, or national home-charging-access studies.
4. **Known point loads to geocode directly.** These buildings have documented chargers:
   - 210 Hancock St (INHS; carshare EV)
   - 1st & Adams St carshare location
   - Three Hills Properties rentals (7 Pheasant Walk, 317 S Aurora St, 882 W Dryden Rd)
   - Arnot Realty multifamily (24 chargers, unverified)
   - Cornell garages and lots (Forest Home, Hoy Rd, Booth, Hollister, Fleet Services Level 3)
   - City garages (Seneca, Green, Cayuga St)
   - Cayuga Medical Center, Ithaca Yards, Taitem, dealerships
   - County Whole Health, Brown Rd (75,760 kWh in 2024; one annual calibration point, no hourly shape)
   - Get a dated inventory from the AFDC API instead of the unsourced "over 85 ports" figure.
5. **Rural vs City.**
   - EV registrations are strongly concentrated in the Ithaca ZIP (about 69% in 2026; 70% "Ithaca" in 2015).
   - Rural residents are car-dependent and poorly served by transit (qualitative), so per-vehicle daily kWh may be higher outside the City.
   - There are no local trip-distance data. Use LEHD LODES and ACS commute data, or NHTS, for distance distributions, not the generic "30 miles" slide.
6. **Students / Cornell.** DMV home-address counts miss out-of-state student vehicles (ZIP 14853 shows 6). Campus charging is permit- or fee-gated, with a $3.50/hour charging fee from July 2025 (unverified snippet), which likely shortens dwell and reduces daytime campus load. Treat student-housing EV propensity as a separate, low-confidence parameter.
7. **Public DCFC reliability.** The only downtown DCFC was out of service for 2021-2023 (24-06 PDF 26). Model public fast-charging availability explicitly as time-varying; do not assume an always-available public network.
8. **Hourly shapes.**
   - No public local hourly charging data was found.
   - The best local lead is **OptimizEV** (NYSEG + Cornell; 35 Tompkins households; minute-level smart-charger data). Consider a data request to NYSEG or Prof. Eilyan Bitar.
   - Other possible sources: ChargePoint session exports held by site hosts (City of Ithaca, Cornell, Cayuga Medical Center) and Ithaca Carshare booking logs.
   - Until then, use statewide or national load shapes (e.g., NYSERDA 22-03 in `data/raw/reports/`) and label them as non-local.
9. **LMI and carshare EVs** are few (2 under 24-06; 9 more planned per Carshare). Their load is negligible in aggregate but should be placed at their host buildings if the model resolves individual sites.
10. **Evidence tagging in the model.** Parameters from 24-06 should be tagged class F: qualitative, direction-only. DMV counts are class A. Single-site metered totals (Whole Health) and chart-only station usage (2015-2016) should be tagged as measured but non-representative.
