"""Download the 2022 National Household Travel Survey (NHTS) public-use CSV files (v2.x).

Source: https://nhts.ornl.gov/downloads  (public, no login). ~40 MB unzipped.
"""
from __future__ import annotations

import zipfile

from src.utils.paths import RAW
from src.utils.provenance import download

URL = "https://nhts.ornl.gov/assets/2022/download/csv.zip"


def main() -> None:
    out = RAW / "nhts2022"
    z = download(URL, out / "nhts2022_csv.zip", manifest="nhts2022", note="NHTS 2022 public-use CSV (hh, per, veh, trip, ldt)")
    with zipfile.ZipFile(z) as zf:
        zf.extractall(out)
    print("extracted:", [i.filename for i in zipfile.ZipFile(z).infolist()])
    download("https://nhts.ornl.gov/assets/2022/doc/codebook.xlsx", out / "codebook.xlsx", manifest="nhts2022",
             note="NHTS 2022 codebook (value labels)")


if __name__ == "__main__":
    main()
