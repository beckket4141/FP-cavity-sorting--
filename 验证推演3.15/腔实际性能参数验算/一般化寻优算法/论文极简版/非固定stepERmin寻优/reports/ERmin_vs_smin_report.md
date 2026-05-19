# ERmin vs smin Nonuniform Study

## Scope
- Target directory only: the current ERmin study folder.
- Reused the same `oe_paper/simulation/scripts/fp_design/core.py` Airy-response and `ER_sum` definition.
- Candidate set is exactly the finite rational search used by the existing `smin` study; no continuous black-box scan was introduced.

## Objective Definition

For fixed finesse `F`, this study treats

`ERmin(F) = max_k min_i ER_sum_i(F; k)`

as a different optimization target from

`smin(k) = max_k s_min(k)`

and from the derived requirement `F_min = tau0 / s_min` with `tau0=3`.

## Baseline Reproduction
- Exact denominator bound reproduced: `q_limit=90`.
- `smin` optimal family reproduced: `6/29, 7/29, 8/29`.
- Geometry-favored `smin` choice reproduced: `7/29`.
- Baseline `7/29` check passed at `F=32.21`: `ER_min=3.441633 dB`, `ER_mean=6.245809 dB`.
- Baseline `7/29` check passed at `F=87`: `ER_min=11.525972 dB`, `ER_mean=14.445406 dB`.

## Main Results
- Fixed `F=32.21` worst-channel optimum moves to `10/37`: `ER_min=4.188 dB`, `ER_mean=7.259 dB`, `s_min=1/37`, `F_min=111.0`. Relative to `7/29`, worst-channel ER changes by `+0.75 dB`.
- Fixed `F=87` worst-channel optimum also moves to `10/37`: `ER_min=12.050 dB`, `ER_mean=15.508 dB`, `s_min=1/37`, `F_min=111.0`. Relative to `7/29`, worst-channel ER changes by `+0.52 dB`.
- The `F=87` optimum `10/37` is **not** a cheaper design: its own `F_min=111.0` is higher than `87`, so it represents a different trade-off rather than a contradiction of the current `smin` choice.
- If we keep the current `tau0=3` requirement ceiling `F_min<=87`, the best `ERmin(F=87)` candidate becomes `6/29`, not `7/29`. It improves worst-channel ER by `+0.47 dB` at the same `F_min=87.0`.

## smin-Optimal Family Comparison
| k_fraction | L_over_R | geometry_gap_to_0p5 | ER_min_dB_F32p21 | ER_min_dB_F87 | ERmin_rank_within_family_F32p21 | ERmin_rank_within_family_F87 |
| --- | --- | --- | --- | --- | --- | --- |
| 7/29 | 0.472931 | 0.027069 | 3.442 | 11.526 | 3 | 3 |
| 8/29 | 0.580891 | 0.080891 | 3.511 | 11.588 | 2 | 2 |
| 6/29 | 0.366236 | 0.133764 | 3.952 | 11.993 | 1 | 1 |

Inside the current `smin`-optimal family, `6/29` is the best `ERmin` point at both fixed finesse values, while `7/29` remains the geometry-favored point because its `L/R` stays closest to `0.5`.

## Pareto View
The Pareto table `pareto_frontier_Fmin_vs_ERmin.csv` uses `ER_min(F=87.00)` as the vertical metric and `F_min=tau0/s_min` as the horizontal cost.
| pareto_rank | k_fraction | F_min_tau0 | ER_min_dB_F87 | ER_mean_dB_F87 | geometry_gap_to_0p5 |
| --- | --- | --- | --- | --- | --- |
| 1 | 6/29 | 87.0 | 11.993 | 15.138 | 0.133764 |
| 2 | 10/37 | 111.0 | 12.05 | 15.508 | 0.063509 |

## Interpretation
- The reviewer-style question is valid: replacing `smin` by fixed-finesse `ERmin` does change the optimizer.
- That change does not invalidate the current `smin` derivation, because the two objectives answer different design questions.
- The current `7/29` point is consistent with the existing policy `maximize smin first, then prefer moderate geometry`.
- If the policy were changed to `maximize ERmin at fixed F=87 while staying within the current threshold`, `6/29` would be the more natural pick than `7/29`.

## Appendix Recommendation
Recommendation: keep the current `smin`-based appendix figure and add one clarifying sentence, rather than inserting a new default appendix figure. The extra Pareto/frontier plot generated here is better kept as reviewer-response backup material.
Suggested sentence: "The nonuniform example in Fig. S3 is selected under the `s_min` / `F_min` design objective; if one instead optimizes the fixed-finesse worst-channel `ER_sum`, the preferred rational candidate shifts, but only by trading against a higher required finesse or a less central cavity geometry."
