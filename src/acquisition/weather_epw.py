"""Ithaca (KITH, WMO 725155) typical-year weather files from climate.onebuilding.org (public, no login).

Used only for the *energy* side of charging (temperature-dependent kWh/mi and cold-weather charging losses),
not for ownership or behavioural timing. TMYx 2011-2025 is the default; the other periods are kept for sensitivity.
Outputs (git-ignored): data/raw/weather/<name>.zip and extracted .epw/.stat files.
"""
from __future__ import annotations

import zipfile

from src.utils.paths import RAW, ensure
from src.utils.provenance import download

BASE = "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/NY_New_York"
FILES = ["USA_NY_Ithaca.Tompkins.Rgnl.AP.725155_TMYx.2011-2025.zip", "USA_NY_Ithaca.Tompkins.Rgnl.AP.725155_TMYx.2009-2023.zip",
         "USA_NY_Ithaca.Tompkins.Rgnl.AP.725155_TMYx.zip"]


def main() -> None:
    out = RAW / "weather"
    ensure(out)
    for f in FILES:
        z = download(f"{BASE}/{f}", out / f, manifest="weather_epw", note="OneBuilding TMYx Ithaca")
        with zipfile.ZipFile(z) as zz:
            zz.extractall(out / f.replace(".zip", ""))


if __name__ == "__main__":
    main()
