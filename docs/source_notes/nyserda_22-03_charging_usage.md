# Source note: NYSERDA Report 22-03, Cost and Usage Trends for EV Chargers (NY Level 2)

## 1. Citation and classification

- **Citation:** Di Filippo, J., and N. Nigro (Atlas Public Policy). 2021. *Cost and Usage Trends for Electric Vehicle Chargers: Evidence from NYSERDA-Funded Level 2 Charging Stations in New York State.* Final Report, NYSERDA Report 22-03, NYSERDA Contract 130602, December 2021. NYSERDA Project Manager: Jason Zimbler. (PDF metadata: created 2022-05-18, modified 2022-08-01.)
- **URL:** https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/Research/Transportation/22-03-Cost-and-Usage-Trends-for-Electric-Vehicle-Chargers.pdf
- **Retrieved:** 2026-09-14. Local copy: `data/raw/reports/nyserda_22-03.pdf` (68 PDF pages, 3,321,994 bytes; git-ignored).
- **Evidence class:** **B.** These are direct New York State observations. The report gives **summary statistics and figures only**; no session-level data was found (see Section 4).
- **Companion source skimmed:** Energetics, Inc. for NYSERDA, *2016 Annual Data Summary: New York State Electrical Vehicle (EV) Charging Station Deployment Program* (June 2017). URL: https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/EV-Charging-Station-Data/2016-ESVE-Annual-Report.pdf. Local copy: `data/raw/reports/nyserda_2016_EVSE_annual_report.pdf`. Also class B and summary-only.

**Page convention.** "p. N" means the page number printed in the report. PDF page index = printed page + 12 (for example, printed p. 37 is PDF page 49). Summary pages S-1 to S-5 are PDF pages 8–12.

**How values are tagged.**
- **[text]**: the number is stated in the report text or a table.
- **[fig]**: I read the value off a plotted figure. Unless noted, expect about ±1–2 percentage points (pp) on utilization and ±1 h on hour position.
- **[derived]**: I calculated it from stated numbers. It is not in the report.

**Reading method.** The Read tool rejected the PDF as "password-protected", but `pdfinfo` reports `Encrypted: no`. I extracted text with `pdftotext -layout` and rendered figures and tables with `pdftoppm` for visual reading. I read the whole report: front matter, summary, sections 1–6, and endnotes EN-1. The report has no appendices.

---

## 2. Study design

### Funding programs (pp. 3, S-1)
- **PON 2301, the EVSE Demonstration Program** (funding rounds in late 2011 and 2012; stations deployed 2012–2016).
  - Covered up to 80% of project costs, up to $1M per project.
  - Eligible sites: public locations, workplaces, and MUDs with more than 5 units.
  - Recipients had to report usage for at least 4 years. [text]
- **Charge Ready NY** (2018–2021).
  - Flat $4,000 per-port rebate. An extra $500 was available in disadvantaged communities after December 2020, but no station in the report qualified for it (EN-1, note 3).
  - Site hosts must provide charging data for at least 5 years. [text]
- A small share of the session data comes from stations funded by Recharge NY and Cleaner Greener Communities (EN-1, notes 1, 2, 4). [text]

### Sample sizes (pp. 4–5, S-1)
| Data universe | Size | Source |
|---|---|---|
| Cost data | 275 PON 2301 projects + 428 Charge Ready NY projects = **2,641 ports**; $11.6M public funding; $19.8M total cost | p. 4 [text] |
| Cost data with address-level location | 1,695 ports | p. 5 [text] |
| **Session (use) data** | **1,288 stations, 2,175 ports, 434,578 sessions, 988,755 charging hours, 4.2 GWh** | p. 4 [text] |
| Session data matched to cost data (has land use and address) | **699 stations, 1,209 ports** | pp. 4–5 [text] |
| Table 1, ports matched to a REDC | 2,151 ports; 24 could not be matched | p. 7 [text] |
| Performance groups (Table 5) | 207 + 516 + 521 = 1,244 stations | p. 27 [text]; sum [derived] |
| Land-use productivity table (Table 6) | 37 MUD + 424 public + 230 workplace = 691 stations | p. 30 [text]; sum [derived] |
| Use-pattern clusters (Fig. 19) | 349 + 213 + 66 + 108 + 167 = 903 stations; stations with fewer than 10 sessions excluded | p. 39, EN-1 note 13 [text]; sum [derived] |

The report notes that at least 466 ports in the cost data are not in the session data (p. 4). The text extraction printed this as "4664"; the trailing 4 is endnote marker 4.

### Time coverage
- Session data runs **April 2012 – December 2020** (p. 4). [text]
- Per-charger mean and median statistics use only data **before March 1, 2020**. This excludes the 429 stations built after that date (EN-1, note 9). Distributions, such as the histograms, are not filtered this way. [text]
  - So the stated means and medians cover about 1,288 − 429 = 859 stations. [derived]
- Figure 15 starts in 2014 because few chargers existed in 2012–2013 (p. 33).
- Figure 16 cohort trends are cut off at March 1, 2020 (p. 35).
- The congestion analysis covers 2017–2019 (p. 44).

### Networks and data providers
- Use data comes only from networked stations on **ChargePoint and EV Connect** (p. 4). [text]
- Data was supplied by NYSERDA, program participants, and those network providers (p. 4). [text]
- 68% of stations in the use data are dual-port and 32% are single-port. Per-port power capacity is unknown (p. 27). [text]

### Geographic coverage (pp. 6–7)
- Statewide. Stations are concentrated in dense areas, with the most around Albany (the Capital Region). NYC and the Capital Region are outliers in stations per capita. [text]
- Session data has ZIP-level location only. The map in Figure 1 is ZIP-approximate. [text]
- **Table 1, ports in the session data by REDC** [text]:

| REDC | Ports |
|---|---|
| Capital Region | 705 |
| Mid-Hudson | 346 |
| Finger Lakes | 326 |
| Long Island | 206 |
| NYC | 152 |
| Western NY | 145 |
| Central NY | 90 |
| North Country | 82 |
| **Southern Tier (includes Tompkins County)** | **51** |
| Mohawk Valley | 48 |
| Total | 2,151 |

- **Station counts by REDC in Figures 13 and 14** [text in figure]: Capital 382, Finger Lakes 182, Mid-Hudson 178, Long Island 117, NYC 103, Western NY 77, Central NY 58, North Country 50, **Southern Tier 38**, Mohawk Valley 37.

### Site and land-use categories (p. 8, Table 2: ports in the *cost* data)
- **PON 2301 (646 ports)** [text]:

| Land use | Ports |
|---|---|
| Parking lot/garage (NYC) | 123 |
| Educational service | 102 |
| Professional and technical services | 72 |
| Hotel | 46 |
| Government/public administration | 45 |
| Transportation hub | 44 |
| Business office | 43 |
| Parking lot/garage (non-NYC) | 42 |
| Healthcare/medical | 26 |
| Retail, big-box national | 22 |
| Retail, local small business | 20 |
| Multifamily (MUD) | 16 |
| Restaurant | 16 |
| Parks and recreation | 15 |
| Arts and entertainment | 7 |
| Fleet/freight | 6 |
| Utilities | 1 |

- **Charge Ready NY (1,995 ports):** Public 1,077; Workplace 552; MUD 366. [text]
- Usage analyses by land use use only the three Charge Ready categories. PON 2301 categories were remapped to public, workplace, or MUD "based on access and type" (EN-1, note 6). [text]
- Land use is known only for the 699 matched stations. The report warns that these matched stations are **more productive on average** than the full sample, so land-use comparisons may be biased (p. 30). [text]

### Data cleaning and definitions
- **Utilization** = in-use time / total time. It comes in two forms (p. 33) [text]:
  - "charging": the vehicle is drawing power;
  - "occupied": the vehicle is plugged in, whether or not it is charging.
- **Idle time** = plugged in but not charging (pp. 24, 41). [text]
- **Productivity** is measured as mean kWh per day and sessions per day for each charger.
  - Low productivity: below the 50th percentile. Mid: 50th–90th. High: at or above the 90th (p. 27).
  - A station takes its better category across the energy and session metrics, and is ranked by its most productive port (pp. 27–28). [text]
- **Sites** were built by grouping stations within 50 m of each other, because the session data has no site IDs (EN-1, note 14). [text]
- **Clustering** used agglomerative hierarchical clustering on usage patterns, excluding stations with fewer than 10 sessions (EN-1, note 13). [text]
- **Not reported:**
  - rules for dropping short or zero-energy sessions, outliers, or duplicates;
  - time-zone handling;
  - how "charging time" was measured (for example, a power threshold).

---

## 3. Quantitative results relevant to hourly load modeling

### 3.1 System totals and per-session means
- Sessions: 434,578. Energy: 4.2 GWh. Charging hours: 988,755 (p. 4). [text]
- Mean energy per session over all data: 4.2 GWh / 434,578 ≈ **9.7 kWh**. [derived; 4.2 GWh is rounded]
- Mean charging hours per session: 988,755 / 434,578 ≈ **2.28 h**. [derived] (The text gives 2.4 h, p. 41. The small difference may come from a different filter.)
- Mean power while charging: 4.2 GWh / 988,755 h ≈ **4.2 kW**. [derived; the report states no average power]
- Commercial L2 stations "typically offer 6.6 kW". The L2 range is 3.1–19.2 kW (p. 2, Box 1). [text]
- Peak month was **February 2020: 166 MWh over 13,825 sessions** (p. 24) [text], or about 12.0 kWh per session. [derived]

### 3.2 Per-charger utilization (pre-March 2020 data; pp. 25, S-3)
- **Average charger:** 3.25 kWh per day and 0.32 sessions per day, which the report describes as "about two 10.5 kWh sessions per week". [text]
- **Median charger:** 1.5 kWh per day and 0.14 sessions per day (about one per week). [text] Medians are computed per metric, so they may not describe the same charger (EN-1, note 10).
- The text calls the unit a "charger". It is not clearly defined as a station or a port.
- **90th-percentile charger:**
  - Energy: 3.5× the average and almost 8× the median [text], or roughly 11 kWh per day (about 80 kWh per week). [derived]
  - Sessions: about 3× the average and 7× the median [text], or roughly 1 session per day. [derived]
  - Figure 11 is consistent with this: the high-productivity bars start at about 80 kWh per week and about 7 sessions per week. [fig]
- Stations above the 90th percentile deliver **about half** of all energy and sessions. The bottom half deliver **7% of sessions and 8% of energy** (p. 25). [text]
- Figure 11 histograms (p. 26) [fig]:
  - Weekly energy: about 400 chargers in the 0–10 kWh bin, about 255 in 10–20, about 140 in 20–30, and a long tail past 300 kWh per week.
  - Weekly sessions: about 415 chargers in the 0–1 bin and about 300 in 1–2, with a tail to about 34.
- Table 5 (p. 27) [text]:

| Productivity group | Stations | Share |
|---|---|---|
| High | 207 | 16.6% |
| Mid | 516 | 41.5% |
| Low | 521 | 41.9% |

- Ports on single-port stations are under-represented among high-productivity ports (p. 28). [text]

### 3.3 Session duration: connection vs. charging vs. idle (pp. 41–43)
- **Mean charging time is about 2.4 h and mean idle time about 2.3 h per session** [text]. That implies a mean connection time of about 4.7 h. [derived]
- **Median charging time is 2 h and median idle time 0.5 h** [text].
- **Figure 20a, mean hours per session by plug-in hour.** Bar total = mean connection time; the lower segment = mean charging time. [fig]

| Start hour | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Connection (h) | 7.2 | 7.25 | 7.0 | 7.2 | 4.4 | 6.0 | 6.3 | 5.85 | 5.6 | 4.85 | 3.95 | 3.85 |
| Charging (h) | 3.35 | 3.5 | 3.4 | 3.35 | 2.65 | 2.9 | 2.85 | 2.8 | 2.8 | 2.55 | 2.3 | 2.2 |

| Start hour | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Connection (h) | 3.75 | 3.65 | 4.05 | 4.05 | 3.95 | 3.65 | 4.4 | 4.8 | 5.4 | 6.3 | 7.05 | 7.25 |
| Charging (h) | 2.15 | 2.05 | 2.05 | 1.95 | 2.0 | 2.05 | 2.3 | 2.5 | 2.6 | 3.05 | 3.5 | 3.65 |

- **Figure 20b, medians by plug-in hour.** The lower segment is the median charging time and the upper segment the median idle time. The report says the stacked total is **not** the median connection time. [fig]

| Start hour | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Median charging (h) | 2.25 | 2.55 | 2.65 | 2.6 | 2.05 | 2.4 | 2.25 | 2.3 | 2.3 | 2.15 | 2.0 | 1.85 |
| Median idle (h) | 1.15 | 1.05 | 0.95 | 0.6 | 0 | 1.0 | 1.95 | 1.95 | 1.8 | 1.25 | 0.3 | 0.2 |

| Start hour | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Median charging (h) | 1.85 | 1.75 | 1.75 | 1.6 | 1.55 | 1.6 | 1.8 | 1.8 | 1.75 | 2.0 | 2.5 | 2.85 |
| Median idle (h) | 0.25 | 0.25 | 0.15 | 0 | 0 | 0 | 0 | 0 | 0.1 | 0.6 | 1.2 | 1.4 |

- The text confirms idle time for the median session "vanishing entirely between 3:00 and 6:00 p.m." and also for sessions starting 4–5 a.m. The longest sessions start late evening or overnight; the second-longest start 5–9 a.m. (p. 42). [text]
- **No session-start count distribution is given.** Figure 20 shows durations conditional on start hour, not how many sessions start in each hour.
- **No distribution of energy per session is given.** Only means are reported (Sections 3.1 and 3.2).

### 3.4 Hourly load shapes and weekday vs. weekend
All shapes below are **utilization** (share of plugs charging or occupied), not kW. Hours are local clock hours, 0–23.

- **Figure 17 (p. 37): hourly utilization for all chargers, by day of week and year (2012–2020).**
  - The caption is ambiguous. It says "occupied and actively charging", but the plot draws two separate lines: occupied (grey) and charging (blue).
  - Stated trends [text]:
    - 2012 had a weekday late-morning peak with weekend use near zero.
    - Weekend and afternoon/evening use grows over time.
    - Overnight charging persists from 2016 onward.
    - Early-morning charging bottoms out near zero.
    - Occupancy develops a base of **about 5% at its 2018–2019 peak** (p. 36).
  - Values read from the high-resolution crop [fig]:

| Year | Weekday charging peak | Weekday occupied peak | Weekend |
|---|---|---|---|
| 2012 | ~6% | ~6–7% | ~0 |
| 2015 | ~10% | ~14–15% | charging ~1.5–2%, flat |
| 2018 | ~16–17% | ~20–21% | charging ~3.5–4% (midday, broad); occupied ~8% |
| 2019 | ~14–15% | ~18–19% | charging ~3.5–4%; occupied ~7% |
| 2020 | ~5% | ~8% | charging ~2%; occupied ~4% |

  - The weekday peak falls at **about 9–10 a.m.** [fig] The Figure 15 annotation also marks the all-time system peak at **Jan. 28, 2019, 9 AM** [text in figure].
  - In 2018–2019, the weekend charging peak is roughly one quarter of the weekday peak, flatter, and centered around midday to afternoon. [fig; approximate ratio]
  - 2019 weekday anchor hours (Mon–Fri look very similar) [fig]:

| Hour | 00 | 03 | 06 | 09 | 12 | 15 | 18 | 21 |
|---|---|---|---|---|---|---|---|---|
| Charging | ~1.5% | ~1% | ~1% | ~14.5% | ~10% | ~8% | ~5% | ~3% |
| Occupied | ~4.5% | ~4.5% | ~4.5% | ~18% | ~18% | ~14% | ~8% | ~6% |

  - 2019 Saturday anchor hours [fig]:

| Hour | 00 | 03 | 06 | 09 | 12 | 15 | 18 | 21 |
|---|---|---|---|---|---|---|---|---|
| Charging | ~2% | ~1% | ~1% | ~3.5% | ~4% | ~4% | ~3.5% | ~3% |
| Occupied | ~5% | ~4.5% | ~4.5% | ~7% | ~7.5% | ~7% | ~6% | ~5.5% |

- **Figure 18 (p. 38): weekday charging utilization by land use and year (2014–2020).** Values are % of plugs actively charging, read from the high-resolution crop. [fig]

| Land use, year | 00 | 03 | 06 | 09 | 12 | 15 | 18 | 21 | Peak |
|---|---|---|---|---|---|---|---|---|---|
| Workplace 2018 | 1 | 0.5 | 1 | ~21 | ~12 | ~8.5 | ~5 | ~2 | ~21.5% at ~9–10a |
| Workplace 2019 | 1 | 0.5 | 1 | ~20 | ~14.5 | ~11 | ~6 | ~2.5 | ~20.5% at ~9–10a; broader afternoon shoulder |
| Workplace 2014 | ~0 | ~0 | ~1 | ~5 | ~9 | ~5 | ~1 | ~0 | ~9% near 11a–12p |
| Workplace 2020 | ~0.5 | ~0.5 | ~0.5 | ~5 | ~7 | ~5.5 | ~3 | ~1.5 | ~7.5% |
| Public 2018 | ~2 | ~1.2 | ~1 | ~15 | ~10 | ~8 | ~6.5 | ~6.5 | ~15.5% at ~9–10a; second bump ~7.5% near 7–8p |
| Public 2019 | ~1.5 | ~1 | ~1 | ~11 | ~8.5 | ~7 | ~6 | ~4 | ~11.5% |
| Public 2020 | ~1 | ~0.5 | ~0.5 | ~3 | ~5 | ~4 | ~3 | ~2 | ~5% |
| MUD 2016 | ~7.5 | ~4 | ~1.5 | ~1 | ~1 | ~2 | ~4.5 | ~9 | ~9% at ~9–11p |
| MUD 2017 | ~7.5 | ~3 | ~1 | ~1 | ~1 | ~1.5 | ~4 | ~9.5 | ~9.5% at ~9–10p |
| MUD 2018 | ~6 | ~3 | ~1.5 | ~1 | ~2.5 | ~3 | ~5 | ~6.5 | ~6.5% |
| MUD 2019 | ~5 | ~2 | ~1 | ~1.5 | ~3 | ~4.5 | ~6 | ~6.5 | ~6.5% |
| MUD 2020 | ~2.5 | ~1 | ~0.5 | ~1.5 | ~2 | ~2.5 | ~3.5 | ~3.5 | ~3.5% |

  - The text (pp. 37–38) says MUD curves are roughly the inverse of public/workplace, with an evening peak and daytime trough, and the ramp gets more gradual in later years. Public shows more late-afternoon and early-evening use than workplace. Both public and workplace show small but real overnight use in later years. [text]
  - Figure 18 is weekday only. No weekend profile by land use is shown.
- **Figure 19 (p. 39): station clusters by hourly utilization (all hours; the day types pooled are not stated).** [fig]

| Cluster (stations) | Shape (read from figure) |
|---|---|
| Low morning (349) | Flat; peak ~4% at ~11a [text gives the 11 a.m. peak]; ~3.5% to ~5p; ~1% late night |
| Mid morning (213) | Peak ~17% at ~9–10a; ~9% at 1p; ~6% at 3p; ~3% at 6p; ~0.5% late |
| High morning (66) | Peak **~40%** at ~9–10a; ~21% at 1p; ~15% at 3p; ~6% at 6p; ~2% at 10p |
| Afternoon (108) | Near 0 before 9a; ~3–4% at 12p; peak ~14% at ~4p; ~3% by 9p |
| Evening (167) | ~4% at midnight; low ~1% around 6–8a; ~2% midday; peak ~5% at ~9–10p |

  - Workplaces dominate "high morning", public sites dominate "low morning", and MUDs are mostly "evening". 16 identified workplace chargers (7%) fall in "evening" (p. 40). [text]
  - Table 7, high-productivity stations by cluster (p. 40) [text]:

| Cluster | High-productivity stations | Share of cluster |
|---|---|---|
| Low morning | 51 | 14.6% |
| Mid morning | 60 | 28.2% |
| High morning | 48 | 72.7% |
| Afternoon | 13 | 12.0% |
| Evening | 28 | 16.7% |

### 3.5 Differences by site type (land use)
- **Figure 12 (p. 29), weekly per-station use** (matched stations):
  - [text] The median workplace station delivers more than 2× the energy over more than 2× the sessions of public and MUD stations. The median MUD station delivers **12.75 kWh per week**.
  - [fig] Box-plot values:

| | MUD | Public | Workplace |
|---|---|---|---|
| Energy median (kWh/week) | ~13 | ~12 | ~25 |
| Energy IQR (kWh/week) | ~4–53 | ~3–37 | ~7–59 |
| Energy upper extreme | whisker ~108 | outliers to ~340 | outliers to ~240 |
| Sessions median (per week) | ~1.0 | ~0.9 | ~2.2 |
| Sessions Q3 (per week) | ~2.7 | ~4.2 | ~5.3 |
| Sessions upper extreme | max ~7.4 | outliers to ~34 | outliers to ~20 |

  - Energy per session implied by the medians: MUD about 12–13 kWh, workplace about 11 kWh. [derived from figure medians; a ratio of medians, so indicative only]
- **Table 6 (p. 30), high-productivity share** [text]: MUD 4/37 (10.8%); public 81/424 (19.1%); workplace 54/230 (23.5%).
- **Specific venue types** (hotel, retail, municipal, parking, education) are **not analyzed for usage in 22-03**. They appear only as cost-data counts in Table 2. See Section 3.10 for 2016 venue-level usage.

### 3.6 Seasonality, monthly trends, and growth
- **Figure 10 (p. 24), monthly totals.**
  - [text] Energy and sessions grew together through February 2020, reaching 166 MWh and 13,825 sessions. Both dropped sharply with COVID, had nearly recovered by fall 2020, then fell again in the winter 2020 wave.
  - [fig] Approximate monthly values:

| Period | Energy (MWh/month) | Sessions/month |
|---|---|---|
| 2016 | ~20 | ~2,500 |
| 2018 | ~40 | ~4,000 |
| Jan 2019 | ~70 | ~7,500 |
| Late 2019 | ~140 | ~13,000 |
| Apr 2020 trough | ~50 | ~4,500 |
| ~Oct 2020 | ~145 | ~12,000 |
| Dec 2020 | ~100 | ~8,000 |

- **Figure 15 (p. 33), system weekly peak utilization (charging).**
  - [text] Strong seasonality: a **summer trough** and a **deep dip at year-end holidays**. The authors link this to commuting and possibly to better summer EV efficiency. The trend rose to a peak of "just under one in four" ports charging at once in early 2019, then fell from 25% to 15% over a few months in Q2 2019 as capacity grew (pp. 33–34).
  - [fig] Weekly peaks were about 7–10% in 2014 and about 12–17% in 2015–2016. Year-end dips reach about 4–7%. The COVID drop went to about 3% in spring 2020, with recovery to about 6% by fall 2020.
  - [fig] Ports reporting were about 50 in 2014, about 150 in 2016–2018, about 250 in early 2019, about 600 in early 2020, and about 1,200 at the end of 2020. This is a capacity series, and it differs from the 2,175 total ports that ever reported.
- **Figure 16 (p. 35), mean charging utilization by installation cohort, 2017 to Feb 2020.** [fig]

| Cohort | Trend |
|---|---|
| 2013 | ~3–4%, flat |
| 2014 | ~3.5% rising to ~6%, then ~5% |
| 2015 | ~4% to ~6.5% |
| 2016 | ~3% to ~8% |
| 2017 | ~2.5% to ~7% |
| 2018 | ~5% to ~7.5% |
| 2019 | ~3–4%, dipping to ~2% |

  - [text] New stations start with low utilization and existing cohorts keep growing. There is no evidence of saturation or cannibalization; the spatial difference-in-differences model was inconclusive (EN-1, note 12).

### 3.7 Geography (pp. 31–32)
- Figure 13, median weekly energy by REDC (kWh/week) [fig]:

| REDC | Median kWh/week |
|---|---|
| Mid-Hudson | ~28 |
| NYC | ~24 |
| Long Island | ~23 |
| Western NY | ~14 |
| Finger Lakes | ~11 |
| North Country | ~10 |
| Mohawk Valley | ~9 |
| **Southern Tier** | **~8** |
| Capital | ~7 |
| Central NY | ~4 |

- Figure 13, median weekly sessions by REDC [fig]:

| REDC | Median sessions/week |
|---|---|
| Mid-Hudson | ~2.3 |
| Long Island | ~2.2 |
| Western NY | ~1.3 |
| NYC | ~1.2 |
| Finger Lakes | ~1.1 |
| Mohawk Valley | ~1.0 |
| North Country | ~0.8 |
| Capital | ~0.6 |
| **Southern Tier** | **~0.6** |
| Central NY | ~0.5 |

- NYC has uniquely high energy per session (p. 32). [text]
- Figure 14, share of stations that are high-productivity [text in figure]:

| REDC | Share (count) |
|---|---|
| NYC | 25% (26/103) |
| Long Island | 23% (27/117) |
| Finger Lakes | 23% (41/182) |
| Mid-Hudson | 22% (39/178) |
| Western NY | 18% (14/77) |
| Capital | 13% (49/382) |
| **Southern Tier** | **8% (3/38)** |
| North Country | 6% (3/50) |
| Central NY | 3% (2/58) |
| Mohawk Valley | 3% (1/37) |

### 3.8 Congestion (pp. 43–44; 2017–2019; sites = stations within 50 m)
- The text says the analysis was limited to "5:00 and 8:00 p.m." and calls those "daytime operating hours". This looks like a typo for 5 a.m.–8 p.m.; the intended window is unclear. Results [text]:
  - About 75% of dual-port sites were congested less than 5% of the time; about 1.5% were congested more than 50% of the time.
  - At 4-port sites, 78% were congested less than 5% of the time, and none more than 10%.
  - No site with more than 4 ports was congested more than 5% of the time.
  - No site with more than 8 ports had more than 10 congestion hours per year.
  - No site with more than 12 ports ever had all ports in use.
- Idle time correlates **positively** with productivity, even among high-productivity stations (pp. 42–43). [text]

### 3.9 Pricing, fees, and costs
- **Pricing:** 22-03 has **no quantitative analysis of fees or prices**. The only statement is that "most site hosts elect to offer free charging" (p. 46). [text]
- **Costs per port, Table 3 (p. 9)** [text]:

| Program | Statistic | Project | Equipment | Installation | Public funding |
|---|---|---|---|---|---|
| Charge Ready NY | Mean | $6,921 | $3,350 | $3,571 | $4,000 |
| Charge Ready NY | Median | $6,518 | $3,484 | $3,250 | $4,000 |
| Charge Ready NY | Min | $976 | $527 | $302 | $4,000 |
| Charge Ready NY | Max | $19,990 | $7,599 | $17,064 | $4,000 |
| PON 2301 | Mean | $8,774 | $4,186 | $4,587 | $5,777 |
| PON 2301 | Median | $7,790 | $4,363 | $3,538 | $5,274 |
| PON 2301 | Min | $4,441 | $1,863 | $777 | $936 |
| PON 2301 | Max | $20,433 | $6,888 | $17,033 | $16,883 |

- Other cost findings [text]:
  - Charge Ready NY costs about 21% less than PON 2301 on average.
  - Charge Ready NY per-port costs have two peaks, near $4,000 and $7,500 (p. 10).
  - ChargePoint equipment cost fell 9% between programs (p. 14).
  - PON 2301 installation breakdown (p. 17): labor >49%, construction 16%, materials 15%, overhead about 11%, permitting and panel about 2% each.
  - Public sites cost less to install than workplace or MUD sites (p. 19).
  - Capital Region costs more than downstate, which costs more than north/west (pp. 20–21).
  - Per-port cost is flat up to 6 ports, rises at 8–10 ports, then declines slowly to 20 ports (LOESS fit; p. 22).
  - Recommended planning figure: **about $6,500 per port** (pp. S-4, 45).

### 3.10 Companion: NYSERDA 2016 Annual Data Summary (PON 2301 stations, calendar 2016)
- **Program scale** [text]: 671 L2 outlets installed through the program in total, 43 of them added in 2016 (p. 4).
- **Hourly occupancy, Figure 2 (p. 3), % of ports with an EV plugged in; axis runs 06:00 to 06:00 next day** [fig]:
  - Weekday median: ~4% at 6 a.m., rising to ~12% by ~10 a.m., plateau ~13% until ~15:00, falling to ~5% by ~22:00, ~4% overnight. Max-day curve ~16%.
  - Weekend median: ~4–6%, flat.
- **Aggregate demand, Figure 3 (p. 3), AC kW across all program ports** [fig]:
  - Weekday median: peak ~190 kW at ~8:30–9:00, ~120 kW midday, ~100 kW at 15:00, ~50 kW by 22:00, ~20–30 kW overnight.
  - Weekend median: ~50 kW, broad midday.
  - The text says most charging starts at **9:00 a.m.** and occupancy is highest 9 a.m.–5 p.m. on weekdays.
- **Trend, Figure 1 (p. 2)** [fig]: mean port occupancy rose from ~3.2% (2013 Q4) to ~6.9% (2016 Q2), then ~6.3% (2016 Q4). Energy per port rose from ~9.8 to ~18 kWh per week.
- **Detailed usage statistics (pp. 14–15; CE = charge event)** [text]:

| Group | Ports | CE/day | Plug-in h/CE | Charging h/CE | Plug-in % of time | % of plug-in time charging | kWh/CE |
|---|---|---|---|---|---|---|---|
| Public access | 432 | 0.29 | 3.4 | 1.8 | 4.1% | 53% | 7.2 |
| Limited access | 244 | 0.25 | 7.1 | 2.5 | 7.5% | 36% | 8.8 |
| Parking garage (NYC) | 126 | 0.09 | 8.5 | 4.0 | 3.2% | 47% | 22.3 |
| University/medical | 128 | 0.42 | 5.3 | 2.3 | 9.3% | 44% | 8.0 |
| Parking (non-NYC) | 107 | 0.32 | 5.7 | 2.0 | 7.6% | 35% | 6.8 |
| Retail | 92 | 0.53 | 1.2 | 1.0 | 2.6% | 82% | 3.5 |
| Workplace | 91 | 0.21 | 4.5 | 2.3 | 3.9% | 52% | 7.6 |
| Transit station | 44 | 0.15 | 7.6 | 2.1 | 4.7% | 28% | 8.6 |
| Hotel | 40 | 0.06 | 5.5 | 2.8 | 1.4% | 51% | 12.7 |
| Leisure destination | 26 | 0.21 | 3.3 | 2.0 | 2.9% | 61% | 7.3 |
| Multifamily | 22 | 0.19 | 14.3 | 4.5 | 11.1% | 31% | 18.8 |
| Suburban | 354 | 0.31 | 4.1 | 1.7 | 5.3% | 42% | 6.1 |
| Urban | 270 | 0.26 | 5.6 | 2.6 | 6.1% | 46% | 10.5 |
| Rural | 52 | 0.14 | 3.7 | 2.1 | 2.2% | 55% | 7.3 |
| No fee | 565 | 0.31 | 4.5 | 2.0 | 5.7% | 44% | 7.3 |
| Fee required | 111 | 0.12 | 6.6 | 2.9 | 3.2% | 45% | 14.1 |
| **Southern Tier** | **14** | **0.23** | **2.5** | **1.6** | **2.4%** | **65%** | **6.2** |
| Rochester/Finger Lakes | 42 | 0.57 | 4.3 | 2.1 | 10.1% | 49% | 6.9 |

- Most fee-charging ports are NYC garages, so the fee effect is confounded with location (p. 10). [text]
- Mean power while charging, 2016 [derived]: public 301,747 kWh / 76,821 h ≈ 3.9 kW; limited-access 184,077 kWh / 52,708 h ≈ 3.5 kW.
- 2016 totals [text]: 486 MWh; 42,070 public and 20,901 limited-access charge events.
- County EV registrations as of 12/31/2015 (p. 8 map table) [text in figure]: **Tompkins had 186 EVs, 0.37% of vehicles**, the second-highest share after New York County (0.44%).

---

## 4. Public-availability classification

**Classification: public summary only.** No session-level or raw usage data from 22-03 or the 2013–2017 EVSE use reports is publicly downloadable. The underlying data appears to be **nonpublic**: it was provided to Atlas by NYSERDA, program participants, and ChargePoint/EV Connect.

Evidence checked on 2026-09-14:
1. **22-03 itself** mentions no data release, appendix tables, or data portal.
2. **NYSERDA landing page** ("Electric Vehicle (EV) and EV Charging Station Data"; fetched, HTTP 200).
   - Its "NYSERDA Charging Station Demonstration Data" section says data was "presented in annual and quarterly reports through Q1 2017".
   - The only links in that section are **PDFs**: 2013 Q4 through 2017 Q1, plus 2013–2016 annual summaries.
   - No CSV, XLSX, or ZIP of session or usage data is linked.
3. **Other data links on the landing page:**
   - EValuateNY (Excel/Power BI tool plus two ZIPs, `EValuateNY_v11_pt1.zip` at 333 MB and `pt2.zip` at 368 MB).
   - EV registration CSV.
   - AFDC/Open NY station locations.
   - I listed the ZIP contents via an HTTP range request on the central directory, without downloading the full files:
     - pt1: `All EV Registrations.csv`, `census_bureau.xlsx`, `Current Registrations.csv`, `DMV Snapshots.csv`, `EValuateNY.xlsx`.
     - pt2: `EValuateNY.pbix`, `New Registrations.csv`, `resources.xlsx`, `Vehicle Description.csv`.
   - None of these files is named as session or usage data. The internal sheets of `EValuateNY.xlsx` (268 MB) were **not inspected**, so a possible aggregated charging-usage sheet cannot be ruled out.
4. **data.ny.gov** catalog search ("charging session", "electric vehicle charging", "EVSE"):
   - Found only station-location datasets (7rrd-248n, bpkx-gmh7) and **Charge Ready NY Programs: Beginning 2018 (9wxk-hakb)**.
   - 9wxk-hakb is **project-level**: ports, location type (Public/Workplace/MUD), address, activation date, EVSE model, network provider, utility. It has **no usage fields**. It is publicly available but not downloaded; I only queried it through the API.
   - Tompkins County rows (API query, data through 2026-08-31):

| City | Location type | Ports | Projects | Activation dates |
|---|---|---|---|---|
| Ithaca | MUD | 38 | 5 | 2020-01 to 2025-11 |
| Ithaca | Workplace | 6 | 2 | 2020 |
| Dryden | Public | 4 | 2 | 2020–2021 |
| Dryden | Workplace | 6 | 1 | 2024 |
| Freeville | Public | 2 | 1 | 2020 |
| Cortland (listed under Tompkins) | Public | 6 | 1 | 2023 |

   - Useful as a site inventory, but it cannot supply load shapes.

**Pathway to raw data, if needed.** Charge Ready NY hosts must report session data to NYSERDA for 5 years. A data request to NYSERDA (Clean Transportation) could possibly yield anonymized Southern Tier or Tompkins session data. This is not acquired and not public.

---

## 5. Limitations and transferability to Ithaca / Tompkins County

- **Charger type and access.** Level 2 only, networked (ChargePoint and EV Connect only), and publicly funded. There is **no home (single-family) charging**, **no DCFC**, and no non-networked stations; non-networked MUD chargers allowed under Charge Ready are excluded from the use data.
  - Home charging is the dominant load in most EV models, so this source says nothing about the largest load component.
- **Selection and representativeness.**
  - Funded sites are self-selected by hosts responding to incentives.
  - Land-use results rely on the 699 matched stations, which are **more productive** than the full sample (p. 30).
  - Land-use labels are coarse (public/workplace/MUD), and PON 2301 categories were remapped.
- **Era.** 2012–2020, when EV penetration in NY was below 1% of vehicles. Shapes changed materially over time: early use was almost purely commuter, with evening, weekend, and overnight use growing later. Absolute utilization levels (sessions per port per day) are tied to fleet size, so levels cannot be transferred directly to 2025+ Ithaca. Normalized shapes are more transferable.
- **COVID.** 2020 is heavily distorted: spring drop, fall recovery, winter fall. Per-charger means and medians exclude post-March-2020 data. Figures 17 and 18 show 2020 as flattened, low-amplitude profiles. Post-2020 hybrid work likely reduces workplace morning peaks relative to 2018–2019.
- **Units.** The hourly figures show **utilization** (share of ports charging), not kW. Converting to load needs ports in service and per-port power, and the report gives neither by hour.
  - The derived fleet-mean charging power is about 4.2 kW, below the 6.6 kW nameplate. Dual-port shared circuits and vehicle acceptance limits likely contribute.
  - Hourly utilization means × ports × about 4–6.6 kW gives only a rough load scale.
- **Undocumented definitions.** Time zone, the rule for "charging" vs. idle, session-cleaning rules, and whether Figure 19 pools weekends are not documented.
- **Geography.**
  - Tompkins is in the **Southern Tier REDC**, which is small in this sample: 51 ports and 38 stations.
  - Southern Tier is near the bottom on productivity: median about 8 kWh and about 0.6 sessions per week per station, and 8% high-productivity (3/38).
  - Statewide results are dominated by the Capital Region and downstate.
  - Ithaca differs from typical upstate small cities in ways that could raise or lower use:
    - early adopter: 0.37% EV share in 2015, second in the state;
    - large university and hospital employers;
    - high renter/MUD share;
    - Cornell's commuter parking.
  - The 2016 summary shows university/medical campuses among the more-used venue types (0.42 CE/day per port). Its Southern Tier row is 14 ports, 0.23 CE/day, and 6.2 kWh/CE.
- **Climate and seasonality.** The seasonal signal (summer trough, holiday dips) is system-wide and commuter-driven. It is not separated from temperature effects on vehicle efficiency, and it is not reported by region.
- **No socio-demographic or vehicle data.** No link to EV registrations, local EV density, or user identity, so sessions cannot be tied to vehicles or households.

---

## 6. Modeling implications (site × hour L2 EV load model)

### What this source can constrain (NY-specific priors or validation targets)
1. **Normalized weekday hourly shapes by site class** (Figure 18; 2018–2019 is the most defensible pre-COVID mature period):
   - Workplace: sharp peak at ~9–10 a.m., about 3 h half-width, long afternoon tail, near zero overnight.
   - Public: morning peak at ~9–10 a.m., plus a secondary early-evening shoulder and low overnight use.
   - MUD: evening/overnight peak at ~9 p.m.–midnight, trough at ~6 a.m.–noon, flatter in later years.
   - Use the cluster shapes (Figure 19) as within-class heterogeneity. For example, a workplace-like site can be a mixture of "high morning", "mid morning", and "afternoon" archetypes; a public site mostly "low morning".
2. **Weekday/weekend contrast** (Figure 17): weekend peak utilization is roughly one quarter of the weekday peak in 2018–2019, and flatter and later. This supports a day-type multiplier.
3. **Dwell and charging duration conditional on arrival hour** (Figure 20): mean and median charging duration and idle time by plug-in hour, useful for arrival-to-load convolution.
   - Overall mean charging 2.4 h, median 2.0 h. Mean idle 2.3 h, median 0.5 h (heavy-tailed).
   - Afternoon arrivals have little or no idle time, which suggests energy is limited by departure.
4. **Energy per session:** about 9.7–10.5 kWh mean overall (derived and text); about 12 kWh in Feb 2020 (derived). From 2016 by venue: retail 3.5, workplace 7.6, university/medical 8.0, MUD 18.8, NYC garage 22.3 kWh per CE.
5. **Utilization levels and heavy-tailed station heterogeneity** (useful for Monte Carlo across sites):
   - mean 3.25 kWh per day and 0.32 sessions per day;
   - median 1.5 kWh per day and 0.14 sessions per day;
   - 90th percentile about 11 kWh per day and about 1 session per day;
   - the top ~10% of stations deliver ~50% of energy, the bottom 50% deliver ~8%;
   - roughly lognormal or long-tailed (Figure 11).
   - Land-use medians: workplace about 2× public/MUD. Southern Tier medians are low. These are era-specific levels and should be scaled with EV stock.
6. **Seasonality qualitative signal:** summer trough and late-December dip in system utilization (Figure 15). The amplitude read from the figure is several percentage points on weekly peaks. This is not a clean monthly factor.
7. **Growth and ramp-up:** a new cohort starts at about 2–5% utilization and climbs about 1–1.5 pp per year (Figure 16). This supports a ramp-up term for newly installed ports.
8. **Capacity assumptions:** congestion is rare, so a model that treats each port's arrivals independently (no queueing) is defensible at 2017–2019 demand levels for sites with more than 2 ports.
9. **Costs** (if the model includes infrastructure scenarios): about $6,500 per port median (Charge Ready NY).

### What this source cannot constrain
- **Home or single-family charging** load shapes, energy, or share of total charging.
- **DCFC** behavior.
- **Hourly kW directly.** Only utilization is given, with no per-port power by hour, no session-level power, and no port-count denominators by hour or land use.
- **Session-start (arrival) count distribution** by hour. It must be inferred from utilization plus Figure 20 durations, which is under-identified.
- **Energy-per-session distributions**, whether overall, by hour, or by land use. Only means are available (22-03), plus 2016 venue means.
- **Weekend profiles by land use**, or month × hour interactions.
- **Fine site types** in the 22-03 usage analysis (hotel, retail, municipal, parking, education). Only 2016-era means exist from the companion report.
- **Price elasticity or time-of-use effects.** Most charging was free; the 2016 fee comparison is confounded with NYC garages.
- **Post-2020 behavior** (hybrid work, larger batteries, higher EV density), and **Tompkins-specific** usage. The Southern Tier sample is small and only REDC-level medians are available.
- **Vehicle or user attributes** (BEV vs. PHEV, battery size, SOC), which a physically based charging model would need.
