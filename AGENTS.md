# AGENTS.md — durable working rules for this repository

These rules apply to any human or automated contributor. Collaborators do **not** have
access to prior chat conversations: anything important must live in this repository.

## Project purpose
Public-data research on EV ownership and charging load for Tompkins County / Ithaca, NY,
feeding an urban building energy model that needs `site/building × hour -> EV kWh`.
The original brief is `docs/20260914_ev_data_research_handoff.md` (treat as a brief, not a checklist).

## Where knowledge lives
| What | Where |
|---|---|
| Source inventory + availability classification | `docs/data_sources.md` |
| Per-source reading notes (reports, surveys) | `docs/source_notes/` |
| Methods, definitions, filters | `docs/methodology.md` |
| Current findings (observed / inferred / simulated labelled) | `docs/findings.md` |
| Decisions and changes of direction | `docs/decisions/NNNN-*.md` (append-only, numbered) |
| Acquisition provenance (URL, query, date, sha256, size) | `metadata/manifests/*.json` (written by scripts) |
| Schemas / data dictionaries | `metadata/schemas/` |

When a conclusion changes, update `docs/findings.md` and add a decision record; do not silently rewrite history.

## Data management
- Raw/external/interim data (`data/raw`, `data/external`, `data/interim`) are git-ignored and must be
  re-creatable by scripts in `src/acquisition/`. Never rely on undocumented manual downloads.
- Every acquisition script records a manifest entry via `src/utils/provenance.py`.
- Commit compact processed outputs (`data/processed/`, typically < ~5 MB each), small samples
  (`data/samples/`), tables (`results/tables/`), figures (`results/figures/`, `results/maps/`).
- Do not use Git LFS unless a strong reason is documented in a decision record.
- No machine-specific absolute paths in code; resolve paths via `src/utils/paths.py`.

## Evidence labelling (use in docs, tables, figure captions)
A local observation · B New York observation · C national/nonlocal observation ·
D derived/processed observation · E model output / synthetic benchmark · F qualitative/contextual.
Never describe agreement with class E as empirical validation.

## Quality rules
Distinguish vehicles vs registrations, stations vs ports, BEV vs PHEV, households vs vehicles;
state denominators, snapshot dates, CRS; report sample sizes; no causal claims from correlation;
state ecological-inference limits when using area-level regressions.

## Git
- Conventional commit prefixes: `docs(...)`, `feat(acquisition)`, `analysis(...)`, `fix(...)`, `data(metadata)`, `chore`.
- Commit at meaningful milestones. No force pushes, destructive resets, or history rewrites.
- Commits use the repository's configured human Git identity. Do **not** add AI/agent/model
  authorship, co-author, or "generated-by" trailers.

## Environment
Python ≥ 3.11. `python -m venv .venv` then `pip install -r requirements.txt`.
Run scripts from the repo root as modules, e.g. `python -m src.acquisition.dmv_registrations`.
