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

## Modelling phase additions (2026-09-14; details in `docs/report_20260914_ev_model.md` §4–§7)

| Model component | Check | Class | Result | Remains unvalidated |
|---|---|---|---|---|
| Synthetic dwelling units | ACS BG marginals (tenure×structure, tenure×vehicles, income) | A | R² 0.994–0.999 | joint distributions within BG |
| Household propensity (ecological) | 10-fold county-grouped CV on 1,361 NY ZIPs; cross-year allocation 2023→2026 | B | vehicles+area models ≈ 0.78–0.80 deviance explained; priors weight ω ≈ 0 | within-ZIP composition effects |
| Dwelling-unit allocation | ZIP totals reproduced (by construction); structural ensemble spread | — | MF share 21 % (9–31 %) | building placement |
| Growth model | backcast fit ≤2021 | A/D | NY +3 % (2023), +27 % (2026); Tompkins +21 % / +90 % | post-2026 adoption path |
| Charging frequency | Drive Clean 2024 categories | B | BEV TVD 0.18 (PHEV by construction) | L1 users |
| Charging shapes | NYSERDA 22-03 weekday shapes | B | r 0.97 (home vs MUD), 0.91 (public), 0.88 (workplace, source) | upstate single-family timing |
| Public L2 utilisation | ChargePoint ZIP 14850 | A/B | 9.6 vs 7.3–16.4 kWh/port-day | non-ChargePoint sites, post-2022 |
| Energy per EV | survey mileage × efficiency | B | 2,994 vs 3,165 kWh | metered per-vehicle energy |
| Seasonality / diversity | Dundee index; Norway diversity | C | r 0.82; within empirical range | NY cold-climate efficiency |
| County load magnitude | TEMPO | E | 2.2× higher (benchmark) | all hourly magnitudes |
| Uncertainty attribution (not validation) | Sobol–Hoeffding decomposition, crossed Monte Carlo (report §6.3) | inferred | 2026: behaviour 77–88 % (county), placement 43–64 % (BG), 71–75 % (1–4-unit parcel peaks); 2035: stock 82–87 % (county) | which checks can discriminate: parcel-level data test placement, county/feeder data test behaviour |
