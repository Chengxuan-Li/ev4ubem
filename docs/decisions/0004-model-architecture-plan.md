# 0004 — Model architecture plan for ownership, growth and charging (2026-09-14)

**Status:** accepted (plan; revised as stages complete)

## Requirements from the project lead (2026-09-14)
- Basic modelling unit as detailed as dwelling / building / parcel; flexible aggregation up to RC-zone, parcel, BG, ZIP.
- Status-quo baseline (2026, earlier data acceptable) **and** annual projections to 2050 with scenarios; a model that
  works with time and growth parameters.
- Uncertainty from randomized simulation plus expected profiles.
- All grid-billed charging: residential meters, workplace, public, fleet depots, campus, pass-through (small).
- Weather only for energy consumption (not behaviour). Public data only. Audience: utility, UBEM validation team,
  municipal planners, research lab.
- Stage order: (3) public data gaps → (1–2) ownership + allocation + growth → (4) charging energy/events.

## Architecture
1. **Synthetic dwelling units (DU).** Tax parcels → residential dwelling units (property class unit rules, calibrated to
   ACS BG occupied units by structure type). Each DU gets household attributes (tenure, income band, vehicles,
   household size, workers) sampled from ACS PUMS households of Tompkins' PUMA, reweighted to BG marginals (IPF).
2. **Household EV propensity model** π(x, t): log-linear relative propensity over DU/household attributes
   (structure type, tenure, income, vehicles), with priors from NHTS 2022 / SMBS / Drive Clean and **ecological
   calibration against NY ZIP-level EV counts** (2023 EValuateNY, 2026 DMV) using ACS ZCTA composition; county-grouped
   cross-validation against uniform / vehicle-proportional baselines.
3. **Status-quo allocation.** Observed ZIP totals by drivetrain and registration class are hard constraints;
   EVs are sampled to DUs ∝ π with ZIP-level calibration factors (Monte Carlo realizations). Fleet EVs → commercial /
   institutional parcels; campus as a site entity.
4. **Growth model (annual to 2050).** County stock-flow: LDV fleet size × new/used registration flows × EV share of
   additions s(t) (logistic diffusion fitted to 2011–2026 history, scenarios low/base/high/policy-aligned), vehicle
   survival; BEV/PHEV split trajectory; propensity *convergence* parameter (adoption spreading from early-adopter
   segments to multifamily/lower income) and home-charging-access trajectory; backcast validation (fit ≤2021,
   predict 2022–2026).
5. **Charging events (stage 4).** Per EV-day: driving energy (NHTS/Drive Clean mileage distributions × kWh/mi(T)
   from EPW), charging need and location choice given access (home L1/L2 by DU type, workplace, public L2, DCFC),
   plug-in time and dwell distributions (Norway home sessions, NYSERDA 22-03 workplace/public shapes, NHTS arrival
   times), charging power, immediate charging (managed/TOU as scenario) → hourly kWh per DU and per site.
6. **Outputs.** Expected hourly kWh per DU/parcel/BG and site; percentile bands from realizations; county scenarios
   2026–2050; parameter tables per year.

## Validation gates
- Stage 1–2: ZIP-level out-of-county predictive skill of π vs baselines; ACS consistency of synthetic DUs;
  backcast of county stock and ZIP distribution 2023→2026; explicit statement that below-ZIP placement is unvalidated.
- Stage 4: session/energy/timing distributions vs source data; NY shape agreement (22-03); public port utilisation vs
  ChargePoint 14850 kWh/port-day; county annual energy vs bottom-up range; TEMPO as benchmark only.
