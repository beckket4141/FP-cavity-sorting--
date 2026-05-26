# Issue B: Errorbar statistics

## Risk level

P0 / High.

## Potential reviewer concern

The manuscript currently describes some error bars as 95% confidence intervals from three independent runs, while the aggregation script uses \(1.96\times\mathrm{SEM}\). For \(n=3\), a strict two-sided 95% CI should use \(t_{0.975,2}=4.303\).

## Why this matters

The data conclusion is stable, but the statistical label can be challenged as technically incorrect. This is a wording/definition risk rather than a result-validity risk.

## Current evidence

- `aggregate_triplicate_full9.py` uses `ci95 = 1.96 * sem`.
- `full9_robustness_audit.xlsx` compares SD, SEM, \(1.96\) SEM, and t-based 95% SEM for Fig. 5(c) ER and Fig. 5(d) transmittance.
- t-based 95% error bars are about 2.20 times the current \(1.96\) SEM bars for per-channel \(n=3\).

## Quantitative result

Examples:

- \(l=7\) ER: \(1.96\mathrm{SEM}=0.4603\,\mathrm{dB}\), t95 SEM \(=1.0106\,\mathrm{dB}\).
- \(l=6\) transmittance: \(1.96\mathrm{SEM}=3.6495\%\), t95 SEM \(=8.0114\%\).

Full tables are in `full9_robustness_audit.xlsx`, sheets `ER_errorbar_compare` and `trans_errorbar_compare`.

## Can claim

- The plotted/aggregated uncertainty can be described as `mean ± 1.96 SEM from three independent runs` if the figures are not redrawn.
- The data conclusion does not rely on the exact statistical label: all corrected diagonal shares remain above 92%, and all ER values remain above the conservative bound.

## Can cautiously say

- The current \(1.96\) SEM bars characterize run-to-run variation, but they should not be presented as strict Student-t confidence intervals for \(n=3\).

## Should not claim

- Do not call \(1.96\mathrm{SEM}\) a strict 95% confidence interval for per-channel \(n=3\).
- Do not mix SD, SEM, and CI labels across main text, figure captions, and supplement.

## Safe response wording

We thank the reviewer for pointing out the statistical wording. The reported uncertainty was calculated as \(1.96\) times the standard error across three independent runs and is intended to characterize run-to-run variation. We will revise the wording to state this explicitly and avoid referring to these bars as strict 95% confidence intervals. If a strict confidence interval is required, the error bars can be recalculated using the Student-t factor for two degrees of freedom.

## Optional supplement/table/figure

- Table comparing SD, SEM, \(1.96\mathrm{SEM}\), and t95 SEM for Fig. 5(c,d).
- If required, regenerated Fig. 5(c,d) with t-based 95% CI.

## Cross-reference

- Issue A: floor sensitivity shows result stability independent of zero entries.
- Issue C: corrected matrix values and diagonal shares.

## If reviewer pushes harder

Use t-based 95% CI and redraw Fig. 5(c,d). Expect high-\(l\) transmittance error bars to become visibly larger; the core mean values and design-bound comparison remain unchanged.

## Action if reviewer explicitly asks

Either revise wording only (`mean ± 1.96 SEM`) or regenerate figures with t-based 95% CI, depending on the reviewer's requested standard.

