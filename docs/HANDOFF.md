# Handoff: state of the work and how to continue

Last updated: 2026-09-14. Written so that a collaborator or automated agent on another machine can continue **without
access to any prior conversation**. Read this file, then `AGENTS.md` (working rules), then the report.

## 1. What this repository is

Public-data research and modelling of EV ownership and hourly EV charging load for Tompkins County / Ithaca, NY, as an
end use for an urban building energy model (UBEM) whose basic unit is a zone-level RC model. The model delivers hourly
kWh for synthetic dwelling units, parcels (building proxies), block groups, the county and non-residential charging
sites, for 2026 and every year to 2050, under 4 ownership × 3 charging scenarios with Monte Carlo uncertainty.

Project lead requirements that shaped the design (recorded here because they are not derivable from code):

| Topic | Requirement |
|---|---|
| Spatial unit | dwelling unit, building/site or parcel; flexibility required (chosen: dwelling unit on parcel; parcel = building proxy) |
| Time | 2026 status quo (earlier data acceptable as baseline) plus short, medium and long-term projections to 2050; annual growth-related parameters |
| Weather | not needed for ownership or behaviour; used for energy per mile (TMYx) |
| Outputs | expected profiles and uncertainty from randomized simulation |
| Charging scope | all grid-billed charging: residential meters, workplace, public, fleet depots, campus, passers-by |
| Scenarios | time-varying functions with best/worst/event-dependent cases |
| Data | public data only (no accounts, no credentials) |
| Audience | utility operator/retailer, UBEM validation team, municipal planners, UBEM research supervisors, researchers and students |
| Excluded for now | NREL ResStock EV upgrades (explicitly excluded by the project lead) |

## 2. Where to read

| Need | File |
|---|---|
| Model report (methods, equations, validation, results) | `docs/report_20260914_ev_model.md` (HTML render alongside; `python -m src.report.render`) |
| Findings with evidence labels | `docs/findings.md` |
| Data sources and availability | `docs/data_sources.md`, `docs/source_notes/` |
| Pipeline commands | `docs/methodology.md` §1 |
| Validation status | `docs/validation_matrix.md` |
| Decisions (append-only) | `docs/decisions/0001`–`0006` |
| UBEM file interface | `docs/ubem_interface.md` |
| Presentation deck generator and style brief | `docs/deck.md`, `docs/style/pptx_deck_style_prompt.md` |

## 3. Status by work package

| Package | Status | Evidence of completion / how to resume |
|---|---|---|
| Data research phase (acquisition, reconciliation, EDA) | done | `docs/findings.md`; commits up to `cf020c4` |
| Public data gaps: Statewide Multifamily Building Study, Drive Clean parameters, AFDC history | done for 2014–2020; AFDC 2021–2025 **incomplete** | `python -m src.acquisition.afdc_historical` is resumable; the NLR v0 historical-date endpoint allows ~10 requests/hour with `DEMO_KEY` and was rate-limiting on 2026-09-14. Then `python -m src.analysis.infrastructure_history`, update report §5.6 table and deck slide on port history (automatic from tables). |
| Ownership model (synthetic dwellings, propensity, allocation ensemble, growth, placement evolution) | done | report §4; `src/model/{growth,ownership_propensity,ownership_allocation}.py` |
| Charging model (parameters, event library, load assembly, UBEM export) | done | report §5–§6; `src/model/{charging_params,charging_library,load_assembly,export_ubem}.py` |
| Report + HTML | done | `docs/report_20260914_ev_model.{md,html}` |
| In-commuter charging gap (LEHD LODES 2023) | done, **not applied** to load tables | `src/analysis/incommuter_charging.py`, `docs/source_notes/lehd_lodes_incommuting.md`, `results/tables/incommuter_*.csv`. Net correction small and negative (central −146 MWh/yr in 2026). Proposed integration in §5 below. |
| Variance decomposition of load uncertainty (stock / placement / behaviour × scale) | **in progress** on 2026-09-14 | `src/analysis/uncertainty_decomposition.py` (docstring has design). If `results/tables/uncertainty_decomposition_*.csv` are missing, run `python -m src.analysis.uncertainty_decomposition --workers 8` (long; scratch in `data/interim/uncertainty/`), repeat with `--seed 7` for a stability check, then `--figure-only`. Add report subsection "6.3 Where the uncertainty comes from". |
| Presentation deck (`.pptx`, not version-controlled) | generator done | `docs/deck.md`. Rebuild after any table change. Uncertainty slide appears automatically when its tables exist (review its layout when first produced). |

## 4. Open questions for the project lead (asked 2026-09-14, unanswered)

1. How will the UBEM use EV load: building meter totals, zone internal gains (e.g. garages), or grid-side aggregation only?
2. Is the 9–31 % multifamily placement range acceptable if delivered as many realizations, or should non-public data
   (utility EV rate enrolment, Cornell parking/charging, municipal permits, DMV address-level data under agreement) be pursued?
3. Should long-range scenarios be tied to named policies (NY Advanced Clean Cars II / zero-emission vehicle sales rule and
   its contested federal status, NY climate plan) instead of fitted trends?

Do not assume answers; the backlog below is ordered so that items 1–4 do not depend on them.

## 5. Backlog (ordered)

1. **Finish the uncertainty decomposition** (see §3) and write report §6.3; update `docs/findings.md` and the deck.
2. **AFDC 2021–2025 snapshots** (see §3); then site-specific **DC fast growth scenarios**: new DC fast sites instead of
   scaling existing stations (the current rule gives a > 9 MW single site by 2050 in the trend scenario; report §6.2).
3. **Commuter adjustment** (optional, small): add to `src/model/load_assembly.py` a function
   `commuter_adjustment(lib, year, own, chg, pools, n_inc_ev_2026=181, bev_share_inc_2026=0.50, omega_out=0.218,
   public_in_tompkins=0.30, kwh_factor=1.0)` that adds in-commuter workplace/public energy scaled by the ownership
   scenario's EV growth and removes the out-commuting share of resident workplace (and, with the symmetry assumption,
   public) pools; site workplace energy by `results/tables/incommuter_workplace_by_bg.csv`. Register the parameters in
   `src/model/charging_params.py` with sources. Record as a decision if applied.
4. **Sensitivity runs** for home L2 power (9.6–11.5 kW) and managed-charging stagger width; temperature-dependent annual
   energy for specific weather years (AMY instead of TMYx).
5. **UBEM coupling test** (depends on question 1): join parcels to building footprints / RC zones and validate the
   `docs/ubem_interface.md` files end to end with the UBEM team.
6. **Policy-tied scenarios** (depends on question 3).

## 6. Environment and reproduction notes

- Python ≥ 3.11 (developed on 3.13, Windows): `python -m venv .venv`, install `requirements.txt`. Run modules from the
  repo root (`python -m src.<pkg>.<module>`).
- Raw data are git-ignored and large (EValuateNY ~840 MB, DMV snapshot stream ~2.5 GB, LODES NY ~200 MB). Tracked
  `data/processed/` and `results/` are enough to rebuild the report figures, the deck and most analyses without raw data;
  the event library in `data/interim/charging_library/` must be regenerated (`python -m src.model.charging_library`)
  before `load_assembly` or the uncertainty decomposition.
- Report HTML needs pandoc ≥ 3 (`-f markdown+tex_math_single_backslash --mathml --embed-resources`).
- Deck needs Node.js ≥ 18 (`cd src/deck && npm ci`), LaTeX (`pdflatex`, `pdftocairo`) for equations; PowerPoint (Windows)
  or LibreOffice for visual QA.
- Service quirks: Census API now requires a key, so ACS summary files are used (decision 0001); `developer.nrel.gov`
  moved to `developer.nlr.gov`; DMV `fuel_type` codes PHEVs as GAS, so VIN decoding is required (decision 0002).

## 7. Rules that must be kept (summary of `AGENTS.md`)

- Public data only; never create accounts or enter credentials.
- Commits use the repository's configured human Git identity; **no AI/agent/model author, co-author or generated-by
  trailers**. No force pushes, destructive resets or history rewrites.
- Raw/external/interim data stay git-ignored and re-creatable by scripts with provenance manifests; no Git LFS without a
  decision record; no machine-specific absolute paths in code.
- Evidence labels A–F on numbers; agreement with class E (model outputs such as NREL TEMPO) is a benchmark, never validation.
- Decks follow `docs/style/pptx_deck_style_prompt.md`; built `.pptx` files are not committed.
