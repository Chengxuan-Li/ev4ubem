"""Prototype event-based home-charging profile library for building-level loads (model family B, home only).

Idea: represent each household EV by an *empirical user-year* of charging sessions (Norway residential dataset,
class C: real plug-in/plug-out behaviour and session energy), re-parameterised for Tompkins:
  1. Weekday alignment: 2019 sessions shifted by whole weeks (366) so day-of-week is preserved in 2026; year-end wraps.
  2. Energy scaling: each user's session kWh scaled so the user-year total equals the drivetrain's home energy target
     (BEV 2,915 x 0.80 home share ~ 2,330 kWh; PHEV 1,764 x 0.80 ~ 1,410 kWh — from hourly_load_scenarios base case).
     This keeps the user's timing and session frequency but not its absolute energy (assumption).
  3. Charging power: L1 = 1.4 kW, L2 = 7.2 kW assigned per EV with Drive Clean 2024 shares (BEV: 85 % L2 incl. 240 V
     outlets; PHEV: 32 % L2) (class B, rebate recipients). Charging immediate from plug-in; if kWh cannot be delivered
     within the connection at the assigned power, the undelivered energy is dropped and reported.
Outputs
  results/tables/home_event_library_building_peaks.csv  distribution of annual-peak hourly kW for buildings with
      N = 1, 2 (single-family), 6, 12, 24, 48 (multifamily garages) EVs; BEV/PHEV mix 57/43 (Tompkins 2026)
  results/tables/home_event_library_energy_check.csv    delivered vs target energy by charger level
  data/interim/home_event_library_2026.parquet          (git-ignored) 400 synthetic EV-year hourly profiles
Limitations: Norway apartment-garage users (not US single-family), one year (2019), no L1 users in the source,
timing not validated for NY homes (only NY MUD utilisation shape r=0.97).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.charging_sessions import clean, load_norway
from src.utils.paths import INTERIM, TABLES, ensure

RNG = np.random.default_rng(2026)
TARGET_HOME_KWH = {"BEV": 2915 * 0.80, "PHEV": 1764 * 0.80}
P_L2_SHARE = {"BEV": 0.85, "PHEV": 0.32}
POWER = {"L1": 1.4, "L2": 7.2}
YEAR = 2026


def user_sessions() -> dict[str, pd.DataFrame]:
    d, _ = clean(load_norway(3.6))
    w = d[(d["start"] >= "2019-01-01") & (d["start"] < "2020-01-01")]
    cnt = w.groupby("user").size()
    span = w.groupby("user")["start"].agg(lambda s: (s.max() - s.min()).days)
    keep = cnt[(cnt >= 60) & (span >= 300)].index
    return {u: g[["start", "conn_h", "kwh"]].reset_index(drop=True) for u, g in w[w["user"].isin(keep)].groupby("user")}


def ev_year(sess: pd.DataFrame, drivetrain: str, level: str) -> tuple[np.ndarray, float]:
    # Shift 2019 sessions by a whole number of weeks (366 weeks = 2,562 days) so day-of-week is preserved in YEAR;
    # sessions falling past year end wrap to the start of the year.
    base = pd.Timestamp("2019-01-01")
    y0 = pd.Timestamp(f"{YEAR}-01-01")
    weeks = int(np.ceil((y0 - base).days / 7))
    s_h = ((sess["start"] + pd.Timedelta(weeks=weeks)) - y0).dt.total_seconds().values / 3600
    s_h = np.mod(s_h, 8760)
    kwh = sess["kwh"].values * TARGET_HOME_KWH[drivetrain] / sess["kwh"].sum()
    p = POWER[level]
    charge_h = np.minimum(kwh / p, sess["conn_h"].values)
    delivered = charge_h * p
    e_h = s_h + charge_h
    ext = np.zeros(8760 + 80, dtype=np.float32)
    for k in range(0, int(np.ceil(e_h.max())) + 1):
        ext[k] = np.sum(np.clip(np.minimum(e_h, k + 1) - np.maximum(s_h, k), 0, 1)) * p
    prof = ext[:8760].copy()
    prof[: len(ext) - 8760] += ext[8760:]
    return prof, float(delivered.sum() / kwh.sum())


def main() -> None:
    ensure(TABLES, INTERIM)
    users = user_sessions()
    ids = list(users)
    lib, meta = [], []
    for i in range(400):
        dt = "BEV" if RNG.random() < 0.57 else "PHEV"
        lvl = "L2" if RNG.random() < P_L2_SHARE[dt] else "L1"
        u = ids[RNG.integers(len(ids))]
        prof, frac = ev_year(users[u], dt, lvl)
        lib.append(prof)
        meta.append({"ev": i, "drivetrain": dt, "level": lvl, "source_user": u, "delivered_fraction": frac, "annual_kwh": float(prof.sum())})
    L = np.vstack(lib)
    meta = pd.DataFrame(meta)
    idx = pd.date_range(f"{YEAR}-01-01", periods=8760, freq="h")
    pd.DataFrame(L.T, index=idx, columns=[f"ev{i}" for i in range(len(lib))]).to_parquet(INTERIM / "home_event_library_2026.parquet")
    (meta.groupby(["drivetrain", "level"]).agg(n=("ev", "size"), delivered_fraction_mean=("delivered_fraction", "mean"),
                                               annual_kwh_mean=("annual_kwh", "mean")).reset_index()
     .round(3).to_csv(TABLES / "home_event_library_energy_check.csv", index=False))

    rows = []
    for n in [1, 2, 6, 12, 24, 48]:
        peaks, means, evening = [], [], []
        for _ in range(300):
            sel = RNG.choice(len(lib), n, replace=False)
            agg = L[sel].sum(axis=0)
            peaks.append(agg.max()); means.append(agg.mean())
            evening.append(agg.reshape(-1)[(idx.hour >= 17) & (idx.hour <= 21)].mean())
        rows.append({"n_evs": n, "building_type": "single-family" if n <= 2 else "multifamily garage",
                     "peak_kw_p50": np.median(peaks), "peak_kw_p90": np.percentile(peaks, 90), "peak_kw_per_ev_p50": np.median(peaks) / n,
                     "mean_kw": np.mean(means), "mean_kw_17_22": np.mean(evening),
                     "peak_to_mean_p50": np.median(np.array(peaks) / np.array(means))})
    out = pd.DataFrame(rows)
    out.round(3).to_csv(TABLES / "home_event_library_building_peaks.csv", index=False)
    print(meta.groupby(["drivetrain", "level"]).delivered_fraction.mean().round(3).to_dict())
    print(out.round(2).to_string())


if __name__ == "__main__":
    main()
