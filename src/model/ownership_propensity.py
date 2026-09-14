r"""Household-class EV propensity: ecological calibration on NY ZIPs with weak priors, and allocation-skill validation.

Model (mean-field over ACS composition; ZIP z):
  μ_z = exp(β0 + γᵀ Z_z) · I_z · Σ_τ HH_{z,τ} · A_{z,τ} · V_{z,τ}
  A_{z,τ} = Σ_g s_{g|τ,z} exp(a_{g,τ})          structure g ∈ {SF, MF2_4, MF5P, MOBILE}, tenure τ ∈ {own, rent}; a_{SF,own} = 0
  V_{z,τ} = Σ_v s_{v|τ,z} v^η                    vehicles available v ∈ {0..5}; 0 vehicles -> 0 EVs
  I_z     = Σ_i s_{i,z} exp(c_i)                 income bands; c_{50-100k} = 0
  EV_z ~ NegBin2(μ_z, α)
Z_z = standardized log median home value and bachelor's+ share (area effects). Composition from ACS 2020-2024
(`data/processed/acs/composition_ny_zcta.parquet`). The product form assumes independence of income and
tenure/structure/vehicles within a ZIP (mean-field approximation; stated limitation).
Priors (log relative risks, N(mean, 1.0²)): informed by NHTS 2022 household propensities (conditional income odds
ratios) and Drive Clean representation ratios (detached ≈1.85×, apartments ≈0.25×, renters ≈0.3×): see PRIORS.
Estimation: penalized maximum likelihood (L-BFGS-B), Hessian-based standard errors.
Compared models (10-fold county-grouped CV): M0 households only; M1 vehicles only; M2 class model with parameters fixed
at prior means; M3 estimated class model + area covariates; M4 estimated class model without area covariates;
M5 tempered priors: a = ω·log(prior_a), c = ω·log(prior_c), η and ω estimated (ω=0 -> vehicles model, ω=1 -> priors);
M6 separately tempered: a = ω_s·log(prior_a), c = ω_i·log(prior_c).
Selection for allocation: lowest within-county allocation deviance in the cross-year test (fit 2023 -> allocate 2026),
restricted to models whose class parameters are consistent in sign with individual-level evidence (M0, M1, M2, M5, M6);
M3/M4 are reported as ecological diagnostics only (their class estimates are confounded).
Metrics: held-out Poisson deviance explained vs M0; and **within-county allocation skill** — held-out county totals are
taken as known and distributed across that county's ZIPs by each model (mimics distributing an observed total to
sub-areas); share deviance and mean absolute error of EV counts.
Responses: 2023 (EValuateNY, all EVs) and 2026 (DMV, all EVs, NY counties). Cross-year: parameters fit on 2023 used to
allocate 2026 county totals.
Outputs: results/tables/propensity_{params,cv}_*.csv, data/processed/model/propensity_params.json,
         results/figures/propensity_relative_risks.png, propensity_allocation_skill.png
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln
from sklearn.model_selection import GroupKFold

from src.utils.paths import FIGURES, PROCESSED, TABLES, ensure

STRUCT = {"SF": ["SFD", "SFA"], "MF2_4": ["MF2_4"], "MF5P": ["MF5_19", "MF20P"], "MOBILE": ["MOBILE"]}
A_NAMES = ["SF|rent", "MF2_4|own", "MF2_4|rent", "MF5P|own", "MF5P|rent", "MOBILE|own", "MOBILE|rent"]
C_NAMES = ["<50k", "100-150k", "150k+"]
PRIORS = {"SF|rent": 0.60, "MF2_4|own": 0.80, "MF2_4|rent": 0.35, "MF5P|own": 0.70, "MF5P|rent": 0.25,
          "MOBILE|own": 0.30, "MOBILE|rent": 0.20, "<50k": 0.45, "100-150k": 1.50, "150k+": 3.00, "eta": 1.0}
PRIOR_SD = 1.0


def design() -> pd.DataFrame:
    c = pd.read_parquet(PROCESSED / "acs" / "composition_ny_zcta.parquet").rename(columns={"geoid": "zip"})
    f = pd.read_parquet(PROCESSED / "acs" / "acs_features_ny_zcta.parquet")[["geoid", "med_home_value", "ba_plus_share"]].rename(columns={"geoid": "zip"})
    d = c.merge(f, on="zip")
    ev23 = pd.read_parquet(PROCESSED / "evaluateny" / "fleet_zip_2023-04.parquet")
    ev23 = ev23[ev23["drivetrain"].isin(["BEV", "PHEV"])].groupby("zip")["vehicles"].sum().rename("ev2023")
    ev26 = pd.read_parquet(PROCESSED / "dmv" / "ny_zip_drivetrain_2026.parquet")
    ev26 = ev26[ev26["drivetrain"].isin(["BEV", "PHEV"]) & ev26["county"].ne("OUT-OF-STATE")].groupby("zip")["vehicles"].sum().rename("ev2026")
    d = d.merge(ev23, left_on="zip", right_index=True, how="left").merge(ev26, left_on="zip", right_index=True, how="left")
    d[["ev2023", "ev2026"]] = d[["ev2023", "ev2026"]].fillna(0)
    cz = pd.read_csv(PROCESSED / "geography" / "zcta_county_popshare_ny.csv", dtype={"zcta": str, "county": str})
    d["county"] = d["zip"].map(cz.sort_values("pop_share_of_zcta", ascending=False).drop_duplicates("zcta").set_index("zcta")["county"])
    d = d[(d["households"] >= 300)].dropna(subset=["med_home_value", "ba_plus_share", "county"]).reset_index(drop=True)
    for col, src in [("z_home", np.log(d["med_home_value"])), ("z_ba", d["ba_plus_share"])]:
        d[col] = (src - src.mean()) / src.std()
    return d


def arrays(d: pd.DataFrame) -> dict:
    hh_t = {t: sum(d[f"{t}|{c}"] for g in STRUCT for c in STRUCT[g]).values for t in ["own", "rent"]}
    s_g = {(g, t): (sum(d[f"{t}|{c}"] for c in STRUCT[g]).values / np.maximum(hh_t[t], 1e-9)) for g in STRUCT for t in ["own", "rent"]}
    veh_tot = {t: sum(d[f"{t}|veh{k}"] for k in range(6)).values for t in ["own", "rent"]}
    s_v = {(t, k): d[f"{t}|veh{k}"].values / np.maximum(veh_tot[t], 1e-9) for t in ["own", "rent"] for k in range(6)}
    inc_tot = sum(d[f"inc|{b}"] for b in ["<50k", "50-100k", "100-150k", "150k+"]).values
    s_i = {b: d[f"inc|{b}"].values / np.maximum(inc_tot, 1e-9) for b in ["<50k", "50-100k", "100-150k", "150k+"]}
    vehicles = sum(k * d[f"{t}|veh{k}"] for t in ["own", "rent"] for k in range(6)).values
    return {"hh_t": hh_t, "s_g": s_g, "s_v": s_v, "s_i": s_i, "Z": d[["z_home", "z_ba"]].values, "hh": d["households"].values, "veh": vehicles}


def unpack(theta, spec):
    out, i = {}, 0
    for name, n in spec:
        out[name] = theta[i:i + n]
        i += n
    return out


def mu_class(p: dict, X: dict, use_area: bool) -> np.ndarray:
    a = dict(zip(A_NAMES, p["a"]))
    a["SF|own"] = 0.0
    c = dict(zip(C_NAMES, p["c"]))
    c["50-100k"] = 0.0
    eta = p["eta"][0]
    I = sum(X["s_i"][b] * np.exp(c[b]) for b in X["s_i"])
    tot = 0.0
    for t in ["own", "rent"]:
        A = sum(X["s_g"][(g, t)] * np.exp(a[f"{g}|{t}"]) for g in STRUCT)
        V = sum(X["s_v"][(t, k)] * (k ** eta if k > 0 else 0.0) for k in range(6))
        tot = tot + X["hh_t"][t] * A * V
    lin = p["b0"][0] + (X["Z"] @ p["g"] if use_area else 0.0)
    return np.exp(lin) * I * tot


def nb_nll(y, mu, log_alpha):
    alpha = np.exp(log_alpha)
    r = 1 / alpha
    mu = np.clip(mu, 1e-9, None)
    return -np.sum(gammaln(y + r) - gammaln(r) - gammaln(y + 1) + r * np.log(r / (r + mu)) + y * np.log(mu / (r + mu)))


MODELS = {
    "M0_households": {"spec": [("b0", 1), ("g", 2), ("la", 1)], "kind": "offset", "offset": "hh"},
    "M1_vehicles": {"spec": [("b0", 1), ("g", 2), ("la", 1)], "kind": "offset", "offset": "veh"},
    "M2_class_prior_fixed": {"spec": [("b0", 1), ("g", 2), ("la", 1)], "kind": "class_fixed"},
    "M3_class_estimated": {"spec": [("b0", 1), ("g", 2), ("a", 7), ("c", 3), ("eta", 1), ("la", 1)], "kind": "class", "area": True},
    "M4_class_no_area": {"spec": [("b0", 1), ("a", 7), ("c", 3), ("eta", 1), ("la", 1)], "kind": "class", "area": False},
    "M5_tempered_prior": {"spec": [("b0", 1), ("g", 2), ("eta", 1), ("w", 1), ("la", 1)], "kind": "tempered"},
    "M6_tempered_split": {"spec": [("b0", 1), ("g", 2), ("eta", 1), ("w", 2), ("la", 1)], "kind": "tempered"},
}
ALLOCATION_CANDIDATES = ["M0_households", "M1_vehicles", "M2_class_prior_fixed", "M5_tempered_prior", "M6_tempered_split"]


def expand(model: str, p: dict) -> dict:
    """Return class-form parameters (b0, g, a, c, eta) for any class-type model."""
    kind = MODELS[model]["kind"]
    la = np.log([PRIORS[n] for n in A_NAMES])
    lc = np.log([PRIORS[n] for n in C_NAMES])
    if kind == "class_fixed":
        return {"b0": p["b0"], "g": p["g"], "a": la, "c": lc, "eta": np.array([PRIORS["eta"]])}
    if kind == "tempered":
        ws, wi = (p["w"][0], p["w"][0]) if len(p["w"]) == 1 else (p["w"][0], p["w"][1])
        return {"b0": p["b0"], "g": p["g"], "a": ws * la, "c": wi * lc, "eta": p["eta"]}
    q = dict(p)
    if "g" not in q:
        q["g"] = np.zeros(2)
    return q


def predict(model: str, p: dict, X: dict) -> np.ndarray:
    m = MODELS[model]
    if m["kind"] == "offset":
        return np.exp(p["b0"][0] + X["Z"] @ p["g"]) * X[m["offset"]]
    if m["kind"] in ("class_fixed", "tempered"):
        return mu_class(expand(model, p), X, True)
    q = dict(p)
    if not m.get("area", True):
        q["g"] = np.zeros(2)
    return mu_class(q, X, m.get("area", True))


def fit_model(model: str, y: np.ndarray, X: dict):
    m = MODELS[model]
    spec = m["spec"]
    x0 = []
    for name, n in spec:
        if name == "b0":
            x0.append([np.log(max(y.sum(), 1) / (X["hh"].sum() if m.get("offset") != "veh" else X["veh"].sum()))])
        elif name == "a":
            x0.append(np.log([PRIORS[k] for k in A_NAMES]))
        elif name == "c":
            x0.append(np.log([PRIORS[k] for k in C_NAMES]))
        elif name == "eta":
            x0.append([1.0])
        elif name == "la":
            x0.append([-1.0])
        elif name == "w":
            x0.append(np.full(n, 0.5))
        else:
            x0.append(np.zeros(n))
    x0 = np.concatenate([np.atleast_1d(v) for v in x0]).astype(float)
    prior_mean = {"a": np.log([PRIORS[k] for k in A_NAMES]), "c": np.log([PRIORS[k] for k in C_NAMES]), "eta": np.array([PRIORS["eta"]])}

    def obj(theta):
        p = unpack(theta, spec)
        mu = predict(model, p, X)
        pen = sum(np.sum((p[k] - prior_mean[k]) ** 2) / (2 * PRIOR_SD ** 2) for k in prior_mean if k in p)
        return nb_nll(y, mu, p["la"][0]) + pen

    bounds = []
    for name, n in spec:
        bounds += [(-6, 6)] * n if name in ("a", "c") else [(0.2, 2.5)] * n if name == "eta" else [(-8, 4)] * n if name == "la"             else [(0.0, 1.5)] * n if name == "w" else [(-30, 30)] * n
    res = minimize(obj, x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": 3000})
    return unpack(res.x, spec), res


def hessian_se(model: str, p: dict, y, X, eps=1e-4):
    spec = MODELS[model]["spec"]
    theta = np.concatenate([p[k] for k, _ in spec])
    prior_mean = {"a": np.log([PRIORS[k] for k in A_NAMES]), "c": np.log([PRIORS[k] for k in C_NAMES]), "eta": np.array([PRIORS["eta"]])}

    def obj(th):
        q = unpack(th, spec)
        pen = sum(np.sum((q[k] - prior_mean[k]) ** 2) / (2 * PRIOR_SD ** 2) for k in prior_mean if k in q)
        return nb_nll(y, predict(model, q, X), q["la"][0]) + pen
    n = len(theta)
    H = np.zeros((n, n))
    f0 = obj(theta)
    for i in range(n):
        for j in range(i, n):
            ei, ej = np.zeros(n), np.zeros(n)
            ei[i], ej[j] = eps, eps
            H[i, j] = H[j, i] = (obj(theta + ei + ej) - obj(theta + ei) - obj(theta + ej) + f0) / eps ** 2
    try:
        cov = np.linalg.inv(H)
        return unpack(np.sqrt(np.clip(np.diag(cov), 0, None)), spec)
    except np.linalg.LinAlgError:
        return unpack(np.full(n, np.nan), spec)


def subset(X: dict, idx) -> dict:
    out = {}
    for k, v in X.items():
        if isinstance(v, dict):
            out[k] = {kk: vv[idx] for kk, vv in v.items()}
        else:
            out[k] = v[idx]
    return out


def poisson_dev(y, mu):
    mu = np.clip(mu, 1e-9, None)
    t = y * np.log(np.where(y > 0, y, 1.0) / mu) * (y > 0)
    return 2 * np.sum(t - (y - mu))


def within_county_skill(d: pd.DataFrame, y: np.ndarray, pred: np.ndarray) -> dict:
    """Rescale predictions to known county totals; score ZIP allocation within counties with >= 3 ZIPs."""
    df = pd.DataFrame({"county": d["county"].values, "y": y, "p": pred})
    df = df[df.groupby("county")["y"].transform("size") >= 3]
    df["alloc"] = df["p"] / df.groupby("county")["p"].transform("sum") * df.groupby("county")["y"].transform("sum")
    return {"alloc_poisson_dev": poisson_dev(df["y"].values, df["alloc"].values), "alloc_mae": float(np.mean(np.abs(df["y"] - df["alloc"]))),
            "alloc_n_zips": len(df)}


def main() -> None:
    ensure(TABLES, FIGURES, PROCESSED / "model")
    d = design()
    X = arrays(d)
    gkf = GroupKFold(n_splits=10)
    cv_rows, par_rows, fitted = [], [], {}
    for year in [2023, 2026]:
        y = d[f"ev{year}"].values.astype(float)
        preds = {m: np.zeros(len(d)) for m in MODELS}
        for tr, te in gkf.split(d, groups=d["county"]):
            Xtr, Xte = subset(X, tr), subset(X, te)
            for m in MODELS:
                p, _ = fit_model(m, y[tr], Xtr)
                preds[m][te] = predict(m, p, Xte)
        base = poisson_dev(y, preds["M0_households"])
        for m in MODELS:
            sk = within_county_skill(d, y, preds[m])
            cv_rows.append({"year": year, "model": m, "cv_poisson_dev": poisson_dev(y, preds[m]),
                            "dev_explained_vs_M0": 1 - poisson_dev(y, preds[m]) / base, "mae": float(np.mean(np.abs(y - preds[m]))), **sk})
        for m in MODELS:
            p, res = fit_model(m, y, X)
            fitted[(year, m)] = p
            if MODELS[m]["kind"] == "tempered":
                se = hessian_se(m, p, y, X)
                for i, nm in enumerate(["omega"] if len(p["w"]) == 1 else ["omega_structure_tenure", "omega_income"]):
                    par_rows.append({"year": year, "model": m, "param": nm, "estimate": p["w"][i], "se": se["w"][i], "n_zips": len(d), "converged": bool(res.success)})
                for k, names in [("eta", ["eta"]), ("g", ["z_log_home_value", "z_ba_share"])]:
                    for i, nm in enumerate(names):
                        par_rows.append({"year": year, "model": m, "param": nm, "estimate": p[k][i], "se": se[k][i], "n_zips": len(d), "converged": bool(res.success)})
            if MODELS[m]["kind"] == "class":
                se = hessian_se(m, p, y, X)
                for k, names in [("a", A_NAMES), ("c", C_NAMES), ("eta", ["eta"]), ("g", ["z_log_home_value", "z_ba_share"])]:
                    if k not in p:
                        continue
                    for i, nm in enumerate(names):
                        est = p[k][i]
                        prior = np.log(PRIORS[nm]) if nm in PRIORS and k != "eta" else (PRIORS["eta"] if k == "eta" else np.nan)
                        par_rows.append({"year": year, "model": m, "param": nm, "estimate": est, "se": se[k][i],
                                         "rel_risk": np.exp(est) if k in ("a", "c") else np.nan,
                                         "rr_lo": np.exp(est - 1.96 * se[k][i]) if k in ("a", "c") else np.nan,
                                         "rr_hi": np.exp(est + 1.96 * se[k][i]) if k in ("a", "c") else np.nan,
                                         "prior_rel_risk": PRIORS.get(nm) if k in ("a", "c") else (PRIORS["eta"] if k == "eta" else np.nan),
                                         "n_zips": len(d), "converged": bool(res.success)})
    # cross-year: 2023-fitted M3 allocating 2026 county totals
    y26 = d["ev2026"].values.astype(float)
    for m in MODELS:
        sk = within_county_skill(d, y26, predict(m, fitted[(2023, m)], X))
        cv_rows.append({"year": "fit2023->alloc2026", "model": m, **sk})
    cv = pd.DataFrame(cv_rows)
    cv.round(4).to_csv(TABLES / "propensity_cv.csv", index=False)
    par = pd.DataFrame(par_rows)
    par.round(4).to_csv(TABLES / "propensity_params.csv", index=False)
    xy = cv[(cv["year"] == "fit2023->alloc2026") & cv["model"].isin(ALLOCATION_CANDIDATES)]
    selected = xy.sort_values("alloc_poisson_dev")["model"].iloc[0]
    alts = {}
    for m in ALLOCATION_CANDIDATES + ["M3_class_estimated"]:
        pm = fitted[(2026, m)]
        e = expand(m, pm) if MODELS[m]["kind"] != "offset" else {"b0": pm["b0"], "g": pm["g"], "a": np.zeros(7), "c": np.zeros(3),
                                                              "eta": np.array([1.0 if m == "M1_vehicles" else 0.0])}
        alts[m] = {k: np.asarray(v).tolist() for k, v in e.items()}
    best = {k: np.asarray(v) for k, v in alts[selected].items()}
    json.dump({k: v.tolist() for k, v in best.items()} | {"selected_model": selected, "alternatives": alts, "A_NAMES": A_NAMES, "C_NAMES": C_NAMES, "STRUCT": STRUCT,
              "z_home_mean_sd": [float(np.log(d["med_home_value"]).mean()), float(np.log(d["med_home_value"]).std())],
              "z_ba_mean_sd": [float(d["ba_plus_share"].mean()), float(d["ba_plus_share"].std())], "fit": "2026 fit on all NY ZIPs"},
              open(PROCESSED / "model" / "propensity_params.json", "w"), indent=2)

    q = par[par["model"] == "M3_class_estimated"]
    q = q[q["param"].isin(A_NAMES + C_NAMES)]
    fig, ax = plt.subplots(figsize=(7, 5.5))
    names = A_NAMES + C_NAMES
    yy = np.arange(len(names))
    for off, yr, col in [(-0.15, 2023, "tab:blue"), (0.15, 2026, "tab:red")]:
        r = q[q["year"] == yr].set_index("param").loc[names]
        ax.errorbar(r["rel_risk"], yy + off, xerr=[r["rel_risk"] - r["rr_lo"], r["rr_hi"] - r["rel_risk"]], fmt="o", color=col, label=f"estimated {yr}")
    ax.scatter([PRIORS[n] for n in names], yy, marker="x", color="k", label="prior mean")
    ax.set_yticks(yy); ax.set_yticklabels(["struct|tenure " + n if n in A_NAMES else "income " + n for n in names])
    ax.set_xscale("log"); ax.axvline(1, color="grey", lw=0.6)
    ax.set_xlabel("relative EV propensity (ref: single-family owner; income 50-100k)")
    ax.set_title("Household-class propensities: ecological estimates (NY ZIPs) vs priors"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIGURES / "propensity_relative_risks.png", dpi=140); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    c1 = cv[cv["year"].isin([2023, 2026])]
    for i, yr in enumerate([2023, 2026]):
        r = c1[c1["year"] == yr]
        ax[0].bar(np.arange(len(r)) + (i - 0.5) * 0.38, r["dev_explained_vs_M0"], width=0.38, label=str(yr))
        ax[1].bar(np.arange(len(r)) + (i - 0.5) * 0.38, r["alloc_mae"], width=0.38, label=str(yr))
    for a_ in ax:
        a_.set_xticks(range(len(MODELS))); a_.set_xticklabels([m.split("_", 1)[1] for m in MODELS], rotation=30, ha="right", fontsize=8); a_.legend()
    ax[0].set_title("Held-out county CV: deviance explained vs households-only")
    ax[1].set_title("Within-county ZIP allocation MAE (EVs), county totals known")
    fig.tight_layout(); fig.savefig(FIGURES / "propensity_allocation_skill.png", dpi=140); plt.close(fig)
    print(cv.round(3).to_string())
    print(q[["year", "param", "rel_risk", "rr_lo", "rr_hi", "prior_rel_risk"]].round(3).to_string())
    print(par[par["param"].isin(["eta", "z_log_home_value", "z_ba_share", "omega", "omega_structure_tenure", "omega_income"])][["year", "model", "param", "estimate", "se"]].round(3).to_string())
    print("selected for allocation:", selected)


if __name__ == "__main__":
    main()
