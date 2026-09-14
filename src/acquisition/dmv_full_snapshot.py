"""Stream the full NYS DMV registration snapshot (w4pv-hbkt, ~12.5M rows) to a compact parquet.

Why: DMV `fuel_type` alone cannot identify PHEVs (hypothesis to test), and SoQL cannot group by VIN
substrings. Streaming the full export lets us attach a VIN-pattern key (VIN chars 1-8 + 10-11)
to every vehicle and VIN-decode drivetrain statewide.

Kept columns (record_type == VEH only): vin_key11 (VIN[:8]+VIN[9:11]), vin_len, registration_class, zip, county,
state, model_year, make, body_type, fuel_type, unladen_weight, reg_valid_date, reg_expiration_date.
Full VINs are not retained (not needed; reduces size). The export is a moving snapshot: the
source 'rowsUpdatedAt' timestamp is recorded in the manifest.
Output: data/raw/ny_open_data/dmv_reg_ny_veh_full_compact.parquet (git-ignored).
"""
from __future__ import annotations

import datetime as _dt
import io

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests

from src.acquisition.socrata import view_metadata
from src.utils.paths import RAW, ensure
from src.utils.provenance import UA, record, rel, sha256

URL = "https://data.ny.gov/api/views/w4pv-hbkt/rows.csv?accessType=DOWNLOAD"
COLS = ["Record Type", "VIN", "Registration Class", "City", "State", "Zip", "County", "Model Year", "Make",
        "Body Type", "Fuel Type", "Unladen Weight", "Reg Valid Date", "Reg Expiration Date"]


def _transform(ch: pd.DataFrame) -> pd.DataFrame:
    ch.columns = [c.strip().lower().replace(" ", "_") for c in ch.columns]
    ch = ch[ch["record_type"] == "VEH"].copy()
    v = ch["vin"].fillna("")
    ch["vin_len"] = v.str.len().astype("int16")
    ch["vin_key11"] = (v.str[:8] + v.str[9:11]).where(ch["vin_len"] == 17)
    ch = ch.drop(columns=["vin", "record_type", "city"])
    ch["model_year"] = pd.to_numeric(ch["model_year"], errors="coerce").astype("float32")
    ch["unladen_weight"] = pd.to_numeric(ch["unladen_weight"], errors="coerce").astype("float32")
    return ch


def main(overwrite: bool = False) -> None:
    out = RAW / "ny_open_data"
    ensure(out)
    dest = out / "dmv_reg_ny_veh_full_compact.parquet"
    meta = view_metadata("w4pv-hbkt")
    if dest.exists() and not overwrite:
        print(f"[skip] {rel(dest)}")
    else:
        tmp_csv = out / "_w4pv-hbkt_full.csv.part"
        with requests.get(URL, headers=UA, stream=True, timeout=3600) as r:
            r.raise_for_status()
            with open(tmp_csv, "wb") as f:
                for b in r.iter_content(8 << 20):
                    f.write(b)
        raw_sha = sha256(tmp_csv)
        raw_bytes = tmp_csv.stat().st_size
        writer, n = None, 0
        for ch in pd.read_csv(tmp_csv, dtype=str, usecols=lambda c: c in COLS, chunksize=1_000_000):
            ch = _transform(ch)
            n += len(ch)
            t = pa.Table.from_pandas(ch, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(dest, t.schema, compression="zstd")
            writer.write_table(t.cast(writer.schema))
            print(f"  VEH rows written: {n}")
        writer.close()
        tmp_csv.unlink()
        record("ny_open_data", {"local_path": rel(dest), "url": URL, "dataset_id": "w4pv-hbkt",
                                "source_rows_updated_utc": _dt.datetime.fromtimestamp(meta.get("rowsUpdatedAt", 0), _dt.timezone.utc).isoformat(),
                                "retrieved_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
                                "raw_csv_bytes": raw_bytes, "raw_csv_sha256": raw_sha, "rows_veh": n,
                                "bytes": dest.stat().st_size, "note": "full export, VEH rows only, VIN reduced to pattern key"})
        print(f"[ok] {rel(dest)} {n} rows")


if __name__ == "__main__":
    main()
