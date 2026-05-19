# Inverse-Shell Criterion Summary

## Verification

- Search window: `[a,b]=[1/5,3/10]`
- Denominator bound: `Q_I(S)=90`
- Branch-level match count: `250/250`
- Denominator-level match count: `80/80`
- Result: the inverse-shell prediction reproduces the exact `rho_q(m)` and the exact best `(q,m)` classification on the full `q<=Q_I(S)` range.

## Exact Design Corollaries

- If `q` has a zero residue, then every admissible branch collides and `rho_q(m)=0`.
- If `q` is zero-free and every admissible inverse pair `{±m^{-1}}` is hit by the residue set, then every admissible branch is forced to `rho_q(m)=1`, hence `s_min(m/q)=1/q` for all admissible `m`.
- If `q` is zero-free and some admissible inverse pair `{±m^{-1}}` is missed, then that branch automatically satisfies `rho_q(m)>=2`, so `q` is immediately worth deeper search.

## Current Example

- `q=29`: all admissible inverse pairs are hit; `missed_first_shell_m_list=`; exact `rho` spectrum `1:3`.
- `q=73`: the only missed first-shell branch is `m=16`; exact best branches `16`; exact `rho` spectrum `1:6;2:1`.

## q Classification in the Current 5.4 Example

- Zero-free q with all admissible inverse pairs hit: `29, 32, 35, 37, 38, 41, 43, 44, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 74, 75, 77, 79, 80, 81, 86`
- Zero-free q with at least one first-shell vacancy: `73, 76, 78, 82, 83, 84, 85, 87, 88, 89, 90`

## Empirical Boundary

- Nontrivial branch-invariant positive-rho q (at least two admissible branches): `29, 32, 35, 37, 38, 41, 43, 44, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 74, 75, 77, 79, 80, 81, 86`
- No nontrivial branch-invariant case with common `rho>1` appeared on `q<=Q_I(S)`.
