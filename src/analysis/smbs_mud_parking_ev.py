"""Multifamily (5+ unit) EV ownership, parking and EV-charging access in New York: NYSERDA SMBS 2022.

Evidence class B (New York observation; self-report surveys + field site visits, 2022-2023).

Inputs (from `python -m src.acquisition.nyserda_smbs`, data/raw/nyserda_smbs/):
  smbs2022_general_survey.parquet   gfhm-wz4s  building-representative survey, 1,366 rows (1 row = 1 building)
  smbs2022_occupant_survey.parquet  gjv3-iq86  occupant survey, 156 rows (1 row = 1 household)
  smbs2022_site_visits.xlsx         qwyr-7esw  field data, 434 buildings / 639 dwelling units

What the SMBS does and does NOT contain (verified against the data dictionaries):
  * EV ownership: occupant G15 "How many electric vehicles are owned or leased ..." (None / One / Three or more
    observed). BEV vs PHEV is NOT distinguished. There is NO question on total (any-fuel) vehicle ownership.
  * Parking: general-survey E14 (amenities incl. "Parking areas", "Electric vehicle charging stations"),
    E15 parking type + spaces, E16 % assigned; site-visit parking_type / parking_spaces / ev_plugin / L1-L3 counts;
    dwelling-unit dwlg_parking_spots / dwlg_parking_type.
  * EV charging: E14 option, E17 station counts by level, E18 tenant fee; occupant G16 (where charge), G17 (pay).
  * Electrical capacity: site-visit dwelling-unit panel volts/amps and building service equipment volts/amps.
  * Geography: no county/ZIP. Electric utility (general survey strata4, site-visit electricity_provider,
    occupant IOU) and, for a minority of occupant rows, climate zone. Tompkins County = NYSEG territory,
    SMBS Climate Zone 6 (appendix Table 4).

Weights. The public files carry no weight variable (Appendix B says site weights exist in the study datasets,
but they are not in the open-data release). We therefore construct approximate post-stratification weights by
raking each file to published building-population margins (122,604 MF buildings statewide):
  building size (Appendix B Table 11), ownership type (Table 10), and electric-utility group derived as
  sum_cz(population_cz [Table 12] x weighted utility share within cz [Appendix A Table 66]).
Weights are trimmed at 5x the mean inside the raking loop. They are building weights; household (occupant) and
dwelling-unit (panel) estimates reuse the building weight of the respondent's building (divided among the sampled
units of a building). This is NOT the Cadmus weighting (which also used vintage/DAC strata and per-metric
non-response factors), so weighted numbers will differ from the published Appendix A tables.

Uncertainty. For every proportion we report (i) unweighted k/n with a Wilson 95% interval and (ii) the raked
weighted estimate with a 95% percentile bootstrap interval (1,000 respondent resamples within the domain, weights
held fixed; no design-effect/raking variance; collapses to a point when k = 0 or k = n) and Kish effective n.

Outputs
  results/tables/smbs_occupant_ev_ownership.csv      (a) share of MF households with >=1 EV by segment
  results/tables/smbs_building_parking_ev.csv        (b)(c) building-level parking / EV-charging indicators
  results/tables/smbs_du_electrical_capacity.csv     dwelling-unit panel amps / volts (site visits)
  results/tables/smbs_parking_spaces_per_unit.csv    reported spaces per dwelling unit
  results/tables/smbs_building_ev_charger_ports.csv  ports by level in buildings reporting EV charging
  results/tables/smbs_distributions.csv              (d) categorical distributions (assigned parking, EV fees, ...)
  results/tables/smbs_published_benchmarks.csv       transcribed Cadmus weighted results (Appendix A) for comparison
  results/tables/smbs_variable_inventory.csv         relevant variables, universes and non-missing counts
  results/tables/smbs_weights_summary.csv            raking targets vs achieved sample
  data/processed/smbs/mf_ev_parameters.csv           model-ready parameters
  results/figures/smbs_parking_ev_charging_by_region.png
  results/figures/smbs_du_panel_amps_by_region.png
  results/figures/smbs_occupant_ev_ownership.png
"""
from __future__ import annotations

import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.utils.paths import FIGURES, PROCESSED, RAW, TABLES, ensure  # noqa: E402

SRC = RAW / "nyserda_smbs"
OUT_PROC = PROCESSED / "smbs"
RNG = np.random.default_rng(20260914)
REPS = 1000

GEN_ID, OCC_ID, SV_ID = "gfhm-wz4s", "gjv3-iq86", "qwyr-7esw"

# ---------------------------------------------------------------- population margins (Appendix B / A)
POP_TOTAL = 122_604
POP_SIZE = {"1-3 floors": 60_659, "4-7 floors": 53_032, "8+ floors": 8_913}  # App. B Table 11
POP_OWN = {"Affordable subsidized": 9_990, "Affordable census block/NOAH": 41_589,  # App. B Table 10
           "Co-op/condo": 15_283, "Market-rate rental": 55_742}
POP_CZ = {"NYC": 75_590, "CZ4 (LI+Westchester)": 11_186, "CZ5": 27_206, "CZ6": 8_622}  # App. B Table 12
# App. A Table 66: weighted % of buildings by electric utility within climate zone (building-rep survey)
UTIL_SHARE_BY_CZ = {
    "NYC": {"CenHud+O&R": 2, "ConEd": 94, "PSEG-LI": 4, "Other": 0.2},
    "CZ4 (LI+Westchester)": {"ConEd": 19, "NYSEG+RG&E": 9, "PSEG-LI": 63, "Other": 9},
    "CZ5": {"CenHud+O&R": 19 + 10, "NationalGrid": 43, "NYSEG+RG&E": 13 + 14},
    "CZ6": {"CenHud+O&R": 16 + 0.5, "NationalGrid": 22, "NYSEG+RG&E": 61},
}
REGIONS = ["ConEd", "PSEG-LI", "CenHud+O&R", "NationalGrid", "NYSEG+RG&E"]
UPSTATE = "Upstate (NationalGrid+NYSEG+RG&E)"
REGION_NOTE = ("ConEd = NYC + Westchester; PSEG-LI = Long Island; CenHud+O&R = mid/lower Hudson Valley; "
               "NationalGrid = Central/Northern/Western NY incl. Syracuse, Albany, Buffalo; "
               "NYSEG+RG&E = Southern Tier/Finger Lakes/Rochester incl. Tompkins County")


def util_targets() -> dict:
    t: dict[str, float] = {}
    for cz, shares in UTIL_SHARE_BY_CZ.items():
        tot = sum(shares.values())
        for u, s in shares.items():
            t[u] = t.get(u, 0) + POP_CZ[cz] * s / tot
    t.pop("Other")
    k = POP_TOTAL / sum(t.values())
    return {u: v * k for u, v in t.items()}


POP_UTIL = util_targets()

# ---------------------------------------------------------------- style (dataviz reference palette)
SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE = "#2a78d6"
ORDINAL_BLUE = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "font.size": 9, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": MUTED,
    "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.spines.top": False, "axes.spines.right": False, "text.color": INK,
})


# ---------------------------------------------------------------- helpers
def num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return np.nan, np.nan
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def rake(df: pd.DataFrame, margins: dict[str, dict], iters: int = 200, trim: float = 5.0) -> pd.Series:
    ok = np.ones(len(df), bool)
    for col, tgt in margins.items():
        ok &= df[col].isin(list(tgt)).to_numpy()
    sub = df.loc[ok]
    w = pd.Series(1.0, index=sub.index)
    tg = {}
    for col, tgt in margins.items():  # drop target levels absent from the sample, rescale to POP_TOTAL
        present = {k: v for k, v in tgt.items() if (sub[col] == k).any()}
        s = POP_TOTAL / sum(present.values())
        tg[col] = {k: v * s for k, v in present.items()}
    for _ in range(iters):
        for col, tgt in tg.items():
            cur = w.groupby(sub[col]).sum()
            w = w * sub[col].map(pd.Series(tgt) / cur).astype(float)
        if trim:
            w = w.clip(upper=trim * w.mean())
    w = w * POP_TOTAL / w.sum()
    out = pd.Series(np.nan, index=df.index)
    out.loc[sub.index] = w
    return out


def weights_summary(name: str, df: pd.DataFrame, margins: dict[str, dict]) -> list[dict]:
    rows = []
    d = df[df["w"].notna()]
    for col, tgt in margins.items():
        for lvl, pop in tgt.items():
            m = d[col] == lvl
            rows.append({"dataset": name, "margin": col, "level": lvl, "population_target": round(pop),
                         "n_sample_weighted_rows": int(m.sum()), "n_sample_all_rows": int((df[col] == lvl).sum()),
                         "weighted_total": round(float(d.loc[m, "w"].sum())),
                         "mean_weight": round(float(d.loc[m, "w"].mean()), 1) if m.any() else np.nan})
    rows.append({"dataset": name, "margin": "ALL", "level": "rows_with_weight", "population_target": POP_TOTAL,
                 "n_sample_weighted_rows": len(d), "n_sample_all_rows": len(df),
                 "weighted_total": round(float(d["w"].sum())),
                 "mean_weight": round(float(d["w"].max() / d["w"].min()), 1)})  # max/min ratio in last col
    return rows


def est(d: pd.DataFrame, flag: str, w: str = "w", units: str | None = None) -> dict:
    d = d[d[flag].notna()]
    n = len(d)
    k = int(d[flag].sum()) if n else 0
    lo, hi = wilson(k, n)
    r = {"n": n, "k": k, "share_unweighted": k / n if n else np.nan, "wilson95_lo": lo, "wilson95_hi": hi}
    dw = d[d[w].notna()]
    nw = len(dw)
    r["n_weighted"] = nw
    if nw:
        x = dw[flag].to_numpy(float)
        ww = dw[w].to_numpy(float)
        r["share_weighted"] = float(np.average(x, weights=ww))
        idx = RNG.integers(0, nw, (REPS, nw))
        bw = ww[idx]
        vals = (x[idx] * bw).sum(1) / bw.sum(1)
        r["boot95_lo"], r["boot95_hi"] = np.percentile(vals, [2.5, 97.5])
        r["kish_n_eff"] = float(ww.sum() ** 2 / (ww ** 2).sum())
        if units:
            uu = dw[units].to_numpy(float)
            wu = np.where(np.isnan(uu), 0.0, ww * np.nan_to_num(uu))
            if wu.sum() > 0:
                r["share_weighted_by_units"] = float(np.average(x, weights=wu))
                bu = wu[idx]
                vu = (x[idx] * bu).sum(1) / np.where(bu.sum(1) > 0, bu.sum(1), np.nan)
                r["boot95_units_lo"], r["boot95_units_hi"] = np.nanpercentile(vu, [2.5, 97.5])
    else:
        r.update(share_weighted=np.nan, boot95_lo=np.nan, boot95_hi=np.nan, kish_n_eff=np.nan)
    return r


def domains(d: pd.DataFrame, dims: list[str]) -> list[tuple[str, str, pd.DataFrame]]:
    out = [("statewide", "all", d)]
    for dim in dims:
        vals = d[dim].dropna().unique()
        order = REGIONS if dim == "region" else sorted(vals, key=str)
        for v in order:
            if v in vals:
                out.append((dim, v, d[d[dim] == v]))
        if dim == "region":
            out.append((dim, UPSTATE, d[d[dim].isin(["NationalGrid", "NYSEG+RG&E"])]))
    return out


def dist(d: pd.DataFrame, col: str, source: str, universe: str, domain: str = "statewide",
         w: str = "w") -> list[dict]:
    d = d[d[col].notna()]
    n = len(d)
    dw = d[d[w].notna()]
    rows = []
    for cat, cnt in d[col].value_counts().items():
        rows.append({"source": source, "variable": col, "universe": universe, "domain": domain,
                     "category": cat, "n": n, "count": int(cnt), "share_unweighted": cnt / n,
                     "share_weighted": float(dw.loc[dw[col] == cat, w].sum() / dw[w].sum()) if len(dw) else np.nan,
                     "n_weighted": len(dw)})
    return rows


def vintage_from_year(y: pd.Series) -> pd.Series:
    return pd.cut(y, [0, 1939, 1978, 2006, 3000], labels=["pre-1940", "1940-1978", "1979-2006", "2007+"]).astype(object)


def size_from_floors(f: pd.Series) -> pd.Series:
    return pd.cut(f, [0, 3, 7, 1000], labels=list(POP_SIZE)).astype(object)


# ---------------------------------------------------------------- general survey (buildings)
def load_general() -> pd.DataFrame:
    g = pd.read_parquet(SRC / "smbs2022_general_survey.parquet")
    g["size"] = size_from_floors(num(g["strata1"]))
    g["own"] = g["strata3"].map({
        "Market-rate rentals (no subsidies)": "Market-rate rental",
        "Subsidized affordable housing rentals (applies to 25% or more of units)": "Affordable subsidized",
        "Naturally occurring affordable rentals (rents are low/affordable without subsidies)": "Affordable census block/NOAH",
        "Co-op or condos": "Co-op/condo"})
    g["region"] = g["strata4"].map({
        "ConEdison": "ConEd", "PSEG Long Island": "PSEG-LI", "Central Hudson": "CenHud+O&R",
        "Orange and Rockland": "CenHud+O&R", "National Grid": "NationalGrid",
        "New York State Electric and Gas Corporation (NYSEG)": "NYSEG+RG&E",
        "Rochester Gas and Electric (RG&E)": "NYSEG+RG&E"})
    g["units"] = num(g["e3"])
    g["units_class"] = pd.cut(g["units"], [4, 9, 19, 49, 99, 1e9],
                              labels=["5-9", "10-19", "20-49", "50-99", "100+"]).astype(object)
    yr = num(g["e9_1_text"])
    g["vintage"] = vintage_from_year(yr.where(yr.between(1700, 2025)))
    g["vintage"] = g["vintage"].fillna(g["e10"].map({"Before 1940": "pre-1940", "1940 to 1978": "1940-1978",
                                                     "1979 to 2006": "1979-2006", "Or after 2006": "2007+"}))
    e14, e15 = g["e14"].fillna(""), g["e15"].fillna("")
    park = e14.str.contains("Parking areas")
    c_ug, c_ag, c_lot = num(g["e15_1_text"]), num(g["e15_2_text"]), num(g["e15_3_text"])
    # a selected option with an explicit 0 spaces is treated as not present
    ug = e15.str.contains("Underground") & ~(c_ug == 0)
    ag = e15.str.contains("Above-ground") & ~(c_ag == 0)
    lot = e15.str.contains("Open parking lot") & ~(c_lot == 0)
    street = e15.eq("Street parking only")
    g["park_any_amenity"] = park.astype(float)
    g["park_offstreet"] = (park & ~street & (ug | ag | lot)).astype(float)
    g["park_garage"] = (park & (ug | ag)).astype(float)
    g["park_open_lot"] = (park & lot).astype(float)
    g["park_street_only"] = street.astype(float)
    g["ev_charging"] = e14.str.contains("Electric vehicle charging").astype(float)
    # spaces: only if every selected off-street type has a count
    sel = pd.concat([e15.str.contains("Underground"), e15.str.contains("Above-ground"),
                     e15.str.contains("Open parking lot")], axis=1).to_numpy()
    cnt = pd.concat([c_ug, c_ag, c_lot], axis=1).to_numpy()
    complete = ~(sel & np.isnan(cnt)).any(axis=1) & sel.any(axis=1)
    g["spaces"] = np.where(complete, np.nansum(np.where(sel, cnt, 0), axis=1), np.nan)
    g.loc[g["park_offstreet"] != 1, "spaces"] = np.nan
    g["spaces_per_unit"] = g["spaces"] / g["units"]
    g["w"] = rake(g, {"size": POP_SIZE, "own": POP_OWN, "region": POP_UTIL})
    return g


# ---------------------------------------------------------------- occupant survey (households)
def income_band(s: str | float) -> str | float:
    if not isinstance(s, str):
        return np.nan
    s = s.replace("â€“", "–")
    if "Prefer" in s:
        return "refused"
    if s.startswith("Less than"):
        return "<$35k"
    m = re.search(r"\$([\d,]+)", s)
    v = int(m.group(1).replace(",", ""))
    return "<$35k" if v < 35_000 else "$35-75k" if v < 75_000 else "$75-150k" if v < 150_000 else "$150k+"


def load_occupant() -> pd.DataFrame:
    o = pd.read_parquet(SRC / "smbs2022_occupant_survey.parquet")
    g15 = o["g15"].str.strip("()")
    o["ev_any"] = g15.isin(["One", "Two", "Three or more"]).astype(float).where(o["g15"].notna())
    o["ev_count_lb"] = g15.map({"None": 0, "One": 1, "Two": 2, "Three or more": 3})
    o["size"] = o["building_size"].str.lower().map({"1-3 stories": "1-3 floors", "4-7 stories": "4-7 floors",
                                                   "8+ stories": "8+ floors"})
    o["own"] = o["ownership_type"].map({"Market-Rate": "Market-rate rental", "Affordable Subsidized":
                                        "Affordable subsidized", "Affordable Unsubsidized":
                                        "Affordable census block/NOAH", "Co_Ops and Condos": "Co-op/condo"})
    o["region"] = o["iou"].map({"Consolidated Edison": "ConEd", "PSEG Long Island": "PSEG-LI",
                                "Central Hudson Gas and Electric": "CenHud+O&R",
                                "Orange and Rockland Utilities": "CenHud+O&R", "National Grid": "NationalGrid",
                                "NYSEG & RGE": "NYSEG+RG&E"})
    t = o["g5"].str.strip("()")
    o["tenure"] = np.where(t.str.startswith("Own"), "own", np.where(t.isin(["Rent", "Sublet"]), "rent", "other"))
    o["income"] = o["g3"].map(income_band)
    o["rent_assist"] = o["g6"]
    o["climate_zone"] = o["climate_zone"]
    o["w"] = rake(o, {"size": POP_SIZE, "own": POP_OWN, "region": POP_UTIL})
    return o


# ---------------------------------------------------------------- site visits (buildings, dwelling units)
def load_sites() -> tuple[pd.DataFrame, pd.DataFrame]:
    x = pd.ExcelFile(SRC / "smbs2022_site_visits.xlsx")
    gi = x.parse("building_information4_05_15_4")
    b = pd.DataFrame({"facility_id": gi["facility_id"], "ark_site_id": gi["ark_site_id"]})
    b["size"] = size_from_floors(num(gi["building_stories_above_grade"]))
    b["own"] = gi["building_ownership_type"].map({
        "Market rate rental": "Market-rate rental", "Subsidized affordable housing": "Affordable subsidized",
        "Naturally occuring affordable housing": "Affordable census block/NOAH", "Co-ops": "Co-op/condo",
        "Condominiums": "Co-op/condo"})
    b["region"] = gi["electricity_provider"].map({
        "Consolidated Edison": "ConEd", "PSEG Long Island": "PSEG-LI",
        "Central Hudson Gas & Electric Corporation": "CenHud+O&R", "Orange & Rockland": "CenHud+O&R",
        "National Grid": "NationalGrid", "New York State Electric and Gas": "NYSEG+RG&E",
        "Rochester Gas & Electric": "NYSEG+RG&E"})
    yr = num(gi["year_constructed"])
    b["vintage"] = vintage_from_year(yr.where(yr.between(1700, 2025)))
    p = x.parse("building_information4_05_15")
    agg = p.groupby("facility_id").agg(
        types=("parking_type", lambda s: set(s.dropna())),
        ev_plugin=("ev_plugin", lambda s: float((num(s) == 1).any())),
        ev_plugin_recorded=("ev_plugin", lambda s: float(s.notna().any())),
        l1=("ev_charging_stations_l1", lambda s: num(s).sum()),
        l2=("ev_charging_stations_l2", lambda s: num(s).sum()),
        l3=("ev_charging_stations_l3", lambda s: num(s).sum()),
        spaces=("parking_spaces", lambda s: num(s).sum(min_count=1)))
    b = b.join(agg, on="facility_id")
    t = b["types"].apply(lambda s: s if isinstance(s, set) else set())
    b["sv_onsite_parking"] = t.apply(len).gt(0).astype(float)
    b["sv_open_lot"] = t.apply(lambda s: "Open lot" in s).astype(float)
    b["sv_covered_lot"] = t.apply(lambda s: "Covered lot" in s).astype(float)
    b["sv_garage"] = t.apply(lambda s: bool(s & {"Underground parking garage", "Above ground parking garage"})).astype(float)
    b["sv_ev_plugin"] = b["ev_plugin"].fillna(0.0)
    b["sv_parking_class"] = t.apply(lambda s: "none recorded" if not s else "garage (any)" if
                                    s & {"Underground parking garage", "Above ground parking garage"} else
                                    "covered/open lot" if s & {"Open lot", "Covered lot"} else "other")
    es = x.parse("electric_service_bui4_05_15")
    ev = es.assign(v=es["elec_service_equip_volts"].astype(str)).groupby("facility_id")["v"].apply(set)
    b = b.join(ev.rename("svc_volts"), on="facility_id")
    known = b["svc_volts"].apply(lambda s: isinstance(s, set) and bool(s & {"208", "240", "480", ">480"}))
    b["svc_has_208V"] = b["svc_volts"].apply(lambda s: float("208" in s) if isinstance(s, set) else np.nan).where(known)
    b["w"] = rake(b, {"size": POP_SIZE, "own": POP_OWN, "region": POP_UTIL})

    pa = x.parse("unit_information_uni4_05_15_4")
    u = pa[["ark_site_id", "facility_id", "dwlg_panel_volts", "dwlg_panel_amps", "dwlg_panel_amps_other"]].copy()
    u["amps"] = num(u["dwlg_panel_amps"]).fillna(num(u["dwlg_panel_amps_other"]))
    u["volts"] = u["dwlg_panel_volts"].astype(str).str.replace("V", "", regex=False).replace({"nan": np.nan})
    u = u.merge(b[["ark_site_id", "size", "own", "region", "vintage", "w"]], on="ark_site_id", how="left")
    u["w_unit"] = u["w"] / u.groupby("ark_site_id")["ark_site_id"].transform("size")
    a = u["amps"]
    for name, cond in {"panel_le60A": a <= 60, "panel_ge100A": a >= 100, "panel_ge125A": a >= 125,
                       "panel_ge200A": a >= 200}.items():
        u[name] = cond.astype(float).where(a.notna())
    u["panel_208V"] = (u["volts"] == "208").astype(float).where(u["volts"].isin(["208", "240", "120"]))
    u["amps_bin"] = pd.cut(a, [0, 60, 100, 150, 1e4], labels=["<=60 A", "61-100 A", "101-150 A", ">150 A"]).astype(object)
    return b, u


# ---------------------------------------------------------------- published benchmarks (transcribed)
BENCH = [  # table, variable, domain, category, pct, eb90 (half-width of 90% CI), n
    ("A-110", "site parking type", "statewide", "Open lot", 40, 8, 294),
    ("A-110", "site parking type", "statewide", "Covered lot", 2, 3, 294),
    ("A-110", "site parking type", "statewide", "Above ground parking garage", 7, 4, 294),
    ("A-110", "site parking type", "statewide", "Underground parking garage", 10, 5, 294),
    ("A-110", "site parking type", "statewide", "None", 41, 11, 294),
    ("A-107", "site parking type", "NYC", "None", 67, 17, 94),
    ("A-107", "site parking type", "Climate Zone 4 (LI+Westchester)", "None", 8, 13, 54),
    ("A-107", "site parking type", "Climate Zone 5", "None", 9, 6, 113),
    ("A-107", "site parking type", "Climate Zone 6 (incl. Tompkins)", "None", 1, 2, 33),
    ("A-107", "site parking type", "Climate Zone 5", "Open lot", 82, 14, 113),
    ("A-107", "site parking type", "Climate Zone 6 (incl. Tompkins)", "Open lot", 90, 42, 33),
    ("A-107", "site parking type", "NYC", "Underground parking garage", 8, 5, 94),
    ("A-116", "assigned parking spaces (E16)", "statewide", "76-100%", 36, 8, 623),
    ("A-116", "assigned parking spaces (E16)", "statewide", "None", 25, 5, 623),
    ("A-116", "assigned parking spaces (E16)", "statewide", "51-75%", 15, 6, 623),
    ("A-116", "assigned parking spaces (E16)", "statewide", "26-50%", 13, 5, 623),
    ("A-116", "assigned parking spaces (E16)", "statewide", "1-25%", 8, 4, 623),
    ("A-141", "households with an EV (G15)", "Affordable subsidized", "has EV", 1, 1, 117),
    ("A-141", "households with an EV (G15)", "Affordable census block", "has EV", 0, 0, 117),
    ("A-141", "households with an EV (G15)", "Co-ops and condos", "has EV", 10, 7, 117),
    ("A-141", "households with an EV (G15)", "Market-rate rental", "has EV", 2, 1, 117),
    ("A-128", "site buildings with EV charging", "statewide", "Level 2 present (3 buildings)", np.nan, np.nan, 3),
    ("A-134", "L2 stations per building with stations", "statewide", "mean 3.57 (EB 0.59)", np.nan, np.nan, 3),
    ("A-140", "EV charging fee to tenants (E18)", "statewide", "Yes, charge per kWh", 32, 33, 31),
    ("A-140", "EV charging fee to tenants (E18)", "statewide", "Yes, monthly charge", 26, 32, 31),
    ("A-140", "EV charging fee to tenants (E18)", "statewide", "No, tenants pay on their electric bill", 24, 15, 31),
    ("A-140", "EV charging fee to tenants (E18)", "statewide", "No, it's free", 12, 12, 31),
]


def main() -> None:
    ensure(TABLES, FIGURES, OUT_PROC)
    g = load_general()
    o = load_occupant()
    b, u = load_sites()

    wsum = (weights_summary("general_survey " + GEN_ID, g, {"size": POP_SIZE, "own": POP_OWN, "region": POP_UTIL})
            + weights_summary("occupant_survey " + OCC_ID, o, {"size": POP_SIZE, "own": POP_OWN, "region": POP_UTIL})
            + weights_summary("site_visits " + SV_ID, b, {"size": POP_SIZE, "own": POP_OWN, "region": POP_UTIL}))
    pd.DataFrame(wsum).to_csv(TABLES / "smbs_weights_summary.csv", index=False)

    # (a) occupant EV ownership
    rows = []
    for dim, lvl, d in domains(o, ["size", "own", "region", "tenure", "income", "rent_assist", "climate_zone"]):
        rows.append({"dimension": dim, "level": lvl, "indicator": "household_has_ge1_EV", **est(d, "ev_any")})
    rows.append({"dimension": "statewide", "level": "all", "indicator": "household_has_any_vehicle",
                 "n": 0, "note": "NOT COLLECTED: SMBS asks only about electric vehicles (G15)"})
    occ = pd.DataFrame(rows)
    ev_lb = o[o["w"].notna()]
    occ.loc[len(occ)] = {"dimension": "statewide", "level": "all", "indicator": "EVs_per_household_lower_bound",
                         "n": int(o["ev_count_lb"].notna().sum()), "k": int(o["ev_count_lb"].sum()),
                         "share_unweighted": o["ev_count_lb"].mean(),
                         "share_weighted": float(np.average(ev_lb["ev_count_lb"], weights=ev_lb["w"])),
                         "n_weighted": len(ev_lb),
                         "note": "mean count with 'Three or more' coded 3 (value is a mean, not a share)"}
    occ.round(4).to_csv(TABLES / "smbs_occupant_ev_ownership.csv", index=False)

    # (b)(c) building parking / EV charging
    rows = []
    gen_flags = ["park_any_amenity", "park_offstreet", "park_garage", "park_open_lot", "park_street_only", "ev_charging"]
    for dim, lvl, d in domains(g, ["size", "units_class", "own", "region", "vintage"]):
        for f in gen_flags:
            rows.append({"source": f"general_survey {GEN_ID}", "dimension": dim, "level": lvl, "indicator": f,
                         **est(d, f, units="units")})
    for dim, lvl, d in domains(b, ["size", "own", "region", "vintage"]):
        for f in ["sv_onsite_parking", "sv_open_lot", "sv_covered_lot", "sv_garage", "sv_ev_plugin", "svc_has_208V"]:
            rows.append({"source": f"site_visits {SV_ID}", "dimension": dim, "level": lvl, "indicator": f, **est(d, f)})
    bld = pd.DataFrame(rows)
    bld.round(4).to_csv(TABLES / "smbs_building_parking_ev.csv", index=False)

    # dwelling-unit electrical capacity
    rows = []
    for dim, lvl, d in domains(u, ["size", "own", "region", "vintage"]):
        for f in ["panel_le60A", "panel_ge100A", "panel_ge125A", "panel_ge200A", "panel_208V"]:
            rows.append({"source": f"site_visits {SV_ID}", "dimension": dim, "level": lvl, "indicator": f,
                         "n_buildings": int(d.loc[d[f].notna(), "ark_site_id"].nunique()), **est(d, f, w="w_unit")})
    duc = pd.DataFrame(rows)
    duc.round(4).to_csv(TABLES / "smbs_du_electrical_capacity.csv", index=False)

    # spaces per unit
    rows = []
    for dim, lvl, d in domains(g, ["size", "units_class", "region"]):
        s = d[d["spaces_per_unit"].notna() & np.isfinite(d["spaces_per_unit"])]
        sw = s[s["w"].notna()]
        rows.append({"dimension": dim, "level": lvl, "n_buildings": len(s),
                     "median": s["spaces_per_unit"].median(), "p25": s["spaces_per_unit"].quantile(.25),
                     "p75": s["spaces_per_unit"].quantile(.75),
                     "weighted_mean_capped5": float(np.average(sw["spaces_per_unit"].clip(upper=5), weights=sw["w"]))
                     if len(sw) else np.nan,
                     "ratio_of_sums_spaces_per_unit": s["spaces"].sum() / s["units"].sum() if len(s) else np.nan})
    spu = pd.DataFrame(rows)
    spu.round(3).to_csv(TABLES / "smbs_parking_spaces_per_unit.csv", index=False)

    # charger ports in buildings reporting EV charging (E17)
    ch = g[g["ev_charging"] == 1].copy()
    for c, k in {"e17_2_text": "L1", "e17_3_text": "L2", "e17_4_text": "L3_DCFC", "e17_5_text": "unknown"}.items():
        ch[k] = num(ch[c])
    ch["ports"] = ch[["L1", "L2", "L3_DCFC", "unknown"]].sum(axis=1, min_count=1)
    rows = []
    for dim, lvl, d in domains(ch, ["region"]):
        dd = d[d["ports"].notna()]
        rows.append({"dimension": dim, "level": lvl, "n_buildings_with_charging": len(d),
                     "n_with_port_counts": len(dd), "L1": dd["L1"].sum(), "L2": dd["L2"].sum(),
                     "L3_DCFC": dd["L3_DCFC"].sum(), "unknown": dd["unknown"].sum(),
                     "median_ports_per_building": dd["ports"].median(),
                     "units_in_those_buildings": dd["units"].sum(),
                     "ports_per_100_units": 100 * dd["ports"].sum() / dd["units"].sum() if len(dd) else np.nan})
    pd.DataFrame(rows).round(3).to_csv(TABLES / "smbs_building_ev_charger_ports.csv", index=False)

    # distributions
    gp = g[g["park_any_amenity"] == 1]
    rows = dist(gp, "e16", f"general_survey {GEN_ID}", "buildings with parking areas (E14)")
    for r in ["ConEd", "NYSEG+RG&E"]:
        rows += dist(gp[gp["region"] == r], "e16", f"general_survey {GEN_ID}", "buildings with parking areas", r)
    rows += dist(gp[gp["region"].isin(["NationalGrid", "NYSEG+RG&E"])], "e16", f"general_survey {GEN_ID}",
                 "buildings with parking areas", UPSTATE)
    rows += dist(g[g["ev_charging"] == 1], "e18", f"general_survey {GEN_ID}", "buildings with EV charging (E14)")
    rows += dist(g, "e19", f"general_survey {GEN_ID}", "all buildings (electric metering)")
    rows += dist(gp, "e15", f"general_survey {GEN_ID}", "buildings with parking areas (raw E15 multi-select)")
    rows += dist(o, "g15", f"occupant_survey {OCC_ID}", "all households (raw G15)")
    rows += dist(o[o["ev_any"] == 1], "g16", f"occupant_survey {OCC_ID}", "households with >=1 EV")
    rows += dist(o[o["ev_any"] == 1], "g17", f"occupant_survey {OCC_ID}", "households with >=1 EV (skip: G16=home)")
    rows += dist(b, "sv_parking_class", f"site_visits {SV_ID}", "all site-visit buildings")
    for r in REGIONS:
        rows += dist(b[b["region"] == r], "sv_parking_class", f"site_visits {SV_ID}", "site-visit buildings", r)
    for r in REGIONS:
        rows += dist(u[u["region"] == r], "amps_bin", f"site_visits {SV_ID}", "dwelling units with panel amps", r,
                     w="w_unit")
    rows += dist(u, "amps_bin", f"site_visits {SV_ID}", "dwelling units with panel amps", "statewide", w="w_unit")
    xl = pd.ExcelFile(SRC / "smbs2022_site_visits.xlsx")
    du = xl.parse("unit_information_uni4_05_15_2")
    du["dwlg_parking_spots"] = num(du["dwlg_parking_spots"])
    rows += dist(du.assign(w=np.nan), "dwlg_parking_spots", f"site_visits {SV_ID}",
                 "dwelling units with spots recorded (blank = not recorded)")
    pd.DataFrame(rows).round(4).to_csv(TABLES / "smbs_distributions.csv", index=False)

    pd.DataFrame(BENCH, columns=["appendix_table", "variable", "domain", "category", "pct_weighted_cadmus",
                                 "eb90_pct", "n"]).to_csv(TABLES / "smbs_published_benchmarks.csv", index=False)

    inv = [
        (OCC_ID, "g15", "How many EVs are owned or leased by people who live in your home?", "all", o["g15"]),
        (OCC_ID, "g16", "Where do people who live in your home most often charge EV(s)?", "G15>0", o["g16"]),
        (OCC_ID, "g17", "How do you pay to use your building's EV charger?", "G16=At home", o["g17"]),
        (OCC_ID, "g3", "Household income (bands)", "all", o["g3"]),
        (OCC_ID, "g5", "Own or rent", "all", o["g5"]),
        (OCC_ID, "g6", "Receives rent assistance", "all", o["g6"]),
        (OCC_ID, "building_size / ownership_type / iou / climate_zone", "derived strata", "all", o["iou"]),
        (GEN_ID, "e14", "Amenities (multi): Parking areas; Electric vehicle charging stations; carsharing ...", "all", g["e14"]),
        (GEN_ID, "e15, e15_1..3_text", "Parking type (multi) + spaces: underground garage, above-ground garage, open lot, street only", "E14 has Parking areas", g["e15"]),
        (GEN_ID, "e16", "% of parking spaces assigned to specific tenants", "E14 has Parking areas", g["e16"]),
        (GEN_ID, "e17, e17_2..5_text", "EV charging stations available to occupants: L1/L2/L3/unknown counts", "E14 has EV charging", g["e17"]),
        (GEN_ID, "e18", "Do you charge tenants to use the EV chargers?", "E14 has EV charging", g["e18"]),
        (GEN_ID, "e19", "Electric metering (direct-metered units / master / submetered)", "all", g["e19"]),
        (GEN_ID, "e3 / strata1 / strata3 / strata4 / e9 / e10", "units, floors, ownership, utility, year built", "all", g["strata4"]),
        (SV_ID, "parking_type, parking_spaces, parking_management", "Parking element per building", "site visits", b["types"].where(b["sv_onsite_parking"] == 1)),
        (SV_ID, "ev_plugin, ev_charging_types, ev_charging_stations_l1..l3 (+make/model)", "EV plug-ins at building", "site visits", b["ev_plugin"]),
        (SV_ID, "dwlg_parking_spots, dwlg_parking_type", "Parking spots tied to dwelling unit", "sampled units", du["dwlg_parking_spots"]),
        (SV_ID, "dwlg_panel_volts, dwlg_panel_amps(_other)", "Dwelling-unit panel rating", "sampled units", u["amps"]),
        (SV_ID, "dwlg_service_* / elec_service_equip_* (type, volts, amps, phase)", "Dwelling / building service equipment", "site visits", b["svc_volts"]),
        (SV_ID, "electricity_provider, building_stories_above_grade, building_ownership_type, year_constructed", "strata", "site visits", b["region"]),
    ]
    pd.DataFrame([{"dataset_id": a, "variables": v, "content": c, "universe": un, "n_nonmissing": int(s.notna().sum())}
                  for a, v, c, un, s in inv]).to_csv(TABLES / "smbs_variable_inventory.csv", index=False)

    # ------------------------------------------------------------ model parameters
    P = []

    def add(param, unit, df, dim, lvl, ind, src, vars_, note="", scale_units=False):
        r = df[(df["dimension"] == dim) & (df["level"] == lvl) & (df["indicator"] == ind)]
        if "source" in df and src.split()[0] in ("general_survey", "site_visits"):
            r = r[r["source"] == src] if (r["source"] == src).any() else r
        r = r.iloc[0]
        k, n = int(r["k"]), int(r["n"])
        boot_ok = 0 < k < n and pd.notna(r.get("boot95_lo"))
        if scale_units:
            P.append({"parameter": param, "domain": f"{dim}={lvl}" if dim != "statewide" else "NY statewide",
                      "unit_of_analysis": unit, "n": n, "k": k, "n_weighted": int(r["n_weighted"]),
                      "kish_n_eff": round(float(r["kish_n_eff"]), 1),
                      "estimate_weighted": round(float(r["share_weighted_by_units"]), 4),
                      "ci95_lo": round(float(r["boot95_units_lo"]), 4), "ci95_hi": round(float(r["boot95_units_hi"]), 4),
                      "ci_method": "bootstrap percentile, weight = building weight x E3 units (weights fixed)",
                      "estimate_unweighted": round(float(r["share_unweighted"]), 4), "source_dataset": src,
                      "source_variables": vars_, "evidence_class": "B", "notes": note})
            return
        P.append({"parameter": param, "domain": f"{dim}={lvl}" if dim != "statewide" else "NY statewide",
                  "unit_of_analysis": unit, "n": n, "k": k, "n_weighted": int(r["n_weighted"]),
                  "kish_n_eff": round(float(r["kish_n_eff"]), 1) if pd.notna(r.get("kish_n_eff")) else np.nan,
                  "estimate_weighted": round(float(r["share_weighted_by_units"] if scale_units else r["share_weighted"]), 4),
                  "ci95_lo": round(float(r["boot95_lo"] if boot_ok and not scale_units else r["wilson95_lo"]), 4),
                  "ci95_hi": round(float(r["boot95_hi"] if boot_ok and not scale_units else r["wilson95_hi"]), 4),
                  "ci_method": ("bootstrap percentile, weighted (weights fixed)" if boot_ok and not scale_units
                                else "Wilson on unweighted k/n"),
                  "estimate_unweighted": round(float(r["share_unweighted"]), 4),
                  "source_dataset": src, "source_variables": vars_, "evidence_class": "B",
                  "notes": note})

    occ_src = f"NYSERDA SMBS 2022 Occupant Survey {OCC_ID}"
    for dim, lvl in [("statewide", "all"), ("size", "1-3 floors"), ("size", "4-7 floors"), ("size", "8+ floors"),
                     ("region", "ConEd"), ("region", UPSTATE), ("region", "NYSEG+RG&E"),
                     ("own", "Market-rate rental"), ("own", "Affordable subsidized"),
                     ("own", "Affordable census block/NOAH"), ("own", "Co-op/condo"), ("tenure", "rent"), ("tenure", "own")]:
        add("share_MF_households_with_ge1_EV", "household", occ, dim, lvl, "household_has_ge1_EV", occ_src,
            "g15; strata building_size/ownership_type/iou; g5",
            "2022-23; BEV+PHEV not distinguished; n tiny; 3 of 8 EV households report 'Three or more' EVs")
    P.append({"parameter": "share_MF_households_with_ge1_vehicle", "domain": "NY statewide", "unit_of_analysis": "household",
              "n": 0, "evidence_class": "B", "source_dataset": occ_src, "source_variables": "none",
              "notes": "NOT AVAILABLE in SMBS (no general vehicle-ownership question); use ACS PUMS BLD x VEH x TEN for Tompkins"})
    gen_src = f"NYSERDA SMBS 2022 General Survey {GEN_ID}"
    for dim, lvl in [("statewide", "all"), ("size", "1-3 floors"), ("size", "4-7 floors"), ("size", "8+ floors"),
                     ("units_class", "5-9"), ("units_class", "10-19"), ("units_class", "20-49"), ("units_class", "50-99"),
                     ("units_class", "100+"), ("region", "ConEd"), ("region", UPSTATE), ("region", "NYSEG+RG&E")]:
        add("share_MF_buildings_with_offstreet_parking", "building", bld, dim, lvl, "park_offstreet", f"general_survey {GEN_ID}",
            "e14 (Parking areas), e15 (types, excl. 'Street parking only')",
            "self-report by building representative; buildings without 'Parking areas' in E14 treated as none")
    for dim, lvl in [("statewide", "all"), ("region", UPSTATE), ("region", "NYSEG+RG&E")]:
        add("share_MF_units_in_buildings_with_offstreet_parking", "dwelling unit (building weight x E3 units)", bld, dim,
            lvl, "park_offstreet", f"general_survey {GEN_ID}", "e14, e15, e3", "CI is Wilson on buildings (approximate)",
            scale_units=True)
    for dim, lvl in [("statewide", "all"), ("region", "ConEd"), ("region", UPSTATE)]:
        add("share_MF_buildings_with_onsite_parking_sitevisit", "building", bld, dim, lvl, "sv_onsite_parking",
            f"site_visits {SV_ID}", "parking_type", "field-observed; blank parking record treated as no parking")
    for dim, lvl in [("statewide", "all"), ("size", "1-3 floors"), ("size", "4-7 floors"), ("size", "8+ floors"),
                     ("region", "ConEd"), ("region", UPSTATE), ("region", "NYSEG+RG&E")]:
        add("share_MF_buildings_with_EV_charging", "building", bld, dim, lvl, "ev_charging", f"general_survey {GEN_ID}",
            "e14 (Electric vehicle charging stations), e17", "2022-23 snapshot; charging access has grown since")
    add("share_MF_units_in_buildings_with_EV_charging", "dwelling unit (building weight x E3 units)", bld, "statewide",
        "all", "ev_charging", f"general_survey {GEN_ID}", "e14, e3", "CI is Wilson on buildings (approximate)",
        scale_units=True)
    for dim, lvl in [("statewide", "all"), ("region", UPSTATE)]:
        add("share_MF_buildings_with_EV_plugin_sitevisit", "building", bld, dim, lvl, "sv_ev_plugin",
            f"site_visits {SV_ID}", "ev_plugin", "field-observed; blank treated as no plug-in")
    for dim, lvl, ind in [("statewide", "all", "panel_ge100A"), ("region", "ConEd", "panel_ge100A"),
                          ("region", UPSTATE, "panel_ge100A"), ("statewide", "all", "panel_ge200A"),
                          ("statewide", "all", "panel_208V")]:
        add(f"share_MF_dwelling_units_{ind}", "dwelling unit (sampled units; building weight / units sampled)",
            duc, dim, lvl, ind, f"site_visits {SV_ID}", "dwlg_panel_amps, dwlg_panel_amps_other, dwlg_panel_volts",
            "panel rating, not spare capacity; technicians confused 208V vs 240V (overview PDF)")
    for lvl in ["all", UPSTATE]:
        r = spu[spu["level"] == lvl].iloc[0]
        P.append({"parameter": "parking_spaces_per_unit_median (buildings with off-street parking)",
                  "domain": "NY statewide" if lvl == "all" else f"region={lvl}", "unit_of_analysis": "building",
                  "n": int(r["n_buildings"]), "estimate_unweighted": round(float(r["median"]), 3),
                  "estimate_weighted": round(float(r["weighted_mean_capped5"]), 3),
                  "ci_method": f"IQR {r['p25']:.2f}-{r['p75']:.2f} (unweighted); estimate_weighted = weighted mean capped at 5",
                  "source_dataset": gen_src, "source_variables": "e15_1_text, e15_2_text, e15_3_text, e3",
                  "evidence_class": "B", "notes": "complex-level lots may be reported against a single building"})
    params = pd.DataFrame(P)
    params.to_csv(OUT_PROC / "mf_ev_parameters.csv", index=False)

    figures(g, bld, u, occ)
    print(params[["parameter", "domain", "n", "k", "estimate_weighted", "ci95_lo", "ci95_hi", "estimate_unweighted"]]
          .to_string())


# ---------------------------------------------------------------- figures
def _ylabels(sub: pd.DataFrame) -> list[str]:
    return [f"{('NY statewide' if l == 'all' else l)}  (n={n})" for l, n in zip(sub["level"], sub["n"])]


def figures(g, bld, u, occ) -> None:
    order = ["all"] + REGIONS + [UPSTATE]
    gen = bld[bld["source"].str.startswith("general") & bld["dimension"].isin(["statewide", "region"])]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.6), sharey=True)
    for ax, ind, title in [(axes[0], "park_offstreet", "Buildings with off-street parking"),
                           (axes[1], "ev_charging", "Buildings with EV charging for occupants")]:
        sub = gen[gen["indicator"] == ind].set_index("level").loc[order].reset_index()
        y = np.arange(len(sub))[::-1]
        ax.barh(y, sub["share_weighted"] * 100, height=0.55, color=BLUE, zorder=2)
        err = np.vstack([sub["share_weighted"] - sub["boot95_lo"], sub["boot95_hi"] - sub["share_weighted"]]) * 100
        ax.errorbar(sub["share_weighted"] * 100, y, xerr=err, fmt="none", ecolor=INK2, elinewidth=1, capsize=2, zorder=3)
        off = 1.2 if ind == "park_offstreet" else 0.25
        for yi, v, hi in zip(y, sub["share_weighted"] * 100, sub["boot95_hi"] * 100):
            ax.text(hi + off, yi, f"{v:.0f}%" if v >= 10 else f"{v:.1f}%", va="center", fontsize=8, color=INK2)
        ax.set_yticks(y, _ylabels(sub))
        ax.set_title(title, loc="left", fontsize=10, color=INK)
        ax.grid(axis="x", color=GRID, linewidth=1, zorder=0)
        ax.set_xlabel("% of MF buildings (raked weights; 95% bootstrap CI)")
        ax.tick_params(length=0)
    axes[0].set_xlim(0, 110)
    axes[1].set_xlim(0, max(12, float(gen.loc[gen["indicator"] == "ev_charging", "boot95_hi"].max() * 100) + 3))
    fig.text(0.01, 0.01, "Source: NYSERDA SMBS 2022 General Survey (gfhm-wz4s), building representatives, 2022-23. "
             "Evidence class B. Region = electric utility; Tompkins County is NYSEG territory.", fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGURES / "smbs_parking_ev_charging_by_region.png", dpi=200)
    plt.close(fig)

    # panel amps stacked
    bins = ["<=60 A", "61-100 A", "101-150 A", ">150 A"]
    rows, labels = [], []
    for lvl in ["statewide"] + REGIONS + [UPSTATE]:
        d = u if lvl == "statewide" else (u[u["region"].isin(["NationalGrid", "NYSEG+RG&E"])] if lvl == UPSTATE
                                          else u[u["region"] == lvl])
        d = d[d["amps_bin"].notna() & d["w_unit"].notna()]
        sh = d.groupby("amps_bin")["w_unit"].sum().reindex(bins).fillna(0) / d["w_unit"].sum()
        rows.append(sh.to_numpy() * 100)
        labels.append(f"{'NY statewide' if lvl == 'statewide' else lvl}  (units={len(d)}, bldgs={d['ark_site_id'].nunique()})")
    arr = np.array(rows)
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    y = np.arange(len(arr))[::-1]
    left = np.zeros(len(arr))
    for j, bname in enumerate(bins):
        ax.barh(y, arr[:, j], left=left, height=0.55, color=ORDINAL_BLUE[j], edgecolor=SURF, linewidth=2,
                label=bname, zorder=2)
        for yi, l0, v in zip(y, left, arr[:, j]):
            if v >= 9:
                ax.text(l0 + v / 2, yi, f"{v:.0f}%", ha="center", va="center", fontsize=7.5,
                        color=INK if j == 0 else "white")
        left += arr[:, j]
    ax.set_yticks(y, labels)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of dwelling units by rated in-unit panel amperage (raked building weights)")
    ax.set_title("Dwelling-unit electric panel rating, multifamily site visits", loc="left", fontsize=10, pad=24)
    ax.legend(ncol=4, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=8)
    ax.tick_params(length=0)
    fig.text(0.01, 0.01, "Source: NYSERDA SMBS 2022 Site Visits (qwyr-7esw). Evidence class B. Panel rating is not "
             "spare capacity; 208V/240V recording was error-prone.", fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGURES / "smbs_du_panel_amps_by_region.png", dpi=200)
    plt.close(fig)

    # occupant EV ownership dot plot
    keep = [("statewide", "all"), ("size", "1-3 floors"), ("size", "4-7 floors"), ("size", "8+ floors"),
            ("own", "Market-rate rental"), ("own", "Affordable subsidized"), ("own", "Affordable census block/NOAH"),
            ("own", "Co-op/condo"), ("region", "ConEd"), ("region", UPSTATE), ("tenure", "rent"), ("tenure", "own"),
            ("income", "<$35k"), ("income", "$35-75k"), ("income", "$75-150k"), ("income", "$150k+")]
    oc = occ[occ["indicator"] == "household_has_ge1_EV"].set_index(["dimension", "level"])
    sub = oc.loc[keep].reset_index()
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    y = np.arange(len(sub))[::-1]
    ax.hlines(y, sub["wilson95_lo"] * 100, sub["wilson95_hi"] * 100, color=AXIS, linewidth=2, zorder=1,
              label="Wilson 95% CI (unweighted k/n)")
    ax.scatter(sub["share_unweighted"] * 100, y, s=22, color=MUTED, zorder=2, label="unweighted k/n")
    ax.scatter(sub["share_weighted"] * 100, y, s=48, color=BLUE, edgecolor=SURF, linewidth=2, zorder=3,
               label="weighted (raked to building population)")
    ax.set_yticks(y, [f"{'NY statewide' if l == 'all' else l}  ({int(k)}/{int(n)})"
                      for l, k, n in zip(sub["level"], sub["k"], sub["n"])])
    ax.set_xlim(0, 50)
    ax.grid(axis="x", color=GRID, linewidth=1, zorder=0)
    ax.set_xlabel("% of multifamily households with >=1 EV (owned or leased)")
    ax.set_title("EV ownership among NY multifamily occupants, 2022-23 (very small sample)", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    ax.tick_params(length=0)
    fig.text(0.01, 0.01, "Source: NYSERDA SMBS 2022 Occupant Survey (gjv3-iq86), n=156 households, 8 with an EV. "
             "Evidence class B.", fontsize=7, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIGURES / "smbs_occupant_ev_ownership.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
