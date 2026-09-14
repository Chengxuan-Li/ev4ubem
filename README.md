# ev4ubem — EV ownership & charging data research for Tompkins County / Ithaca, NY

Public-data research to support an **hourly EV charging load** end use
(`site/building × hour -> kWh`) in an urban building energy model (EnergyAtlas/RC).
This phase covers data acquisition, cross-source reconciliation, exploratory analysis,
and model-feasibility/validation design. See the original brief:
[`docs/20260914_ev_data_research_handoff.md`](docs/20260914_ev_data_research_handoff.md).

**Start here:** [`docs/findings.md`](docs/findings.md) (what we know, labelled by evidence class) ·
[`docs/data_sources.md`](docs/data_sources.md) (source inventory and availability) ·
[`docs/methodology.md`](docs/methodology.md) · [`docs/decisions/`](docs/decisions/) ·
[`AGENTS.md`](AGENTS.md) (working rules).

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
