# EV Ownership and Charging Data Research — Tompkins County / Ithaca

**Date:** 2026-09-14  
**Status:** Autonomous research handoff  
**Primary scope:** Tompkins County and Ithaca, New York  
**Temporal focus:** 2024–2026 current conditions, with historical trends and future projections where useful

## 1. Mission

Investigate the **publicly downloadable/API-accessible data** that can support a defensible model of EV ownership and charging load for Tompkins County / Ithaca.

The downstream application is an urban/building energy model. EV charging will ultimately be represented as **hourly electrical load** associated with buildings, sites, or other spatial entities. This phase is primarily about data acquisition, cross-checking, exploratory analysis, model feasibility, and validation design—not prematurely implementing a final EV model.

The work should advance through actual data acquisition and analysis rather than stop at a literature/source inventory.

Core questions:

1. **EV ownership / stock**
   - How many BEVs and PHEVs are registered in Tompkins County and Ithaca-area ZIP codes?
   - How has this changed over time?
   - What vehicle types, makes, model years, and characteristics are observable?
   - At what spatial resolution can ownership be observed directly?

2. **Population / building distribution**
   - What household, housing, socioeconomic, travel, and locational characteristics are associated with EV ownership?
   - Which characteristics are locally available at useful spatial resolution?
   - Can observed ZIP-level totals be spatialized plausibly to census geographies, parcels, households, or buildings?
   - Which household/building classes appear to have systematically different EV ownership rates?

3. **Charging behavior**
   - What empirical evidence exists on charging frequency, start/end time, session energy, charging power, home/work/public split, weekday/weekend effects, seasonality, and charging access?
   - Which distributions can be estimated from New York data versus national/nonlocal sources?
   - Which sources provide raw/downloadable session data versus only published summaries?

4. **Validation**
   - Which observed datasets can directly validate local ownership assumptions?
   - Which observed charging datasets can validate hourly charging patterns?
   - Which sources are measurements versus model outputs usable only for benchmarking?

5. **Model feasibility**
   - Given the available evidence, what can reasonably be modeled at building/site/hourly resolution?
   - What assumptions would remain unvalidated?
   - What simple, relatively simple, and moderate-complexity formulations are justified?

Do not force the final research into these exact categories if the data suggest a better structure.

---

## 2. Downstream constraint

The final EnergyAtlas/RC integration only requires **hourly EV electrical load**:

```text
site/building/entity × hour -> EV charging kWh or hourly-average kW
```

Sub-hourly source data are useful for learning event distributions and aggregating events accurately, but the final model output need not be finer than hourly.

EV charging should generally be treated as a separate electrical end use rather than part of the building thermal RC equations.

Potential spatial endpoints include:

- residential building;
- multifamily property;
- workplace/commercial building;
- campus/site;
- public charging station/parcel;
- another external electrical-load entity where a charger is not meaningfully tied to a thermally modeled building.

---

## 3. Geographic and temporal scope

### Geography

Prioritize:

1. Tompkins County;
2. City/Town of Ithaca and Ithaca-area ZIP codes;
3. local census tracts/block groups;
4. local parcels/buildings where public data permit.

Use New York State as the main comparison/reference geography. Use national data where important variables or behavioral evidence are unavailable locally. Use non-New-York charging data only as behavioral priors, sensitivity ranges, or external validation references, with transferability limitations documented.

### Time

Center the analysis on **2024–2026**. Also investigate:

- historical trends where consistent data exist;
- EV stock, market share, vehicle mix, and infrastructure growth;
- future trend projections when useful for model extensibility.

Do not let long-range forecasting displace the current-period analysis.

---

## 4. Public-data-only constraint

Use only datasets that are publicly downloadable or available through public APIs/endpoints.

You may note useful nonpublic datasets if encountered, but:

- do not make progress depend on obtaining them;
- do not contact organizations for access;
- do not build the primary workflow around confidential/proprietary data.

Classify sources as:

- **publicly available and acquired**;
- **publicly available but not yet acquired/processed**;
- **public summary only / raw data unavailable**;
- **nonpublic or restricted**.

---

## 5. Strong initial source leads

These are starting points, not a closed list. Verify them independently and search for newer/better sources.

### 5.1 New York DMV vehicle registrations

**Dataset:** NYS DMV Vehicle, Snowmobile, and Boat Registrations  
**Portal:** New York Open Data  
**Known dataset ID:** `w4pv-hbkt`

Dataset page:  
https://data.ny.gov/Transportation/Vehicle-Snowmobile-and-Boat-Registrations/w4pv-hbkt

Public data dictionary:  
https://data.ny.gov/api/views/w4pv-hbkt/files/nnqYEBpA-BzyJbpU7VZOkoPwDhS02i8-jOD95M_H4xw?download=true&filename=NYSDMV_VehicleSnowmobileandBoat_Registrations_DataDictionary.pdf

Useful fields include ZIP, county, model year, make, body type, fuel type, registration class, registration validity/expiration fields, and partially redacted VIN information.

Investigate:

- current Tompkins EV stock;
- ZIP-level counts;
- BEV/PHEV identification methodology;
- denominator of total passenger/light-duty vehicles;
- duplicate/renewal issues;
- historical snapshots;
- direct fuel-type filtering versus VIN-prefix decoding;
- schema/definition changes over time.

Do not assume every row is a unique currently active household vehicle without testing registration semantics.

### 5.2 NYSERDA EValuateNY / EV registration data

Landing page:  
https://www.nyserda.ny.gov/All-Programs/Drive-Clean-Rebate-For-Electric-Cars-Program/Rebate-Data/Data-on-Electric-Vehicles-and-Charging-Stations

NYSERDA provides an EV registration map, regularly updated EV registration data, EValuateNY Excel/Power BI versions, and downloadable relational data archives.

EValuateNY documentation has historically included files such as:

- `ny_ev_registrations.csv`;
- `NY Original Registrations.csv`;
- `Vehicle_Share.csv`;
- Census demographic inputs;
- decoded VIN-prefix data;
- supporting resources.

Tasks:

- download a sample or full database if manageable;
- document table structure/keys;
- isolate Tompkins County/local ZIPs;
- compare totals against raw DMV;
- understand treatment of renewals, historical snapshots, and original registrations;
- assess whether EValuateNY's vehicle-share denominator is preferable to recreating one;
- determine what demographic data are bundled versus obtaining newer ACS inputs independently.

Treat DMV and EValuateNY as potentially overlapping sources and explicitly reconcile discrepancies.

### 5.3 NYSERDA Drive Clean rebate and survey data

Landing page:  
https://www.nyserda.ny.gov/All-Programs/Drive-Clean-Rebate-For-Electric-Cars-Program/Rebate-Data

Investigate at minimum:

- Drive Clean adoption surveys;
- ownership surveys;
- consumer characteristics/equity reports;
- rebated vehicle characteristics;
- historical rebate statistics/data.

A particularly relevant source is the **2024 Drive Clean Rebate Ownership Survey**:

https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Programs/Drive-Clean-NY/Drive-Clean-Rebate-Ownership-Survey-2024-Results.pdf

It includes observed respondent information on annual driving, vehicle use, home charging frequency, public charging, workplace charging access/use, and related ownership behavior.

Also inspect 2025 adoption results and newer ownership results if available.

Important caveat: Drive Clean respondents are **rebate participants**, not a random sample of all New York households or EV owners. Examine weighting, response rate, eligibility, sampling frame, and selection bias before turning survey results into population probabilities.

### 5.4 Tompkins-specific NYSERDA report

**NYSERDA Report 24-06**  
*Facilitating Electric Vehicle Adoption among Used Car Buyers and Low- to Middle-Income Community Members in Tompkins County*

PDF:  
https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/Research/Transportation/2406Facilitating-EV-Adoption-Among-Used-Car-Buyers-and-LMI-Community-Members-in-Tompkins-Countyacc.pdf

Read for:

- Tompkins-specific adoption barriers;
- population segmentation;
- local EV market observations;
- charging access considerations;
- cited local datasets/surveys;
- methodological leads and references.

Separate qualitative/contextual evidence from statistically representative measurements.

### 5.5 ACS / Census demographic and housing data

Use recent ACS 5-year data appropriate for small-area Tompkins analysis.

Potential variables include:

- household income;
- tenure;
- units in structure/housing type;
- vehicles available;
- household size;
- age;
- employment;
- commute mode/duration/departure time;
- population density;
- renter/owner × vehicle availability combinations;
- other variables suggested by EV adoption literature.

Prioritize block-group/tract data where methodologically defensible.

Tasks:

- determine which ACS variables align with attributes available in the local building/parcel model;
- test relationships between ZIP-level EV penetration and aggregated ACS characteristics across a wider New York comparison sample if useful;
- quantify uncertainty/margins of error where relevant;
- avoid ecological inference without stating it.

A likely use is:

```text
observed EV totals at ZIP level
        +
small-area household/housing composition
        +
building stock
        ->
probabilistic spatial allocation within ZIP
```

### 5.6 NHTS 2022

National Household Travel Survey downloads:  
https://nhts.ornl.gov/downloads

The 2022 NHTS V2.1 data are publicly downloadable.

Potentially useful variables include household vehicle ownership, household/person characteristics, daily vehicle miles, vehicle trips, trip purpose, departure/arrival timing, commuting, vehicle characteristics, and trip chains.

Use NHTS primarily as **travel-behavior evidence**, not observed Ithaca charging data.

Explore whether New York/regional subsamples have adequate sample sizes. If not, use broader Northeast/urban/rural classes rather than overinterpreting sparse local samples.

### 5.7 NYSERDA charging-session study

**NYSERDA Report 22-03**  
*Cost and Usage Trends for Electric Vehicle Chargers: Evidence from NYSERDA-Funded Level 2 Charging Stations in New York State*

PDF:  
https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/Research/Transportation/22-03-Cost-and-Usage-Trends-for-Electric-Vehicle-Chargers.pdf

Investigate:

- exact sample size/time coverage;
- charging-network sources;
- station/port counts;
- land-use/site categories;
- session start/end patterns;
- energy/session;
- duration;
- utilization;
- weekday/weekend effects;
- multifamily/workplace/public/retail differences;
- whether raw/session-level data are publicly downloadable or only summarized in the report.

Treat this as a strong New-York-specific charging-behavior reference, while verifying what is actually available publicly.

### 5.8 Alternative Fuels Data Center — charging infrastructure

AFDC data download:  
https://afdc.energy.gov/data_download/new

AFDC supports current and historical station downloads; historical station records extend back to 2014.

Use it to characterize:

- station locations;
- public/private access;
- charging-port counts;
- Level 1 / Level 2 / DC fast infrastructure;
- network/operator;
- station history/opening information where available;
- geographic relationship to local buildings/land uses.

AFDC is primarily **infrastructure evidence**, not observed charging behavior.

For Tompkins/Ithaca, map current chargers, investigate historical growth, classify surrounding land use/building type where practical, and assess likely residential/workplace/public charging geography.

### 5.9 NREL / OpenEI hourly EV charging models

Investigate public NREL/OpenEI datasets such as TEMPO/dsgrid-type products that provide **county-level hourly EV charging/load projections**, including Tompkins County if available.

Potential uses:

- aggregate hourly benchmark;
- annual EV charging energy comparison;
- peak timing;
- weekday/seasonal shape;
- future scenarios.

Important: these are **model outputs**, not empirical validation. Read assumptions carefully and label any comparison accordingly.

### 5.10 Additional open charging datasets

Search for and assess other raw public charging-session datasets.

Examples:

#### ACN-Data / Caltech
https://ev.caltech.edu/dataset

Potential variables: connection time, disconnect time, done-charging time, delivered energy, charging-current time series, and some user-requested departure/energy information. Useful especially for workplace/event distributions, with explicit California-to-Ithaca transferability caveats.

#### Pecan Street / Dataport
https://www.pecanstreet.org/dataport/

Potentially useful for residential circuit-level EV charging. Determine what is truly public/free versus restricted or licensed. Acquire only public data under this project constraint.

#### ElaadNL and other open charging-session datasets

Investigate where useful for session energy, arrival/departure, connection time, station type, charging power, and aggregate distribution shape. Use them as external behavioral references, not local ground truth.

---

## 6. Evidence hierarchy

Classify important sources/results by evidence type:

### A. Direct local observation
Examples: Tompkins EV registrations; Tompkins/Ithaca charging infrastructure.

### B. Direct New York observation
Examples: NYSERDA charging-session measurements; statewide EV owner surveys.

### C. Direct national/nonlocal observation
Examples: NHTS; ACN-Data; public residential charging datasets.

### D. Derived/processed observation
Examples: EValuateNY tables derived from DMV/Census.

### E. Model output / synthetic benchmark
Examples: NREL county hourly EV charging scenarios.

### F. Qualitative/contextual evidence
Examples: local planning reports, focus groups, small surveys.

Do not mix these categories in validation claims.

---

## 7. Research activities

### 7.1 Experimental/sample data fetching

Before building large pipelines:

- test accessibility;
- download small samples where APIs permit;
- inspect schemas;
- identify keys;
- verify spatial/temporal coverage;
- estimate data size;
- test reproducibility.

Preserve sample queries separately from full-acquisition logic when useful.

### 7.2 Full acquisition where justified

Fetch full public datasets when relevant and manageable.

For large sources:

- provide deterministic download scripts;
- record source URL/API query;
- record retrieval date;
- record checksums if practical;
- retain schemas/data dictionaries;
- preserve enough metadata to reproduce acquisition.

Do not rely on undocumented manual downloads.

### 7.3 Cross-source reconciliation

At minimum, test overlapping sources against each other. Examples:

- DMV EV counts vs NYSERDA/EValuateNY;
- total passenger/light-duty denominator definitions;
- ZIP/county totals;
- BEV/PHEV categorization;
- snapshot dates;
- Drive Clean rebate counts versus total EV registrations;
- AFDC station counts versus other public NY station sources if available;
- NHTS mileage versus NYSERDA owner-survey mileage;
- survey-reported charging versus observed charging-session datasets.

For discrepancies, investigate definition, time, geography, sample frame, missingness, data cleaning, registration renewals, vehicle classification, station-vs-port counting, public-vs-private access, and other methodological causes.

Do not silently choose one source.

---

## 8. Exploratory analyses to consider

These are directions, not rigid requirements.

### EV stock/adoption

- EV count and light-duty market share by local ZIP;
- BEV vs PHEV share;
- make/model/model-year composition;
- growth by year/month where supported;
- spatial concentration;
- EVs per household / registered vehicle / capita.

### Population/housing correlates

Candidate variables include income, tenure, single-family/multifamily prevalence, household vehicle availability, household size, population density, commute characteristics, age, education, employment, housing value, and local building attributes.

Possible methods:

- descriptive stratification;
- maps;
- correlations/partial correlations;
- linear, Poisson, or negative-binomial models;
- logistic-style formulations where a proper response/denominator exists;
- hierarchical/spatial regression;
- regularized regression;
- tree-based exploratory models;
- demographic standardization.

The goal is not maximum predictive complexity. Prefer interpretable analysis that determines what information is useful for **downscaling observed EV counts**.

### Charging behavior

Where data permit, analyze:

- charging start-hour distribution;
- end/departure/connection duration;
- delivered kWh/session;
- average/peak charging power;
- probability of charging on a day;
- weekday/weekend;
- season/month;
- home/work/public/MUD/retail distinctions;
- BEV/PHEV distinctions;
- charger-level distinctions;
- correlations among arrival, duration, energy, and power;
- multimodality / latent charging classes;
- coincidence/diversity as EVs are aggregated.

Assess whether simple distributions, mixtures, conditional distributions, or archetypes are empirically justified.

### Location patterns

Possible spatial analyses:

- charger density;
- distance to employment centers;
- Ithaca/Cornell-related concentration;
- residential versus workplace/public charger geography;
- relationship between EV adoption and housing/urban form.

---

## 9. Modeling questions this research should inform

Do not prematurely select one model. Determine which families are supportable.

### A. Fixed/profile-library baseline

```text
EV count × normalized hourly profile
```

### B. Stochastic charging-event model

For each EV/vehicle-day, infer/sample daily driving energy, charging occurrence, plug-in/start time, required kWh, charging power, and home/work/public location; aggregate events to hourly energy.

### C. Ownership/spatial allocation + charging events

```text
observed EV stock
-> allocation to households/buildings
-> charging behavior
-> hourly load
```

This is currently a particularly plausible direction.

### D. Archetype / mixture model

Represent populations by classes such as home L1, home L2, short/long commute, workplace-access, multifamily/public-dependent, PHEV, and different BEV classes.

### E. Minimal SOC/trip model

Carry state of charge and simple departure/arrival constraints only if evidence shows meaningful benefit or if it is important for later managed-charging/flexibility work.

The research should determine what additional complexity is actually justified by available data.

---

## 10. Validation framework to build toward

### Ownership/stock

Potential targets:

- county EV count;
- ZIP EV count;
- BEV/PHEV mix;
- make/model composition;
- historical growth;
- market share relative to total light-duty vehicles.

### Spatial allocation below ZIP

Exact parcel-level EV ownership is unlikely to be publicly observed. Possible validation includes:

- out-of-sample ZIP prediction across New York;
- holdout geographies;
- aggregate demographic consistency;
- sensitivity to downscaling assumptions;
- any independently available small-area source discovered during research.

Be explicit that reproducing known ZIP totals does not validate parcel assignment.

### Charging behavior

Possible empirical targets:

- start-time distribution;
- energy/session;
- connection duration;
- power;
- home/work/public shares;
- weekday/weekend shape;
- seasonal differences.

### Aggregate hourly load

Possible checks:

- observed public charging usage if available;
- New York empirical distributions;
- independent simulated benchmarks such as NREL/TEMPO.

Do not describe agreement with another model as empirical validation.

---

## 11. Repository operating rules

This task is executed in a Git-controlled repository.

### 11.1 First actions

At the beginning:

1. initialize Git if the repository is not already initialized;
2. inspect existing files and preserve useful existing work;
3. ensure this handoff document is stored under `docs/` and Git controlled;
4. create/update a clear root `README.md`;
5. create/update `AGENTS.md` with durable project/repository working rules;
6. create an appropriate `.gitignore`;
7. establish a sensible reproducible project structure before substantial acquisition.

Do not overwrite useful existing content merely to impose a template.

### 11.2 Git permissions

Allowed:

- ordinary non-destructive Git inspection;
- staging;
- commits;
- branches where useful;
- normal diff/log/status operations.

Do **not** use destructive Git actions such as force pushes, destructive resets, deleting unmerged work, or rewriting shared history unless explicitly authorized by a human.

### 11.3 Commit style

Commit at meaningful research/implementation milestones. Examples:

```text
docs(scope): record EV data research methodology
feat(acquisition): add NY DMV registration downloader
analysis(ownership): compare DMV and EValuateNY Tompkins counts
fix(acs): correct ZIP aggregation denominator
data(metadata): record AFDC snapshot provenance
```

Use a conventional prefix appropriate to the change.

### 11.4 Agent identity in Git

Do **not** identify the AI system, agent, model, vendor, or model version as commit author or co-author.

Do not add lines such as:

```text
Co-authored-by: ChatGPT ...
Co-authored-by: Codex ...
Co-authored-by: Claude ...
Generated-by: ...
```

Do not change Git identity to an agent/model identity. Use the environment/repository's existing human-configured Git identity.

### 11.5 Conversation/decision persistence

Assume collaborators on other machines will **not have access to prior user/agent conversations**.

Therefore:

- persist important decisions in repository documentation;
- record methodological decisions and unresolved issues;
- keep source/provenance records;
- update documentation as conclusions evolve;
- use Git commits as durable records of meaningful progress.

Do not leave essential project knowledge only in chat responses or notebook state.

---

## 12. Data-management rules

### Commit to ordinary Git

Prefer committing:

- code;
- reasonably sized notebooks;
- documentation;
- metadata;
- source manifests;
- schemas;
- data dictionaries when licensing permits;
- small samples;
- derived summary tables;
- compact processed datasets;
- figures;
- important machine-readable results.

### Do not commit large raw datasets by default

For large reproducible raw sources:

- keep them outside ordinary Git;
- ignore them appropriately;
- write acquisition scripts;
- preserve source URLs/API queries;
- preserve retrieval metadata/checksums where useful;
- document expected local paths.

Use Git LFS only if already configured or if there is a strong project reason. Do not make LFS an unnecessary dependency.

### Reproducibility target

A collaborator on another machine should be able to:

```text
clone repository
-> install environment
-> run documented acquisition commands
-> reproduce key processed data
-> run analyses
-> recover major findings
```

Prefer this standard over preserving every transient intermediate file.

### Data lineage

For important processed outputs, record:

- raw source(s);
- source version/snapshot/retrieval date;
- processing script/notebook;
- filters;
- geographic/time definitions;
- units;
- known limitations.

---

## 13. Python / analysis conventions

Python is the default environment. Preferred tools include:

- pandas;
- NumPy;
- GeoPandas;
- matplotlib;
- scipy/statsmodels;
- scikit-learn where useful;
- requests/httpx or source-specific clients;
- pyarrow/parquet;
- Jupyter notebooks for EDA.

Use `.py` scripts for reproducible acquisition/cleaning pipelines.

Notebooks are encouraged for EDA, but important results should not exist **only** as implicit notebook state. Export key findings to durable formats such as Markdown, CSV/Parquet, figures, documented tables, and reproducible analysis scripts.

Avoid machine-specific absolute paths. Provide environment/dependency documentation such as `pyproject.toml`, `requirements.txt`, or equivalent.

---

## 14. Suggested repository structure

Adapt rather than follow mechanically.

```text
/
├─ AGENTS.md
├─ README.md
├─ .gitignore
├─ pyproject.toml / requirements.txt
│
├─ docs/
│  ├─ 20260914_ev_data_research_handoff.md
│  ├─ data_sources.md
│  ├─ methodology.md
│  ├─ findings.md
│  └─ decisions/
│
├─ src/
│  ├─ acquisition/
│  ├─ processing/
│  ├─ analysis/
│  └─ utils/
│
├─ notebooks/
│  ├─ ownership/
│  ├─ demographics/
│  ├─ charging/
│  └─ validation/
│
├─ data/
│  ├─ raw/          # normally ignored
│  ├─ external/     # normally ignored if large/reproducible
│  ├─ interim/      # selective
│  ├─ processed/    # compact important outputs may be tracked
│  └─ samples/      # tracked where useful
│
├─ metadata/
│  ├─ sources/
│  ├─ schemas/
│  └─ manifests/
│
├─ results/
│  ├─ tables/
│  ├─ figures/
│  └─ maps/
│
└─ tests/
```

---

## 15. Autonomous-progress rule

The researcher/agent is expected to evolve the work as evidence accumulates.

Do not treat the source list, proposed analyses, or tentative modeling families in this document as fixed requirements.

When evidence suggests a better direction:

1. document the reason;
2. update the research plan;
3. execute the revised direction;
4. preserve the decision in Git-controlled documentation;
5. commit at a meaningful milestone.

When the human states that **no human intervention will be available for this task**, continue autonomously:

- resolve noncritical ambiguities with reasonable assumptions;
- document those assumptions;
- advance to subsequent stages without waiting for approval;
- revise goals dynamically when findings warrant it;
- do not stop merely to request a routine checkpoint or permission to proceed.

Stop only for a genuine blocker that cannot reasonably be resolved within the public-data/repository constraints.

---

## 16. Quality controls

Before treating a result as established:

- verify definitions and units;
- verify geographic boundaries;
- verify snapshot/retrieval dates;
- distinguish vehicles from registrations/renewals;
- distinguish stations from ports/connectors;
- distinguish BEV from PHEV;
- distinguish household counts from vehicle counts;
- examine denominator choices;
- identify sample-selection bias;
- inspect missingness;
- label results as observed, inferred, or simulated;
- cross-check against an independent source where feasible.

For statistical relationships:

- report sample size;
- avoid causal claims from correlation;
- inspect collinearity;
- consider spatial autocorrelation;
- account for exposure/denominator differences;
- avoid overfitting small local samples;
- use uncertainty intervals/sensitivity analysis where meaningful.

For maps:

- document CRS;
- avoid misleading count-only choropleths where denominators vary;
- prefer rates/market shares where appropriate.

---

## 17. Expected durable outputs

The exact outputs should evolve during the work. The repository should ultimately make it easy for another collaborator to understand:

- which public datasets were found;
- which were actually acquired;
- how to reacquire them;
- how they relate to one another;
- which fields/resolutions are useful;
- what local EV ownership patterns are observable;
- which demographic/building variables appear informative;
- what charging-behavior evidence is publicly available;
- which assumptions can be empirically validated;
- which assumptions cannot;
- how different sources agree/disagree;
- what simple-to-moderate ownership/charging models appear supportable;
- what the strongest validation strategy is;
- what remaining uncertainties matter for hourly building/site load modeling.

Likely artifacts include some combination of source/data inventory, acquisition pipeline, provenance manifests, processed Tompkins tables, exploratory notebooks/scripts, maps/figures, cross-source comparisons, modeling-feasibility notes, validation matrix, and preliminary recommendations.

This list is intentionally indicative rather than exhaustive.

---

## 18. Initial hypotheses to test, not assume

1. Current Tompkins EV **total stock and ZIP-level distribution can be observed directly** from DMV/NYSERDA rather than predicted.
2. The main ownership problem for the building model is likely **spatial allocation below observed geography**, not county-level adoption prediction.
3. Housing type, tenure, income, household vehicle availability, density, and commute/travel characteristics may explain spatial variation in EV penetration.
4. Residential, workplace, multifamily, and public charging likely require distinct temporal distributions.
5. A stochastic event formulation may capture aggregate hourly charging adequately without a full transportation-agent model.
6. Exact parcel/building-level ownership probably cannot be directly validated from current public data; validation may need ZIP/aggregate holdouts plus sensitivity testing.
7. New York charging-session evidence may constrain several behavioral distributions even if raw session data are unavailable publicly.
8. A model sufficient for present hourly load estimation may be simpler than one needed later for managed charging/flexibility.

Test these hypotheses and revise or reject them when evidence disagrees.

---

## 19. Definition of success

This phase is successful when the repository can answer, with reproducible evidence:

> **Given only public data, what do we actually know about EV ownership and charging behavior in Tompkins/Ithaca; what can we infer defensibly at building/site scale; what model complexity is justified; and how can the resulting hourly EV load model be validated?**

The conclusions must clearly distinguish measurements, assumptions, inference, and synthetic/model-based benchmarks.
