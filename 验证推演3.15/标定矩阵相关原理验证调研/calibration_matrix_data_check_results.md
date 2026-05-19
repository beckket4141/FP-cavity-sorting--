# Calibration matrix data check

All source workbooks were opened read-only. No source workbook is modified by this script.

## Combined calibration response matrix S

| metric | value |
|---|---:|
| diag_mean_% | 11.0729 |
| diag_min_% | 3.79273 |
| diag_max_% | 19.4892 |
| offdiag_mean_% | 0.0275913 |
| offdiag_median_% | 0.001937 |
| offdiag_max_% | 0.167137 |
| diag_col_share_min_% | 92.3832 |
| diag_col_share_mean_% | 97.2257 |
| diag_col_share_max_% | 99.5521 |
| condition_number | 5.1504 |

## Raw vs diagonal-only vs full-matrix calibration

| method | diagonal share mean (%) | min (%) | max (%) | ER from mean share (dB) |
|---|---:|---:|---:|---:|
| full_matrix_calibration | 93.190768 | 92.075145 | 94.410181 | 11.3627 |
| diagonal_only_calibration | 91.594457 | 89.392035 | 93.831972 | 10.3730 |
| raw_uncalibrated | 88.900657 | 76.816829 | 97.154702 | 9.0361 |

## Workbook-level reported metrics

| source | metric | value |
|---|---|---:|
| deembedded aggregate | ER_sum_all_mean_dB | 11.40508625069569 |
| deembedded aggregate | ER_sum_all_errorbar95_dB | 0.2506947071451499 |
| deembedded aggregate | combined_diag_share_mean_% | 93.19076756509892 |
| deembedded aggregate | combined_diag_share_min_% | 92.07514528431582 |
| deembedded aggregate | combined_diag_share_max_% | 94.4101810351771 |
| raw aggregate | raw_ER_sum_all_mean_dB | 10.12102613312784 |
| raw aggregate | raw_ER_sum_all_errorbar95_dB | 1.369078156333417 |
| raw aggregate | combined_raw_diag_share_mean_% | 88.90065679088599 |
| raw aggregate | combined_raw_diag_share_min_% | 76.81682853743852 |
| raw aggregate | combined_raw_diag_share_max_% | 97.15470216771736 |

Key reading:

- The calibration matrix diagonal spans roughly a five-fold efficiency range, so raw powers are not a faithful FP-cavity sorting metric.
- Full-matrix calibration improves the merged diagonal share relative to raw and diagonal-only processing, indicating that off-diagonal readout response is small but not useless.
- The condition number is moderate for this 9 x 9 intensity-response matrix, so NNLS de-embedding is numerically plausible rather than an ill-conditioned artifact.
