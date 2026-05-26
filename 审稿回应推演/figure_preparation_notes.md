# Figure preparation notes

当前阶段只规划图件，不正式改稿或重画论文图。收到审稿意见后按需选择。

## Figure G: single FP module vs Wei-style cascaded multiport sorter

**Issue:** G.  
**Priority:** P0 if reviewer challenges sorter definition.

### Purpose

Clarify that the experiment follows the modular FP-resonator OAM sorter architecture established by Wei et al.: one tunable resonator acts as a mode-selective module, while a complete multiport sorter is built by cascading modules. The present paper contributes the high-dimensional capacity/design rule for each module.

### Suggested layout

- Left panel: simultaneous nine-mode input enters one FP module. The selected resonance mode is transmitted; other modes are rejected/reflected or passed to downstream stages.
- Right panel: Wei-style cascaded architecture. Multiple FP modules are tuned to different target modes and route them to separate output ports.

### Caption message

Single-module capacity validation is the natural module-level counterpart of the Wei-style cascaded sorter architecture; it is not the same as directly demonstrating a single-shot nine-output device.

## Figure A/C: raw matrix / response matrix / corrected matrix

**Issues:** A, C, D.  
**Priority:** P0 if response correction is challenged.

### Purpose

Make the correction pipeline transparent.

### Suggested panels

1. Raw detector-side projection matrix, column-normalized for visualization.
2. Independently measured response matrix \(S\).
3. Response-corrected sorting matrix.

### Required data

- `triplicate_full9_raw_aggregate.xlsx` / `combined_raw_percentage`
- `triplicate_full9_calib_matrix_heatmap.xlsx` / `combined_calib_S_percent`
- `triplicate_full9_aggregate.xlsx` / `combined_percentage`

### Caption message

Raw values include projection-arm response; corrected values estimate cavity-output modal weights under \(y=Sx\).

## Figure A: floor sensitivity table or plot

**Issue:** A.  
**Priority:** P0 if NNLS zeros are challenged.

### Purpose

Show ER conclusion does not rely on treating NNLS boundary zeros as exact physical zeros.

### Suggested format

Small table is likely enough:

- floor = min non-zero off-diagonal 0.0297%
- floor = 0.1%
- floor = 0.2%
- mean \(ER_{\mathrm{sum}}\)
- min \(ER_{\mathrm{sum}}\)
- mean ER drop

### Required data

- `full9_robustness_audit.xlsx` / `floor_sensitivity`

## Figure/Table B: errorbar policy comparison

**Issue:** B.  
**Priority:** only if reviewer challenges statistics.

### Purpose

Show the relation among SD, SEM, \(1.96\) SEM, and t-based 95% CI.

### Suggested format

Table rather than figure:

- \(l\)
- mean ER
- SD
- \(1.96\) SEM
- t95 SEM

### Required data

- `full9_robustness_audit.xlsx` / `ER_errorbar_compare`
- `full9_robustness_audit.xlsx` / `trans_errorbar_compare`

## Figure/Table F: \(\tau_0\) design threshold

**Issue:** F.  
**Priority:** P1 if threshold choice is challenged.

### Purpose

Clarify that \(\tau_0\) is a tunable design threshold and capacity scales as \(M_{\max}\approx\lfloor\mathcal{F}/\tau_0\rfloor\).

### Suggested format

Small table:

- \(\tau_0\)
- conservative \(ER_{\mathrm{sum}}^{(\infty)}\)
- conservative sorting efficiency
- required finesse for \(M=9\)

### Required data

- Existing manuscript analytical values.
- If exact entries for \(\tau_0=2,4,5\) are needed, regenerate from the theory script or manuscript formula before using.

## Figure E: folded-neighbor leakage table

**Issue:** E.  
**Priority:** P2, only if \(l=8>l=7\) is questioned.

### Purpose

Explain local ER non-monotonicity through different largest leakage channels.

### Suggested format

Table:

- lock \(l\)
- diagonal share
- largest leakage channel
- largest leakage percentage
- off-sum
- ER

### Required data

- `triplicate_full9_aggregate.xlsx` / `combined_percentage`
