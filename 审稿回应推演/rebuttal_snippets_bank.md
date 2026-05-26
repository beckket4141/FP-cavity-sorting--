# Rebuttal snippets bank

本文件汇总可复用英文短段。收到真实审稿意见后，应按 issue card 裁剪，不要整段机械复制。

## G. Single FP module vs multiport sorter

**Risk:** P0 / Medium-High.  
**Use:** response letter; may require concept figure.

We follow the modular FP-resonator OAM sorter architecture introduced by Wei et al., where each tunable resonator functions as a state-preserving mode-selective module and a multiport sorter is obtained by cascading such modules. The present experiment validates the capacity boundary of one such FP-cavity module for a nine-mode target set, rather than demonstrating a single-shot nine-output device. The model developed here specifies the spectral-spacing and finesse requirements for each module in this architecture.

## H. Transverse-order degeneracy

**Risk:** P0 / High.  
**Use:** response letter and possible text clarification.

The FP resonance condition depends on the transverse order \(N=2p+|l|+1\). Thus, a single FP cavity discriminates distinct transverse orders rather than the sign of the OAM charge or an arbitrary unique \((p,l)\) label. This degeneracy is already recognized in the predecessor FP-resonator OAM sorter work. The experimental set \(p=0,l=0\ldots8\) avoids this degeneracy because \(N=|l|+1\) is one-to-one in this subspace.

## A. NNLS zero boundary

**Risk:** P0 / High.  
**Use:** response letter; supplement table recommended if challenged.

The off-diagonal zero entries in the response-corrected matrix are NNLS boundary estimates rather than raw measured zeros. The corresponding raw detector powers are finite, while unconstrained least-squares inversion assigns small negative components. Under the physical non-negativity constraint, NNLS places these components at zero. Conservative leakage-floor tests show that replacing these entries by finite floors up to 0.2% changes the mean \(ER_{\mathrm{sum}}\) by only about 0.10 dB.

## C. Raw vs corrected response

**Risk:** P0 / High.  
**Use:** response letter; supplement figure/table recommended.

The raw projection matrix is a detector-side readout and includes the mode-dependent response of the projection arm. The response matrix \(S\) was independently measured in each run and used to de-embed the raw vectors through \(y=Sx\). The maximum raw diagonal at \(l=1\) is consistent with the largest measured readout response \(S_{11}\), and should not be interpreted as a stronger cavity sorting response for that mode.

## B. Errorbar statistics

**Risk:** P0 / High.  
**Use:** response letter if statistical wording is raised.

The uncertainty bars were calculated as \(1.96\) times the standard error across three independent runs and were intended to characterize run-to-run variation. We agree that for \(n=3\) this should not be described as a strict Student-t 95% confidence interval. We can revise the wording to state the calculation explicitly, or, if required, recalculate the bars using the \(t_{0.975,2}\) factor.

## I. State-preservation evidence boundary

**Risk:** P1 / Medium.  
**Use:** response letter and wording clarification.

The CCD images demonstrate preservation of the transverse intensity profiles at the resonance peaks. We agree that these images alone do not constitute full complex-field or single-photon state tomography. The state-preserving character referred to here follows from the linear FP-cavity eigenmode response, while the present experiment directly verifies transverse-profile consistency in the measured intensity.

## F. Capacity bound and \(\tau_0\)

**Risk:** P1 / Medium-High.  
**Use:** response letter and abstract/conclusion wording if needed.

For arbitrary finite target sets, \(M\le\lfloor\mathcal{F}/\tau_0\rfloor\) is a necessary upper bound derived from \(s_{\min}\le1/M\). It becomes tight for uniform-step target sets, while the attainable optimum for a general nonuniform set is determined by the finite rational search. The parameter \(\tau_0\) is a design threshold; \(\tau_0=3\) is used here as a representative operating point that gives a conservative \(ER_{\mathrm{sum}}\) bound of about \(10.47\,\mathrm{dB}\).

## F. Finite-\(M\) Airy reference

**Risk:** P1 / Medium.  
**Use:** response letter or text clarification.

The finite-\(M\) Airy value is an exact reference within the adopted Airy lineshape model and measured finesse. It is not intended to include all experimental nonidealities. The measured mean ER lies between this ideal reference and the conservative design bound, consistent with residual mode matching, transmittance variation, and other experimental imperfections.

## D. High-\(l\) readout SNR

**Risk:** P1 / Medium-High.  
**Use:** response letter; avoid overclaiming.

The high-\(l\) readout response is lower than that of the low-\(l\) channels, which motivates the independent response calibration. The response matrices remain moderately conditioned, with condition numbers around 5 across independent runs, and the corrected high-\(l\) metrics are stable across repeated measurements. A separate detector dark-noise or background-only measurement would be needed to quote an absolute noise-floor margin.

## E. \(l=8\) vs \(l=7\)

**Risk:** P2 / Low-Medium.  
**Use:** short response only if asked.

The small non-monotonicity between \(l=7\) and \(l=8\) reflects local folded-neighbor leakage and run-to-run variation rather than a distinct physical advantage of \(l=8\). Both channels remain above the conservative design bound, so this local ordering does not affect the main conclusion.

## J. Data package

**Risk:** P1 / Medium.  
**Use:** response letter if data availability is requested.

We have prepared the raw projection matrices, response matrices, response-corrected matrices, and aggregation/audit scripts in a compact reproducibility package. These files can be provided upon request or uploaded as supplementary data according to the journal's data policy.
