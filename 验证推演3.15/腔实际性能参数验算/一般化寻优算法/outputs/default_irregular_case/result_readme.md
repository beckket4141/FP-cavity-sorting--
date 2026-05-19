# Generalized FP Screening Workspace

## What the program does
- Searches the configured k interval for non-continuous candidate total-order sets.
- Builds a conflict graph under the configured task threshold tau_0 and feasibility finesse budget.
- Solves the maximum coexistence subset with a branch-and-bound maximum-clique search on the coexistence graph.
- Adds a near-optimal candidate layer that keeps feasible subsets above a configurable size threshold around the k-local maximum subset size.
- Separates geometry screening (`s_min`, `F_min`) from physical evaluation (`F_eval`, exact periodic Airy response).
- Exports ranked solutions, region summaries, per-solution structured data, and paper-ready plots.

## Main inputs
- candidate_modes = [1, 4, 6, 10, 15, 18, 22, 27, 31, 37, 40, 46]
- tau_0 = 3.0
- feasibility_finesse = 32.0
- F_eval = 32.0
- k search = [0.01, 0.49] with 6001 coarse samples
- near_optimal_size_drop = 1
- near_optimal_min_subset_size = 5
- max_near_optimal_subsets_per_k = 120

## How to read the outputs
- `main_ranked_solutions.csv` is the main table for thesis writing; `all_ranked_solutions.csv` is kept as a compatibility alias.
- `near_optimal_ranked_candidates.csv` is the trade-off table for appendix / supplementary analysis.
- `subset_regions.csv` groups the same best subset over contiguous k regions and keeps one representative working point per region.
- `search_landscape.csv` is the full screening trace for reproducibility and appendix use.
- Each `solution_rankXX_*` folder contains the structured data and figures for one representative solution.

## Main-result layer vs near-optimal layer
- Main-result layer: one representative maximum-coexistence subset per contiguous k region; best suited to Section 5.4 main-text presentation.
- Near-optimal layer: 173475 exported feasible candidate subsets, including 157710 non-maximum alternatives; best suited to appendix / trade-off analysis.
- Near-optimal threshold: subset_size >= min(max_subset_size, max(near_optimal_min_subset_size, max_subset_size - near_optimal_size_drop)).
- Near-optimal rows mark whether a subset is maximal for that k and how far its subset size falls below the k-local maximum.

## Figures most suitable for the main text
- The best-solution circle plot of mode positions on the normalized FP ring.
- The search landscape plot showing subset size / s_min / F_min versus k.
- The best-solution conditional-probability heatmap.
- The per-mode ER_sum / separation-efficiency bar plot.

## Better suited to appendix / supplementary material
- Near-optimal ranked candidate tables.
- All subset-region summaries.
- Pairwise distance tables and raw response matrices for each representative solution.
