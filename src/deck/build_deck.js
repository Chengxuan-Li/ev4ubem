// Build the project presentation deck (editable .pptx) with pptxgenjs.
// Design brief: docs/style/pptx_deck_style_prompt.md · build notes: docs/deck.md
// Inputs: results/deck/build/deck_data.json, maps/*.png, eq/*.png (from `python -m src.deck.deck_data`)
// Values in tables marked `// source:` are transcribed from docs/report_20260914_ev_model.md; charts read deck_data.json.
// Usage: cd src/deck && node build_deck.js [output.pptx]
'use strict';
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');

const ROOT = path.resolve(__dirname, '..', '..');
const BUILD = path.join(ROOT, 'results', 'deck', 'build');
const OUT = process.argv[2] ? path.resolve(process.argv[2]) : path.join(ROOT, 'results', 'deck', 'ev4ubem_model_deck.pptx');
const D = JSON.parse(fs.readFileSync(path.join(BUILD, 'deck_data.json'), 'utf8'));

// ------------------------------------------------------------------------------------------------ style tokens
const C = {
  text: '1F2328', muted: '5F6B73', rule: 'BFC5CA', faint: 'E3E6E8', accent: '1A5E63', accentLight: '8DB3B5', obs: '222222',
  grey: '8C8C8C', lightGrey: 'C8CCCF', stateFill: 'EEF0F1',
  home: '0072B2', work: '009E73', public_l2: '56B4E9', dcfc: 'D55E00', fleet: 'CC79A7', passerby: 'E69F00',
};
const LOCS = ['home', 'work', 'public_l2', 'dcfc', 'fleet', 'passerby'];
const LOC_LABEL = { home: 'Home', work: 'Workplace', public_l2: 'Public Level 2', dcfc: 'DC fast (residents)', fleet: 'Fleet depots', passerby: 'Passers-by (DC fast)' };
const F = 'Calibri';
const W = 13.333, ML = 0.6, CW = W - 2 * ML, TOP = 1.5;
const SZ = { deckTitle: 40, title: 28, body: 18, small: 16, label: 13, cite: 12, table: 14 };

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.author = 'Cheng Xuan Li';
pres.title = 'EV ownership and charging load in Tompkins County, NY';
pres.theme = { headFontFace: F, bodyFontFace: F };

const fmt = (x, d = 0) => (x === null || x === undefined ? '' : Number(x).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }));
const pngSize = (p) => { const b = fs.readFileSync(p); return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) }; };

// ------------------------------------------------------------------------------------------------ helpers
function slide(title, notes) {
  const s = pres.addSlide();
  s.background = { color: 'FFFFFF' };
  s.addText(title, { x: ML, y: 0.35, w: CW, h: 1.0, fontFace: F, fontSize: SZ.title, color: C.text, valign: 'top', margin: 0, isTextBox: true });
  if (notes) s.addNotes(notes);
  return s;
}

// paragraphs: string | {t, bold, bullet, color, size} | {runs:[{t, bold, italic, sub, sup, color}], bullet}
function text(s, paras, o = {}) {
  const runs = [];
  paras.forEach((p, i) => {
    const q = typeof p === 'string' ? { t: p } : p;
    const last = i === paras.length - 1;
    const rr = q.runs || [{ t: q.t, bold: q.bold, color: q.color, italic: q.italic }];
    rr.forEach((r, j) => {
      const opt = { bold: !!r.bold, italic: !!r.italic, color: r.color || q.color || o.color || C.text };
      if (r.sub) opt.subscript = true;
      if (r.sup) opt.superscript = true;
      if (q.size) opt.fontSize = q.size;
      if (q.bullet) opt.bullet = { indent: 16 };
      if (j === rr.length - 1 && !last) opt.breakLine = true;
      runs.push({ text: r.t, options: opt });
    });
  });
  s.addText(runs, Object.assign({ fontFace: F, fontSize: SZ.body, color: C.text, valign: 'top', margin: 0, isTextBox: true, paraSpaceAfter: 9 }, o));
}

function cite(s, t, y = 6.95, o = {}) {
  s.addText(t, Object.assign({ x: ML, y, w: CW, h: 0.42, fontFace: F, fontSize: SZ.cite, color: C.muted, valign: 'top', margin: 0, isTextBox: true }, o));
}

function caption(s, t, x, y, w, h = 0.35) {
  s.addText(t, { x, y, w, h, fontFace: F, fontSize: SZ.label, color: C.muted, valign: 'top', margin: 0, isTextBox: true });
}

function table(s, header, rows, o) {
  const n = header.length;
  const align = o.align || header.map((_, i) => (i === 0 ? 'left' : 'right'));
  const rule = (pt, color) => ({ type: 'solid', pt, color });
  const none = { type: 'none' };
  const hdr = header.map((h, i) => ({ text: h, options: { bold: true, align: align[i], color: C.text, valign: 'bottom', border: [rule(1, C.text), none, rule(0.75, C.text), none] } }));
  const body = rows.map((r, ri) => r.map((c, i) => {
    const cell = c !== null && typeof c === 'object' ? c : { text: String(c) };
    const last = ri === rows.length - 1;
    const opt = { align: align[i], color: cell.color || C.text, valign: 'middle', border: [none, none, last ? rule(1, C.text) : rule(0.5, C.faint), none] };
    if (cell.bold) opt.bold = true;
    if (cell.fill) opt.fill = { color: cell.fill };
    return { text: cell.text, options: opt };
  }));
  s.addTable([hdr, ...body], { x: o.x, y: o.y, w: o.w, colW: o.colW, fontFace: F, fontSize: o.fontSize || SZ.table, color: C.text, margin: o.margin || [0.03, 0.08, 0.03, 0.08], rowH: o.rowH, autoPage: false });
  if (n !== (o.colW || []).length) throw new Error('colW length mismatch for table: ' + header.join('|'));
}

function chartOpts(o) {
  return Object.assign({
    fontFace: F, showLegend: false, legendFontFace: F, legendFontSize: 12, legendColor: C.text, legendPos: 't',
    catAxisLabelColor: C.muted, valAxisLabelColor: C.muted, catAxisLabelFontFace: F, valAxisLabelFontFace: F,
    catAxisLabelFontSize: 12, valAxisLabelFontSize: 12, catAxisLineShow: true, catAxisLineColor: C.rule, valAxisLineShow: false,
    valGridLine: { color: C.faint, size: 0.5 }, catGridLine: { style: 'none' },
    catAxisTitleFontFace: F, valAxisTitleFontFace: F, catAxisTitleFontSize: 13, valAxisTitleFontSize: 13, catAxisTitleColor: C.text, valAxisTitleColor: C.text,
    plotArea: { fill: { color: 'FFFFFF' } }, chartArea: { fill: { color: 'FFFFFF' }, roundedCorners: false },
    dataLabelFontFace: F, dataLabelFontSize: 12, dataLabelColor: C.text,
  }, o);
}

function eqImage(s, name, x, y, maxW, scale = 1.25) {
  const p = path.join(BUILD, 'eq', `eq_${name}.png`);
  const { w, h } = pngSize(p);
  let iw = (w / 400) * scale, ih = (h / 400) * scale;
  if (iw > maxW) { ih *= maxW / iw; iw = maxW; }
  s.addImage({ path: p, x, y, w: iw, h: ih, altText: `Equation: ${name}` });
  return { w: iw, h: ih };
}

function mapImage(s, name, x, y, w, alt) {
  const p = path.join(BUILD, 'maps', name);
  const { w: pw, h: ph } = pngSize(p);
  const h = (w * ph) / pw;
  s.addImage({ path: p, x, y, w, h, altText: alt });
  return h;
}

// "E_{d}(y)" -> runs with subscript; "x^{2}" -> superscript
function rich(str) {
  const out = []; const re = /([_^])\{([^}]*)\}/g; let last = 0; let m;
  while ((m = re.exec(str)) !== null) {
    if (m.index > last) out.push({ t: str.slice(last, m.index) });
    out.push(m[1] === '_' ? { t: m[2], sub: true } : { t: m[2], sup: true });
    last = re.lastIndex;
  }
  if (last < str.length) out.push({ t: str.slice(last) });
  return out;
}
const toPptRuns = (runs, base = {}) => runs.map((r) => ({ text: r.t, options: Object.assign({}, base, r.sub ? { subscript: true } : {}, r.sup ? { superscript: true } : {}) }));

const sym = (base, sub, sup) => {
  const r = [{ t: base, italic: true }];
  if (sub) r.push({ t: sub, sub: true });
  if (sup) r.push({ t: sup, sup: true });
  return r;
};
const def = (symRuns, meaning) => ({ runs: [...symRuns, ...rich('  ' + meaning)], size: SZ.small });

// ================================================================================================ slides
// 1 — title
{
  const s = pres.addSlide();
  s.background = { color: 'FFFFFF' };
  s.addText('EV ownership and charging load in Tompkins County, New York', { x: ML, y: 2.2, w: 11.2, h: 1.5, fontFace: F, fontSize: SZ.deckTitle, color: C.text, margin: 0, valign: 'bottom', isTextBox: true });
  s.addText('A public-data model for urban building energy modelling: 2026 status quo, validation and projections to 2050', { x: ML, y: 3.85, w: 10.5, h: 0.9, fontFace: F, fontSize: 22, color: C.muted, margin: 0, valign: 'top', isTextBox: true });
  s.addText('Cheng Xuan Li  ·  14 September 2026  ·  working draft', { x: ML, y: 5.9, w: 8, h: 0.4, fontFace: F, fontSize: SZ.small, color: C.muted, margin: 0, isTextBox: true });
  s.addNotes('Deck generated from the repository (src/deck). Every number comes from docs/report_20260914_ev_model.md or results/tables. Evidence classes: A local observation, B New York observation, C non-local observation, D derived, E external model output; "inferred" = our model result conditional on stated assumptions.');
}

// 2 — scope
{
  const s = slide('The model produces hourly EV charging load for every dwelling, parcel and charging site in the county, 2026–2050',
    'Audience mapping: utility planners (load results, managed charging), UBEM validation team (interface, validation), municipal planners (maps, scenarios), researchers (methods). Basic unit is the synthetic dwelling unit; parcels act as building proxies.');
  text(s, [
    { runs: [{ t: 'Need. ', bold: true }, { t: 'Hourly EV charging energy (kWh) at building, parcel or dwelling scale for an urban building energy model built on zone-level RC models.' }] },
    { runs: [{ t: 'Basic unit. ', bold: true }, { t: '43,251 synthetic dwelling units on 2025 tax parcels; aggregates to parcels, 65 block groups and the county; non-residential sites separately.' }] },
    { runs: [{ t: 'Scope. ', bold: true }, { t: 'All grid-billed charging: home meters, workplace, public Level 2, DC fast, fleet depots, passers-by.' }] },
    { runs: [{ t: 'Time. ', bold: true }, { t: '2026 status quo; every year to 2050; 8,760 hours per year.' }] },
    { runs: [{ t: 'Data. ', bold: true }, { t: 'Public sources only.' }] },
  ], { x: ML, y: TOP, w: 5.6, h: 5.2 });
  // source: report §3 scenario table
  table(s, ['Scenario axis', 'Values', 'What varies'], [
    ['Ownership growth', 'trend, slow, stall, policy', 'EV share of new vehicle additions after 2026'],
    ['Charging', 'base, access+, managed', 'Home access (multifamily, renters), workplace buildout, off-peak managed charging'],
    ['Uncertainty', 'Monte Carlo', 'Growth parameters (400 draws), placement (200 draws), building-peak realizations (30)'],
  ], { x: 6.7, y: TOP + 0.1, w: 6.03, colW: [1.55, 1.75, 2.73], align: ['left', 'left', 'left'], fontSize: 14 });
}

// 3 — workflow diagram
{
  const s = slide('Three coupled components connect observed EV stock to hourly load at building scale',
    'Rows: growth (county stock over time), placement (which dwellings hold EVs), charging behaviour (when and how much they charge). Columns separate observed inputs, parameters, calculations, model states and outputs. Assembly combines dwelling EV expectations with class profiles and allocates non-residential pools to AFDC ports and parcels.');
  const colW = [2.25, 1.95, 1.95, 1.7, 1.4, 1.75];
  const gap = (CW - colW.reduce((a, b) => a + b, 0)) / 5;
  const xs = []; colW.reduce((x, w) => { xs.push(x); return x + w + gap; }, ML);
  const rowY = [2.0, 3.45, 4.9], rowH = 1.2;
  const heads = ['Observed inputs', 'Parameters', 'Calculations', 'States', '', 'Outputs'];
  heads.forEach((h, i) => h && s.addText(h, { x: xs[i], y: 1.55, w: colW[i], h: 0.32, fontFace: F, fontSize: SZ.label, color: C.muted, margin: 0, isTextBox: true }));
  const kinds = {
    input: { fill: { color: 'FFFFFF' }, line: { color: C.obs, width: 0.75 }, color: C.text },
    param: { fill: { color: 'FFFFFF' }, line: { color: C.muted, width: 1, dashType: 'dash' }, color: C.text },
    calc: { fill: { color: 'FFFFFF' }, line: { color: C.accent, width: 2 }, color: C.text },
    state: { fill: { color: C.stateFill }, line: { color: C.stateFill, width: 0.5 }, color: C.text },
    output: { fill: { color: C.accent }, line: { color: C.accent, width: 0.5 }, color: 'FFFFFF' },
  };
  const box = (col, y, h, kind, t) => s.addText(toPptRuns(rich(t)), Object.assign({ shape: pres.shapes.RECTANGLE, x: xs[col], y, w: colW[col], h, fontFace: F, fontSize: 13, align: 'left', valign: 'middle', margin: [3, 6, 3, 6] }, kinds[kind]));
  const arrow = (x1, y1, x2, y2) => s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipV: y2 < y1, line: { color: C.muted, width: 1.25, endArrowType: 'triangle' } });
  const rows = [
    ['EValuateNY 2011–2023 and DMV 2026 stock; new-vehicle inflows [A/D]', 't₀, k, m; survival λ, κ; scenario share s(y)', 'Cohort stock–flow model, Monte Carlo draws', 'County stock EV(y), BEV / PHEV'],
    ['DMV 2026 EVs by ZIP [A]; tax parcels, ACS, PUMS [A]', 'η, γ from NY ZIP fit [B]; NHTS odds ratios [C]; φ = 0.90', 'Allocation ensemble and placement evolution', 'Expected EVs per dwelling E_{d}(y)'],
    ['Drive Clean surveys [B]; NHTS, Norway, Boulder, Dundee sessions [C]; TMYx weather', 'Access, L1/L2, frequency, power, workplace, managed share by year', 'EV-year event simulation, 52 archetypes', 'Class profiles Π_{k,v}(t)'],
  ];
  rows.forEach((r, i) => {
    const y = rowY[i];
    box(0, y, rowH, 'input', r[0]); box(1, y, rowH, 'param', r[1]); box(2, y, rowH, 'calc', r[2]); box(3, y, rowH, 'state', r[3]);
    const cy = y + rowH / 2;
    arrow(xs[0] + colW[0], cy, xs[1], cy); arrow(xs[1] + colW[1], cy, xs[2], cy); arrow(xs[2] + colW[2], cy, xs[3], cy);
    arrow(xs[3] + colW[3], cy, xs[4], cy);
  });
  // county stock scales dwelling expectations
  arrow(xs[3] + colW[3] / 2, rowY[0] + rowH, xs[3] + colW[3] / 2, rowY[1]);
  const aY = rowY[0], aH = rowY[2] + rowH - rowY[0];
  box(4, aY, aH, 'calc', 'Load assembly: profile basis L_{d}(t); site pools allocated to AFDC ports and parcels');
  const outs = ['Hourly kWh per dwelling, parcel, block group, county', 'Hourly site loads: public L2, DC fast, workplace, fleet', 'Realizations for parcel peaks (p50, p90)'];
  outs.forEach((t, i) => { box(5, rowY[i], rowH, 'output', t); arrow(xs[4] + colW[4], rowY[i] + rowH / 2, xs[5], rowY[i] + rowH / 2); });
  cite(s, 'Evidence classes of inputs in brackets: A local, B New York, C non-local, D derived. States and outputs are model inferences conditional on stated assumptions. Validation references (NYSERDA 22-03, ChargePoint 14850, Drive Clean, Norway sessions, NREL TEMPO as benchmark) are applied to outputs.', 6.4, { h: 0.6 });
}

// 4 — observed stock
{
  const st = D.stock;
  const years = []; for (let y = 2011; y <= 2026; y++) years.push(String(y));
  const byYear = {}; st.t.forEach((t, i) => { byYear[String(Math.floor(t))] = i; });
  const ser = (k) => years.map((y) => (y in byYear ? st[k][byYear[y]] : null));
  const s = slide('Tompkins has 3,233 plug-in EVs in 2026, 5.4 % of light-duty vehicles and the second-highest share in New York',
    'PHEVs are coded GAS in the DMV file, so drivetrain comes from VIN decoding (decision 0002). Bars use the ZIP population-share definition to stay consistent with EValuateNY history (3,123 in 2026); the county-field count is 3,233. No snapshots exist for 2024–2025 in either source.');
  s.addChart(pres.charts.BAR, [{ name: 'BEV', labels: years, values: ser('BEV') }, { name: 'PHEV', labels: years, values: ser('PHEV') }], chartOpts({
    x: ML, y: TOP, w: 7.4, h: 5.1, barDir: 'col', barGrouping: 'stacked', barGapWidthPct: 45, chartColors: [C.accent, C.accentLight],
    showLegend: true, legendPos: 't', showValAxisTitle: true, valAxisTitle: 'Plug-in EVs registered', valAxisLabelFormatCode: '#,##0',
    showCatAxisTitle: true, catAxisTitle: 'Snapshot year (2024–2025 not observed)', catAxisLabelFrequency: 1,
  }));
  // source: report §4.1
  table(s, ['Quantity (2026)', 'Value'], [
    ['Plug-in EVs, county field', { text: '3,233', bold: true }],
    ['BEV / PHEV', '1,833 / 1,400'],
    ['Share of light-duty vehicles', '5.36 %'],
    ['Rank among 62 NY counties', '2nd (NY 3.14 %)'],
    ['Personal EVs placed in housing', '2,875'],
    ['Fleet / organizational EVs', '≈ 297'],
  ], { x: 8.4, y: TOP + 0.15, w: 4.33, colW: [2.63, 1.7], fontSize: 15 });
  cite(s, 'NYS DMV registrations (data.ny.gov w4pv-hbkt, snapshot 2026-09-02), VIN-decoded with NHTSA vPIC and EValuateNY [A]; EValuateNY v11 annual snapshots 2011–2023 [D]. Bars: ZIP population-share definition (2026: 3,123).', 6.8);
}

// 5 — synthetic population
{
  const v = D.synthetic.tenure_structure;
  const s = slide('Synthetic dwelling units reproduce block-group tenure, structure, vehicle and income counts (R² ≥ 0.99)',
    'Parcels give dwelling-unit counts by property class; counts are calibrated per block group to ACS occupied units by structure. Each unit receives a PUMS household with weights raked (IPF) to block-group marginals. 1,723 ACS units had no parcel of matching class in their block group and were placed on the nearest class.');
  s.addChart(pres.charts.SCATTER, [{ name: 'ACS', values: v.acs }, { name: 'Synthetic dwelling units', values: v.synthetic }, { name: 'Equal counts', values: v.acs }], chartOpts({
    x: ML, y: TOP, w: 5.6, h: 5.1, lineSize: 0, lineDataSymbol: 'circle', lineDataSymbolSize: 5, chartColors: [C.accent, C.lightGrey],
    showValAxisTitle: true, valAxisTitle: 'Synthetic dwelling units per cell', showCatAxisTitle: true, catAxisTitle: 'ACS 2020–2024 households per cell',
    valAxisLabelFormatCode: '#,##0', catAxisLabelFormatCode: '#,##0', showLegend: true, legendPos: 't',
  }));
  caption(s, `Tenure × structure cells, ${v.n} block-group cells (65 block groups × 12 classes)`, ML, TOP + 5.15, 5.6);
  // source: report §4.2
  table(s, ['Block-group margin', 'Cells', 'R²', 'SRMSE'], [
    ['Tenure × structure', String(D.synthetic.tenure_structure.n), '0.999', '0.063'],
    ['Tenure × vehicles', String(D.synthetic.tenure_vehicles.n), '0.995', '0.117'],
    ['Income band', String(D.synthetic.income.n), '0.994', '0.065'],
  ], { x: 6.8, y: TOP + 0.15, w: 5.93, colW: [2.6, 1.0, 1.1, 1.23] });
  text(s, [
    'Total: 43,251 dwelling units vs 43,263 ACS households.',
    'Structure mix: single-family detached 52 %, attached 4 %, 2–4 units 14 %, 5–19 units 12 %, 20+ units 11 %, mobile 7 %.',
    { t: 'Validates composition only; joint distributions within block groups are not observed.', color: C.muted },
  ], { x: 6.8, y: 3.35, w: 5.93, h: 3.0, fontSize: SZ.body });
  cite(s, 'NYS ITS tax parcels 2025 [A]; ACS 2020–2024 5-year block-group tables and PUMS, PUMA 02300 [A]. SRMSE = standardized root mean square error.', 6.95);
}

// 6 — propensity equation
{
  const s = slide('Household-class EV propensity is calibrated on New York ZIP codes as a mean-field count model',
    'Ecological model: ZIP-level counts over ACS composition. Class effects a and c are identified only between areas. Tempered-prior variants shrink class effects toward NHTS 2022 and Drive Clean representation ratios with weight ω.');
  const e = eqImage(s, 'propensity', ML, TOP + 0.1, 8.2, 1.3);
  text(s, [
    def(sym('μ', 'z'), 'expected EVs in ZIP z;  HH_{z,τ} households by tenure τ'),
    def(sym('s', 'g|τ,z'), 'share of structure class g;  a_{g,τ} class effect'),
    def(sym('s', 'v|τ,z'), 'share with v vehicles;  η vehicle elasticity'),
    def(sym('s', 'i,z'), 'income-band share;  c_{i} income effect'),
    def(sym('Z', 'z'), 'standardized log median home value, bachelor’s-degree share'),
    def([{ t: 'a = ω log a', italic: true }, { t: 'prior', sup: true }], 'tempered priors (NHTS 2022, Drive Clean); same for c'),
  ], { x: ML, y: TOP + e.h + 0.45, w: 7.6, h: 3.2, paraSpaceAfter: 6 });
  text(s, [
    { t: 'Interpretation', bold: true },
    'Fitted to 1,361 New York ZIPs (DMV 2023 and 2026) with a negative-binomial likelihood.',
    'Tested by 10-fold cross-validation that holds out whole counties, and by a within-county allocation test: fit on 2023, distribute known 2026 county totals across ZIPs.',
    { t: 'Class effects are ecological; they do not identify within-area household behaviour.', color: C.muted },
  ], { x: 8.75, y: TOP + 0.1, w: 3.98, h: 5.2 });
  cite(s, 'DMV registrations [A/B]; ACS 2020–2024 ZCTA composition [B]; NHTS 2022 [C]; NYSERDA Drive Clean rebate surveys [B]. Report §4.3.', 6.95);
}

// 7 — CV table
{
  const s = slide('Vehicles available explain most between-ZIP variation; imposing survey priors makes allocation worse',
    'Deviance explained is relative to a households-only model under county-grouped cross-validation. Allocation MAE: fit on 2023, allocate observed 2026 county totals to ZIPs. M5 (tempered priors) is selected for placement; its prior weight is near zero, so it behaves like M1/M3 while retaining a principled link to individual evidence.');
  // source: report §4.3 table
  const hl = (t) => ({ text: t, bold: true, color: C.accent });
  table(s, ['Model', 'Deviance explained 2023', 'Deviance explained 2026', 'Allocation MAE 2023→2026 (EVs/ZIP)'], [
    ['M0 households only', '0', '0', '68.6'],
    ['M1 vehicles only', hl('0.803'), hl('0.783'), '64.1'],
    ['M2 priors fixed (NHTS / Drive Clean)', '0.657', '0.652', '79.1'],
    ['M3 free class effects', '0.786', '0.763', hl('62.6')],
    ['M4 free class effects, no area terms', '0.741', '0.729', '75.6'],
    [{ text: 'M5 tempered priors (selected)', bold: true }, '0.790', '0.753', '63.6'],
    ['M6 separately tempered', '0.788', '0.753', '63.6'],
  ], { x: ML, y: TOP + 0.05, w: 8.1, colW: [3.3, 1.5, 1.5, 1.8], fontSize: 15 });
  text(s, [
    'Prior weight ω = 0.00 ± 0.07 (2023) and 0.04 ± 0.06 (2026).',
    'EVs scale sub-proportionally with vehicles: η ≈ 0.5–0.8.',
    'Full priors double-count: multifamily and renter households already own fewer vehicles.',
    { t: 'Individual-level NHTS evidence (income odds ratio 6.7 for ≥ $150k vs < $50k) remains the only evidence on within-area composition effects.', color: C.muted },
  ], { x: 9.15, y: TOP + 0.05, w: 3.58, h: 5.3 });
  cite(s, '10-fold county-grouped cross-validation over 1,361 NY ZIPs [B]. MAE = mean absolute error. Report §4.3; results/tables/propensity_cv.csv.', 6.95);
}

// 8 — allocation equation
{
  const s = slide('Observed ZIP totals are placed on dwelling units by a two-model ensemble, capped by vehicles',
    'The ensemble averages the tested ecological weighting and NHTS individual-level odds ratios. Monte Carlo draws sample vehicle slots without replacement (Efraimidis–Spirakis) and pick one of the weightings per draw, so draws carry both sampling and structural uncertainty.');
  const e = eqImage(s, 'allocation', ML, TOP + 0.1, 7.6, 1.25);
  text(s, [
    def(sym('T', 'z'), 'observed personal EVs in ZIP z (DMV 2026)'),
    def(sym('v', 'd'), 'vehicles available to dwelling d'),
    def(sym('w', 'd', '(m)'), 'weighting m: ecological model or individual evidence'),
    def(sym('Z', 'bg'), 'block-group area covariates of the selected model'),
    def([{ t: 'OR', italic: true }], 'NHTS 2022 odds ratios: income < $50k 0.48, $50–100k 1.00, $100–150k 1.51, ≥ $150k 3.23; single-family 1.31; owner 0.96'),
  ], { x: ML, y: TOP + e.h + 0.45, w: 7.6, h: 3.0, paraSpaceAfter: 6 });
  text(s, [
    { t: 'Interpretation', bold: true },
    'Every weighting reproduces the observed ZIP totals exactly.',
    '200 Monte Carlo draws; each draw samples vehicle slots and one weighting.',
    'Bounds use the uniform and full-prior weightings.',
    { t: 'Reproducing ZIP totals validates nothing below ZIP (decision 0005).', color: C.muted },
  ], { x: 8.75, y: TOP + 0.1, w: 3.98, h: 5.2 });
  cite(s, 'DMV 2026 [A]; NHTS 2022 [C]; synthetic dwelling units [A/D]. Report §4.4.', 6.95);
}

// 9 — allocation shares chart
{
  const a = D.allocation;
  const s = slide('Below ZIP level placement is unobserved: the multifamily share of EVs ranges from 9 % to 31 % across weightings',
    'Shares of personal EVs in multifamily (2+ units) housing and in renter households, 2026, by weighting. The central ensemble is used for all load results; uniform and full-prior weightings bound the plausible range.');
  const labels = a.labels.slice().reverse();
  s.addChart(pres.charts.BAR, [
    { name: 'Multifamily (2+ units)', labels, values: a.mf.slice().reverse() },
    { name: 'Renter households', labels, values: a.renter.slice().reverse() },
  ], chartOpts({
    x: ML, y: TOP, w: 7.6, h: 5.2, barDir: 'bar', barGrouping: 'clustered', barGapWidthPct: 60, chartColors: [C.accent, C.lightGrey],
    showLegend: true, legendPos: 't', showValue: true, dataLabelFormatCode: '0.0', dataLabelPosition: 'outEnd',
    valAxisMinVal: 0, valAxisMaxVal: 50, valAxisMajorUnit: 10, showValAxisTitle: true, valAxisTitle: 'Share of personal EVs, 2026 (%)',
    catAxisLabelFontSize: 13,
  }));
  text(s, [
    { runs: [{ t: 'Central ensemble: ' }, { t: `${fmt(a.mf[0], 1)} %`, bold: true }, { t: ` of personal EVs in multifamily housing, where ${fmt(a.mf_households, 1)} % of households live.` }] },
    { runs: [{ t: 'Renters: ' }, { t: `${fmt(a.renter[0], 1)} %`, bold: true }, { t: ' of personal EVs.' }] },
    'Block-group totals differ by up to 2–3× across weightings in central Ithaca; sampling uncertainty is 10–50 % of the mean at block-group level.',
    { t: 'Placement below ZIP is the most consequential unvalidated quantity for building-level load.', color: C.muted },
  ], { x: 8.7, y: TOP + 0.1, w: 4.03, h: 5.2 });
  cite(s, 'Model inference [inferred]; weightings defined on the previous slide. results/tables/allocation_structure_shares_2026.csv, allocation_tenure_shares_2026.csv.', 6.95);
}

// 10 — map EVs per household
{
  const s = slide('Expected EV ownership per household is highest in the suburban ring around the City of Ithaca',
    'Central-ensemble expectation of personal EVs per 100 households by 2020 block group, 2026. Right panel enlarges the City of Ithaca (dashed outline). Values are model inferences constrained to observed ZIP totals.');
  mapImage(s, 'map_ev_per_100hh_2026.png', ML + 0.2, TOP - 0.05, 11.7, 'Map of expected personal EVs per 100 households by block group, 2026');
  cite(s, 'Central allocation ensemble, 2026 [inferred], constrained to DMV ZIP totals [A]. 2020 block groups (TIGER/Line 2024), EPSG:32618.', 6.95);
}

// 11 — map structural spread
{
  const m = D.map_allocation;
  const s = slide(`Weightings disagree most in central Ithaca: block-group spread is ${fmt(m.spread_median, 1)}× at the median and up to ${fmt(m.spread_max, 0)}×`,
    'Ratio of the largest to the smallest expected EV count across the five weightings (ecological, uniform, vehicles, individual NHTS, full priors), per block group. High ratios mark where placement assumptions, not data, determine the result.');
  mapImage(s, 'map_structural_spread_2026.png', ML + 0.2, TOP - 0.05, 11.7, 'Map of structural spread of expected EVs across weightings by block group, 2026');
  cite(s, 'Model inference [inferred]; results/tables/allocation_bg_2026_uncertainty.csv. 2020 block groups, EPSG:32618.', 6.95);
}

// 12 — concentration
{
  const c = D.concentration;
  const labels = c.t.map((t) => String(Math.floor(t)));
  const s = slide('Adoption becomes less concentrated as it grows, so placement converges by φ ≈ 0.90 per doubling of the stock',
    'Gini coefficient of EVs across households (ZIP level) and share of EVs in the top-decile ZIPs, New York State, EValuateNY snapshots and DMV 2026. φ is the slope of log ZIP rates between snapshots; 0.87 over 2023→2026, about 0.90 per doubling of penetration. Projections use this exponent to flatten relative ZIP and dwelling weights.');
  s.addChart(pres.charts.LINE, [
    { name: 'Gini across households', labels, values: c.gini },
    { name: 'Top-decile ZIP share of EVs', labels, values: c.top_decile.map((x) => x / 100) },
  ], chartOpts({
    x: ML, y: TOP, w: 7.3, h: 3.9, lineSize: 2.25, lineDataSymbol: 'circle', lineDataSymbolSize: 6, chartColors: [C.accent, C.grey],
    showLegend: true, legendPos: 't', valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.2, valAxisLabelFormatCode: '0.0',
    showValAxisTitle: true, valAxisTitle: 'Index or share (0–1)', showCatAxisTitle: true, catAxisTitle: 'Snapshot year, New York State',
  }));
  // source: report §4.5
  table(s, ['NY snapshot', 'EVs per 100 households', 'Gini'], [
    ['2011', '0.02', '0.86'], ['2016', '0.19', '0.57'], ['2020', '0.77', '0.51'], ['2023', '1.73', '0.49'], ['2026', { text: '4.23', bold: true }, { text: '0.46', bold: true }],
  ], { x: 8.45, y: TOP + 0.1, w: 4.28, colW: [1.4, 1.78, 1.1] });
  const e = eqImage(s, 'evolution', ML, 5.72, 7.3, 1.05);
  text(s, [{ runs: [{ t: 'π', italic: true }, { t: 'z', sub: true }, { t: ' ZIP share of EVs;  ' }, { t: 'h', italic: true }, { t: 'z', sub: true }, { t: ' household share;  ' }, { t: 'w', italic: true }, { t: 'd', sub: true }, { t: ' dwelling weight' }], size: SZ.small }],
    { x: ML, y: 5.72 + e.h + 0.12, w: 7.3, h: 0.4 });
  cite(s, 'EValuateNY v11 snapshots 2011–2023 [D]; DMV 2026 [A/B]; ACS households [B]. results/tables/adoption_concentration_ny.csv.', 6.95);
}

// 13 — growth model and backcast
{
  const b = D.backcast;
  const years = []; for (let y = 2011; y <= 2031; y++) years.push(y);
  const at = (ts, vs) => years.map((y) => { const i = ts.indexOf(y); return i >= 0 ? vs[i] : null; });
  const obs = years.map((y) => { let v = null; b.obs_t.forEach((t, i) => { if (Math.floor(t) === y) v = b.obs_ev[i]; }); return v; });
  const labels = years.map(String);
  const s = slide('A stock–flow model fitted to data through 2021 overshoots the 2026 Tompkins stock by 90 %',
    'Backcast validation: parameters fitted only to observations up to 2021 predict later stock. Early-diffusion extrapolation missed the 2024–2026 slowdown (federal tax credit ended 2025; the observed EV share of new additions dipped). Projections therefore start from the observed 2026 stock by model year.');
  const e = eqImage(s, 'growth', ML, TOP + 0.1, 5.4, 1.2);
  text(s, [
    def(sym('s', '', '') .slice(0, 1).concat([{ t: '(v)' }]), 'EV share of new light-duty additions in year v'),
    def(sym('N', 'new'), '3,600 additions per year;  m absorbs net used-EV imports'),
    def(sym('S', '').slice(0, 1).concat([{ t: '(a)' }]), 'Weibull survival, κ = 3.5, λ = 17 years'),
  ], { x: ML, y: TOP + e.h + 0.35, w: 5.4, h: 1.4, paraSpaceAfter: 4 });
  // source: report §4.6 backcast table
  table(s, ['Backcast (fit ≤ 2021)', 'Stock 2023-04', 'Stock 2026-09'], [
    ['New York', '+3 %', '+27 %'],
    ['Tompkins', '+21 %', { text: '+90 %', bold: true, color: C.accent }],
  ], { x: ML, y: 4.95, w: 5.4, colW: [2.2, 1.6, 1.6], fontSize: 15 });
  s.addChart([
    { type: pres.charts.BAR, data: [{ name: 'Observed stock', labels, values: obs }], options: { barDir: 'col', chartColors: [C.lightGrey], barGapWidthPct: 50 } },
    { type: pres.charts.LINE, data: [{ name: 'Fit, all data', labels, values: at(b.fit_full_t, b.fit_full_ev) }, { name: 'Fit, data ≤ 2021', labels, values: at(b.fit_le2021_t, b.fit_le2021_ev) }], options: { chartColors: [C.accent, C.dcfc], lineSize: 2.5, lineDataSymbol: 'none' } },
  ], chartOpts({
    x: 6.4, y: TOP, w: 6.33, h: 5.1, showLegend: true, legendPos: 't', valAxisLabelFormatCode: '#,##0', valAxisMaxVal: 8000, valAxisMinVal: 0,
    showValAxisTitle: true, valAxisTitle: 'Tompkins plug-in EVs', catAxisLabelFrequency: 5, showCatAxisTitle: true, catAxisTitle: 'Year', displayBlanksAs: 'gap',
  }));
  cite(s, 'EValuateNY v11 2011–2023 [D]; DMV 2026 [A]; DMV transactions and EValuateNY first appearances for new-vehicle shares [D/A]. Fits: results/tables/growth_fit_params.csv.', 6.95);
}

// 14 — projections
{
  const P = D.projections;
  const labels = P.trend.year.map(String);
  const s = slide('Projections start from the observed 2026 stock: about 6,000 EVs in 2030 and 48,000 by 2050 under the trend scenario',
    'Scenarios define the EV share of new additions after 2026, anchored at the observed 10.9 %. Trend band: 5th–95th percentile of 400 parameter draws (t0, k, m, N_new ±15 %, λ ±2 years). Parameter uncertainty dominates after 2035.');
  s.addChart(pres.charts.LINE, [
    { name: 'trend (median)', labels, values: P.trend.p50 },
    { name: 'trend 5th pct', labels, values: P.trend.p05 },
    { name: 'trend 95th pct', labels, values: P.trend.p95 },
    { name: 'policy', labels, values: P.policy.p50 },
    { name: 'stall', labels, values: P.stall.p50 },
    { name: 'slow', labels, values: P.slow.p50 },
  ], chartOpts({
    x: ML, y: TOP, w: 6.6, h: 5.15, lineSize: 2, lineDataSymbol: 'none', chartColors: [C.accent, C.accentLight, C.accentLight, C.obs, C.grey, C.lightGrey],
    showLegend: true, legendPos: 'r', valAxisLabelFormatCode: '#,##0', showValAxisTitle: true, valAxisTitle: 'Tompkins plug-in EVs (year end)', catAxisLabelFrequency: 4,
  }));
  // source: report §4.6 scenario table
  table(s, ['Scenario after 2026', '2030', '2035', '2040', '2050', '2050 fleet share'], [
    [{ text: 'trend: fitted steepness', bold: true }, '5,995', '13,097', '24,578', '47,874', '80 %'],
    ['slow: s_max 0.6, half steepness', '5,249', '8,388', '12,397', '22,161', '37 %'],
    ['stall: flat to 2030, +4 years', '4,752', '8,020', '15,975', '40,681', '68 %'],
    ['policy: 100 % of additions by 2035', '8,686', '23,409', '39,955', '57,825', '97 %'],
  ], { x: 7.45, y: TOP + 0.1, w: 5.28, colW: [1.78, 0.62, 0.68, 0.68, 0.72, 0.8], fontSize: 12.5 });
  text(s, [
    'Trend 2030: 90 % band 4,683–8,223; 2040: 14,155–43,521.',
    { t: 'Post-2030 adoption is scenario-conditional and cannot be validated.', color: C.muted },
  ], { x: 7.45, y: 4.35, w: 5.28, h: 2.0, fontSize: SZ.small });
  cite(s, 'Cohort stock–flow model [inferred / E]; initial stock by model year from DMV 2026 [A]. results/tables/growth_projection_tompkins.csv.', 6.95);
}

// 15 — charging parameters
{
  const s = slide('Charging parameters change by year and scenario; most rest on New York survey data or stated assumptions',
    'Values are linear between anchor years (data/processed/charging/parameters_by_year.csv). Drive Clean respondents are rebate recipients (new-car buyers, mostly owners), so access and frequency parameters for renters and multifamily residents are assumptions informed by the Statewide Multifamily Building Study.');
  // source: report §5.1
  table(s, ['Parameter', '2026', '2035 (base / access+ / managed)', '2050 (base)', 'Evidence'], [
    ['Annual miles, BEV / PHEV', '10,670 / 10,082', 'held', 'held', 'B (Drive Clean 2024)'],
    ['Energy at wheel, BEV / PHEV (kWh/mi, 20 °C)', '0.31 / 0.34', '0.29 / 0.32', '0.27 / 0.30', 'assumption'],
    ['PHEV electric range (mi)', '35', '45', '50', 'assumption'],
    ['Home access: single-family owner / renter', '0.95 / 0.75', '0.96 / 0.80 (access+ 0.88)', '0.97 / 0.85', 'B + assumption'],
    ['Home access: 2–4 units / 5+ units', '0.55 / 0.35', '0.62 / 0.45 (access+ 0.75 / 0.65)', '0.70 / 0.60', 'B (SMBS) + assumption'],
    ['Home Level 2 share, BEV / PHEV', '0.80 / 0.28', '0.88 / 0.40', '0.92 / 0.50', 'B (Drive Clean)'],
    ['Power L1 / L2 BEV / L2 PHEV (kW)', '1.4 / 7.2 / 3.6', '1.4 / 8.0 / 5.0', '1.4 / 8.5 / 6.0', 'assumption'],
    ['Frequency BEV: daily / few-weekly / weekly / rare (%)', '34 / 28 / 20 / 7', '', '30 / 30 / 22 / 8', 'B'],
    ['Workplace access per worker × use', '0.23 × 0.65', '0.32 (access+ 0.45) × 0.65', '0.40 × 0.65', 'B'],
    ['Public top-up share (home-access EVs)', '0.08', '0.07', '0.06', 'assumption'],
    ['Managed share of home L2 sessions', '0 (managed 0.05)', '0 (managed 0.35)', '0 (managed 0.60)', 'scenario'],
    ['Passer-by share of DC fast energy', '0.25', '0.25', '0.25', 'assumption'],
    ['Fleet miles per year; kWh/mi', '14,000; 0.40', '', '', 'assumption'],
  ], { x: ML, y: TOP, w: CW, colW: [4.1, 1.75, 2.85, 1.55, 1.88], align: ['left', 'right', 'right', 'right', 'left'], fontSize: 13 });
  text(s, [{ runs: [{ t: 'Temperature multiplier on energy per mile:  ' }, { t: 'm(T) = 1 + 0.011 max(0, 20 − T) + 0.006 max(0, T − 25)', italic: true }, { t: '  (≈ +30 % at −7 °C; assumption, TMYx 2011–2025 Ithaca weather)' }], size: SZ.small }],
    { x: ML, y: 5.75, w: CW, h: 0.7 });
  cite(s, 'NYSERDA Drive Clean Ownership and Adoption Surveys 2023–2025 [B]; NYSERDA Statewide Multifamily Building Study 2022 [B]; OneBuilding TMYx [A]. Report §5.1.', 6.95);
}

// 16 — event model
{
  const s = slide('Each simulated EV-year follows an energy ledger with sampled trips, plug-in times and dwell times',
    'The library holds 52 behavioural archetypes (drivetrain × home access × level × frequency × workplace × managed) × 60 EV-years for anchor years 2026, 2030, 2035, 2040, 2050. Hourly energy is the overlap of each charging session with each clock hour.');
  const e = eqImage(s, 'event', ML, TOP + 0.1, 7.9, 1.15);
  text(s, [
    def(sym('D', 't'), 'battery deficit at the wheel (0 ≤ D ≤ C, capacity C);  E_{t} energy used in hour t'),
    def(sym('d', 't'), 'miles in hour t; annual miles A lognormal, hourly weights g_{t} gamma'),
    def(sym('q', ''), 'energy delivered at the plug; η_{ℓ} efficiency (L1 0.83, L2 0.90, DC 0.92), P_{ℓ} power'),
  ], { x: ML, y: TOP + e.h + 0.4, w: 7.9, h: 1.5, paraSpaceAfter: 5 });
  text(s, [
    { t: 'Daily sequence', bold: true },
    { t: 'Morning driving → workplace opportunity (NHTS 2022 work arrival and dwell, 6.6 kW)', bullet: true },
    { t: 'Afternoon driving → public top-up (Boulder L2, Dundee DC fast sessions)', bullet: true },
    { t: 'Home plug-in by frequency type; BEVs forced when D > 0.6 C; plug-in time and connection from Norway sessions of the same day type', bullet: true },
    { t: 'BEVs above 0.95 C take an en-route DC fast session; PHEVs never DC fast charge', bullet: true },
    { t: 'Managed sessions start at max(plug-in, 23:00 + U[0, 2] h)', bullet: true },
  ], { x: 8.85, y: TOP + 0.1, w: 3.88, h: 5.3, fontSize: 16, paraSpaceAfter: 6 });
  cite(s, 'NHTS 2022 [C]; Norway residential charging sessions (Zenodo 13896176) [C]; City of Boulder sessions [C]; Dundee public charge points [C]; TMYx weather [A]. Report §5.2.', 6.95);
}

// 17 — sampling results
{
  const V = D.validation;
  const lab = { daily: 'Daily', few_week: 'Few times a week', weekly: 'Weekly', rare: 'Rarely' };
  const s = slide('Sampled home sessions match Norwegian session energy; simulated BEV charging frequency is close to survey categories',
    'Left: share of BEV drivers by home charging frequency, simulated vs Drive Clean 2024 (total variation distance 0.18). PHEV agreement is by construction because frequency types are inputs. Right: quantiles of home session energy, simulated vs Norway residential sessions (connection times are partly by construction).');
  const f = V.frequency.BEV;
  s.addChart(pres.charts.BAR, [
    { name: 'Simulated', labels: f.category.map((k) => lab[k] || k), values: f.sim },
    { name: 'Drive Clean 2024 survey', labels: f.category.map((k) => lab[k] || k), values: f.drive_clean },
  ], chartOpts({
    x: ML, y: TOP + 0.35, w: 5.9, h: 4.6, barDir: 'col', barGrouping: 'clustered', barGapWidthPct: 60, chartColors: [C.accent, C.obs],
    showLegend: true, legendPos: 't', showValue: true, dataLabelFormatCode: '0', dataLabelPosition: 'outEnd',
    valAxisMinVal: 0, valAxisMaxVal: 60, valAxisMajorUnit: 10, showValAxisTitle: true, valAxisTitle: 'Share of BEV drivers (%)',
  }));
  caption(s, 'BEV home charging frequency', ML, TOP, 5.9);
  const q = V.sessions;
  const ql = q.quantile.map((x) => `p${Math.round(x * 100)}`);
  s.addChart(pres.charts.LINE, [
    { name: 'Simulated home sessions', labels: ql, values: q.sim_home_kwh },
    { name: 'Norway residential sessions', labels: ql, values: q.norway_kwh },
  ], chartOpts({
    x: 6.83, y: TOP + 0.35, w: 5.9, h: 4.6, lineSize: 2.25, lineDataSymbol: 'circle', lineDataSymbolSize: 7, chartColors: [C.accent, C.obs],
    showLegend: true, legendPos: 't', valAxisMinVal: 0, showValAxisTitle: true, valAxisTitle: 'Energy per session (kWh)', showCatAxisTitle: true, catAxisTitle: 'Quantile of sessions',
  }));
  caption(s, 'Home session energy quantiles', 6.83, TOP, 5.9);
  cite(s, 'NYSERDA Drive Clean Ownership Survey 2024 [B, self-report]; Norway residential charging sessions [C]; simulated 2026 library [inferred]. results/tables/charging_validation_frequency.csv, charging_validation_sessions.csv.', 6.7, { h: 0.6 });
}

// 18 — shape validation
{
  const V = D.validation.shapes;
  const s = slide('Simulated weekday charging shapes match New York measurements: r = 0.97 at homes vs multifamily sites, 0.91 at public ports',
    'Shapes are normalized to their peak, compared at the NYSERDA 22-03 Figure 18 anchor hours (figure-read, ±1–2 percentage points). The workplace comparison (r = 0.88) is not independent because 22-03 is also the workplace shape source.');
  const panel = (key, x, title, ref) => {
    const d = V[key];
    const labels = d.hour.map((h) => `${String(h).padStart(2, '0')}:00`);
    s.addChart(pres.charts.LINE, [
      { name: 'Simulated', labels, values: d.sim }, { name: ref, labels, values: d.ny },
    ], chartOpts({
      x, y: TOP + 0.35, w: 5.9, h: 4.5, lineSize: 2.25, lineDataSymbol: 'circle', lineDataSymbolSize: 7, chartColors: [C.accent, C.obs],
      showLegend: true, legendPos: 't', valAxisMinVal: 0, valAxisMaxVal: 1.1, valAxisMajorUnit: 0.2, valAxisLabelFormatCode: '0.0',
      showValAxisTitle: true, valAxisTitle: 'Load relative to daily peak', showCatAxisTitle: true, catAxisTitle: 'Hour of weekday (local standard time)',
    }));
    caption(s, title, x, TOP, 5.9);
  };
  panel('home', ML, 'Home charging vs NY multifamily sites', 'NYSERDA 22-03 multifamily');
  panel('public_l2', 6.83, 'Public Level 2 vs NY public sites', 'NYSERDA 22-03 public');
  cite(s, 'NYSERDA Report 22-03, Electric Vehicle Charging Station Cost and Usage Trends, Fig. 18 (1,288 stations, 2012–2020) [B]; simulated 2026 library [inferred].', 6.8);
}

// 19 — validation summary table
{
  const s = slide('Validation of the 2026 charging model: most checks agree, and each is labelled by independence',
    'V8 compares with NREL TEMPO, a model: a benchmark, not validation. Checks marked “by construction” or “not independent” cannot falsify the model and are reported for transparency.');
  // source: report §5.4
  const ok = (t) => ({ text: t, color: C.accent, bold: true });
  table(s, ['Check', 'Result', 'Reference', 'Class', 'Status'], [
    ['V1 Home charging frequency, BEV', 'TVD 0.18', 'Drive Clean 2024', 'B', 'partly calibrated'],
    ['V1 Home charging frequency, PHEV', 'TVD ≈ 0.00', 'Drive Clean 2024', 'B', 'by construction'],
    ['V2 Home session energy, connection', 'quantiles within ~10 %', 'Norway sessions', 'C', 'connection partly by construction'],
    ['V3 Weekday shape, home vs multifamily', ok('r = 0.97'), 'NYSERDA 22-03', 'B', 'independent'],
    ['V3 Weekday shape, workplace', 'r = 0.88', 'NYSERDA 22-03', 'B', 'not independent'],
    ['V3 Weekday shape, public Level 2', ok('r = 0.91'), 'NYSERDA 22-03', 'B', 'independent'],
    ['V4 Public L2 utilisation', ok('9.6 kWh/port-day'), 'ChargePoint 14850: 7.3 (2019), 16.4 (2022)', 'A/B', 'independent, within range'],
    ['V5 Annual plug energy per resident EV', ok('2,994 kWh'), 'Survey miles × efficiency: 3,165', 'B', 'consistent (−5 %)'],
    ['V6 Monthly energy index', 'r = 0.82', 'Dundee public, detrended', 'C', 'independent, non-NY'],
    ['V7 Residential diversity, peak kW per EV', 'between 3.6 and 7.2 kW curves', 'Norway sessions', 'C', 'shape consistent'],
    ['V8 County annual energy', 'TEMPO / simulated = 2.2', 'NREL TEMPO 2022', 'E', 'benchmark only'],
  ], { x: ML, y: TOP, w: CW, colW: [3.55, 2.35, 3.1, 0.75, 2.38], align: ['left', 'right', 'left', 'left', 'left'], fontSize: 14 });
  cite(s, 'TVD = total variation distance; r = Pearson correlation at anchor hours. results/tables/charging_validation_summary.csv; decision 0006 records design changes triggered by failed checks.', 6.85);
}

// 20 — energy per EV
{
  const e = D.energy_reconciliation;
  const pick = [
    ['Drive Clean miles × efficiency (Tompkins mix)', 'Drive Clean miles × efficiency, Tompkins mix [B]'],
    ['NHTS 2022 BEV diary miles (n=166)', 'NHTS 2022 BEVs, diary miles, n = 166 [C]'],
    ['NHTS 2022 BEV self-reported annual miles', 'NHTS 2022 BEVs, self-reported miles [C]'],
    ['Norway residential median user (home energy only)', 'Norway median user, home only [C]'],
    ['Event model 2026: BEV', 'Event model 2026, BEV [inferred]'],
    ['Event model 2026: PHEV', 'Event model 2026, PHEV [inferred]'],
    ['Event model 2026: resident EV mix', 'Event model 2026, resident mix [inferred]'],
    ['TEMPO 2022 reference MY2026 / observed EVs', 'NREL TEMPO 2022 per observed EV [E]'],
  ];
  const labels = [], values = [];
  pick.forEach(([src, lab]) => { const i = e.source.indexOf(src); if (i >= 0) { labels.push(lab); values.push(e.kwh_per_ev[i]); } });
  const s = slide('A resident EV draws about 3,000 kWh a year from the grid, consistent with survey mileage; TEMPO implies 2.5 times more',
    'Location energy shares of resident EVs are model outputs of the event simulation, replacing the earlier 80/7/8/5 assumption. The DC fast share is the least constrained quantity: no public New York data.');
  s.addChart(pres.charts.BAR, [{ name: 'kWh per EV-year', labels: labels.slice().reverse(), values: values.slice().reverse() }], chartOpts({
    x: ML, y: TOP, w: 8.0, h: 5.2, barDir: 'bar', barGapWidthPct: 45, chartColors: [C.accent], showValue: true, dataLabelFormatCode: '#,##0', dataLabelPosition: 'outEnd',
    valAxisMinVal: 0, valAxisMaxVal: 8000, valAxisMajorUnit: 2000, valAxisLabelFormatCode: '#,##0', showValAxisTitle: true, valAxisTitle: 'Grid energy per EV-year (kWh)', catAxisLabelFontSize: 13,
  }));
  // source: report §5.5
  table(s, ['Location (resident EVs, 2026)', 'Energy share'], [
    ['Home', '67 %'], ['Workplace', '5 %'], ['Public Level 2', '10 %'], ['DC fast (incl. en route)', '18 %'],
  ], { x: 9.0, y: TOP + 0.1, w: 3.73, colW: [2.53, 1.2], fontSize: 15 });
  text(s, [{ t: 'Shares are model outputs [inferred]; the DC fast share has no public New York observation.', color: C.muted }], { x: 9.0, y: 3.55, w: 3.73, h: 1.5, fontSize: SZ.small });
  cite(s, 'NYSERDA Drive Clean surveys [B]; NHTS 2022 [C]; Norway sessions [C]; NREL TEMPO 2022 via dsgrid [E]. results/tables/energy_reconciliation.csv.', 6.95);
}

// 21 — assembly equation and UBEM interface
{
  const s = slide('Expected load at any entity is exact through a profile basis; realizations are needed for building peaks',
    'UBEM coupling: expected hourly kWh per dwelling, parcel or block group is reconstructed from annual expectations E and class profiles Π (docs/ubem_interface.md). Peaks are not additive: use Monte Carlo realizations (Poisson EV counts per dwelling, archetype and library EV-year per EV) for building capacity questions.');
  const e = eqImage(s, 'assembly', ML, TOP + 0.1, 7.6, 1.2);
  text(s, [
    def(sym('E', 'd', 'BEV'), 'expected annual BEV count of dwelling d in year y (likewise PHEV)'),
    def(sym('Π', 'k,v'), 'hourly profile basis of dwelling class k and drivetrain v'),
    def([{ t: 'P(a | k, v, y, c)', italic: true }], 'archetype probability by class, drivetrain, year and charging scenario'),
    def(sym('h̄', 'a'), 'mean home-charging profile of archetype a from the event library'),
  ], { x: ML, y: TOP + e.h + 0.45, w: 7.6, h: 2.2, paraSpaceAfter: 5 });
  table(s, ['Delivered to the UBEM', 'Resolution'], [
    ['Home charging, expected', 'dwelling, parcel, block group × 8,760 h'],
    ['Home charging, realizations', 'parcel p50 / p90 annual peak'],
    ['Non-residential sites', 'AFDC ports, workplace, fleet parcels × 8,760 h'],
    ['County totals by location', '12 scenarios × 5 anchor years'],
  ], { x: 8.55, y: TOP + 0.1, w: 4.18, colW: [2.0, 2.18], align: ['left', 'left'], fontSize: 13.5 });
  text(s, [{ t: 'Time: local standard time, hour-beginning; energy in kWh per hour. Files and caveats: docs/ubem_interface.md.', color: C.muted }],
    { x: 8.55, y: 4.2, w: 4.18, h: 1.5, fontSize: SZ.small });
  cite(s, 'Model structure [inferred]. Report §5.3; src/model/load_assembly.py, src/model/export_ubem.py.', 6.95);
}

// 22 — 2026 hourly profile
{
  const h = D.hourly['2026_base'];
  const labels = [...Array(24).keys()].map((x) => String(x));
  const s = slide('In 2026 EV charging uses 10.9 GWh a year, with a 4.9 MW county peak on winter weekday evenings',
    'Stacked mean winter (December–February) weekday profile by charging location, ownership trend, charging base. The annual peak hour (late November weekday evening) is higher than this seasonal mean. Home charging is 53 % of energy; fleet depots 16 % (≈ 290 organizational EVs, depot locations unknown).');
  s.addChart(pres.charts.AREA, LOCS.map((k) => ({ name: LOC_LABEL[k], labels, values: h[k] })), chartOpts({
    x: ML, y: TOP, w: 7.5, h: 5.1, barGrouping: 'stacked', chartColors: LOCS.map((k) => C[k]), showLegend: true, legendPos: 'b',
    valAxisLabelFormatCode: '0.0', showValAxisTitle: true, valAxisTitle: 'Mean winter weekday load (MW)', catAxisLabelFrequency: 3,
    showCatAxisTitle: true, catAxisTitle: 'Hour (local standard time)',
  }));
  // source: report §6.1
  table(s, ['Location', 'MWh per year', 'Share'], [
    ['Home (residential meters)', '5,702', '52.5 %'], ['Workplace', '447', '4.1 %'], ['Public Level 2', '831', '7.7 %'],
    ['DC fast, residents', '1,569', '14.5 %'], ['Fleet depots', '1,780', '16.4 %'], ['Passers-by (DC fast)', '523', '4.8 %'],
    [{ text: 'Total', bold: true }, { text: '10,851', bold: true }, ''],
  ], { x: 8.5, y: TOP + 0.1, w: 4.23, colW: [2.2, 1.18, 0.85], fontSize: 15 });
  text(s, ['Annual peak 4.9 MW; residential peak 1.7 MW; load factor 0.25.'], { x: 8.5, y: 4.85, w: 4.23, h: 1.0, fontSize: SZ.small });
  cite(s, 'Model inference, ownership = trend, charging = base [inferred]. data/processed/load/county_hourly_2026_trend_base.parquet; results/tables/load_scenarios_annual.csv.', 6.95);
}

// 23 — home energy map
{
  const s = slide('Home charging per household grows almost fivefold by 2035, and is largest outside the city centre',
    'Expected home EV charging energy per household per year by block group, ownership trend, charging base; common colour scale for both years. Central Ithaca block groups are small and have many renters and multifamily units with lower home access.');
  mapImage(s, 'map_home_kwh_per_hh_2026_2035.png', ML + 0.2, TOP - 0.05, 11.7, 'Maps of home EV charging kWh per household by block group, 2026 and 2035');
  cite(s, 'Model inference [inferred]; data/processed/load/bg_home_hourly_{2026,2035}_trend_base.parquet; ACS-calibrated dwelling units. 2020 block groups, EPSG:32618.', 6.95);
}

// 24 — sites map
{
  const s = slide('Non-residential charging in 2026: 12 DC fast sites carry 2.1 GWh and 90 public Level 2 sites 0.8 GWh',
    'Site energy is allocated from county pools to AFDC ports (public L2 by ports; DC fast including passers-by), workplace energy half to listed workplace stations and half to large non-residential parcels as unlisted chargers (low confidence). Fleet depot energy (1.8 GWh over non-residential parcels) is not mapped because depot locations are unknown.');
  const mw = 9.9;
  const hh = mapImage(s, 'map_sites_2026.png', ML + (CW - mw) / 2, TOP - 0.15, mw, 'Map of 2026 non-residential charging sites sized by annual energy');
  const ty = TOP - 0.15 + hh + 0.05;
  text(s, [
    'DC fast: median 143 kWh/port-day; largest site peak 0.69 MW.   Public Level 2: median 9.6 kWh/port-day.',
    { runs: [{ t: 'Workplace: 0.45 GWh over 8 listed sites and 271 large non-residential parcels.   ' }, { t: 'Fleet depots (1.8 GWh) are not mapped: locations unknown.', color: C.muted }] },
  ], { x: ML, y: ty, w: CW, h: 6.9 - ty, fontSize: 15, paraSpaceAfter: 3 });
  cite(s, 'AFDC station locator, NY ELEC [A]; Charge Ready NY [A/B]; allocation [inferred]. data/processed/load/site_summary_2026_trend_base.csv. EPSG:32618.', 6.95);
}

// 25 — parcel peaks
{
  const P = D.parcel_peaks;
  const s = slide('Parcel peaks grow less than proportionally with EVs: the p90 peak of a 50+-unit parcel is 12 kW in 2026 and 31 kW in 2035',
    'Mean across parcels (with expected EVs > 0) of the 50th and 90th percentile annual peak-hour home charging load over 30 realizations. Most small parcels host no EV in a given realization, so their p50 peak is zero. A single Level 2 EV adds 7.2 kW; a 12-EV garage peaks near 29 kW and a 48-EV garage near 71 kW in the library.');
  s.addChart(pres.charts.BAR, [
    { name: '2026 p90', labels: P.bins, values: P['2026'].p90 }, { name: '2035 p90', labels: P.bins, values: P['2035'].p90 },
    { name: '2026 p50', labels: P.bins, values: P['2026'].p50 }, { name: '2035 p50', labels: P.bins, values: P['2035'].p50 },
  ], chartOpts({
    x: ML, y: TOP, w: 6.8, h: 5.1, barDir: 'col', barGrouping: 'clustered', barGapWidthPct: 50, chartColors: ['9AA3A8', C.accent, 'D0D5D8', C.accentLight],
    showLegend: true, legendPos: 't', valAxisMinVal: 0, showValAxisTitle: true, valAxisTitle: 'Mean annual peak-hour load (kW)',
    showCatAxisTitle: true, catAxisTitle: 'Dwelling units on parcel',
  }));
  const r = (y, i, k, d = 1) => fmt(P[y][k][i], d);
  table(s, ['Units on parcel', 'Parcels', 'EVs 2026', 'p90 kW 2026', 'EVs 2035', 'p90 kW 2035'],
    P.bins.map((b, i) => [b, fmt(P['2026'].parcels[i]), r('2026', i, 'E_ev', 2), r('2026', i, 'p90'), r('2035', i, 'E_ev', 2), i === P.bins.length - 1 ? { text: r('2035', i, 'p90'), bold: true, color: C.accent } : r('2035', i, 'p90')]),
    { x: 7.65, y: TOP + 0.1, w: 5.08, colW: [0.98, 0.78, 0.8, 0.84, 0.8, 0.88], fontSize: 13 });
  text(s, [{ t: 'Use realizations, not expected profiles, for building peak and capacity questions.', bold: true }], { x: 7.65, y: 4.4, w: 5.08, h: 1.0, fontSize: SZ.small });
  cite(s, 'EVs = expected EVs per parcel. Model inference, ownership = trend, charging = base [inferred]. data/processed/load/parcel_summary_{2026,2035}_trend_base.csv.', 6.95);
}

// 26 — load projections
{
  const O = D.scenarios.own;
  const order = [['trend', C.accent], ['policy', C.obs], ['stall', C.grey], ['slow', C.lightGrey]];
  const yrs = O.trend.year;
  const scatter = (key) => [{ name: 'Year', values: yrs }, ...order.map(([k]) => ({ name: k, values: O[k][key] }))];
  const s = slide('County EV load reaches 176 GWh and 84 MW by 2050 under trend adoption; ownership scenarios span 82–213 GWh',
    'Annual energy and annual peak-hour load, charging scenario base, anchor years 2026, 2030, 2035, 2040, 2050. Intermediate years are interpolated only in these charts. Peaks occur on winter weekday evenings (17:00–20:00) in all scenarios.');
  const common = { lineSize: 2.25, lineDataSymbol: 'circle', lineDataSymbolSize: 7, chartColors: order.map((o) => o[1]), showLegend: true, legendPos: 't',
    catAxisMinVal: 2025, catAxisMaxVal: 2051, catAxisMajorUnit: 5, catAxisLabelFormatCode: '0', valAxisMinVal: 0 };
  s.addChart(pres.charts.SCATTER, scatter('gwh'), chartOpts(Object.assign({ x: ML, y: TOP + 0.35, w: 5.9, h: 4.3, showValAxisTitle: true, valAxisTitle: 'Annual charging energy (GWh)' }, common)));
  caption(s, 'Energy', ML, TOP, 5.9);
  s.addChart(pres.charts.SCATTER, scatter('mw'), chartOpts(Object.assign({ x: 6.83, y: TOP + 0.35, w: 5.9, h: 4.3, showValAxisTitle: true, valAxisTitle: 'Annual peak-hour load (MW)' }, common)));
  caption(s, 'Peak', 6.83, TOP, 5.9);
  // source: report §6.2
  cite(s, 'Trend: 22.1 GWh / 10.9 MW (2030), 50.5 / 22.9 (2035), 94.1 / 50.7 (2040), 176.4 / 84.4 (2050). Policy 2050: 213.0 / 101.9; slow 2050: 81.7 / 39.1. Model inference, charging = base [inferred]; results/tables/load_scenarios_annual.csv.', 6.3, { h: 0.7, fontSize: 13 });
}

// 27 — managed charging
{
  const b = D.hourly['2050_base'], m = D.hourly['2050_managed'];
  const tot = (h) => h.home.map((_, i) => LOCS.reduce((a, k) => a + h[k][i], 0));
  const labels = [...Array(24).keys()].map((x) => String(x));
  const s = slide('Managed charging cuts the 2050 county peak by 19 % but creates a later residential peak that is 26 % higher',
    'Mean winter weekday profiles, ownership trend, 2050. Managed charging starts 60 % of home Level 2 sessions at 23:00 plus a uniform 0–2 h stagger. The shifted residential peak exceeds the unmanaged residential peak from 2040: feeder assessments need the staggering window as a design parameter.');
  s.addChart(pres.charts.LINE, [
    { name: 'All locations, base', labels, values: tot(b) }, { name: 'All locations, managed', labels, values: tot(m) },
    { name: 'Home, base', labels, values: b.home }, { name: 'Home, managed', labels, values: m.home },
  ], chartOpts({
    x: ML, y: TOP, w: 7.3, h: 5.15, lineSize: 2.5, lineDataSymbol: 'none', chartColors: [C.obs, C.grey, C.home, C.public_l2],
    showLegend: true, legendPos: 't', valAxisMinVal: 0, showValAxisTitle: true, valAxisTitle: 'Mean winter weekday load, 2050 (MW)',
    catAxisLabelFrequency: 3, showCatAxisTitle: true, catAxisTitle: 'Hour (local standard time)',
  }));
  // source: report §6.2 charging scenario table
  table(s, ['Charging scenario (trend ownership)', '2035 total / home MW', '2050 total / home MW', '2050 DC fast GWh'], [
    ['base', '22.9 / 9.5', '84.4 / 35.5', '26.3'],
    ['access+ (home and workplace access)', '23.1 / 9.4', '82.8 / 37.2', '20.4'],
    [{ text: 'managed (35 % by 2035, 60 % by 2050)', bold: true }, { text: '20.0 / 10.0', bold: true }, { text: '68.1 / 44.7', bold: true, color: C.accent }, '26.0'],
  ], { x: 8.2, y: TOP + 0.1, w: 4.53, colW: [1.75, 0.95, 0.95, 0.88], fontSize: 12.5 });
  text(s, [
    'Values in the table are annual peak hours; the chart shows seasonal means.',
    'Access+ shifts ≈ 6 GWh/yr (2050) from DC fast sites to homes and workplaces with little change in the county peak.',
  ], { x: 8.2, y: 3.85, w: 4.53, h: 2.5, fontSize: SZ.small });
  cite(s, 'Model inference [inferred]; data/processed/load/county_hourly_2050_trend_{base,managed}.parquet; results/tables/load_scenarios_annual.csv.', 6.95);
}

// 28 — infrastructure history
{
  const I = D.infrastructure;
  const yrs = I.public_L2.year.slice();
  const l2 = I.public_L2.ports.slice(), dc = I.public_DCFC.ports.slice();
  const current = { year: 2026.67, l2: 237, dc: 42 }; // source: report §5.6, AFDC current API 2026-09 (DC fast: all access)
  if (Math.max(...yrs) < 2026) {
    for (let y = Math.max(...yrs) + 1; y <= 2025; y++) { yrs.push(y); l2.push(null); dc.push(null); } // not observed: draw a gap
    yrs.push(current.year); l2.push(current.l2); dc.push(current.dc);
  }
  const s = slide('Public charging ports have grown with the EV stock, at 11–15 EVs per public port since 2017',
    'AFDC station records as published on past dates (NLR historical-date endpoint), Tompkins County by point-in-polygon, open stations. The open-date curve of surviving stations understates history (2018 public L2: 3 vs 39 ports) because 75–92 % of 2014–2017 public records were retired or re-keyed. AFDC changed its counting method (OCPI) in 2021.');
  s.addChart(pres.charts.SCATTER, [{ name: 'Year', values: yrs }, { name: 'Public Level 2 ports', values: l2 }, { name: 'DC fast ports', values: dc }], chartOpts({
    x: ML, y: TOP, w: 7.4, h: 5.1, lineSize: 2.25, lineDataSymbol: 'circle', lineDataSymbolSize: 7, chartColors: [C.public_l2, C.dcfc], showLegend: true, legendPos: 't',
    catAxisMinVal: 2013, catAxisMaxVal: 2027, catAxisMajorUnit: 2, catAxisLabelFormatCode: '0', valAxisMinVal: 0, displayBlanksAs: 'gap',
    showValAxisTitle: true, valAxisTitle: 'Ports in Tompkins County', showCatAxisTitle: true, catAxisTitle: 'Year end (last point: September 2026)',
  }));
  const ep = I.evs_per_public_port;
  table(s, ['Year end', 'EVs per public port'], ep.date.map((d, i) => [d.slice(0, 4), fmt(ep.value[i], 1)]).concat([['2026-09', '≈ 11.7']]),
    { x: 8.6, y: TOP + 0.1, w: 4.13, colW: [2.0, 2.13], fontSize: 15 });
  text(s, ['Public Level 2 ports grew 43 % a year over 2014–2020.', { t: 'Supports the projection rule that ports scale with the EV stock.', color: C.muted }],
    { x: 8.6, y: 4.3, w: 4.13, h: 1.8, fontSize: SZ.small });
  cite(s, 'AFDC historical station records via developer.nlr.gov v0/historical-date (DEMO_KEY) and current station locator API [A]; EValuateNY stock [D]. results/tables/infrastructure_*.csv.', 6.95);
}

// 29 — uncertainty decomposition (when available)
if (D.optional && D.optional.uncertainty_decomposition_county && D.optional.uncertainty_decomposition_bg && D.optional.uncertainty_decomposition_parcel) {
  const all = [...D.optional.uncertainty_decomposition_county, ...D.optional.uncertainty_decomposition_bg, ...D.optional.uncertainty_decomposition_parcel]
    .filter((r) => r.index === 'first_order');
  const FACT = [['stock', 'How many EVs (stock)', C.accent], ['placement', 'Where they are (placement)', '8C6D1F'],
    ['behaviour', 'How they charge (behaviour)', '9AA3A8'], ['interaction', 'Interactions', 'DDE1E4']];
  const ROWS = [
    ['County · annual energy', (r) => r.scale === 'county' && r.metric === 'annual_mwh_home'],
    ['County · peak hour', (r) => r.scale === 'county' && r.metric === 'peak_kw_home'],
    ['Block group (median) · annual energy', (r) => r.scale === 'block_group' && r.entity === 'median over BGs' && r.metric === 'annual_mwh_home'],
    ['Block group (median) · peak hour', (r) => r.scale === 'block_group' && r.entity === 'median over BGs' && r.metric === 'peak_kw_home'],
    ['Parcel, 20+ units · peak hour', (r) => r.scale === 'parcel' && String(r.entity).startsWith('20+')],
    ['Parcel, 5–19 units · peak hour', (r) => r.scale === 'parcel' && String(r.entity).startsWith('5-19')],
    ['Parcel, 2–4 units · peak hour', (r) => r.scale === 'parcel' && String(r.entity).startsWith('2-4')],
    ['Parcel, 1 unit · peak hour', (r) => r.scale === 'parcel' && String(r.entity).startsWith('1 ')],
  ];
  const share = (year, pred, f) => { const r = all.find((x) => x.year === year && pred(x) && x.factor === f); return r ? Math.max(0, Number(r.variance_share)) * 100 : 0; };
  const labels = ROWS.map((r) => r[0]).reverse();
  const s = slide('County load uncertainty comes from behaviour parameters today and stock growth by 2035; placement dominates parcel peaks',
    'First-order variance shares (bias-corrected functional ANOVA on a fully crossed Monte Carlo design; ownership trend, charging base; home charging). Stock is observed in 2026, so its share is zero by construction. Placement = weighting choice plus sampling of which dwellings own EVs; behaviour = parameter uncertainty plus stochastic archetype and EV-year choice. Interactions are large for parcel peaks because an EV must be placed on a parcel before its charging behaviour matters. Small negative estimates (Monte Carlo noise) are shown as zero. Bootstrap 95 % intervals and factor ranges: results/tables/uncertainty_decomposition_*.csv, uncertainty_factor_ranges.csv.');
  // shared legend (one for both panels): colour key squares with labels
  let lx = ML;
  FACT.forEach(([, name, col]) => {
    s.addShape(pres.shapes.RECTANGLE, { x: lx, y: TOP + 0.07, w: 0.18, h: 0.18, fill: { color: col }, line: { color: col, width: 0.5 } });
    s.addText(name, { x: lx + 0.25, y: TOP, w: 2.75, h: 0.32, fontFace: F, fontSize: SZ.label, color: C.text, margin: 0, valign: 'middle', isTextBox: true });
    lx += 3.0;
  });
  const chart = (year, x) => {
    s.addChart(pres.charts.BAR, FACT.map(([f, name]) => ({ name, labels, values: ROWS.map((r) => share(year, r[1], f)).reverse() })), chartOpts({
      x, y: TOP + 0.8, w: 5.95, h: 4.45, barDir: 'bar', barGrouping: 'stacked', barGapWidthPct: 40, chartColors: FACT.map((f) => f[2]),
      showLegend: false, valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 25, showValAxisTitle: true, valAxisTitle: 'Share of variance (%)',
      catAxisLabelFontSize: 12,
    }));
    s.addText(String(year), { x, y: TOP + 0.45, w: 5.95, h: 0.35, fontFace: F, fontSize: 16, bold: true, color: C.text, margin: 0, isTextBox: true });
  };
  chart(2026, ML);
  chart(2035, ML + 6.15);
  cite(s, 'Model inference [inferred]; src/analysis/uncertainty_decomposition.py; results/tables/uncertainty_decomposition_{county,bg,parcel}.csv (bootstrap 95 % intervals, seed-stability repeat).', 6.95);
}

// 30 — in-commuter charging (when available)
if (D.optional && D.optional.incommuter_charging_estimate && D.optional.incommuter_flows_by_origin) {
  const est = D.optional.incommuter_charging_estimate;
  const flows = D.optional.incommuter_flows_by_origin.filter((r) => r.origin !== 36109 && r.within_100km === true)
    .sort((a, b) => b.jobs_JT01 - a.jobs_JT01).slice(0, 8);
  const share = Math.round(est[0].incommuter_share_of_tompkins_jobs * 100);
  const s = slide(`In-commuters hold ${share} % of Tompkins jobs but add only about 33 MWh of charging; residents charging at jobs elsewhere offset more`,
    'Jobs from LEHD LODES 2023 (primary jobs, origins within 100 km). In-commuter EVs = jobs × cars per job (ACS commute mode) × origin-county passenger EV share (DMV 2026); workplace and public top-up energy use the resident parameters and charging library. The offset removes charging that the resident model places in Tompkins although about 22 % of resident EV owners work outside the county. Low/central/high are bounding cases, not probability intervals. Not applied to load tables.');
  const labels = flows.map((r) => r.name.replace(' County', '')).reverse();
  s.addChart(pres.charts.BAR, [{ name: 'Primary jobs in Tompkins', labels, values: flows.map((r) => r.jobs_JT01).reverse() }], chartOpts({
    x: ML, y: TOP + 0.35, w: 4.9, h: 4.7, barDir: 'bar', barGapWidthPct: 45, chartColors: [C.work], showValue: true, dataLabelFormatCode: '#,##0', dataLabelPosition: 'outEnd',
    valAxisMinVal: 0, valAxisMaxVal: 3500, valAxisMajorUnit: 1000, valAxisLabelFormatCode: '#,##0', showValAxisTitle: true, valAxisTitle: 'Primary jobs held in Tompkins, 2023', catAxisLabelFontSize: 13,
  }));
  caption(s, 'Largest origin counties within 100 km', ML, TOP, 4.9);
  const g = (y, c) => est.find((r) => r.year === y && r.case === c);
  const row = (label, key, d = 0) => [label, ...['low', 'central', 'high'].map((c) => fmt(g(2026, c)[key], d)), ...['low', 'central', 'high'].map((c) => fmt(g(2035, c)[key], d))];
  const offset = (y, c) => g(y, c).outcommuter_workplace_offset_mwh + g(y, c).outcommuter_public_offset_mwh;
  table(s, ['MWh per year', '2026 low', 'central', 'high', '2035 low', 'central', 'high'], [
    row('In-commuter EVs', 'incommuter_evs'),
    row('Workplace charging', 'workplace_mwh'),
    row('Public top-up', 'public_topup_mwh'),
    row('Gross addition', 'gross_mwh').map((t, i) => (i ? { text: t, bold: true } : { text: t, bold: true })),
    ['Offset: residents charging outside', ...['low', 'central', 'high'].map((c) => fmt(-offset(2026, c))), ...['low', 'central', 'high'].map((c) => fmt(-offset(2035, c)))],
    row('Net, workplace only', 'net_workplace_mwh'),
    row('Net, all', 'net_mwh').map((t, i) => ({ text: t, bold: true, color: i === 2 ? C.accent : C.text })),
  ], { x: 5.9, y: TOP + 0.35, w: 6.83, colW: [2.33, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75], fontSize: 13.5 });
  text(s, [
    'Central 2026 gross addition: 0.3 % of county charging (10,851 MWh); in-commuter origin counties have EV shares of 1.1–2.6 % against 5.6 % in Tompkins.',
    'Cornell central campus holds 14 % of in-commuter workplace charging; 7 block groups hold half.',
    { t: 'Smaller than the uncertainty in DC fast and fleet pools; recorded, not applied.', color: C.muted },
  ], { x: 5.9, y: 4.95, w: 6.83, h: 1.9, fontSize: 15, paraSpaceAfter: 5 });
  cite(s, 'US Census LEHD LODES8 NY 2023 origin–destination [A, noise-infused]; ACS commute mode [A/B]; DMV 2026 county EV shares [B]; charging library [inferred]. results/tables/incommuter_*.csv.', 6.95);
}

// 31 — validated vs not
{
  const s = slide('What public data can observe, validate, only benchmark, or not test at all',
    'The main unvalidated quantities for building-level load: within-ZIP placement (multifamily and renter share), home charging power and timing in upstate homes, DC fast and workplace energy shares, fleet depot locations, post-2030 adoption, managed-charging design, students and group-quarters vehicles.');
  const st = (t, c) => ({ text: t, bold: true, color: c });
  // source: report §7
  table(s, ['Component', 'Evidence', 'Status'], [
    ['County and ZIP EV stock 2026', 'Direct DMV observation; two geographic definitions within 3.5 %', st('observed', C.accent)],
    ['Synthetic dwelling units', 'ACS block-group marginals, R² ≥ 0.99', st('validated (composition)', C.accent)],
    ['Placement between ZIPs', 'NY county-grouped CV (≈ 0.78 deviance explained), cross-year allocation test', st('validated between areas', C.accent)],
    ['Placement below ZIP (building, parcel)', 'None possible; ensemble spread 9–31 % multifamily share', st('unvalidated, bounded', C.dcfc)],
    ['Stock growth', 'Backcast: NY +3 % / +27 %; Tompkins +21 % / +90 %', st('weak for extrapolation', C.muted)],
    ['Charging shapes', 'NYSERDA 22-03 weekday shapes, r = 0.88–0.97', st('validated (shape)', C.accent)],
    ['Charging energy magnitude', 'Survey kWh per EV (−5 %); ChargePoint utilisation range', st('consistent', C.accent)],
    ['Upstate home timing, Level 1 use, DC fast share', 'No public local data', st('unvalidated', C.dcfc)],
    ['County hourly magnitude', 'NREL TEMPO only (model, 2.2× higher)', st('benchmark only', C.muted)],
    ['2030–2050 load', 'Scenario-conditional', st('not validatable', C.muted)],
  ], { x: ML, y: TOP, w: CW, colW: [3.7, 5.9, 2.5], align: ['left', 'left', 'left'], fontSize: 15 });
  cite(s, 'Full matrix: docs/validation_matrix.md. Report §7–§8.', 6.95);
}

// 32 — synthesis and decisions
{
  const s = slide('The model runs end to end; the next stage depends on how the building energy model will use it',
    'Decisions requested from the UBEM team and project lead. Work that does not depend on them continues in the repository (see docs/HANDOFF.md).');
  const colw = (CW - 0.6) / 2;
  text(s, [
    { t: 'Decisions needed', bold: true },
    { t: 'How is EV load used: building meter totals, zone internal gains, or grid-side aggregation only?', bullet: true },
    { t: 'Is a 9–31 % placement range acceptable if delivered as many realizations, or should non-public data (utility EV rates, Cornell parking, municipal permits) be pursued?', bullet: true },
    { t: 'Should long-range scenarios be tied to named policies (New York zero-emission vehicle sales rule, state climate plan) rather than fitted trends?', bullet: true },
  ], { x: ML, y: TOP, w: colw, h: 5.2, paraSpaceAfter: 10 });
  const haveUnc = !!(D.optional && D.optional.uncertainty_decomposition_county);
  const haveInc = !!(D.optional && D.optional.incommuter_charging_estimate);
  text(s, [
    { t: 'Completed since the report', bold: true },
    ...(haveInc ? [{ t: 'In-commuter and out-commuter charging from LEHD flows: net correction −79 MWh/yr (workplace), not applied', bullet: true }] : []),
    ...(haveUnc ? [{ t: 'Variance decomposition of load uncertainty by source and scale (earlier slide)', bullet: true }] : []),
    { t: 'Next, regardless of the decisions', bold: true },
    ...(haveUnc ? [] : [{ t: 'Variance decomposition of load uncertainty by source (stock, placement, behaviour) and scale', bullet: true }]),
    ...(haveInc ? [] : [{ t: 'In-commuter workplace charging from LEHD commuting flows', bullet: true }]),
    { t: 'AFDC charging history 2021–2025 and siting scenarios for new DC fast sites', bullet: true },
    { t: 'Sensitivity runs: home Level 2 power and managed-charging stagger width', bullet: true },
    { t: 'End-to-end test of the export format against building footprints and RC zones', bullet: true },
  ], { x: ML + colw + 0.6, y: TOP, w: colw, h: 5.2, paraSpaceAfter: 10 });
  cite(s, 'Repository: README.md, docs/report_20260914_ev_model.md, docs/HANDOFF.md.', 6.95);
}

pres.writeFile({ fileName: OUT }).then((f) => console.log('wrote', f));
