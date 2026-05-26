# Issue C: Raw vs corrected response

## Risk level

P0 / High.

## Potential reviewer concern

The raw projection matrix and response-corrected matrix differ strongly, especially for high-\(l\) channels. A reviewer may ask whether the correction artificially improves performance or whether raw data contradicts the reported sorting efficiency.

## Why this matters

The raw matrix is detector-side readout \(y\), not the cavity-output modal weights \(x\). The correction removes the independently measured projection-arm response \(S\). This distinction must be clear to avoid misinterpreting raw high-\(l\) loss as poor cavity sorting.

## Current evidence

- Raw \(l=1\) diagonal is largest at 97.1547%, matching the largest readout response \(S_{11}=19.4892\%\).
- High-\(l\) raw diagonals are lower because readout response falls to \(S_{88}=3.7927\%\).
- After de-embedding, all corrected diagonal shares are between 92.075% and 94.410%.
- Calibration off-diagonal max is 0.1671%, and condition numbers are about 5.

## Quantitative result

Raw / response / corrected diagonal examples:

| \(l\) | raw diag | \(S_{ll}\) | corrected diag |
|---:|---:|---:|---:|
| 1 | 97.1547% | 19.4892% | 94.4110% |
| 7 | 79.5755% | 5.3864% | 92.0764% |
| 8 | 76.8168% | 3.7927% | 92.5471% |

Full table: `full9_robustness_audit.xlsx` / `raw_S_corrected_diag`.

## Can claim

- Raw projection values include the projection-arm response.
- The response matrix was independently measured for each run.
- The corrected matrix is a de-embedded estimate of the cavity-output modal weights under the calibrated readout model.
- Raw \(l=1\) being highest is explained by the largest \(S_{11}\), not by superior cavity sorting for \(l=1\).

## Can cautiously say

- The correction isolates the cavity sorting behavior from detector/projection-arm efficiency, within the calibrated linear model \(y=Sx\).

## Should not claim

- Do not call the raw matrix the cavity sorting matrix.
- Do not imply correction removes all possible experimental nonidealities.
- Do not say high-\(l\) raw suppression is entirely unrelated to mode quality; it is mainly readout response, while high-\(l\) transmittance and mode matching also matter.

## Safe response wording

The raw projection matrix is a detector-side readout and includes the mode-dependent response of the projection arm. The response matrix \(S\) was independently measured in each run and then used to de-embed the raw vectors through \(y=Sx\). The largest raw diagonal at \(l=1\) follows directly from the largest calibrated readout response \(S_{11}\). After de-embedding, the corrected matrix remains diagonally dominant across all nine modes.

## Optional supplement/table/figure

- Three-panel figure: raw projection matrix, readout-response matrix \(S\), response-corrected sorting matrix.
- Table: raw diagonal, \(S_{ll}\), corrected diagonal, corrected ER.
- Data-package note explaining which matrices are raw and which are corrected.

## Cross-reference

- Issue A: NNLS zero boundary.
- Issue D: high-\(l\) readout SNR.
- Issue J: data package readiness.

## If reviewer pushes harder

Provide diagonal-only correction and raw/corrected comparison from `triplicate_full9_percentage_compare.xlsx` or regenerate an explicit comparison table. If the concern shifts to noise amplification in high-\(l\) channels, use Issue D.

## Action if reviewer explicitly asks

Add a supplement figure/table rather than overloading the main text.

