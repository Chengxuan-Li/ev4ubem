# ev4ubem — EV ownership & charging data research for Tompkins County / Ithaca, NY

Public-data research to support an **hourly EV charging load** end use
(`site/building × hour -> kWh`) in an urban building energy model (EnergyAtlas/RC).
This phase covers data acquisition, cross-source reconciliation, exploratory analysis,
and model-feasibility/validation design. See the original brief:
[`docs/20260914_ev_data_research_handoff.md`](docs/20260914_ev_data_research_handoff.md).

**Start here:** [`docs/findings.md`](docs/findings.md) (what we know, labelled by evidence class) ·
[`docs/data_sources.md`](docs/data_sources.md) (source inventory and availability) ·
[`docs/methodology.md`](docs/methodology.md) · [`docs/validation_matrix.md`](docs/validation_matrix.md) ·
[`docs/decisions/`](docs/decisions/) ·
[`AGENTS.md`](AGENTS.md) (working rules).

## Key results so far (2026-09-14; details and evidence labels in `docs/findings.md`)

- **Tompkins EV stock is directly observed:** 3,233 plug-in EVs (1,833 BEV, 1,400 PHEV) in the NYS DMV snapshot of
  2026-09-02, ~5.4 % of light-duty vehicles, roughly doubled since April 2023. PHEVs are registered as `GAS`, so the
  identification relies on VIN decoding.
- **Nothing public observes EVs below ZIP code.** Plausible allocation rules place 8–38 % of EVs in multi-unit housing.
  This is the dominant uncertainty for building-level loads.
- **No public New York session-level charging data.** NY summary evidence (NYSERDA 22-03, Drive Clean surveys) plus open
  non-NY session datasets give charging shapes; public-L2 and residential shapes agree with NY utilisation curves (r ≈ 0.9+).
- **Bottom-up 2026 county EV energy ≈ 9.4 GWh/yr (6.9–12.3)** with a ~2.1 MW hourly peak; NREL TEMPO (model) is ~2.5× higher.
- **Building peaks need event-based profiles:** per-EV peak falls from ~7 kW (one EV) to ~1.5 kW (48 EVs).

## Reproduce

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Windows; use .venv/bin/pip on Linux/macOS
```

Acquisition (writes git-ignored files under `data/raw/` and provenance to `metadata/manifests/`):

```bash
python -m src.acquisition.run_all          # or run individual modules listed below
```

Processing and analysis (write tracked compact outputs to `data/processed/`, `results/`):

```bash
python -m src.processing.run_all
python -m src.analysis.run_all
```

Individual pipeline steps are listed in [`docs/methodology.md`](docs/methodology.md).

## Layout

```text
docs/          brief, source inventory, source notes, methodology, findings, decision records
src/           acquisition/ processing/ analysis/ utils/  (run as python -m src.<pkg>.<module>)
notebooks/     exploratory notebooks (key results are exported to results/ and docs/)
data/raw       git-ignored raw downloads (re-creatable)      data/processed  tracked compact outputs
data/samples   small tracked samples                          metadata/       manifests, schemas
results/       tables/ figures/ maps/
tests/         lightweight checks of processing invariants
```
