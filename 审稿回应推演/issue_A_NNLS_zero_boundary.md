# Issue A: NNLS zero boundary

## Risk level

P0 / High.

## Potential reviewer concern

The response-corrected matrix contains seven off-diagonal zero entries even though the raw projection matrix has finite readings. A reviewer may suspect that NNLS or post-processing artificially removed crosstalk and inflated the reported ER.

## Why this matters

The final sorting matrix and ER values are reported after response correction. If the zero entries are interpreted as exact physical zeros, the result appears over-processed. The correct interpretation is numerical and physical: these entries are non-negative least-squares boundary estimates.

## Current evidence

- Raw detector-side entries at the seven positions are finite.
- Unconstrained least-squares estimates are small negative values.
- NNLS sets the corresponding components to zero under the physical non-negativity constraint.
- Recomputed NNLS agrees with the source corrected matrices to within \(4.93\times10^{-10}\,\mathrm{W}\).
- The three response matrices have condition numbers 5.05, 4.99, and 5.43.
- Conservative leakage floors up to 0.2% change mean \(ER_{\mathrm{sum}}\) by only about 0.10 dB.

## Quantitative result

See `data_provenance_map.md` and `full9_robustness_audit.xlsx`:

- `nnls_zero_trace`: raw values, LS values, NNLS values, residuals, active set.
- `nnls_reproduction`: agreement between recomputed NNLS and source corrected matrices.
- `floor_sensitivity`: ER changes after replacing zero entries with finite floors.

The seven combined corrected zero positions are:

- ch3, lock1
- ch4, lock2
- ch5, lock3
- ch6, lock4
- ch7, lock5
- ch7, lock8
- ch8, lock6

## Can claim

- The zero entries are reproduced by rerunning NNLS from the per-run raw vector \(y\) and response matrix \(S\).
- The raw detector powers at those positions are non-zero.
- The corresponding unconstrained LS estimates are small negative values.
- These zero entries are NNLS boundary estimates, not measured physical zeros.
- Applying conservative finite leakage floors does not alter the conclusion that the ER values remain above the conservative design bound.

## Can cautiously say

- The zero entries are below the resolvable level of the response de-embedding procedure.
- The correction is numerically stable because \(\kappa(S)\approx5\), but the high-\(l\) channels remain more sensitive to noise than low-\(l\) channels.

## Should not claim

- Do not claim the physical crosstalk at those positions is exactly zero.
- Do not claim the raw experiment directly measured zero leakage.
- Do not claim a complete dark-noise-limited floor unless additional background measurements are provided.

## Safe response wording

The off-diagonal zero entries in the response-corrected matrix are NNLS boundary estimates rather than raw measured zeros. For these positions, the raw detector-side powers are finite, while the unconstrained least-squares solution assigns small negative components. Under the physical non-negativity constraint, NNLS places these components at zero. A conservative leakage-floor test shows that replacing these entries with finite floors up to 0.2% changes the mean \(ER_{\mathrm{sum}}\) by only about 0.10 dB, leaving the sorting conclusion unchanged.

## Optional supplement/table/figure

- Table: zero position, raw percentage, LS value, NNLS value, residual.
- Table or plot: floor sensitivity for 0.0297%, 0.1%, and 0.2%.
- Short supplement paragraph after the NNLS equation.

## Cross-reference

- Issue C: raw vs corrected response.
- Issue B: errorbar statistics.
- Issue D: high-\(l\) readout SNR.

## If reviewer pushes harder

Provide `full9_robustness_audit.xlsx` sheets `nnls_zero_trace`, `nnls_reproduction`, and `floor_sensitivity`. If they ask for detector noise floors, move to Issue D and state that additional dark/background measurements would be needed for an absolute noise-floor analysis.

## Action if reviewer explicitly asks

Add a compact supplement subsection explaining NNLS boundary estimates and include a table or floor-sensitivity statement. Do not rewrite the main text defensively unless requested.

