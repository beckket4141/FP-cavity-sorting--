# Full 9-mode sorting robustness audit

- Data source: `D:\自制软件\1.thesis\Data\full`
- Output workbook: `full9_robustness_audit.xlsx`
- Runs: 1, 2, 3

## Key computed facts

- Combined corrected diagonal mean: 93.191%
- Combined corrected ER_sum mean: 11.397 dB
- Combined corrected ER_sum min: 10.652 dB
- Calibration condition numbers: 5.05, 4.99, 5.43; mean 5.16
- Recomputed NNLS max absolute difference from source corrected matrices: 4.931e-10 W
- Smallest non-zero corrected off-diagonal entry: 0.0297%

## NNLS zero entries

- `ch3, lock1`: raw pct per run = 0.0762%, 0.0635%, 0.0367%; LS x = -1.002e-08, -1.355e-08, -1.586e-08; NNLS x = 0.000e+00, 0.000e+00, 0.000e+00.
- `ch4, lock2`: raw pct per run = 0.0726%, 0.0757%, 0.0622%; LS x = -2.324e-08, -2.703e-08, -2.726e-08; NNLS x = 0.000e+00, 0.000e+00, 0.000e+00.
- `ch5, lock3`: raw pct per run = 0.1002%, 0.0878%, 0.0476%; LS x = -3.757e-08, -5.112e-08, -5.039e-08; NNLS x = 0.000e+00, 0.000e+00, 0.000e+00.
- `ch6, lock4`: raw pct per run = 0.1116%, 0.1962%, 0.1207%; LS x = -6.922e-08, -6.721e-08, -7.256e-08; NNLS x = 0.000e+00, 0.000e+00, 0.000e+00.
- `ch7, lock5`: raw pct per run = 0.3007%, 0.3678%, 0.3420%; LS x = -6.764e-08, -6.463e-08, -5.977e-08; NNLS x = 0.000e+00, 0.000e+00, 0.000e+00.
- `ch7, lock8`: raw pct per run = 0.3275%, 0.9485%, 0.1667%; LS x = -1.836e-07, -2.481e-07, -4.305e-08; NNLS x = 0.000e+00, 0.000e+00, 0.000e+00.
- `ch8, lock6`: raw pct per run = 0.5932%, 0.6106%, 0.5256%; LS x = -6.934e-08, -7.657e-08, -7.988e-08; NNLS x = 0.000e+00, 0.000e+00, 0.000e+00.

Interpretation: each listed zero is reproduced by rerunning NNLS on the per-run raw vector and response matrix. The raw detector entry is non-zero, while the fitted physical component is placed on the non-negativity boundary.

## Floor sensitivity

|   floor_% | renormalized   |   ER_mean_dB |   ER_min_dB |   ER_delta_mean_dB |
|----------:|:---------------|-------------:|------------:|-------------------:|
|    0.0297 | False          |      11.3821 |     10.6523 |            -0.0150 |
|    0.0297 | True           |      11.3821 |     10.6523 |            -0.0150 |
|    0.0100 | False          |      11.3921 |     10.6523 |            -0.0051 |
|    0.0100 | True           |      11.3921 |     10.6523 |            -0.0051 |
|    0.0500 | False          |      11.3719 |     10.6523 |            -0.0252 |
|    0.0500 | True           |      11.3719 |     10.6523 |            -0.0252 |
|    0.1000 | False          |      11.3469 |     10.6523 |            -0.0502 |
|    0.1000 | True           |      11.3469 |     10.6523 |            -0.0502 |
|    0.2000 | False          |      11.2975 |     10.6417 |            -0.0997 |
|    0.2000 | True           |      11.2975 |     10.6417 |            -0.0997 |

## ER errorbar comparison

|      l |   ER_sum_mean_dB |   SD_dB |   SEM_dB |   1.96SEM_dB |   t95SEM_df2_dB |
|-------:|-----------------:|--------:|---------:|-------------:|----------------:|
| 0.0000 |          12.0148 |  0.4243 |   0.2450 |       0.4802 |          1.0541 |
| 1.0000 |          12.2787 |  0.1643 |   0.0949 |       0.1860 |          0.4082 |
| 2.0000 |          12.1768 |  0.1839 |   0.1062 |       0.2081 |          0.4568 |
| 3.0000 |          11.5758 |  0.2600 |   0.1501 |       0.2942 |          0.6458 |
| 4.0000 |          11.1600 |  0.2626 |   0.1516 |       0.2971 |          0.6523 |
| 5.0000 |          11.0628 |  0.4566 |   0.2636 |       0.5167 |          1.1343 |
| 6.0000 |          10.7673 |  0.4846 |   0.2798 |       0.5484 |          1.2038 |
| 7.0000 |          10.6629 |  0.4068 |   0.2349 |       0.4603 |          1.0106 |
| 8.0000 |          10.9468 |  0.3153 |   0.1821 |       0.3568 |          0.7833 |

## Transmittance errorbar comparison

|      l |   trans_mean_% |   SD_% |   SEM_% |   1.96SEM_% |   t95SEM_df2_% |
|-------:|---------------:|-------:|--------:|------------:|---------------:|
| 0.0000 |        92.8928 | 0.7105 |  0.4102 |      0.8041 |         1.7651 |
| 1.0000 |        91.6597 | 0.9309 |  0.5375 |      1.0535 |         2.3126 |
| 2.0000 |        90.4994 | 1.0776 |  0.6221 |      1.2194 |         2.6769 |
| 3.0000 |        88.8197 | 1.8507 |  1.0685 |      2.0943 |         4.5974 |
| 4.0000 |        88.5996 | 2.5189 |  1.4543 |      2.8504 |         6.2572 |
| 5.0000 |        86.5429 | 2.2577 |  1.3035 |      2.5549 |         5.6085 |
| 6.0000 |        85.1426 | 3.2250 |  1.8620 |      3.6495 |         8.0114 |
| 7.0000 |        82.6473 | 2.5499 |  1.4722 |      2.8854 |         6.3342 |
| 8.0000 |        82.7064 | 2.4165 |  1.3951 |      2.7345 |         6.0028 |

## Raw / response / corrected diagonal

|      l |   raw_diag_% |   S_diag_% |   corrected_diag_% |   corrected_ER_sum_dB |
|-------:|-------------:|-----------:|-------------------:|----------------------:|
| 0.0000 |      94.1673 |    10.9971 |            94.0681 |               12.0025 |
| 1.0000 |      97.1547 |    19.4892 |            94.4110 |               12.2768 |
| 2.0000 |      96.3821 |    17.5364 |            94.2853 |               12.1745 |
| 3.0000 |      94.8659 |    14.7849 |            93.4893 |               11.5713 |
| 4.0000 |      92.2693 |    11.4964 |            92.8815 |               11.1554 |
| 5.0000 |      86.9946 |     9.0980 |            92.7177 |               11.0489 |
| 6.0000 |      81.8796 |     7.0749 |            92.2427 |               10.7522 |
| 7.0000 |      79.5755 |     5.3864 |            92.0764 |               10.6523 |
| 8.0000 |      76.8168 |     3.7927 |            92.5470 |               10.9403 |

## Rebuttal-ready wording

The raw projection matrix is the detector-side readout and therefore includes the independently measured projection-arm response. For each independent run, we re-solved Sx=y using both unconstrained least squares and non-negative least squares. The zero off-diagonal entries in the corrected matrix are NNLS boundary estimates: the corresponding raw detector powers are non-zero, but the best physical non-negative solution assigns those components to zero. The response matrices are moderately conditioned (condition numbers about 5), and imposing conservative leakage floors on the zero entries changes the mean ER_sum only weakly, leaving the full-load sorting conclusion intact.
