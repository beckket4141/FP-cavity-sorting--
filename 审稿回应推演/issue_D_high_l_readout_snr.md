# Issue D: High-\(l\) readout SNR

## Risk level

P1 / Medium-High.

## Potential reviewer concern

The response matrix diagonal falls to \(S_{88}=3.79\%\). A reviewer may ask whether the high-\(l\) correction is reliable or whether the inversion approaches the detector noise floor.

## Why this matters

Low readout response can amplify measurement noise. The current data support numerical stability and repeatability, but do not include a complete dark-noise/background noise budget.

## Current evidence

- \(S_{88}=3.7927\%\), the smallest diagonal response.
- The three response matrices have condition numbers 5.05, 4.99, and 5.43.
- Corrected high-\(l\) diagonal shares remain above 92%.
- Repeated runs show stable high-\(l\) ER values; the lowest corrected ER remains about 10.66 dB at \(l=7\).
- Transmittance for \(l=7,8\) is about 82.65% and 82.71%, respectively.

## Quantitative result

See:

- `triplicate_full9_calib_matrix_heatmap.xlsx` / `combined_calib_S_percent`, `summary`.
- `full9_robustness_audit.xlsx` / `condition_numbers`.
- `triplicate_transmittance_l0_8_stats.txt`.

## Can claim

- The response-matrix inversion is moderately conditioned, not severely ill-conditioned.
- High-\(l\) readout response is lower, but repeated corrected results remain stable.
- Current evidence supports numerical robustness under the measured response matrix.

## Can cautiously say

- The lower \(S_{88}\) increases sensitivity to readout noise, but no instability is observed in the run-to-run corrected metrics.

## Should not claim

- Do not claim a dark-noise-limited SNR margin without dark/background measurements.
- Do not claim \(S_{88}\) is far above all instrument noise floors unless measured.

## Safe response wording

The high-\(l\) readout response is lower than that of the low-\(l\) channels, which is why the response calibration is necessary. The corresponding response matrices remain moderately conditioned, with condition numbers around 5 across the independent runs, and the corrected high-\(l\) metrics are stable across repeated measurements. A separate detector dark-noise or background-only measurement would be needed to quote an absolute noise-floor margin.

## Optional supplement/table/figure

- Table: \(S_{ll}\), corrected diagonal share, corrected ER, transmittance for each \(l\).
- If new data are collected: dark reading, background-only reading, power meter resolution, high-\(l\) SNR table.

## Cross-reference

- Issue C: raw vs corrected response.
- Issue A: NNLS zero boundary.
- Issue J: data readiness.

## If reviewer pushes harder

Propose or perform a small add-on measurement:

1. Power meter dark reading with blocked input.
2. Background-only reading with no first-order selected signal.
3. Repeated high-\(l\) projection readings near the weakest channels.
4. Recompute absolute SNR margin for \(S_{88}\) and high-\(l\) raw signals.

## Action if reviewer explicitly asks

If the review requires a noise-floor claim, do not rely on current data alone. Either add the measurement or explicitly limit the claim to numerical conditioning and run-to-run repeatability.

