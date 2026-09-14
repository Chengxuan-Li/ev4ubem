r"""Prepare data and image assets for the presentation deck (built by src/deck/build_deck.js).

Design rules: docs/style/pptx_deck_style_prompt.md. Content (claims, values, units, equations, sources) comes from
docs/report_20260914_ev_model.md and results/tables/; this script only extracts series for native (editable) charts,
draws analytical maps in the deck style, and renders display equations with LaTeX.

Usage (repo root):  .venv/Scripts/python.exe -m src.deck.deck_data
Outputs (git-ignored): results/deck/build/deck_data.json, results/deck/build/maps/*.png, results/deck/build/eq/*.png
Requires: pdflatex + pdftocairo (TeX Live / MiKTeX with poppler) for equations; falls back to matplotlib mathtext.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, LogNorm, Normalize
from matplotlib.lines import Line2D

from src.utils.paths import PROCESSED, RAW, RESULTS, TABLES, ensure

BUILD = RESULTS / "deck" / "build"
MAPS_OUT = BUILD / "maps"
EQ_OUT = BUILD / "eq"

# Deck palette (mirrored in build_deck.js). Location categories use Okabe–Ito (colour-blind safe).
PAL = {
    "text": "#1F2328", "muted": "#5F6B73", "rule": "#BFC5CA", "accent": "#1A5E63", "observed": "#222222", "grey": "#8C8C8C",
    "home": "#0072B2", "work": "#009E73", "public_l2": "#56B4E9", "dcfc": "#D55E00", "fleet": "#CC79A7", "passerby": "#E69F00",
}
FONT = "Roboto"
plt.rcParams.update({"font.family": ["Roboto", "DejaVu Sans"], "font.size": 13, "axes.edgecolor": PAL["rule"],
                     "text.color": PAL["text"], "axes.labelcolor": PAL["text"], "xtick.color": PAL["muted"], "ytick.color": PAL["muted"]})
LOCS = ["home", "work", "public_l2", "dcfc", "fleet", "passerby"]


def r(x, n=3):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)


# ----------------------------------------------------------------------------------------------------------- charts
def stock_series() -> dict:
    ts = pd.read_csv(TABLES / "tompkins_ev_stock_timeseries.csv", parse_dates=["snapshot_date"])
    e = ts[ts["source"].str.startswith("EValuateNY")]
    e = e.sort_values("snapshot_date").groupby(e["snapshot_date"].dt.year).tail(1)
    z = ts[ts["source"].str.contains("method-consistent")]
    s = pd.concat([e, z]).sort_values("snapshot_date")
    t = (s["snapshot_date"].dt.year + s["snapshot_date"].dt.dayofyear / 365.25).round(2)
    return {"t": t.tolist(), "BEV": s["BEV"].round(0).tolist(), "PHEV": s["PHEV"].round(0).tolist(), "EV": s["EV"].round(0).tolist(),
            "source": s["source"].tolist()}


def synthetic_validation() -> dict:
    v = pd.read_csv(TABLES / "synthetic_dwellings_validation_bg.csv")
    out = {}
    for mg in ["tenure_structure", "tenure_vehicles", "income"]:
        q = v[v["margin"] == mg]
        r2 = 1 - ((q["acs"] - q["synthetic"]) ** 2).sum() / ((q["acs"] - q["acs"].mean()) ** 2).sum()
        out[mg] = {"acs": q["acs"].tolist(), "synthetic": q["synthetic"].tolist(), "r2": r(r2), "n": int(len(q))}
    return out


def allocation_shares() -> dict:
    s = pd.read_csv(TABLES / "allocation_structure_shares_2026.csv").set_index("structure")
    t = pd.read_csv(TABLES / "allocation_tenure_shares_2026.csv").set_index("tenure")
    cols = {"E_ev": "Central ensemble", "E_ev_model": "Ecological", "E_ev_uniform": "Uniform", "E_ev_vehicles": "Vehicles",
            "E_ev_individual": "Individual (NHTS)", "E_ev_prior": "Full priors"}
    mf = s.loc[["MF2_4", "MF5_19", "MF20P"]].sum()
    return {"labels": list(cols.values()), "mf": [r(mf[c] * 100, 1) for c in cols], "renter": [r(t.loc["rent", c] * 100, 1) for c in cols],
            "mf_households": r(s.loc[["MF2_4", "MF5_19", "MF20P"], "households_share"].sum() * 100, 1)}


def concentration() -> dict:
    c = pd.read_csv(TABLES / "adoption_concentration_ny.csv")
    t = pd.to_datetime(c["snapshot"])
    return {"t": (t.dt.year + t.dt.dayofyear / 365.25).round(2).tolist(), "ev_per_100hh": c["ev_per_100hh"].round(2).tolist(),
            "gini": c["gini_households"].round(3).tolist(), "top_decile": (c["top_decile_hh_share_of_evs"] * 100).round(1).tolist()}


def growth_backcast() -> dict:
    from src.model import growth as G

    stock, sh, _ = G.observations("tompkins")
    out = {"obs_t": stock["t"].round(2).tolist(), "obs_ev": stock["EV"].round(0).tolist()}
    g = G.GEO["tompkins"]
    for label, tmax in [("full", None), ("le2021", 2022.0)]:
        f = G.fit("tompkins", tmax)
        df = G.simulate(lambda v, f=f: G.logistic(v, 1.0, f["k"], f["t0"]), lambda v, f=f: G.logistic(v, 0.95, f["kb"], f["tb"]),
                        g["N_new"], g["F"], f["m"])
        df = df[(df["year"] + 1 >= 2011) & (df["year"] + 1 <= 2031)]
        out[f"fit_{label}_t"] = (df["year"] + 1).tolist()
        out[f"fit_{label}_ev"] = df["EV"].round(0).tolist()
    return out


def projections() -> dict:
    p = pd.read_csv(TABLES / "growth_projection_tompkins.csv")
    out = {}
    for sc, q in p.groupby("scenario"):
        q = q.sort_values("year")
        out[sc] = {"year": q["year"].tolist(), "p05": q["EV_p05"].round(0).tolist(), "p50": q["EV_p50"].round(0).tolist(),
                   "p95": q["EV_p95"].round(0).tolist(), "share_new": (q["new_share_p50"] * 100).round(1).tolist()}
    return out


def validation_charts() -> dict:
    fr = pd.read_csv(TABLES / "charging_validation_frequency.csv")
    se = pd.read_csv(TABLES / "charging_validation_sessions.csv")
    sh = pd.read_csv(TABLES / "charging_validation_shapes.csv")
    dv = pd.read_csv(TABLES / "charging_validation_diversity.csv")
    sn = pd.read_csv(TABLES / "charging_validation_seasonality.csv")
    shapes = {}
    for loc, q in sh.groupby("location"):
        q = q.sort_values("hour")
        shapes[loc] = {"hour": q["hour"].tolist(), "sim": q["sim_peak_norm"].round(3).tolist(), "ny": q["ny_peak_norm"].round(3).tolist(),
                       "ny_land_use": q["ny_land_use"].iloc[0]}
    freq = {}
    for dt, q in fr.groupby("drivetrain"):
        freq[dt] = {"category": q["category"].tolist(), "sim": (q["simulated_share"] * 100).round(1).tolist(),
                    "drive_clean": (q["drive_clean_share"] * 100).round(1).tolist()}
    return {"frequency": freq, "sessions": se.round(2).to_dict(orient="list"), "shapes": shapes,
            "diversity": dv.round(2).to_dict(orient="list"), "seasonality": sn.round(3).to_dict(orient="list")}


def energy_reconciliation() -> dict:
    e = pd.read_csv(TABLES / "energy_reconciliation.csv")
    return e.round(0).to_dict(orient="list")


def hourly_profiles() -> dict:
    out = {}
    for year, chg in [(2026, "base"), (2035, "base"), (2050, "base"), (2050, "managed"), (2035, "managed")]:
        p = PROCESSED / "load" / f"county_hourly_{year}_trend_{chg}.parquet"
        if not p.exists():
            continue
        c = pd.read_parquet(p)
        hrs = pd.date_range(f"{year}-01-01", periods=len(c), freq="h")
        m = hrs.month.isin([12, 1, 2]) & (hrs.dayofweek < 5)
        ms = hrs.month.isin([6, 7, 8]) & (hrs.dayofweek < 5)
        prof = {loc: (c.loc[m, loc].groupby(hrs[m].hour).mean() / 1000).round(3).tolist() for loc in LOCS if loc in c.columns}
        prof["summer_total"] = (c.loc[ms].sum(axis=1).groupby(hrs[ms].hour).mean() / 1000).round(3).tolist()
        out[f"{year}_{chg}"] = prof
    return out


def scenarios() -> dict:
    s = pd.read_csv(TABLES / "load_scenarios_annual.csv")
    out = {"own": {}, "chg": {}, "loc_trend_base": {}}
    for own, q in s[s["charging_scenario"] == "base"].groupby("ownership_scenario"):
        q = q.sort_values("year")
        out["own"][own] = {"year": q["year"].tolist(), "gwh": (q["annual_mwh_total"] / 1000).round(1).tolist(), "mw": q["peak_mw_total"].round(1).tolist()}
    for chg, q in s[s["ownership_scenario"] == "trend"].groupby("charging_scenario"):
        q = q.sort_values("year")
        out["chg"][chg] = {"year": q["year"].tolist(), "mw": q["peak_mw_total"].round(1).tolist(), "home_mw": q["home_peak_mw"].round(1).tolist(),
                           "dcfc_gwh": (q["annual_mwh_dcfc"] / 1000).round(1).tolist()}
    q = s[(s["ownership_scenario"] == "trend") & (s["charging_scenario"] == "base")].sort_values("year")
    out["loc_trend_base"] = {"year": q["year"].tolist()} | {loc: (q[f"annual_mwh_{loc}"] / 1000).round(2).tolist() for loc in LOCS}
    return out


def parcel_peaks() -> dict:
    du = pd.read_parquet(PROCESSED / "synthetic" / "dwelling_units.parquet", columns=["parcel"])
    units = du.groupby("parcel").size().rename("units")
    bins, labels = [0, 1, 2, 4, 19, 49, 10_000], ["1", "2", "3–4", "5–19", "20–49", "50+"]
    out = {"bins": labels}
    for year in [2026, 2035]:
        p = PROCESSED / "load" / f"parcel_summary_{year}_trend_base.csv"
        if not p.exists():
            continue
        s = pd.read_csv(p, dtype={"parcel": str}).join(units, on="parcel")
        s = s[s["E_ev"] > 0]
        g = s.groupby(pd.cut(s["units"], bins, labels=labels), observed=False).agg(
            parcels=("parcel", "size"), E_ev=("E_ev", "mean"), p50=("peak_kw_p50", "mean"), p90=("peak_kw_p90", "mean"))
        out[str(year)] = {k: [r(x, 2) for x in g[k].values] for k in g.columns}
    return out


def infrastructure() -> dict:
    t = pd.read_csv(TABLES / "infrastructure_history_tompkins_ny.csv")
    q = t[(t["geography"] == "Tompkins County")]
    out = {}
    for (acc, lvl), g in q.groupby(["access", "level"]):
        g = g.sort_values("year")
        out[f"{acc}_{lvl}"] = {"year": g["year"].tolist(), "ports": g["ports"].tolist(), "stations": g["stations"].tolist()}
    e = pd.read_csv(TABLES / "infrastructure_evs_per_public_port.csv")
    e = e[e["geography"] == "Tompkins County"]
    out["evs_per_public_port"] = {"date": e["date"].tolist(), "value": e["evs_per_public_port"].round(1).tolist()}
    return out


def optional_tables() -> dict:
    """Results from follow-on analyses, included when present."""
    out = {}
    for name in ["uncertainty_decomposition_county", "uncertainty_decomposition_bg", "uncertainty_decomposition_parcel",
                 "uncertainty_factor_ranges", "incommuter_charging_estimate", "incommuter_flows_by_origin"]:
        p = TABLES / f"{name}.csv"
        if p.exists():
            t = pd.read_csv(p)
            if name == "incommuter_flows_by_origin" and len(t) > 40:
                t = t.head(40)
            out[name] = t.astype(object).where(t.notna(), None).to_dict(orient="records")
    return out


# ------------------------------------------------------------------------------------------------------------- maps
def _geo():
    bg = gpd.read_file(PROCESSED / "geography" / "tompkins_bg.gpkg").to_crs(32618).rename(columns={"GEOID": "bg"})
    county = bg.dissolve()
    place = RAW / "census" / "tiger" / "tl_2024_36_place.zip"
    city = None
    if place.exists():
        pl = gpd.read_file(f"zip://{place.as_posix()}").to_crs(32618)
        city = pl[(pl["NAME"] == "Ithaca") & (pl["LSAD"] == "25")]
        city = city if len(city) else None
    return bg, county, city


def _frame(ax, extent=None):
    ax.set_axis_off()
    if extent is not None:
        ax.set_xlim(extent[0], extent[2]); ax.set_ylim(extent[1], extent[3])
    ax.set_aspect("equal")


def _scalebar(ax, km, loc=(0.06, 0.05)):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    x = x0 + loc[0] * (x1 - x0); y = y0 + loc[1] * (y1 - y0)
    ax.plot([x, x + km * 1000], [y, y], color=PAL["text"], lw=2, solid_capstyle="butt")
    ax.text(x + km * 500, y + 0.015 * (y1 - y0), f"{km:g} km", ha="center", va="bottom", fontsize=12, color=PAL["text"])


def _city_extent(city, pad=900):
    b = city.total_bounds
    return (b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)


def _choropleth_pair(g, column, cmap, norm, cbar_label, fname, ticks=None, fmt="{:g}"):
    bg, county, city = _geo()
    fig = plt.figure(figsize=(12.0, 5.4))
    ax1 = fig.add_axes([0.0, 0.02, 0.44, 0.96]); ax2 = fig.add_axes([0.47, 0.10, 0.40, 0.80]); cax = fig.add_axes([0.905, 0.18, 0.018, 0.64])
    for ax in (ax1, ax2):
        g[g[column].isna()].plot(ax=ax, color="white", edgecolor=PAL["rule"], hatch="///", linewidth=0.3)
        g[g[column].notna()].plot(ax=ax, column=column, cmap=cmap, norm=norm, edgecolor="white", linewidth=0.35)
        county.boundary.plot(ax=ax, color=PAL["muted"], linewidth=0.6)
        if city is not None:
            city.boundary.plot(ax=ax, color=PAL["text"], linewidth=1.0, linestyle=(0, (4, 2)))
    _frame(ax1); _scalebar(ax1, 5)
    if city is not None:
        ext = _city_extent(city)
        _frame(ax2, ext); _scalebar(ax2, 1)
        ax1.add_patch(plt.Rectangle((ext[0], ext[1]), ext[2] - ext[0], ext[3] - ext[1], fill=False, edgecolor=PAL["text"], lw=0.8))
        ax2.text(0.0, 1.02, "City of Ithaca (dashed) and surroundings", transform=ax2.transAxes, fontsize=12, color=PAL["muted"])
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, cax=cax)
    cb.outline.set_visible(False); cb.ax.tick_params(labelsize=12, length=0)
    if ticks is not None:
        cb.set_ticks(ticks); cb.set_ticklabels([fmt.format(t) for t in ticks])
    cb.set_label(cbar_label, fontsize=13)
    if g[column].isna().any():
        fig.text(0.87, 0.08, "hatched: no households", fontsize=11, color=PAL["muted"], ha="right")
    fig.savefig(MAPS_OUT / fname, dpi=220, facecolor="white"); plt.close(fig)


def map_allocation():
    bg, _, _ = _geo()
    a = pd.read_csv(TABLES / "allocation_bg_2026_uncertainty.csv", dtype={"bg": str})
    a["spread"] = a["structural_max"] / a["structural_min"]
    a["ev_per_100hh"] = a["ev_per_hh"] * 100
    g = bg.merge(a, on="bg", how="left")
    g.loc[g["households"].fillna(0) == 0, ["ev_per_100hh", "spread"]] = np.nan
    _choropleth_pair(g, "ev_per_100hh", plt.get_cmap("GnBu"), Normalize(0, 14), "Expected personal EVs per 100 households, 2026",
                     "map_ev_per_100hh_2026.png", ticks=[0, 2, 4, 6, 8, 10, 12, 14])
    _choropleth_pair(g, "spread", plt.get_cmap("Purples"), BoundaryNorm([1, 1.25, 1.5, 2, 3, 5], 256, extend="max"),
                     "Structural spread: max / min expected EVs across 5 weightings", "map_structural_spread_2026.png",
                     ticks=[1, 1.25, 1.5, 2, 3, 5], fmt="{:g}×")
    return {"spread_median": r(g["spread"].median(), 2), "spread_max": r(g["spread"].max(), 2)}


def map_home_energy():
    bg, county, city = _geo()
    du = pd.read_parquet(PROCESSED / "synthetic" / "dwelling_units.parquet", columns=["bg"]).groupby("bg").size().rename("households")
    frames = {}
    for year in [2026, 2035]:
        h = pd.read_parquet(PROCESSED / "load" / f"bg_home_hourly_{year}_trend_base.parquet")
        d = pd.DataFrame({"bg": h.columns.astype(str), "kwh": h.sum().values}).merge(du, left_on="bg", right_index=True, how="left")
        d["kwh_per_hh"] = d["kwh"] / d["households"]
        frames[year] = bg.merge(d, on="bg", how="left")
    norm = BoundaryNorm([0, 50, 100, 200, 400, 800, 1600], 256, extend="max")
    cmap = plt.get_cmap("YlOrBr")
    fig = plt.figure(figsize=(12.0, 5.4))
    axes = [fig.add_axes([0.0, 0.02, 0.43, 0.80]), fig.add_axes([0.45, 0.02, 0.43, 0.80])]
    cax = fig.add_axes([0.905, 0.12, 0.018, 0.64])
    for ax, (year, g) in zip(axes, frames.items()):
        g.plot(ax=ax, column="kwh_per_hh", cmap=cmap, norm=norm, edgecolor="white", linewidth=0.3,
               missing_kwds={"color": "white", "hatch": "///", "edgecolor": PAL["rule"]})
        county.boundary.plot(ax=ax, color=PAL["muted"], linewidth=0.6)
        if city is not None:
            city.boundary.plot(ax=ax, color=PAL["text"], linewidth=1.0, linestyle=(0, (4, 2)))
        _frame(ax)
        tot = g["kwh"].sum() / 1e3
        ax.text(0.0, 1.13, str(year), transform=ax.transAxes, fontsize=18, fontweight="bold", va="bottom", color=PAL["text"])
        ax.text(0.0, 1.03, f"{tot:,.0f} MWh/yr at homes (county)", transform=ax.transAxes, fontsize=13, va="bottom", color=PAL["muted"])
    _scalebar(axes[0], 5)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, cax=cax); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=12, length=0)
    cb.set_label("Home EV charging, kWh per household per year", fontsize=13)
    fig.savefig(MAPS_OUT / "map_home_kwh_per_hh_2026_2035.png", dpi=220, facecolor="white"); plt.close(fig)
    return {str(y): r(g["kwh"].sum() / 1e3, 0) for y, g in frames.items()}


def map_sites():
    bg, county, city = _geo()
    s = pd.read_csv(PROCESSED / "load" / "site_summary_2026_trend_base.csv").dropna(subset=["lat", "lon"])
    st = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s["lon"], s["lat"]), crs=4326).to_crs(32618)
    types = [("public_l2", "Public Level 2", PAL["public_l2"], "o", True), ("dcfc", "DC fast", PAL["dcfc"], "o", True),
             ("workplace_listed", "Workplace, listed", PAL["work"], "s", True),
             ("workplace_unlisted_parcel", "Workplace, assumed\n(large non-res. parcel)", PAL["work"], "s", False)]
    fig = plt.figure(figsize=(12.0, 5.6))
    ax1 = fig.add_axes([0.0, 0.02, 0.38, 0.96]); ax2 = fig.add_axes([0.40, 0.06, 0.38, 0.86])
    size = lambda kwh: np.clip(kwh / 1000 * 1.2, 6, 900)  # noqa: E731  marker area ∝ MWh
    for ax in (ax1, ax2):
        bg.plot(ax=ax, color="#F4F5F6", edgecolor="white", linewidth=0.4)
        county.boundary.plot(ax=ax, color=PAL["muted"], linewidth=0.6)
        if city is not None:
            city.boundary.plot(ax=ax, color=PAL["text"], linewidth=0.9, linestyle=(0, (4, 2)))
        for key, _, col, mk, filled in types:
            q = st[st["site_type"] == key]
            ax.scatter(q.geometry.x, q.geometry.y, s=size(q["annual_kwh"]), marker=mk, facecolor=col if filled else "none",
                       edgecolor=col, linewidth=0.9, alpha=0.8 if filled else 0.7, zorder=3)
    _frame(ax1); _scalebar(ax1, 5)
    if city is not None:
        ext = _city_extent(city, 700)
        _frame(ax2, ext); _scalebar(ax2, 1)
        ax1.add_patch(plt.Rectangle((ext[0], ext[1]), ext[2] - ext[0], ext[3] - ext[1], fill=False, edgecolor=PAL["text"], lw=0.8))
    handles = [Line2D([], [], marker=mk, linestyle="", markersize=10, markerfacecolor=col if filled else "none", markeredgecolor=col, label=lab)
               for _, lab, col, mk, filled in types]
    leg1 = fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.79, 0.94), frameon=False, fontsize=12, title="Site type", title_fontsize=12)
    leg1._legend_box.align = "left"
    sz = [Line2D([], [], marker="o", linestyle="", markersize=np.sqrt(size(v * 1000)), markerfacecolor="none", markeredgecolor=PAL["muted"],
                 label=f"{v:g} MWh/yr") for v in [10, 100, 500]]
    leg2 = fig.legend(handles=sz, loc="upper left", bbox_to_anchor=(0.79, 0.50), frameon=False, fontsize=12, labelspacing=1.4, title="Annual energy", title_fontsize=12)
    leg2._legend_box.align = "left"
    fig.savefig(MAPS_OUT / "map_sites_2026.png", dpi=220, facecolor="white"); plt.close(fig)
    return st.groupby("site_type")["annual_kwh"].agg(["size", "sum"]).round(0).to_dict()


# -------------------------------------------------------------------------------------------------------- equations
EQUATIONS = {
    "propensity": r"""\begin{aligned}
\mu_z &= e^{\beta_0+\gamma^{\top}Z_z}\, I_z \sum_{\tau\in\{\mathrm{own},\mathrm{rent}\}} HH_{z,\tau}\,A_{z,\tau}\,V_{z,\tau},
\qquad EV_z \sim \mathrm{NegBin}(\mu_z,\alpha)\\[4pt]
A_{z,\tau} &= \sum_g s_{g\mid\tau,z}\,e^{a_{g,\tau}},\qquad V_{z,\tau}=\sum_{v\ge 1} s_{v\mid\tau,z}\,v^{\eta},\qquad I_z=\sum_i s_{i,z}\,e^{c_i}
\end{aligned}""",
    "allocation": r"""\begin{aligned}
E^{(m)}_d &= \min\!\Big(v_d,\; T_z\,\frac{w^{(m)}_d}{\sum_{d'\in z} w^{(m)}_{d'}}\Big)\quad\text{(excess redistributed)}\\[4pt]
E_d &= \tfrac12\big(E^{(\mathrm{model})}_d + E^{(\mathrm{individual})}_d\big)\\[4pt]
w^{(\mathrm{model})}_d &= e^{\gamma^{\top}Z_{bg}}\,v_d^{\eta},\qquad
w^{(\mathrm{individual})}_d = v_d\cdot OR_{\mathrm{income}}\cdot OR_{\mathrm{SF}}\cdot OR_{\mathrm{tenure}}
\end{aligned}""",
    "growth": r"""\begin{aligned}
s(v) &= \frac{1}{1+e^{-k(v-t_0)}},\qquad A(v)=N_{\mathrm{new}}\,m\,s(v)\\[4pt]
EV(t) &= \sum_v A(v)\,S\big(t-v-\tfrac12\big),\qquad S(a)=e^{-(a/\lambda)^{\kappa}}
\end{aligned}""",
    "evolution": r"""\pi_z(y)\propto \pi_z(2026)^{\varphi(y)}\,h_z^{\,1-\varphi(y)},\qquad w_d(y)=w_d^{\varphi(y)},\qquad
\varphi(y)=0.90^{\log_2\left(EV(y)/EV(2026)\right)}""",
    "event": r"""\begin{aligned}
E_t &= d_t\,e_{\mathrm{wheel}}(y)\,m(T_t),\qquad m(T)=1+0.011\max(0,20-T)+0.006\max(0,T-25)\\[4pt]
d_t &= A\,\frac{g_t\,\mathbb{1}[\mathrm{drive}_t]}{\sum_{t'} g_{t'}\,\mathbb{1}[\mathrm{drive}_{t'}]},\qquad g_t\sim\Gamma(1.3,1),\qquad A\sim\mathrm{LogN}\\[4pt]
q &= \min\!\big(D/\eta_\ell,\; P_\ell\cdot\mathrm{conn}\big)
\end{aligned}""",
    "assembly": r"""\begin{aligned}
L_d(t) &= E^{\mathrm{BEV}}_d(y)\,\Pi_{k(d),\mathrm{BEV}}(t) + E^{\mathrm{PHEV}}_d(y)\,\Pi_{k(d),\mathrm{PHEV}}(t)\\[4pt]
\Pi_{k,v}(t) &= \sum_a P(a\mid k,v,y,c)\,\bar h_a(t)\\[4pt]
P(\text{workplace user}\mid k) &= 1-\big(1-p_{\mathrm{access}}(y)\,p_{\mathrm{use}}\big)^{\mathrm{workers}(k)}
\end{aligned}""",
}


def render_equations() -> dict:
    ensure(EQ_OUT)
    have_tex = shutil.which("pdflatex") and shutil.which("pdftocairo")
    sizes = {}
    for name, body in EQUATIONS.items():
        out = EQ_OUT / f"eq_{name}.png"
        if have_tex:
            # Roboto text with matching sans-serif math (newtxsf) so equations share the deck typeface
            doc = (r"\documentclass[border=2pt,varwidth=40cm]{standalone}\usepackage[T1]{fontenc}\usepackage[sfdefault]{roboto}"
                   r"\usepackage{amsmath}\usepackage{newtxsf}"
                   r"\begin{document}\Large $\displaystyle " + body.replace(r"\mathbb{1}", r"\mathbf{1}") + r"$\end{document}")
            with tempfile.TemporaryDirectory() as td:
                (Path(td) / "eq.tex").write_text(doc, encoding="utf-8")
                subprocess.run(["pdflatex", "-interaction=nonstopmode", "eq.tex"], cwd=td, check=True, capture_output=True)
                subprocess.run(["pdftocairo", "-png", "-transp", "-r", "400", "-singlefile", "eq.pdf", "eq"], cwd=td, check=True, capture_output=True)
                shutil.copy(Path(td) / "eq.png", out)
        from PIL import Image

        with Image.open(out) as im:
            sizes[name] = {"px": list(im.size), "dpi": 400}
    return sizes


def main() -> None:
    ensure(BUILD, MAPS_OUT, EQ_OUT)
    data = {"palette": PAL, "font": FONT}
    for key, fn in [("stock", stock_series), ("synthetic", synthetic_validation), ("allocation", allocation_shares),
                    ("concentration", concentration), ("backcast", growth_backcast), ("projections", projections),
                    ("validation", validation_charts), ("energy_reconciliation", energy_reconciliation), ("hourly", hourly_profiles),
                    ("scenarios", scenarios), ("parcel_peaks", parcel_peaks), ("infrastructure", infrastructure),
                    ("optional", optional_tables), ("map_allocation", map_allocation), ("map_home_energy", map_home_energy),
                    ("map_sites", map_sites), ("equations", render_equations)]:
        data[key] = fn()
        print("ok", key)
    (BUILD / "deck_data.json").write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
    print("wrote", BUILD / "deck_data.json")


if __name__ == "__main__":
    main()
