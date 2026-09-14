# Source notes: NYSERDA Drive Clean Rebate surveys and consumer reports

Compiled 2026-09-14. Landing page:
<https://www.nyserda.ny.gov/All-Programs/Drive-Clean-Rebate-For-Electric-Cars-Program/Rebate-Data>
(fetched with `curl -A "Mozilla/5.0"`; every PDF linked from it is listed below).
Local copies are in `data/raw/reports/` (git-ignored via `data/raw/*`).

All documents were prepared for NYSERDA by the Center for Sustainable Energy (CSE), the program administrator.

## Conventions

- **[T]** means the number is stated in the report text. **[F]** means I read it off a data label in a chart image. **[F-derived]** means I worked it out from chart labels, for example as 100% minus the labelled segments. **[D]** means I computed it myself, and the method is given.
- Page citations use the printed page number and then the PDF page, e.g. "p. 19 / PDF 27". In the two survey reports, printed page 1 is PDF page 9. Slide decks give only the PDF (slide) page.
- **Evidence class B** means a direct New York observation. There are two kinds:
  - **B-self-report:** survey answers given by rebate recipients (the primary driver). These are not metered or logged.
  - **B-admin:** counts taken from program application records.
- All survey percentages are **weighted** (raking) unless stated otherwise.

---

## 1. Inventory

| # | Title (as on landing page) | Year / date | Local file / URL (prefix `https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Programs/Drive-Clean-NY/`) | Type, pages | What it covers | Raw microdata public? |
|---|---|---|---|---|---|---|
| 1 | NYSERDA Drive Clean Rebate **Ownership Survey, 2024 Results** | Vehicles acquired CY2024; report Mar 2026 | `Drive-Clean-Rebate-Ownership-Survey-2024-Results.pdf` | Report, 52 pp | Survey about 1 year after purchase: miles driven, trip use, charging location and frequency, home charging method, workplace access, perceptions of public charging, demographics, DAC split, full questionnaire | **No** (report says "The analysis will only use summary level data") |
| 2 | NYSERDA Drive Clean Rebate **Ownership Survey, 2023 Results** | Vehicles acquired CY2023; report 2025 | `NYSERDA-Drive-Clean-Rebate-Ownership-Survey-2023-Results.pdf` | Report, 51 pp | Same instrument as #1 for 2023 vehicles | No |
| 3 | NYSERDA Drive Clean Rebate **Adoption Survey, 2025 Results** | Vehicles acquired CY2025; report May 2026 | `NYSERDA-Drive-Clean-Rebate-Adoption-Survey-2025-Results.pdf` | Report, 55 pp | Survey 1 to 3 weeks after rebate approval: purchase motives, replaced vehicle, rebate influence, dealer experience, home charging (yes/planned), charger type used or planned, workplace access, demographics, DAC | No |
| 4 | NYSERDA Drive Clean Rebate **Adoption Survey, 2024 Results** | Vehicles acquired CY2024; report 2025 | `NYSERDA-Drive-Clean-Rebate-Adoption-Survey-2024-Results.pdf` | Report, 55 pp | Same instrument as #3 for 2024 vehicles | No |
| 5 | Rebate Influence through 2024 and Designing for Cost Effectiveness | Jun 2025 | `Rebate-Influence-through-2024-and-Designing-for-Cost-Effectiveness.pdf` | Slide deck, 34 pp | Rebate importance and "essentiality" (free-ridership) by rebate amount, income, MSRP; built on adoption-survey data | No |
| 6 | Rebate Influence through 2023 and Designing for Cost-Effectiveness | 2025 | `Rebate-Influence-through-2023-and-Designing-for-Cost-Effectiveness.pdf` | Slide deck, 32 pp | Same for 2023 | No |
| 7 | NY Drive Clean Rebated Vehicle Characteristics through 2024 | Apr 2025 | `NY-Drive-Clean-Rebated-Vehicle-Characteristics-through-2024.pdf` | Slide deck, 22 pp | Rebates by make/model, buy vs lease, rebate amount, MSRP; **top counties and REDC regions; urban vs rural** (from application records) | Application-level data public: NY Open Data `thd2-fu8y` |
| 8 | NY Drive Clean Rebated Vehicle Characteristics through 2023 | 2025 | `NY-Drive-Clean-Rebated-Vehicle-Characteristics-through-2023.pdf` | Slide deck, 20 pp | Same for 2023 | Same as #7 |
| 9 | NY Drive Clean Rebate Vehicle Replacement through 2024 | Jul 2025 | `NY-Drive-Clean-Rebate-Vehicle-Replacement-through-2024.pdf` | Slide deck, 21 pp | Replacement rate over time, fuel type and model year of replaced vehicles (adoption-survey data) | No |
| 10 | NY Drive Clean Rebate Vehicle Replacement through 2023 | 2025 | `NY-Drive-Clean-Rebate-Vehicle-Replacement-through-2023.pdf` | Slide deck, 16 pp | Same for 2023 | No |
| 11 | NY Drive Clean Rebate Consumer Characteristics & Equity Metrics through 2024 | Aug 2025 | `Drive-Clean-Rebate-Consumer-Characteristics-and-Equity-Metrics-Through-2024.pdf` | Slide deck, 33 pp | Income, race, age, tenure, education and gender of recipients compared with NY new-vehicle buyers (NVES 2022) and the NY population (ACS PUMS 2019–2023); **program share of the NY EV market** | No |
| 12 | NY Drive Clean Rebate Consumer Characteristics & Equity Metrics thru 2023 | 2025 | `NY-Drive-Clean-Rebate-Consumer-Characteristics--Equity-Metrics-thru-2023.pdf` | Slide deck, 27 pp | Same for 2023 | No |

Notes on the inventory:

- **No 2025 Ownership Survey** (2025 vehicles) was linked as of 2026-09-14. On the normal schedule it would cover invitations sent through about Q1 2027.
- **Microdata:** a search of the data.ny.gov catalog for "drive clean" returned only `thd2-fu8y`, "NYSERDA Electric Vehicle Drive Clean Rebate Data: Beginning 2017", last updated 2026-09-01. That dataset holds application records, not survey responses. I found no public survey microdata. Some CSE journal papers cited in the decks mention "open-access data-summary" supplements; these are summaries, not respondent-level data.
- The same landing page also links interactive dashboards: Rebate Stats, Rebates by Geography, EV Registration Map, and EV/charging-station data. These are not PDFs and are not covered here.
- Rebate design since 2021-07-01 [T, deck #7 PDF 21]:
  - $2,000 for a range of at least 200 e-miles
  - $1,000 for at least 40 e-miles
  - $500 for under 40 e-miles, or for any vehicle with MSRP above $42,000
  - Paid at point of sale, for new vehicles only

---

## 2. Survey design

### 2a. 2024 Ownership Survey (report #1)

| Item | Value | Source |
|---|---|---|
| Sampling frame | Individual Drive Clean rebate recipients (purchasers or lessees of eligible **new** BEVs or PHEVs from participating dealers) whose vehicle was acquired 2024-01-01 to 2024-12-31. Businesses and government entities are not "individual participants". | [T] p. 1 / PDF 9; endnote 3, PDF 52 |
| Mode | Email invitation, web questionnaire, voluntary. A census of all participants is invited; there is no sampling. | [T] p. 1 |
| Timing | Invited about 1 year after acquisition, in quarterly batches. Time owned at survey: **9.4–14.1 months**. | [T] p. 1; endnotes 1 and 4 |
| Administration dates | 2025-02-04 to 2025-10-30. Responses received 2025-02-04 to 2026-02-07. | [T] Table 1, p. 1 |
| Invited | **46,074** | [T] p. 1 |
| Responses | 4,913 (10.7%). 44 disqualified because the household no longer had the rebated car. | [T] p. 1 |
| Valid completes | **4,869 (10.6%)** | [T] p. 2 / PDF 10 |
| Population represented | N = **45,958**. 116 recipients were excluded because some weighting stratum had no respondents. | [T] Table 2, p. 2 |
| Eligibility / screen | Household still has the rebated car. The survey asks whether the respondent is the primary driver and asks that the primary driver complete it, but not being the primary driver is **not** listed as a disqualifier in this survey. | [T] questionnaire, PDF 39–40 |
| Weighting | Iterative proportional fitting (raking) on **car model, purchase vs lease, county, and technology (BEV/PHEV)**. Tests use Rao-Scott chi-square with Holm-Bonferroni correction. Results are shown by technology only where the BEV/PHEV difference is significant. | [T] p. 2 |
| Margins of error | **Not reported.** For comparison, a simple-random-sample ±95% half-width at n = 4,869 and p = 0.5 is about **±1.4 percentage points** [D: 1.96·√(0.25/4869)]. The true error is larger because of the weighting design effect (not reported) and item nonresponse (item n values run from 3,533 to 4,862). Subgroup items such as workplace charging frequency (n = 912) are much less precise. Nonresponse bias is not quantified. | [D] |
| BEV/PHEV split | **66% BEV / 34% PHEV** (Fig. 1). Text: "two-thirds … a third". | [F] p. 3 / PDF 11 |
| BEV share by survey year | 2017–18: 28%; 2018–19: 44%; 2020: 69%; 2021: 58%; 2022: 73%; 2023: 70%; 2024: 66% | [F] Fig. 2, p. 3 |
| Geography reported | **Statewide only.** County is used for weighting, but no county, REDC or regional (Southern Tier, Central NY, Finger Lakes) breakdown is reported, and there is no urban/rural split. The only sub-state split is **DAC vs non-DAC**: 14% of respondents and 16% of 2024 participants live in a DAC. The questionnaire collects workplace ZIP, but it is not reported. | [T] pp. 24–29 |

### 2b. 2025 Adoption Survey (report #3, the latest adoption survey)

| Item | Value | Source |
|---|---|---|
| Sampling frame | Individual rebate recipients with vehicles acquired 2025-01-01 to 2025-12-31. Businesses and government entities excluded. | [T] p. 1 / PDF 9; endnotes 1–2 |
| Timing | Rolling. Email invitation **about 1–3 weeks after rebate approval**, so charging questions record early or **planned** behavior. | [T] p. 1 |
| Invited | **38,300** | [T] p. 1 |
| Responses | 4,492 (11.7%). Completed 2025-02-11 to 2026-03-02. | [T] p. 1 |
| Disqualified | 131 (vehicle mainly for commercial use, or respondent not the primary driver) | [T] p. 1 |
| Valid completes | **4,361 (11.4%)** | [T] p. 1; Table 1, p. 2 |
| Population represented | N = **38,177** (123 excluded for empty strata) | [T] Table 1, p. 2 |
| Weighting | Raking on rebated car model, purchase vs lease, county, and technology. Rao-Scott plus Holm-Bonferroni. Only whole distributions are tested, not individual response values. | [T] pp. 1–2 |
| Margins of error | Not reported. SRS approximation at n = 4,361: about **±1.5 pp** [D]. Same caveats as 2a. | [D] |
| BEV/PHEV split | **76% BEV / 24% PHEV**. For 2024 vehicles it was 65/35. | [T] p. 3 / PDF 11 |
| Geography | **Statewide only**, plus DAC vs non-DAC (16% of participants and 14% of respondents in a DAC). No county or regional results. | [T] p. 20 |

### 2c. Comparison designs (for trend context)

- **2023 Ownership Survey (#2):** 46,497 invited; 6,615 responses (14%); **6,542 valid (14%)**. Administered 2024-02-13 to 2024-12-02 [T] pp. 1–2 / PDF 10–11. BEV/PHEV split 70/30 [T, #1 p. 3].
- **2024 Adoption Survey (#4):** 42,498 invited; 5,430 responses; **5,292 valid (12%)**; completed 2024-01-30 to 2025-03-05; BEV/PHEV 65/35 [T] ES-1 and p. 1 / PDF 8–9.
- **CSE decks (#5, #9, #11)** for 2024 vehicles use "5,593 survey responses weighted to represent 45,443 program participants" [T, #11 PDF 3]. These are adoption-survey data with a different cut-off, so the counts do not match #4.

---

## 3. Quantitative findings relevant to modeling

Unless noted, figures come from the **2024 Ownership Survey (#1)** for CY2024 vehicles. Page numbers are printed page / PDF page. All values are B-self-report and weighted.

### 3.1 Driving

| Parameter | BEV | PHEV | All | Type | Page |
|---|---|---|---|---|---|
| Self-reported **miles per day** (mean) | **33** | **30** | — | [T] | p. 9 / PDF 17. Significant, endnote 12. |
| **Total miles since acquisition** (mean; the report treats this as approximately annual mileage, over 9.4–14.1 months of ownership) | **10,670** | **10,082** | — | [F] Fig. 11 and body text | p. 10 / PDF 18; text p. 9 |
| Same, as stated in Executive Summary | 10,674 | 10,097 | — | [T] | ES-1 / PDF 8. **Inconsistent** with body by 4 to 15 miles. |
| 2023 Ownership Survey comparison | 12,056 mi; 41 mi/day | 10,606 mi; 30 mi/day | — | [T] | #2 ES-1 and p. 9 |
| Commute all the way: daily/almost daily; few times per week; about once per week; few times per month or less; never | — | — | 57 / 14 / 3 / 8 / 18 % (n = 4,112). Text: 71% at least a few times a week. | [F] Fig. 12; [T] 71% | p. 10 |
| Partial commute (same scale) | — | — | 20 / 9 / 3 / 7 / 60 % (n = 3,533) | [F] Fig. 13 | p. 11 |
| Local errands (under 10 mi) | — | — | 59 / 31 / 6 / 4 / 0.8 % (n = 4,817) | [F] Fig. 14 | p. 11 |
| Long trips (over 50 mi from home) | — | — | 7 / 6 / 13 / 64 / 9 % (n = 4,768) | [F] Fig. 15 | p. 12 |
| Ride-hailing (Uber/Lyft) | — | — | 2 / 1 / 0.6 / 3 / 94 % | [F] Fig. 16 | p. 12 |
| **PHEV electric share of miles (eVMT)** | — | **asked, not reported** | — | — | Questionnaire PDF 43 |
| EV share of household driving | not asked or reported | | | | |
| **Number of household vehicles** | **Asked** (ownership A.3 counts by fuel type; adoption Q5 total cars) **but not reported** in either report | | | | PDF 40; #3 PDF 41 |

### 3.2 Housing and demographics

| Parameter | Value | Type | Page |
|---|---|---|---|
| Tenure | Own 85%, rent 12%, neither 2% (n = 4,712; no BEV/PHEV difference) | [F] Fig. 8; [T] 85% | p. 8 / PDF 16 |
| Residence type | Detached 78%, apartment/condo 11%, attached (townhome/duplex/triplex) 10%, other 1% (n = 4,709) | [F] Fig. 9; [T] 78% | p. 8 |
| Residence type, **inside DAC** vs outside | Detached 54 vs 82%; apt/condo 28 vs 8%; attached 15 vs 9%; other 4 vs 0.7% | [F] Fig. 36 | p. 28 / PDF 36 |
| Solar at residence | BEV: 21% have, 29% considering, 50% no plans. PHEV: 15 / 24 / 61. Overall 19%. | [F] Fig. 10; [T] 19%, 21 vs 15% | pp. 8–9 |
| Education | HS or less 6%, some college 11%, associate 8%, bachelor's 36%, graduate 40%. Bachelor's or higher 76%. | [F] Fig. 3; [T] 76% | p. 5 |
| Household income | <$25k 1%; $25–50k 4%; $50–75k 8%; $75–100k 11%; $100–150k 21%; $150–200k 17%; $200–250k 13%; $250–300k 8%; $300–350k 4%; $350–400k 3%; ≥$400k 11% (n = 4,008). $100k or more: 77%. | [F] Fig. 4; [T] 77% | p. 5 |
| Age (BEV / PHEV) | 16–29: 3/3; 30–39: 16/12; 40–49: 29/23; 50–59: 24/26; 60–69: 17/19; 70–79: 10/14; 80+: 2/3 (%). Age 40+ overall: 83%. | [F] Fig. 5; [T] 83% | p. 6 |
| Gender | 69% male. Female: BEV 24%, PHEV 42%. | [T] | p. 6 |
| Race | 75% solely white. 9% Latino/Hispanic. | [T] | p. 7 |
| Comparison with NY new-car buyers (NVES 2022) | Male 69 vs 55; solely white 75 vs 76; age 40+ 83 vs 76; bachelor's+ 76 vs 64; income $100k+ 77 vs 55; own home 85 vs 77 (%) | [T] Table 3 | p. 4 / PDF 12 |
| **2025 Adoption Survey (#3)** | Own 84% / rent 13% / neither 3%. Detached 77%, apt/condo 13%, attached 10%, other 0.8%. 70% male. 74% bachelor's+. 49% income below $150k. 75% white. 10% Hispanic. | [T] 84, 77, 70, 74, 49, 75, 10; [F] remaining shares, Figs. 18–19 | pp. 15–17 / PDF 23–25 |
| 2025 Adoption income distribution | <$25k 1; $25–50k 4; $50–75k 9; $75–100k 12; $100–150k 23; $150–200k 16; $200–300k 18; $300–400k 7; ≥$400k 10 (%) | [F] Fig. 24 | p. 19 / PDF 27 |
| 2025 Adoption, DAC vs non-DAC residence | Detached 59 vs 79; apt/condo 24 vs 11; attached 16 vs 9 (%) | [F] Fig. 29 | p. 22 / PDF 30 |

### 3.3 Charging (2024 Ownership Survey)

**Workplace charging access.** Question shown only to respondents who do not say "I don't work" or "I work at home" (n = 3,792). 23% overall have access [T].

| | Yes, free | Yes, must pay | No | Don't know |
|---|---|---|---|---|
| BEV | 11% | 13% | 70% | 6% |
| PHEV | 10% | 9% | 73% | 8% |

[F] Fig. 23, p. 18 / PDF 26. Of those with on-site access, 66% of BEV and 63% of PHEV respondents charge there at least occasionally [T].

**Charging frequency by location.** [F] Fig. 24, p. 19 / PDF 27. Columns: daily or almost daily / a few times per week / about once per week / a few times per month or less / never.

| Location | Tech | Daily | Few/wk | ~1/wk | Few/mo or less | Never | Notes |
|---|---|---|---|---|---|---|---|
| **Home** (n = 4,849) | BEV | **34** | **28** | **20** | 7 | **11** | Text: 34% daily; 62% few/wk or daily; 11% never |
| | PHEV | **51** | 15 | ~5 [F-derived, unlabeled] | 10 | **19** | Text: 51% daily; 19% never |
| **On-site at work** (only those with access, n = 912) | BEV | 9 | 16 | 16 | 24 | 34 | |
| | PHEV | 19 | 17 | 8 | 19 | 37 | |
| **Where I park during work, off-site** (n = 3,429) | BEV | small, unlabeled | | | 5 (label) | 86 | No BEV/PHEV difference |
| | PHEV | small, unlabeled | | | | 88 | |
| **Public stations** (n = 4,794) | BEV | ~2 [F-derived] | 5 | 9 | **57** | **27** | Text: 73% use at least occasionally |
| | PHEV | unlabeled, about 4 in total | | | 28 | **68** | Text: 32% at least occasionally |
| **Other** (n = 4,234) | BEV | small | | | 14 | 81 | Write-ins (n = 584) include public stations, friends' or relatives' homes, businesses/malls, so public use is probably **under-counted** [T] |
| | PHEV | small | | | 8 | 90 | |

Public charging inconsistency within report #1:
- The Executive Summary (ES-1) says PHEV "never use public chargers" rose from 54% to **60%**.
- Fig. 24 and the p. 19 text give **68% never** (32% use at least occasionally).
- 60% was the **2023** value (#2 ES-2), so ES-1 appears to repeat last year's number.
- For modeling, use the figure (68%).
- The Discussion (p. 30) describes the 73% / 32% as "at least a few times a month". The figure labels them as "at least occasionally" (not "never").

**Home charging method.** Multi-select, asked of anyone charging at home at least a few times a month or more (n = 4,288). [F] Fig. 25, p. 20 / PDF 28. Text states 120V 68 vs 14 and L2 58 vs 24.

| Method | BEV | PHEV |
|---|---|---|
| Level 2 (240V) charging station | **58%** | **24%** |
| 240V outlet, direct plug (e.g., dryer outlet) | 27% | 11% |
| Level 1 (120V) charging station | 8% | 7% |
| 120V outlet, direct plug | **14%** | **68%** |

Answers are multi-select, so shares do not sum to 100%. Taken together, **BEV: about 58–85% have some 240V access** [D: lower bound max(58, 27); upper bound 58 + 27 if no overlap]. The report does not publish the overlap.

**Time of day, TOU and managed charging, DCFC vs L2 public, session energy or kWh, charging duration:** **not asked** in either questionnaire, so no numbers exist. The ownership instrument has no rate or TOU question. The adoption instrument only asks how important "special electricity rates for charging at home" were to the purchase decision, and that item is not reported in the 2025 text.

**Public charging perceptions** (context for model parameters):
- 62% disagree that "there are enough public chargers" [T p. 20]. The text typo says "Seventy percent (62%)". The Discussion says only 15% agree.
- 38% agree public stations are often in use by others [T p. 24].
- 23% agree stations are often not working, 29% disagree [T p. 24].
- 22% agree stations are "in the places where I need them" [T p. 22].
- Endnote 13 (from the NYSERDA registration map, Feb 2026): **18.5 EVs per public L2 port; 65.77 BEVs per DCFC port** in NYS. This is B-admin, second-hand.

**Trend: 2023 → 2024 Ownership** [T, #1 ES-1 and pp. 19, 30; #2 pp. 18–20]:
- Home charging daily: BEV 37% → 34%; PHEV 56% → 51%
- BEV home charging few/wk or daily: 64% → 62%
- Never charge at home: BEV 14% → 11%; PHEV 15% → 19%
- Any public charging use: BEV 77% → 73%; PHEV 40% → 32%
- Workplace access: 22% → 23%
- BEV home L2 station: 59% → 58%; PHEV home 120V outlet: 64% → 68%

### 3.4 Charging (2025 Adoption Survey, 1–3 weeks after approval)

| Parameter | Value | Type | Page |
|---|---|---|---|
| Charge at home | **Yes 82%**; no but planning 9%; no, no plans 9% (n = 4,331; no BEV/PHEV difference). 2024 adoption survey: 78% yes, 11% planning. | [T] 82, 9; [F] 9 no plans | p. 13 / PDF 21–22; #4 p. 12 |
| Home charging method, current or planned (multi-select, n = 3,965), BEV / PHEV | 120V outlet 22 / 70; L2 station 62 / 23; 240V outlet 21 / 9; L1 station 7 / 8 (%) | [F] Fig. 17 | p. 15 / PDF 23 |
| Access to workplace charging (yes / no / don't know) | BEV 35 / 58 / 6; PHEV 28 / 63 / 9 (%) (n = 3,030) | [F] Fig. 16 | p. 14 / PDF 22 |
| Access to charging **near** workplace | BEV 61 / 24 / 15; PHEV 34 / 37 / 29 (%) (n = 3,071) | [F] Fig. 16 | p. 14 |

The adoption workplace-access question uses a different wording and base from the ownership one ("Not applicable" is allowed), so its 28–35% "yes" is not directly comparable with the ownership survey's 23%.

### 3.5 Replaced vehicle and fleet change

| Parameter | Value | Type | Page |
|---|---|---|---|
| 2025: EV replaces a household car / adds to fleet / first or only car | BEV 79 / 16 / 5; PHEV 90 / 7 / 3 (%). Overall: 82% replace, 14% add. | [F] Fig. 2; [T] 82, 14 | #3 pp. 3–4 / PDF 11–12 |
| 2025: DAC vs non-DAC (replace / add / first or only) | 75 / 14 / 11 vs 83 / 14 / 3 (%) | [F] Fig. 30 | #3 p. 23 / PDF 31 |
| 2025: fuel type of replaced car (BEV / PHEV buyers) | Gasoline 56 / 53; BEV 34 / 4; conventional hybrid 5 / 11; PHEV 4 / 32; diesel 0.3 / 0.6 (%). Overall: 55% gasoline, 6% hybrid. | [F] Fig. 3; [T] 55, 6 | #3 p. 5 / PDF 13 |
| 2025: first EV ever | 69% overall (BEV 68, PHEV 72). 2024: 75%. | [T] 69, 75; [F] split | #3 pp. 4–5, 28 |
| Replacement rate by year (all plug-ins) | 2017: 81; 2018: 85; 2019: 84; 2020: 79; 2021: 80; 2022: 78; 2023: 77; 2024: 83 (%) | [F] deck #9 PDF 8 | #9 |
| 2024 replaced vehicles | Over 70% gasoline-fueled, including 7% conventional hybrid. Gasoline-only 64% (down from 70% in 2023). About one-fifth are 10+ model years old. | [T] | #9 PDF 9, 12 |

### 3.6 Geography and program coverage (B-admin, from application records)

| Parameter | Value | Type | Source |
|---|---|---|---|
| 2024 personal-consumer rebates | 45,535 rebates, $29,314,500 (approved as of 2025-04-01) | [T] | #7 PDF 2 |
| 2024 mix | Tesla 41%, PHEV 35%, other BEV 24%. Leased 64%. $500 rebates were 90% of rebates. | [T] | #7 PDF 4, 15 |
| **Urban vs rural, 2024** | **Rural 12% of rebates and 12% of funding**; urban 88%. Uses Census 2020 urban-rural classification, matched for 95% of purchases. | [F] | #7 PDF 19 |
| Top counties, 2024 (% of rebates) | Nassau 19, Suffolk 17, Westchester 10, Queens 8, Monroe 5, Erie 5, Kings 4; all other counties 32 | [F] | #7 PDF 18 |
| "Top REDC Regions", 2024 (% of rebates) | Long Island 35, NYC 20, Mid-Hudson 18, Monroe 5, Erie 5, Onondaga 3, Albany 2, Other 12 | [F] | #7 PDF 18 |
| Program share of NY EV sales | 3/2017–2019: 56%; 2020: 72%; 2021: 65%; 2022: 66%; 2023: 61%; **2024: 53%**. Approximate, compared against the Alliance for Automotive Innovation dashboard. | [F] | #11 PDF 22 |
| Survey responses over program life | 32,331 responses representing 176,846 participants (3/2017–2024) | [F] | #11 PDF 22 |

On the "Top REDC Regions" chart:
- Some bars are labelled with county names (Monroe, Erie, Onondaga, Albany). These are presumably the Finger Lakes, Western NY, Central NY and Capital Region REDCs, but the deck does not say so.
- The **Southern Tier REDC (which includes Tompkins County)** is not shown separately. It falls inside "Other" (12%).
- No survey result is reported for Southern Tier, Central NY or Finger Lakes, or for any rural/urban split. The county-level rebate counts in `thd2-fu8y` are the only NY Drive Clean source for Tompkins.

### 3.7 BEV vs PHEV differences (summary)

Compared with PHEV respondents, BEV respondents:
- charge at home **less often** (34 vs 51% daily)
- are less likely to **never** charge at home (11 vs 19%)
- use **public charging far more** (73 vs 32% ever)
- rely on **L2 or 240V** at home rather than a 120V outlet (L2 station 58 vs 24%; 120V outlet 14 vs 68%)
- drive slightly more (33 vs 30 mi/day; 10,670 vs 10,082 total miles)
- are younger and more often male, and more often have solar (21 vs 15%)
- are more satisfied (88 vs 69% very or extremely satisfied)

All of these differences are significant per the report (pp. 6–20).

---

## 4. Selection bias assessment

1. **Participants are not all NY EV owners.**
   - The program covers only **new** vehicles bought or leased from **participating dealers** with a point-of-sale rebate. Used EVs, private sales, most out-of-state purchases, fleets and business registrants, and non-participating sales channels are excluded.
   - Rebated vehicles were only **53% of NY EV sales in 2024**, down from 72% in 2020 [F, #11 PDF 22].
   - Eligibility thresholds (e-miles, MSRP) and dealer participation shape the vehicle mix: $500 rebates made up 90% of 2024 rebates [T, #7].
2. **EV buyers are not all households.**
   - Recipients are more often **homeowners (85%)** and live in **detached houses (78%)**, with high income (77% earn $100k or more) and education (76% bachelor's or higher). They are more often male (69%) and aged 40 or older (83%) [T, #1 Table 3].
   - Compared with the NY population (ACS 2019–2023), homeownership is 54% and household income over $100k is 43% [T, #11 PDF 13].
   - For NY new-car buyers (NVES 2022), homeownership is 77% and income over $100k is 55% [T].
   - CSE estimates about **61% of the income disparity** between program and state population is specific to EVs and rebates; the other 39% comes from car-buying in general [T, #11 PDF 13].
3. **Survey response is not the same as participation.**
   - Response rates are 10.6% (ownership) and 11.4% (adoption).
   - Weights correct only for **model, purchase vs lease, county and technology**. No demographic, housing or behavioral variables are used, because they are not in the application data.
   - Nonresponse related to enthusiasm, satisfaction, home-charging access or tenure is **not** corrected. Charging-engaged owners may be over-represented. Direction and size are unknown.
4. **Survivorship.** The ownership survey drops households that no longer have the car (0.9%). There is some light evidence of it: a small share of respondents sold the car or had it damaged or stolen.
5. **Self-report.**
   - Miles are recalled odometer estimates. The daily-miles question is "about how many miles … per day", which is ambiguous for non-driving days.
   - Charging frequencies are **ordinal bins**, not session counts.
   - No metered energy, timestamps or session durations are collected.
6. **Timing.** The 2024 ownership cohort is 2024 vehicles surveyed in 2025, a market dominated by leases (64%) and Tesla (41%). The 2025 adoption charging answers include **planned** behavior and come 1–3 weeks after purchase.
7. **No sub-state results.** County enters the weights, but no county or regional estimates are published. For Tompkins, statewide results are dominated by Long Island, NYC and Mid-Hudson (73% of 2024 rebates [F]).

**What cannot be generalized:**
- Home-charging access and L2 shares from this survey should not be applied to renters or multi-unit dwellers. Ithaca has many renters and students, and future adopters will increasingly include used-EV buyers.
- Program demographics should not be treated as the EV-owner population in Tompkins.
- Suburban downstate commute patterns should not be assumed to describe rural or small-city Southern Tier driving.
- Nothing here gives time-of-day or energy data.
- The DAC subgroup (54% detached, 28% apartment/condo) is the only in-survey hint of how multi-unit households differ, and the report does not publish charging behavior by DAC status.

---

## 5. Modeling implications (stochastic charging-event model)

### Usable as NY-specific priors (with self-report and selection caveats)

| Model parameter | Suggested prior basis | Notes / caveats |
|---|---|---|
| Annual VMT per EV | BEV about 10,670 mi, PHEV about 10,082 mi (2024 cohort); BEV 12,056 mi in the 2023 cohort | Covers 9.4–14.1 months of ownership, so it is not exactly annual. Weighted mean only; no distribution or median is published. Year-to-year change is large (BEV −1,386 mi). Use a wide prior, e.g. span both years. |
| Daily VMT | BEV 33 mi/day, PHEV 30 mi/day | Mean of self-reported "per day" answers. 33 × 365 = 12,045, which does not equal the total-miles figure, so the question probably means driving days. |
| Share of EVs that ever charge at home | BEV 89%, PHEV 81% (ownership). 82% charge at home plus 9% planning (adoption 2025). | Upper bound for general households. Condition on housing type or tenure using external sources (ACS for Tompkins, NREL/EVI-Pro, multifamily-access studies). |
| Home charging frequency distribution | Fig. 24 bins: BEV 34 / 28 / 20 / 7 / 11; PHEV 51 / 15 / ~5 / 10 / 19 | Converting bins to sessions per week needs an analyst mapping, e.g. daily ≈ 5–7, few/wk ≈ 2–4, 1/wk ≈ 1, few/mo or less ≈ 0.25–0.75. That mapping is an **assumption**, not survey data. |
| Home L1 vs L2 | BEV: L2 station 58%, 240V outlet 27%, 120V outlet 14%, L1 station 8% (multi-select). PHEV: 120V outlet 68%, L2 24%. 2025 adoption (incl. planned): BEV L2 62%. | Normalize for overlap, e.g. assign "any 240V" to L2 power. Charger power (kW) is not reported, so take kW distributions from other sources. |
| Workplace charging availability | 23% of workers (ownership). About 11% free and 10–13% paid. | Among those with access, about 63–66% ever use it. On-site frequency bins are given above (n = 912, so imprecise). |
| Public charging propensity | BEV: 27% never, 57% few/mo or less, about 16% weekly or more. PHEV: 68% never. | Probably **under-counted** (the "Other" write-ins include public). No L2 vs DCFC split. |
| BEV/PHEV fleet mix | Rebates: BEV 66% (2024) and 76% (2025 respondents) | For Tompkins, use `thd2-fu8y` county data and DMV registrations instead. |
| Replacement vs addition | About 82–83% of EVs replace a household car; 14–16% add one | Useful for fleet-growth assumptions, not for charging. |

### Must come from other sources

- **Location split of energy or sessions** (home / work / public kWh shares). The survey gives only ordinal frequencies by location, with no energy per session. Use NREL EVI-Pro, the INL EV Project, utility AMI studies (e.g. NYSEG/RG&E or Con Edison SmartCharge), or charging-network data.
- **Time-of-day / arrival-time distributions**: not asked. Use NHTS or NYS travel-survey trip end times, utility load research, and TOU program evaluations.
- **TOU and managed-charging participation**: not asked. Use utility program enrollment data (NYSEG/RG&E EV programs, the NY PSC EV Make-Ready / Managed Charging proceedings).
- **DCFC share and DCFC session energy**: not asked. Use the AFDC station inventory, the NYSERDA charging-station map, and network utilization data. The survey endnote gives only port-to-EV ratios.
- **Annual kWh per EV**: not reported. It can be derived as VMT × efficiency, e.g. 10,670 mi × an external kWh/mi value from fueleconomy.gov by model mix. Label any such value as **derived**.
- **PHEV eVMT share**: asked but not reported. Use literature (e.g. ICCT, UC Davis) or a data request to NYSERDA/CSE.
- **Charging-access conditional on housing** for renters and multifamily households, and any **rural / Southern Tier / Tompkins-specific behavior**: not reported. Use ACS housing data, the Tompkins-specific studies, and `thd2-fu8y` for adoption counts.
- **Household vehicle count / EV share of household VMT**: asked but not reported. Use NHTS or ACS vehicles-available data.
- **Distributions** (variance, medians) of any metric: not published. Only means or binned shares are available. Respondent-level data would require a request to NYSERDA/CSE.

---

## 6. Evidence class labels

| Item | Class | Note |
|---|---|---|
| Miles driven, trip-use frequencies, charging location and frequency, home charging method, workplace access, perceptions | **B-self-report** | Weighted web survey of rebate recipients; about 11% response |
| Tenure, residence type, income, education, age, gender, race, solar | **B-self-report** | Same |
| Replacement status, replaced-vehicle fuel and model year | **B-self-report** | Adoption survey |
| Rebate counts, BEV/PHEV/Tesla mix, lease share, rebate amounts, county/REDC shares, urban/rural share | **B-admin** | Program application records (CSE decks; same underlying data as `thd2-fu8y`) |
| Program share of NY EV market (53% in 2024) | **B-admin (approximate)** | Rebates compared with a third-party sales dashboard |
| EVs per L2 port / BEVs per DCFC port (report #1 endnote 13) | **B-admin, second-hand** | Quoted from the NYSERDA EV Registration Map |
| NY new-car-buyer comparisons | Third-party survey (Strategic Vision NVES 2022, no Tesla buyers) | Cited, not NYSERDA's own data |
| MOE values and "any 240V" range in this note | **Derived [D]** | My calculations, not from the reports |

## Known internal inconsistencies in the source reports

- #1 ES-1 gives mileage of 10,674 (BEV) and 10,097 (PHEV); the body and Fig. 11 give 10,670 and 10,082.
- #1 ES-1 says 60% of PHEV respondents never use public charging; Fig. 24 and p. 19 imply 68%. 60% was the 2023 value.
- #1 gives a response rate of 10.7% for all responses and 10.6% for valid responses; both are stated.
- #1 p. 20 reads "Seventy percent (62%)" disagree there are enough public chargers.
- #3 captions for Figs. 3 and 4 appear to have swapped chi-square statistics (759 vs 7). This has no effect on the shares.
