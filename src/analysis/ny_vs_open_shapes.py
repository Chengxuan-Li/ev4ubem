"""Check non-NY session-derived weekday charging shapes (class C) against NYSERDA 22-03 Figure 18 (class B).

NY reference: weekday % of plugs actively charging at anchor hours 0,3,...,21 (figure-read, 2018-2019),
data/processed/nyserda_2203/fig18_weekday_charging_utilization_anchor_hours.csv.
Open-data analogue: for each dataset, the weekday mean number of sessions *actively charging* in each clock hour
(immediate charging from plug-in for charge_h), per station-day is unknown, so shapes are compared after
normalising each curve to its own maximum over the 8 anchor hours (shape only, not utilisation level).
Mapping: workplace <- workplace_midwest L2; public <- boulder_public L2, palo_alto_public L2; mud <- norway_residential L2_home.
Metrics: Pearson r and mean absolute difference of peak-normalised anchor values; hour of maximum.
Outputs: results/tables/ny_vs_open_weekday_shapes.csv, results/tables/ny_vs_open_weekday_shape_metrics.csv,
         results/figures/ny_vs_open_weekday_shapes.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analysis.charging_sessions import clean, load_boulder, load_norway, load_palo_alto, load_workplace
from src.utils.paths import FIGURES, PROCESSED, TABLES, ensure

ANCHORS = [0, 3, 6, 9, 12, 15, 18, 21]


def charging_by_hour(d: pd.DataFrame) -> np.ndarray:
    d = d[~d["weekend"]]
    s = d["start"].dt.hour.values + d["start"].dt.minute.values / 60
    e = s + d["charge_h"].values
    acc = np.zeros(24)
    for k in range(0, 73):
        acc[k % 24] += np.clip(np.minimum(e, k + 1) - np.maximum(s, k), 0, 1).sum()
    return acc


def main() -> None:
    ensure(TABLES, FIGURES)
    ny = pd.read_csv(PROCESSED / "nyserda_2203" / "fig18_weekday_charging_utilization_anchor_hours.csv", comment="#")
    ny = ny.groupby(["land_use", "hour"], as_index=False)["pct_charging"].mean()  # mean of 2018 and 2019
    open_sets = {"workplace": [("workplace_midwest L2", load_workplace, None)],
                 "public": [("boulder_public L2", load_boulder, "L2"), ("palo_alto_public L2", load_palo_alto, "L2")],
                 "mud": [("norway_residential home", load_norway, None)]}
    rows, metrics = [], []
    for lu, sets in open_sets.items():
        ref = ny[ny["land_use"] == lu].set_index("hour").loc[ANCHORS, "pct_charging"].values
        refn = ref / ref.max()
        for h, v, vn in zip(ANCHORS, ref, refn):
            rows.append({"land_use": lu, "source": "NYSERDA 22-03 Fig.18 (2018-19 mean)", "hour": h, "value": v, "peak_normalised": vn})
        for name, fn, pt in sets:
            d, _ = clean(fn())
            if pt:
                d = d[d["port_type"] == pt]
            c = charging_by_hour(d)
            a = c[ANCHORS]
            an = a / a.max()
            for h, v, vn in zip(ANCHORS, a, an):
                rows.append({"land_use": lu, "source": name, "hour": h, "value": v, "peak_normalised": vn})
            metrics.append({"land_use": lu, "open_source": name, "pearson_r": float(np.corrcoef(refn, an)[0, 1]),
                            "mean_abs_diff_peak_norm": float(np.mean(np.abs(refn - an))),
                            "ny_anchor_max_hour": ANCHORS[int(np.argmax(ref))], "open_anchor_max_hour": ANCHORS[int(np.argmax(a))],
                            "open_hourly_max_hour": int(np.argmax(c))})
    r = pd.DataFrame(rows)
    r.round(4).to_csv(TABLES / "ny_vs_open_weekday_shapes.csv", index=False)
    m = pd.DataFrame(metrics)
    m.round(3).to_csv(TABLES / "ny_vs_open_weekday_shape_metrics.csv", index=False)
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), sharey=True)
    for ax, lu in zip(axes, ["workplace", "public", "mud"]):
        for src, g in r[r["land_use"] == lu].groupby("source"):
            ax.plot(g["hour"], g["peak_normalised"], marker="o", ls="-" if src.startswith("NYSERDA") else "--", label=src)
        ax.set_title(f"{lu}: weekday charging (peak-normalised)"); ax.set_xticks(ANCHORS); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIGURES / "ny_vs_open_weekday_shapes.png", dpi=140)
    print(m.round(3).to_string())


if __name__ == "__main__":
    main()
