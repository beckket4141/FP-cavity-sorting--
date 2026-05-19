# q Counting Bounds Summary

- Window: `[a,b]=[1/5,3/10]`
- Denominator search bound: `90`
- Difference set max: `45`

## Current Example Highlight

- `q=29`: `profile=1:27`, `mu_q=3`, `layered upper=1`, `composite lower=1`, exact `rho_q^*=1`.
- Best branches at `q=29`: `6,7,8`.

## Composite-Denominator Snapshots

- `q=32`: `profile=1:15;2:8;4:3;8:2;16:1`, `layered upper=1`, `composite lower=1`, exact `rho_q^*=1`.
- `q=35`: `profile=1:22;5:5;7:4`, `layered upper=2`, `composite lower=1`, exact `rho_q^*=1`.
- `q=36`: `profile=1:9;2:6;3:4;4:4;6:2;9:2;12:2;18:1`, `layered upper=0`, `composite lower=0`, exact `rho_q^*=N/A`.
- `q=40`: `profile=1:13;2:7;4:4;5:3;8:3;10:2`, `layered upper=0`, `composite lower=0`, exact `rho_q^*=0`.
- `q=42`: `profile=1:8;2:9;3:6;6:6;7:1;14:2;21:1`, `layered upper=0`, `composite lower=0`, exact `rho_q^*=0`.

## Interpretation

- `profile_by_gcd` records how the nonzero difference residues are distributed across gcd layers.
- `layered_upper_bound_rho` is a stronger necessary-condition upper bound than the old coarse count bound.
- `composite_lower_bound_rho` extends the prime-denominator lower bound to general composite denominators.
- When layered upper and composite lower meet, `rho_q^*` is determined exactly by counting alone.
