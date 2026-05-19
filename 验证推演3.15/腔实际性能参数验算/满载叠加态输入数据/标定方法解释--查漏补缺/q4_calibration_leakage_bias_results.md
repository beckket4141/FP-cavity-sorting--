# Q4 calibration-leakage bias check

- Generated at: `2026-03-28T18:36:30`
- Data root: `D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\腔实际性能参数验算\满载叠加态输入数据\最终数据`
- Fixed finesse reused from Q2/Q3: `32.21`

## Core result

- Using the measured lock spacings and the same Airy model as Q2, the nearest-neighbor cavity leakage coefficient is indeed about `2.002%` on average, with a run-and-column range of `1.650%` to `2.350%`.
- But that coefficient is not the same thing as the amount actually mixed into the measured calibration column `S[:,k]`. From the present `S` matrix itself, the two-neighbor total postmix fraction is conservatively bounded by only `0.0091%` on average and `0.0314%` in the worst column.
- Propagating this conservative upper bound through the same NNLS correction pipeline changes the reported mean success rate by only `0.0076` percentage points on average and the mean `ER_sum` by only `0.0052 dB`.
- Even the largest entry-wise change in the normalized 9x9 matrix remains only `0.0284` percentage points, and the largest per-column `ER_sum` change is `0.0195 dB`.

## Why the raw Q4 statement is too strong

- `~2%` is the cavity leak coefficient of a neighboring mode *if that neighbor is present in the calibration input*.
- The actual contamination absorbed into `S[:,k]` must still be multiplied by however much nearest-neighbor impurity existed before the cavity.
- The current data imply that this pre-cavity nearest-neighbor impurity was at most about `0.247%` on average and `1.839%` at the worst single-neighbor case.
- So the physically relevant calibration impurity is sub-`10^-3` in fraction units, not a literal `2%` mixed into each measured column of `S`.

## Literal 2% scenario check

- For completeness, the script also tests the reviewer-style literal scenario that each calibration column truly absorbs its full nearest-neighbor cavity leakage. That scenario forces the inferred ideal response matrix to develop negative entries at the `10^-3` to `10^-2` level, which is physically inconsistent with the present measured `S`.

## Per-run summary

### Run 1
- Nearest-neighbor cavity leakage: mean `2.006%`, range `1.653%` to `2.350%`.
- Total calibration postmix upper bound per column: mean `0.0093%`, max `0.0314%`.
- Data-driven upper-bound bias: mean success `0.0069` pct-pt high, mean `ER_sum` `0.0046 dB` high.
- Literal full-leak scenario: mean success bias `3.664` pct-pt, mean `ER_sum` bias `2.114 dB`, minimum inferred ideal-response entry `-5.0734e-03`.

### Run 2
- Nearest-neighbor cavity leakage: mean `2.000%`, range `1.662%` to `2.258%`.
- Total calibration postmix upper bound per column: mean `0.0095%`, max `0.0304%`.
- Data-driven upper-bound bias: mean success `0.0085` pct-pt high, mean `ER_sum` `0.0060 dB` high.
- Literal full-leak scenario: mean success bias `3.669` pct-pt, mean `ER_sum` bias `2.103 dB`, minimum inferred ideal-response entry `-4.5049e-03`.

### Run 3
- Nearest-neighbor cavity leakage: mean `2.001%`, range `1.650%` to `2.253%`.
- Total calibration postmix upper bound per column: mean `0.0085%`, max `0.0255%`.
- Data-driven upper-bound bias: mean success `0.0074` pct-pt high, mean `ER_sum` `0.0050 dB` high.
- Literal full-leak scenario: mean success bias `3.626` pct-pt, mean `ER_sum` bias `1.957 dB`, minimum inferred ideal-response entry `-4.7100e-03`.

