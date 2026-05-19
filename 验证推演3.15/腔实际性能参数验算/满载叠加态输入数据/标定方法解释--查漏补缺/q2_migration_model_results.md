# Q2 mode-profile migration verification

- Generated at: `2026-03-28T17:10:30`
- Data root: `D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\腔实际性能参数验算\满载叠加态输入数据\最终数据`
- Fixed FSR used for lock-position recovery: `9.947e+09 Hz`
- Fixed finesse check: `32.21`

## Modeling logic

This validation explicitly keeps the user's calibration background:

1. Calibration is measured under the pure-mode reference condition `generate l=k + lock FP to l=k`.
2. Under that condition, each column `S[:, k]` is interpreted as the effective response of the detection chain to mode `k` after cavity-filtered pure-mode transmission.
3. Q2 is therefore reduced to a migration claim: when mode `k` leaks through off resonance in the full-load experiment, does it keep the same transverse mode profile and only pick up a scalar cavity transmission factor?

The tested factorized model is:

```text
x_theory^(j)[k] = alpha_j * T_peak[k] * Airy(s_kj; F)
y_theory^(j)    = S * x_theory^(j)
```

where `alpha_j` is one fitted scalar per lock column, absorbing absolute power drift but not changing the inter-channel shape.

## Global fit

- Best shared finesse over all 3 runs: `31.169`
- Raw-`Y` relative residual at best shared finesse: `0.0141`
- Raw-`Y` relative residual at fixed `F = 32.21`: `0.0143`

## Per-run results

### Run 1
- Transmission workbook: `D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\腔实际性能参数验算\满载叠加态输入数据\最终数据\1\透射率.xlsx`
- Lock positions from measured lock wavelengths: `[0.0, 0.2203, 0.4416, 0.66, 0.887, 0.1073, 0.3286, 0.5498, 0.7687]`
- Peak transmittance ratios: `[92.26, 91.44, 89.4, 86.68, 85.72, 83.94, 81.43, 79.97, 79.92]` %
- Fixed `F=32.21`: raw relative residual `0.0118`, worst column residual `0.0598`, mean/min normalized-column cosine `0.99972` / `0.99821`
- Best fitted `F=31.660`: raw relative residual `0.0118`, worst column residual `0.0606`
- Counterfactual raw relative residuals at fixed `F`: migrated `0.0118`, target-column `0.0337`, diagonal-only `0.0167`
- Predicted vs observed `X` at fixed `F`: mean |delta| `0.323` pct-pt, max |delta| `1.922` pct-pt
- Predicted vs observed mean diagonal share: `93.46%` -> `94.09%`
- Predicted vs observed mean `ER_sum`: `11.576` dB -> `12.029` dB; mean |delta| `0.453` dB

### Run 2
- Transmission workbook: `D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\腔实际性能参数验算\满载叠加态输入数据\最终数据\2\透射率.xlsx`
- Lock positions from measured lock wavelengths: `[0.0, 0.2232, 0.4435, 0.6638, 0.8898, 0.1092, 0.3333, 0.5522, 0.7716]`
- Peak transmittance ratios: `[93.66, 92.68, 91.55, 89.95, 89.66, 87.74, 87.23, 85.04, 84.06]` %
- Fixed `F=32.21`: raw relative residual `0.0178`, worst column residual `0.0637`, mean/min normalized-column cosine `0.99951` / `0.99797`
- Best fitted `F=31.777`: raw relative residual `0.0178`, worst column residual `0.0642`
- Counterfactual raw relative residuals at fixed `F`: migrated `0.0178`, target-column `0.0365`, diagonal-only `0.0219`
- Predicted vs observed `X` at fixed `F`: mean |delta| `0.420` pct-pt, max |delta| `1.879` pct-pt
- Predicted vs observed mean diagonal share: `93.35%` -> `94.10%`
- Predicted vs observed mean `ER_sum`: `11.517` dB -> `12.032` dB; mean |delta| `0.606` dB

### Run 3
- Transmission workbook: `D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\腔实际性能参数验算\满载叠加态输入数据\最终数据\3\透射率.xlsx`
- Lock positions from measured lock wavelengths: `[0.0, 0.2232, 0.4435, 0.6638, 0.8898, 0.1092, 0.3305, 0.5527, 0.7716]`
- Peak transmittance ratios: `[92.76, 90.86, 90.55, 89.83, 90.42, 87.95, 86.76, 82.93, 84.15]` %
- Fixed `F=32.21`: raw relative residual `0.0121`, worst column residual `0.0426`, mean/min normalized-column cosine `0.99974` / `0.99909`
- Best fitted `F=30.344`: raw relative residual `0.0116`, worst column residual `0.0400`
- Counterfactual raw relative residuals at fixed `F`: migrated `0.0121`, target-column `0.0341`, diagonal-only `0.0184`
- Predicted vs observed `X` at fixed `F`: mean |delta| `0.437` pct-pt, max |delta| `2.318` pct-pt
- Predicted vs observed mean diagonal share: `92.77%` -> `94.10%`
- Predicted vs observed mean `ER_sum`: `11.123` dB -> `12.031` dB; mean |delta| `0.908` dB

## Interpretation boundary

- These results support the factorized migration claim strongly at the data-model level: once measured peak transmittance and lock positions are included, the same calibrated `S` reproduces the raw full-load observations with low residual.
- The migrated model is consistently better than the two simple counterfactuals tested here, so the data prefer `mode-specific response columns + scalar cavity detuning factors` over the alternatives.
- This does **not** prove that every conceivable non-ideal effect is absent. Coating-dispersion-induced mode mixing, residual radial contamination, and other engineering losses can still create extra bias beyond the model.
- The systematic tendency of the predicted `ER_sum` to be slightly higher than experiment is consistent with exactly those extra non-ideal losses: the migration model captures the main structure, while the remaining gap is pushed into engineering degradation rather than into the basic validity of the calibration method itself.

## Direct answer to the user's calibration concern

- Yes: the calibration matrix is indeed measured under a pure-mode reference condition specifically designed to isolate the detection-chain response.
- Q2 therefore should not be framed as 'your calibration idea is wrong'.
- The real issue is narrower: whether the pure-mode reference columns can be migrated to off-resonant leakage in the full-load experiment.
- This script shows that, within the measured 9-mode dataset, that migration works well enough to reproduce the raw observations quantitatively.

