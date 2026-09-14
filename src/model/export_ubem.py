r"""Export hourly EV charging load for the urban building energy model (UBEM) at dwelling-unit, parcel or block-group level.

Exact expected load via the profile basis written by src.model.load_assembly:
  L_d(t) = E^{BEV}_d(y) · Π_{k(d),BEV}(t) + E^{PHEV}_d(y) · Π_{k(d),PHEV}(t)       [kWh in hour t; = mean kW over the hour]
Parcel / building load = Σ_{d ∈ parcel} L_d(t). Non-residential site loads (public L2, DCFC, workplace, fleet) come from
the site summaries and county pools (per-site hourly = pool(t) × site share).
Usage:
  python -m src.model.export_ubem --year 2026 --level parcel [--own trend --chg base] [--parcels ID ...]
Outputs (git-ignored unless --sample):
  data/interim/ubem_export/ev_home_{level}_{year}_{own}_{chg}.parquet   rows = hour (0..8759), columns = entity ids (float32 kWh)
  data/processed/load/ubem_export_sample_{year}.parquet                  20 parcels spanning structure types (tracked sample)
Time: hour-beginning index in local standard time of calendar year `year` (weekday-aligned; TMYx weather).
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from src.model.load_assembly import G5, du_expectations, load_dus
from src.utils.paths import INTERIM, PROCESSED, ensure


def basis(year: int, chg: str) -> dict:
    z = np.load(INTERIM / "load" / f"class_profiles_{year}_{chg}.npz")
    out = {}
    for k in z.files:
        g, t, w, dt, loc = k.split("|")
        if loc == "home":
            out[(g, t, int(w), dt)] = z[k]
    return out


def export(year: int, level: str, own: str = "trend", chg: str = "base", parcels: list[str] | None = None) -> pd.DataFrame:
    du = load_dus()
    Eb, Ep = du_expectations(du, year, own)
    du["Eb"], du["Ep"] = Eb, Ep
    if parcels:
        du = du[du["parcel"].isin(parcels)]
    B = basis(year, chg)
    key = {"du": "du_id", "parcel": "parcel", "bg": "bg"}[level]
    cols = {}
    for ent, g in du.groupby(key):
        acc = np.zeros(8760, np.float32)
        for (gg, t, w), q in g.groupby(["g", "tenure", "workers"]):
            acc += q["Eb"].sum() * B[(gg, t, int(w), "BEV")] + q["Ep"].sum() * B[(gg, t, int(w), "PHEV")]
        cols[str(ent)] = acc
    return pd.DataFrame(cols)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--level", choices=["du", "parcel", "bg"], default="parcel")
    ap.add_argument("--own", default="trend")
    ap.add_argument("--chg", default="base")
    ap.add_argument("--parcels", nargs="*")
    ap.add_argument("--sample", action="store_true")
    a = ap.parse_args()
    if a.sample:
        du = load_dus()
        pe = du.groupby(["parcel", "structure"])["E_ev"].sum().reset_index().sort_values("E_ev", ascending=False)
        pick = pe.groupby("structure").head(4)["parcel"].tolist()[:20]
        df = export(a.year, "parcel", a.own, a.chg, pick)
        ensure(PROCESSED / "load")
        df.to_parquet(PROCESSED / "load" / f"ubem_export_sample_{a.year}.parquet")
        print(df.sum().round(0).to_dict())
        return
    df = export(a.year, a.level, a.own, a.chg, a.parcels)
    out = INTERIM / "ubem_export"
    ensure(out)
    df.to_parquet(out / f"ev_home_{a.level}_{a.year}_{a.own}_{a.chg}.parquet")
    print(df.shape, float(df.values.sum()))


if __name__ == "__main__":
    main()
