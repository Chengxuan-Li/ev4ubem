# 0005 — Ownership allocation: ecological + individual-evidence ensemble (2026-09-14)

**Status:** accepted

## Evidence
- NY ZIP-level ecological models (`results/tables/propensity_cv.csv`): allocating EVs proportional to household vehicles
  (with area effects) explains ~0.78–0.80 of held-out Poisson deviance and gives the best or near-best within-county
  allocation skill; a tempered-prior model estimates the weight on individual-level structure/tenure/income priors at
  ω = 0.00–0.04 (± 0.06–0.07). Imposing full priors (Drive Clean representation ratios, NHTS marginals) *worsens*
  ZIP allocation below a uniform split, largely because multifamily/renter households already have fewer vehicles.
- Estimated free class effects (M3) are ecologically confounded (e.g. 2–4-unit owners 0.12×), so they are not used.
- Individual-level evidence (NHTS 2022 conditional logit): income strongly associated (OR 6.7 for ≥$150k vs <$50k),
  ≥2 vehicles OR 2.4, detached/attached OR 1.3 (n.s.), owner OR ≈1 (n.s.). Drive Clean respondents (new-EV rebate
  recipients) are 1.85× over-represented in detached homes and ~0.25× in apartments (unconditional, statewide).
- ZIP-level data cannot identify within-ZIP composition effects because composition co-varies with area effects;
  individual data cannot be validated locally.

## Decision
- Within each ZIP (observed totals), dwelling-unit EV expectations are the **mean of two capped allocations**:
  (1) S_model — selected ecological model (vehicles^η × BG area effect), and (2) S_individual — NHTS conditional odds
  ratios (income, single-family, tenure) × vehicles.
- Monte Carlo realizations pick one of the two variants per draw, so percentiles include structural uncertainty.
- S_uniform and S_prior are reported as lower/upper concentration bounds (multifamily share of personal EVs 31 % vs 9 %).
- Fleet/organizational EVs are placed on non-residential parcels by floor area (low confidence).

## Consequences
- 2026 central multifamily share of personal EVs ≈ 21 % (households 36 %); renters ≈ 28 %.
- Building-level EV placement is *inferred*, validated only between ZIPs and against ACS composition.
