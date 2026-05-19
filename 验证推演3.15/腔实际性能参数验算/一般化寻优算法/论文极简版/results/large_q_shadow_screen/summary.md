# Large-q Shadow Screen Summary

## Setup

- Difference-set max: `D_max=45`
- Exact denominator bound: `Q_I(S)=90`
- Large-q range considered here: `46 <= q <= 90`
- Difference-set complement on `[1,D_max]`: `1, 20, 29, 32, 35, 37, 38, 41, 43, 44`

## Exact Large-q Facts For The Current Example

- Large-q denominators with exact best `rho=1`: `46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 74, 75, 77, 79, 80, 81, 86`
- Large-q denominators with exact best `rho=2`: `73, 76, 78, 82, 83, 84, 85, 87, 88, 89, 90`
- First denominator where a shell-1 vacancy appears: `q=73`
- All denominators with shell-1 vacancy branches: `73, 76, 78, 82, 83, 84, 85, 87, 88, 89, 90`
- Any admissible branch with exact `rho>=3` on the large-q range: `False`

## Meaning

- For `q>D_max`, the nonzero difference residues are exactly the original difference set `D(S)` itself.
- Therefore fixed-branch screening can be done by projecting each inverse shell onto `[1,D_max]` and checking whether that projection already hits `D(S)`.
- In the current example, every large-q branch either hits `D(S)` on shell 1 or, if shell 1 misses, it already hits on shell 2.
- Since shell-1 vacancies start only at `q=73`, every large-q branch satisfies `s_min<=2/73=0.027397260274 < 1/29=0.034482758621`.
- Hence no denominator in `46 <= q <= 90` can beat the known optimum `q=29` for the current 12-mode example.
