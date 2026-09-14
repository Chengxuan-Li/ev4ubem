# Presentation deck style prompt (`.pptx`)

Status: adopted 2026-09-14 for all project slide decks. Supplied by the project lead; this text is the
reference design brief. Any human or automated contributor producing a `.pptx` from this repository must follow it.
The deck generator implementing it is `src/deck/` (see `docs/deck.md`); built decks are **not** Git-controlled.

Scope note: the prompt governs *design only*. Research claims, values, units, equations and sources come from
`docs/report_20260914_ev_model.md`, `docs/findings.md` and `results/tables/`, and must not be altered by deck design.

---

Design and produce an editable `.pptx` for a technical research presentation containing models, data analysis, maps,
charts, tables, figures, and limited mathematical notation. Handle design only. Do not change research claims, values,
units, equations, or sources.

Use a restrained academic style centered on evidence and analytical clarity. Apply consistent typography, margins,
alignment, colors, captions, and figure treatment. Prefer one strong composition per slide with generous whitespace.
Use a small set of layouts: full-width figure, figure with explanatory text, two-figure comparison, modeling workflow,
equation with definitions, editable table, and results synthesis.

Avoid recognizable AI-generated presentation aesthetics:

* Floating rounded boxes, color washes, decorative highlight strips
* Card grids, KPI tiles, pills, badges, tabs, or dashboard layouts
* Decorative gradients, glass effects, blobs, synthetic 3D objects, and abstract technology imagery
* Icons, callouts, or infographics that add no analytical meaning
* Repetitive headers, footers, section labels, or institutional branding on every slide
* Generic titles such as "Key Insights," "Unlocking Potential," or "The Road Ahead"

Use direct subject titles or conclusions supported by the slide. Keep the title slide minimal. Use a professional
sans-serif typeface, approximately 36–44 pt for the deck title, 27–32 pt for slide titles, 18–22 pt for body text, and
at least 11–14 pt for figure labels and citations.

Use a neutral background, one principal accent, and only the additional data colors needed. Keep variable and category
colors consistent across the deck. Use colorblind-conscious sequential, diverging, or categorical scales according to
the data.

Keep charts editable when practical. Preserve axes, units, uncertainty, sample sizes, baselines, and statistical
meaning. Remove heavy borders, shadows, redundant legends, and unnecessary gridlines. Favor one readable plot over
several undersized plots.

Treat maps as analytical figures. Maximize useful geographic area, use quiet basemaps, distinguish missing data from
zero, and include only necessary legends, scales, insets, or labels. Align extents and color scales across comparable
maps.

Make modeling diagrams accurate and economical. Clearly distinguish observed inputs, parameters, states, calculations,
and outputs. Use meaningful directional connectors and avoid decorative complexity.

Format equations with proper mathematical notation. Align related expressions, define symbols nearby, and separate
mathematical definitions from their interpretation. Do not place equations in decorative boxes.

Keep tables editable, lightly ruled, and numerically aligned. Put units in headers, use consistent precision, and
highlight only analytically important values. Do not convert tables into card grids.

Prefer authentic technical material such as maps, simulation outputs, geometry, schematics, field photographs, and
experimental setups. Do not add generic or AI-generated imagery merely to fill space.

Keep citations attached to the relevant evidence. Use concise on-slide citations and consistent captions without
creating a large repetitive footer.

Use no animation by default. Deliver a clean, fully editable `.pptx` with legible figures, preserved image resolution,
no overlaps or overflow, and no unnecessary template artifacts. The result should feel composed by a technically
literate human researcher: precise, coherent, and centered on the evidence.
