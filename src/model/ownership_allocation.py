r"""EV ownership allocation to synthetic dwelling units: 2026 status quo (observed ZIP totals) and annual evolution to 2050.

Dwelling-unit weight (household-class propensity; parameters of the selected model in data/processed/model/propensity_params.json):
  w_d = exp(γᵀ Z_bg(d)) · exp(a_{g(d),τ(d)}) · v_d^η · exp(c_{i(d)}),   v_d = vehicles available (w_d = 0 if v_d = 0)
  Z_bg = BG log median home value and bachelor's+ share standardized with the NY ZCTA means/SDs used in fitting
  (BG-level covariates are noisier than ZCTA-level; missing BG values -> 0).
Status quo 2026 (per ZIP z, T_z = observed personal light-duty EVs, DMV `PAS` class, county = TOMPKINS):
  expected EVs E_d = T_z · w_d / Σ_{d∈z} w_d, iteratively capped at v_d (excess redistributed within the ZIP).
  Realizations: T_z vehicle slots drawn without replacement with slot weight w_d / v_d (Efraimidis–Spirakis keys);
  drivetrain per EV ~ Bernoulli(BEV share of ZIP z).
Structural alternatives (same totals): S_uniform (w=1 per household with a vehicle), S_vehicles (w = v_d),
  S_individual (NHTS 2022 conditional odds ratios: income, single-family, tenure; w ∝ v_d), S_prior (full priors,
  concentration upper bound), S_model (selected ecological model) -> spread = structural uncertainty below ZIP.
Central estimate (decision 0005): equal-weight ensemble of S_model (validated between ZIPs) and S_individual (evidence on
  within-area household composition); realizations draw one of the two per draw (structural + sampling uncertainty).
Evolution (year y, growth scenario σ from data/processed/growth/growth_parameters_by_year.csv):
  T_county^pers(y) = EV_p50(σ, y) · ρ_pers,   ρ_pers = personal share of Tompkins EVs in 2026 (observed)
  penetration ratio q(y) = EV(y)/EV(2026);  convergence exponent φ(y) = φ₂^{log2 q(y)}  with φ₂ = 0.90 per doubling
  (from NY ZIP rate regression 2023→2026, results/tables/adoption_concentration_ny.csv)
  ZIP shares: π_z(y) ∝ π_z(2026)^{φ(y)} · h_z^{1-φ(y)}   (h_z = household share) ;  DU weights w_d(y) = w_d^{φ(y)}
  BEV share of personal EVs follows the county BEV/(BEV+PHEV) median path.
  Housing stock held at 2026 (new construction not modelled).
Fleet/organizational EVs (non-PAS or non-LDV, Tompkins-area ZIPs) are placed on commercial/industrial/public-service/
  community parcels (RPS classes 4xx, 5xx, 6xx, 7xx, 8xx) proportional to gross floor area within the ZIP
  (low confidence; no public depot data).
Outputs
  data/processed/model/du_ev_2026.parquet            du_id, parcel, bg, zcta, structure, tenure, income_band, veh, w,
                                                     E_ev, E_bev, E_phev, p_any_ev (realizations), E_ev_uniform, E_ev_vehicles, E_ev_individual, E_ev_prior
  data/processed/model/du_ev_by_year_trend.parquet   du_id x years {2026, 2030, 2035, 2040, 2045, 2050} expected EVs (trend)
  data/processed/model/fleet_ev_sites_2026.csv       parcel-level fleet EV expectation
  results/tables/allocation_*.csv, results/figures/allocation_*.png, results/maps/allocation_*.png
"""
from __future__ import annotations

import json

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.paths import FIGURES, MAPS, PROCESSED, RAW, TABLES, ensure

SEED = 7
R_DRAWS = 200
PHI_PER_DOUBLING = 0.90
YEARS_OUT = [2026, 2030, 2035, 2040, 2045, 2050]
G_MAP = {"SFD": "SF", "SFA": "SF", "MF2_4": "MF2_4", "MF5_19": "MF5P", "MF20P": "MF5P", "MOBILE": "MOBILE"}


def load_units() -> pd.DataFrame:
    du = pd.read_parquet(PROCESSED / "synthetic" / "dwelling_units.parquet")
    du["zcta"] = du["zcta"].fillna("unknown")
    return du


def weights(du: pd.DataFrame, params: dict, mode: str = "model") -> np.ndarray:
    v = du["veh"].values.astype(float)
    if mode == "uniform":
        return np.where(v > 0, 1.0, 0.0)
    if mode == "vehicles":
        return v
    if mode == "individual":
        # NHTS 2022 conditional logit (income ORs relative to 50-100k; detached/attached OR 1.31; owner OR ~0.96),
        # EVs proportional to vehicles; no area effect
        inc = {"<50k": 0.48, "50-100k": 1.0, "100-150k": 1.51, "150k+": 3.23}
        sf = np.where(du["structure"].isin(["SFD", "SFA"]), 1.31, 1.0)
        ten = np.where(du["tenure"].eq("own"), 0.96, 1.0)
        return v * sf * ten * du["income_band"].map(inc).fillna(1.0).values
    if mode == "prior":
        from src.model.ownership_propensity import A_NAMES, C_NAMES, PRIORS
        a = dict(zip(A_NAMES, np.log([PRIORS[n] for n in A_NAMES])))
        c = dict(zip(C_NAMES, np.log([PRIORS[n] for n in C_NAMES])))
        eta, g = PRIORS["eta"], np.zeros(2)
    else:
        a, c = dict(zip(params["A_NAMES"], params["a"])), dict(zip(params["C_NAMES"], params["c"]))
        eta, g = params["eta"][0], np.array(params["g"])
    a["SF|own"] = 0.0
    c["50-100k"] = 0.0
    f = pd.read_parquet(PROCESSED / "acs" / "acs_features_tompkins_bg.parquet")[["geoid", "med_home_value", "ba_plus_share"]]
    zh = (np.log(f["med_home_value"]) - params["z_home_mean_sd"][0]) / params["z_home_mean_sd"][1]
    zb = (f["ba_plus_share"] - params["z_ba_mean_sd"][0]) / params["z_ba_mean_sd"][1]
    area = pd.Series(np.exp(g[0] * zh.fillna(0) + g[1] * zb.fillna(0)).values, index=f["geoid"].values)
    key = du["structure"].map(G_MAP) + "|" + du["tenure"]
    w = (du["bg"].map(area).fillna(1.0).values * np.exp(key.map(a).values) * np.where(v > 0, v ** eta, 0.0) * du["income_band"].map(c).fillna(0).map(np.exp).values)
    return w


def capped_allocation(total: float, w: np.ndarray, cap: np.ndarray) -> np.ndarray:
    E = np.zeros_like(w, dtype=float)
    free = (w > 0) & (cap > 0)
    remaining = total
    for _ in range(50):
        if remaining <= 1e-9 or not free.any():
            break
        add = remaining * w * free / (w * free).sum()
        E = E + add
        over = E > cap
        remaining = float((E[over] - cap[over]).sum())
        E[over] = cap[over]
        free = free & ~over
    return E


def observed_zip_totals() -> tuple[pd.DataFrame, float]:
    d = pd.read_csv(PROCESSED / "dmv" / "tompkins_ev_stock_zip_2026.csv", dtype={"zip": str})
    ev = d[d["drivetrain"].isin(["BEV", "PHEV"])].copy()
    ev["zip"] = ev["zip"].replace({"14851": "14850", "14852": "14850"})
    pers = ev[(ev["class_group"] == "PAS") & ev["is_ldv"]]
    t = pers.pivot_table(index="zip", columns="drivetrain", values="vehicles", aggfunc="sum").fillna(0)
    t["EV"] = t["BEV"] + t["PHEV"]
    rho = float(pers["vehicles"].sum() / ev["vehicles"].sum())
    fleet = ev[~((ev["class_group"] == "PAS") & ev["is_ldv"])].groupby("zip")["vehicles"].sum()
    t = t.join(fleet.rename("fleet_EV"), how="outer").fillna(0)
    return t, rho


def allocate_status_quo(du: pd.DataFrame, tz: pd.DataFrame, wlist: list[np.ndarray], rng) -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    """Central expected allocation = mean of the capped allocations under each weight array; realizations draw a
    weight array at random per draw (structural + sampling uncertainty)."""
    cap = du["veh"].values.astype(float)
    E = np.zeros(len(du))
    Eb = np.zeros(len(du))
    hits = np.zeros(len(du))
    bg_draws = []
    zips_in_model = set(du["zcta"])
    variant_of_draw = rng.integers(len(wlist), size=R_DRAWS)
    for z, row in tz.iterrows():
        if z not in zips_in_model or row["EV"] <= 0:
            continue
        idx = np.where(du["zcta"].values == z)[0]
        T = int(round(row["EV"]))
        Ez = np.mean([capped_allocation(T, w[idx], cap[idx]) for w in wlist], axis=0)
        E[idx] = Ez
        Eb[idx] = Ez * row["BEV"] / row["EV"]
        slots = np.repeat(idx, cap[idx].astype(int))
        for r in range(R_DRAWS):
            w = wlist[variant_of_draw[r]]
            sw = np.repeat(w[idx] / np.maximum(cap[idx], 1), cap[idx].astype(int))
            ok = sw > 0
            sd, sw = slots[ok], sw[ok]
            Tr = min(T, len(sd))
            keys = rng.random(len(sw)) ** (1.0 / sw)
            chosen = sd[np.argpartition(-keys, Tr - 1)[:Tr]] if Tr > 0 else np.array([], dtype=int)
            hits[np.unique(chosen)] += 1
            bg_draws.append(pd.DataFrame({"draw": r, "bg": du["bg"].values[chosen]}))
    bgd = pd.concat(bg_draws).groupby(["draw", "bg"]).size().rename("evs").reset_index()
    return E, Eb, hits / R_DRAWS, bgd


def fleet_sites(tz: pd.DataFrame) -> pd.DataFrame:
    p = gpd.read_file(RAW / "parcels" / "tompkins_parcels_2025.gpkg")
    pc = p["PROP_CLASS"].astype(str).str[:3]
    nonres = pc.str[0].isin(["4", "5", "6", "7", "8"]) & ~pc.isin(["411", "416", "418"])
    q = p[nonres].copy()
    q["gfa"] = pd.to_numeric(q["GFA"], errors="coerce").fillna(0)
    pts = q.to_crs(32618).geometry.representative_point().to_crs(4326)
    g = gpd.GeoDataFrame(q[["SWIS_SBL_ID", "PROP_CLASS", "gfa"]], geometry=pts.values, crs=4326)
    z = gpd.read_file(PROCESSED / "geography" / "tompkins_area_zcta.gpkg")[["ZCTA5CE20", "geometry"]].rename(columns={"ZCTA5CE20": "zcta"})
    g = gpd.sjoin(g, z, how="inner", predicate="within")
    rows = []
    for zc, gg in g.groupby("zcta"):
        n = float(tz["fleet_EV"].get(zc, 0))
        if n <= 0 or gg["gfa"].sum() <= 0:
            continue
        rows.append(gg.assign(E_fleet_ev=n * gg["gfa"] / gg["gfa"].sum())[["SWIS_SBL_ID", "PROP_CLASS", "zcta", "gfa", "E_fleet_ev"]])
    return pd.concat(rows) if rows else pd.DataFrame()


def evolve(du: pd.DataFrame, E26: np.ndarray, wlist: list[np.ndarray], rho: float, scen: pd.DataFrame, tz: pd.DataFrame) -> dict:
    cap = du["veh"].values.astype(float)
    hh_z = du.groupby("zcta").size()
    ev26_county = float(scen.loc[scen["year"] == 2026, "EV_p50"].iloc[0])
    pi26 = pd.Series(E26).groupby(du["zcta"].values).sum()
    pi26 = pi26 / pi26.sum()
    h = hh_z / hh_z.sum()
    out = {}
    for y in YEARS_OUT:
        ev_y = float(scen.loc[scen["year"] == y, "EV_p50"].iloc[0])
        q = max(ev_y / ev26_county, 1.0)
        phi = PHI_PER_DOUBLING ** np.log2(q)
        T = ev_y * rho * float(tz.loc[tz.index.isin(set(du["zcta"])), "EV"].sum() / tz["EV"].sum())
        share = (pi26.clip(lower=1e-12) ** phi) * (h.reindex(pi26.index).fillna(0) ** (1 - phi))
        share = share / share.sum()
        Ey = np.zeros(len(du))
        for w in wlist:
            wy = np.where(w > 0, w ** phi, 0.0)
            for z, sz in share.items():
                idx = np.where(du["zcta"].values == z)[0]
                Ey[idx] += capped_allocation(T * sz, wy[idx], cap[idx]) / len(wlist)
        out[y] = {"E": Ey, "phi": phi, "T": T}
    return out


def main() -> None:
    ensure(PROCESSED / "model", TABLES, FIGURES, MAPS)
    rng = np.random.default_rng(SEED)
    params = json.load(open(PROCESSED / "model" / "propensity_params.json"))
    du = load_units()
    tz, rho = observed_zip_totals()
    w = weights(du, params, "model")
    w_ind = weights(du, params, "individual")
    E, Eb, p_any, bgd = allocate_status_quo(du, tz, [w, w_ind], rng)
    du["w"] = w
    du["w_individual"] = w_ind
    du["E_ev"], du["E_bev"], du["E_phev"], du["p_any_ev"] = E, Eb, E - Eb, p_any
    for mode in ["model", "uniform", "vehicles", "individual", "prior"]:
        wm = weights(du, params, mode)
        Em = np.zeros(len(du))
        for z, row in tz.iterrows():
            idx = np.where(du["zcta"].values == z)[0]
            if len(idx) and row["EV"] > 0:
                Em[idx] = capped_allocation(row["EV"], wm[idx], du["veh"].values[idx].astype(float))
        du[f"E_ev_{mode}"] = Em
    cols = ["du_id", "parcel", "bg", "zcta", "structure", "tenure", "income_band", "veh", "w", "w_individual", "E_ev", "E_bev", "E_phev", "p_any_ev",
            "E_ev_model", "E_ev_uniform", "E_ev_vehicles", "E_ev_individual", "E_ev_prior"]
    du[cols].to_parquet(PROCESSED / "model" / "du_ev_2026.parquet", index=False)

    # tables: structure shares, BG uncertainty
    struct = du.groupby("structure")[["E_ev", "E_ev_model", "E_ev_uniform", "E_ev_vehicles", "E_ev_individual", "E_ev_prior"]].sum()
    struct = (struct / struct.sum()).round(4)
    struct["households_share"] = (du.groupby("structure").size() / len(du)).round(4)
    struct.to_csv(TABLES / "allocation_structure_shares_2026.csv")
    ten = du.groupby("tenure")[["E_ev", "E_ev_model", "E_ev_uniform", "E_ev_vehicles", "E_ev_individual", "E_ev_prior"]].sum()
    (ten / ten.sum()).round(4).to_csv(TABLES / "allocation_tenure_shares_2026.csv")
    inc = du.groupby("income_band")[["E_ev", "E_ev_model", "E_ev_uniform", "E_ev_vehicles", "E_ev_individual", "E_ev_prior"]].sum()
    (inc / inc.sum()).round(4).to_csv(TABLES / "allocation_income_shares_2026.csv")
    bg = du.groupby("bg").agg(households=("du_id", "size"), E_ev=("E_ev", "sum"), E_uniform=("E_ev_uniform", "sum"),
                              E_model=("E_ev_model", "sum"), E_vehicles=("E_ev_vehicles", "sum"), E_individual=("E_ev_individual", "sum"), E_prior=("E_ev_prior", "sum"))
    q = bgd.groupby("bg")["evs"].quantile([0.05, 0.95]).unstack().rename(columns={0.05: "draw_p05", 0.95: "draw_p95"})
    bg = bg.join(q).fillna(0)
    bg["structural_min"] = bg[["E_model", "E_uniform", "E_vehicles", "E_individual", "E_prior"]].min(axis=1)
    bg["structural_max"] = bg[["E_model", "E_uniform", "E_vehicles", "E_individual", "E_prior"]].max(axis=1)
    bg["ev_per_hh"] = bg["E_ev"] / bg["households"]
    bg.round(3).to_csv(TABLES / "allocation_bg_2026_uncertainty.csv")

    fleet = fleet_sites(tz)
    fleet.round(3).to_csv(PROCESSED / "model" / "fleet_ev_sites_2026.csv", index=False)

    # evolution
    gp = pd.read_csv(PROCESSED / "growth" / "growth_parameters_by_year.csv")
    evo_rows, wide = [], {"du_id": du["du_id"].values}
    for sc in ["trend", "slow", "stall", "policy"]:
        res = evolve(du, E, [w, w_ind], rho, gp[gp["scenario"] == sc], tz)
        for y, r in res.items():
            e = pd.Series(r["E"])
            by_s = e.groupby(du["structure"].values).sum()
            evo_rows.append({"scenario": sc, "year": y, "phi": r["phi"], "personal_evs": r["T"],
                             **{f"share_{k}": v / e.sum() for k, v in by_s.items()},
                             "share_renter": float(e[du["tenure"].values == "rent"].sum() / e.sum()),
                             "share_income_lt50k": float(e[du["income_band"].values == "<50k"].sum() / e.sum()),
                             "hh_with_ev_share_expected": float(np.minimum(r["E"], 1).sum() / len(du))})
            if sc == "trend":
                wide[f"E_ev_{y}"] = r["E"].astype("float32")
    evo = pd.DataFrame(evo_rows)
    evo.round(4).to_csv(TABLES / "allocation_evolution_by_scenario.csv", index=False)
    pd.DataFrame(wide).to_parquet(PROCESSED / "model" / "du_ev_by_year_trend.parquet", index=False)

    # figures
    g = gpd.read_file(PROCESSED / "geography" / "tompkins_bg.gpkg").rename(columns={"GEOID": "bg"}).merge(bg.reset_index(), on="bg").to_crs(32618)
    g["cv_draws"] = (g["draw_p95"] - g["draw_p05"]) / (2 * 1.645 * g["E_ev"].clip(lower=1e-6))
    g["struct_ratio"] = g["structural_max"] / g["structural_min"].clip(lower=0.5)
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    g.plot(column="ev_per_hh", ax=axes[0], legend=True, cmap="viridis", edgecolor="w", linewidth=0.2)
    axes[0].set_title("2026 expected personal EVs per household (central ensemble)")
    g.plot(column="cv_draws", ax=axes[1], legend=True, cmap="magma_r", vmin=0, vmax=0.5, edgecolor="w", linewidth=0.2)
    axes[1].set_title("Sampling uncertainty: (p95-p05)/(3.29·mean)")
    g.plot(column="struct_ratio", ax=axes[2], legend=True, cmap="magma_r", vmin=1, vmax=3, edgecolor="w", linewidth=0.2)
    axes[2].set_title("Structural spread: max/min across 5 weightings")
    for a_ in axes:
        a_.set_axis_off()
    fig.suptitle("Tompkins 2026 EV allocation to dwelling units, aggregated to block groups (inferred; EPSG:32618)")
    fig.tight_layout(); fig.savefig(MAPS / "allocation_bg_2026.png", dpi=130); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    for sc, col in zip(["trend", "slow", "stall", "policy"], ["tab:blue", "tab:orange", "tab:grey", "tab:green"]):
        e = evo[evo["scenario"] == sc]
        ax[0].plot(e["year"], e["share_MF5_19"].fillna(0) + e["share_MF20P"].fillna(0) + e["share_MF2_4"].fillna(0), marker="o", color=col, label=f"{sc}: multifamily")
        ax[1].plot(e["year"], e["hh_with_ev_share_expected"], marker="o", color=col, label=sc)
    ax[0].axhline(struct.loc[["MF2_4", "MF5_19", "MF20P"], "households_share"].sum(), color="k", ls=":", label="multifamily share of households")
    ax[0].set_title("Share of personal EVs in multifamily dwellings"); ax[0].legend(fontsize=7)
    ax[1].set_title("Share of households with ≥1 EV (expected, capped)"); ax[1].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(FIGURES / "allocation_evolution.png", dpi=140); plt.close(fig)
    print(struct.to_string()); print(ten.div(ten.sum()).round(3).to_string())
    print(evo.round(3).to_string())
    print("rho_personal", round(rho, 4), "fleet EV placed", round(fleet["E_fleet_ev"].sum(), 1) if len(fleet) else 0)


if __name__ == "__main__":
    main()
