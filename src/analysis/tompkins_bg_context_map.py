"""Context map of Tompkins block-group attributes that drive sub-ZIP EV allocation (ACS 2020-2024; class A survey estimates).

Panels: owner-occupied share, share of housing units in 5+ unit structures, median household income, vehicles per
household, college-enrolled share of population. ZCTA outlines (CB 2020) and AFDC public charging stations overlaid.
CRS: data stored EPSG:4326; plotted in EPSG:32618 (UTM 18N). Rates/shares are mapped (not counts). Block groups with
MOE/estimate > 0.5 for the mapped share are hatched as unreliable.
Output: results/maps/tompkins_bg_context.png ; results/tables/tompkins_bg_context.csv
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from src.utils.paths import MAPS, PROCESSED, TABLES, ensure

PANELS = [("owner_share", "Owner-occupied share", "owner_share_moe"),
          ("mf5plus_share", "Units in 5+ unit structures", "mf5plus_share_moe"),
          ("med_hh_income", "Median household income ($)", "med_hh_income_moe"),
          ("veh_per_hh", "Vehicles per household", None),
          ("college_share", "College-enrolled share of population", "college_share_moe")]


def main() -> None:
    ensure(MAPS, TABLES)
    bg = gpd.read_file(PROCESSED / "geography" / "tompkins_bg.gpkg")
    acs = pd.read_parquet(PROCESSED / "acs" / "acs_features_tompkins_bg.parquet")
    g = bg.merge(acs, left_on="GEOID", right_on="geoid", how="left").to_crs(32618)
    z = gpd.read_file(PROCESSED / "geography" / "tompkins_area_zcta.gpkg").to_crs(32618)
    st = gpd.read_file(PROCESSED / "infrastructure" / "tompkins_afdc_stations.gpkg").to_crs(32618)
    st = st[(st["access_code"] == "public") & (st["status_code"] == "E")]
    cols = ["GEOID"] + [c for p in PANELS for c in (p[0], p[2]) if c] + ["households", "pop", "pop_density_km2"]
    g[cols].round(4).to_csv(TABLES / "tompkins_bg_context.csv", index=False)

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    for ax, (col, title, moe) in zip(axes.flat, PANELS):
        g.plot(column=col, ax=ax, legend=True, cmap="viridis", edgecolor="white", linewidth=0.2, missing_kwds={"color": "lightgrey"})
        if moe:
            unrel = g[(g[moe] / g[col].where(g[col] != 0)) > 0.5]
            if len(unrel):
                unrel.plot(ax=ax, facecolor="none", hatch="///", edgecolor="grey", linewidth=0)
        z.boundary.plot(ax=ax, color="black", linewidth=0.6)
        ax.set_title(title); ax.set_axis_off()
    ax = axes.flat[-1]
    g.plot(ax=ax, color="whitesmoke", edgecolor="grey", linewidth=0.2)
    z.boundary.plot(ax=ax, color="black", linewidth=0.6)
    st.plot(ax=ax, markersize=(st["ports_total"].clip(1, 20) * 6), color="tab:red", alpha=0.7)
    ax.set_title("Public open AFDC stations (size ~ ports) and ZCTAs"); ax.set_axis_off()
    fig.suptitle("Tompkins County block groups — ACS 2020–2024 (hatched: MOE > 50% of estimate); EPSG:32618")
    fig.tight_layout()
    fig.savefig(MAPS / "tompkins_bg_context.png", dpi=120)
    print("mapped BGs:", len(g), "public stations:", len(st))


if __name__ == "__main__":
    main()
