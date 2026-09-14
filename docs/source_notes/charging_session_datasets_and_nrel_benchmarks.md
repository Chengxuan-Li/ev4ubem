# Charging-session datasets and NREL/NLR model benchmarks (Tompkins County, NY)

**Probe date:** 2026-09-14
**Scope:** (a) public raw EV charging-session datasets; (b) NREL (now NLR, National Laboratory of the Rockies) model outputs with county-level hourly EV load, checked for Tompkins County (FIPS 36109).
**Access rule used:** only anonymous HTTP or S3 access. No accounts, no API keys, no logins. Sources that need any of these are marked **RESTRICTED** and are not relied on.
**Samples written:** `data/raw/samples_probe/` (git-ignored, about 0.8 MB total; list in section 5).

> Note on domain names: `data.nrel.gov` and `docs.nrel.gov` no longer resolve (DNS fails). The same content is now at `data.nlr.gov` and `docs.nlr.gov`. The OEDI S3 buckets are unchanged.

---

## 1. Summary table

Role key: **BP** = behavioral prior (fit arrival, duration and energy distributions). **VR** = validation reference (compare aggregate shapes or magnitudes). **NU** = not useful or not accessible.

| # | Dataset | Access (verified) | Site type | Geography / climate | Period | Size | Key fields | Role |
|---|---|---|---|---|---|---|---|---|
| 1 | **Norway residential, 12 locations, 35k sessions** (Sørensen et al. 2024, Zenodo) | Direct download, no login, CC-BY-4.0 | Home (apartment/housing-coop garages) | Norway, cold climate | 2018-12 to 2020-01 | 3.1 MB sessions; 41 MB hourly | plugin_time, plugout_time, connection_time, energy_session, user_id, location; modeled SoC and hourly energy | **BP (home), top pick** |
| 2 | **Norway residential apartment datasets** (Sørensen et al. 2021, Mendeley jbks2rcwyj) | Direct download, no login, CC-BY-4.0 | Home (apartment garage, private and shared chargers) | Trondheim, Norway | 2018-12 to 2020-01 | about 1 to 5 MB per file | session_ID, User_ID, User_type (Private/Shared), Start_plugin, End_plugout, El_kWh, Duration_hours | BP (home); overlaps #1 |
| 3 | **Dundee City Council public charge-point usage** | Direct CSV (ArcGIS item), no login, OGL-UK | Public, mostly rapid DCFC plus some fast AC | Dundee, Scotland, cool maritime | 2021-07 to 2025-08 (yearly files) | 4 to 14 MB per year | SDR ID, Site, CP ID, Connector Type, Consum(kWh), Duration, Start, End, Postcode | **BP (public DCFC/L2), top pick** |
| 4 | **Perth & Kinross Council charge-station use** | Direct CSV (ArcGIS item), no login, OGL-UK | Public (rapid + fast; P&R, car parks, rural towns) | Perth & Kinross, Scotland (semi-rural) | 2016-09 to 2019-08 | 1.7 to 4.2 MB per year | CP ID, Connector, Start/End date+time, Total kWh, Site, Model | BP (public, small-town/rural) |
| 5 | **City of Boulder CO charging sessions** | ArcGIS FeatureServer REST (no login), CC0 | Public/municipal L2 (+ some DCFC) | Boulder, CO, cold/snowy, university town | 2018-01 to 2023-09 | 148,136 rows | Station, Address, Start/End date-time, Total duration, Charging time, Energy kWh, Port Type | **BP/VR (public L2, US college town), top pick** |
| 6 | **City of Palo Alto charging sessions** | Direct CSV, no login (Open Data Commons badge; ORNL mirror says no license asserted) | Public/municipal L2 | Palo Alto, CA, mild | 2011-07 to 2020-12 | 85.4 MB CSV | Start/End date, total duration, charging time, kWh, Port Type, Plug Type, User ID, Driver Postal Code, lat/lon, fee | BP (public L2, long record); climate caveat |
| 7 | **Workplace charging, 3,395 sessions** (Asensio et al., Harvard Dataverse DVN/QF1PMO) | Direct download, no login, CC0 | Workplace (25 sites, 105 stations, 85 users) | US Midwest manufacturer campus | 2014-11 to 2015-10 | 0.45 MB | sessionId, kwhTotal, created, ended, chargeTimeHrs, userId, stationId, locationId, facilityType, distance, weekday dummies | **BP (workplace), top pick** |
| 8 | UK DfT *Electric Chargepoint Analysis 2017: Domestics* | gov.uk asset CSV, no login, OGL v3 | Home (OLEV-grant domestic chargers) | UK-wide | 2017 | 17.2 MB "incomplete/anomalous" CSV is directly listed; main raw CSV only via archived data.gov.uk link (not re-verified) | ChargingEvent, CPID, StartDate, StartTime, EndDate, EndTime, Energy, PluginDuration | BP (home, large-N) if main file is recovered; else VR via published tables |
| 9 | Caltech ACN-Data (Caltech, JPL, Office001) | **RESTRICTED**: API token after registration for web UI, API and acnportal | Workplace/campus L2 (adaptive) | Pasadena CA | 2018 to 2021+ | n/a | connectionTime, disconnectTime, doneChargingTime, kWhDelivered, userID, userInputs, time-series current | NU under rules (would be BP workplace) |
| 10 | EV WATTS public database (Energetics/DOE) | **RESTRICTED**: Livewire needs a free account to download; ORNL OpenEnergyHub mirror returns `ForbiddenAccess` for records | Public, workplace, fleet, some residential | US, all states | 2019 to 2022 | >13M sessions | session start/end, kWh, power, site type, region (anonymized) | NU under rules; strongest US source if rules relax |
| 11 | DOE EV Data Collection, charging data (INL/NREL/PNNL; Livewire) | **RESTRICTED** (Livewire account) | Mixed | US | through 2023 | n/a | session/daily dictionaries | NU |
| 12 | Pecan Street Dataport | **RESTRICTED**: login plus academic verification. The free Kaggle sample (10 homes, 3 days) also needs a Kaggle login | Home, 1-min circuit-level EV | Austin TX, some NY/CA | 2012+ | n/a | 1-min car1/car2 kW | NU |
| 13 | ElaadNL (NL) | Old platform.elaad.io now redirects to elaad.nl/data. Only aggregated distributions and the synthetic "Laadprofielengenerator" (charging.elaad.nl). The raw open transaction file is no longer offered | Public, home, workplace (aggregates) | Netherlands | 2018 to 2020 aggregates | small | distributions of arrival, connection time, energy | VR (shape sanity check) only |
| 14 | INL EV Project / ChargePoint America / workplace charging studies | Public **reports only** (avt.inl.gov, OSTI). No raw session download | Home, workplace, public | 18 US regions | 2011 to 2015 | PDFs | aggregated demand profiles, home/work split (e.g., Leaf drivers about 65% home, 32% work) | VR (published curves) |
| 15 | SLAC/Stanford workplace | No public raw SLAC session file located. The Sci Data "workplace" paper is dataset #7 (Midwest firm, not SLAC). IEEE DataPort synthetic sets need login | Workplace | CA | n/a | n/a | n/a | NU |
| 16 | Georgia Tech | Same Asensio dataset as #7 (Harvard Dataverse). Kaggle mirror needs login | Workplace | n/a | n/a | n/a | n/a | use #7 |
| 17 | Fort Collins, Chattanooga/EPB, Washington State | No public session-level data found. Only station-location layers (AFDC/NREL-derived) | n/a | n/a | n/a | n/a | n/a | NU |
| 18 | NYSERDA EVSE Use Reports (2013 to 2017, quarterly PDFs); EValuateNY ZIPs | Direct download, no login | Public/limited/private L2 in NYS, by urban/suburban/rural | New York State | 2013 to 2017 | PDFs; EValuateNY v11 pt1/pt2 ZIPs | aggregated utilization and kWh by land-use and access type; EValuateNY charging = AFDC station data, not sessions | **VR (NY-specific)**; see also existing note `nyserda_22-03_charging_usage.md` |
| 19 | NYC DCAS fleet (NYC Open Data *NYC EV Fleet Station Network*) | Direct, no login | Fleet station locations | NYC | current | small | station attributes only, no sessions | NU for load |
| 20 | NY utilities: Con Edison SmartCharge NY evaluation; NYSEG/RG&E and National Grid managed-charging implementation plans (DPS DMM) | Public PDFs on documents.dps.ny.gov | Home (telematics, FleetCarma C2), fleets | NYC (ConEd); upstate (NYSEG/RG&E incl. Ithaca area) | 2018+ | PDFs | average active charging kW (ConEd: BEV 4.0 kW, PHEV 1.3 kW), peak-shift results, enrollment | VR (NY magnitude/shape, managed vs unmanaged) |

---

## 2. Per-dataset details

### 2.1 Norway residential, 35,000 sessions (Zenodo 13896176), recommended
- **Record:** https://zenodo.org/records/13896176 (DOI 10.5281/zenodo.13896176). Article: Data in Brief 57 (2024) 110883, https://doi.org/10.1016/j.dib.2024.110883
- **License:** CC-BY-4.0. **Access:** anonymous direct download (verified with a Range GET).
- **Files (bytes):**
  - `Dataset1_charging_reports.csv` 3,105,240: `location;user_id;session_id;plugin_time;plugout_time;connection_time;energy_session`
  - `Dataset2_user_predictions.csv` 9,687: per-user battery capacity and charging-power estimates
  - `Dataset3_session_predictions.csv` 3,868,748: `user_id;session_id;charging_time;SoC_diff;SoC_start;idle_time;idle_session;non_flex_session`
  - `Dataset4_hourly_predictions.csv` 41,123,497: `user_id;session_id;date_from;energy_charged_i;energy_idle_i;energy_connected_i;SoC_diff_i;SoC_from_i;SoC_to_i`
- **Format quirks:** semicolon delimiter, decimal comma, `NA` for missing values.
- **Coverage:** 267 users, 12 residential locations (housing cooperatives/apartment garages), mature EV market. Sessions run from about 2018-12 to 2020-01 or later (spot rows are from 2019-08 to 2020-01; confirm the exact span from the article or the file after download).
- **Why useful:** the best open *home* charging record with repeat users and true plug-in/plug-out times, plus modeled hourly energy per session. Cold-winter climate lets us test seasonality.
- **Transferability caveats:** apartment/shared-garage residents with high EV maturity (Norway had >50% EV sales by 2019). Most Tompkins EV owners live in single-family homes with private L2 or L1. Norwegian home chargers are often 3.6 to 7.4 kW (some 1-phase 230 V), with different tariffs and commute lengths. Use it for timing (arrival/departure) and plug-in frequency, not directly for kWh per session.

### 2.2 Norway apartment datasets (Mendeley jbks2rcwyj)
- https://data.mendeley.com/datasets/jbks2rcwyj (v3, DOI 10.17632/jbks2rcwyj.3). CC-BY-4.0. The public API lists files, so no login is needed.
- **Files:**
  - `Dataset 1_EV charging reports.csv` (976 KB): `session_ID;Garage_ID;User_ID;User_type;Shared_ID;Start_plugin;Start_plugin_hour;End_plugout;End_plugout_hour;El_kWh;Duration_hours;month_plugin;weekdays_plugin;Plugin_category;Duration_category`
  - `Dataset 2_Hourly EV loads - Per user.csv` (5.4 MB)
  - `Dataset 3a/3b_Hourly EV loads - Aggregated private/shared.csv`
  - further smart-meter files and the article PDF
- **Download URL pattern:** `https://data.mendeley.com/public-files/datasets/jbks2rcwyj/files/<file_id>/file_downloaded`. File IDs come from `https://data.mendeley.com/public-api/datasets/jbks2rcwyj/files?folder_id=root&version=2`. Dataset 1 is file id `2e3b8ced-9887-4a91-b721-8e510e18a127`.
- **Relation to 2.1:** same research group (Trondheim, one location). The 2024 Zenodo release supersedes it for sessions, but the *measured aggregated hourly* private-vs-shared loads here are a useful validation shape.

### 2.3 Dundee City Council public charge-point usage, recommended
- Hub: https://data.dundeecity.gov.uk (search "Public EV Charge Point Usage"). License OGL-UK-3.0.
- **Direct CSV URLs** (ArcGIS items, anonymous; sizes in bytes):
  - 2021-07 to 2021-12: https://www.arcgis.com/sharing/rest/content/items/189b838f51e74f6bb77509d91c47d7c0/data (4,155,268)
  - 2022: https://www.arcgis.com/sharing/rest/content/items/f1a6b5df441d4606821d5f1a78e92d7e/data (10,264,136)
  - 2023: https://www.arcgis.com/sharing/rest/content/items/80df5f177b8c4a94b2bc692835801e8e/data (13,743,007)
  - 2024: https://www.arcgis.com/sharing/rest/content/items/8b443deaf9174b7aa9d3e10eaa906422/data (10,883,129). A second 2024 item, `701795ab29c04e4bbf21f6a4be3404cd`, also exists.
  - 2025-01 to 2025-08: https://www.arcgis.com/sharing/rest/content/items/e185a3a1cfc948a69ada76e950b9d447/data (5,755,833)
- **Schema (verified):** `SDR ID,Site,CP ID,Connector Type,Consum(kWh),Duration,Start,End,Postcode`. Connector Type is e.g. `rapid` or `fast`. Dates are `dd/mm/yyyy hh:mm`, local time.
- **Why useful:** recent (2021 to 2025), large, public DCFC hubs plus AC fast chargers in a mid-size city (about 150k people) with a cool, damp climate and winter seasons.
- **Caveats:** Dundee has high council-owned rapid hub use by taxis and residents without driveways, and UK tariffs differ. Temperature regime is milder than Ithaca (fewer severe cold days). Earlier Dundee years (2017 to 2021) appear in older CKAN releases, not re-verified.

### 2.4 Perth & Kinross Council charge-station use
- Hub: https://data.pkc.gov.uk (tag "electric vehicles"). License: Open Government Licence (acknowledge source).
- **Direct CSV URLs:**
  - 2016-09 to 2017-08: https://www.arcgis.com/sharing/rest/content/items/79cec80b01764d9db32961c3476c9346/data (1.69 MB)
  - 2017-09 to 2018-08: https://www.arcgis.com/sharing/rest/content/items/93748dde99cd45468a5e9c08f61c1953/data (2.62 MB)
  - 2018-09 to 2019-08: https://www.arcgis.com/sharing/rest/content/items/ca6cae3df2624832a2eaf678f2eabee8/data (4.19 MB)
- **Schema (verified):** `_id,CP ID,Connector,Start Date,Start Time,End Date,End Time,Total kWh,Site,Model`
- **Why useful:** public rapid and fast chargers at park-and-rides and small towns, which is closer to the rural/small-town mix around Ithaca. Caveat: old data (2016 to 2019, early adopters), ChargePlace Scotland free-charging period.
- An IEEE DataPort copy exists but needs login. Use the council files.

### 2.5 City of Boulder, CO, recommended (US public L2)
- Portal: https://open-data.bouldercolorado.gov/datasets/95992b3938be4622b07f0b05eba95d4c_0. License CC0 (ArcGIS item licenseInfo).
- Data dictionary: https://webappsprod.bouldercolorado.gov/opendata/ev_datadictionary.csv
- **REST endpoint (verified, anonymous):** `https://services.arcgis.com/ePKBjXrBZ2vEEgWd/arcgis/rest/services/Electric_Vehicle_Charging_Station_Data/FeatureServer/0/query`
  - `returnCountOnly=true` gives 148,136 records
  - Start_Date___Time ranges from 1/1/2018 17:49 to 9/9/2023 9:19 (string field)
  - The Hub CSV download (`/api/download/v1/items/.../csv?layers=0`) did not respond in this probe. Page through the FeatureServer instead (below).
- **Fields:** Station_Name, Address, City, State_Province, Zip_Postal_Code, Start_Date___Time, Start_Time_Zone, End_Date___Time, End_Time_Zone, Total_Duration__hh_mm_ss_, Charging_Time__hh_mm_ss_, Energy__kWh_, GHG_Savings__kg_, Gasoline_Savings__gallons_, Port_Type. There is no user ID.
- **Why useful:** a US university town (about 105k people, CU Boulder) with cold, snowy winters and a municipal L2 network (rec centers, libraries, garages). This is the closest US analogue to Ithaca public L2. Both plug-in duration and active charging time are present, so idle time can be derived.
- **Caveats:** high-altitude sunny climate, fewer cloudy days than Ithaca. City-owned sites only. Times are stored as strings with a zone column (MDT/MST), so parse with care.

### 2.6 City of Palo Alto
- Portal: https://data.paloalto.gov/datasets/194693/electric-vehicle-charging-station-usage-july-2011-dec-2020/
- **Full CSV (verified, 85,445,823 bytes):** https://data.paloalto.gov/datasets/194693-electric-vehicle-charging-station-usage-july-2011-dec-2020.download/. Send a browser User-Agent; the UI export caps at 10k rows, but this link returns the whole file.
- **Schema (verified header):** Station Name, MAC Address, Org Name, Start Date, Start Time Zone, End Date, End Time Zone, Transaction Date (Pacific Time), Total Duration, Charging Time, Energy (kWh), GHG Savings, Gasoline Savings, Port Type, Port Number, Plug Type, EVSE ID, Address 1, City, State/Province, Postal Code, Country, Latitude, Longitude, Currency, Fee, Ended By, Plug In Event Id, Driver Postal Code, User ID, County, System S/N, Model Number.
- **Role:** a long US public L2 record with a user ID and driver ZIP, useful for repeat-user behavior. **Caveat:** mild California climate and a very high-income, early-adopter tech workforce. Poor transfer to upstate NY for seasonality.

### 2.7 Workplace charging, Harvard Dataverse DVN/QF1PMO, recommended (workplace)
- https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/QF1PMO. License CC0. File `ev_workplace_charging_data.tab` (447,586 bytes), not restricted.
- **Direct download:** `https://dataverse.harvard.edu/api/access/datafile/4491950` (tab-delimited; verified).
- **Fields:** sessionId, kwhTotal, dollars, created, ended, chargeTimeHrs, platform, distance, userId, stationId, locationId, managerVehicle, facilityType, Mon to Sun dummies, reportedZip, totalSessions, habitualUser, earlyAdopter.
- **Coverage:** 3,395 sessions, 85 drivers, 105 stations, 25 facilities of one Midwest US manufacturer, Nov 2014 to Oct 2015. Paper: Sci Data 8, 175 (2021), https://doi.org/10.1038/s41597-021-00956-1
- **Caveats:** early-adopter period, small N, paid and free sessions, a single employer. Midwest climate is a reasonable analogue. Use it for workplace arrival/dwell shapes (Cornell, Ithaca College, hospital, downtown employers).

### 2.8 UK DfT Electric Chargepoint Analysis 2017: Domestics
- Landing: https://www.gov.uk/government/statistics/electric-chargepoint-analysis-2017-domestics; data.gov.uk: https://www.data.gov.uk/dataset/5438d88d-695b-4381-a5f2-6ea03bf3dcf0/electric-chargepoint-analysis-2017-domestics
- **Directly listed files (gov.uk content API, verified):**
  - report PDF: https://assets.publishing.service.gov.uk/media/5c114a0fe5274a0bad85ade0/electric-chargepoint-analysis-2017-domestics.pdf
  - summary tables ODS: https://assets.publishing.service.gov.uk/media/5c114a23ed915d0c1bc0d585/electric-chargepoint-analysis-2017-domestics-tables.ods
  - **incomplete/anomalous raw CSV** (17,226,730 bytes): https://assets.publishing.service.gov.uk/media/5c114a59e5274a0bf3cbe173/electric-chargepoint-analysis-2017-domestics-incomplete-anomalies.csv. Header: `ChargingEvent,CPID,StartDate,StartTime,EndDate,EndTime,Energy,PluginDuration`
- **Main raw domestics CSV** (the roughly 3.2M-event file): data.gov.uk now points only to a National Archives snapshot of the old CKAN resource (`webarchive.nationalarchives.gov.uk/ukgwa/20230106125147/https://ckan.publishing.service.gov.uk/dataset/5438d88d-.../resource/e4a2198c-...`). The snapshot page returned no CSV link in this probe, and data.gov.uk was erroring. **Status: not verified.** Retry later, or use the published ODS tables (median 7.5 kWh, mean 9.1 kWh per event) as a VR.
- **Caveats:** 2017 UK home chargers (mostly 3.6 to 7 kW), dominated by early Leaf/PHEV owners. No household attributes and no user ID beyond CPID.

### 2.9 Caltech ACN-Data (RESTRICTED)
- https://ev.caltech.edu/dataset. "We ask all users to register in order to use the ACN-Data API." This applies to the web download, REST API and the `acnportal` client alike. No anonymous bulk dump was found. **Not used.**

### 2.10 EV WATTS and DOE EV Data Collection (RESTRICTED)
- Livewire: https://livewire.energy.gov/project/evwatts and https://livewire.energy.gov/ds/evwatts/evwatts.public. The single-page app loads anonymously, but DOE/OSTI docs state a free account is needed to download. OSTI: https://www.osti.gov/biblio/1970735
- The ORNL OpenEnergyHub mirror (`openenergyhub.ornl.gov/explore/dataset/ev-watts/`) lists metadata only (records_count 0). The records API returns `ForbiddenAccess`. Same for `doe-ev-data-collection-charging-data` (OSTI 1989855).
- **Not used.** EV WATTS PDF summary reports (e.g., https://www.clearesult.com/sites/default/files/2024-05/EVWATTS_EV_National.pdf) are public and can serve as a VR.

### 2.11 Pecan Street Dataport (RESTRICTED)
- https://dataport.pecanstreet.org requires login and academic ID verification. The Kaggle sample needs a Kaggle account. **Not used.**

### 2.12 ElaadNL
- `platform.elaad.io` gives 301 to `elaad.nl/data`. The download page (https://elaad.nl/delen/download) lists open files, but currently only non-session items. The 2018 to 2020 "Open Data Dashboard" offered *aggregated* distributions (arrival time, connection duration, energy, charging curves) by location type, not raw transactions. A synthetic profile generator is at https://charging.elaad.nl/.
- **Role:** VR only, for normalized Dutch public/home/work shape comparison.

### 2.13 INL EV Project / workplace charging
- Public reports: e.g., https://www.osti.gov/biblio/1244615 (ARRA final report) and https://www.energy.gov/sites/prod/files/2014/02/f8/evs26_charging_demand_manuscript.pdf (residential charging demand profiles). There is no public raw session download.
- **Role:** VR for published weekday/weekend residential demand shapes (2011 to 2013, with and without TOU rates). Caveat: Leaf/Volt early adopters, mostly L2, several TOU-rate regions.

### 2.14 New York-specific sources
- **NYSERDA EV/EVSE data page:** https://www.nyserda.ny.gov/All-Programs/Drive-Clean-Rebate-For-Electric-Cars-Program/Rebate-Data/Data-on-Electric-Vehicles-and-Charging-Stations
  - EVSE Use Reports 2013 to 2017, e.g., https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/EV-Charging-Station-Data/2014-EVSE-Use-Report-Q1.pdf. They give aggregated usage and load by urban/suburban/rural and public/limited/private access. **VR (NY public L2, old).**
  - EValuateNY v11 raw ZIPs: `https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/Research/Transportation/EValuateNY%5Fv11%5Fpt1.zip` and `...%5Fpt2.zip`. Their charging component is AFDC station inventory, not sessions.
  - EV registrations CSV: https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Programs/ChargeNY/ny%5Fev%5Fregistrations.csv (covered in other notes)
- **data.ny.gov:** *Charge Ready NY Programs* (https://data.ny.gov/Energy-Environment/Charge-Ready-NY-Programs-Beginning-2018/9wxk-hakb) and *EV Charging Stations in NY* (7rrd-248n). Installations and locations only, no sessions.
- **NYC DCAS:** *NYC EV Fleet Station Network* (https://data.cityofnewyork.us/City-Government/NYC-EV-Fleet-Station-Network/fc53-9hrv). Station attributes only.
- **Utilities (PSC filings, public PDFs):**
  - Con Edison SmartCharge NY impact evaluation: https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7BBF5BB327-2EF4-4A4C-9692-8DA7C78D707C%7D. FleetCarma telematics; reports BEV about 4.0 kW and PHEV about 1.3 kW average active charging load, plus peak-period shift.
  - NYSEG/RG&E EV Managed Charging Implementation Plan: https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B60EEB894-0000-CB12-883C-4C3E5137E61C%7D. Commercial plan: `...%7B80AF6A89-0000-CF1F-87B0-F38BFD0C5507%7D`. NYSEG is Tompkins County's electric utility, and its OptimizEV program is run with ev.energy.
  - National Grid (Niagara Mohawk) filing: `...%7B90F9568D-0000-C71A-ADD5-A62A54A29A1D%7D`
  - No NY utility publishes session-level or hourly EV load *data*. The Joint Utilities portals (https://jointutilitiesofny.org/utility-specific-pages/system-data/historical-load-data) publish system/feeder load, not EV-specific load.
  - **Role:** VR (NY-specific magnitudes, managed-charging response). Mine the NYSEG/RG&E program annual reports in the PSC EV proceeding (Case 18-E-0138) for upstate numbers.

---

## 3. Ranked recommendation: datasets to acquire

| Rank | Dataset | Primary use | Why it wins |
|---|---|---|---|
| **1** | Norway residential 35k sessions (Zenodo 13896176) | Home arrival/departure, dwell, plug-in frequency, per-user heterogeneity; cold-climate seasonality | Only open multi-site *home* dataset with true plug-in/out times and user IDs; CC-BY; 48 MB total |
| **2** | City of Boulder CO sessions (ArcGIS REST) | Public L2 (and some DCFC) arrival/energy/duration by weekday and season in a cold US college town | 148k sessions, CC0, US units/behavior, snow climate, recent (2018 to 2023) |
| **3** | Workplace charging (Harvard Dataverse QF1PMO) | Workplace arrival/dwell/kWh, habitual vs casual users | Only open, login-free US workplace session file; CC0; tiny |
| **4** | Dundee public charge-point usage 2022 to 2025 (+ Perth & Kinross 2016 to 2019 for small-town/rural) | DCFC session energy/duration and diurnal/seasonal shape | Recent, large, direct CSV, OGL; cool climate; DCFC coverage missing from the US open sets |

Secondary/validation: Palo Alto (a long US L2 record with user IDs, but a poor climate analogue), the Norway Mendeley aggregated hourly loads, the UK DfT 2017 domestic tables, NYSERDA EVSE Use Reports, and the Con Edison SmartCharge and NYSEG/RG&E filings.

### 3.1 Acquisition commands (bash/curl; run from repo root)

```bash
mkdir -p data/raw/charging_sessions/{norway_zenodo_13896176,boulder_co,workplace_dvn_qf1pmo,dundee,perth_kinross}

# 1. Norway residential (CC-BY-4.0), about 48 MB total
for f in Dataset1_charging_reports.csv Dataset2_user_predictions.csv Dataset3_session_predictions.csv Dataset4_hourly_predictions.csv 1-s2.0-S2352340924008461-main.pdf; do
  curl -L -o "data/raw/charging_sessions/norway_zenodo_13896176/$f" "https://zenodo.org/api/records/13896176/files/$f/content"
done

# 2. Boulder CO (CC0): page the FeatureServer (maxRecordCount likely 1000-2000), 148,136 rows
python - <<'EOF'
import json, urllib.request, urllib.parse, csv
base="https://services.arcgis.com/ePKBjXrBZ2vEEgWd/arcgis/rest/services/Electric_Vehicle_Charging_Station_Data/FeatureServer/0/query"
rows=[]; off=0
while True:
    q=urllib.parse.urlencode({"where":"1=1","outFields":"*","orderByFields":"ObjectId2","resultOffset":off,"resultRecordCount":2000,"f":"json"})
    d=json.load(urllib.request.urlopen(base+"?"+q)); feats=d.get("features",[])
    rows+= [f["attributes"] for f in feats]; off+=len(feats)
    if not feats or not d.get("exceededTransferLimit"): break
with open("data/raw/charging_sessions/boulder_co/boulder_ev_sessions_2018_2023.csv","w",newline="",encoding="utf8") as fh:
    w=csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows))
EOF
curl -L -o data/raw/charging_sessions/boulder_co/ev_datadictionary.csv https://webappsprod.bouldercolorado.gov/opendata/ev_datadictionary.csv

# 3. Workplace (CC0), 0.45 MB
curl -L -o data/raw/charging_sessions/workplace_dvn_qf1pmo/ev_workplace_charging_data.tsv "https://dataverse.harvard.edu/api/access/datafile/4491950"

# 4. Dundee (OGL-UK), about 45 MB total
for id in 189b838f51e74f6bb77509d91c47d7c0 f1a6b5df441d4606821d5f1a78e92d7e 80df5f177b8c4a94b2bc692835801e8e 8b443deaf9174b7aa9d3e10eaa906422 e185a3a1cfc948a69ada76e950b9d447; do
  curl -L -o "data/raw/charging_sessions/dundee/$id.csv" "https://www.arcgis.com/sharing/rest/content/items/$id/data"
done
#    Perth & Kinross (OGL), about 8.5 MB total
for id in 79cec80b01764d9db32961c3476c9346 93748dde99cd45468a5e9c08f61c1953 ca6cae3df2624832a2eaf678f2eabee8; do
  curl -L -o "data/raw/charging_sessions/perth_kinross/$id.csv" "https://www.arcgis.com/sharing/rest/content/items/$id/data"
done

# optional: Palo Alto (85 MB)
curl -L -A "Mozilla/5.0" -o data/raw/charging_sessions/palo_alto_2011_2020.csv "https://data.paloalto.gov/datasets/194693-electric-vehicle-charging-station-usage-july-2011-dec-2020.download/"
```

### 3.2 Transferability caveats for all session datasets (upstate NY)
- **Climate:** Ithaca winters (heating-degree days about 7,000 °F-day, frequent sub-0 °F nights) cut EV efficiency by 20 to 40% and raise kWh per mile and battery pre-conditioning load. Only Norway and Boulder see comparable cold. Dundee and Perth are milder. Palo Alto is not comparable.
- **Housing/land use:** Tompkins mixes single-family owner-occupied homes (private L1/L2) with a large renter and student population (Cornell, IC) that has little home charging. Norway data comes from apartment garages, and Boulder and Dundee represent municipal public networks. Weight the priors by home-charging access class.
- **Market maturity:** early-adopter datasets (Palo Alto 2011 to 2015, the workplace set 2014 to 2015, PKC 2016 to 2019, DfT 2017) over-represent short-range PHEVs and free charging. Prefer post-2019 records for kWh per session.
- **Tariffs:** NYSEG residential rates are flat by default, with an optional TOU and OptimizEV managed charging program. Norway (spot price), UK (Economy 7) and Boulder (Xcel TOU) behave differently. Evening-peak timing transfers better than off-peak timer spikes.

---

## 4. NREL/NLR model-output benchmarks for Tompkins County (FIPS 36109)

### 4.1 TEMPO county LDV charging profiles v2022 (dsgrid), **the Tompkins-level hourly path exists**
- **OEDI submission:** https://data.openei.org/submissions/5958 (CC-BY-4.0). **Docs:** https://github.com/dsgrid/dsgrid-project-StandardScenarios/tree/main/tempo_project. **Tech report:** Yip et al. 2023, https://www.nrel.gov/docs/fy23osti/83916.pdf (NREL/TP-5400-83916)
- **Bucket:** `s3://nrel-pds-dsgrid/tempo/tempo-2022/v1.0.0/` (public, region us-west-2, `--no-sign-request`). HTTP listing works: `https://nrel-pds-dsgrid.s3.amazonaws.com/?list-type=2&prefix=tempo/tempo-2022/v1.0.0/`
- **Folders (verified):**

| Folder | Content | Size / partitioning |
|---|---|---|
| `full_dataset/table.parquet/scenario=<s>/tempo_project_model_years=<y>/state=<ST>/part-*.parquet` | hourly × county × 720 household-vehicle types × 2 end uses | 796 GB total, 13,437 files; NY 23.3 GB |
| `full_state_level/` | hourly × state × subsector | about 119 GB |
| `state_level_simplified/table.parquet/scenario=<s>/` | hourly × state × 8 subsectors, one end use | about 345 MB per scenario |
| `annual_summary_county/table.parquet/part-00000-711279c3-...parquet` | annual × county × 8 subsectors × 5-yr intervals | 3.2 MB |
| `annual_summary_state/`, `annual_summary_conus/` | annual | 1 MB / 5 KB (CSV also) |

- **Scenarios (partition values):** `reference` (AEO2018-aligned), `efs_high_ldv` (EFS High Electrification), `ldv_sales_evs_2035` (50% EV sales 2030, 100% 2035).
- **Model years:** 2024 to 2050 in 2-year steps (14 years). **Weather year:** 2012 AMY.
- **Schema of `full_dataset` (verified via Parquet footer):** `time_est: timestamp[ns]`, `end_use: string`, `household_and_vehicle_type: string`, `transportation: string`, `weather_2012: string`, `value: double`, `county: string`. Partition columns add `scenario`, `tempo_project_model_years`, `state`.
  - `county` is the 5-digit FIPS string, e.g. `"36109"`
  - `end_use` ∈ {`electricity_ev_l1l2`, `electricity_ev_dcfc`}
  - 720 subsector labels like `Single_Driver+Middle_Income+Rural+Pickup+BEV_100` (driver count × income × urbanity × size class × powertrain/range)
  - **Units: MWh per hour** (OEDI README: "All energy use reported in the OEDI data is in MWh")
  - **Time:** stored UTC, 8,784 hourly steps from `2012-01-01 05:00` to `2013-01-01 04:00` UTC, i.e. period-beginning EST hours of 2012 (subtract 5 h). Profiles already reflect local DST behavior.
- **Tompkins extraction cost (verified by scanning all 438 NY file footers for county min/max statistics):**
  - Files are sorted by county. Partitions for later years hold 13 files, and **Tompkins is always in exactly one file** (e.g., `part-00251-*`, county range 36103 to 36109).
  - Each file is a single Parquet row group, so a filter must read that whole file (no row-group skipping).
  - **45 files, 3.07 GB total, cover all 3 scenarios × 14 years for Tompkins.** Per file: 26 to 150 MB. Complete list with exact S3 keys: `data/raw/samples_probe/tempo2022_full_dataset_files_containing_county36109.csv`.
  - A single scenario-year costs 0.03 to 0.15 GB. For example, reference MY2024 is `scenario=reference/tempo_project_model_years=2024/state=NY/part-00247-d668d769-0c35-46e0-94bc-3fa450b31efc.c000.snappy.parquet` (91.2 MB, all 62 NY counties, 33.7M rows). **County-level extraction is feasible well under 1 to 2 GB** if you pick a few scenario-years.
- **Verified extraction** (pyarrow, anonymous S3, streamed in memory, about 30 to 45 s, nothing written except the Tompkins subset):

```python
import pyarrow.parquet as pq, pyarrow.fs as pfs
fs = pfs.S3FileSystem(anonymous=True, region="us-west-2")
f = ("nrel-pds-dsgrid/tempo/tempo-2022/v1.0.0/full_dataset/table.parquet/scenario=reference/"
     "tempo_project_model_years=2024/state=NY/part-00247-d668d769-0c35-46e0-94bc-3fa450b31efc.c000.snappy.parquet")
df = pq.read_table(f, filesystem=fs, filters=[("county", "=", "36109")]).to_pandas()   # 2,233,480 rows
hourly = df.groupby(["time_est", "end_use"])["value"].sum().unstack()                  # MWh per UTC hour
```
  (The anaconda Python on this machine has pyarrow 19 and duckdb 1.2. The project venv lists `pyarrow>=15`.)

- **Tompkins result, reference scenario, MY2024:**
  - Annual 21,579 MWh, of which L1/L2 21,363 MWh and DCFC 216 MWh (1%)
  - The mean hourly profile peaks at 21:00 UTC-labelled hour, which is **about 16:00 EST**. Mean load per UTC-labelled hour runs from about 0.65 MWh (08 UTC, i.e. 03:00 EST) to about 4.1 MWh (21 UTC). This fits "immediate charging after the last trip".
- **Annual summary for Tompkins** (`annual_summary_county`, MWh, sum of 8 subsectors; the 2012 weather year appears as `year`):

| scenario \ 5-yr interval | 2025 | 2030 | 2035 | 2040 | 2045 | 2050 |
|---|---|---|---|---|---|---|
| reference | 22,785 | 36,123 | 52,298 | 69,062 | 92,864 | 104,898 |
| efs_high_ldv | 15,595 | 63,412 | 126,080 | 190,817 | 229,289 | 260,385 |
| ldv_sales_evs_2035 | 13,537 | 41,348 | 126,462 | 205,888 | 267,277 | 321,957 |

- **Caveats (critical for use as a benchmark):**
  1. **Ubiquitous charger access plus immediate charging.** This is a stated *bounding case*. Energy totals are plausible, but timing is biased early (afternoon/evening right after trips) and too smooth. Every trip end is a plug-in event, so sessions far exceed real frequency. Do **not** use it for peak timing or session statistics.
  2. **Stock is projected from AEO2018-era adoption, not observed registrations.** The reference 2024/2025 totals (about 21 to 23 GWh/yr, roughly 6,000+ EVs at about 3.5 MWh/yr) look high against observed Tompkins registrations. Cross-check with the NYSERDA registration CSV. The EFS-High 2025 value is *lower* than reference, so scenario trajectories differ in near years.
  3. LDV household passenger vehicles only: no fleets, MD/HD vehicles, ride-hail, or non-resident commuters or visitors (relevant for Cornell). County assignment follows household residence, not where charging happens.
  4. 2012 weather, EST period-beginning timestamps stored as UTC.
- **Recommended role:** VR for *annual energy magnitude by scenario* and for vehicle-mix composition. It is a weak, upper-bound reference for hourly shape (unmanaged, ubiquitous). Pair it with session-based priors for timing.

### 4.2 ResStock 2025 Release 1 (AMY2018): EV charging end use per dwelling, **the Tompkins subset is extractable**
- **Bucket:** `s3://oedi-data-lake/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2025/resstock_amy2018_release_1/` (public). Data dictionary: `.../data_dictionary.tsv`. Upgrades: `.../upgrades_lookup.json`.
- **EV fields:**
  - inputs `in.electric_vehicle_ownership`, `in.electric_vehicle_charger` (None/L1/L2), `in.electric_vehicle_battery`, `in.electric_vehicle_miles_traveled`, `in.electric_vehicle_charge_at_home`, `in.electric_vehicle_outlet_access`
  - outputs `out.electricity.ev_charging.energy_consumption..kwh` (annual and timeseries) and `out.unmet_hours.ev_driving..hour`
  - (ResStock 2024.1 has no EV fields.)
- **EV upgrades:** 19 L1 adoption; 20 L2 adoption; 21 efficient EV + L2; 22 L2 + demand flexibility; 23 efficient + L2 + flexibility. Baseline is upgrade 0.
- **Paths:**
  - metadata/annual: `metadata_and_annual_results/by_state/full/parquet/state=NY/NY_upgrade{N}.parquet` (34 to 58 MB; 771 columns; column-projected reads are small)
  - individual 15-min timeseries: `timeseries_individual_buildings/by_state/upgrade={N}/state=NY/{bldg_id}-{N}.parquet` (about 6 to 7 MB each, 35,040 rows, `timestamp` from 2018-01-01 00:15 to 2019-01-01 00:00, i.e. period-ending; that it is local standard time is ResStock convention, not verified here)
  - state aggregates: `timeseries_aggregates/by_state/upgrade={N}/state=NY/up{N}-ny-<building_type>.csv` (about 60 MB each). There is **no by-county aggregate folder**; available aggregations are by state, ISO/RTO, and climate zone.
- **Verified Tompkins numbers** (`in.county == "G3601090"`):
  - 173 dwelling-unit samples, weight 253.9 each, sum 43,925 units
  - **Baseline (upgrade 0):** 2 samples own EVs (both single-family detached, L1, 9,000 and 15,000 mi/yr, 2,831 and 3,527 kWh/yr). Weighted Tompkins residential EV charging is **1,614 MWh/yr** (NY-wide weighted EV ownership 0.58% of dwellings).
  - **Upgrade 20** (EV + L2 for all applicable units, 157/173 applicable): 84,938 MWh/yr, a full-adoption bound.
  - Hourly baseline profile (weighted sum of the 2 samples): peaks 18:00 to 21:00 (about 480 kWh/h), minimum 08:00 to 10:00. Saved to `resstock2025r1_upgrade0_tompkins_ev_samples_weighted_hourly_kwh.csv`.
- **Caveats:** only 2 EV-owning samples in the county baseline, so the county-level baseline EV load is statistically meaningless (pure sampling noise). Use state-level or regional (NY upstate PUMA) sample pools. The EV module is behavior-driven (trip schedules from ATUS/NHTS, home-charging share), which suits hourly shape by building type better than TEMPO. It covers only home charging at dwellings, and at most one EV per dwelling.
- **Recommended role:** **the best open model benchmark for *home* charging shape by building type.** Aggregate the NY or upstate-NY EV-owning samples, or run upgrades 19/20 over Tompkins's 173 samples: about 1.1 GB of full files, but column-projected reads of `timestamp` + EV column need about 2 s per building. This result is also a direct building-level link for the UBEM.

### 4.3 Electrification Futures Study load profiles (EnergyPATHWAYS), state level only
- https://data.nlr.gov/submissions/126 (DOI 10.7799/1593122; the old data.nrel.gov host is dead)
- 9 ZIPs, one per electrification × technology scenario: e.g. `https://data.nlr.gov/system/files/126/EFSLoadProfile_Reference_Moderate.zip`. That link 302-redirects to a presigned `nrel-datacat-public-prod` S3 URL, which supports Range.
- Each ZIP (about 290 to 305 MB) holds **one CSV of about 2.82 GB** (`EFSLoadProfile_Reference_Moderate.csv`), stored with a compression method Python's zipfile cannot read (likely Deflate64), so partial extraction is impractical.
- **Content:** hourly load by state × sector × subsector (including light-duty vehicles) for 2018, 2020, 2024, 2030, 2040, 2050. Scenarios: Reference/Medium/High × Slow/Moderate/Rapid.
- **Tompkins:** **no county data.** Downscaling NY LDV via registrations would be needed. The EFS dsgrid bucket (`s3://oedi-data-lake/dsgrid-2018-efs/`, `.dsg` HDF5 files) has *no transportation sector* (commercial, residential, industrial, outdoor lighting, municipal water, DG, rail only).
- **Role:** superseded by TEMPO for LDV. Optional VR only.

### 4.4 Other NREL items checked
- **OEDI 8265, *2030 National Charging Network*:** EVSE port counts by state and CBSA for 2025/2030. No hourly load, no county. Ithaca CBSA port counts could be a useful VR for public-charger supply.
- **NREL/NLR "Forward-Looking Dataset of EV Managed Charging Resource and Costs"** (presentation Aug 2025, https://docs.nlr.gov/docs/fy26osti/96548.pdf): announces hourly 8760 unmanaged and managed load profiles for counties and/or ReEDS BAs, 2025 to 2050, with scenarios High-Baseline/Daytime/Flat/Flexible/Stress, built on TEMPO + EVI-Pro + dsgrid-flex. **No public OEDI/S3 path was found in this probe.** Watch https://data.openei.org and `s3://nrel-pds-dsgrid/`, which currently holds only `building/` and `tempo/`. This would be the preferred successor to 4.1, because it uses realistic EVI-Pro charging instead of ubiquitous-immediate charging.
- **EVI-Pro Lite API** (load profiles by vehicle count, temperature, home/work access): needs a developer API key (signup). **RESTRICTED.** The web tool at afdc.energy.gov/evi-pro-lite is interactive only.
- **Buildings Sector Scenarios** (`s3://oedi-data-lake/buildings-sector-scenarios/dmd_cal_ann_state_county_hourly/`): county-hourly *building* demand by state file (e.g., com NY 2026 is 85 MB). No EV end use was identified from the folder structure; not probed further.
- **dsgrid building-2021** (`s3://nrel-pds-dsgrid/building/building-2021/`): ResStock/ComStock 2021, no EV.

### 4.5 Bottom line for Tompkins County
- **Exact public hourly county path exists:** `s3://nrel-pds-dsgrid/tempo/tempo-2022/v1.0.0/full_dataset/table.parquet/scenario={reference|efs_high_ldv|ldv_sales_evs_2035}/tempo_project_model_years={2024..2050}/state=NY/` with a filter of `county == "36109"`. The one file per partition that contains Tompkins is listed in `tempo2022_full_dataset_files_containing_county36109.csv`: 45 files, 3.07 GB for everything, 26 to 150 MB per scenario-year.
- It is a model upper-bound shape (ubiquitous/immediate charging) with AEO2018-era stock. Use it for energy-magnitude bracketing, not timing.
- ResStock 2025.1 gives a behavior-based home-charging benchmark with county tags, but too few EV samples in Tompkins. Pool NY samples.

---

## 5. Probe samples saved (git-ignored)

`E:\Coding\ev4ubem\data\raw\samples_probe\`
| File | Content |
|---|---|
| `tempo2022_annual_summary_county36109.csv` | TEMPO annual MWh, Tompkins, 3 scenarios × 6 intervals × 8 subsectors |
| `tempo2022_reference_my2024_county36109_hourly_by_enduse.csv` | 8,784 h × {L1L2, DCFC} MWh, Tompkins, reference MY2024 (UTC timestamps) |
| `tempo2022_reference_my2024_county36109_annual_by_subsector.csv` | annual MWh by 720 household-vehicle types × end use |
| `tempo2022_full_dataset_files_containing_county36109.csv` | exact S3 keys and sizes of the 45 files containing 36109 |
| `resstock2025r1_upgrade20_tompkins_metadata_subset.csv` | 173 Tompkins samples: weight, EV inputs, annual EV kWh (upgrade 20) |
| `resstock2025r1_upgrade0_tompkins_ev_samples_weighted_hourly_kwh.csv` | weighted hourly EV kWh of the 2 baseline EV-owning samples |

No session datasets were downloaded; only a few KB of headers were read through Range requests.
