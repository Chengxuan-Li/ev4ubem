"""Open, login-free EV charging-session datasets used as behavioural references (evidence class C).

See docs/source_notes/charging_session_datasets_and_nrel_benchmarks.md for access verification,
licences and transferability caveats. Outputs under data/raw/charging_sessions/<dataset>/ (git-ignored).

Datasets
- norway_residential : Sørensen et al. residential charging, Trondheim apartment-complex (Zenodo 13896176, CC-BY-4.0)
- boulder_public_l2  : City of Boulder CO public charging sessions 2018-2023 (ArcGIS FeatureServer, CC0)
- workplace_midwest  : workplace charging program, one US employer 2014-2015 (Harvard Dataverse QF1PMO, CC0)
- dundee_public      : Dundee City Council public charge points 2021-2025 (OGL-UK-3.0)
- palo_alto_public   : City of Palo Alto public charging 2011-2020 (open data portal)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import time

import pandas as pd
import requests

from src.utils.paths import RAW, ensure
from src.utils.provenance import UA, download, record, rel, sha256

OUT = RAW / "charging_sessions"

# Zenodo record file keys (verified 2026-09-14). Only Dataset1 contains observed sessions; Datasets 2-4 are
# the authors' predictions and are not acquired.
NORWAY = ["Dataset1_charging_reports.csv"]
DUNDEE = {"2021H2": "189b838f51e74f6bb77509d91c47d7c0", "2022": "f1a6b5df441d4606821d5f1a78e92d7e",
          "2023": "80df5f177b8c4a94b2bc692835801e8e", "2024": "8b443deaf9174b7aa9d3e10eaa906422",
          "2025H1": "e185a3a1cfc948a69ada76e950b9d447"}
BOULDER = "https://services.arcgis.com/ePKBjXrBZ2vEEgWd/arcgis/rest/services/Electric_Vehicle_Charging_Station_Data/FeatureServer/0/query"


def norway() -> None:
    for f in NORWAY:
        try:
            download(f"https://zenodo.org/api/records/13896176/files/{f}/content", OUT / "norway_residential" / f,
                     manifest="charging_sessions", note="Zenodo 13896176 residential charging (Norway)")
        except Exception as exc:  # noqa: BLE001  (file names in the record may differ; logged)
            print("[warn] norway", f, exc)


def boulder(overwrite: bool = False) -> None:
    dest = OUT / "boulder_public_l2" / "boulder_sessions.parquet"
    ensure(dest.parent)
    if not dest.exists() or overwrite:
        rows, off = [], 0
        while True:
            p = {"where": "1=1", "outFields": "*", "orderByFields": "ObjectId2", "resultOffset": off,
                 "resultRecordCount": 2000, "f": "json"}
            for attempt in range(5):
                try:
                    r = requests.get(BOULDER, params=p, headers=UA, timeout=300)
                    r.raise_for_status()
                    feats = r.json().get("features", [])
                    break
                except Exception as exc:  # noqa: BLE001
                    print("retry", exc)
                    time.sleep(5 * (attempt + 1))
            if not feats:
                break
            rows += [f["attributes"] for f in feats]
            off += len(feats)
            if off % 20000 == 0:
                print("  boulder", off)
        pd.DataFrame(rows).astype(str).to_parquet(dest, index=False)
    record("charging_sessions", {"local_path": rel(dest), "url": BOULDER, "params": {"where": "1=1", "outFields": "*"},
                                 "retrieved_utc": _dt.datetime.fromtimestamp(dest.stat().st_mtime, _dt.timezone.utc).isoformat(timespec="seconds"),
                                 "bytes": dest.stat().st_size, "sha256": sha256(dest), "note": "City of Boulder EV charging sessions (CC0)"})
    download("https://webappsprod.bouldercolorado.gov/opendata/ev_datadictionary.csv", OUT / "boulder_public_l2" / "ev_datadictionary.csv",
             manifest="charging_sessions")


def workplace() -> None:
    download("https://dataverse.harvard.edu/api/access/datafile/4491950", OUT / "workplace_midwest" / "ev_workplace_charging_data.tsv",
             manifest="charging_sessions", note="Harvard Dataverse doi:10.7910/DVN/QF1PMO (CC0)")


def dundee() -> None:
    for k, i in DUNDEE.items():
        download(f"https://www.arcgis.com/sharing/rest/content/items/{i}/data", OUT / "dundee_public" / f"dundee_{k}.csv",
                 manifest="charging_sessions", note="Dundee City Council public EV charge point usage (OGL-UK-3.0)")


def palo_alto() -> None:
    download("https://data.paloalto.gov/datasets/194693-electric-vehicle-charging-station-usage-july-2011-dec-2020.download/",
             OUT / "palo_alto_public" / "palo_alto_2011_2020.csv", manifest="charging_sessions",
             note="City of Palo Alto EV charging station usage Jul 2011-Dec 2020")


def main(only: list[str] | None = None) -> None:
    for name, fn in [("norway", norway), ("boulder", boulder), ("workplace", workplace), ("dundee", dundee), ("palo_alto", palo_alto)]:
        if only and name not in only:
            continue
        print("==", name)
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            print(f"[error] {name}: {exc}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    main(ap.parse_args().only)
