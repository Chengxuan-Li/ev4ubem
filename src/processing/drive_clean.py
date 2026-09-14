"""Summaries of NYSERDA Drive Clean Rebate applications (NY Open Data thd2-fu8y).

Rebates cover new BEV/PHEV purchases/leases at participating dealers (since 2017-03). They are a
flow of *rebated new vehicles*, not stock, and exclude used EVs, non-participating sales, and
out-of-state purchases. County field is as reported on the application.
Outputs (tracked):
  data/processed/drive_clean/rebates_county_year_type.csv
  data/processed/drive_clean/rebates_zip_year_type_ny.csv
  data/processed/drive_clean/rebates_tompkins_models.csv
"""
from __future__ import annotations

import pandas as pd

from src.utils.paths import PROCESSED, RAW, ensure

OUT = PROCESSED / "drive_clean"


def main() -> None:
    ensure(OUT)
    d = pd.read_parquet(RAW / "ny_open_data" / "drive_clean_rebates.parquet")
    d["year"] = d["submitted_date"].str[:4].astype(int)
    d["county"] = d["county"].str.upper().str.strip()
    d["rebate_amount_usd"] = pd.to_numeric(d["rebate_amount_usd"], errors="coerce")
    through = d["data_through_date"].max()[:10]
    (d.groupby(["county", "year", "ev_type", "transaction_type"]).agg(rebates=("zip", "size"), rebate_usd=("rebate_amount_usd", "sum"))
     .reset_index().assign(data_through=through).to_csv(OUT / "rebates_county_year_type.csv", index=False))
    (d.groupby(["zip", "year", "ev_type"]).size().rename("rebates").reset_index().assign(data_through=through)
     .to_csv(OUT / "rebates_zip_year_type_ny.csv", index=False))
    t = d[d["county"] == "TOMPKINS"]
    (t.groupby(["make", "model", "ev_type"]).size().rename("rebates").reset_index().sort_values("rebates", ascending=False)
     .assign(data_through=through).to_csv(OUT / "rebates_tompkins_models.csv", index=False))
    print("rebates", len(d), "tompkins", len(t), "through", through)


if __name__ == "__main__":
    main()
