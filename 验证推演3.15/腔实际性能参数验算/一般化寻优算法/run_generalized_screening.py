from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

from generalized_fp.config import load_config
from generalized_fp.core import build_detailed_solution, evaluate_k, extract_region_representatives, quick_solution_to_row, select_refine_seeds
from generalized_fp.exporting import ensure_dir, export_detailed_solution, export_markdown_reports, export_summary_tables
from generalized_fp.plotting import plot_condition_matrix, plot_conflict_graph, plot_mode_metrics, plot_search_landscape, plot_solution_circle


def linspace(start: float, stop: float, samples: int) -> list[float]:
    if samples == 1:
        return [start]
    step = (stop - start) / (samples - 1)
    return [start + idx * step for idx in range(samples)]


def deduplicate_solutions(solutions):
    dedup = {}
    for solution in solutions:
        key = (solution.subset_signature, int(round(solution.k * 1e9)))
        existing = dedup.get(key)
        if existing is None or solution.sorting_score > existing.sorting_score:
            dedup[key] = solution
    return list(dedup.values())


def run_search(config_path: Path) -> None:
    config = load_config(config_path)
    base_dir = Path(__file__).resolve().parent
    case_dir = base_dir / "outputs" / config.output.case_name
    if case_dir.exists():
        shutil.rmtree(case_dir)
    ensure_dir(case_dir)
    all_quick_solutions = []
    all_candidate_solutions = []
    landscape_rows = []
    coarse_grid = linspace(config.search.k_min, config.search.k_max, config.search.coarse_samples)
    coarse_step = (config.search.k_max - config.search.k_min) / (config.search.coarse_samples - 1)

    for k in coarse_grid:
        solutions, candidate_solutions, landscape = evaluate_k(config, k)
        all_quick_solutions.extend(solutions)
        all_candidate_solutions.extend(candidate_solutions)
        landscape_rows.append(landscape)

    if config.search.refine_enabled and all_quick_solutions:
        seeds = select_refine_seeds(all_quick_solutions, config.search.refine_seed_count, config.search.min_seed_spacing)
        for seed in seeds:
            k_lo = max(config.search.k_min, seed.k - config.search.refine_half_window)
            k_hi = min(config.search.k_max, seed.k + config.search.refine_half_window)
            for k in linspace(k_lo, k_hi, config.search.refine_samples):
                solutions, candidate_solutions, landscape = evaluate_k(config, k)
                all_quick_solutions.extend(solutions)
                all_candidate_solutions.extend(candidate_solutions)
                landscape_rows.append(landscape)

    if not all_quick_solutions:
        raise RuntimeError("No feasible solutions survived the configured geometry constraints.")

    unique_solutions = deduplicate_solutions(all_quick_solutions)
    unique_candidate_solutions = deduplicate_solutions(all_candidate_solutions)

    landscape_df = pd.DataFrame(landscape_rows).drop_duplicates(subset=["k"], keep="last").sort_values("k").reset_index(drop=True)
    ranked_regions = extract_region_representatives(unique_solutions, coarse_step=coarse_step, config=config)
    region_df = pd.DataFrame([quick_solution_to_row(rank, region.region_id, region, region.best_solution) for rank, region in enumerate(ranked_regions, start=1)])
    candidate_rows = []
    sorted_candidate_solutions = sorted(unique_candidate_solutions, key=lambda item: (item.k, item.sorting_score), reverse=False)
    global_sorted_candidates = sorted(unique_candidate_solutions, key=lambda item: item.sorting_score, reverse=True)
    global_rank_map = {(solution.subset_signature, int(round(solution.k * 1e9))): rank for rank, solution in enumerate(global_sorted_candidates, start=1)}
    grouped_by_k = {}
    for solution in sorted_candidate_solutions:
        grouped_by_k.setdefault(int(round(solution.k * 1e9)), []).append(solution)
    for k_key in sorted(grouped_by_k):
        group = sorted(grouped_by_k[k_key], key=lambda item: item.sorting_score, reverse=True)
        for k_rank, solution in enumerate(group, start=1):
            key = (solution.subset_signature, int(round(solution.k * 1e9)))
            candidate_rows.append(
                {
                    "global_rank": global_rank_map[key],
                    "k_rank": k_rank,
                    "k": solution.k,
                    "L_over_R": solution.L_over_R,
                    "subset_modes": solution.subset_signature,
                    "subset_size": solution.subset_size,
                    "s_min": solution.s_min,
                    "F_min": solution.F_min,
                    "F_eval_used": solution.F_eval_used,
                    "avg_ER_sum_dB": solution.avg_ER_sum_dB,
                    "min_ER_sum_dB": solution.min_ER_sum_dB,
                    "avg_separation_efficiency": solution.avg_efficiency,
                    "min_separation_efficiency": solution.min_efficiency,
                    "geometry_gap_to_target": solution.geometry_gap,
                    "feasible_under_budget": solution.feasible_under_budget,
                    "tau_min_at_budget": solution.tau_min_at_budget,
                    "is_max_subset_for_k": solution.is_max_subset_for_k,
                    "max_subset_size_for_k": solution.max_subset_size_for_k,
                    "subset_size_gap_to_k_max": solution.subset_size_gap_to_k_max,
                }
            )
    candidate_df = pd.DataFrame(candidate_rows).sort_values(["k", "k_rank", "global_rank"]).reset_index(drop=True)

    figures_dir = case_dir / "figures"
    details_root = case_dir / "solutions"
    ensure_dir(figures_dir)
    ensure_dir(details_root)
    export_summary_tables(case_dir, config, ranked_regions, landscape_df, region_df, candidate_df)
    export_markdown_reports(case_dir, config, ranked_regions, unique_candidate_solutions)
    plot_search_landscape(landscape_df, figures_dir / "search_landscape.png")

    for rank, region in enumerate(ranked_regions[: config.output.top_solution_details], start=1):
        detail = build_detailed_solution(config, region.best_solution)
        solution_dir = details_root / f"solution_rank{rank:02d}_{region.region_id}"
        export_detailed_solution(solution_dir, detail, rank=rank, region=region)
        plot_solution_circle(detail, solution_dir / "positions_circle.png")
        plot_conflict_graph(detail, solution_dir / "conflict_graph.png", config.evaluation.tau_0, config.evaluation.feasibility_finesse)
        plot_condition_matrix(detail, solution_dir / "condition_probability_heatmap.png")
        plot_mode_metrics(detail, solution_dir / "per_mode_metrics.png")

    best = ranked_regions[0].best_solution
    print("Completed generalized FP screening.")
    print(f"Config : {config_path.resolve()}")
    print(f"Output : {case_dir.resolve()}")
    print(f"Best region: {ranked_regions[0].region_id}")
    print(f"Best subset: {best.subset_signature}")
    print(f"Best k: {best.k:.9f}")
    print(f"Best L/R: {best.L_over_R:.9f}")
    print(f"Best F_min: {best.F_min:.6f}")
    print(f"Best avg ER_sum (dB): {best.avg_ER_sum_dB:.6f}")
    print(f"Best avg efficiency: {100.0 * best.avg_efficiency:.4f}%")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generalized non-continuous FP mode-set screening and performance evaluation.")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parent / "configs" / "default_irregular_case.json", help="Path to the JSON config file.")
    args = parser.parse_args()
    run_search(args.config)


if __name__ == "__main__":
    main()
