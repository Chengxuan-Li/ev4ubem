"""Parse Ithaca TMYx EPW files into tidy hourly weather (tracked compact output).

EPW fields used: year, month, day, hour (1-24, hour-ending, local standard time), dry-bulb temperature (°C),
relative humidity (%), wind speed (m/s), global horizontal radiation (Wh/m²).
Outputs: data/processed/weather/ithaca_tmyx_2011-2025_hourly.csv (8760 rows), weather_daily_summary.csv
Evidence: typical-meteorological-year composite of observed KITH weather (not a specific calendar year).
"""
from __future__ import annotations

import pandas as pd

from src.utils.paths import PROCESSED, RAW, ensure

EPW = RAW / "weather" / "USA_NY_Ithaca.Tompkins.Rgnl.AP.725155_TMYx.2011-2025" / "USA_NY_Ithaca.Tompkins.Rgnl.AP.725155_TMYx.2011-2025.epw"
COLS = {0: "src_year", 1: "month", 2: "day", 3: "hour_ending", 6: "t_drybulb_c", 8: "rh_pct", 13: "ghi_wh_m2", 21: "wind_ms"}


def load(path=EPW) -> pd.DataFrame:
    d = pd.read_csv(path, skiprows=8, header=None)
    d = d[list(COLS)].rename(columns=COLS)
    d["hour_of_year"] = range(len(d))
    d["hour"] = d["hour_ending"] - 1  # hour-beginning index 0-23 (local standard time)
    return d


def main() -> None:
    out = PROCESSED / "weather"
    ensure(out)
    d = load()
    assert len(d) == 8760, len(d)
    d.to_csv(out / "ithaca_tmyx_2011-2025_hourly.csv", index=False)
    daily = d.groupby(["month", "day"]).agg(t_mean_c=("t_drybulb_c", "mean"), t_min_c=("t_drybulb_c", "min"), t_max_c=("t_drybulb_c", "max")).reset_index()
    daily.round(2).to_csv(out / "weather_daily_summary.csv", index=False)
    print(d.groupby("month")["t_drybulb_c"].mean().round(1).to_dict())


if __name__ == "__main__":
    main()
