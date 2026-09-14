r"""Variance decomposition of residential EV charging load uncertainty by source and spatial scale (2026, 2035).

Question: at each spatial scale, how much of the uncertainty in EV charging load comes from
  (1) HOW MANY EVs there are (county stock growth),
  (2) WHERE they are placed within ZIPs ((2a) weighting choice, (2b) sampling of which dwellings), and
  (3) HOW they charge ((3a) stochastic behaviour = archetype and simulated EV-year per EV, (3b) behaviour parameters)?
Ownership = trend, charging = base. All results are model output conditional on assumptions ("inferred").

Design: fully crossed Monte Carlo over five independent factors (one model evaluation per cell)
  S   stock        2026: observed (K=1, variance 0 by construction). 2035: growth.project Monte Carlo (400 draws,
                   identical stream to growth.main: θ=(t0,k,m) ~ N(θ̂,Σ̂), N_new ±15 %, λ ±2 y); the 400 draws are
                   sorted by EV(2035) into K_S equal-probability strata and one draw is taken at random per stratum
                   (stratified sampling). Personal EVs per ZIP scale with EV_s/EV_p50 (as load_assembly does for
                   ownership scenarios; placement convergence φ held at the central value); the BEV share of the stock
                   comes from the same draw.
  M   weighting    enumerated: {M5 ecological model, NHTS individual} (central ensemble, decision 0005), w^φ(y).
                   `--weightings all` adds uniform, vehicles and full-prior weightings (sensitivity).
  UP  sampling     per-vehicle-slot uniforms u: Efraimidis–Spirakis keys log(u)/(w_d^φ / v_d); the top T_z slots of
                   each ZIP own an EV (nested in T_z, so the same u gives consistent draws across stock levels);
                   a second per-slot uniform sets the drivetrain (BEV if u' < BEV share of ZIP (2026) / stock (2035)).
  TH  parameters   behaviour parameter vector (table uncertainty_factor_ranges.csv): home L2 power multiplier,
                   energy-per-mile multiplier, annual-miles multiplier, multifamily home-access shift, Dirichlet
                   frequency mix. Each level re-simulates a home-charging library with charging_library.simulate_ev
                   (36 unmanaged archetypes × 60 EV-years, common random numbers across levels) and recomputes
                   archetype probabilities with load_assembly.archetype_probs, with parameter values supplied through a
                   scoped substitute for charging_params.value (no model file is modified).
  UB  stochastic   per-vehicle-slot uniforms for archetype choice P(a | dwelling class, drivetrain, θ) and EV-year
                   choice within the archetype library.
Cell output Y(s, m, u_P, θ, u_B): hourly home charging summed to county, 65 block groups and sampled parcels ->
annual energy (MWh) and annual peak-hour load (kW = max hourly kWh); county also all resident-EV charging
(home + workplace + public L2 + DCFC of resident EVs; excludes fleet depots and passers-by).
Design sizes: 2026 M2 × UP16 × TH16 × UB16 = 8,192 cells; 2035 S10 × M2 × UP10 × TH10 × UB10 = 20,000 cells.

Estimator (bias-corrected functional ANOVA / Sobol–Hoeffding on the crossed grid). With Ȳ_A the mean of Y over
all factors not in A and Ṽ_A the empirical variance of Ȳ_A over the A-cells (population normalisation),
  empirical partial variances   D̂_A = Σ_{B ⊆ A} (−1)^{|A|−|B|} Ṽ_B           (exact orthogonal decomposition of the grid)
  expectation                   E[D̂_A] = Σ_{B ⊇ A} D_B · Π_{f∈A} a_f · Π_{f∈B∖A} b_f
  a_f = (K_f − 1)/K_f, b_f = 1/K_f for iid random factors (UP, TH, UB); a_f = 1, b_f = 0 for enumerated or
  stratified factors (M, S). The triangular system is solved from the highest-order subset downwards, giving
  unbiased D_A (not clipped; small negative values indicate Monte Carlo noise). Var Y = Σ_A D_A.
  Group (closed) first-order share  S_G = Σ_{∅≠A⊆G} D_A / Var Y,   G ∈ {stock {S}, placement {M,UP}, behaviour {TH,UB}}
  Total-effect share               T_G = Σ_{A ∩ G ≠ ∅} D_A / Var Y
  Interaction share                1 − S_stock − S_placement − S_behaviour (subsets spanning ≥ 2 groups)
Sub-factor shares D_M, D_UP, D_{M,UP}, D_TH, D_UB, D_{TH,UB} are also reported.
Block groups: per-BG indices, plus mean / median / IQR across the 65 BGs and the mean over urban-core BGs (ACS
population density ≥ 1,000 per km²). Parcels: annual peak kW of individual parcels (random sample of up to 1,500
parcels with vehicles per bin for 1 and 2–4 dwelling units; all parcels for 5–19 and 20+), pooled within bin as
Σ_p D_{A,p} / Σ_p Var_p Y.
Uncertainty of the estimates: 95 % bootstrap intervals resampling the levels of the random factors (UP, TH, UB)
with replacement; percentile intervals shifted by the bootstrap bias, because duplicated levels bias the corrected
estimator (B = 200; 100 for parcels); a repeat with another master seed checks stability
(`--seed`, written to data/interim/uncertainty/).

Outputs
  results/tables/uncertainty_decomposition_{county,bg,parcel}.csv, results/tables/uncertainty_factor_ranges.csv
  results/figures/uncertainty_decomposition.png
  data/interim/uncertainty/cells_*.npz (per-θ cell outputs; cache)
Run: python -m src.analysis.uncertainty_decomposition [--years 2026 2035] [--workers 8] [--quick]
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import time
from contextlib import contextmanager
from multiprocessing import get_context

import numpy as np
import pandas as pd
from scipy import sparse

from src.model import charging_library as cl
from src.model import charging_params as cp
from src.model import growth as gr
from src.model import load_assembly as la
from src.model import ownership_allocation as oa
from src.utils.paths import FIGURES, INTERIM, PROCESSED, TABLES, ensure

SEED = 20260914
N_PER_ARCH = 60
FACTORS = ["S", "M", "UP", "TH", "UB"]
KIND = {"S": "stratified", "M": "enumerated", "UP": "random", "TH": "random", "UB": "random"}
GROUPS = {"stock": ["S"], "placement": ["M", "UP"], "behaviour": ["TH", "UB"]}
DESIGN = {2026: {"S": 1, "M": 2, "UP": 16, "TH": 16, "UB": 16}, 2035: {"S": 10, "M": 2, "UP": 10, "TH": 10, "UB": 10}}
QUICK = {2026: {"S": 1, "M": 2, "UP": 3, "TH": 3, "UB": 3}, 2035: {"S": 3, "M": 2, "UP": 3, "TH": 3, "UB": 3}}
WEIGHTINGS = {"central": ["model", "individual"], "all": ["model", "individual", "uniform", "vehicles", "prior"]}
CLASSES = list(itertools.product(["SF", "MF2_4", "MF5P", "MOBILE"], ["own", "rent"], [0, 1, 2, 3]))
FREQS = la.FREQS
BINS = ["1", "2-4", "5-19", "20+"]
PARCEL_SAMPLE_MAX = {"1": 1500, "2-4": 1500, "5-19": 10**6, "20+": 10**6}
URBAN_CORE_DENSITY = 1000.0
PHEV_L2_MAX_KW = 7.2
COUNTY_METRICS = ["annual_mwh_home", "peak_kw_home", "annual_mwh_resident_all", "peak_kw_resident_all"]
BG_METRICS = ["annual_mwh_home", "peak_kw_home"]
OUTDIR = INTERIM / "uncertainty"

# behaviour-parameter distributions: (name, low, high, unit, applies to, rationale)
THETA_SPEC = [
    ("l2_power_mult", 0.85, 1.35, "× year value", "l2_kw_bev; l2_kw_phev (capped at 7.2 kW)",
     "home L2 power: 30 A (7.2 kW) EVSE central; 6.6 kW legacy onboard chargers to 40–48 A EVSE (9.6–11.5 kW) limited by "
     "onboard chargers; report §8 names 9.6–11.5 kW as a sensitivity"),
    ("e_wheel_mult", 0.85, 1.15, "× year value", "e_wheel_bev_kwh_per_mi; e_wheel_phev_kwh_per_mi",
     "energy per mile: assumption (EPA-label-like fleet mix); ±15 % spans sedan-heavy to SUV/pickup-heavy mixes"),
    ("annual_miles_mult", 0.85, 1.25, "× year value", "annual_miles_bev; annual_miles_phev",
     "Drive Clean 2024 self-reported miles (B); NHTS 2022 BEVs imply ≈ +40 % energy (C, n=166) -> asymmetric range"),
    ("mf_access_delta", -0.20, 0.20, "additive (prob)", "home_access_mf2_4; home_access_mf5p (clipped 0.02–0.98)",
     "multifamily home access: SMBS upstate 84 % of MF units with off-street parking vs 5.7 % of MF buildings with "
     "EV charging (B); central 0.55 / 0.35 in 2026 are assumptions"),
    ("freq_dirichlet_concentration", 50.0, 50.0, "Dirichlet α = 50 · p_base", "freq_{daily,few_week,weekly,rare}_{bev,phev}",
     "Drive Clean 2024 frequency shares (B, self-report, rebate recipients); effective sample size 50 reflects category "
     "mapping and representativeness rather than survey sampling error"),
]


# --------------------------------------------------------------------------------------------------------------------
# behaviour parameters
# --------------------------------------------------------------------------------------------------------------------
def draw_theta(level: int, seed: int) -> dict:
    rng = np.random.default_rng([seed, 4, level])
    th = {name: float(rng.uniform(lo, hi)) for name, lo, hi, *_ in THETA_SPEC[:4]}
    for dt in ["bev", "phev"]:
        p = np.array([cp.value(f"freq_{f}_{dt}", "base", 2026) for f in FREQS])
        p = p / p.sum()
        th[f"freq_ratio_{dt}"] = rng.dirichlet(50.0 * p) / p  # multiplicative perturbation of the base mix
    return th


def central_theta() -> dict:
    return {"l2_power_mult": 1.0, "e_wheel_mult": 1.0, "annual_miles_mult": 1.0, "mf_access_delta": 0.0,
            "freq_ratio_bev": np.ones(4), "freq_ratio_phev": np.ones(4)}


@contextmanager
def patched_params(theta: dict):
    """Temporarily route charging_params.value lookups of charging_library and load_assembly through θ."""
    base = cp.value

    def value(param: str, scenario: str, year: int) -> float:
        x = base(param, scenario, year)
        if param == "l2_kw_bev":
            return x * theta["l2_power_mult"]
        if param == "l2_kw_phev":
            return min(x * theta["l2_power_mult"], PHEV_L2_MAX_KW)
        if param.startswith("e_wheel_"):
            return x * theta["e_wheel_mult"]
        if param in ("annual_miles_bev", "annual_miles_phev"):
            return x * theta["annual_miles_mult"]
        if param in ("home_access_mf2_4", "home_access_mf5p"):
            return float(np.clip(x + theta["mf_access_delta"], 0.02, 0.98))
        if param.startswith("freq_"):
            parts = param.split("_")
            f, dt = "_".join(parts[1:-1]), parts[-1]
            return x * float(theta[f"freq_ratio_{dt}"][FREQS.index(f)])
        return x

    old = (cl.value, la.value)
    cl.value, la.value = value, value
    try:
        yield
    finally:
        cl.value, la.value = old


def build_library(year: int, theta: dict, emp, n_per: int = N_PER_ARCH):
    """Home and all-location hourly kWh for the unmanaged archetypes (base charging has no managed sessions)."""
    archs = [a for a in cl.archetypes("base") if not a["managed"]]
    tday, weekend = cl.weather(year)
    rng = np.random.default_rng(11 + year)  # same seed for every θ level -> common random numbers
    n = len(archs) * n_per
    H = np.zeros((n, 8760), np.float32)
    T = np.zeros((n, 8760), np.float32)
    i = 0
    with patched_params(theta):
        for a in archs:
            for _ in range(n_per):
                h, w, pl, dc, _m = cl.simulate_ev(a, year, rng, emp, tday, weekend, [], i)
                H[i], T[i] = h, h + w + pl + dc
                i += 1
    keys = [(a["drivetrain"], a["access"], a["level"], a["freq"], a["work"], a["managed"]) for a in archs]
    return H, T, keys


def class_cum_probs(year: int, theta: dict, keys: list) -> np.ndarray:
    """Cumulative P(archetype | dwelling class, drivetrain) [n_class, 2, n_arch] under θ (base charging)."""
    kidx = {k: i for i, k in enumerate(keys)}
    P = np.zeros((len(CLASSES), 2, len(keys)))
    with patched_params(theta):
        for ci, (g, t, w) in enumerate(CLASSES):
            for di, dt in enumerate(["BEV", "PHEV"]):
                for a, p in la.archetype_probs(g, t, w, dt, year, "base").items():
                    if p > 1e-15:
                        P[ci, di, kidx[a]] += p  # KeyError if a managed archetype had probability > 0
    assert np.allclose(P.sum(-1), 1.0, atol=1e-9)
    return np.cumsum(P, axis=-1)


# --------------------------------------------------------------------------------------------------------------------
# stock
# --------------------------------------------------------------------------------------------------------------------
def growth_mc(year: int, n_draws: int = 400) -> pd.DataFrame:
    """Trend-scenario Monte Carlo draws of year-end EV stock, identical random stream to growth.main (seed 42)."""
    f = gr.fit("tompkins")
    g = gr.GEO["tompkins"]
    init = pd.read_csv(PROCESSED / "dmv" / "tompkins_ev_model_year_2026.csv").rename(columns={"model_year_n": "model_year"})
    init = init[init["model_year"].notna()]
    _, sh, _ = gr.observations("tompkins")
    s_obs = float(sh[sh["source"].str.startswith("DMV")]["share"].mean())
    rng = np.random.default_rng(42)
    draws = rng.multivariate_normal([f["t0"], f["k"], f["m"]], f["cov"], size=n_draws)
    bfn = lambda v: gr.logistic(v, 0.95, f["kb"], f["tb"])  # noqa: E731
    rows = []
    for i, dd in enumerate(draws):  # 'trend' is the first scenario in growth.main, so the N_new/λ stream matches
        prm = {"t0": dd[0], "k": float(np.clip(dd[1], 0.05, 1.0)), "m": float(np.clip(dd[2], 0.3, 4.0))}
        N = g["N_new"] * rng.uniform(0.85, 1.15)
        lam = gr.LAMBDA + rng.uniform(-2, 2)
        p = gr.project(gr.share_scenario("trend", prm, s_obs), bfn, init, N, g["F"], prm["m"], lam, years=range(2026, year + 1))
        r = p[p["year"] == year].iloc[0]
        rows.append({"draw": i, "EV": r["EV"], "bev_share": r["BEV"] / r["EV"]})
    return pd.DataFrame(rows)


def stock_levels(year: int, K: int, seed: int) -> pd.DataFrame:
    gp = pd.read_csv(PROCESSED / "growth" / "growth_parameters_by_year.csv")
    tr = gp[gp["scenario"] == "trend"].set_index("year")
    if year == 2026 or K == 1:
        return pd.DataFrame({"stratum": [0], "EV": [np.nan], "ratio": [1.0], "bev_share": [np.nan]})
    mc = growth_mc(year).sort_values("EV").reset_index(drop=True)
    rng = np.random.default_rng([seed, 1, year])
    rows = []
    for k, idx in enumerate(np.array_split(np.arange(len(mc)), K)):
        r = mc.iloc[int(rng.choice(idx))]
        rows.append({"stratum": k, "EV": r["EV"], "ratio": r["EV"] / tr.loc[year, "EV_p50"], "bev_share": r["bev_share"]})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------------------------------------
# context shared by workers
# --------------------------------------------------------------------------------------------------------------------
def context(year: int, weightings: str, seed: int) -> dict:
    du = la.load_dus()
    params = json.load(open(PROCESSED / "model" / "propensity_params.json"))
    veh = du["veh"].values.astype(int)
    slot_du = np.repeat(np.arange(len(du)), veh)
    zips = du["zcta"].values
    gp = pd.read_csv(PROCESSED / "growth" / "growth_parameters_by_year.csv")
    tr = gp[gp["scenario"] == "trend"].set_index("year")
    if year == 2026:
        phi = 1.0
        tz, _ = oa.observed_zip_totals()
        tz = tz[tz.index.isin(set(zips)) & (tz["EV"] > 0)]
        zip_T = {z: float(round(r["EV"])) for z, r in tz.iterrows()}
        zbev = (tz["BEV"] / tz["EV"]).to_dict()
        slot_bev = pd.Series(zips[slot_du]).map(zbev).fillna(0.0).values
        bev_central = np.nan
    else:
        q = max(tr.loc[year, "EV_p50"] / tr.loc[2026, "EV_p50"], 1.0)
        phi = oa.PHI_PER_DOUBLING ** np.log2(q)
        s = du.groupby("zcta")[f"E_ev_{year}"].sum()
        zip_T = {z: float(v) for z, v in s.items() if v > 0}
        slot_bev = None
        bev_central = tr.loc[year, "BEV_p50"] / (tr.loc[year, "BEV_p50"] + tr.loc[year, "PHEV_p50"])
    W = []
    for mode in WEIGHTINGS[weightings]:
        w = oa.weights(du, params, mode)
        w = np.where(w > 0, w ** phi, 0.0)
        W.append(w[slot_du] / np.maximum(veh[slot_du], 1))
    zip_slots = {z: np.where(zips[slot_du] == z)[0] for z in zip_T}
    bgs = np.array(sorted(du["bg"].unique()), dtype=str)
    bg_idx = pd.Series(np.arange(len(bgs)), index=bgs)[du["bg"].values].values
    cmap = {c: i for i, c in enumerate(CLASSES)}
    class_idx = np.array([cmap[k] for k in zip(du["g"], du["tenure"], du["workers"])])
    # parcel sample
    n_du = du.groupby("parcel").size()
    veh_p = du.groupby("parcel")["veh"].sum()
    pbin = pd.cut(n_du, [0, 1, 4, 19, np.inf], labels=BINS).astype(str)
    rng = np.random.default_rng([seed, 9])
    chosen = []
    for b in BINS:
        cand = np.array(sorted(pbin.index[(pbin == b) & (veh_p > 0)]))
        if len(cand) > PARCEL_SAMPLE_MAX[b]:
            cand = np.sort(rng.choice(cand, PARCEL_SAMPLE_MAX[b], replace=False))
        chosen.append(cand)
    parcels = np.concatenate(chosen).astype(str)
    pl_map = pd.Series(np.arange(len(parcels)), index=parcels)
    psamp = du["parcel"].map(pl_map).fillna(-1).astype(int).values
    return {"year": year, "phi": phi, "slot_du": slot_du, "zip_T": zip_T, "zip_slots": zip_slots, "slot_bev": slot_bev,
            "bev_central": bev_central, "W": W, "bgs": bgs, "bg_idx": bg_idx, "class_idx": class_idx, "parcels": parcels,
            "parcel_bin": np.asarray(pbin[parcels].tolist(), dtype="U8"), "parcel_ndu": n_du[parcels].values.astype(int), "psamp": psamp}


# --------------------------------------------------------------------------------------------------------------------
# cell evaluation (one worker per θ level)
# --------------------------------------------------------------------------------------------------------------------
def cell_path(year: int, th: int, tag: str) -> "os.PathLike":
    return OUTDIR / f"cells_{year}_{tag}_theta{th:02d}.npz"


def run_theta(job: dict) -> str:
    year, th, seed, design, tag = job["year"], job["th"], job["seed"], job["design"], job["tag"]
    out = cell_path(year, th, tag)
    if out.exists() and not job["force"]:
        return str(out)
    t0 = time.time()
    ctx = context(year, job["weightings"], seed)
    stock = pd.DataFrame(job["stock"])
    theta = draw_theta(th, seed)
    H, Htot, keys = build_library(year, theta, cl.empirical())
    cum = class_cum_probs(year, theta, keys)
    n_lib, nA = H.shape[0], len(keys)
    peak_lib = H.max(axis=1)
    n_slots, nbg, nps = len(ctx["slot_du"]), len(ctx["bgs"]), len(ctx["parcels"])
    S, M, UP, UB = design["S"], len(ctx["W"]), design["UP"], design["UB"]
    county = np.zeros((S, M, UP, UB, len(COUNTY_METRICS)))
    bg = np.zeros((S, M, UP, UB, nbg, len(BG_METRICS)), np.float32)
    par = np.zeros((S, M, UP, UB, nps), np.float32)
    # placement orders per (m, u_P) and drivetrain uniforms
    orders, udt = {}, []
    for ui in range(UP):
        rng = np.random.default_rng([seed, 2, year, ui])
        u = rng.random(n_slots)
        udt.append(rng.random(n_slots))
        logu = np.log(np.clip(u, 1e-300, None))
        for mi, sw in enumerate(ctx["W"]):
            key = np.where(sw > 0, logu / np.where(sw > 0, sw, 1.0), -np.inf)
            orders[(mi, ui)] = {z: s_[np.argsort(-key[s_], kind="stable")][: int((sw[s_] > 0).sum())] for z, s_ in ctx["zip_slots"].items()}
    ub_u = []
    for bi in range(UB):
        rng = np.random.default_rng([seed, 5, year, bi])
        ub_u.append((rng.random(n_slots), rng.random(n_slots)))
    for si, st in stock.iterrows():
        Tz = {z: int(round(T * st["ratio"])) for z, T in ctx["zip_T"].items()}
        for mi in range(M):
            for ui in range(UP):
                sel = np.concatenate([orders[(mi, ui)][z][: Tz[z]] for z in Tz])
                d = ctx["slot_du"][sel]
                thr = ctx["slot_bev"][sel] if year == 2026 else st["bev_share"]
                phev = (udt[ui][sel] >= thr).astype(int)
                cumsel = cum[ctx["class_idx"][d], phev]
                bgi = ctx["bg_idx"][d]
                pl = ctx["psamp"][d]
                pm = pl >= 0
                pp = pl[pm]
                cnt_p = np.bincount(pp, minlength=nps)
                single = cnt_p[pp] == 1
                multi_ids, inv = np.unique(pp[~single], return_inverse=True)
                for bi in range(UB):
                    u1, u2 = ub_u[bi][0][sel], ub_u[bi][1][sel]
                    a = np.minimum((cumsel < u1[:, None]).sum(axis=1), nA - 1)
                    row = a * N_PER_ARCH + np.minimum((u2 * N_PER_ARCH).astype(int), N_PER_ARCH - 1)
                    C = np.bincount(bgi * n_lib + row, minlength=nbg * n_lib).reshape(nbg, n_lib).astype(np.float32)
                    P = C @ H
                    bg[si, mi, ui, bi, :, 0] = P.sum(axis=1) / 1000.0
                    bg[si, mi, ui, bi, :, 1] = P.max(axis=1)
                    cty = P.sum(axis=0, dtype=np.float64)
                    tot = C.sum(axis=0) @ Htot
                    county[si, mi, ui, bi] = [cty.sum() / 1000.0, cty.max(), tot.sum(dtype=np.float64) / 1000.0, tot.max()]
                    rp = row[pm]
                    pk = np.zeros(nps, np.float32)
                    pk[pp[single]] = peak_lib[rp[single]]
                    if len(multi_ids):
                        Mx = sparse.csr_matrix((np.ones(len(inv), np.float32), (inv, rp[~single])), shape=(len(multi_ids), n_lib))
                        pk[multi_ids] = np.asarray(Mx @ H).max(axis=1)
                    par[si, mi, ui, bi] = pk
        print(f"  {year} θ{th}: stock level {si + 1}/{len(stock)} done ({time.time() - t0:.0f}s)", flush=True)
    ensure(OUTDIR)
    np.savez_compressed(out, county=county, bg=bg, par=par, bgs=ctx["bgs"], parcels=ctx["parcels"], parcel_bin=ctx["parcel_bin"],
                        parcel_ndu=ctx["parcel_ndu"], theta=np.array(json.dumps({k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in theta.items()})),
                        phi=ctx["phi"], seconds=time.time() - t0)
    return str(out)


# --------------------------------------------------------------------------------------------------------------------
# estimator
# --------------------------------------------------------------------------------------------------------------------
def _subsets(n: int):
    return [A for r in range(1, n + 1) for A in itertools.combinations(range(n), r)]


def anova_components(Y: np.ndarray, kinds: list[str]) -> tuple[dict, np.ndarray]:
    """Bias-corrected Sobol–Hoeffding partial variances D_A for a crossed grid.

    Y has len(kinds) leading factor axes followed by entity axes. Returns ({subset tuple: D_A array}, grand mean)."""
    nf = len(kinds)
    K = Y.shape[:nf]
    fax = tuple(range(nf))
    Y = Y.astype(np.float64)
    grand = Y.mean(axis=fax)
    Yc = Y - grand
    subs = _subsets(nf)
    Vc = {}
    for A in subs:
        other = tuple(f for f in fax if f not in A)
        mA = Yc.mean(axis=other, keepdims=False) if other else Yc
        Vc[A] = (mA ** 2).mean(axis=tuple(range(len(A))))
    Dhat = {}
    for A in subs:
        acc = 0.0
        for r in range(1, len(A) + 1):
            for B in itertools.combinations(A, r):
                acc = acc + (-1) ** (len(A) - r) * Vc[B]
        Dhat[A] = acc
    a = [(k - 1) / k if kind == "random" else 1.0 for k, kind in zip(K, kinds)]
    b = [1.0 / k if kind == "random" else 0.0 for k, kind in zip(K, kinds)]
    D = {}
    for A in sorted(subs, key=len, reverse=True):
        acc = Dhat[A].copy() if isinstance(Dhat[A], np.ndarray) else Dhat[A]
        aA = float(np.prod([a[f] for f in A]))
        for B in D:
            if set(A) < set(B):
                acc = acc - D[B] * aA * float(np.prod([b[f] for f in set(B) - set(A)]))
        D[A] = acc / aA
    return D, grand


def shares_from_components(D: dict, names: list[str]) -> dict:
    """Group / sub-factor partial variances (not yet normalised) keyed by output factor name; plus 'total'."""
    idx = {n: i for i, n in enumerate(names)}
    tot = sum(D.values())
    out = {"total": tot}

    def closed(group):
        g = {idx[f] for f in group if f in idx}
        return sum((v for A, v in D.items() if set(A) <= g), 0.0 * tot)

    def total_effect(group):
        g = {idx[f] for f in group if f in idx}
        return sum((v for A, v in D.items() if set(A) & g), 0.0 * tot)

    def one(*fs):
        key = tuple(sorted(idx[f] for f in fs)) if all(f in idx for f in fs) else None
        return D.get(key, 0.0 * tot) if key else 0.0 * tot

    for gname, g in GROUPS.items():
        out[f"first_order|{gname}"] = closed(g)
        out[f"total_effect|{gname}"] = total_effect(g)
    out["first_order|interaction"] = tot - sum(out[f"first_order|{g}"] for g in GROUPS)
    out["first_order|placement:weighting"] = one("M")
    out["first_order|placement:sampling"] = one("UP")
    out["first_order|placement:weighting_x_sampling"] = one("M", "UP")
    out["first_order|behaviour:parameters"] = one("TH")
    out["first_order|behaviour:stochastic"] = one("UB")
    out["first_order|behaviour:parameters_x_stochastic"] = one("TH", "UB")
    return out


def load_cells(year: int, design: dict, tag: str) -> dict:
    parts = [np.load(cell_path(year, th, tag), allow_pickle=False) for th in range(design["TH"])]
    # stack θ as axis 3 -> (S, M, UP, TH, UB, ...)
    res = {k: np.stack([p[k] for p in parts], axis=3) for k in ["county", "bg", "par"]}
    p0 = parts[0]
    res.update({"bgs": p0["bgs"], "parcels": p0["parcels"], "parcel_bin": p0["parcel_bin"], "parcel_ndu": p0["parcel_ndu"],
                "theta": [json.loads(str(p["theta"])) for p in parts], "phi": float(p0["phi"]),
                "seconds": float(sum(float(p["seconds"]) for p in parts))})
    return res


def active_axes(Y: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Drop factor axes with a single level (e.g. stock in 2026)."""
    keep = [i for i in range(len(FACTORS)) if Y.shape[i] > 1]
    Y = Y.reshape([Y.shape[i] for i in keep] + list(Y.shape[len(FACTORS):]))
    return Y, [FACTORS[i] for i in keep]


def bootstrap_index(shape: tuple, names: list[str], rng) -> list[np.ndarray]:
    return [rng.integers(k, size=k) if KIND[n] == "random" else np.arange(k) for k, n in zip(shape, names)]


def take(Y: np.ndarray, idx: list[np.ndarray]) -> np.ndarray:
    for ax, ix in enumerate(idx):
        if not np.array_equal(ix, np.arange(Y.shape[ax])):
            Y = np.take(Y, ix, axis=ax)
    return Y


def decompose(Y: np.ndarray) -> tuple[dict, np.ndarray]:
    Ya, names = active_axes(Y)
    D, grand = anova_components(Ya, [KIND[n] for n in names])
    return shares_from_components(D, names), grand


# --------------------------------------------------------------------------------------------------------------------
# tables
# --------------------------------------------------------------------------------------------------------------------
def design_label(design: dict, M: int) -> str:
    d = dict(design, M=M)
    return "×".join(f"{f}{d[f]}" for f in FACTORS if d[f] > 1)


def tidy_rows(base: dict, point: dict, boots: list[dict] | None, mean, sd, ci_type="bootstrap_95_bias_shifted") -> list[dict]:
    rows = []
    for key, v in point.items():
        if key == "total":
            continue
        index, factor = key.split("|")
        share = float(v)
        lo = hi = np.nan
        if boots:
            bs = np.array([b[key] for b in boots], dtype=float)
            # bias-shifted percentile interval: resampled designs contain duplicate levels, which shifts the
            # bias-corrected estimator; shift the percentile interval by the bootstrap bias (mean_boot - estimate)
            lo, hi = np.nanpercentile(bs, [2.5, 97.5]) - (np.nanmean(bs) - share)
        rows.append({**base, "index": index, "factor": factor, "variance_share": share, "ci_low": lo, "ci_high": hi,
                     "ci_type": ci_type if boots else "none", "mean": float(mean), "sd": float(sd)})
    return rows


def normalise(sh: dict) -> dict:
    tot = sh["total"]
    with np.errstate(invalid="ignore", divide="ignore"):
        return {k: (v / tot if k != "total" else tot) for k, v in sh.items()}


def analyse_year(year: int, design: dict, tag: str, n_boot: int, n_boot_parcel: int, seed: int) -> tuple[list, list, list]:
    c = load_cells(year, design, tag)
    M = c["county"].shape[1]
    ncell = int(np.prod([design[f] for f in FACTORS if f != "M"]) * M)
    lab = design_label(design, M)
    rng = np.random.default_rng([seed, 77, year])
    county_rows, bg_rows, parcel_rows = [], [], []

    # county
    Yc = c["county"]
    Ya, names = active_axes(Yc)
    boot_idx = [bootstrap_index(Ya.shape[: len(names)], names, rng) for _ in range(n_boot)]
    for j, metric in enumerate(COUNTY_METRICS):
        pt, grand = decompose(Yc[..., j])
        pt = normalise(pt)
        boots = []
        for ix in boot_idx:
            D, _ = anova_components(take(Ya[..., j], ix), [KIND[n] for n in names])
            boots.append(normalise(shares_from_components(D, names)))
        county_rows += tidy_rows({"year": year, "scale": "county", "entity": "Tompkins County", "metric": metric,
                                  "n_draws": ncell, "design": lab}, pt, boots, grand, np.sqrt(max(pt["total"], 0)))

    # block groups
    ctxt = pd.read_csv(TABLES / "tompkins_bg_context.csv", dtype={"GEOID": str}).set_index("GEOID")
    bgs = c["bgs"].astype(str)
    core = np.isin(bgs, ctxt.index[ctxt["pop_density_km2"] >= URBAN_CORE_DENSITY])
    Yb = c["bg"]
    Yba, names = active_axes(Yb)
    for j, metric in enumerate(BG_METRICS):
        pt, grand = decompose(Yb[..., j])
        per = normalise(pt)  # arrays over BGs
        boots = []
        for ix in boot_idx:
            D, _ = anova_components(take(Yba[..., j], ix), [KIND[n] for n in names])
            boots.append(normalise(shares_from_components(D, names)))
        base = {"year": year, "scale": "block_group", "metric": metric, "n_draws": ncell, "design": lab}
        for e, g in enumerate(bgs):
            rows = tidy_rows({**base, "entity": g}, {k: v[e] for k, v in per.items()}, [{k: v[e] for k, v in b.items()} for b in boots],
                             grand[e], np.sqrt(max(per["total"][e], 0)))
            bg_rows += rows
        for ent, mask in [(f"mean over {len(bgs)} BGs", np.ones(len(bgs), bool)), (f"mean over {core.sum()} urban-core BGs", core)]:
            pm = {k: np.nanmean(v[mask]) for k, v in per.items()}
            bm = [{k: np.nanmean(v[mask]) for k, v in b.items()} for b in boots]
            bg_rows += tidy_rows({**base, "entity": ent}, pm, bm, grand[mask].mean(), np.sqrt(np.clip(per["total"][mask], 0, None)).mean())
        for ent, q in [("median over BGs", 50), ("p25 over BGs", 25), ("p75 over BGs", 75)]:
            pm = {k: np.nanpercentile(v, q) for k, v in per.items()}
            bg_rows += tidy_rows({**base, "entity": ent}, pm, None, np.percentile(grand, q), np.percentile(np.sqrt(np.clip(per["total"], 0, None)), q))

    # parcels (pooled within bin)
    Yp = c["par"]
    Ypa, names = active_axes(Yp)
    pbin = c["parcel_bin"].astype(str)
    kinds = [KIND[n] for n in names]
    pboot_idx = boot_idx[:n_boot_parcel]

    def pooled(Yarr):
        acc = {b: None for b in BINS}
        chunks = np.array_split(np.arange(Yarr.shape[-1]), max(1, Yarr.shape[-1] // 400))
        for ch in chunks:
            D, _ = anova_components(Yarr[..., ch], kinds)
            sh = shares_from_components(D, names)
            for b in BINS:
                m = pbin[ch] == b
                if not m.any():
                    continue
                s = {k: float(np.sum(v[m])) for k, v in sh.items()}
                acc[b] = s if acc[b] is None else {k: acc[b][k] + s[k] for k in s}
        return acc

    pt = pooled(Ypa)
    grand = Ypa.reshape(-1, Ypa.shape[-1]).mean(axis=0)
    boots = {b: [] for b in BINS}
    for bi, ix in enumerate(pboot_idx):
        r = pooled(take(Ypa, ix))
        for b in BINS:
            boots[b].append(normalise(r[b]))
    for b in BINS:
        m = pbin == b
        parcel_rows += tidy_rows({"year": year, "scale": "parcel", "entity": f"{b} dwelling units (n={int(m.sum())} parcels, pooled)",
                                  "metric": "peak_kw_home", "n_draws": ncell, "design": lab}, normalise(pt[b]), boots[b],
                                 grand[m].mean(), np.sqrt(max(pt[b]["total"] / m.sum(), 0)))
    print(f"{year}: cells {ncell}, cell-evaluation time {c['seconds'] / 60:.1f} worker-min, φ={c['phi']:.3f}")
    return county_rows, bg_rows, parcel_rows


def ranges_table(stock: dict[int, pd.DataFrame], designs: dict, weightings: str) -> pd.DataFrame:
    gp = pd.read_csv(PROCESSED / "growth" / "growth_parameters_by_year.csv")
    tr = gp[gp["scenario"] == "trend"].set_index("year")
    rows = []
    s35 = stock.get(2035)
    mc = growth_mc(2035) if 2035 in designs else None
    rows.append({"factor_group": "stock", "factor": "stock", "parameter": "county EV stock, year-end (trend)", "unit": "EVs",
                 "central_2026": "3,233 observed (DMV 2026-09); 2,855 personal EVs placed", "range_2026": "fixed (observed)",
                 "central_2035": f"{tr.loc[2035, 'EV_p50']:,.0f}",
                 "range_2035": (f"MC p05–p95 {np.percentile(mc['EV'], 5):,.0f}–{np.percentile(mc['EV'], 95):,.0f}; strata draws "
                                + ", ".join(f"{x:,.0f}" for x in s35["EV"])) if mc is not None else "",
                 "distribution": "growth.project Monte Carlo (400 draws: θ=(t0,k,m)~N(θ̂,Σ̂), N_new ±15 %, λ ±2 y); stratified, one draw per equal-probability stratum",
                 "levels_2026": 1, "levels_2035": designs.get(2035, {}).get("S", ""),
                 "source_or_rationale": "src.model.growth; personal EVs per ZIP scaled by EV_s / EV_p50; φ held at central"})
    rows.append({"factor_group": "stock", "factor": "stock", "parameter": "BEV share of EV stock", "unit": "share",
                 "central_2026": "ZIP observed", "range_2026": "fixed",
                 "central_2035": f"{tr.loc[2035, 'BEV_p50'] / (tr.loc[2035, 'BEV_p50'] + tr.loc[2035, 'PHEV_p50']):.3f}",
                 "range_2035": f"MC p05–p95 {np.percentile(mc['bev_share'], 5):.3f}–{np.percentile(mc['bev_share'], 95):.3f}" if mc is not None else "",
                 "distribution": "joint with stock draw", "levels_2026": 1, "levels_2035": designs.get(2035, {}).get("S", ""),
                 "source_or_rationale": "logistic BEV share of additions (growth fit)"})
    rows.append({"factor_group": "placement", "factor": "placement:weighting", "parameter": "dwelling-unit weighting",
                 "unit": "-", "central_2026": "ensemble", "range_2026": " | ".join(WEIGHTINGS[weightings]), "central_2035": "ensemble, w^φ (φ=0.81)",
                 "range_2035": " | ".join(WEIGHTINGS[weightings]), "distribution": "enumerated, equal probability",
                 "levels_2026": len(WEIGHTINGS[weightings]), "levels_2035": len(WEIGHTINGS[weightings]),
                 "source_or_rationale": "src.model.ownership_allocation.weights; central ensemble per decision 0005"})
    rows.append({"factor_group": "placement", "factor": "placement:sampling", "parameter": "which vehicle slots own the T_z EVs; drivetrain",
                 "unit": "-", "central_2026": "", "range_2026": "Efraimidis–Spirakis slot sampling within ZIP", "central_2035": "",
                 "range_2035": "same, T_z scaled by stock draw", "distribution": "per-slot U(0,1) keys (iid seeds)",
                 "levels_2026": designs.get(2026, {}).get("UP", ""), "levels_2035": designs.get(2035, {}).get("UP", ""),
                 "source_or_rationale": "as ownership_allocation.allocate_status_quo realizations"})
    for name, lo, hi, unit, applies, why in THETA_SPEC:
        r = {"factor_group": "behaviour", "factor": "behaviour:parameters", "parameter": f"{name} -> {applies}", "unit": unit,
             "distribution": "Dirichlet" if "dirichlet" in name else "uniform",
             "levels_2026": designs.get(2026, {}).get("TH", ""), "levels_2035": designs.get(2035, {}).get("TH", ""), "source_or_rationale": why}
        for y in (2026, 2035):
            if name == "l2_power_mult":
                cen = cp.value("l2_kw_bev", "base", y)
                r[f"central_{y}"] = f"BEV {cen:.1f} kW / PHEV {cp.value('l2_kw_phev', 'base', y):.1f} kW"
                r[f"range_{y}"] = f"BEV {cen * lo:.1f}–{cen * hi:.1f} kW; PHEV {cp.value('l2_kw_phev', 'base', y) * lo:.1f}–{min(cp.value('l2_kw_phev', 'base', y) * hi, PHEV_L2_MAX_KW):.1f} kW"
            elif name == "e_wheel_mult":
                cen = cp.value("e_wheel_bev_kwh_per_mi", "base", y)
                r[f"central_{y}"] = f"BEV {cen:.2f} kWh/mi"
                r[f"range_{y}"] = f"BEV {cen * lo:.3f}–{cen * hi:.3f} kWh/mi (PHEV same multiplier)"
            elif name == "annual_miles_mult":
                cen = cp.value("annual_miles_bev", "base", y)
                r[f"central_{y}"] = f"BEV {cen:,.0f} mi/yr"
                r[f"range_{y}"] = f"BEV {cen * lo:,.0f}–{cen * hi:,.0f} mi/yr (PHEV same multiplier)"
            elif name == "mf_access_delta":
                a24, a5 = cp.value("home_access_mf2_4", "base", y), cp.value("home_access_mf5p", "base", y)
                r[f"central_{y}"] = f"2–4 units {a24:.2f}; 5+ units {a5:.2f}"
                r[f"range_{y}"] = f"2–4 units {a24 + lo:.2f}–{a24 + hi:.2f}; 5+ units {a5 + lo:.2f}–{a5 + hi:.2f}"
            else:
                pb = np.array([cp.value(f"freq_{f}_bev", "base", y) for f in FREQS]); pb /= pb.sum()
                r[f"central_{y}"] = "BEV daily/few-wk/weekly/rare " + "/".join(f"{x:.2f}" for x in pb)
                r[f"range_{y}"] = "Dirichlet(50·p); daily share 90 % interval ≈ ±0.11 (BEV)"
        rows.append(r)
    rows.append({"factor_group": "behaviour", "factor": "behaviour:stochastic", "parameter": "archetype and simulated EV-year per EV",
                 "unit": "-", "central_2026": "", "range_2026": "36 unmanaged archetypes × 60 EV-years", "central_2035": "",
                 "range_2035": "same (2035 calendar and parameters)", "distribution": "per-slot U(0,1) (iid seeds)",
                 "levels_2026": designs.get(2026, {}).get("UB", ""), "levels_2035": designs.get(2035, {}).get("UB", ""),
                 "source_or_rationale": "load_assembly.archetype_probs; charging_library.simulate_ev (event model)"})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------------------------------------
# figure
# --------------------------------------------------------------------------------------------------------------------
def figure(county: pd.DataFrame, bg: pd.DataFrame, parcel: pd.DataFrame, path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fo = lambda d: d[d["index"] == "first_order"]  # noqa: E731
    specs = [("County · annual energy", county, "Tompkins County", "annual_mwh_home"),
             ("County · peak hour", county, "Tompkins County", "peak_kw_home"),
             ("Block group · annual energy", bg, "mean over 65 BGs", "annual_mwh_home"),
             ("Block group · peak hour", bg, "mean over 65 BGs", "peak_kw_home"),
             ("Urban-core block group · peak hour", bg, "urban-core", "peak_kw_home")]
    specs += [(f"Parcel, {b} dwelling unit{'s' if b != '1' else ''} · peak hour", parcel, f"{b} dwelling units", "peak_kw_home") for b in BINS]
    segs = [("stock", "Stock (how many)", "#4C72B0"),
            ("placement:weighting", "Placement: weighting", "#C4622D"),
            ("placement:sampling+", "Placement: sampling", "#EDB48E"),
            ("behaviour:parameters", "Behaviour: parameters", "#3A7D44"),
            ("behaviour:stochastic+", "Behaviour: stochastic", "#9FD0A6"),
            ("interaction", "Interactions", "#CFCFCF")]
    years = sorted(county["year"].unique())
    fig, axes = plt.subplots(1, len(years), figsize=(11, 5), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, y in zip(axes, years):
        labels = []
        for r, (lab, df, ent, met) in enumerate(specs):
            d = fo(df)
            d = d[(d["year"] == y) & (d["metric"] == met) & d["entity"].str.contains(ent, regex=False)]
            v = d.set_index("factor")["variance_share"]
            vals = {"stock": v.get("stock", 0.0), "placement:weighting": v.get("placement:weighting", 0.0),
                    "placement:sampling+": v.get("placement:sampling", 0.0) + v.get("placement:weighting_x_sampling", 0.0),
                    "behaviour:parameters": v.get("behaviour:parameters", 0.0),
                    "behaviour:stochastic+": v.get("behaviour:stochastic", 0.0) + v.get("behaviour:parameters_x_stochastic", 0.0),
                    "interaction": v.get("interaction", 0.0)}
            left = 0.0
            for key, _, col in segs:
                w = max(float(vals[key]), 0.0)
                ax.barh(r, w, left=left, color=col, height=0.72, edgecolor="white", linewidth=0.6)
                if w >= 0.07:
                    ax.text(left + w / 2, r, f"{100 * w:.0f}", ha="center", va="center", fontsize=7.5,
                            color="white" if key in ("stock", "placement:weighting", "behaviour:parameters") else "#222222")
                left += w
            labels.append(lab)
        ax.set_yticks(range(len(specs)))
        ax.set_yticklabels(labels, fontsize=8.5)
        ax.set_xlim(0, 1)
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xticklabels(["0", "25", "50", "75", "100"], fontsize=8)
        ax.set_xlabel("Share of variance (%)", fontsize=9)
        ax.set_title(f"{y}" + (" (stock observed)" if y == 2026 else " (trend ownership)"), fontsize=10, loc="left")
        for s in ["top", "right", "left"]:
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#888888")
        ax.tick_params(axis="y", length=0)
        ax.axhline(4.5, color="#BBBBBB", lw=0.6)
    axes[0].invert_yaxis()  # shared y: invert once
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in segs]
    fig.legend(handles, [l for _, l, _ in segs], loc="upper center", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.6, 1.0))
    fig.text(0.01, 0.012, "Residential (home) EV charging; trend ownership, base charging. First-order closed-group variance shares from a "
             "bias-corrected ANOVA on a crossed Monte Carlo design.\n"
             "Within-group interactions are included in the lighter tint; "
             "block-group bars are means of per-BG shares, parcel bars pool variance within bin; negative estimates drawn as 0. "
             "Model output (inferred).", fontsize=7, color="#555555")
    fig.tight_layout(rect=(0, 0.05, 1, 0.9))
    fig.savefig(path, dpi=200, facecolor="white")
    plt.close(fig)


# --------------------------------------------------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2026, 2035])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--weightings", choices=list(WEIGHTINGS), default="central")
    ap.add_argument("--quick", action="store_true", help="small design for testing (writes to data/interim/uncertainty only)")
    ap.add_argument("--boot", type=int, default=200)
    ap.add_argument("--boot-parcel", type=int, default=100)
    ap.add_argument("--force", action="store_true", help="recompute cached cell files")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--figure-only", action="store_true", help="redraw the figure from the existing tables")
    a = ap.parse_args()
    designs = {y: (QUICK if a.quick else DESIGN)[y] for y in a.years}
    tag = f"s{a.seed}_{a.weightings}_{'quick' if a.quick else 'full'}"
    official = (a.seed == SEED) and (a.weightings == "central") and not a.quick
    ensure(OUTDIR, TABLES, FIGURES)
    if a.figure_only:
        src = TABLES if official else OUTDIR / tag
        t = {k: pd.read_csv(src / f"uncertainty_decomposition_{k}.csv", dtype={"entity": str}) for k in ["county", "bg", "parcel"]}
        figure(t["county"], t["bg"], t["parcel"], (FIGURES if official else src) / "uncertainty_decomposition.png")
        return
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
    os.environ.setdefault("MKL_NUM_THREADS", "2")
    t0 = time.time()
    stock = {y: stock_levels(y, designs[y]["S"], a.seed) for y in a.years}
    if not a.analyse_only:
        jobs = [{"year": y, "th": th, "seed": a.seed, "design": designs[y], "tag": tag, "weightings": a.weightings,
                 "stock": stock[y].to_dict("list"), "force": a.force} for y in a.years for th in range(designs[y]["TH"])]
        with get_context("spawn").Pool(min(a.workers, len(jobs))) as pool:
            for p in pool.imap_unordered(run_theta, jobs):
                print("  wrote", os.path.relpath(p), f"({time.time() - t0:.0f}s)", flush=True)
    rows = {"county": [], "bg": [], "parcel": []}
    for y in a.years:
        c, b, p = analyse_year(y, designs[y], tag, a.boot, a.boot_parcel, a.seed)
        rows["county"] += c; rows["bg"] += b; rows["parcel"] += p
    cols = ["year", "scale", "entity", "metric", "index", "factor", "variance_share", "ci_low", "ci_high", "ci_type", "mean", "sd", "n_draws", "design"]
    dest = TABLES if official else OUTDIR / tag
    ensure(dest)
    out = {k: pd.DataFrame(v)[cols] for k, v in rows.items()}
    for k, df in out.items():
        df.round(5).to_csv(dest / f"uncertainty_decomposition_{k}.csv", index=False)
    ranges_table(stock, designs, a.weightings).to_csv(dest / "uncertainty_factor_ranges.csv", index=False)
    pd.concat([s.assign(year=y) for y, s in stock.items()]).to_csv(OUTDIR / f"stock_levels_{tag}.csv", index=False)
    figure(out["county"], out["bg"], out["parcel"], (FIGURES if official else dest) / "uncertainty_decomposition.png")
    fo = pd.concat(out.values())
    fo = fo[(fo["index"] == "first_order") & fo["factor"].isin(["stock", "placement", "behaviour", "interaction"])
            & ~fo["entity"].str.match(r"^\d{12}$")]
    print(fo.pivot_table(index=["year", "scale", "entity", "metric"], columns="factor", values="variance_share").round(3).to_string())
    print(f"total runtime {(time.time() - t0) / 60:.1f} min; tables in {os.path.relpath(dest)}")


if __name__ == "__main__":
    main()
