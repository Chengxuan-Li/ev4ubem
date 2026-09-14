"""Run all acquisition steps in dependency order (large downloads; see docs/methodology.md for sizes).

The EValuateNY archives must be unzipped into data/raw/nyserda/evaluateny_v11/ (done here with zipfile).
"""
from __future__ import annotations

import zipfile

from src.acquisition import (afdc, census, charging_sessions, dmv_full_snapshot, nhts, nrel_tempo, ny_open_data,
                             nys_parcels, nyserda_evaluateny, vpic)
from src.utils.paths import RAW


def unzip_evaluateny() -> None:
    out = RAW / "nyserda" / "evaluateny_v11"
    if (out / "Vehicle Description.csv").exists():
        return
    out.mkdir(parents=True, exist_ok=True)
    for part in ["EValuateNY_v11_pt1.zip", "EValuateNY_v11_pt2.zip"]:
        with zipfile.ZipFile(RAW / "nyserda" / part) as z:
            z.extractall(out)


def main() -> None:
    nyserda_evaluateny.main()
    unzip_evaluateny()
    ny_open_data.main()
    dmv_full_snapshot.main()
    census.main()
    nhts.main()
    nys_parcels.main()
    afdc.main()
    vpic.main(statewide=True)
    charging_sessions.main()
    nrel_tempo.main(nrel_tempo.DEFAULT)


if __name__ == "__main__":
    main()
