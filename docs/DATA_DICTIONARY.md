# Data Dictionary

`data/zone_modeling_table_FINAL.csv` — 517 rows (one per CONUS zone), 18 columns, no missing values.

| Column | Description | Source | Range |
|---|---|---|---|
| `CBSAFP2` | Zone identifier. Numeric = CBSA-based metro zone; RXXn = FHWA non-metro zone | FHWA | — |
| `zone_name` | Zone name | FHWA | — |
| `is_nonmsa` | 1 = non-metropolitan zone, 0 = metropolitan | derived | 0.000 – 1.000 |
| `n_bg` | Block groups aggregated into this zone | derived | 9.000 – 14900.000 |
| `SUM_TotPop` | Total population, 2018 | ACS/SLD | 15239.000 – 19990592.000 |
| `D1B_weighted` | Gross population density, people per acre of unprotected land (pop-weighted) | SLD v3.0 | 0.156 – 58.772 |
| `D1D_weighted` |  |  | 0.112 – 42.660 |
| `D2A_weighted` | Employment & household entropy, land-use mix, 0-1 (pop-weighted) | SLD v3.0 | 0.342 – 0.685 |
| `D3B_weighted` | Street intersection density per sq mi, pedestrian-oriented (pop-weighted) | SLD v3.0 | 3.157 – 149.111 |
| `pct_near_transit` | Share of population within 1207m (3/4 mi) of a transit stop, % | derived from SLD D4A | 0.000 – 87.081 |
| `D5AR_weighted` | Jobs reachable within 45 min by car, time-decay weighted (pop-weighted) | SLD v3.0 | 755.040 – 444826.663 |
| `pct_white` | Share of residents identifying as white, % | ACS | 3.531 – 96.436 |
| `pct_male` | Share of residents male, % | ACS | 46.952 – 65.209 |
| `avg_hh_size` | Average household size (residents/households) | ACS | 2.224 – 4.031 |
| `Veh_Within` | Intrazonal vehicle trips, 0-10 mi, annual | NHTS OD 2022 | 6123230.000 – 17434128292.000 |
| `ATF_Within` | Intrazonal active-transport+ferry trips, 0-10 mi, annual | NHTS OD 2022 | 888996.000 – 5646135449.000 |
| `atf_share_within` | OUTCOME. ATF_Within/(ATF_Within+Veh_Within) | derived | 0.071 – 0.245 |
| `atf_share_total` | Robustness variant using all trip types (r=0.997 with primary) | derived | 0.070 – 0.244 |

---

## Notes

**Population weighting.** All `*_weighted` variables were aggregated from Census block groups
to zones as `Σ(population × variable) / Σ(population)`, so each zone's value represents the
built environment of its average resident rather than its average acre.

**`pct_near_transit` replaces raw `D4A`.** SLD codes distance-to-transit as −99999 beyond
1207 m, censoring 56.8% of block groups and leaving 48% of zones invariant. See
[METHODOLOGY.md §4.2](METHODOLOGY.md).

**`D1D` (activity density) excluded.** r = 0.94 with `D1B`, VIF 13.2. See
[METHODOLOGY.md §4.1](METHODOLOGY.md).

**Zone codes.** Metropolitan zones use numeric CBSA-based codes (e.g. `19100` =
Dallas-Fort Worth-Arlington). Non-metropolitan zones use FHWA string codes (e.g. `RAL1` =
Alabama non-metro NW, `RTX9` = Texas non-metro).
