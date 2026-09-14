"""Validate NYSERDA Drive Clean survey parameters and build a compact model-ready table + figure.

Input
  data/processed/drive_clean_surveys/survey_parameters.csv  (hand-transcribed from the CSE/NYSERDA PDFs;
  see docs/source_notes/nyserda_drive_clean_surveys.md, "Model-ready parameters")
  data/processed/acs/acs_features_ny_county.parquet          (ACS 2020-2024, for NY household shares)
Outputs
  results/tables/drive_clean_key_parameters.csv
  results/figures/drive_clean_charging_frequency.png
Evidence class: B-self-report (weighted surveys of new-EV rebate recipients) except rows marked derived (D).
No published charging parameter is broken down by housing type, tenure, income or region; the only
housing-related outputs here are respondent housing/tenure distributions and the derived
over/under-representation ratios versus NY households.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.paths import FIGURES, PROCESSED, TABLES, ensure

CSV = PROCESSED / "drive_clean_surveys" / "survey_parameters.csv"
COLUMNS = ["survey", "survey_year", "drivetrain", "segment_dimension", "segment_value", "parameter", "category",
           "value", "unit", "base_n", "page", "value_source", "note"]
FREQ = ["daily_or_almost_daily", "few_times_per_week", "about_once_per_week", "few_times_per_month_or_less", "never"]
GROUP = ["survey", "survey_year", "drivetrain", "segment_dimension", "segment_value", "parameter"]


def load() -> pd.DataFrame:
    df = pd.read_csv(CSV, dtype={"base_n": "Int64"})
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"missing columns: {missing}")
    return df


def validate(df: pd.DataFrame, tol: float = 3.0) -> pd.DataFrame:
    """Raise on hard errors; return a report of checked categorical groups."""
    errs = []
    if df["value"].isna().any() or not np.issubdtype(df["value"].dtype, np.number):
        errs.append("non-numeric or missing values")
    if not df["drivetrain"].isin(["BEV", "PHEV", "All"]).all():
        errs.append("bad drivetrain")
    if not df["value_source"].isin(["text", "figure", "table", "derived"]).all():
        errs.append("bad value_source")
    pct = df["unit"].isin(["percent", "percent_multiselect"])
    if ((df.loc[pct, "value"] < 0) | (df.loc[pct, "value"] > 100)).any():
        errs.append("percent outside [0, 100]")
    if df.duplicated(GROUP + ["category"]).any():
        errs.append("duplicate rows: " + str(df[df.duplicated(GROUP + ['category'], keep=False)][GROUP + ['category']].values[:5]))

    report = []
    single = df[df["unit"] == "percent"]
    # full category set is defined per (survey, parameter); groups holding only some categories are partial
    # (e.g. a text-only "overall own = 83%") and are not sum-checked.
    full = single.groupby(["survey", "parameter"])["category"].agg(lambda s: frozenset(s))
    for key, g in single.groupby(GROUP):
        cats = frozenset(g["category"])
        if len(cats) < 2 or cats != full[(key[0], key[5])]:
            continue
        total = g["value"].sum()
        ok = abs(total - 100) <= tol
        report.append(dict(zip(GROUP, key), n_categories=len(cats), sum=round(total, 2), ok=ok))
        if not ok:
            errs.append(f"distribution does not sum to ~100: {key} -> {total}")
    for key, g in df[df["unit"] == "percent_multiselect"].groupby(GROUP):
        total = g["value"].sum()
        report.append(dict(zip(GROUP, key), n_categories=len(g), sum=round(total, 2), ok=total >= 95))
        if total < 95:
            errs.append(f"multi-select shares sum < 95 (someone must use a method): {key}")
    if errs:
        raise ValueError("survey_parameters.csv failed validation:\n  " + "\n  ".join(errs))
    return pd.DataFrame(report)


KEY_PARAMS = [
    ("home_access", "home_charging_status"),
    ("home_frequency", "charging_frequency_home"),
    ("home_frequency", "home_charging_few_per_week_or_more"),
    ("home_method", "home_charging_method"),
    ("home_method", "home_charging_method_current_or_planned"),
    ("workplace", "workplace_charging_access"),
    ("workplace", "workplace_charging_access_any"),
    ("workplace", "workplace_charging_use_any_given_access"),
    ("workplace", "charging_frequency_workplace_onsite"),
    ("public", "charging_frequency_public"),
    ("public", "public_charging_any_use"),
    ("driving", "miles_per_day_mean"),
    ("driving", "total_miles_since_acquisition_mean"),
    ("fleet", "technology_share"),
    ("fleet", "vehicle_replacement_status"),
    ("fleet", "first_ev_ever"),
    ("respondent_housing", "residence_type"),
    ("respondent_housing", "tenure"),
]


def key_table(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["survey"].isin(["ownership", "adoption"])].copy()
    out = []
    for block, param in KEY_PARAMS:
        sub = d[d["parameter"] == param]
        if sub.empty:
            continue
        idx = ["survey", "survey_year", "segment_dimension", "segment_value", "parameter", "category", "unit"]
        wide = sub.pivot_table(index=idx, columns="drivetrain", values="value", aggfunc="first").reset_index()
        meta = sub.groupby(idx).agg(base_n=("base_n", "max"),
                                    value_source=("value_source", lambda s: "|".join(sorted(set(s)))),
                                    note=("note", lambda s: "; ".join(sorted({x for x in s.dropna() if x})))).reset_index()
        wide = wide.merge(meta, on=idx)
        wide.insert(0, "block", block)
        out.append(wide)
    t = pd.concat(out, ignore_index=True)
    for c in ["BEV", "PHEV", "All"]:
        if c not in t:
            t[c] = np.nan
    t["housing_type_or_tenure_breakdown_published"] = np.where(t["block"] == "respondent_housing", "dac_only", "no")
    return pd.concat([t, derived_rows(df)], ignore_index=True)


def ny_household_shares() -> dict[str, float]:
    """NY statewide household shares from ACS 2020-2024 county features (household-weighted)."""
    c = pd.read_parquet(PROCESSED / "acs" / "acs_features_ny_county.parquet")
    w = c["households"]
    s = {k: float((c[k] * w).sum() / w.sum()) for k in
         ["owner_share", "sf_detached_share", "sf_attached_share", "mf2_4_share", "mf5plus_share", "mobile_home_share"]}
    return {
        "detached_house": s["sf_detached_share"],
        "attached_house": s["sf_attached_share"],
        "apartment_condominium": s["mf2_4_share"] + s["mf5plus_share"],
        "other": 1 - s["sf_detached_share"] - s["sf_attached_share"] - s["mf2_4_share"] - s["mf5plus_share"],
        "own": s["owner_share"],
        "rent": 1 - s["owner_share"],
    }


def derived_rows(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    base = dict(segment_dimension="all", segment_value="all", value_source="derived",
                housing_type_or_tenure_breakdown_published="no")
    # 1) any-240V home access among home chargers: bounds from multi-select shares (overlap unpublished)
    for (survey, year, param), g in df[df["unit"] == "percent_multiselect"].groupby(["survey", "survey_year", "parameter"]):
        for dt, gg in g.groupby("drivetrain"):
            v = gg.set_index("category")["value"]
            l2, o240 = v["level2_240v_station"], v["outlet_240v_direct"]
            for cat, val in [("any_240v_lower_bound", max(l2, o240)), ("any_240v_upper_bound", min(100.0, l2 + o240))]:
                rows.append(dict(base, block="home_method", survey=survey, survey_year=year, parameter=param + "_any_240v",
                                 category=cat, unit="percent_of_home_chargers", **{dt: val},
                                 note="D: max(L2 station, 240V outlet) .. min(100, sum); true overlap not published"))
    # 2) over/under-representation of housing type & tenure among respondents vs NY households (ACS 2020-2024)
    ny = ny_household_shares()
    for survey, year in [("ownership", 2024), ("ownership", 2023), ("adoption", 2025), ("adoption", 2024)]:
        for param in ["residence_type", "tenure"]:
            g = df[(df.survey == survey) & (df.survey_year == year) & (df.parameter == param) & (df.segment_dimension == "all")]
            dt = "All" if (g.drivetrain == "All").sum() >= 3 else None
            if dt is None:  # only BEV/PHEV published -> combine with the survey's own technology shares
                ts = df[(df.survey == survey) & (df.survey_year == year) & (df.parameter == "technology_share")
                        & (df.segment_dimension == "all")].set_index("category")["value"] / 100
                p = (g.pivot_table(index="category", columns="drivetrain", values="value") * ts).sum(axis=1)
                src_note = "combined from BEV/PHEV shares weighted by technology share"
            else:
                p = g[g.drivetrain == "All"].set_index("category")["value"]
                src_note = "survey All"
            cats = ["own", "rent"] if param == "tenure" else list(p.index)
            p = p[cats] / p[cats].sum()  # renormalise (drops 'neither' for tenure)
            for cat in cats:
                rows.append(dict(base, block="relative_propensity_vs_ny_acs", survey=survey, survey_year=year,
                                 parameter=param + "_share_ratio_respondents_vs_ny_households", category=cat,
                                 unit="ratio", All=round(float(p[cat] / ny[cat]), 3),
                                 note=(f"D: respondent share {p[cat]:.3f} / NY ACS 2020-2024 household share {ny[cat]:.3f}; "
                                       f"{src_note}; = P(rebate|type)/P(rebate) only if survey is unbiased; survey 'attached "
                                       "house' includes duplex/triplex which ACS counts as 2-4 units; new-vehicle rebate "
                                       "recipients only")))
    return pd.DataFrame(rows)


def figure(df: pd.DataFrame) -> None:
    locs = [("charging_frequency_home", "Home"), ("charging_frequency_workplace_onsite", "Work on-site*"),
            ("charging_frequency_public", "Public")]
    colors = ["#0d366b", "#1c5cab", "#3987e5", "#86b6ef", "#e1e0d9"]
    labels = ["Daily or almost daily", "A few times per week", "About once per week", "A few times a month or less", "Never"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    for ax, year in zip(axes, [2023, 2024]):
        ylabels, ypos = [], []
        y = 0
        for param, name in locs:
            for dt in ["BEV", "PHEV"]:
                g = df[(df.survey == "ownership") & (df.survey_year == year) & (df.parameter == param)
                       & (df.drivetrain == dt)].set_index("category")["value"].reindex(FREQ)
                left = 0.0
                for k, (cat, v) in enumerate(g.items()):
                    ax.barh(y, v, left=left, color=colors[k], edgecolor="#fcfcfb", linewidth=2, height=0.72)
                    if v >= 8:
                        ax.text(left + v / 2, y, f"{v:.0f}", ha="center", va="center", fontsize=8,
                                color="#ffffff" if k < 3 else "#0b0b0b")
                    left += v
                ylabels.append(f"{name} - {dt}")
                ypos.append(y)
                y += 1
            y += 0.5
        ax.set_yticks(ypos, ylabels, fontsize=9, color="#52514e")
        ax.set_xlim(0, 100)
        ax.set_xlabel("% of respondents (weighted)", color="#52514e", fontsize=9)
        ax.set_title(f"Vehicles acquired {year} (surveyed ~1 yr later)", fontsize=10, color="#0b0b0b", loc="left")
        for s in ["top", "right", "left"]:
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#c3c2b7")
        ax.tick_params(colors="#898781", length=0)
    axes[0].invert_yaxis()  # shared y-axis: invert once only
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors]
    fig.legend(handles, labels, loc="upper center", ncol=5, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, 0.93))
    fig.suptitle("NYSERDA Drive Clean Ownership Survey: charging frequency by location", fontsize=12, x=0.01, ha="left", y=0.995)
    fig.text(0.01, 0.01, "B-self-report: weighted web survey of NY new-EV rebate recipients (n=6,542 for 2023, 4,869 for 2024; "
             "\n*work on-site base = respondents with workplace access, n=1,212 / 912).\n"
             "Values from report figures; some small segments pixel-measured. Not published by housing type, tenure, income or region. Public L2 vs DCFC not "
             "distinguished.",
             fontsize=7.5, color="#52514e")
    fig.tight_layout(rect=(0, 0.1, 1, 0.9))
    fig.savefig(FIGURES / "drive_clean_charging_frequency.png", dpi=150, facecolor="#fcfcfb")
    plt.close(fig)


def main() -> None:
    ensure(TABLES, FIGURES)
    df = load()
    rep = validate(df)
    print(f"validated {len(df)} rows; {int(rep.ok.sum())}/{len(rep)} categorical groups within tolerance")
    t = key_table(df)
    cols = ["block", "survey", "survey_year", "segment_dimension", "segment_value", "parameter", "category", "BEV", "PHEV",
            "All", "unit", "base_n", "value_source", "housing_type_or_tenure_breakdown_published", "note"]
    t[cols].to_csv(TABLES / "drive_clean_key_parameters.csv", index=False)
    figure(df)


if __name__ == "__main__":
    main()
