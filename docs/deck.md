# Presentation deck: how it is built

Last updated: 2026-09-14.

The project slide deck is **generated**, not hand-edited, so any contributor (human or agent, local or remote) can
rebuild it from the repository. Built `.pptx` files and intermediate assets are **not Git-controlled**
(`results/deck/` and `*.pptx` are in `.gitignore`); the generator, its data extraction and the design brief are.

| Item | Location | Git |
|---|---|---|
| Design brief (mandatory style rules) | `docs/style/pptx_deck_style_prompt.md` | tracked |
| Data/asset extraction (charts series, maps, LaTeX equations) | `src/deck/deck_data.py` | tracked |
| Slide builder (pptxgenjs; native editable charts and tables) | `src/deck/build_deck.js`, `src/deck/package.json`, `src/deck/package-lock.json` | tracked |
| Slide rendering for visual QA (Windows + PowerPoint) | `src/deck/export_slides.ps1` | tracked |
| Built assets | `results/deck/build/` (`deck_data.json`, `maps/`, `eq/`) | ignored |
| Deck | `results/deck/ev4ubem_model_deck.pptx` | ignored |

## Content rules

- The deck reports what `docs/report_20260914_ev_model.md`, `docs/findings.md` and `results/tables/` say. Numbers
  on slides are either read from `results/tables/*.csv` / `data/processed/` by `deck_data.py` or transcribed from the
  report tables in `build_deck.js` (search for `// source:` comments). If the report changes, update both.
- Evidence classes (A–F, "inferred") stay attached to numbers, as in the report. Agreement with class E is a benchmark.
- Titles state the supported conclusion or the subject; no generic titles.

## Build

Prerequisites: the Python environment from `requirements.txt` (plus `lxml`, `defusedxml`, `markitdown[pptx]` only for
QA), Node.js ≥ 18, a LaTeX distribution with `pdflatex` and `pdftocairo` (TeX Live includes both) for equations, and
the model outputs (run the pipeline in `docs/methodology.md` first if `data/processed/load/` is missing).
Census place boundaries (`data/raw/census/tiger/tl_2024_36_place.zip`, from `src.acquisition.census`) are used for the
City of Ithaca outline on maps; maps render without it.

```bash
.venv/Scripts/python.exe -m src.deck.deck_data
cd src/deck && npm ci && node build_deck.js
```

Optional follow-on results are picked up automatically when their tables exist:
`results/tables/uncertainty_decomposition_*.csv` and `results/tables/incommuter_charging_estimate.csv`.

## Visual QA

On Windows with PowerPoint installed, `powershell -File src/deck/export_slides.ps1` exports every slide to
`results/deck/png/`. Inspect every slide for overflow, overlaps, legibility (labels ≥ 11–12 pt at slide size) and
consistency with the style brief. Elsewhere, LibreOffice (`soffice --headless --convert-to pdf`) plus `pdftoppm` gives
an approximate render (Calibri is substituted by Carlito). Structural validation of the package can be done with any
OOXML validator; the build used the validator shipped with the `pptx` agent skill.

## Design decisions (implementation of the brief)

- 13.33 × 7.5 in (16:9), white background, Calibri; deck title 40 pt, slide titles 28 pt, body 18–20 pt, chart
  labels and citations 12–14 pt. No slide numbers, footers or logos.
- One principal accent (dark teal `1A5E63`) marks model output; observations are near-black `222222`; alternatives and
  context are greys. Charging locations use Okabe–Ito colours throughout: home `0072B2`, workplace `009E73`,
  public L2 `56B4E9`, DC fast `D55E00`, fleet `CC79A7`, passers-by `E69F00`.
- Charts are native PowerPoint charts (editable data) except maps and equations. Maps are rendered by `deck_data.py`
  with common extents and colour scales for comparable panels, hatching for "no households" (missing ≠ zero), a
  scale bar and a City of Ithaca zoom panel.
- Equations are LaTeX-rendered transparent PNGs (400 dpi) with symbol definitions as editable text beside them.
  Their LaTeX source is in `EQUATIONS` in `deck_data.py`.
- Tables are native, lightly ruled (header rule and bottom rule), right-aligned numbers, units in headers.
