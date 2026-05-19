# Large-q Complement-Layer Summary

## Setup

- Difference-set max: `D_max=45`
- Large-q range: `46 <= q <= 90`
- Difference complement on `[1,D_max]`: `1, 20, 29, 32, 35, 37, 38, 41, 43, 44`

## Exact Verification

- Branch count in the large-q range: `186`
- `rho>=2` <=> shell-1 projection misses `D`: `186/186` matches
- `rho>=3` <=> both shell-1 and shell-2 projections miss `D`: `186/186` matches

## Current Example

- Denominators with at least one shell-1 vacancy branch: `73, 76, 78, 82, 83, 84, 85, 87, 88, 89, 90`
- Denominators with at least one shell-2 vacancy branch: `none`
- Therefore every large-q admissible branch is already forced by shell 1 or shell 2; no large-q branch reaches `rho>=3`.
