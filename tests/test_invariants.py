"""Lightweight invariant checks on tracked processed outputs and helper functions (no raw data needed).

Run: python -m pytest -q tests
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.acquisition.vpic import wildcard_vin
from src.analysis.zip_ev_penetration import poisson_dev
from src.processing.acs_features import _share
from src.processing.dmv_ev_stock import vpic_class
from src.utils.paths import PROCESSED, TABLES


def test_wildcard_vin_shape():
    k = pd.Series(["5YJ3E1EA5NF"[:8] + "NF"])
    w = wildcard_vin(k).iloc[0]
    assert len(w) == 17 and w[8] == "*" and w[9:11] == "NF"


def test_vpic_class_rules():
    v = pd.DataFrame({"ElectrificationLevel": ["BEV (Battery Electric Vehicle)", "PHEV (Plug-in Hybrid Electric Vehicle)",
                                               "Strong HEV (Hybrid Electric Vehicle)", "", ""],
                      "FuelTypePrimary": ["Electric", "Electric", "Gasoline", "Gasoline", "Electric"],
                      "FuelTypeSecondary": ["", "Gasoline", "Electric", "", ""]})
    assert vpic_class(v).tolist() == ["BEV", "PHEV", "HEV", "ICE", "BEV"]


def test_acs_share_moe_nonnegative():
    p, m = _share(pd.Series([50.0]), pd.Series([10.0]), pd.Series([100.0]), pd.Series([20.0]))
    assert p.iloc[0] == 0.5 and m.iloc[0] >= 0


def test_poisson_deviance_zero_at_truth():
    y = np.array([0.0, 3.0, 10.0])
    assert poisson_dev(y, y) == pytest.approx(0.0, abs=1e-6)


def test_allocation_preserves_zip_totals():
    p = PROCESSED / "allocation" / "parcel_ev_allocation.parquet"
    if not p.exists():
        pytest.skip("allocation output not present")
    a = pd.read_parquet(p)
    tot = a[["S0", "S1", "S2", "S3"]].groupby(a["zcta"]).sum()
    assert np.allclose(tot["S0"], tot["S3"]) and np.allclose(tot["S1"], tot["S2"])


def test_tompkins_stock_consistency():
    d = pd.read_csv(PROCESSED / "dmv" / "tompkins_ev_stock_zip_2026.csv", dtype={"zip": str})
    ev = d[d["drivetrain"].isin(["BEV", "PHEV"])]["vehicles"].sum()
    ts = pd.read_csv(TABLES / "tompkins_ev_stock_timeseries.csv")
    assert ts["EV"].iloc[-1] == ev
    # ZIP-share and county-field definitions should agree within 10 %
    zw = ts[ts["source"].str.contains("method-consistent")]["EV"].iloc[0]
    assert abs(zw - ev) / ev < 0.10


def test_hourly_shares_sum_to_one():
    t = pd.read_csv(TABLES / "sessions_hourly_energy_share.csv")
    s = t.groupby(["dataset", "port_type", "day_type"])["energy_share"].sum()
    assert np.allclose(s, 1.0, atol=1e-3)
