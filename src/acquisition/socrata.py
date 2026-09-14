"""Minimal Socrata (data.ny.gov) client with paging and provenance recording."""
from __future__ import annotations

import datetime as _dt
import io
import json
import time
from pathlib import Path

import pandas as pd
import requests

from src.utils.paths import SCHEMAS, ensure
from src.utils.provenance import UA, record, rel, sha256

DOMAIN = "https://data.ny.gov"


def view_metadata(dataset_id: str, save: bool = True) -> dict:
    r = requests.get(f"{DOMAIN}/api/views/{dataset_id}.json", headers=UA, timeout=120)
    r.raise_for_status()
    meta = r.json()
    if save:
        ensure(SCHEMAS)
        slim = {
            "id": dataset_id,
            "name": meta.get("name"),
            "description": meta.get("description"),
            "attribution": meta.get("attribution"),
            "rowsUpdatedAt_utc": _dt.datetime.fromtimestamp(meta.get("rowsUpdatedAt", 0), _dt.timezone.utc).isoformat(),
            "columns": [{"fieldName": c["fieldName"], "name": c.get("name"), "dataTypeName": c.get("dataTypeName"),
                         "description": c.get("description")} for c in meta.get("columns", [])],
        }
        (SCHEMAS / f"socrata_{dataset_id}.json").write_text(json.dumps(slim, indent=2) + "\n", encoding="utf-8")
    return meta


def query(dataset_id: str, soql: dict, page: int = 50000, max_rows: int | None = None,
          sleep: float = 0.5) -> pd.DataFrame:
    """Run a SoQL query with $limit/$offset paging; returns all rows as strings."""
    url = f"{DOMAIN}/resource/{dataset_id}.csv"
    frames, offset = [], 0
    while True:
        params = dict(soql)
        params["$limit"] = page
        params["$offset"] = offset
        for attempt in range(5):
            try:
                r = requests.get(url, params=params, headers=UA, timeout=900)
                r.raise_for_status()
                break
            except Exception as exc:  # noqa: BLE001
                print(f"  retry {attempt + 1}: {exc}")
                time.sleep(10 * (attempt + 1))
        else:
            raise RuntimeError(f"query failed: {dataset_id} {params}")
        df = pd.read_csv(io.StringIO(r.text), dtype=str, keep_default_na=False, na_values=[""])
        frames.append(df)
        offset += len(df)
        print(f"  {dataset_id}: {offset} rows")
        if len(df) < page or (max_rows and offset >= max_rows):
            break
        time.sleep(sleep)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fetch_to_parquet(dataset_id: str, soql: dict, dest: Path, manifest: str, note: str = "",
                     overwrite: bool = False, **kw) -> Path:
    dest = Path(dest)
    ensure(dest.parent)
    meta = view_metadata(dataset_id)
    if dest.exists() and not overwrite:
        print(f"[skip] {rel(dest)} exists")
    else:
        df = query(dataset_id, soql, **kw)
        df.to_parquet(dest, index=False)
        print(f"[ok] {rel(dest)} ({len(df)} rows)")
    record(manifest, {
        "local_path": rel(dest),
        "url": f"{DOMAIN}/resource/{dataset_id}.csv",
        "dataset_id": dataset_id,
        "dataset_name": meta.get("name"),
        "source_rows_updated_utc": _dt.datetime.fromtimestamp(meta.get("rowsUpdatedAt", 0), _dt.timezone.utc).isoformat(),
        "params": soql,
        "retrieved_utc": _dt.datetime.fromtimestamp(dest.stat().st_mtime, _dt.timezone.utc).isoformat(timespec="seconds"),
        "rows": int(pd.read_parquet(dest, columns=[]).shape[0]) if dest.exists() else None,
        "bytes": dest.stat().st_size,
        "sha256_parquet": sha256(dest),
        "note": note,
    })
    return dest
