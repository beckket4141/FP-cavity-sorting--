# Issue G: Single FP module vs multiport sorter

## Risk level

P0 / Medium-High.

## Potential reviewer concern

The experiment may be interpreted as a complete simultaneous nine-output sorter, while the demonstrated FP cavity is a mode-selective sorting module measured through sequential locking/projection conditions. The term "sorter" itself is supported by the predecessor work of Wei et al.; the remaining risk is scope, not terminology legitimacy.

## Why this matters

This is primarily a scope issue. Wei et al. explicitly established the language of a modular FP-resonator OAM sorter, where each tunable resonator filters one OAM state and a multiport sorter is constructed by cascading modules. The present manuscript should therefore position itself as a capacity/design-boundary extension of that FP-resonator sorter architecture, not as a standalone reinvention of the sorter concept.

## Current evidence

- Wei et al., "Active sorting of orbital angular momentum states of light with a cascaded tunable resonator," Light: Science & Applications 9, 10 (2020), explicitly calls the device a reconfigurable OAM sorter based on cascaded optical resonators.
- Wei et al. describes a modular process in which each module accepts multiple OAM states, outputs one selected state, and diverts the other states unaltered to subsequent modules.
- Wei et al. demonstrates a two-output cascaded FP-cavity sorter and states that additional FP cavities can be cascaded for more OAM states.
- The current experiment injects an equal-weight nine-mode input and measures sorting performance across locking conditions.
- The projection arm reads out modes sequentially.
- The model contribution is the design/capacity rule for a single FP module under a target set and finesse.

## Can claim

- The work follows the modular FP-resonator OAM sorter architecture established by Wei et al.
- The present experiment validates the capacity boundary of a single FP-cavity mode-selective sorting module.
- A complete multiport sorter can be constructed by cascading such modules, consistent with the predecessor architecture.
- The capacity rule describes how many target modes a module can spectrally isolate under the chosen threshold.

## Can cautiously say

- The module is a building block for high-dimensional OAM/LG sorting architectures.
- The present work generalizes the predecessor two-state/two-port demonstration toward a high-dimensional design rule, but it does not by itself demonstrate a full nine-output cascaded device.

## Should not claim

- Do not claim the experiment directly demonstrates a single-shot nine-output spatial sorter.
- Do not imply the sequential projection arm is itself the multiport output.
- Do not present the word "sorter" as unsupported by precedent; the stronger position is that the terminology follows Wei et al., while the current implementation is a single-module capacity validation.

## Safe response wording

We follow the modular FP-resonator OAM sorter architecture introduced by Wei et al., where each tunable resonator functions as a state-preserving mode-selective module and a multiport sorter is obtained by cascading such modules. The present experiment validates the capacity boundary of one such FP-cavity module for a nine-mode target set, rather than demonstrating a single-shot nine-output device. The model developed here specifies the spectral-spacing and finesse requirements for each module in this architecture.

## Optional supplement/table/figure

Prepare a concept figure:

- Left: single FP module, simultaneous input, selected transmitted mode, rejected/reflected residual modes.
- Right: Wei-style cascaded multiport sorter, repeated modules extracting target modes into separate ports.

## Cross-reference

- Issue H: transverse-order degeneracy.
- Issue F: capacity bound applies to the target set/module design.
- Issue J: data/package readiness if reviewers ask for implementation details.

## If reviewer pushes harder

Add a clarification to the main text and possibly a supplement schematic. Cite Wei et al. as the source of the modular/cascaded FP-OAM sorter architecture. Use "mode-selective FP sorting module" where needed, but avoid retreating to language that makes the FP sorter terminology appear unsupported.

## Action if reviewer explicitly asks

Revise terminology in abstract/conclusion if necessary and include the concept figure if the reviewer frames this as a major concern. The preferred framing is "capacity model for a modular FP-resonator OAM sorter" rather than "not really a sorter."
