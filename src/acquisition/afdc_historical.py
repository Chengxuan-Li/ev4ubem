"""Historical AFDC charging-infrastructure data (unbiased by station retirement) for New York / Tompkins County.

Three public sources, none requiring registration (checked 2026-09-14):

1. Static workbook  https://afdc.energy.gov/files/docs/historical-station-counts.xlsx
   Year-end (late-December) station counts by state and fuel, 2007-2025. Electric = public + private
   (non-residential). 2007-2010 = station locations; 2011-2013 = charging outlets (ports) only;
   2014+ = stations | ports and L1 | L2 | DC fast ports. No public/private split.

2. Server-rendered state count page  https://afdc.energy.gov/stations/states?count={public|private|total}&date=YYYY-MM-DD
   Same counts as the Station Locator "Historical Date" view, with access split; dates from 2014-01-20.
   No key. Raw HTML saved; parsed in src/analysis/infrastructure_history.py.

3. Undocumented v0 NLR API used by the Station Locator's "Historical Date" filter:
   https://developer.nlr.gov/api/alt-fuel-stations/v0/historical-date/{YYYY-MM-DD}.json
   (params as for v1 All Stations: state, fuel_type, access, status, limit). Returns the full station records
   *as published on that date* (so retired stations are present), enabling county-level (Tompkins) history by
   point-in-polygon. Works with the public DEMO_KEY, which on this endpoint reported X-Ratelimit-Limit: 10
   (requests per rolling hour), so this script is resumable and sleeps when the quota is exhausted.
   Found in https://widgets.nlr.gov/afdc/station-locator/assets/main-*.js; the companion
   v0/historical-fuel-station-counts.json rejects a `state` parameter (national only), so it is not used.
   (The afdc.energy.gov/data_download "historical" form requires name + email registration and is NOT used.)

Outputs (git-ignored): data/raw/afdc_historical/
Manifest: metadata/manifests/afdc_historical.json (api_key never recorded)
Env: NLR_API_KEY overrides DEMO_KEY.  CLI: --no-wait  (stop instead of sleeping when rate-limited)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import time

import requests

from src.utils.paths import RAW, ensure
from src.utils.provenance import UA, download, record, rel, sha256

OUT = RAW / "afdc_historical"
XLSX_URL = "https://afdc.energy.gov/files/docs/historical-station-counts.xlsx"
STATES_URL = "https://afdc.energy.gov/stations/states"
V0_URL = "https://developer.nlr.gov/api/alt-fuel-stations/v0/historical-date/{date}.json"
MANIFEST = "afdc_historical"

# Year-end snapshots (the xlsx uses "near the end of December"); final date approximates the present.
DATES = [f"{y}-12-31" for y in range(2014, 2026)] + ["2026-09-01"]
V0_PARAMS = {"state": "NY", "fuel_type": "ELEC", "access": "all", "status": "all", "limit": "all"}


def fetch_xlsx(overwrite: bool = False) -> None:
    download(XLSX_URL, OUT / "historical-station-counts.xlsx", MANIFEST, overwrite=overwrite,
             note="AFDC annual historical station counts by state/fuel (late December each year), 2007-2025")


def fetch_state_pages(overwrite: bool = False) -> None:
    d = OUT / "state_count_pages"
    for date in DATES:
        for count in ["public", "private", "total"]:
            dest = d / f"states_{count}_{date}.html"
            existed = dest.exists()
            download(STATES_URL, dest, MANIFEST, params={"count": count, "date": date}, overwrite=overwrite,
                     note="AFDC state station counts on date (Historical Data view); HTML table")
            if not existed or overwrite:
                time.sleep(1.0)  # be polite


def _get_v0(date: str, api_key: str, wait: bool) -> requests.Response | None:
    for attempt in range(1, 8):
        r = requests.get(V0_URL.format(date=date), params=dict(V0_PARAMS, api_key=api_key), headers=UA, timeout=600)
        if r.status_code == 429 or "OVER_RATE_LIMIT" in r.text[:500]:
            if not wait:
                print(f"[rate-limited] {date}: stopping (--no-wait)")
                return None
            print(f"[rate-limited] {date}: sleeping 20 min (attempt {attempt})", flush=True)
            time.sleep(1200)
            continue
        r.raise_for_status()
        return r
    return None


def fetch_v0_snapshots(overwrite: bool = False, wait: bool = True) -> None:
    d = OUT / "historical_date"
    ensure(d)
    api_key = os.environ.get("NLR_API_KEY", "DEMO_KEY")
    for date in DATES:
        dest = d / f"ny_elec_{date}.json"
        if dest.exists() and not overwrite:
            print(f"[skip] {rel(dest)}")
        else:
            r = _get_v0(date, api_key, wait)
            if r is None:
                return
            js = r.json()
            dest.write_text(json.dumps(js), encoding="utf-8")
            remaining = r.headers.get("X-Ratelimit-Remaining")
            print(f"[ok] {rel(dest)} stations={len(js.get('fuel_stations', []))} ratelimit_remaining={remaining}", flush=True)
            if remaining is not None and int(remaining) <= 0 and wait and date != DATES[-1]:
                print("[rate-limit] quota exhausted; sleeping 20 min", flush=True)
                time.sleep(1200)
        record(MANIFEST, {
            "local_path": rel(dest), "url": V0_URL.format(date=date), "params": V0_PARAMS,
            "retrieved_utc": _dt.datetime.fromtimestamp(dest.stat().st_mtime, _dt.timezone.utc).isoformat(timespec="seconds"),
            "bytes": dest.stat().st_size, "sha256": sha256(dest),
            "note": "NLR v0 historical-date station snapshot (as published on date); api_key omitted from record",
        })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--no-wait", action="store_true")
    a = ap.parse_args()
    ensure(OUT)
    fetch_xlsx(a.overwrite)
    fetch_state_pages(a.overwrite)
    fetch_v0_snapshots(a.overwrite, wait=not a.no_wait)


if __name__ == "__main__":
    main()
