# 0001 — Acquisition access choices (2026-09-14)

**Status:** accepted

## Context
Several planned endpoints behaved differently from the brief's expectations when tested on 2026-09-14.

## Decisions
1. **Census ACS via table-based summary files, not the Census API.** `api.census.gov` now returns a
   "Missing Key" page without a registered key. Registration is out of scope (no account creation),
   so `src/acquisition/census.py` streams the public ACS 2020–2024 5-year *table-based summary files*
   from `www2.census.gov` and filters to NY geographies. ACS 2021–2025 5-year is not yet released
   (expected Dec 2026). Some tables (B08201, B25118, B08006, B26001) are not published at block-group level.
2. **AFDC via `developer.nlr.gov` with DEMO_KEY.** `developer.nrel.gov` no longer resolves (lab renamed);
   `developer.nlr.gov` serves the same station API. The NY Open Data AFDC mirror (`bpkx-gmh7`) is
   acquired as an independent copy for cross-checking.
3. **DMV full snapshot streamed and reduced.** SoQL cannot group by VIN substrings, so drivetrain
   decoding statewide requires the full export (~12.5 M rows). We keep a compact parquet with a VIN
   *pattern* key (VIN[:8]+VIN[9:11]) and drop full VINs.
4. **VIN decoding with NHTSA vPIC** (public, no key) for patterns not covered by EValuateNY's
   `Vehicle Description.csv` (which ends with the April 2023 snapshot and lacks MY2024+ patterns).
5. **Tompkins parcels from NYS ITS public tax-parcel service** (Tompkins permits redistribution);
   owner and mailing fields are excluded.
6. **NHTS 2022** public CSV (`nhts.ornl.gov/assets/2022/download/csv.zip`).

## Consequences
All acquisitions are scripted and recorded in `metadata/manifests/`. DMV and AFDC endpoints are
moving snapshots; analyses must cite the recorded `source_rows_updated_utc`/retrieval date.
