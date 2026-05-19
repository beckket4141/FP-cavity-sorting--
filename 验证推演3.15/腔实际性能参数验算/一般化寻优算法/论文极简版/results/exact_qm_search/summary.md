# Exact (q,m) Search Summary

- Mode set: `[1, 4, 6, 10, 15, 18, 22, 27, 31, 37, 40, 46]`
- Difference set max: `D_max=45`
- Window: `[0.2, 0.3] = [1/5, 3/10]`
- Exact denominator bound: `Q_I(S)=max(den(a), den(b), 2 D_max) = 90`

## Best Exact Candidate

- `q=29`
- `m=7`
- `k=7/29 ≈ 0.241379310344828`
- `s_min=1/29 ≈ 0.034482758620690`
- `(L/R)=0.472930545707291`
- Limiting differences: `4,25,33`

## Meaning

- This result is no longer a dense real-variable scan.
- It is the exact finite search guaranteed by the denominator bound theorem.
- For the current 5.4 example, the exact discrete search still returns `k=7/29`.
