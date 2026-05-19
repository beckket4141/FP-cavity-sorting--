# Bad Branch Overlap Summary

- Window: `[a,b]=[1/5,3/10]`
- Target denominators: `29, 32, 35, 73`

## q=29

- Allowed branches: `6,7,8`
- Exact best rho: `1`
- `r=1`: covered `` / `6,7,8`, survivors `6,7,8`.
- `r=2`: covered `6,7,8` / `6,7,8`, survivors `none`.
  pattern `6` <= residues `5,24`
  pattern `7` <= residues `4,25`
  pattern `8` <= residues `11,18`

## q=32

- Allowed branches: `7,9`
- Exact best rho: `1`
- `r=1`: covered `` / `7,9`, survivors `7,9`.
- `r=2`: covered `7,9` / `7,9`, survivors `none`.
  pattern `7` <= residues `9,23`
  pattern `9` <= residues `7,25`

## q=35

- Allowed branches: `8,9`
- Exact best rho: `1`
- `r=1`: covered `` / `8,9`, survivors `8,9`.
- `r=2`: covered `8,9` / `8,9`, survivors `none`.
  pattern `8` <= residues `13,22`
  pattern `9` <= residues `4,31`

## q=73

- Allowed branches: `15,16,17,18,19,20,21`
- Exact best rho: `2`
- `r=2`: covered `15,17,18,19,20,21` / `15,16,17,18,19,20,21`, survivors `16`.
  pattern `15` <= residues `34,39`
  pattern `17` <= residues `30`
  pattern `18` <= residues `4`
  pattern `19` <= residues `23`
  pattern `20` <= residues `11`
  pattern `21` <= residues `7`
- `r=3`: covered `15,16,17,18,19,20,21` / `15,16,17,18,19,20,21`, survivors `none`.
  pattern `15` <= residues `5,34,39`
  pattern `16` <= residues `9`
  pattern `17` <= residues `13,30`
  pattern `18` <= residues `4,8`
  pattern `19` <= residues `23,27`
  pattern `20` <= residues `11,22`
  pattern `21` <= residues `7,14`

