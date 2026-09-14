# 0002 — EV identification in DMV registrations requires VIN decoding (2026-09-14)

**Status:** accepted (evidence below; statewide quantification in progress)

## Context
The brief asked whether DMV `fuel_type` filtering or VIN-prefix decoding should identify BEVs/PHEVs.

## Evidence (DMV snapshot `w4pv-hbkt`, source rows updated 2026-09-02; Tompkins residents, record_type VEH)
Cross-tabulating DMV `fuel_type` against EValuateNY's VIN-key drivetrain lookup
(key = VIN chars 1–8 + char 10; matches 99.4 % of EValuateNY EV VIN prefixes):

| DMV fuel_type | BEV (lookup) | PHEV (lookup) | ICE (lookup) | no lookup match |
|---|---:|---:|---:|---:|
| ELECTRIC (1,853) | 1,056 | 4 | 19 | 774 (MY2023–2027, beyond lookup coverage) |
| GAS (59,056) | 2 | **988** | 47,111 | 10,613 |

PHEVs (Toyota Prius Prime / RAV4 Prime, Chevrolet Volt, Chrysler Pacifica Hybrid, …) are
registered with `fuel_type = GAS`. `ELECTRIC` is effectively BEV-only.

## Decision
- EV stock = BEV + PHEV identified by VIN pattern decoding (EValuateNY lookup, then NHTSA vPIC for
  unmatched patterns). DMV `ELECTRIC` is used only as a BEV cross-check.
- Every EV table states its identification method. Counting PHEVs as `GAS` would understate Tompkins
  EV stock by roughly half.
- The 19 `ELECTRIC` rows matching ICE patterns and 2 `GAS` rows matching BEV patterns are retained as
  classification-conflict diagnostics (resolved by vPIC where possible).
