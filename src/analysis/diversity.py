"""Coincidence / diversity of residential charging load vs number of aggregated EVs (evidence class C).

Data: Norway residential sessions (Zenodo 13896176), 267 users. Hourly energy per user from sessions with
immediate charging at constant power P (3.6 kW base; 7.2 kW sensitivity) — charging duration is imputed,
so absolute peaks depend on P; the *shape of the diversity curve* is the quantity of interest.
Method: restrict to users with >= 60 sessions over the analysis window (2019-01-01..2019-12-31 if
coverage allows, else each user's active span re-based to a common calendar year of hourly steps).
For N in {1,2,5,10,20,50,100,all}: 200 random draws of N users; per-EV annual-peak hourly kW = max_t(sum load)/N;
per-EV 99th-percentile hourly kW; mean kW per EV. Coincidence factor = peak(N)/ (N x mean individual peak).
Outputs: results/tables/diversity_norway_residential.csv, results/figures/diversity_norway_residential.png
Relevance: building-level (single-family: N=1-2; multifamily garages: N=10-50) vs feeder/ZIP (N>=100) loads.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analysis.charging_sessions import clean, load_norway
from src.utils.paths import FIGURES, TABLES, ensure

RNG = np.random.default_rng(7)


def user_hourly(d: pd.DataFrame, start: pd.Timestamp, hours: int) -> tuple[np.ndarray, list]:
    users = sorted(d["user"].unique())
    uidx = {u: i for i, u in enumerate(users)}
    M = np.zeros((len(users), hours), dtype=np.float32)
    s_h = (d["start"] - start).dt.total_seconds().values / 3600
    e_h = s_h + d["charge_h"].values
    p = d["power_kw"].values
    ui = d["user"].map(uidx).values
    for k in range(int(np.floor(s_h.min())), int(np.ceil(e_h.max())) + 1):
        if k < 0 or k >= hours:
            continue
        ov = np.clip(np.minimum(e_h, k + 1) - np.maximum(s_h, k), 0, 1) * p
        m = ov > 0
        np.add.at(M[:, k], ui[m], ov[m])
    return M, users


def curve(M: np.ndarray, label: str) -> pd.DataFrame:
    ind_peak = M.max(axis=1)
    rows = []
    n_users = M.shape[0]
    for n in [1, 2, 5, 10, 20, 50, 100, n_users]:
        if n > n_users:
            continue
        draws = 1 if n == n_users else 200
        pk, p99, mn, cf = [], [], [], []
        for _ in range(draws):
            sel = RNG.choice(n_users, n, replace=False)
            agg = M[sel].sum(axis=0)
            pk.append(agg.max() / n); p99.append(np.percentile(agg, 99) / n); mn.append(agg.mean() / n)
            cf.append(agg.max() / ind_peak[sel].sum())
        rows.append({"power_assumption": label, "n_evs": n, "draws": draws, "peak_kw_per_ev_mean": np.mean(pk),
                     "peak_kw_per_ev_p90": np.percentile(pk, 90), "p99_hour_kw_per_ev": np.mean(p99),
                     "mean_kw_per_ev": np.mean(mn), "coincidence_factor": np.mean(cf)})
    return pd.DataFrame(rows)


def main() -> None:
    ensure(TABLES, FIGURES)
    out = []
    for P, label in [(3.6, "3.6kW"), (7.2, "7.2kW")]:
        d, _ = clean(load_norway(P))
        win0, win1 = pd.Timestamp("2019-01-01"), pd.Timestamp("2020-01-01")
        w = d[(d["start"] >= win0) & (d["start"] < win1)]
        cnt = w.groupby("user").size()
        span = w.groupby("user")["start"].agg(lambda s: (s.max() - s.min()).days)
        keep = cnt[(cnt >= 60) & (span >= 300)].index
        w = w[w["user"].isin(keep)]
        M, users = user_hourly(w, win0, 8760)
        c = curve(M, label)
        c["n_users_pool"] = len(users)
        c["window"] = "2019"
        out.append(c)
    res = pd.concat(out)
    res.round(4).to_csv(TABLES / "diversity_norway_residential.csv", index=False)
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for lab, g in res.groupby("power_assumption"):
        ax.plot(g["n_evs"], g["peak_kw_per_ev_mean"], marker="o", label=f"annual peak hour, P={lab}")
        ax.plot(g["n_evs"], g["mean_kw_per_ev"], ls="--", label=f"mean, P={lab}")
    ax.set_xscale("log"); ax.set_xlabel("EVs aggregated (N)"); ax.set_ylabel("kW per EV (hourly average)")
    ax.set_title("Residential charging diversity (Norway sessions, class C)")
    ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(FIGURES / "diversity_norway_residential.png", dpi=140)
    print(res.round(3).to_string())


if __name__ == "__main__":
    main()
