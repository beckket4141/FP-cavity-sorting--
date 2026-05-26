# Issue E: \(l=8\) ER slightly higher than \(l=7\)

## Risk level

P2 / Low-Medium.

## Evidence

- \(l=7\): corrected diagonal 92.075%, \(ER_{\mathrm{sum}}=10.6629\,\mathrm{dB}\).
- \(l=8\): corrected diagonal 92.547%, \(ER_{\mathrm{sum}}=10.9468\,\mathrm{dB}\).
- Difference is about 0.28 dB.
- \(l=7\) and \(l=8\) transmittance values are nearly equal: 82.6473% and 82.7064%.

## Can claim

- ER is not expected to be strictly monotonic with \(l\), because each lock condition has a different folded-neighbor leakage pattern.
- Both \(l=7\) and \(l=8\) remain above the conservative \(10.47\,\mathrm{dB}\) bound.

## Can cautiously say

- The small \(l=8\) over \(l=7\) difference is consistent with run-to-run variation and local leakage differences.

## Should not claim

- Do not interpret \(l=8\) as physically better or easier than \(l=7\).
- Do not claim a monotonic ER trend.

## Safe response wording

The small non-monotonicity between \(l=7\) and \(l=8\) reflects local folded-neighbor leakage and run-to-run variation rather than a distinct physical advantage of \(l=8\). Both channels remain above the conservative design bound, so this local ordering does not affect the main conclusion.

## If reviewer pushes harder

Provide a folded-neighbor leakage table listing, for each lock channel, the largest off-diagonal leakage channels and their percentages.

