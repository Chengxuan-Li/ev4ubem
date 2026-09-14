r"""County EV stock growth model (cohort stock-flow with logistic adoption), calibration, backcast and scenarios to 2050.

Model (annual cohorts v, additions assumed at mid-year):
  s(v)   = s_max / (1 + exp(-k (v - t0)))                       EV share of new light-duty vehicle additions
  b(v)   = b_max / (1 + exp(-k_b (v - t_b)))                    BEV share of EV additions
  A(v)   = N_new * m * s(v)                                     EV additions (new + net used imports; m = effective multiplier); EV <= 0.99 F
  EV(t)  = sum_{v} A(v) * S(t - v - 0.5),   S(a) = exp(-(a/λ)^κ)  Weibull survival (κ = 3.5, λ = 17 y; median ≈ 15.3 y)
  BEV(t), PHEV(t) analogously with A(v) b(v), A(v) (1 - b(v)).
N_new = annual new light-duty vehicle additions (Tompkins ≈ 3,600; NY ≈ 1.0 M; from first-appearance and DMV
transaction data), F = light-duty fleet (Tompkins 59,554; NY 10.6 M; DMV 2026), m = effective additions multiplier
(absorbs net used-EV imports and definitional differences; identified by stock growth given the observed shares).
Calibration: least squares on log(stock + c) at snapshot dates and on new-vehicle EV share (binomial-scaled residuals);
free parameters θ = (t0, k, m) with s_max = 1 in the historical fit; b(v) fitted separately.
Projection (status-quo anchored): start from the *observed* DMV 2026-09 EV stock by model year and drivetrain,
survive cohorts conditionally, add future cohorts A(y) = N_new m s(y) (EV capped at 0.99 F); scenario share paths start at
the observed recent new-vehicle share s_obs (mean of the two DMV 12-month windows ending Aug 2025/2026).
Validation: backcast — fit with observations up to 2021-12, predict 2022–2026 stock and shares (Tompkins and NY).
Uncertainty: Monte Carlo over θ ~ N(θ̂, Σ̂) (Gauss–Newton covariance), N_new ±15 %, λ ±2 y.
Scenarios for s(y) after 2026 (anchored at s_obs):
  trend   – logistic with the fitted steepness k and midpoint shifted so that s(2026) = s_obs (s_max = 1)
  slow    – s_max = 0.6 with half the fitted steepness
  stall   – share flat at s_obs until 2030, then the trend curve shifted by +4 years
  policy  – linear ramp from s_obs to 100 % of new additions by 2035 (ACC II-like; upper bound)
Outputs
  results/tables/growth_fit_params.csv, growth_backcast_validation.csv, growth_projection_tompkins.csv
  data/processed/growth/growth_parameters_by_year.csv   (scenario × year: s, b, EV/BEV/PHEV p05/p50/p95, fleet share)
  results/figures/growth_backcast.png, growth_projection_tompkins.png
Evidence: calibrated to A/D observations; projections are model output (E) conditional on scenario assumptions.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from src.utils.paths import FIGURES, PROCESSED, TABLES, ensure

YEARS = np.arange(2005, 2051)
KAPPA, LAMBDA = 3.5, 17.0
RNG = np.random.default_rng(42)
GEO = {"tompkins": {"N_new": 3600.0, "F": 59554.0, "c": 10.0}, "ny": {"N_new": 1.0e6, "F": 10.6e6, "c": 1000.0}}


def survival(a, lam=LAMBDA):
    a = np.clip(a, 0, None)
    return np.exp(-(a / lam) ** KAPPA)


def logistic(v, smax, k, t0):
    return smax / (1 + np.exp(-k * (v - t0)))


def simulate(share_fn, bev_fn, N_new, F, m, lam=LAMBDA):
    """Return year-end EV, BEV, PHEV stock (index = YEARS) given share and BEV-share functions of year."""
    add_b, add_p = np.zeros(len(YEARS)), np.zeros(len(YEARS))
    ev_end = np.zeros(len(YEARS))
    for i, v in enumerate(YEARS):
        prev = ev_end[i - 1] if i else 0.0
        A = N_new * m * share_fn(v)
        bs = bev_fn(v)
        add_b[i], add_p[i] = A * bs, A * (1 - bs)
        age = (v + 1) - (YEARS[: i + 1] + 0.5)
        sv = survival(age, lam)
        ev_end[i] = np.sum((add_b[: i + 1] + add_p[: i + 1]) * sv)
    ages = (YEARS[:, None] + 1) - (YEARS[None, :] + 0.5)
    mask = ages > 0
    S = np.where(mask, survival(ages, lam), 0)
    bev = S @ add_b
    phev = S @ add_p
    return pd.DataFrame({"year": YEARS, "EV": bev + phev, "BEV": bev, "PHEV": phev, "additions": add_b + add_p})


def at_time(df: pd.DataFrame, col: str, t: np.ndarray) -> np.ndarray:
    # year-end values at t = year + 1; interpolate
    return np.interp(t, df["year"].values + 1.0, df[col].values)


def observations(geo: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if geo == "tompkins":
        ts = pd.read_csv(TABLES / "tompkins_ev_stock_timeseries.csv", parse_dates=["snapshot_date"])
        e = ts[ts["source"].str.startswith("EValuateNY")].copy()
        e = e.sort_values("snapshot_date").groupby(e["snapshot_date"].dt.year).tail(1)
        z = ts[ts["source"].str.contains("method-consistent")]
        st = pd.concat([e, z])
        stock = pd.DataFrame({"t": st["snapshot_date"].dt.year + (st["snapshot_date"].dt.dayofyear / 365.25), "EV": st["EV"], "BEV": st["BEV"], "PHEV": st["PHEV"]})
        inf = pd.read_csv(PROCESSED / "growth" / "tompkins_inflows_by_year.csv")
    else:
        s = pd.read_parquet(PROCESSED / "evaluateny" / "ev_stock_zip_snapshot.parquet")
        s = s[s["drivetrain"].isin(["BEV", "PHEV"])].groupby(["snapshot_date", "drivetrain"])["vehicles"].sum().unstack().reset_index()
        s = s.sort_values("snapshot_date").groupby(s["snapshot_date"].dt.year).tail(1)
        c = pd.read_csv(PROCESSED / "dmv" / "ny_county_ev_2026.csv")
        c = c[c["county"] != "OUT-OF-STATE"]
        d26 = pd.DataFrame({"snapshot_date": [pd.Timestamp("2026-09-02")], "BEV": [c["bev"].sum()], "PHEV": [c["phev"].sum()]})
        s = pd.concat([s, d26])
        stock = pd.DataFrame({"t": s["snapshot_date"].dt.year + s["snapshot_date"].dt.dayofyear / 365.25, "BEV": s["BEV"], "PHEV": s["PHEV"]})
        stock["EV"] = stock["BEV"] + stock["PHEV"]
        inf = pd.read_csv(PROCESSED / "growth" / "ny_inflows_by_year.csv")
        inf["source"] = "EValuateNY first appearances"
    inf = inf[inf["light_duty"] & (inf["age_class"] == "new")]
    p = inf.pivot_table(index=["source", "year"], columns="dt", values="vehicles", aggfunc="sum").fillna(0).reset_index()
    p["n"] = p[["BEV", "PHEV", "nonEV"]].sum(axis=1)
    p["share"] = (p["BEV"] + p["PHEV"]) / p["n"]
    p["bev_share"] = p["BEV"] / (p["BEV"] + p["PHEV"]).replace(0, np.nan)
    dmv = p["source"].str.startswith("DMV")
    p["t"] = np.where(dmv, p["year"] - 1 + 0.67, np.where(p["year"] == 2023, 2023.15, p["year"] + 0.5))
    p = p[(p["year"] >= 2013)]
    return stock.reset_index(drop=True), p.reset_index(drop=True), inf


def fit(geo: str, t_max: float | None = None) -> dict:
    g = GEO[geo]
    stock, sh, _ = observations(geo)
    if t_max:
        stock, sh = stock[stock["t"] <= t_max], sh[sh["t"] <= t_max]
    shb = sh.dropna(subset=["bev_share"])
    nb = (sh["BEV"] + sh["PHEV"]).loc[shb.index]
    resb = least_squares(lambda q: (logistic(shb["t"], 0.95, q[0], q[1]) - shb["bev_share"]) * np.sqrt(np.maximum(nb, 1)) /
                         np.sqrt(np.clip(shb["bev_share"] * (1 - shb["bev_share"]), 0.02, None)), x0=[0.2, 2020.0],
                         bounds=([0.01, 2000], [2.0, 2050]))
    kb, tb = resb.x
    bev_fn = lambda v: logistic(v, 0.95, kb, tb)  # noqa: E731

    def resid(q):
        t0, k, m = q
        df = simulate(lambda v: logistic(v, 1.0, k, t0), bev_fn, g["N_new"], g["F"], m)
        r1 = (np.log(at_time(df, "EV", stock["t"].values) + g["c"]) - np.log(stock["EV"].values + g["c"])) * 3.0
        sm = logistic(sh["t"].values, 1.0, k, t0)
        sig = np.sqrt(np.clip(sh["share"] * (1 - sh["share"]), 1e-4, None) / sh["n"]) + 0.005
        r2 = (sm - sh["share"].values) / sig
        return np.concatenate([r1, r2])

    res = least_squares(resid, x0=[2032.0, 0.25, 1.2], bounds=([2015, 0.02, 0.3], [2080, 1.5, 4.0]))
    J = res.jac
    dof = max(len(res.fun) - len(res.x), 1)
    s2 = 2 * res.cost / dof
    try:
        cov = np.linalg.inv(J.T @ J) * s2
    except np.linalg.LinAlgError:
        cov = np.diag([1.0, 0.01, 0.1])
    return {"geo": geo, "t_max": t_max, "t0": res.x[0], "k": res.x[1], "m": res.x[2], "kb": kb, "tb": tb, "cov": cov,
            "rmse_resid": float(np.sqrt(np.mean(res.fun ** 2))), "n_obs": len(res.fun)}


def share_scenario(name: str, p: dict, s_obs: float):
    """Share of new additions by year for y >= 2026, continuous at s(2026) = s_obs."""
    k = p["k"]
    t0 = 2026 + np.log(1 / s_obs - 1) / k
    trend = lambda v: logistic(v, 1.0, k, t0)  # noqa: E731
    if name == "trend":
        return trend
    if name == "slow":
        k2 = k / 2
        t0s = 2026 + np.log(0.6 / s_obs - 1) / k2
        return lambda v: logistic(v, 0.6, k2, t0s)
    if name == "stall":
        return lambda v: s_obs if v <= 2030 else max(s_obs, trend(v - 4))
    if name == "policy":
        return lambda v: min(1.0, s_obs + (1 - s_obs) * max(0, v - 2026) / (2035 - 2026))
    raise ValueError(name)


def project(share_fn, bev_fn, init: pd.DataFrame, N_new: float, F: float, m: float, lam: float, t_init: float = 2026.67,
            years=range(2026, 2051)) -> pd.DataFrame:
    """Year-end stock y >= 2026 from observed stock by model year at t_init plus future cohorts."""
    mv = init["model_year"].values.astype(float)
    s_init = survival(t_init - (mv + 0.5), lam)
    coh = []  # (birth_time, BEV, PHEV)
    rows = []
    ev_prev = float(init[["BEV", "PHEV"]].sum().sum())
    for y in years:
        frac = (y + 1 - t_init) if y == int(t_init) else 1.0
        A = N_new * m * share_fn(y) * frac
        bs = bev_fn(y)
        birth = (t_init + (y + 1)) / 2 if y == int(t_init) else y + 0.5
        coh.append((birth, A * bs, A * (1 - bs)))
        t_end = y + 1.0
        surv_init = survival(t_end - (mv + 0.5), lam) / np.clip(s_init, 1e-9, None)
        bev = float(np.sum(init["BEV"].values * surv_init)) + sum(cb * survival(t_end - bt, lam) for bt, cb, _ in coh)
        phev = float(np.sum(init["PHEV"].values * surv_init)) + sum(cp * survival(t_end - bt, lam) for bt, _, cp in coh)
        tot = bev + phev
        if tot > 0.99 * F:  # fleet cap (all vehicles electric)
            bev, phev = bev * 0.99 * F / tot, phev * 0.99 * F / tot
        ev_prev = bev + phev
        rows.append({"year": y, "EV": bev + phev, "BEV": bev, "PHEV": phev, "additions": A, "new_share": share_fn(y), "bev_share_add": bs})
    return pd.DataFrame(rows)


def main() -> None:
    ensure(TABLES, FIGURES, PROCESSED / "growth")
    fits = {}
    rows = []
    for geo in ["tompkins", "ny"]:
        for label, tmax in [("full", None), ("backcast_le2021", 2022.0)]:
            f = fit(geo, tmax)
            fits[(geo, label)] = f
            rows.append({k: v for k, v in f.items() if k != "cov"} | {"fit": label,
                         "se_t0": float(np.sqrt(f["cov"][0, 0])), "se_k": float(np.sqrt(f["cov"][1, 1])), "se_m": float(np.sqrt(f["cov"][2, 2]))})
    pd.DataFrame(rows).round(4).to_csv(TABLES / "growth_fit_params.csv", index=False)

    # backcast validation
    val = []
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for gi, geo in enumerate(["tompkins", "ny"]):
        g = GEO[geo]
        stock, sh, _ = observations(geo)
        for label, ls in [("full", "-"), ("backcast_le2021", "--")]:
            f = fits[(geo, label)]
            df = simulate(lambda v, f=f: logistic(v, 1.0, f["k"], f["t0"]), lambda v, f=f: logistic(v, 0.95, f["kb"], f["tb"]), g["N_new"], g["F"], f["m"])
            yy = df["year"] + 1
            axes[0, gi].plot(yy, df["EV"], ls=ls, label=f"model ({label})")
            axes[1, gi].plot(YEARS + 0.5, logistic(YEARS + 0.5, 1.0, f["k"], f["t0"]), ls=ls, label=f"model ({label})")
            if label == "backcast_le2021":
                hold = stock[stock["t"] > 2022.0]
                for _, r in hold.iterrows():
                    pred = at_time(df, "EV", np.array([r["t"]]))[0]
                    val.append({"geo": geo, "quantity": "EV stock", "t": round(r["t"], 2), "observed": r["EV"], "predicted": pred, "ape": abs(pred - r["EV"]) / r["EV"]})
                for _, r in sh[sh["t"] > 2022.0].iterrows():
                    pred = logistic(r["t"], 1.0, f["k"], f["t0"])
                    val.append({"geo": geo, "quantity": "EV share of new additions", "t": round(r["t"], 2), "observed": r["share"], "predicted": pred, "ape": abs(pred - r["share"]) / r["share"]})
        axes[0, gi].scatter(stock["t"], stock["EV"], color="k", s=14, zorder=3, label="observed (EValuateNY / DMV 2026)")
        axes[0, gi].axvline(2022, color="grey", lw=0.8)
        axes[0, gi].set_xlim(2011, 2031); axes[0, gi].set_title(f"{geo}: EV stock (backcast fit ≤2021 dashed)"); axes[0, gi].legend(fontsize=7)
        axes[0, gi].set_ylim(0, stock["EV"].max() * 2.2)
        axes[1, gi].scatter(sh["t"], sh["share"], color="k", s=14, zorder=3, label="observed new-vehicle EV share")
        axes[1, gi].axvline(2022, color="grey", lw=0.8)
        axes[1, gi].set_xlim(2011, 2031); axes[1, gi].set_ylim(0, 0.35); axes[1, gi].set_title(f"{geo}: EV share of new additions"); axes[1, gi].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIGURES / "growth_backcast.png", dpi=140); plt.close(fig)
    pd.DataFrame(val).round(4).to_csv(TABLES / "growth_backcast_validation.csv", index=False)

    # projections with Monte Carlo (Tompkins), anchored at the observed DMV 2026-09 stock by model year
    f = fits[("tompkins", "full")]
    g = GEO["tompkins"]
    init = pd.read_csv(PROCESSED / "dmv" / "tompkins_ev_model_year_2026.csv").rename(columns={"model_year_n": "model_year"})
    init = init[init["model_year"].notna()]
    stock, sh, _ = observations("tompkins")
    s_obs = float(sh[sh["source"].str.startswith("DMV")]["share"].mean())
    draws = RNG.multivariate_normal([f["t0"], f["k"], f["m"]], f["cov"], size=400)
    bfn = lambda v: logistic(v, 0.95, f["kb"], f["tb"])  # noqa: E731
    out = []
    for sc in ["trend", "slow", "stall", "policy"]:
        sims = []
        for dd in draws:
            prm = {"t0": dd[0], "k": float(np.clip(dd[1], 0.05, 1.0)), "m": float(np.clip(dd[2], 0.3, 4.0))}
            N = g["N_new"] * RNG.uniform(0.85, 1.15)
            lam = LAMBDA + RNG.uniform(-2, 2)
            sims.append(project(share_scenario(sc, prm, s_obs), bfn, init, N, g["F"], prm["m"], lam))
        allsim = pd.concat([x.assign(draw=i) for i, x in enumerate(sims)])
        for y, gg in allsim.groupby("year"):
            out.append({"scenario": sc, "year": int(y), "new_share_p50": float(gg["new_share"].median()),
                        "bev_share_of_additions": float(gg["bev_share_add"].median()),
                        "additions_p50": float(gg["additions"].median()),
                        "EV_p05": float(gg["EV"].quantile(.05)), "EV_p50": float(gg["EV"].median()), "EV_p95": float(gg["EV"].quantile(.95)),
                        "BEV_p50": float(gg["BEV"].median()), "PHEV_p50": float(gg["PHEV"].median()),
                        "fleet_share_p05": float(gg["EV"].quantile(.05) / g["F"]), "fleet_share_p50": float(gg["EV"].median() / g["F"]),
                        "fleet_share_p95": float(gg["EV"].quantile(.95) / g["F"])})
    proj = pd.DataFrame(out)
    proj.insert(2, "s_obs_2026", s_obs)
    proj.round(4).to_csv(TABLES / "growth_projection_tompkins.csv", index=False)
    proj.round(4).to_csv(PROCESSED / "growth" / "growth_parameters_by_year.csv", index=False)

    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    for sc, col in zip(["trend", "slow", "stall", "policy"], ["tab:blue", "tab:orange", "tab:grey", "tab:green"]):
        q = proj[proj["scenario"] == sc]
        ax[0].plot(q["year"] + 1, q["EV_p50"], color=col, label=sc)
        ax[0].fill_between(q["year"] + 1, q["EV_p05"], q["EV_p95"], color=col, alpha=0.15)
        ax[1].plot(q["year"] + 0.5, q["new_share_p50"], color=col, label=sc)
    ax[0].scatter(stock["t"], stock["EV"], color="k", s=12, zorder=3, label="observed (ZIP-weighted history)")
    ax[0].scatter([2026.67], [init[["BEV", "PHEV"]].sum().sum()], color="red", marker="s", s=30, zorder=4, label="DMV 2026-09 (county field)")
    ax[0].set_title("Tompkins EV stock: history and projections (median, 90% band)"); ax[0].set_ylabel("EVs"); ax[0].legend(fontsize=8)
    ax[1].scatter(sh["t"], sh["share"], color="k", s=12, zorder=3, label="observed")
    ax[1].set_title("EV share of new light-duty additions"); ax[1].set_ylim(0, 1.02); ax[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIGURES / "growth_projection_tompkins.png", dpi=140); plt.close(fig)
    print(pd.DataFrame(rows).round(3).to_string())
    print(pd.DataFrame(val).round(3).to_string())
    print("s_obs", round(s_obs, 4))
    print(proj[proj["year"].isin([2026, 2030, 2035, 2040, 2050])][["scenario", "year", "new_share_p50", "EV_p05", "EV_p50", "EV_p95", "fleet_share_p50"]].round(3).to_string())


if __name__ == "__main__":
    main()
