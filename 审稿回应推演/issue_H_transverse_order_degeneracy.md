# Issue H: Transverse-order degeneracy

## Risk level

P0 / High.

## Potential reviewer concern

An FP cavity resonance depends on transverse order \(N=2p+|l|+1\), so it cannot distinguish modes with the same \(N\), including \(+l\) and \(-l\) for the same \(p\). A reviewer may argue that the manuscript overstates OAM sorting generality.

## Why this matters

This is a fundamental physics boundary. The model remains valid for distinct transverse-order target sets, but the manuscript must not imply that a single FP cavity uniquely sorts all OAM labels.

## Current evidence

- The theory uses the transverse order \(N\).
- The experiment uses \(p=0,l=0\ldots8\), for which \(N=|l|+1\) is one-to-one.
- Degenerate modes require additional elements if the goal is to distinguish them.
- Wei et al. explicitly notes that two OAM states with opposite topological charges are degenerate in a single FP cavity because the resonant cavity length depends on \(|l|\), and suggests using only one sign or adding extra elements to remove the degeneracy.

## Can claim

- The FP cavity discriminates transverse-order resonances.
- The experimental target set avoids Gouy-order degeneracy.
- The \(p=0,l=0\ldots8\) experiment is a valid boundary case for distinct transverse orders.

## Can cautiously say

- The method applies directly to target sets with distinct transverse orders; for degenerate sets it can be combined with additional mode-discriminating elements.

## Should not claim

- Do not claim a single FP cavity distinguishes \(+l\) from \(-l\).
- Do not claim it distinguishes arbitrary \((p,l)\) states with identical \(N\).
- Do not call the capacity bound a guarantee for degenerate mode labels without extra degrees of freedom.

## Safe response wording

The FP resonance condition depends on the transverse order \(N=2p+|l|+1\). Therefore, a single FP cavity discriminates distinct transverse orders rather than unique OAM signs or arbitrary \((p,l)\) labels. This degeneracy is already recognized in the predecessor FP-resonator OAM sorter work. The experimental set \(p=0,l=0\ldots8\) avoids this degeneracy because \(N=|l|+1\) is one-to-one in that subspace. We can clarify this scope in the revised text.

## Optional supplement/table/figure

- Short table showing \(p=0,l=0\ldots8\) maps to \(N=1\ldots9\).
- Optional note listing examples of degenerate pairs.

## Cross-reference

- Issue G: sorter definition and module scope.
- Issue F: capacity bound for target sets.
- Issue I: state-preservation boundary.

## If reviewer pushes harder

State explicitly that resolving same-\(N\) degeneracies would require additional mode-discriminating optics, such as interferometric OAM sign sorting, MPLC, Dove-prism interferometry, or other basis-specific elements. Do not retrofit such capability into the current single-cavity claim.

## Action if reviewer explicitly asks

Revise abstract/conclusion wording if needed to say "LG transverse-order target sets" or "the selected \(p=0,l=0\ldots8\) subspace" where broad "OAM sorting" could be misunderstood.
