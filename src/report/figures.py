"""Report figures that combine model outputs (maps, profiles, scenario trajectories, validation panels).

Run after src.model.load_assembly (all scenarios). Figures are written to results/figures/report_*.png and
results/maps/report_*.png. CRS for maps: EPSG:32618.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.paths import FIGURES, MAPS, PROCESSED, TABLES, ensure

LOC_COLORS = {"home": "tab:blue", "work": "tab:orange", "public_l2": "tab:green", "dcfc": "tab:red", "fleet": "tab:purple", "passerby": "tab:brown"}


def synthetic_validation():
    v = pd.read_csv(TABLES / "synthetic_dwellings_validation_bg.csv")
    fig, ax = plt.subplots(1, 3, figsize=(13, 4))
    for a, (mg, t) in zip(ax, [("tenure_structure", "tenure × structure"), ("tenure_vehicles", "tenure × vehicles"), ("income", "income band")]):
        q = v[v["margin"] == mg]
        a.scatter(q["acs"], q["synthetic"], s=8, alpha=0.5)
        m = max(q["acs"].max(), q["synthetic"].max())
        a.plot([0, m], [0, m], "k--", lw=0.8)
        r2 = 1 - ((q["acs"] - q["synthetic"]) ** 2).sum() / ((q["acs"] - q["acs"].mean()) ** 2).sum()
        a.set_title(f"{t}: R² = {r2:.3f} ({len(q)} BG cells)"); a.set_xlabel("ACS 2020–2024 households"); a.set_ylabel("synthetic dwelling units")
    fig.suptitle("Synthetic dwelling units vs ACS block-group marginals (Tompkins, 65 BGs)")
    fig.tight_layout(); fig.savefig(FIGURES / "report_synthetic_population_validation.png", dpi=140); plt.close(fig)


def scenario_trajectories():
    s = pd.read_csv(TABLES / "load_scenarios_annual.csv")
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
    for own, col in zip(["trend", "slow", "stall", "policy"], ["tab:blue", "tab:orange", "tab:grey", "tab:green"]):
        q = s[(s["ownership_scenario"] == own) & (s["charging_scenario"] == "base")].sort_values("year")
        ax[0].plot(q["year"], q["annual_mwh_total"] / 1000, "-o", color=col, label=own)
        ax[1].plot(q["year"], q["peak_mw_total"], "-o", color=col, label=own)
    for chg, ls in zip(["base", "access+", "managed"], ["-", "--", ":"]):
        q = s[(s["ownership_scenario"] == "trend") & (s["charging_scenario"] == chg)].sort_values("year")
        ax[2].plot(q["year"], q["peak_mw_total"], ls, marker="o", label=f"trend / {chg}")
    ax[0].set_title("County EV charging energy (GWh/yr), charging=base"); ax[0].legend()
    ax[1].set_title("County peak hourly load (MW), charging=base"); ax[1].legend()
    ax[2].set_title("Peak hourly load by charging scenario (ownership=trend)"); ax[2].legend()
    fig.tight_layout(); fig.savefig(FIGURES / "report_scenario_trajectories.png", dpi=140); plt.close(fig)
    q = s[(s["ownership_scenario"] == "trend") & (s["charging_scenario"] == "base")].sort_values("year")
    locs = [c for c in s.columns if c.startswith("annual_mwh_") and c != "annual_mwh_total"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bottom = np.zeros(len(q))
    for c in locs:
        loc = c.replace("annual_mwh_", "")
        ax.bar(q["year"].astype(str), q[c] / 1000, bottom=bottom, color=LOC_COLORS.get(loc), label=loc)
        bottom += q[c].values / 1000
    ax.set_ylabel("GWh/yr"); ax.set_title("Charging energy by location, ownership=trend, charging=base"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIGURES / "report_energy_by_location.png", dpi=140); plt.close(fig)


def hourly_profiles():
    fig, axes = plt.subplots(2, 3, figsize=(16, 8), sharey="row")
    for row, (own, chg) in enumerate([("trend", "base"), ("trend", "managed")]):
        for col, year in enumerate([2026, 2035, 2050]):
            p = PROCESSED / "load" / f"county_hourly_{year}_{own}_{chg}.parquet"
            if not p.exists():
                continue
            c = pd.read_parquet(p)
            hrs = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
            ax = axes[row, col]
            for season, months, ls in [("winter (DJF)", [12, 1, 2], "-"), ("summer (JJA)", [6, 7, 8], "--")]:
                m = hrs.month.isin(months) & (hrs.dayofweek < 5)
                bottom = np.zeros(24)
                if season.startswith("winter"):
                    for loc in c.columns:
                        prof = c.loc[m, loc].groupby(hrs[m].hour).mean().values / 1000
                        ax.fill_between(range(24), bottom, bottom + prof, color=LOC_COLORS.get(loc), alpha=0.6, label=loc if col == 0 else None)
                        bottom = bottom + prof
                else:
                    tot = c.loc[m].sum(axis=1).groupby(hrs[m].hour).mean().values / 1000
                    ax.plot(range(24), tot, "k--", label="summer total" if col == 0 else None)
            ax.set_title(f"{year}, ownership={own}, charging={chg}: winter weekday (stacked)")
            ax.set_xlabel("hour (local standard time)")
        axes[row, 0].set_ylabel("MW (mean weekday)")
    axes[0, 0].legend(fontsize=7, loc="upper left")
    fig.tight_layout(); fig.savefig(FIGURES / "report_hourly_profiles.png", dpi=130); plt.close(fig)


def bg_maps():
    bg = gpd.read_file(PROCESSED / "geography" / "tompkins_bg.gpkg")
    du = pd.read_parquet(PROCESSED / "synthetic" / "dwelling_units.parquet").groupby("bg").size().rename("households")
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    vmax = None
    data = {}
    for year in [2026, 2035, 2050]:
        p = PROCESSED / "load" / f"bg_home_hourly_{year}_trend_base.parquet"
        if p.exists():
            h = pd.read_parquet(p)
            data[year] = pd.DataFrame({"bg": h.columns, "annual_mwh": h.sum().values / 1000, "peak_kw": h.max().values})
    if not data:
        return
    vmax = max(d["annual_mwh"].max() for d in data.values())
    for ax, (year, d) in zip(axes, data.items()):
        g = bg.rename(columns={"GEOID": "bg"}).merge(d, on="bg").merge(du, left_on="bg", right_index=True).to_crs(32618)
        g["kwh_per_hh"] = g["annual_mwh"] * 1000 / g["households"]
        g.plot(column="kwh_per_hh", ax=ax, legend=True, cmap="viridis", vmin=0, vmax=np.nanpercentile(pd.concat(data.values())["annual_mwh"] * 1000 / du.reindex(pd.concat(data.values())["bg"]).values, 97),
               edgecolor="w", linewidth=0.2)
        ax.set_title(f"{year}: expected home EV charging kWh per household"); ax.set_axis_off()
    fig.suptitle("Residential EV charging by block group (ownership=trend, charging=base; inferred; EPSG:32618)")
    fig.tight_layout(); fig.savefig(MAPS / "report_bg_home_energy.png", dpi=130); plt.close(fig)


def parcel_peaks():
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
    du = pd.read_parquet(PROCESSED / "synthetic" / "dwelling_units.parquet")
    struct = du.groupby("parcel")["structure"].agg(lambda s: s.mode().iloc[0])
    units = du.groupby("parcel").size().rename("units")
    for year, col in [(2026, "tab:blue"), (2035, "tab:red")]:
        p = PROCESSED / "load" / f"parcel_summary_{year}_trend_base.csv"
        if not p.exists():
            continue
        s = pd.read_csv(p).join(struct, on="parcel").join(units, on="parcel")
        s = s[(s["prob_any_ev_charging"] > 0) & (s["E_ev"] > 0) & (s["peak_kw_p90"] > 0)]
        for st, mk in [("SFD", "o"), ("MF20P", "s")]:
            q = s[s["structure"] == st]
            ax[0].scatter(q["E_ev"], q["peak_kw_p90"], s=6, alpha=0.4, marker=mk, color=col, label=f"{year} {st}")
        g = s.groupby(pd.cut(s["units"], [0, 1, 2, 4, 19, 49, 1000]), observed=True)[["peak_kw_p50", "peak_kw_p90", "E_ev"]].mean()
        ax[1].plot(range(len(g)), g["peak_kw_p90"], "-o", color=col, label=f"{year} p90 peak")
        ax[1].plot(range(len(g)), g["peak_kw_p50"], "--o", color=col, label=f"{year} p50 peak")
        ax[1].set_xticks(range(len(g))); ax[1].set_xticklabels([str(i) for i in g.index], rotation=20)
    ax[0].set_xlabel("expected EVs on parcel"); ax[0].set_ylabel("annual peak hourly kW (p90 of realizations)"); ax[0].set_xscale("log"); ax[0].legend(fontsize=7)
    ax[0].set_title("Parcel home-charging peak vs expected EVs")
    ax[1].set_xlabel("dwelling units on parcel"); ax[1].set_ylabel("kW"); ax[1].legend(fontsize=7); ax[1].set_title("Mean annual peak by parcel size (parcels with EVs)")
    fig.tight_layout(); fig.savefig(FIGURES / "report_parcel_peaks.png", dpi=140); plt.close(fig)


def sites():
    p = PROCESSED / "load" / "site_summary_2026_trend_base.csv"
    s = pd.read_csv(p)
    g = s.groupby("site_type").agg(sites=("site_id", "size"), annual_mwh=("annual_kwh", lambda x: x.sum() / 1000), max_site_peak_kw=("peak_kw", "max")).reset_index()
    g.round(2).to_csv(TABLES / "report_site_types_2026.csv", index=False)
    st = gpd.GeoDataFrame(s.dropna(subset=["lat", "lon"]), geometry=gpd.points_from_xy(s.dropna(subset=["lat", "lon"])["lon"], s.dropna(subset=["lat", "lon"])["lat"]), crs=4326).to_crs(32618)
    bg = gpd.read_file(PROCESSED / "geography" / "tompkins_bg.gpkg").to_crs(32618)
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    bg.plot(ax=ax, color="whitesmoke", edgecolor="grey", linewidth=0.3)
    for t, col in [("public_l2", "tab:green"), ("dcfc", "tab:red"), ("workplace_listed", "tab:orange"), ("workplace_unlisted_parcel", "gold")]:
        q = st[st["site_type"] == t]
        ax.scatter(q.geometry.x, q.geometry.y, s=np.clip(q["annual_kwh"] / 400, 3, 300), color=col, alpha=0.6, label=t)
    ax.legend(fontsize=8); ax.set_axis_off(); ax.set_title("2026 non-residential charging sites (size ∝ annual kWh; inferred)")
    fig.tight_layout(); fig.savefig(MAPS / "report_sites_2026.png", dpi=130); plt.close(fig)


def model_overview():
    boxes = [
        (0.02, 0.70, "Observed stock\nDMV 2026 VIN-decoded\n(ZIP × BEV/PHEV × class)", "A"),
        (0.02, 0.40, "Synthetic dwelling units\nparcels × ACS BG × PUMS\n(43,251 DUs)", "A/D"),
        (0.02, 0.10, "Growth model\nlogistic sales share + survival\n2026–2050 scenarios", "D→E"),
        (0.30, 0.55, "Propensity & allocation\necological NY ZIP fit +\nNHTS evidence ensemble", "B/C"),
        (0.30, 0.15, "Evolution\nZIP/propensity convergence\n(φ = 0.90 per doubling)", "D"),
        (0.56, 0.70, "Charging parameters(y)\naccess, L1/L2, frequency,\nworkplace, managed, efficiency", "B/C"),
        (0.56, 0.35, "Event library\nEV-years per archetype\nenergy ledger + TMYx", "C"),
        (0.80, 0.55, "Load assembly\nDU/parcel/BG hourly +\nsites (public, DCFC, work, fleet)", "inferred"),
        (0.80, 0.15, "Validation\nNY 22-03, ChargePoint, Drive Clean,\nNorway diversity, TEMPO (benchmark)", "B/C/E"),
    ]
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    centers = {}
    for x, y, txt, ev in boxes:
        ax.add_patch(plt.Rectangle((x, y), 0.18, 0.22, facecolor="#eef3fb", edgecolor="#335", lw=1))
        ax.text(x + 0.09, y + 0.13, txt, ha="center", va="center", fontsize=8.5)
        ax.text(x + 0.09, y + 0.02, f"evidence: {ev}", ha="center", va="bottom", fontsize=7, color="#555")
        centers[txt.split("\n")[0]] = (x, y)
    arrows = [("Observed stock", "Propensity & allocation"), ("Synthetic dwelling units", "Propensity & allocation"),
              ("Growth model", "Evolution"), ("Propensity & allocation", "Evolution"), ("Propensity & allocation", "Load assembly"),
              ("Evolution", "Load assembly"), ("Charging parameters(y)", "Event library"), ("Event library", "Load assembly"),
              ("Load assembly", "Validation")]
    for a, b in arrows:
        xa, ya = centers[a]; xb, yb = centers[b]
        ax.annotate("", xy=(xb, yb + 0.11), xytext=(xa + 0.18, ya + 0.11), arrowprops=dict(arrowstyle="->", color="#335"))
    ax.set_title("Tompkins EV ownership and charging load model: structure and evidence")
    fig.tight_layout(); fig.savefig(FIGURES / "report_model_overview.png", dpi=140); plt.close(fig)


def main() -> None:
    ensure(FIGURES, MAPS, TABLES)
    for fn in [model_overview, synthetic_validation, scenario_trajectories, hourly_profiles, bg_maps, parcel_peaks, sites]:
        try:
            fn()
            print("ok", fn.__name__)
        except Exception as exc:  # noqa: BLE001
            print("FAILED", fn.__name__, exc)


if __name__ == "__main__":
    main()
