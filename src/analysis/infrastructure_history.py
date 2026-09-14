"""Unbiased charging-infrastructure history for New York State and Tompkins County (2007/2014-2026).

Inputs (python -m src.acquisition.afdc_historical)
  data/raw/afdc_historical/historical-station-counts.xlsx        AFDC year-end state counts 2007-2025 (public+private)
  data/raw/afdc_historical/state_count_pages/*.html              AFDC state counts on date, public/private/total
  data/raw/afdc_historical/historical_date/ny_elec_<date>.json   NLR v0 station records as published on <date>
  data/processed/infrastructure/tompkins_ports_by_open_year.csv  survivorship-biased open_date curve (existing)
  data/raw/afdc/afdc_elec_ny_all_status.json                     current (2026-09-14) API snapshot, for NY open_date curve
  results/tables/tompkins_ev_stock_timeseries.csv, data/processed/evaluateny/ev_stock_zip_snapshot.parquet,
  data/processed/dmv/ny_county_ev_2026.csv                       EV stock denominators

Definitions
- station = AFDC station record (location); ports = EVSE ports (ev_level1/2_evse_num + ev_dc_fast_num).
  AFDC changed counting logic in 2021 (OCPI: connectors -> ports; ChargePoint/Greenlots stations split), so
  2020->2021 changes are partly definitional.
- Snapshots use status E (open) only, matching the AFDC state-count default (excludes planned/temporarily unavailable).
- Tompkins = point-in-polygon in TIGER 2024 county 36109 (same as src/processing/infrastructure.py).
- Evidence: Tompkins rows A (local observation, AFDC), NY rows B; ratios/CAGR/bias metrics D.

Outputs
  results/tables/infrastructure_history_tompkins_ny.csv
  results/tables/infrastructure_survivorship_bias.csv
  results/tables/infrastructure_station_persistence.csv
  results/tables/infrastructure_growth_metrics.csv
  results/tables/infrastructure_evs_per_public_port.csv
  results/figures/infrastructure_history.png
"""
from __future__ import annotations

import json
import re

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.processing.infrastructure import counties, to_points
from src.utils.paths import FIGURES, PROCESSED, RAW, TABLES, ensure

RAWH = RAW / "afdc_historical"
SRC_XLSX = "AFDC historical-station-counts.xlsx (late-Dec, public+private)"
SRC_PAGE = "AFDC stations/states?date= page (status E)"
SRC_V0 = "NLR API v0/historical-date station records (status E)"
LEVELS = {"L1": "ev_level1_evse_num", "L2": "ev_level2_evse_num", "DCFC": "ev_dc_fast_num"}


def _num(s: str) -> int:
    return int(str(s).replace(",", "").strip())


def _elec_cell(cell: str, cell2: str | None) -> dict:
    """'5,482 | 20,363' + '57 | 17,344 | 2,962' -> stations, ports, L1, L2, DCFC."""
    a = [_num(x) for x in str(cell).split("|")]
    b = [_num(x) for x in str(cell2).split("|")] if cell2 is not None else []
    out = {"stations": a[0], "ports": a[1] if len(a) > 1 else np.nan}
    if len(b) == 3:
        out.update(L1=b[0], L2=b[1], DCFC=b[2])
    return out


def parse_xlsx() -> pd.DataFrame:
    x = pd.ExcelFile(RAWH / "historical-station-counts.xlsx")
    rows = []
    for s in x.sheet_names:
        if not s.isdigit():
            continue
        yr = int(s)
        d = pd.read_excel(x, s, header=None)
        top = d.iloc[:6].astype(str)
        col = next(c for c in d.columns if top[c].str.strip().str.startswith("Electric").any())
        i = d.index[d[0].astype(str).str.strip() == "New York"][0]
        v, v2 = d.iat[i, col], d.iat[i + 1, col] if i + 1 < len(d) else None
        base = dict(date=f"{yr}-12-31", year=yr, geography="New York State", access="all", source=SRC_XLSX, evidence="B")
        if yr >= 2014:
            e = _elec_cell(v, v2)
            rows.append(dict(base, level="all", stations=e["stations"], ports=e["ports"], count_basis="stations|ports"))
            rows += [dict(base, level=k, stations=np.nan, ports=e[k], count_basis="ports") for k in LEVELS]
        elif yr >= 2011:
            rows.append(dict(base, level="all", stations=np.nan, ports=_num(v), count_basis="outlets (ports) only, 2011-2013"))
        else:
            rows.append(dict(base, level="all", stations=_num(v), ports=np.nan, count_basis="station locations only, 2007-2010"))
    return pd.DataFrame(rows)


def parse_state_pages() -> pd.DataFrame:
    rows = []
    for f in sorted((RAWH / "state_count_pages").glob("states_*_*.html")):
        _, count, date = f.stem.split("_")
        h = re.sub(r"\s+", " ", f.read_text(encoding="utf-8"))
        heads = [re.sub("<[^>]*>", " ", t).strip() for t in re.findall(r"<th[^>]*>(.*?)</th>", h)]
        ecol = next(i for i, t in enumerate(heads) if t.startswith("Electric"))  # 0 = State
        m = re.search(r"<tr>\s*<td>New York</td>(.*?)</tr>", h)
        tds = re.findall(r"<td[^>]*>(.*?)</td>", m.group(1))
        cell = tds[ecol - 1]
        parts = re.split(r"<br\s*/?>", cell)
        e = _elec_cell(re.sub("<[^>]*>", "", parts[0]), re.sub("<[^>]*>", "", parts[1]) if len(parts) > 1 else None)
        base = dict(date=date, year=int(date[:4]), geography="New York State", access=count if count != "total" else "all",
                    source=SRC_PAGE, evidence="B", count_basis="stations|ports")
        rows.append(dict(base, level="all", stations=e["stations"], ports=e["ports"]))
        rows += [dict(base, level=k, stations=np.nan, ports=e.get(k, np.nan)) for k in LEVELS]
    return pd.DataFrame(rows)


def load_snapshots() -> dict[str, gpd.GeoDataFrame]:
    cty = counties()
    snaps = {}
    for f in sorted((RAWH / "historical_date").glob("ny_elec_*.json")):
        date = f.stem.replace("ny_elec_", "")
        df = pd.DataFrame(json.loads(f.read_text(encoding="utf-8"))["fuel_stations"])
        g = gpd.sjoin(to_points(df), cty, how="left", predicate="within").drop(columns="index_right")
        snaps[date] = g
    return snaps


def summarise_snapshot(g: pd.DataFrame, date: str, geography: str, evidence: str) -> list[dict]:
    e = g[g["status_code"] == "E"]
    rows = []
    for acc in ["public", "private", "all"]:
        s = e if acc == "all" else e[e["access_code"] == acc]
        base = dict(date=date, year=int(date[:4]), geography=geography, access=acc, source=SRC_V0, evidence=evidence,
                    count_basis="stations|ports")
        rows.append(dict(base, level="all", stations=len(s), ports=int(s["ports_total"].sum())))
        for k, c in LEVELS.items():
            rows.append(dict(base, level=k, stations=int((s[c] > 0).sum()), ports=int(s[c].sum())))
    return rows


def open_date_curve(api: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    """Cumulative ports by open_date year among currently-open stations (survivorship-biased)."""
    e = api[api["status_code"] == "E"].copy()
    e["oy"] = pd.to_datetime(e["open_date"], errors="coerce").dt.year
    out = []
    for acc in ["public", "private"]:
        s = e[e["access_code"] == acc]
        for y in years:
            k = s[s["oy"] <= y]
            out.append(dict(year=y, access=acc, stations=len(k), L2=int(k["ev_level2_evse_num"].sum()),
                            DCFC=int(k["ev_dc_fast_num"].sum()), missing_open_date=int(s["oy"].isna().sum())))
    return pd.DataFrame(out)


def cagr(a: float, b: float, n: float) -> float:
    return (b / a) ** (1 / n) - 1 if a and a > 0 and b > 0 and n > 0 else np.nan


def ev_stock() -> pd.DataFrame:
    t = pd.read_csv(TABLES / "tompkins_ev_stock_timeseries.csv", parse_dates=["snapshot_date"])
    t = t[t["source"].str.startswith("EValuateNY") | t["source"].str.contains("VIN-decoded")]
    t = t.assign(geography="Tompkins County", ev_source=t["source"])[["snapshot_date", "geography", "EV", "ev_source"]]
    p = pd.read_parquet(PROCESSED / "evaluateny" / "ev_stock_zip_snapshot.parquet")
    z3 = pd.to_numeric(p["zip"].str[:3], errors="coerce")
    p = p[p["drivetrain"].isin(["BEV", "PHEV"]) & z3.between(100, 149)]
    n = p.groupby("snapshot_date")["vehicles"].sum().rename("EV").reset_index()
    n = n.assign(geography="New York State", ev_source="EValuateNY v11 (NY ZIPs 100-149, BEV+PHEV)")
    c = pd.read_csv(PROCESSED / "dmv" / "ny_county_ev_2026.csv")
    c = c[c["county"] != "OUT-OF-STATE"]
    n26 = pd.DataFrame([dict(snapshot_date=pd.Timestamp("2026-09-02"), geography="New York State",
                             EV=float(c["bev"].sum() + c["phev"].sum()), ev_source="DMV w4pv-hbkt 2026-09-02, VIN-decoded, NY counties")])
    return pd.concat([t, n, n26], ignore_index=True)


def main() -> None:
    ensure(TABLES, FIGURES)
    snaps = load_snapshots()
    rows = []
    for d, g in snaps.items():
        rows += summarise_snapshot(g, d, "New York State", "B")
        rows += summarise_snapshot(g[g["COUNTYFP"] == "109"], d, "Tompkins County", "A")
    hist = pd.concat([pd.DataFrame(rows), parse_state_pages(), parse_xlsx()], ignore_index=True)
    hist = hist[["year", "date", "geography", "access", "level", "stations", "ports", "count_basis", "source", "evidence"]]
    hist = hist.sort_values(["geography", "source", "access", "level", "date"]).reset_index(drop=True)
    hist.to_csv(TABLES / "infrastructure_history_tompkins_ny.csv", index=False)

    v0 = hist[hist["source"] == SRC_V0]

    def val(geo, acc, lvl, date, col="ports"):
        r = v0[(v0.geography == geo) & (v0.access == acc) & (v0.level == lvl) & (v0.date == date)]
        return float(r[col].iloc[0]) if len(r) else np.nan

    # --- cross-check v0 vs AFDC page/xlsx (NY) ---
    chk = hist[(hist.geography == "New York State") & (hist.level.isin(["all", "L2", "DCFC"]))]
    chk = chk.pivot_table(index=["date", "access", "level"], columns="source", values="ports").reset_index()
    print("NY ports cross-check (v0 vs page vs xlsx):\n", chk.to_string())

    # --- survivorship bias ---
    dates = sorted(snaps)
    yend = [d for d in dates if d.endswith("12-31")]
    years = [int(d[:4]) for d in yend]
    tb = pd.read_csv(PROCESSED / "infrastructure" / "tompkins_ports_by_open_year.csv")
    bias = []
    for acc in ["public", "private"]:
        s = tb[tb.access_code == acc].set_index("open_year")
        for d, y in zip(yend, years):
            k = s[s.index <= y]
            od = dict(stations=k["cum_stations"].iloc[-1] if len(k) else 0, L2=k["cum_l2"].iloc[-1] if len(k) else 0,
                      DCFC=k["cum_dcfc"].iloc[-1] if len(k) else 0)
            for m, lvl, col in [("stations", "all", "stations"), ("L2 ports", "L2", "ports"), ("DCFC ports", "DCFC", "ports")]:
                true = val("Tompkins County", acc, lvl, d, col)
                bias.append(dict(year=y, geography="Tompkins County", access=acc, metric=m, historical_snapshot=true,
                                 open_date_curve=od[m.split()[0] if m != "stations" else "stations"],
                                 open_date_basis="data/processed/infrastructure/tompkins_ports_by_open_year.csv (2026-09-14 API, status E)"))
    api = to_points(pd.DataFrame(json.loads((RAW / "afdc" / "afdc_elec_ny_all_status.json").read_text(encoding="utf-8"))["fuel_stations"]))
    odc = open_date_curve(api, years)
    for _, r in odc.iterrows():
        d = f"{r.year}-12-31"
        for m, lvl, col in [("stations", "all", "stations"), ("L2 ports", "L2", "ports"), ("DCFC ports", "DCFC", "ports")]:
            bias.append(dict(year=r.year, geography="New York State", access=r.access, metric=m,
                             historical_snapshot=val("New York State", r.access, lvl, d, col),
                             open_date_curve=r[m.split()[0]] if m != "stations" else r.stations,
                             open_date_basis=f"data/raw/afdc/afdc_elec_ny_all_status.json status E; {r.missing_open_date} stations lack open_date"))
    bias = pd.DataFrame(bias)
    bias["difference"] = bias["open_date_curve"] - bias["historical_snapshot"]
    bias["ratio_open_date_to_snapshot"] = bias["open_date_curve"] / bias["historical_snapshot"].replace(0, np.nan)
    bias["evidence"] = "D"
    bias.to_csv(TABLES / "infrastructure_survivorship_bias.csv", index=False)

    # --- station persistence: share of open stations on date D still present (any status) in latest snapshot ---
    # IDs are sometimes re-keyed (e.g. network re-imports / 2021 OCPI split), so also test whether any station in the
    # latest snapshot lies within 100 m (EPSG:32618 UTM 18N) of a missing ID ("no nearby successor" ~ physical removal).
    last = dates[-1]
    last_g = snaps[last][snaps[last].geometry.notna()].to_crs(32618)
    last_ids = set(snaps[last]["id"])
    pers = []
    for d in dates[:-1]:
        g = snaps[d]
        for geo, gg in [("New York State", g), ("Tompkins County", g[g["COUNTYFP"] == "109"])]:
            for acc in ["public", "private", "all"]:
                e = gg[(gg.status_code == "E") & ((gg.access_code == acc) if acc != "all" else True)]
                gone = e[~e["id"].isin(last_ids)]
                if len(gone):
                    near = gpd.sjoin_nearest(gone.to_crs(32618)[["id", "geometry"]], last_g[["geometry"]],
                                             how="left", max_distance=100, distance_col="dist")
                    no_succ = set(near.loc[near["dist"].isna(), "id"])
                else:
                    no_succ = set()
                ns = gone[gone["id"].isin(no_succ)]
                pers.append(dict(date=d, geography=geo, access=acc, open_stations=len(e), absent_in_latest=len(gone),
                                 share_absent=len(gone) / len(e) if len(e) else np.nan,
                                 absent_no_station_within_100m=len(ns),
                                 share_absent_no_station_within_100m=len(ns) / len(e) if len(e) else np.nan,
                                 ports_open=int(e["ports_total"].sum()), ports_absent_in_latest=int(gone["ports_total"].sum()),
                                 ports_absent_no_station_within_100m=int(ns["ports_total"].sum()),
                                 latest_snapshot=last, evidence="D"))
    pers = pd.DataFrame(pers)
    pers.to_csv(TABLES / "infrastructure_station_persistence.csv", index=False)

    # --- growth metrics (public ports, v0 snapshots) ---
    periods = [(2014, 2025), (2014, 2020), (2016, 2020), (2021, 2025), (2019, 2025), (2022, 2025)]
    gm = []
    for geo in ["New York State", "Tompkins County"]:
        for lvl in ["L2", "DCFC", "all"]:
            for a, b in periods:
                pa, pb = val(geo, "public", lvl, f"{a}-12-31"), val(geo, "public", lvl, f"{b}-12-31")
                gm.append(dict(geography=geo, access="public", level=lvl, start_year=a, end_year=b, start_ports=pa,
                               end_ports=pb, cagr=cagr(pa, pb, b - a), abs_growth_per_year=(pb - pa) / (b - a),
                               note="spans 2021 AFDC OCPI counting change" if a <= 2020 < b else "", evidence="D"))
    gm = pd.DataFrame(gm)
    gm.to_csv(TABLES / "infrastructure_growth_metrics.csv", index=False)

    # --- EVs per public port (nearest EV snapshot within 45 days) ---
    ev = ev_stock()
    epp = []
    for d in dates:
        dt = pd.Timestamp(d)
        for geo in ["New York State", "Tompkins County"]:
            e = ev[ev.geography == geo].copy()
            e["lag"] = (e["snapshot_date"] - dt).abs()
            e = e[e["lag"] <= pd.Timedelta(days=45)].sort_values("lag")
            if e.empty:
                continue
            r = e.iloc[0]
            pp, l2, dc = val(geo, "public", "all", d), val(geo, "public", "L2", d), val(geo, "public", "DCFC", d)
            epp.append(dict(date=d, geography=geo, ev_stock=round(r.EV, 1), ev_snapshot=r.snapshot_date.date(), ev_source=r.ev_source,
                            public_ports=pp, public_l2=l2, public_dcfc=dc, evs_per_public_port=r.EV / pp if pp else np.nan,
                            evs_per_public_l2=r.EV / l2 if l2 else np.nan, evs_per_public_dcfc=r.EV / dc if dc else np.nan,
                            evidence="D"))
    epp = pd.DataFrame(epp)
    epp.to_csv(TABLES / "infrastructure_evs_per_public_port.csv", index=False)

    # --- figure ---
    fig, ax = plt.subplots(2, 2, figsize=(12, 9))
    col = {"L1": "#9aa5b1", "L2": "#2a6fdb", "DCFC": "#d9480f", "all": "#222222"}

    def series(geo, acc, lvl, col_="ports", src=SRC_V0):
        r = hist[(hist.geography == geo) & (hist.access == acc) & (hist.level == lvl) & (hist.source == src)].sort_values("date")
        return pd.to_datetime(r["date"]), r[col_]

    a = ax[0, 0]
    for lvl in ["L2", "DCFC"]:
        x, y = series("New York State", "public", lvl)
        a.plot(x, y, "-o", color=col[lvl], ms=3, label=f"public {lvl} ports (v0 snapshot)")
        x, y = series("New York State", "private", lvl)
        a.plot(x, y, ":", color=col[lvl], label=f"private {lvl} ports")
    x, y = series("New York State", "all", "all", src=SRC_XLSX)
    a.plot(x, y, "s", color="#555", ms=3, mfc="none", label="all ports, xlsx year-end (2011-13 outlets)")
    a.set_title("New York State - EVSE ports (AFDC, status open)")
    a.set_yscale("log")
    a.legend(fontsize=7)

    a = ax[0, 1]
    tbp = tb[tb.access_code == "public"]
    for lvl, c_ in [("L2", "cum_l2"), ("DCFC", "cum_dcfc")]:
        x, y = series("Tompkins County", "public", lvl)
        a.plot(x, y, "-o", color=col[lvl], ms=3, label=f"public {lvl}: historical snapshot")
        a.step(pd.to_datetime(tbp["open_year"].astype(str) + "-12-31"), tbp[c_], where="post", ls="--", color=col[lvl],
               alpha=0.7, label=f"public {lvl}: open_date of surviving stations")
    a.set_title("Tompkins County - public ports: snapshot vs survivorship-biased curve")
    a.legend(fontsize=7)

    a = ax[1, 0]
    for geo, m in [("New York State", "o"), ("Tompkins County", "s")]:
        r = epp[epp.geography == geo]
        a.plot(pd.to_datetime(r["date"]), r["evs_per_public_port"], marker=m, label=f"{geo}: EVs / public port")
    a.set_title("EVs (BEV+PHEV) per public EVSE port")
    a.legend(fontsize=7)

    a = ax[1, 1]
    for geo, m in [("New York State", "-o"), ("Tompkins County", "-s")]:
        r = pers[(pers.geography == geo) & (pers.access == "all")]
        a.plot(pd.to_datetime(r["date"]), 100 * r["share_absent"], m, label=geo)
    a.set_title(f"Share of stations open on date absent from {last} snapshot (%)")
    a.legend(fontsize=7)
    for a in ax.flat:
        a.axvline(pd.Timestamp("2021-01-01"), color="grey", lw=0.8, ls="-.")
        a.grid(alpha=0.3)
    fig.suptitle("AFDC charging infrastructure history (B: NY, A: Tompkins; derived D). Dash-dot: 2021 OCPI counting change",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGURES / "infrastructure_history.png", dpi=150)

    show = hist[(hist.source == SRC_V0) & (hist.access == "public") & hist.level.isin(["all", "L2", "DCFC"])]
    print(show.pivot_table(index="date", columns=["geography", "level"], values="ports").to_string())
    print(gm[gm.level != "all"].to_string())
    print(epp.to_string())
    print(pers[pers.access == "all"].to_string())


if __name__ == "__main__":
    main()
