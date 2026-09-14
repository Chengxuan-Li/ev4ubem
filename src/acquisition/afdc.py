"""AFDC alternative fuel station data for New York via the public NLR (formerly NREL) developer API.

API: https://developer.nlr.gov/api/alt-fuel-stations/v1.json  (DOE AFDC station locator).
Uses the public DEMO_KEY by default (rate-limited); set env var NLR_API_KEY to use your own key.
Note: developer.nrel.gov no longer resolves (lab renamed); developer.nlr.gov is the live host (checked 2026-09-14).
Output: data/raw/afdc/afdc_elec_ny_all_status.json (all statuses: E=open, P=planned, T=temporarily unavailable).
"""
from __future__ import annotations

import datetime as _dt
import json
import os

import requests

from src.utils.paths import RAW, ensure
from src.utils.provenance import UA, record, rel, sha256

URL = "https://developer.nlr.gov/api/alt-fuel-stations/v1.json"


def main(overwrite: bool = False) -> None:
    out = RAW / "afdc"
    ensure(out)
    dest = out / "afdc_elec_ny_all_status.json"
    params = {"state": "NY", "fuel_type": "ELEC", "status": "all", "access": "all", "limit": "all"}
    if dest.exists() and not overwrite:
        print(f"[skip] {rel(dest)}")
    else:
        q = dict(params, api_key=os.environ.get("NLR_API_KEY", "DEMO_KEY"))
        r = requests.get(URL, params=q, headers=UA, timeout=600)
        r.raise_for_status()
        d = r.json()
        dest.write_text(json.dumps(d), encoding="utf-8")
        print(f"[ok] {rel(dest)} stations={len(d.get('fuel_stations', []))}")
    record("afdc", {"local_path": rel(dest), "url": URL, "params": params,
                    "retrieved_utc": _dt.datetime.fromtimestamp(dest.stat().st_mtime, _dt.timezone.utc).isoformat(timespec="seconds"),
                    "bytes": dest.stat().st_size, "sha256": sha256(dest), "note": "api_key omitted from record"})


if __name__ == "__main__":
    main()
