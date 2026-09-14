"""Household composition counts for NY ZCTAs and Tompkins block groups (inputs to ecological propensity calibration).

Counts (ACS 2020-2024 5-year, occupied housing units):
  tenure x structure (B25032): own|rent x SFD, SFA, MF2_4, MF5_19, MF20P, MOBILE
  tenure x vehicles  (B25044): own|rent x 0..5+
  income bands       (B19001): <50k, 50-100k, 100-150k, 150k+
Outputs: data/processed/acs/composition_ny_zcta.parquet, composition_tompkins_bg.parquet
"""
from __future__ import annotations

import pandas as pd

from src.utils.paths import PROCESSED, RAW, ensure

ACS = RAW / "census" / "acs5_2024"
STRUCT_LINES = {"SFD": ([3], [14]), "SFA": ([4], [15]), "MF2_4": ([5, 6], [16, 17]), "MF5_19": ([7, 8], [18, 19]),
                "MF20P": ([9, 10], [20, 21]), "MOBILE": ([11, 12], [22, 23])}
INC = {"<50k": range(2, 12), "50-100k": [12, 13], "100-150k": [14, 15], "150k+": [16, 17]}


def composition(prefix: str) -> pd.DataFrame:
    def load(t):
        d = pd.read_parquet(ACS / f"{t}_ny.parquet")
        return d[d["GEO_ID"].str.startswith(prefix)].set_index("GEO_ID")
    b32, b44, b19 = load("b25032"), load("b25044"), load("b19001")
    out = pd.DataFrame(index=b32.index)
    for c, (own, rent) in STRUCT_LINES.items():
        out[f"own|{c}"] = sum(b32[f"B25032_E{l:03d}"].clip(lower=0) for l in own)
        out[f"rent|{c}"] = sum(b32[f"B25032_E{l:03d}"].clip(lower=0) for l in rent)
    for t, base in [("own", 3), ("rent", 10)]:
        for k in range(6):
            out[f"{t}|veh{k}"] = b44[f"B25044_E{base + k:03d}"].reindex(out.index).clip(lower=0)
    for b, ls in INC.items():
        out[f"inc|{b}"] = sum(b19[f"B19001_E{l:03d}"].reindex(out.index).clip(lower=0) for l in ls)
    out["households"] = b32["B25032_E001"].clip(lower=0)
    out = out.reset_index()
    out["geoid"] = out["GEO_ID"].str.split("US").str[-1]
    return out


def main() -> None:
    ensure(PROCESSED / "acs")
    z = composition("860Z200US")
    z.to_parquet(PROCESSED / "acs" / "composition_ny_zcta.parquet", index=False)
    b = composition("1500000US36109")
    b.to_parquet(PROCESSED / "acs" / "composition_tompkins_bg.parquet", index=False)
    print(z.shape, b.shape, round(z["households"].sum()))


if __name__ == "__main__":
    main()
