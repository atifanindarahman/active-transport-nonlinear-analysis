# Anticipated Questions

Questions a reviewer, advisor or interviewer is likely to ask, with defensible answers.
Read this before discussing the project.

---

## On the research design

**Q: Why not just use linear regression from the start?**
The point was to *test* whether non-linearity matters, not assume it. A growing literature
claims it does. Testing that claim and reporting a null is a result, not a failure — and the
comparison itself (random vs spatial CV) turned out to be the more interesting finding.

**Q: Isn't a null result just a failed project?**
No. The null is accompanied by a mechanism (78.7% state-level variance, aggregation
destroying within-zone variation) and a methodological finding (+0.269 spatial leakage) that
has implications for how the existing literature is validated. A null with an explanation is
more useful than a weak positive nobody can replicate.

**Q: Why intrazonal trips only?**
Within-zone trips begin and end in the same zone, so that zone's BE characteristics can
plausibly explain the mode choice. Interzonal trips would require separate origin and
destination feature sets. The all-trips variant correlates at r = 0.997, so the choice does
not drive results.

**Q: Why these five BE variables and not more?**
One per "D" dimension of the standard framework, chosen a priori for theoretical grounding
and interpretability at n = 517. Adding 20 correlated SLD columns would inflate variance
and make SHAP unreadable. `D1D` was dropped for collinearity (r = 0.94 with `D1B`).

---

## On the data

**Q: Can you actually measure e-bike substitution with this?**
No, and the write-up says so explicitly. NHTS OD bundles walking, cycling, e-biking,
e-scootering and ferries into one category. This measures active-mode share generally.
Claiming e-bike specificity would misrepresent the data.

**Q: Ferries are in the active category — doesn't that contaminate results?**
Ferries are negligible in nearly all inland zones. It is a real limitation, disclosed, but
not a meaningful source of error outside a handful of coastal zones.

**Q: Trip data is 2022 but SLD/ACS is 2018 — is that a problem?**
A four-year gap in built-environment measures is modest; density, street networks and
land-use mix change slowly. It is disclosed as a limitation. Population weighting uses the
2018 ACS field, matching the SLD vintage, so weights and weighted variables are consistent.

**Q: How do you know your aggregation is correct?**
Three checks: all 216,330 block groups matched to a zone with zero invalid county codes;
zone count came out at exactly 517, matching the zone table; `n_bg` and `SUM_TotPop` are
retained in the output so any zone can be audited. Total population sums to 320.7M, consistent
with CONUS.

**Q: Why population weighting rather than a simple mean?**
A plain mean lets a 50-person rural block group count as much as a 4,000-person urban one.
Population weighting makes each zone's value describe the built environment of the *average
resident* — the people actually generating the trips in the outcome variable.

---

## On the transit variable

**Q: Why did you change `D4A` instead of using it as published?**
It is right-censored at 1207 m. 56.8% of block groups sit at the cap, and 48% of zones are
*completely* invariant — every block group at the ceiling. A variable with no variance across
half the sample cannot inform the model about those zones, and produces a flat artefactual
region in SHAP plots that could be misread as a real threshold.

**Q: Isn't reformulating the variable a form of p-hacking?**
The decision was made on the censoring diagnostic before seeing final model results, and all
three candidate formulations are reported with their CV scores. The chosen measure also
happens to be more interpretable and policy-legible. The alternative — silently multiplying
−99999 by population — would have been the actual error.

---

## On the methods

**Q: Why state-grouped cross-validation rather than random k-fold?**
Because 63.4% of OLS residual variance falls between states (F = 18.1, p ≈ 1e-77). Under
random k-fold, a training zone leaks information about its in-state test neighbour, so the
score reflects recognising neighbours rather than learning generalizable structure. The
measured leakage is +0.269.

**Q: Grouping by state is crude — why not a proper spatial weights matrix?**
Agreed, and it is listed as a limitation. State is a practical proxy that captures the
dominant clustering. A distance-based weights matrix with Moran's I, and spatial lag/error
models, are the stated next step.

**Q: Did you tune XGBoost enough? Maybe better hyperparameters would win.**
Tuning was deliberately minimal to avoid overfitting the validation set at n = 517. Three
simpler and regularised variants were tested (depth 2, depth 2 + L2, stumps): all landed
between 0.136 and 0.148, none reaching OLS at 0.152. The pattern — simpler is consistently
better but still not competitive — indicates the flexible model is fitting state-specific
noise, not that it is undertuned.

**Q: Your SHAP plots come from a model that doesn't generalize. Why show them?**
They are labelled descriptive throughout — they characterise the shape of relationships the
model fitted, not validated causal thresholds. The transit-access threshold is explicitly
framed as a hypothesis for finer-resolution testing.

**Q: Residuals are non-normal (Jarque-Bera p < 0.001). Doesn't that invalidate OLS?**
Expected for a bounded proportion outcome. It affects the exactness of inference, not
coefficient consistency, and it is disclosed. A beta regression or logit-transformed outcome
would be a reasonable robustness check.

---

## On the findings

**Q: Why is intersection density non-significant? That contradicts the walkability literature.**
That is precisely the most informative result. It correlates +0.314 bivariately but collapses
to p = 0.96 once density and transit are controlled. The best explanation is aggregation:
averaging a gridded downtown with cul-de-sac suburbs produces a number describing neither.
It is the sharpest evidence that the null is a resolution artefact rather than a substantive
claim that connectivity does not matter.

**Q: Why is auto job accessibility negative?**
Holding density and transit constant, places where cars reach many destinations quickly have
less active travel. Car convenience suppresses active modes. It is positive bivariately and
negative in the multivariate model — a suppression effect, since auto accessibility is itself
correlated with density.

**Q: Metro and non-metro have almost identical active-mode share. Is that believable?**
It is surprising and flagged as such. The likely explanation is that non-metro zones contain
small towns with walkable intra-town trips, while metro zones dilute dense cores with
car-oriented suburbs. It is consistent with `is_nonmsa` being nearly useless as a predictor
(mean |SHAP| 0.0001). Testing this properly needs finer resolution.

**Q: If state explains 78.7%, why not just include state fixed effects?**
That would absorb the variance without explaining it, and with 47 states at n = 517 would
consume substantial degrees of freedom. The more useful direction is identifying *what* state
stands for — climate, DOT investment, development era — and measuring it directly. That is a
stated next step.

---

## On process and tooling

**Q: Did you write the analysis code yourself?**
The analysis code was developed with AI assistance, and the repository says so. Research
design, data acquisition, all GIS processing, methodological decisions and interpretation are
mine. I can explain and defend every choice documented in `METHODOLOGY.md`.

**Q: What was the hardest part?**
The data engineering, not the modelling. Three issues would have silently corrupted results:
the censored transit variable affecting 48% of zones, GEOID corruption shifting county codes
in 82% of rows, and the CBSA join that appeared to work but dropped every non-metro zone.
Each was caught by validating against an external reference rather than trusting the output.

**Q: What would you do differently?**
Start at finer spatial resolution. The zone-level design was determined by data availability
rather than by what the question needs, and that constraint is most likely what produced the
null.
