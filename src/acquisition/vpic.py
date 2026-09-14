"""Decode VIN patterns with the public NHTSA vPIC API (no key) to classify drivetrain (BEV/PHEV/HEV/ICE).

For each VIN pattern key (VIN chars 1-8 + 10-11) we decode one representative full VIN via
DecodeVINValuesBatch (50 VINs/request). Results are cached incrementally so reruns resume.

Inputs: row-level DMV extracts (which contain full VINs):
  data/raw/ny_open_data/dmv_reg_tompkins_area_veh.parquet  (all fuels, MY>=2010)
  data/raw/ny_open_data/dmv_reg_ny_electric.parquet         (fuel_type=ELECTRIC statewide)
  optionally extra keys (see decode_keys) for statewide PHEV identification
Output cache: data/raw/vpic/vpic_decoded.parquet ; compact lookup exported by processing step.
"""
from __future__ import annotations

import argparse
import time

import pandas as pd
import requests

from src.utils.paths import RAW, ensure
from src.utils.provenance import UA, record, rel, sha256

URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/"
KEEP = ["VIN", "Make", "Model", "ModelYear", "Trim", "BodyClass", "VehicleType", "GVWR", "ElectrificationLevel",
        "FuelTypePrimary", "FuelTypeSecondary", "BatteryKWh", "BatteryType", "ChargerLevel", "ChargerPowerKW",
        "EVDriveUnit", "ErrorCode"]
CACHE = RAW / "vpic" / "vpic_decoded.parquet"


def key11(vin: pd.Series) -> pd.Series:
    return vin.str[:8] + vin.str[9:11]


def representatives(df: pd.DataFrame) -> pd.DataFrame:
    v = df[df["vin"].fillna("").str.len() == 17].copy()
    v["vin_key11"] = key11(v["vin"])
    return v.drop_duplicates("vin_key11")[["vin_key11", "vin"]]


def decode(reps: pd.DataFrame, batch: int = 50, sleep: float = 0.3) -> pd.DataFrame:
    ensure(CACHE.parent)
    cache = pd.read_parquet(CACHE) if CACHE.exists() else pd.DataFrame(columns=["vin_key11"] + KEEP)
    todo = reps[~reps["vin_key11"].isin(cache["vin_key11"])]
    print(f"vPIC: {len(reps)} keys, {len(todo)} to decode")
    rows = []
    for i in range(0, len(todo), batch):
        chunk = todo.iloc[i:i + batch]
        for attempt in range(5):
            try:
                r = requests.post(URL, data={"format": "json", "data": ";".join(chunk["vin"])}, headers=UA, timeout=180)
                r.raise_for_status()
                res = r.json()["Results"]
                break
            except Exception as exc:  # noqa: BLE001
                print("  retry", attempt, exc)
                time.sleep(10 * (attempt + 1))
        else:
            raise RuntimeError("vPIC failed")
        for k, x in zip(chunk["vin_key11"], res):
            rows.append({"vin_key11": k, **{c: x.get(c, "") for c in KEEP}})
        if (i // batch) % 20 == 19 or i + batch >= len(todo):
            cache = pd.concat([cache, pd.DataFrame(rows)], ignore_index=True)
            rows = []
            out = cache.copy()
            out["VIN"] = out["VIN"].str[:11] + "******"  # don't retain full representative VINs
            out.to_parquet(CACHE, index=False)
            print(f"  decoded {min(i + batch, len(todo))}/{len(todo)}")
        time.sleep(sleep)
    return cache


def wildcard_vin(key11: pd.Series) -> pd.Series:
    """Build a decodable partial VIN from a pattern key: VIN[:8] + '*' (check digit) + VIN[9:11] + '******'.
    vPIC decodes such partial VINs (ErrorCode 1 'check digit' warning only; verified 2026-09-14)."""
    return key11.str[:8] + "*" + key11.str[8:10] + "******"


def main(extra_keys_file: str | None = None, statewide: bool = False) -> None:
    src = RAW / "ny_open_data"
    parts = []
    t = pd.read_parquet(src / "dmv_reg_tompkins_area_veh.parquet", columns=["vin", "model_year"])
    parts.append(representatives(t[pd.to_numeric(t["model_year"], errors="coerce") >= 2010]))
    parts.append(representatives(pd.read_parquet(src / "dmv_reg_ny_electric.parquet", columns=["vin"])))
    if extra_keys_file:
        parts.append(pd.read_parquet(extra_keys_file)[["vin_key11", "vin"]])
    if statewide:
        # statewide MY>=2011 VIN patterns absent from EValuateNY's lookup, decoded via wildcard partial VINs
        full = pd.read_parquet(src / "dmv_reg_ny_veh_full_compact.parquet", columns=["vin_key11", "model_year"])
        keys = full.loc[(full["model_year"] >= 2011) & full["vin_key11"].notna(), "vin_key11"].drop_duplicates()
        vd = pd.read_csv(RAW / "nyserda" / "evaluateny_v11" / "Vehicle Description.csv", dtype=str, low_memory=False,
                         usecols=["VIN_Key"])
        keys = keys[~keys.str[:9].isin(set(vd["VIN_Key"]))]
        parts.append(pd.DataFrame({"vin_key11": keys, "vin": wildcard_vin(keys)}))
    reps = pd.concat(parts).drop_duplicates("vin_key11")
    decode(reps)
    record("vpic", {"local_path": rel(CACHE), "url": URL, "params": {"method": "DecodeVINValuesBatch", "key": "VIN[:8]+VIN[9:11]"},
                    "bytes": CACHE.stat().st_size, "sha256": sha256(CACHE),
                    "note": "one representative VIN per pattern key; representative VIN serials masked in cache"})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra-keys")
    ap.add_argument("--statewide", action="store_true", help="also decode statewide MY>=2011 patterns not in EValuateNY")
    a = ap.parse_args()
    main(a.extra_keys, a.statewide)
