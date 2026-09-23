# Methodology

Complete record of how the dataset was built and the analysis run, including every
consequential decision and why it was made.

---

## 1. Research design

**Question.** Which built-environment characteristics predict the share of short trips
(0–10 miles) made by active modes across U.S. zones, and are those relationships non-linear?

**Unit of analysis.** FHWA's 583-zone national geography (447 CBSA-based + 136 non-metro),
restricted to the contiguous U.S. → **517 zones**.

**Design.** Cross-sectional, observational. Associations only; no causal identification.

---

## 2. Data sources

### 2.1 Trip data — FHWA NextGen NHTS Passenger OD (2022)

Aggregated trip counts between zones by mode, purpose and distance band, derived from
passively collected mobile device data and calibrated to NHTS.

Mode categories: **air, rail, vehicle, Active Transportation & Ferries (ATF)**.

> **Critical limitation.** ATF bundles walking, cycling, e-biking, e-scootering and ferries.
> E-bike/e-scooter trips cannot be isolated in this product. Findings describe active-mode
> share generally, not micromobility substitution.

Trips are split three ways per zone: **Entering**, **Leaving**, **Within** (intrazonal).

### 2.2 Built environment — EPA Smart Location Database v3.0

Block-group level, 216,330 block groups nationally. Variables selected one per "D" dimension
of the standard density / diversity / design / destination-accessibility / distance-to-transit
framework, to keep the feature set theoretically grounded and interpretable at n = 517.

### 2.3 Demographics — American Community Survey

Block-group estimates, 2018 vintage, matching SLD v3.0's vintage.

### 2.4 Geography crosswalk — FHWA Revised County–Zone file

One row per county (3,142), mapping `COUNTY_FIP` + `STATEFP` → `CBSAFP2` zone code.
Non-metro zones carry string codes (`RAL1`, `RTX9`, …) rather than numeric CBSA codes.

---

## 3. Outcome variable

```
atf_share_within = ATF_Within / (ATF_Within + Veh_Within)
```

**Why intrazonal only.** Within-zone trips begin and end inside the same zone, so that
zone's BE characteristics can plausibly explain the mode choice. Interzonal trips have
origins and destinations in different zones and would require separate origin/destination
feature sets — a known complication in this literature. A robustness variant using all trip
types (`atf_share_total`) correlates with the primary measure at **r = 0.997**, so the choice
does not materially affect results.

**Distribution.** Mean 12.6%, range 7.1%–24.5%, no degenerate 0/1 values. Annual aggregates
run to millions of trips even in the smallest zone, so small-sample noise is not a concern
and no minimum-volume filter was applied.

---

## 4. Predictors

| Variable | Definition | Unit |
|---|---|---|
| `D1B_weighted` | Gross population density, per acre of unprotected land | people/acre |
| `D2A_weighted` | Employment & household entropy (land-use mix) | 0–1 index |
| `D3B_weighted` | Street intersection density, pedestrian-oriented, weighted | per sq mi |
| `pct_near_transit` | Share of population within 1207 m of a transit stop | % |
| `D5AR_weighted` | Jobs reachable within 45 min by car, time-decay weighted | weighted count |

Controls: `pct_white`, `pct_male`, `avg_hh_size`, `is_nonmsa`.

### 4.1 Why `D1D` (activity density) was dropped

`D1B` and `D1D` correlated at **r = 0.94**, VIF 13.2 and 11.3 — well above the conventional
threshold of 10. Retaining `D1B` alone:

| Kept | OLS R² | GBM CV R² | max VIF |
|---|---|---|---|
| `D1B` | **0.346** | **0.377** | **4.82** |
| `D1D` | 0.322 | 0.328 | 4.12 |

`D1B` wins on both criteria; `D1D` excluded.

### 4.2 Why transit access was reformulated

SLD codes `D4A` (distance to nearest transit stop) as **−99999** for any block group beyond
3/4 mile (1207 m). This is a measurement cap, not missing data — EPA simply stops measuring
past that distance.

Scale of the problem:
- **56.8% of block groups** (122,839) sit at the cap, covering 188M of 321M residents
- **248 of 517 zones (48%)** are *fully* censored — every block group at the cap, so
  `D4A_weighted` = 1207.00 identically

A variable with no variance across half the sample cannot inform a model about those zones,
and would produce a flat artefactual region in SHAP dependence plots that could be
misread as a genuine threshold.

Three candidates tested (5-fold CV, GBM, all other features held constant):

| Formulation | CV R² | Issue |
|---|---|---|
| `D4A_weighted` (censored mean distance) | 0.350 | 48% of zones invariant |
| **`pct_near_transit`** | **0.362** | — |
| Mean distance among uncensored only | — | null for 248 zones (r = −0.11) |
| Both distance + share together | 0.361 | collinear (r = −0.987), no gain |

`pct_near_transit` adopted: higher predictive value, a true zero rather than a ceiling
artefact, natural 0–100 scale, and policy-legible ("transit coverage of population").

---

## 5. Spatial aggregation (ArcGIS Pro)

Block groups → zones, by population weighting.

### 5.1 Why population weighting

A plain mean would let a 50-person rural block group count as much as a 4,000-person urban
one. Population weighting makes each zone's value represent **the built environment of the
average resident**, which is what should predict the travel behaviour in the outcome.

```
zone_value = Σ(population_i × variable_i) / Σ(population_i)
```

Implemented in three tool steps, since ArcGIS Summary Statistics has no weighted-mean option:
1. **Calculate Field** — `popD1B = TotPop * D1B` (Double type; Long Integer overflows on
   `popD5AR`, whose products exceed 10¹⁰)
2. **Summary Statistics** — Case Field `CBSAFP2`, Sum on `TotPop` and each `pop*` field
3. **Calculate Field** — `D1B_weighted = SUM_popD1B / SUM_TotPop`

### 5.2 Why the county crosswalk, not a CBSA join

The first attempt joined block groups' native Census `CBSA` field to the zone table's
`CBSAFP2`. This failed for **39,341 block groups (18%)** across 540 CBSAs:

- Block groups outside any CBSA (rural) have no code to match
- Micropolitan areas have real CBSA codes but were folded into FHWA's non-metro zones,
  so their codes do not appear in the zone table

Grouping on that field returns **919 groups** (the full Census CBSA + micropolitan universe)
rather than 517. Aggregating there would have silently dropped or merged every non-metro zone.

The FHWA county crosswalk resolves this because **every** block group has a county, metro or
not. Final join:

```
CountyFIPS = GEOID20[:5]   →   crosswalk COUNTY_FIP   →   CBSAFP2
```

Result: **216,330 of 216,330 block groups matched, 0 invalid county codes, all 517 zones present.**

### 5.3 GEOID corruption

An intermediate export wrote `GEOID20` in scientific notation for **82% of rows**
(`4.8113E+11`). Since scientific notation *rounds*, county codes shifted — e.g. Ulster
County NY `361119801001` → `36112`, which is not a valid county.

Detected by validating derived county codes against the crosswalk: 23,678 rows resolved to
non-existent counties. Undetectable cases (rounding into a *different but valid* county) made
the file unusable rather than repairable. A cross-validation against the original `CBSA`
field could not separate corruption from legitimate FHWA-vs-Census differences.

Resolved by re-exporting with `GEOID20` explicitly typed as Text via **Conversion Tools →
Export Table**, and never opening the CSV in Excel (which re-converts long digit strings).

**Lesson for replication:** always verify ID fields survive export before building on them.

---

## 6. Modelling

### 6.1 Linear baseline

OLS, all nine features. In-sample R² = 0.346, adj R² = 0.334, F = 29.7 (p ≈ 1×10⁻⁴¹).

Diagnostics: Breusch–Pagan p = 0.074 (no strong heteroskedasticity); Jarque–Bera p < 0.001
(non-normal residuals — expected for a bounded proportion outcome).

### 6.2 Spatial dependence check

ANOVA of OLS residuals grouped by state (47 states with n ≥ 3):

```
F = 18.11,  p = 4.6e-77,  between-state share of residual variance = 63.4%
```

Zones in the same state behave alike in ways the BE variables do not capture. Two
consequences: OLS standard errors are understated, and **random k-fold CV is invalid** —
a training zone leaks information about its in-state test neighbour.

### 6.3 Cross-validation strategy

All headline numbers use `GroupKFold(n_splits=5)` with `groups=state`, holding out entire
states. Random `KFold` results are reported **only** to quantify the leakage.

### 6.4 XGBoost configuration

`n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8`

**Tuning was deliberately minimal.** With 517 observations, extensive hyperparameter search
risks overfitting the validation set itself. Three simpler/regularised variants were tested
to confirm the null is not a tuning artefact:

| Variant | Grouped CV R² |
|---|---|
| depth 2 | 0.148 |
| depth 2 + L2 (λ=5, min_child_weight=10) | 0.144 |
| decision stumps (depth 1) | 0.136 |

None beat OLS (0.152).

### 6.5 SHAP

Computed on a full-sample fit via `TreeExplainer`. **Used descriptively** — to characterise
the shape of fitted relationships — not as evidence of validated thresholds, since the model
does not generalize across states.

---

## 7. Decision log

| Decision | Choice | Rationale |
|---|---|---|
| Trip type | Intrazonal only | Both ends in-zone; clean BE attribution. r = 0.997 with all-trips variant |
| Non-metro zones | Retained | Anchors low end of BE range, needed to detect thresholds; widened density floor from 1.05 to 0.16 |
| Geographic scope | CONUS | AK/HI excluded — 0 block groups from FIPS 02/15 in final data |
| Density measure | `D1B` only | r = 0.94 with `D1D`; better on both OLS and GBM |
| Transit measure | `pct_near_transit` | 48% of zones invariant under censored `D4A` |
| Aggregation | Population-weighted | Represents average resident, not average land area |
| Zone assignment | FHWA county crosswalk | CBSA join fails for all non-metro zones |
| Cross-validation | State-grouped | 63.4% between-state residual variance |
| Hyperparameter tuning | Minimal | n = 517; avoid overfitting the validation set |

---

## 8. Limitations

1. **Aggregation.** Zones are metropolitan-scale — the New York zone averages Manhattan with
   Westchester. This is the most plausible explanation for the null result.
2. **Mode bundling.** ATF cannot isolate e-bike/e-scooter trips.
3. **No causal identification.** Residential self-selection is unaddressed.
4. **Temporal mismatch.** Trips 2022; SLD and ACS 2018.
5. **State as spatial proxy.** State grouping approximates spatial structure; a distance-based
   weights matrix (Moran's I, spatial lag/error) would be more rigorous.
6. **`is_nonmsa` uninformative.** Mean |SHAP| 0.0001 — the intended metro/non-metro
   comparison did not materialise.
