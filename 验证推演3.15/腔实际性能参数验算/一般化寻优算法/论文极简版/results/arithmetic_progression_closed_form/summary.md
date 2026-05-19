# Arithmetic-Progression Closed-Form Verification

This report verifies the closed-form claim for equally spaced mode-order sets
`S_{N_\mathrm{start},\Delta_\mathrm{ord},M}`.
The exact search is compared against the predicted unconstrained optimum
`s_min^*=1/M` and against the full optimal branch family
`k^*=(n+m/M)/\Delta_\mathrm{ord}` with `gcd(m,M)=1` and `0<k^*<1/2`.
## Global Summary

- Total test cases: `12`
- Cases with exact best value `1/M`: `12/12`
- Cases where the full optimal family matches exact search: `12/12`
- Cases where the minimal subfamily is contained in exact search: `12/12`
- Repeated `(Delta_ord, M)` groups passing `N_start`-invariance: `4/4`
- Cases where the full optimal family is strictly larger than the minimal subfamily: `(N_start=1, Delta_ord=3, M=5); (N_start=3, Delta_ord=3, M=5); (N_start=1, Delta_ord=3, M=9); (N_start=1, Delta_ord=4, M=9); (N_start=4, Delta_ord=4, M=9); (N_start=1, Delta_ord=5, M=7); (N_start=2, Delta_ord=5, M=7); (N_start=1, Delta_ord=6, M=8); (N_start=5, Delta_ord=6, M=8)`


## N_start=1, Delta_ord=1, M=5

- Mode set: `[1, 2, 3, 4, 5]`
- Exact best `s_min`: `1/5`
- Predicted best `s_min`: `1/5`
- Exact best branch family: `1/5, 2/5`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/5, 2/5`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/5, 2/5`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `False`

## N_start=1, Delta_ord=2, M=5

- Mode set: `[1, 3, 5, 7, 9]`
- Exact best `s_min`: `1/5`
- Predicted best `s_min`: `1/5`
- Exact best branch family: `1/10, 1/5, 3/10, 2/5`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/10, 1/5, 3/10, 2/5`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/10, 1/5, 3/10, 2/5`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `False`

## N_start=1, Delta_ord=3, M=5

- Mode set: `[1, 4, 7, 10, 13]`
- Exact best `s_min`: `1/5`
- Predicted best `s_min`: `1/5`
- Exact best branch family: `1/15, 2/15, 1/5, 4/15, 2/5, 7/15`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/15, 2/15, 1/5, 4/15, 2/5, 7/15`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/15, 2/15, 1/5, 4/15`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `True`

## N_start=3, Delta_ord=3, M=5

- Mode set: `[3, 6, 9, 12, 15]`
- Exact best `s_min`: `1/5`
- Predicted best `s_min`: `1/5`
- Exact best branch family: `1/15, 2/15, 1/5, 4/15, 2/5, 7/15`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/15, 2/15, 1/5, 4/15, 2/5, 7/15`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/15, 2/15, 1/5, 4/15`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `True`

## N_start=1, Delta_ord=2, M=9

- Mode set: `[1, 3, 5, 7, 9, 11, 13, 15, 17]`
- Exact best `s_min`: `1/9`
- Predicted best `s_min`: `1/9`
- Exact best branch family: `1/18, 1/9, 2/9, 5/18, 7/18, 4/9`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/18, 1/9, 2/9, 5/18, 7/18, 4/9`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/18, 1/9, 2/9, 5/18, 7/18, 4/9`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `False`

## N_start=1, Delta_ord=3, M=9

- Mode set: `[1, 4, 7, 10, 13, 16, 19, 22, 25]`
- Exact best `s_min`: `1/9`
- Predicted best `s_min`: `1/9`
- Exact best branch family: `1/27, 2/27, 4/27, 5/27, 7/27, 8/27, 10/27, 11/27, 13/27`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/27, 2/27, 4/27, 5/27, 7/27, 8/27, 10/27, 11/27, 13/27`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/27, 2/27, 4/27, 5/27, 7/27, 8/27`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `True`

## N_start=1, Delta_ord=4, M=9

- Mode set: `[1, 5, 9, 13, 17, 21, 25, 29, 33]`
- Exact best `s_min`: `1/9`
- Predicted best `s_min`: `1/9`
- Exact best branch family: `1/36, 1/18, 1/9, 5/36, 7/36, 2/9, 5/18, 11/36, 13/36, 7/18, 4/9, 17/36`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/36, 1/18, 1/9, 5/36, 7/36, 2/9, 5/18, 11/36, 13/36, 7/18, 4/9, 17/36`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/36, 1/18, 1/9, 5/36, 7/36, 2/9`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `True`

## N_start=4, Delta_ord=4, M=9

- Mode set: `[4, 8, 12, 16, 20, 24, 28, 32, 36]`
- Exact best `s_min`: `1/9`
- Predicted best `s_min`: `1/9`
- Exact best branch family: `1/36, 1/18, 1/9, 5/36, 7/36, 2/9, 5/18, 11/36, 13/36, 7/18, 4/9, 17/36`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/36, 1/18, 1/9, 5/36, 7/36, 2/9, 5/18, 11/36, 13/36, 7/18, 4/9, 17/36`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/36, 1/18, 1/9, 5/36, 7/36, 2/9`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `True`

## N_start=1, Delta_ord=5, M=7

- Mode set: `[1, 6, 11, 16, 21, 26, 31]`
- Exact best `s_min`: `1/7`
- Predicted best `s_min`: `1/7`
- Exact best branch family: `1/35, 2/35, 3/35, 4/35, 1/7, 6/35, 8/35, 9/35, 2/7, 11/35, 12/35, 13/35, 3/7, 16/35, 17/35`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/35, 2/35, 3/35, 4/35, 1/7, 6/35, 8/35, 9/35, 2/7, 11/35, 12/35, 13/35, 3/7, 16/35, 17/35`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/35, 2/35, 3/35, 4/35, 1/7, 6/35`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `True`

## N_start=2, Delta_ord=5, M=7

- Mode set: `[2, 7, 12, 17, 22, 27, 32]`
- Exact best `s_min`: `1/7`
- Predicted best `s_min`: `1/7`
- Exact best branch family: `1/35, 2/35, 3/35, 4/35, 1/7, 6/35, 8/35, 9/35, 2/7, 11/35, 12/35, 13/35, 3/7, 16/35, 17/35`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/35, 2/35, 3/35, 4/35, 1/7, 6/35, 8/35, 9/35, 2/7, 11/35, 12/35, 13/35, 3/7, 16/35, 17/35`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/35, 2/35, 3/35, 4/35, 1/7, 6/35`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `True`

## N_start=1, Delta_ord=6, M=8

- Mode set: `[1, 7, 13, 19, 25, 31, 37, 43]`
- Exact best `s_min`: `1/8`
- Predicted best `s_min`: `1/8`
- Exact best branch family: `1/48, 1/16, 5/48, 7/48, 3/16, 11/48, 13/48, 5/16, 17/48, 19/48, 7/16, 23/48`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/48, 1/16, 5/48, 7/48, 3/16, 11/48, 13/48, 5/16, 17/48, 19/48, 7/16, 23/48`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/48, 1/16, 5/48, 7/48`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `True`

## N_start=5, Delta_ord=6, M=8

- Mode set: `[5, 11, 17, 23, 29, 35, 41, 47]`
- Exact best `s_min`: `1/8`
- Predicted best `s_min`: `1/8`
- Exact best branch family: `1/48, 1/16, 5/48, 7/48, 3/16, 11/48, 13/48, 5/16, 17/48, 19/48, 7/16, 23/48`
- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `1/48, 1/16, 5/48, 7/48, 3/16, 11/48, 13/48, 5/16, 17/48, 19/48, 7/16, 23/48`
- Full family matches exact search: `True`
- Predicted minimal subfamily `k=m/(M Delta_ord)`: `1/48, 1/16, 5/48, 7/48`
- Minimal subfamily contained in exact search: `True`
- Full family strictly larger than minimal subfamily: `True`

## N_start Invariance Check

The theory predicts that `N_start` only translates the orbit on the circle and should not change either
the optimal value or the optimal branch family. The repeated `(Delta_ord, M)` pairs below verify this directly.

- Delta_ord=3, M=5, N_start in {1,3}: `True`; best `s_min=1/5`; branch family `1/15,2/15,1/5,4/15,2/5,7/15`
- Delta_ord=4, M=9, N_start in {1,4}: `True`; best `s_min=1/9`; branch family `1/36,1/18,1/9,5/36,7/36,2/9,5/18,11/36,13/36,7/18,4/9,17/36`
- Delta_ord=5, M=7, N_start in {1,2}: `True`; best `s_min=1/7`; branch family `1/35,2/35,3/35,4/35,1/7,6/35,8/35,9/35,2/7,11/35,12/35,13/35,3/7,16/35,17/35`
- Delta_ord=6, M=8, N_start in {1,5}: `True`; best `s_min=1/8`; branch family `1/48,1/16,5/48,7/48,3/16,11/48,13/48,5/16,17/48,19/48,7/16,23/48`

