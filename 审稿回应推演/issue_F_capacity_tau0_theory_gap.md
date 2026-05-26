# Issue F: Capacity bound, \(\tau_0\), and theory-experiment gap

## Risk level

P1 / Medium-High.

## Potential reviewer concern

The theory claims may be read too broadly: the capacity inequality for arbitrary target sets may look like a guaranteed achievable capacity, \(\tau_0=3\) may seem arbitrary, and the phrase "exact finite-\(M\) Airy prediction" may appear to include all experimental nonidealities.

## Why this matters

These are claim-boundary issues. They do not undermine the model if worded precisely, but overstatement in the abstract, conclusion, or response letter could invite major revision.

## F1. Arbitrary finite target sets: upper bound vs attainable optimum

### Can claim

- \(M\le\lfloor\mathcal{F}/\tau_0\rfloor\) is a universal upper bound from \(s_{\min}\le 1/M\).
- Uniform-step target sets can attain this bound under the closed-form optimal geometry.
- General nonuniform target sets require finite rational search to determine the attainable optimum.

### Should not claim

- Do not say every arbitrary finite target set can achieve the bound.

### Safe wording

For arbitrary finite target sets, the capacity inequality is a necessary upper bound. It becomes tight for uniform-step sets, while the attainable optimum for a general nonuniform set is determined by the finite rational search.

## F2. \(\tau_0=3\): design threshold

### Can claim

- \(\tau_0\) is a design threshold, not a universal constant.
- \(\tau_0=3\) corresponds to a conservative large-\(M\) lower bound of \(10.47\,\mathrm{dB}\) and sorting efficiency \(91.76\%\).
- For \(M=9\), \(\mathcal{F}_{\min}=M\tau_0=27\).

### Can cautiously say

- The choice balances experimentally accessible finesse and a meaningful nine-mode boundary demonstration.

### Should not claim

- Do not imply \(\tau_0=3\) is uniquely optimal for all applications.

### Safe wording

The parameter \(\tau_0\) sets the chosen isolation threshold. We use \(\tau_0=3\) as a representative operating point because it corresponds to a conservative \(ER_{\mathrm{sum}}\) bound of about \(10.47\,\mathrm{dB}\) while remaining experimentally accessible for a nine-mode boundary demonstration.

## F3. Finite-\(M\) Airy reference and theory-experiment gap

### Can claim

- The 12.04 dB line is the finite-\(M\) Airy reference evaluated within the adopted Airy lineshape model and measured finesse.
- The measured mean ER is 11.41 dB, below the ideal Airy reference but above the conservative 10.47 dB bound.
- The gap is consistent with experimental nonidealities such as mode matching, finite aperture, transmittance variation, and readout residuals.

### Should not claim

- Do not imply 12.04 dB includes all experimental nonidealities.
- Do not call the Airy reference "exact" without specifying "within the Airy model" or equivalent.

### Safe wording

The finite-\(M\) Airy value is an exact reference within the adopted Airy lineshape model and measured finesse. It is not intended to include all experimental nonidealities. The measured mean ER lies between this ideal reference and the conservative design bound, as expected for the actual cavity and mode-matching conditions.

## Current evidence

- `main.tex`: \(\tau_0=3\), \(10.47\,\mathrm{dB}\), \(91.76\%\), \(12.04\,\mathrm{dB}\).
- `supplement.tex`: tolerance map and finite-\(M\) Airy discussion.
- `triplicate_full9_aggregate.xlsx`: measured mean ER 11.405 dB and min channel above conservative bound.

## Cross-reference

- Issue G: single-module scope.
- Issue H: distinct transverse-order target sets.
- Issue E: local ER non-monotonicity.

## If reviewer pushes harder

Offer to revise wording in abstract/conclusion to say "upper capacity bound" for arbitrary finite sets and "attainable/tight for uniform-step target sets." If needed, add a short supplement paragraph distinguishing the Airy reference from the full experimental model.

## Action if reviewer explicitly asks

Modify wording rather than adding new experiments. Add a small table for \(\tau_0=2,3,4,5\) only if requested.

