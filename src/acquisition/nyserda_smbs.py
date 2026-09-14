"""Acquire the NYSERDA Statewide Multifamily Building Study (SMBS) 2022 public datasets.

Sources (data.ny.gov, NYSERDA Market Characterization and Evaluation, static):
  gjv3-iq86  SMBS 2022 Occupant Survey   (tabular; ~135 respondents)
  gfhm-wz4s  SMBS 2022 General Survey    (tabular; ~1,337 building representatives)
  qwyr-7esw  SMBS 2022 Site Visits       (file asset: multi-sheet .xlsx)
Each asset carries an Overview PDF and a Data Dictionary PDF as attachments; the attachment
list is read from https://data.ny.gov/api/views/<id>.json at run time (not hard-coded).
The public study report and appendix on nyserda.ny.gov (linked from the dataset metadata) are
also downloaded because they document sampling and weighting.

Outputs (git-ignored): data/raw/nyserda_smbs/
Manifest: metadata/manifests/nyserda_smbs.json

Run: python -m src.acquisition.nyserda_smbs [--overwrite]
"""
from __future__ import annotations

import argparse
import urllib.parse

from src.acquisition.socrata import DOMAIN, fetch_to_parquet, view_metadata
from src.utils.paths import RAW
from src.utils.provenance import download

MANIFEST = "nyserda_smbs"
OUT = RAW / "nyserda_smbs"

TABULAR = {
    "gjv3-iq86": "smbs2022_occupant_survey.parquet",
    "gfhm-wz4s": "smbs2022_general_survey.parquet",
}
FILE_ASSETS = {
    "qwyr-7esw": "smbs2022_site_visits.xlsx",
}
ALL_IDS = list(TABULAR) + list(FILE_ASSETS)

NYSERDA_PUB = "https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Publications/building-stock-potential-studies"
REPORTS = {
    "Multifamily-Market-Assessment-Report.pdf": f"{NYSERDA_PUB}/Multifamily-Market-Assessment-Report.pdf",
    "Multifamily-Market-Assessment-Appendix.pdf": f"{NYSERDA_PUB}/Multifamily-Market-Assessment-Appendix.pdf",
}


def _attachment_url(dataset_id: str, asset_id: str, filename: str) -> str:
    q = urllib.parse.urlencode({"download": "true", "filename": filename})
    return f"{DOMAIN}/api/views/{dataset_id}/files/{asset_id}?{q}"


def main(overwrite: bool = False) -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # 1) Full tabular datasets (all columns, all rows)
    for ds, fname in TABULAR.items():
        fetch_to_parquet(ds, {}, OUT / fname, manifest=MANIFEST, overwrite=overwrite,
                         note="SMBS 2022 full table (all rows/columns, strings)")

    # 2) File asset (site-visit workbook) and 3) attachments (overview + data dictionary PDFs)
    for ds in ALL_IDS:
        meta = view_metadata(ds, save=ds in TABULAR)
        if ds in FILE_ASSETS and meta.get("blobId"):
            download(f"{DOMAIN}/api/views/{ds}/files/{meta['blobId']}?download=true",
                     OUT / FILE_ASSETS[ds], manifest=MANIFEST, overwrite=overwrite,
                     note=f"{meta.get('name')} (blob: {meta.get('blobFilename')})")
        for att in (meta.get("metadata") or {}).get("attachments") or []:
            fn = att.get("filename") or att.get("name")
            if not att.get("assetId") or not fn:
                continue
            download(_attachment_url(ds, att["assetId"], fn), OUT / fn, manifest=MANIFEST,
                     overwrite=overwrite, note=f"attachment of {ds}: {meta.get('name')}")

    # 4) Study report + appendix (sampling, weighting, results)
    for fn, url in REPORTS.items():
        try:
            download(url, OUT / fn, manifest=MANIFEST, overwrite=overwrite,
                     note="NYSERDA Multifamily Market Assessment (SMBS 2022) public report")
        except Exception as exc:  # noqa: BLE001  (report host may block; data remain usable)
            print(f"[warn] report not downloaded: {url}: {exc}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true")
    main(ap.parse_args().overwrite)
