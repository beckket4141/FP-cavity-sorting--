# Bound Meeting Summary

- Window: `[a,b]=[1/5,3/10]`
- Denominator search bound: `90`
- One-step exact cases: `2`
- Positive one-step exact cases: `2`

## Key Examples

- `q=29`: `upper=1`, `lower=1`, `surplus=3`, `critical layers at r+1=1`, exact `rho_q^*=1`.
- `q=32`: `upper=1`, `lower=1`, `surplus=2`, `critical layers at r+1=1`, exact `rho_q^*=1`.
- `q=35`: `upper=2`, `lower=1`, `surplus=-42`, `critical layers at r+1=1`, exact `rho_q^*=1`.

## Interpretation

- `branch_surplus_at_r > 0` means the lower-bound counting argument still leaves at least one branch uncovered by all low-shell bad sets.
- `critical_layers_at_r_plus_1` lists the gcd layers that are already overcrowded at the next radius, forcing the upper bound down to `r`.
- When both appear simultaneously, `rho_q^*` is fixed exactly by pure counting.
