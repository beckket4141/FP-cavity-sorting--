# Random Validation Summary

- Random seed: `20260322`
- Case count: `100`
- Set size: `12`
- Mode range: `[1, 60]`
- Search window: `k in [0.2, 0.3]`
- Rational search denominator cap: `q <= 200`

## Outcome Counts

- `match`: `100`
- `rational_beats_grid`: `0`
- `unmatched`: `0`

## Interpretation

- `match` means the best rational candidate up to the scanned denominator cap matches the dense continuous search to within the tolerance.
- `rational_beats_grid` usually means the dense grid missed a narrow optimum but the rational candidate found it more cleanly.
- `unmatched` means the dense continuous search still beats the rational search cap by more than the tolerance; this may indicate either a larger-denominator optimum or simple undersampling effects.

## Most Frequent Best Denominators

- `q=22` appears `8` times.
- `q=24` appears `6` times.
- `q=25` appears `5` times.
- `q=47` appears `5` times.
- `q=18` appears `4` times.
- `q=19` appears `4` times.
- `q=21` appears `4` times.
- `q=26` appears `4` times.
- `q=27` appears `4` times.
- `q=49` appears `4` times.

## Largest Continuous Advantage Cases

- Case 65: gap = `0.00000000`, continuous `k≈0.240000`, rational `6/25`.
- Case 90: gap = `0.00000000`, continuous `k≈0.240000`, rational `6/25`.
- Case 97: gap = `0.00000000`, continuous `k≈0.240000`, rational `6/25`.
- Case 3: gap = `-0.00000000`, continuous `k≈0.233333`, rational `7/30`.
- Case 80: gap = `-0.00000000`, continuous `k≈0.216667`, rational `13/60`.
- Case 94: gap = `-0.00000000`, continuous `k≈0.233333`, rational `7/30`.
- Case 79: gap = `-0.00000000`, continuous `k≈0.291667`, rational `5/24`.
- Case 96: gap = `-0.00000000`, continuous `k≈0.291667`, rational `5/24`.
- Case 29: gap = `-0.00000000`, continuous `k≈0.291667`, rational `5/24`.
- Case 39: gap = `-0.00000000`, continuous `k≈0.291667`, rational `5/24`.

## Largest Rational Advantage Cases

- Case 62: gap = `-0.00000925`, continuous `k≈0.236842`, rational `9/38`.
- Case 63: gap = `-0.00000905`, continuous `k≈0.261905`, rational `5/21`.
- Case 60: gap = `-0.00000893`, continuous `k≈0.271739`, rational `25/92`.
- Case 9: gap = `-0.00000754`, continuous `k≈0.296297`, rational `7/27`.
- Case 42: gap = `-0.00000655`, continuous `k≈0.238096`, rational `5/21`.
- Case 92: gap = `-0.00000626`, continuous `k≈0.275363`, rational `19/69`.
- Case 73: gap = `-0.00000619`, continuous `k≈0.228572`, rational `8/35`.
- Case 44: gap = `-0.00000552`, continuous `k≈0.212766`, rational `10/47`.
- Case 49: gap = `-0.00000552`, continuous `k≈0.212766`, rational `10/47`.
- Case 12: gap = `-0.00000514`, continuous `k≈0.237288`, rational `14/59`.
