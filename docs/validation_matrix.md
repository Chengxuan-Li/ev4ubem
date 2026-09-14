# Validation matrix

Last updated: 2026-09-14. What each model component can be checked against, with evidence class
(A local obs · B NY obs · C nonlocal obs · D derived · E model output · F qualitative).
"Agreement with E" is benchmarking, never validation.

| Model component | Target quantity | Best available check | Class | Status / result | What remains unvalidated |
|---|---|---|---|---|---|
| County EV stock | BEV, PHEV count, 2026 | DMV snapshot, VIN-decoded; cross-check ZIP-share vs county-field definitions | A | 3,233 vs 3,123 (−3.5 %) | VIN decoding of MY2027 edge cases (3 UNKNOWN LDVs) |
| ZIP EV stock | BEV, PHEV by ZIP | DMV snapshot (direct observation) | A | observed, used as constraint | — (observed) |
| Stock history | EVs 2011–2026 | EValuateNY monthly snapshots (2011–2023) + DMV 2026 | D + A | consistent methods; ~20 %/yr growth 2023→2026 | 2023-04→2026-09 gap months (transactions dataset only covers 2024-08+) |
| BEV/PHEV mix, models | shares | DMV + vPIC | A/D | PHEV 44 % of LDV EVs | — |
| Area-level adoption predictors | ZIP EV/household | NY ZIP cross-section, county-grouped CV, Tompkins holdout | B (ecological) | NB GLM: 72 % (2023) and 67 % (2026) of Poisson deviance explained out-of-county; rural Tompkins ZIPs under-predicted ~2× in both years | Individual-level effects; transfer to sub-ZIP units |
| Sub-ZIP / parcel placement | EVs per BG / building | **No public observation** | — | S0–S3 scenario spread reported (multi-unit share 38 %→8 %) | All parcel-level placement; only aggregate consistency (ACS households) can be checked |
| Household propensity by class | relative EV ownership | NHTS 2022 (national), Drive Clean survey demographics (NY rebate recipients) | C / B (biased) | apartments ≈ 0.2× average; income dominant | Upstate NY applicability; students; renters in SFD |
| Annual kWh per EV | kWh/yr | Drive Clean miles (self-report) × efficiency; NHTS diary/self-report; Norway home (2.5 MWh/yr/user) | B / C | 2,900 kWh/EV base (2,100–3,800) | No NY metered per-vehicle data public (OptimizEV nonpublic) |
| Location split | home/work/public energy | Drive Clean frequencies (B); NYSERDA 22-03 port utilisation (B); AFDC ports (A) | B/A | assumption 80/7/8/5 | Energy shares not observed anywhere public for NY |
| Home charging timing | plug-in hour, duration | Norway sessions (C); TEMPO shape (E); NHTS last-arrival-home (C) | C | evening peak 16–22 h consistent across C sources | NY/Ithaca home timing; TOU/managed charging participation |
| Workplace / public timing | start hour, energy, duration | NYSERDA 22-03 occupancy shapes & summary stats (B); Boulder/Palo Alto/workplace sessions (C) | B/C | workplace AM peak 9–10 h (B) matches C | Ithaca-specific utilisation; Cornell campus |
| Public utilisation magnitude | kWh/port-day | NYSERDA 22-03 (B, 2012–2020); EValuateNY ChargePoint ZIP-month (B/A, to 2022) | B/A | available for 14850 (ChargePoint only) | Post-2022 local utilisation; non-ChargePoint networks |
| Seasonality | monthly index | Boulder L2, Norway (C); NYSERDA 22-03 (B, qualitative) | C/B | winter energy index > summer | Upstate cold-weather efficiency penalty magnitude |
| Aggregation / diversity | peak kW per EV vs N | Norway residential (C) | C | 4.7 kW (N=1) → 1.2 kW (N≈60) at 3.6 kW | Depends on imputed charging power; L1-heavy PHEV fleets |
| County hourly load | 8,760 h kWh | TEMPO 2022 (E); no observed county EV load | E | TEMPO energy ≈ 2.5× bottom-up per observed EV | Everything at hourly magnitude is unvalidated empirically |
