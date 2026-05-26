# Issue J: Data/package readiness

## Risk level

P1 / Medium.

## Potential reviewer concern

OE reviewers may request data or scripts supporting the response correction, fitting, matrices, and figures.

## Why this matters

The most likely technical concerns involve reproducibility of the matrix correction and final Fig. 5 values. A compact package reduces response time during revision.

## Minimal package contents

### Data

- `triplicate_full9_aggregate.xlsx`
- `triplicate_full9_raw_aggregate.xlsx`
- `triplicate_full9_calib_matrix_heatmap.xlsx`
- `triplicate_transmittance_l0_8_stats.txt`
- Per-run source folders `1`, `2`, `3`, or a reduced subset containing:
  - `full9_matrix_with_uncertainty.xlsx`
  - `calib_matrix_with_uncertainty.xlsx`
  - `channel_snr_analysis.xlsx`
  - `channel_snr_summary.txt`

### Scripts

- `aggregate_triplicate_full9.py`
- `aggregate_transmittance_l0_8.py`
- `full9_robustness_audit.py`
- Any final figure-generation script for Fig. 5, if requested.

### Documentation

- `README_response_correction.md`
- `data_provenance_map.md`
- `full9_robustness_audit_summary.md`

## Can claim

- The key final matrices, raw matrices, calibration matrices, and audit scripts are available internally and can be packaged if requested.

## Can cautiously say

- Data can be made available upon reasonable request if journal policy permits, with raw experimental files curated into a compact reproducible package.

## Should not claim

- Do not claim the package is already public unless uploaded.
- Do not claim full raw instrument logs are curated unless checked.

## Safe response wording

We have prepared the raw projection matrices, response matrices, response-corrected matrices, and aggregation/audit scripts in a compact reproducibility package. These files can be provided upon request or uploaded as supplementary data according to the journal's data policy.

## Cross-reference

- All issues, especially A, B, C, D.

## If reviewer pushes harder

Create a zip package with a README and a one-command or step-by-step reproduction path. If file size is large, provide reduced matrices and scripts sufficient to regenerate the reported Fig. 5 metrics.

## Action if reviewer explicitly asks

Package the minimal set first; avoid sending the entire uncurated experiment folder unless specifically requested.

