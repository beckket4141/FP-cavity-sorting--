# Projection/SMF overlap lightweight model

This script uses a deliberately simple multiplicative projection model:

- incident field: normalized `LG_0^l(w_in)`;
- phase-flattening reference: remove only the azimuthal phase and couple the remaining radial field to a fixed Gaussian SMF mode;
- complex-amplitude restoration reference: multiply by the normalized radial amplitude of the conjugate `LG_0^l(w_holo)` hologram, then couple to the same fixed Gaussian;
- fixed SMF waist is chosen as the l=0 optimum of the complex-amplitude product model, `w_smf = w_holo / sqrt(2)`.

The model is not an end-to-end SLM/4f/fiber simulation. Its purpose is to test whether a matched conjugate-amplitude projection automatically produces the same Gaussian spot for every l. In this model it does not: the restored radial envelope still broadens roughly with the LG mode scale.

| l | phase-flatten SMF | hologram power factor | conditional SMF | total detected | restored RMS / w | best SMF waist / w | best total |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.888889 | 0.500000 | 1.000000 | 0.500000 | 0.5000 | 0.7095 | 0.499994 |
| 1 | 0.465421 | 0.679570 | 0.500000 | 0.339785 | 0.8660 | 1.2238 | 0.573387 |
| 2 | 0.197531 | 0.692724 | 0.166667 | 0.115454 | 1.1180 | 1.5833 | 0.494914 |
| 3 | 0.077570 | 0.697414 | 0.050000 | 0.034871 | 1.3229 | 1.8729 | 0.438194 |
| 4 | 0.029264 | 0.699805 | 0.014286 | 0.009997 | 1.5000 | 2.1226 | 0.396608 |
| 5 | 0.010774 | 0.701252 | 0.003968 | 0.002783 | 1.6583 | 2.3473 | 0.364735 |
| 6 | 0.003902 | 0.702221 | 0.001082 | 0.000760 | 1.8028 | 2.5520 | 0.339385 |
| 7 | 0.001397 | 0.702915 | 0.000291 | 0.000205 | 1.9365 | 2.7367 | 0.318628 |
| 8 | 0.000495 | 0.703437 | 0.000078 | 0.000055 | 2.0616 | 2.9165 | 0.301240 |

Key reading:

- The fixed-SMF total detected fraction falls strongly with l in both phase-only and amplitude-weighted projection models.
- The best SMF waist increases with l, which is a compact way to say that the matched restoration field is not a single l-independent Gaussian mode.
- Therefore a real detection chain can easily have l-dependent diagonal response even when the input and restoration hologram labels match.
