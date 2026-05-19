from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import ProblemConfig
from .core import DetailedSolution, QuickSolution, RegionRepresentative, quick_solution_to_row


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def export_summary_tables(
    output_dir: Path,
    config: ProblemConfig,
    ranked_regions: list[RegionRepresentative],
    landscape_df: pd.DataFrame,
    region_df: pd.DataFrame,
    candidate_df: pd.DataFrame,
) -> tuple[Path, Path, Path, Path]:
    ensure_dir(output_dir)
    summary_rows = [
        quick_solution_to_row(rank, region.region_id, region, region.best_solution)
        for rank, region in enumerate(ranked_regions, start=1)
    ]
    summary_df = pd.DataFrame(summary_rows)

    summary_csv = output_dir / "main_ranked_solutions.csv"
    legacy_summary_csv = output_dir / "all_ranked_solutions.csv"
    landscape_csv = output_dir / "search_landscape.csv"
    region_csv = output_dir / "subset_regions.csv"
    candidate_csv = output_dir / "near_optimal_ranked_candidates.csv"

    summary_df.to_csv(summary_csv, index=False, encoding="utf-8-sig")
    summary_df.to_csv(legacy_summary_csv, index=False, encoding="utf-8-sig")
    landscape_df.to_csv(landscape_csv, index=False, encoding="utf-8-sig")
    region_df.to_csv(region_csv, index=False, encoding="utf-8-sig")
    candidate_df.to_csv(candidate_csv, index=False, encoding="utf-8-sig")

    if config.output.export_excel:
        with pd.ExcelWriter(output_dir / "screening_summary.xlsx") as writer:
            summary_df.to_excel(writer, sheet_name="main_ranked_solutions", index=False)
            candidate_df.to_excel(writer, sheet_name="near_optimal_candidates", index=False)
            landscape_df.to_excel(writer, sheet_name="search_landscape", index=False)
            region_df.to_excel(writer, sheet_name="subset_regions", index=False)
        with pd.ExcelWriter(output_dir / "all_ranked_solutions.xlsx") as writer:
            summary_df.to_excel(writer, sheet_name="ranked_solutions", index=False)

    return summary_csv, candidate_csv, landscape_csv, region_csv


def export_detailed_solution(solution_dir: Path, detail: DetailedSolution, rank: int, region: RegionRepresentative) -> None:
    ensure_dir(solution_dir)
    quick = detail.quick

    pd.DataFrame(
        [{"mode": mode, "pos": quick.pos_all[mode], "selected": mode in quick.subset_modes} for mode in sorted(quick.pos_all)]
    ).to_csv(solution_dir / "positions_all_modes.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(detail.pairwise_rows).to_csv(solution_dir / "pairwise_distances.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(detail.per_mode_records).to_csv(solution_dir / "per_mode_metrics.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        detail.raw_response_matrix,
        index=[f"out_{mode}" for mode in quick.subset_modes],
        columns=[f"in_{mode}" for mode in quick.subset_modes],
    ).to_csv(solution_dir / "raw_response_matrix.csv", encoding="utf-8-sig")
    pd.DataFrame(
        detail.condition_matrix,
        index=[f"out_{mode}" for mode in quick.subset_modes],
        columns=[f"in_{mode}" for mode in quick.subset_modes],
    ).to_csv(solution_dir / "condition_probability_matrix.csv", encoding="utf-8-sig")

    payload = {
        "rank": rank,
        "region_id": region.region_id,
        "k": quick.k,
        "L_over_R": quick.L_over_R,
        "subset_modes": list(quick.subset_modes),
        "subset_size": quick.subset_size,
        "s_min": quick.s_min,
        "F_min": quick.F_min,
        "F_eval_used": quick.F_eval_used,
        "avg_ER_sum_dB": quick.avg_ER_sum_dB,
        "avg_separation_efficiency": quick.avg_efficiency,
        "min_ER_sum_dB": quick.min_ER_sum_dB,
        "min_separation_efficiency": quick.min_efficiency,
        "geometry_gap_to_target": quick.geometry_gap,
        "k_region_start": region.k_start,
        "k_region_end": region.k_end,
        "region_point_count": region.point_count,
    }
    (solution_dir / "solution_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_markdown_reports(
    output_dir: Path,
    config: ProblemConfig,
    ranked_regions: list[RegionRepresentative],
    candidate_solutions: list[QuickSolution],
) -> tuple[Path, Path]:
    ensure_dir(output_dir)
    best = ranked_regions[0]
    best_solution = best.best_solution
    near_optimal_count = len(candidate_solutions)
    non_max_count = sum(1 for solution in candidate_solutions if not solution.is_max_subset_for_k)

    best_path = output_dir / "best_solution_summary.md"
    explanation_path = output_dir / "result_readme.md"

    best_lines = [
        "# Best Solution Summary",
        "",
        f"- Case: `{config.output.case_name}`",
        f"- Best region: `{best.region_id}`",
        f"- Representative k: `{best_solution.k:.9f}`",
        f"- Representative L/R: `{best_solution.L_over_R:.9f}`",
        f"- Candidate set size: `{len(config.candidate_modes)}`",
        f"- Candidate modes: `{config.candidate_modes}`",
        f"- Best coexistence subset size: `{best_solution.subset_size}`",
        f"- Best coexistence subset: `{best_solution.subset_signature}`",
        f"- s_min: `{best_solution.s_min:.9f}`",
        f"- F_min: `{best_solution.F_min:.6f}`",
        f"- F_eval used: `{best_solution.F_eval_used:.6f}`",
        f"- Average ER_sum: `{best_solution.avg_ER_sum_dB:.6f} dB`",
        f"- Minimum ER_sum: `{best_solution.min_ER_sum_dB:.6f} dB`",
        f"- Average separation efficiency: `{100.0 * best_solution.avg_efficiency:.4f}%`",
        f"- Minimum separation efficiency: `{100.0 * best_solution.min_efficiency:.4f}%`",
        "",
        "Why this one ranks first:",
        "",
        "- It has the highest-ranked subset size under the configured feasibility budget.",
        "- Within that cardinality, it offers the largest s_min / lowest F_min according to the configured sort priorities.",
        "- It also respects the configured geometry preference through the L/R distance term in the ranking.",
    ]
    best_path.write_text("\n".join(best_lines) + "\n", encoding="utf-8")

    readme_lines = [
        "# Generalized FP Screening Workspace",
        "",
        "## What the program does",
        "- Searches the configured k interval for non-continuous candidate total-order sets.",
        "- Builds a conflict graph under the configured task threshold tau_0 and feasibility finesse budget.",
        "- Solves the maximum coexistence subset with a branch-and-bound maximum-clique search on the coexistence graph.",
        "- Adds a near-optimal candidate layer that keeps feasible subsets above a configurable size threshold around the k-local maximum subset size.",
        "- Separates geometry screening (`s_min`, `F_min`) from physical evaluation (`F_eval`, exact periodic Airy response).",
        "- Exports ranked solutions, region summaries, per-solution structured data, and paper-ready plots.",
        "",
        "## Main inputs",
        f"- candidate_modes = {config.candidate_modes}",
        f"- tau_0 = {config.evaluation.tau_0}",
        f"- feasibility_finesse = {config.evaluation.feasibility_finesse}",
        f"- F_eval = {config.evaluation.F_eval}",
        f"- k search = [{config.search.k_min}, {config.search.k_max}] with {config.search.coarse_samples} coarse samples",
        f"- near_optimal_size_drop = {config.output.near_optimal_size_drop}",
        f"- near_optimal_min_subset_size = {config.output.near_optimal_min_subset_size}",
        f"- max_near_optimal_subsets_per_k = {config.output.max_near_optimal_subsets_per_k}",
        "",
        "## How to read the outputs",
        "- `main_ranked_solutions.csv` is the main table for thesis writing; `all_ranked_solutions.csv` is kept as a compatibility alias.",
        "- `near_optimal_ranked_candidates.csv` is the trade-off table for appendix / supplementary analysis.",
        "- `subset_regions.csv` groups the same best subset over contiguous k regions and keeps one representative working point per region.",
        "- `search_landscape.csv` is the full screening trace for reproducibility and appendix use.",
        "- Each `solution_rankXX_*` folder contains the structured data and figures for one representative solution.",
        "",
        "## Main-result layer vs near-optimal layer",
        "- Main-result layer: one representative maximum-coexistence subset per contiguous k region; best suited to Section 5.4 main-text presentation.",
        f"- Near-optimal layer: {near_optimal_count} exported feasible candidate subsets, including {non_max_count} non-maximum alternatives; best suited to appendix / trade-off analysis.",
        "- Near-optimal threshold: subset_size >= min(max_subset_size, max(near_optimal_min_subset_size, max_subset_size - near_optimal_size_drop)).",
        "- Near-optimal rows mark whether a subset is maximal for that k and how far its subset size falls below the k-local maximum.",
        "",
        "## Figures most suitable for the main text",
        "- The best-solution circle plot of mode positions on the normalized FP ring.",
        "- The search landscape plot showing subset size / s_min / F_min versus k.",
        "- The best-solution conditional-probability heatmap.",
        "- The per-mode ER_sum / separation-efficiency bar plot.",
        "",
        "## Better suited to appendix / supplementary material",
        "- Near-optimal ranked candidate tables.",
        "- All subset-region summaries.",
        "- Pairwise distance tables and raw response matrices for each representative solution.",
    ]
    explanation_path.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")
    return best_path, explanation_path
