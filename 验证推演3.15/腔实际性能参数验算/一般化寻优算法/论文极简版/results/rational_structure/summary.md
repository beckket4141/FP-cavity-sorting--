# Rational Structure Summary

- Mode set: `[1, 4, 6, 10, 15, 18, 22, 27, 31, 37, 40, 46]`
- Search window: `k in [0.2, 0.3]`
- Difference-set size: `35`
- Difference set: `[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 30, 31, 33, 34, 36, 39, 40, 42, 45]`

## Current Best Rational Candidate

- Best denominator `q`: `29`
- Best branch `m/q`: `7/29`
- Best `s_min`: `1/29 = 0.034482758621`
- Best `(L/R)`: `0.472930545707`
- Limiting differences: `[4, 25, 33]`

## What This Verifies

- The best candidates in the current moderate branch window cluster on denominator `q=29`.
- For `q=29`, the best admissible branches are `m=6,7,8`, i.e. `6/29, 7/29, 8/29`.
- Among these tied branches, the current main script picks the one closest to `L/R=0.5`, namely `7/29`.

## Important Caveat

- The stronger claim 'for fixed q, s_min does not depend on m' is false in general. A counterexample already appears at `q=73`.
- At `q=73`, `m=16` gives `s_min=2/73`.
- At `q=73`, `m=21` gives `s_min=1/73`.
- At `q=73`, `m=20` gives `s_min=1/73`.
- At `q=73`, `m=19` gives `s_min=1/73`.
- At `q=73`, `m=18` gives `s_min=1/73`.
- At `q=73`, `m=17` gives `s_min=1/73`.

## Safer Conjecture

- For a fixed finite mode set, the optimum seems to be controlled by the difference set `D`, not by the mode count itself.
- The denominator `q` is the main structural quantity to search.
- Once `q` is fixed, one should still scan admissible coprime `m` in the branch window, because different `m` can yield different `s_min` for some denominators.
- If a rational-optimum theorem is proved, then the continuous search over `k` can be reduced to an exact discrete search over `(q,m)`.
