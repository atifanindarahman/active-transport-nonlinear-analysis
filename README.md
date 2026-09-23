# Do Built-Environment Effects on Active Travel Hold at National Scale?

**A non-linear analysis of short-trip mode share across 517 U.S. zones**

Atif Aninda Rahman · [Portfolio](https://atifanindarahman.github.io)

---

## Headline finding

Non-linear machine learning offers **no generalizable improvement** over ordinary least
squares for predicting active-mode share of short trips at national zone scale — once
spatial dependence is handled honestly.

| Model | Validation | R² |
|---|---|---|
| OLS | random 5-fold | 0.276 |
| XGBoost | random 5-fold | **0.399** |
| OLS | state-grouped | **0.152** |
| XGBoost | state-grouped | 0.130 |

![CV comparison](figures/fig5_cv_comparison.png)

Under conventional random cross-validation XGBoost appears to beat OLS decisively. Under
state-grouped cross-validation — which prevents a zone leaking information about its
in-state neighbour — the advantage vanishes and slightly reverses. **Spatial leakage
(+0.269) is larger than the entire apparent non-linear gain.**

The reason: **78.7% of variance in active-mode share is explained by state alone.** At this
resolution, regional context dominates the measurable built environment.

---

## Why this matters

A growing literature uses gradient boosting and SHAP to argue that built-environment effects
on travel behaviour are non-linear, with thresholds and saturation points. That work is
almost entirely single-city, survey-based, and validated with random cross-validation on
spatially autocorrelated data.

This study tests whether the finding replicates at national scale with passively collected
trip data and spatially honest validation. It does not. The result bounds the non-linear
literature rather than refuting it: those effects appear to operate at neighbourhood scale
and may not survive aggregation to metropolitan units.

---

## Repository contents

```
data/     zone_modeling_table_FINAL.csv   517 zones, analysis-ready
figures/  fig1–fig10                      all figures, reproducible
notebooks/04_modeling_full.py             full Phase 3–5 pipeline
docs/     METHODOLOGY.md                  complete method, decision log
          FINDINGS.md                     results and interpretation
          DATA_DICTIONARY.md              every variable defined
          FAQ.md                          anticipated questions + answers
```

Start with [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for how the data was built, or
[`docs/FINDINGS.md`](docs/FINDINGS.md) for results.

---

## Data

| Source | Role |
|---|---|
| FHWA NextGen NHTS Passenger OD (2022) | Trip counts by mode and distance band, 583-zone national geography |
| EPA Smart Location Database v3.0 | Built-environment measures, 216,330 block groups |
| American Community Survey | Sociodemographic controls |
| FHWA Revised County–Zone crosswalk | County → zone assignment (metro and non-metro) |

**Final dataset:** 517 CONUS zones (382 metropolitan, 135 non-metropolitan), 48 states + DC,
320.7 million residents, zero missing values.

### Framing caveat

The NHTS OD product bundles walking, cycling, e-biking, e-scootering and ferry trips into a
single *Active Transportation & Ferries* category. **E-bike and e-scooter trips cannot be
isolated.** This study measures observed active-mode share and which BE characteristics
predict it — not e-bike substitution specifically.

---

## Method summary

**Outcome:** active-mode share of intrazonal short (0–10 mi) trips,
`ATF_within / (ATF_within + Vehicle_within)`.

**Predictors:** five BE measures, one per "D" dimension, aggregated from block groups to
zones by population weighting.

**Models:** OLS baseline vs XGBoost, with SHAP for interpretation. All headline numbers use
`GroupKFold` holding out entire states.

Full detail in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

---

## Data-quality issues identified and resolved

Three problems that would have silently corrupted results:

1. **Right-censored transit variable.** SLD codes `D4A` as −99999 beyond 3/4 mile from
   transit — affecting 56.8% of block groups and leaving **48% of zones completely invariant**.
   Reformulated as share of population within 1207 m.
2. **Corrupted geographic identifiers.** 82% of `GEOID20` values exported in scientific
   notation, silently shifting county FIPS codes. Detected by validation against the
   crosswalk; fixed by re-export as text.
3. **Collinear density measures.** `D1B` and `D1D` correlated r = 0.94 (VIF 13.2 / 11.3).
   Retained `D1B`; max VIF fell to 4.82.

---

## Reproducing

```bash
pip install -r requirements.txt
python notebooks/04_modeling_full.py
```

Runs in under two minutes on `data/zone_modeling_table_FINAL.csv`.
Upstream GIS processing (block-group aggregation) was done in ArcGIS Pro — steps documented
in [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

---

## Next steps

1. **Finer resolution.** Replicate at tract or block-group level within selected metros —
   the direct test of whether the null result is an aggregation artefact.
2. **Spatial models.** Given 63.4% between-state residual variance, spatial lag/error models
   or GWR are more appropriate than either OLS or tree-based methods at this scale.
3. **Regional mechanisms.** Identify what the state effect represents — climate, DOT
   investment, development era — and measure it directly.

---

## Note on tooling

Analysis code was developed with AI assistance. All research design, data acquisition, GIS
processing, methodological decisions and interpretation are the author's.
