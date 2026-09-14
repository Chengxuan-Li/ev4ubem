"""Cross-sectional NY ZIP-level EV adoption vs ACS characteristics (ecological analysis).

Purpose: determine which area-level housing/household characteristics carry information for
*downscaling* observed EV counts, and how well they transfer to held-out geographies (incl. Tompkins).
This is an ecological (area-level) analysis: coefficients describe ZIP-level association, not household
behaviour, and must not be read causally.

Data
- Response (year=2023, April 2023): EValuateNY v11 Current Registrations, VIN-decoded; EV = BEV + PHEV (all categories);
  vehicles = all registered vehicles in the ZIP (all drivetrains incl. UNKNOWN).
- Response (year=2026): DMV snapshot 2026-09 VIN-decoded (data/processed/dmv/ny_zip_drivetrain_2026.parquet);
  run `python -m src.analysis.zip_ev_penetration 2026`.
- Predictors: ACS 2020-2024 5-year ZCTA features (ZIP treated as ZCTA; PO-box ZIPs without ZCTA dropped).
- County for grouping: county with the largest population share of the ZCTA.
Sample filter: households >= 300 and vehicles >= 200 (stability).
Models
- M0 offset-only Poisson (constant EVs per household)
- M1 NB2 GLM: log E[EV] = log(households) + b'x   (statsmodels, alpha estimated by NB MLE)
- M2 same with a reduced interpretable set; VIFs reported
- M3 HistGradientBoosting (Poisson loss) on EV per household with household weights (predictive benchmark)
Validation: 10-fold county-grouped CV (whole counties held out) -> Poisson deviance, MAE on EV counts,
and Tompkins County ZIPs predicted by models fit without Tompkins.
Outputs: results/tables/zip_ev_model_*.csv, results/figures/zip_ev_*.png
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.utils.paths import FIGURES, PROCESSED, TABLES, ensure

FEATURES_FULL = ["log_income", "ba_plus_share", "owner_sfd_share", "renter_mf5_share", "log_density", "veh_per_hh",
                 "zero_veh_share", "commute30plus_share", "wfh_share", "transit_share", "college_share", "med_age",
                 "built2000plus_share", "log_home_value", "inc150k_share"]
FEATURES_SMALL = ["log_income", "ba_plus_share", "owner_sfd_share", "log_density", "veh_per_hh", "commute30plus_share", "college_share"]
TOMPKINS = "36109"


def load_2023() -> pd.DataFrame:
    f = pd.read_parquet(PROCESSED / "evaluateny" / "fleet_zip_2023-04.parquet")
    g = f.assign(ev=f["drivetrain"].isin(["BEV", "PHEV"]) * f["vehicles"],
                 bev=(f["drivetrain"] == "BEV") * f["vehicles"], phev=(f["drivetrain"] == "PHEV") * f["vehicles"])
    z = g.groupby("zip")[["vehicles", "ev", "bev", "phev"]].sum().reset_index()
    return z


def load_2026() -> pd.DataFrame:
    """DMV 2026-09 statewide snapshot, VIN-decoded (processing/dmv_statewide_ev.py); all VEH rows as denominator."""
    f = pd.read_parquet(PROCESSED / "dmv" / "ny_zip_drivetrain_2026.parquet")
    f = f[f["county"].ne("OUT-OF-STATE") & f["zip"].notna()]
    g = f.assign(ev=f["drivetrain"].isin(["BEV", "PHEV"]) * f["vehicles"],
                 bev=(f["drivetrain"] == "BEV") * f["vehicles"], phev=(f["drivetrain"] == "PHEV") * f["vehicles"])
    return g.groupby("zip")[["vehicles", "ev", "bev", "phev"]].sum().reset_index()


def design(z: pd.DataFrame) -> pd.DataFrame:
    a = pd.read_parquet(PROCESSED / "acs" / "acs_features_ny_zcta.parquet")
    a["zip"] = a["geoid"]
    cz = pd.read_csv(PROCESSED / "geography" / "zcta_county_popshare_ny.csv", dtype={"zcta": str, "county": str})
    main_cty = cz.sort_values("pop_share_of_zcta", ascending=False).drop_duplicates("zcta").set_index("zcta")["county"]
    d = z.merge(a, on="zip", how="inner")
    d["county"] = d["zip"].map(main_cty)
    d["log_income"] = np.log(d["med_hh_income"])
    d["log_density"] = np.log1p(d["pop_density_km2"])
    d["log_home_value"] = np.log(d["med_home_value"])
    d = d[(d["households"] >= 300) & (d["vehicles"] >= 200)]
    d = d.dropna(subset=FEATURES_FULL + ["county"])
    return d.reset_index(drop=True)


def standardize(train: pd.DataFrame, test: pd.DataFrame, cols):
    mu, sd = train[cols].mean(), train[cols].std()
    return (train[cols] - mu) / sd, (test[cols] - mu) / sd


def fit_nb(d: pd.DataFrame, cols, test: pd.DataFrame | None = None):
    Xtr, Xte = standardize(d, d if test is None else test, cols)
    Xtr = sm.add_constant(Xtr)
    y = d["ev"].values
    off = np.log(d["households"].values)
    nb = sm.NegativeBinomial(y, Xtr, offset=off).fit(disp=0, maxiter=200)
    alpha = nb.params["alpha"]
    glm = sm.GLM(y, Xtr, family=sm.families.NegativeBinomial(alpha=alpha), offset=off).fit()
    pred = None
    if test is not None:
        pred = glm.predict(sm.add_constant(Xte, has_constant="add"), offset=np.log(test["households"].values))
    return glm, alpha, pred


def poisson_dev(y, mu):
    y, mu = np.asarray(y, float), np.clip(np.asarray(mu, float), 1e-9, None)
    t = y * np.log(np.where(y > 0, y, 1.0) / mu) * (y > 0)
    return 2 * np.sum(t - (y - mu))


def main(year: int = 2023) -> None:
    ensure(TABLES, FIGURES)
    d = design(load_2023() if year == 2023 else load_2026())
    d["ev_per_hh"] = d["ev"] / d["households"]
    d["ev_share_veh"] = d["ev"] / d["vehicles"]
    print("sample ZIPs:", len(d), "EVs:", int(d["ev"].sum()))

    # descriptive correlations (Spearman) of EV per household with features
    corr = d[FEATURES_FULL + ["ev_per_hh", "ev_share_veh"]].corr(method="spearman")[["ev_per_hh", "ev_share_veh"]].drop(["ev_per_hh", "ev_share_veh"])
    corr.round(3).to_csv(TABLES / f"zip_ev_model_spearman_{year}.csv")

    X = (d[FEATURES_FULL] - d[FEATURES_FULL].mean()) / d[FEATURES_FULL].std()
    vif = pd.DataFrame({"feature": FEATURES_FULL, "vif_full": [variance_inflation_factor(X.values, i) for i in range(len(FEATURES_FULL))]})
    Xs = X[FEATURES_SMALL]
    vif = vif.merge(pd.DataFrame({"feature": FEATURES_SMALL, "vif_small": [variance_inflation_factor(Xs.values, i) for i in range(len(FEATURES_SMALL))]}), how="left")
    vif.round(2).to_csv(TABLES / f"zip_ev_model_vif_{year}.csv", index=False)

    coefs = []
    for name, cols in [("NB_full", FEATURES_FULL), ("NB_small", FEATURES_SMALL)]:
        glm, alpha, _ = fit_nb(d, cols)
        ci = glm.conf_int()
        for k in glm.params.index:
            coefs.append({"model": name, "term": k, "coef": glm.params[k], "irr_per_sd": np.exp(glm.params[k]),
                          "irr_lo": np.exp(ci.loc[k, 0]), "irr_hi": np.exp(ci.loc[k, 1]), "p": glm.pvalues[k], "alpha": alpha,
                          "n": len(d), "deviance_explained": 1 - glm.deviance / glm.null_deviance})
    pd.DataFrame(coefs).round(4).to_csv(TABLES / f"zip_ev_model_nb_coefficients_{year}.csv", index=False)

    # county-grouped CV
    gkf = GroupKFold(n_splits=10)
    preds = {k: np.zeros(len(d)) for k in ["M0_const_rate", "NB_small", "NB_full", "HGB_poisson"]}
    for tr, te in gkf.split(d, groups=d["county"]):
        a, b = d.iloc[tr], d.iloc[te]
        rate = a["ev"].sum() / a["households"].sum()
        preds["M0_const_rate"][te] = rate * b["households"]
        preds["NB_small"][te] = fit_nb(a, FEATURES_SMALL, b)[2]
        preds["NB_full"][te] = fit_nb(a, FEATURES_FULL, b)[2]
        hgb = HistGradientBoostingRegressor(loss="poisson", max_iter=300, learning_rate=0.05, min_samples_leaf=20)
        hgb.fit(a[FEATURES_FULL], a["ev_per_hh"], sample_weight=a["households"])
        preds["HGB_poisson"][te] = hgb.predict(b[FEATURES_FULL]) * b["households"]
    cv = []
    y = d["ev"].values
    for k, p in preds.items():
        cv.append({"model": k, "cv": "10-fold county-grouped", "poisson_deviance": poisson_dev(y, p),
                   "deviance_explained_vs_M0": 1 - poisson_dev(y, p) / poisson_dev(y, preds["M0_const_rate"]),
                   "mae_ev": np.mean(np.abs(y - p)), "median_ape": np.median(np.abs(y - p) / np.maximum(y, 1)),
                   "spearman_rate": pd.Series(p / d["households"]).corr(d["ev_per_hh"], method="spearman")})
    pd.DataFrame(cv).round(4).to_csv(TABLES / f"zip_ev_model_cv_{year}.csv", index=False)

    # Tompkins holdout
    tr, te = d[d["county"] != TOMPKINS], d[d["county"] == TOMPKINS]
    out = te[["zip", "households", "vehicles", "ev", "bev", "phev", "ev_per_hh", "med_hh_income", "owner_sfd_share", "college_share"]].copy()
    out["pred_M0"] = tr["ev"].sum() / tr["households"].sum() * te["households"]
    out["pred_NB_small"] = fit_nb(tr, FEATURES_SMALL, te)[2]
    out["pred_NB_full"] = fit_nb(tr, FEATURES_FULL, te)[2]
    hgb = HistGradientBoostingRegressor(loss="poisson", max_iter=300, learning_rate=0.05, min_samples_leaf=20)
    hgb.fit(tr[FEATURES_FULL], tr["ev_per_hh"], sample_weight=tr["households"])
    out["pred_HGB"] = hgb.predict(te[FEATURES_FULL]) * te["households"]
    for k, p in preds.items():
        out[f"cv_{k}"] = p[d["county"] == TOMPKINS]
    out.round(2).to_csv(TABLES / f"zip_ev_model_tompkins_holdout_{year}.csv", index=False)

    fig, ax = plt.subplots(1, 2, figsize=(10, 4.5))
    for k, m in [("NB_full", "o"), ("HGB_poisson", "x")]:
        ax[0].scatter(d["ev"] + 1, preds[k] + 1, s=6, alpha=0.4, marker=m, label=k)
    lim = [1, d["ev"].max() * 1.5]
    ax[0].plot(lim, lim, "k--", lw=0.8)
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].set_xlabel(f"Observed EVs + 1 ({year})"); ax[0].set_ylabel("County-held-out prediction + 1")
    ax[0].legend(); ax[0].set_title("NY ZIPs, county-grouped CV")
    ax[1].scatter(out["ev"], out["pred_NB_full"], label="NB_full (fit w/o Tompkins)")
    ax[1].scatter(out["ev"], out["pred_M0"], marker="x", label="constant EV/household")
    for _, r in out.iterrows():
        ax[1].annotate(r["zip"], (r["ev"], r["pred_NB_full"]), fontsize=7)
    m = max(out["ev"].max(), out["pred_NB_full"].max()) * 1.1
    ax[1].plot([0, m], [0, m], "k--", lw=0.8)
    ax[1].set_xlabel("Observed EVs"); ax[1].set_ylabel("Predicted EVs"); ax[1].legend(fontsize=8)
    ax[1].set_title("Tompkins ZIPs held out")
    fig.tight_layout()
    fig.savefig(FIGURES / f"zip_ev_model_validation_{year}.png", dpi=150)
    print(pd.DataFrame(cv).round(3).to_string())
    print(out[["zip", "households", "ev", "pred_M0", "pred_NB_small", "pred_NB_full", "pred_HGB"]].round(1).to_string())
    print(pd.DataFrame(coefs).query("model=='NB_full'")[["term", "irr_per_sd", "irr_lo", "irr_hi", "p"]].round(3).to_string())


if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2023)
