# 0003 — Research direction after first acquisition and analyses (2026-09-14)

**Status:** accepted

## Evidence that changed the plan
1. **EValuateNY is stale** (last DMV snapshot 2023-04-02; `ny_ev_registrations.csv` ends 2022-03). It remains
   valuable for history (2011–2023) and for a VIN-decoded all-vehicle denominator, but the **current stock must come
   from the live DMV snapshot** with our own VIN decoding (decision 0002).
2. **Ownership is directly observable at ZIP level** (hypothesis 1 supported). Tompkins, DMV 2026-09:
   3,233 BEV+PHEV (county field) vs 3,123 (ZIP population-share method) — the two geographic definitions agree
   within 3.5 %. The modelling problem for the building model is **below-ZIP placement** (hypothesis 2 supported).
3. **DMV `county` is not always a household location.** ZIP 12449 (Lake Katrine, Ulster County) carries 731 vehicles
   coded `county = TOMPKINS`, 75 % commercial class — a fleet address. Household allocation therefore uses
   personal (`PAS`) light-duty EVs in Tompkins-area ZIPs only; commercial/organizational EVs are reported separately.
4. **Sub-ZIP allocation is dominated by unvalidated assumptions.** Plausible weighting schemes move the share of EVs
   placed in multi-unit housing from ~39 % to ~8 % (first run). No public data observe EVs below ZIP, so the model
   must carry this as explicit structural uncertainty (hypothesis 6 supported).
5. **NREL TEMPO overstates Tompkins charging energy** relative to observed stock: reference MY2026 = 24.0 GWh/yr,
   i.e. ~7,400 kWh per *observed* EV, vs ~2,900 kWh/EV from survey mileage. TEMPO is retained for *shape* and
   scenario-growth benchmarking only (class E), never for magnitude validation.
6. **No public New York session-level charging data** were found (NYSERDA 22-03 is summary-only; OptimizEV is
   nonpublic). Behavioural distributions must come from non-NY open datasets (class C), constrained by NY summaries
   (class B) — hypothesis 7 only partially supported.
7. **NHTS 2022 is too small for EV-specific behaviour** (266 plug-in vehicles, no state) but supports relative
   household propensities and generic vehicle-day timing.

## Revised plan
- Treat ZIP totals (by BEV/PHEV and registration class) as fixed observed constraints; build allocation as a
  scenario ensemble, not a single deterministic map.
- Use the NY ZIP-level cross-section (2023 now; 2026 once statewide VIN decoding completes) for out-of-sample
  validation of *area-level* predictors, explicitly not of parcel placement.
- Charging: a mixture of location-specific event distributions (home / workplace / public L2 / DCFC), with location
  energy shares as explicit assumptions and NYSERDA 22-03 occupancy shapes as NY checks.
- Separate fleet/organizational EVs from household EVs in the load model.
- Deprioritise long-range forecasting; TEMPO scenario growth may be used for extensibility only.
