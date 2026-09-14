"""Invariant checks for the ownership, growth and charging models (tracked outputs only).

Run: python -m pytest -q tests
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from src.model.charging_params import value
from src.model.growth import logistic, survival
from src.utils.paths import PROCESSED, TABLES


def _need(path):
    if not path.exists():
        pytest.skip(f"{path} not present")
    return path


def test_synthetic_dwellings_match_acs_total():
    s = pd.read_csv(_need(TABLES / "synthetic_dwellings_summary.csv")).set_index("metric")["value"]
    assert abs(s["synthetic DUs"] - s["total ACS income"]) / s["total ACS income"] < 0.01


def test_allocation_preserves_observed_zip_totals():
    du = pd.read_parquet(_need(PROCESSED / "model" / "du_ev_2026.parquet"))
    d = pd.read_csv(PROCESSED / "dmv" / "tompkins_ev_stock_zip_2026.csv", dtype={"zip": str})
    d = d[d["drivetrain"].isin(["BEV", "PHEV"]) & (d["class_group"] == "PAS") & d["is_ldv"]].copy()
    d["zip"] = d["zip"].replace({"14851": "14850", "14852": "14850"})
    obs = d.groupby("zip")["vehicles"].sum()
    alloc = du.groupby("zcta")["E_ev"].sum()
    common = alloc.index.intersection(obs.index)
    assert np.allclose(alloc[common], obs[common], rtol=1e-6, atol=0.5)
    for col in ["E_ev_model", "E_ev_uniform", "E_ev_individual", "E_ev_prior"]:
        assert np.allclose(du.groupby("zcta")[col].sum()[common], obs[common], rtol=1e-6, atol=0.5)


def test_allocation_respects_vehicle_cap():
    du = pd.read_parquet(_need(PROCESSED / "model" / "du_ev_2026.parquet"))
    assert (du["E_ev"] <= du["veh"] + 1e-6).all()


def test_propensity_selected_model_recorded():
    p = json.load(open(_need(PROCESSED / "model" / "propensity_params.json")))
    assert p["selected_model"] in p["alternatives"]


def test_growth_projection_starts_at_observed_stock():
    g = pd.read_csv(_need(PROCESSED / "growth" / "growth_parameters_by_year.csv"))
    y26 = g[g["year"] == 2026]
    assert ((y26["EV_p50"] > 3233) & (y26["EV_p50"] < 3233 * 1.1)).all()  # year-end 2026 slightly above Sep-2026 stock
    assert (g.groupby("scenario")["EV_p50"].apply(lambda s: s.is_monotonic_increasing)).all()


def test_growth_helpers():
    assert survival(0) == pytest.approx(1.0)
    assert logistic(2030, 1.0, 0.3, 2030) == pytest.approx(0.5)


def test_charging_params_interpolate():
    assert value("home_access_mf5p", "access+", 2026) == pytest.approx(value("home_access_mf5p", "base", 2026))
    assert value("home_access_mf5p", "access+", 2050) > value("home_access_mf5p", "base", 2050)


def test_library_energy_balance_2026():
    s = pd.read_csv(_need(PROCESSED / "charging" / "library_summary_2026.csv"))
    bev = s[s["drivetrain"] == "BEV"]
    eta = bev["level"].map({"L1": 0.83, "L2": 0.90, "none": 0.90})
    delivered = bev["kwh_home"] * eta + (bev["kwh_work"] + bev["kwh_public_l2"]) * 0.90 + (bev["kwh_dcfc"] + bev["kwh_enroute"]) * 0.92
    ratio = delivered / bev["need_wheel"]
    assert ((ratio > 0.95) & (ratio < 1.05)).all()


def test_county_load_has_all_locations():
    c = pd.read_parquet(_need(PROCESSED / "load" / "county_hourly_2026_trend_base.parquet"))
    assert len(c) == 8760
    assert set(["home", "work", "public_l2", "dcfc", "fleet", "passerby"]) <= set(c.columns)
    assert (c.values >= -1e-6).all()
