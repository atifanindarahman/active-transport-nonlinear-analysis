"""
04_modeling_full.py — Phases 3–5
Non-linear built-environment effects on active-transport share, 517 CONUS zones.

Run top to bottom, or paste cell-by-cell into Jupyter.
Input:  zone_modeling_table_FINAL.csv
Output: cv_results, SHAP values, figures/

KEY METHODOLOGICAL NOTE
-----------------------
Residuals from the OLS baseline are strongly spatially clustered: 63.4% of
residual variance lies BETWEEN states (F=18.1, p~1e-77). Random k-fold CV is
therefore optimistic — a zone in the training set leaks information about its
in-state neighbour in the test set. All headline numbers below use
GroupKFold holding out entire states.
"""

import pandas as pd, numpy as np, re, warnings
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold, KFold, cross_val_score
from xgboost import XGBRegressor
import shap
warnings.filterwarnings("ignore")

# ----------------------------------------------------------------------
# 1. LOAD
# ----------------------------------------------------------------------
d = pd.read_csv("zone_modeling_table_FINAL.csv", dtype={"CBSAFP2": str})

# D1D_weighted (activity density) is EXCLUDED: r=0.94 with D1B_weighted,
# VIF 13.2 vs 11.3. Keeping D1B alone gave higher OLS R2 (0.346 vs 0.322)
# and higher GBM CV R2 (0.377 vs 0.328); max VIF fell to 4.82.
PRED = ["D1B_weighted", "D2A_weighted", "D3B_weighted",
        "pct_near_transit", "D5AR_weighted"]
CTRL = ["pct_white", "pct_male", "avg_hh_size", "is_nonmsa"]
FEAT = PRED + CTRL

# State label for spatial grouping: last 2-letter token in zone_name
# (handles multi-state names, e.g. "Allentown-Bethlehem-Easton, PA-NJ" -> NJ)
d["state"] = d["zone_name"].apply(
    lambda n: (re.findall(r"\b([A-Z]{2})\b", str(n)) or ["XX"])[-1])

X, y, groups = d[FEAT], d["atf_share_within"], d["state"]
print(f"N={len(d)}  features={len(FEAT)}  states={groups.nunique()}")

# ----------------------------------------------------------------------
# 2. PHASE 3 — OLS BASELINE + DIAGNOSTICS
# ----------------------------------------------------------------------
Xc = sm.add_constant(X)
ols = sm.OLS(y, Xc).fit()
print(f"\nOLS in-sample R2={ols.rsquared:.4f}  adjR2={ols.rsquared_adj:.4f}")
print(ols.summary2().tables[1][["Coef.", "Std.Err.", "t", "P>|t|"]].round(6))

print("\nVIF:")
for i, c in enumerate(Xc.columns):
    if c != "const":
        print(f"  {c:18s}{variance_inflation_factor(Xc.values, i):6.2f}")

# Spatial autocorrelation check (state-level ANOVA on residuals)
from scipy import stats
d["resid"] = ols.resid
gs = [g["resid"].values for _, g in d.groupby("state") if len(g) >= 3]
F, p = stats.f_oneway(*gs)
ss_b = sum(len(g) * (g.mean() - d["resid"].mean())**2 for g in gs)
ss_t = ((d["resid"] - d["resid"].mean())**2).sum()
print(f"\nResidual clustering by state: F={F:.2f} p={p:.2e} "
      f"between-state share={ss_b/ss_t*100:.1f}%")

# ----------------------------------------------------------------------
# 3. PHASE 4 — MODEL COMPARISON (random vs state-grouped CV)
# ----------------------------------------------------------------------
gkf, rkf = GroupKFold(n_splits=5), KFold(5, shuffle=True, random_state=42)
mk_xgb = lambda **kw: XGBRegressor(
    n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8,
    colsample_bytree=0.8, random_state=42, verbosity=0, **kw)

res = {
    "OLS_random":  cross_val_score(LinearRegression(), X, y, cv=rkf, scoring="r2"),
    "XGB_random":  cross_val_score(mk_xgb(), X, y, cv=rkf, scoring="r2"),
    "OLS_grouped": cross_val_score(LinearRegression(), X, y, cv=gkf, groups=groups, scoring="r2"),
    "XGB_grouped": cross_val_score(mk_xgb(), X, y, cv=gkf, groups=groups, scoring="r2"),
}
print("\n--- CV comparison ---")
for k, v in res.items():
    print(f"  {k:12s} R2={v.mean():+.4f} (±{v.std():.3f})  folds={np.round(v,3)}")
print(f"  spatial leakage (XGB random - grouped) = "
      f"{res['XGB_random'].mean()-res['XGB_grouped'].mean():+.4f}")

# Ceiling check: how much variance is purely state-level?
sm_ = d.groupby("state")["atf_share_within"].mean()
d["state_mean"] = d["state"].map(sm_)
r2_state = 1 - ((y - d["state_mean"])**2).sum() / ((y - y.mean())**2).sum()
print(f"  R2 from state mean alone = {r2_state:.4f}")

# ----------------------------------------------------------------------
# 4. PHASE 5 — SHAP (descriptive, full-sample fit)
# ----------------------------------------------------------------------
# NOTE: fitted on all data for interpretation, NOT for performance claims.
model = mk_xgb().fit(X, y)
sv = shap.TreeExplainer(model).shap_values(X)

imp = (pd.DataFrame({"feature": X.columns, "mean_abs_shap": np.abs(sv).mean(0)})
       .sort_values("mean_abs_shap", ascending=False))
print("\nSHAP importance:\n", imp.to_string(index=False))

import os; os.makedirs("figures", exist_ok=True)
shap.summary_plot(sv, X, show=False); plt.tight_layout()
plt.savefig("figures/shap_summary.png", dpi=200); plt.close()
for f in PRED:
    shap.dependence_plot(f, sv, X, show=False, interaction_index=None)
    plt.tight_layout(); plt.savefig(f"figures/shap_dep_{f}.png", dpi=200); plt.close()

print("\nSHAP by quintile of each predictor (shape of the relationship):")
for f in PRED:
    q = pd.qcut(X[f], 5, labels=False, duplicates="drop")
    s = pd.Series(sv[:, list(X.columns).index(f)]).groupby(q).mean()
    print(f"  {f:18s} " + " -> ".join(f"{v:+.4f}" for v in s.values))

d.to_csv("zone_table_with_resid.csv", index=False)
np.save("shap_values.npy", sv)
print("\nDone. Figures in figures/, SHAP values saved.")
