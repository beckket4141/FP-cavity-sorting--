from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from .config import ProblemConfig


EPS = 1e-12


@dataclass
class QuickSolution:
    subset_modes: tuple[int, ...]
    subset_signature: str
    subset_size: int
    k: float
    L_over_R: float
    geometry_gap: float
    s_min: float
    F_min: float
    F_eval_used: float
    avg_ER_sum_dB: float
    avg_efficiency: float
    min_ER_sum_dB: float
    min_efficiency: float
    sorting_score: tuple[float, ...]
    pos_all: dict[int, float]
    feasible_under_budget: bool
    tau_min_at_budget: float | None
    is_max_subset_for_k: bool
    max_subset_size_for_k: int
    subset_size_gap_to_k_max: int


@dataclass
class RegionRepresentative:
    region_id: str
    subset_signature: str
    subset_modes: tuple[int, ...]
    k_start: float
    k_end: float
    point_count: int
    best_solution: QuickSolution


@dataclass
class DetailedSolution:
    quick: QuickSolution
    pairwise_distance_matrix: np.ndarray
    raw_response_matrix: np.ndarray
    condition_matrix: np.ndarray
    per_mode_records: list[dict[str, Any]]
    pairwise_rows: list[dict[str, Any]]


def compute_positions(modes: list[int], k: float) -> dict[int, float]:
    return {mode: float((mode * k) % 1.0) for mode in modes}


def circular_distance(a: float, b: float) -> float:
    delta = abs(a - b)
    return min(delta, 1.0 - delta)


def circular_distance_matrix(modes: list[int], positions: dict[int, float]) -> np.ndarray:
    n = len(modes)
    matrix = np.zeros((n, n), dtype=float)
    for i, mode_i in enumerate(modes):
        for j, mode_j in enumerate(modes):
            if i == j:
                continue
            matrix[i, j] = circular_distance(positions[mode_i], positions[mode_j])
    return matrix


def resolve_F_eval(config: ProblemConfig, F_min: float) -> float:
    mode = config.evaluation.F_eval
    if isinstance(mode, float):
        return mode
    if mode == "use_F_min":
        return F_min
    if mode == "use_feasibility":
        if config.evaluation.feasibility_finesse is None:
            return F_min
        return config.evaluation.feasibility_finesse
    raise ValueError(f"Unsupported F_eval mode: {mode}")


def airy_response(distance: np.ndarray, finesse: float) -> np.ndarray:
    return 1.0 / (1.0 + ((2.0 * finesse / math.pi) ** 2) * np.sin(math.pi * distance) ** 2)


def build_conflict_adjacency(distance_matrix: np.ndarray, tau_0: float, feasibility_finesse: float | None) -> list[int]:
    n = distance_matrix.shape[0]
    adjacency = [0] * n
    if feasibility_finesse is None:
        for i in range(n):
            for j in range(i + 1, n):
                if distance_matrix[i, j] <= EPS:
                    adjacency[i] |= 1 << j
                    adjacency[j] |= 1 << i
        return adjacency

    threshold = tau_0 / feasibility_finesse
    for i in range(n):
        for j in range(i + 1, n):
            if distance_matrix[i, j] + EPS < threshold:
                adjacency[i] |= 1 << j
                adjacency[j] |= 1 << i
    return adjacency


def complement_adjacency(conflict_adjacency: list[int], n: int) -> list[int]:
    all_mask = (1 << n) - 1
    return [all_mask & ~(1 << i) & ~conflict_adjacency[i] for i in range(n)]


def _iter_bits(mask: int) -> list[int]:
    items: list[int] = []
    while mask:
        lsb = mask & -mask
        items.append(lsb.bit_length() - 1)
        mask ^= lsb
    return items


def enumerate_max_cliques(coexist_adjacency: list[int], max_output: int) -> list[tuple[int, ...]]:
    best_size = 0
    best_sets: list[tuple[int, ...]] = []

    def bronk(r_mask: int, p_mask: int, x_mask: int) -> None:
        nonlocal best_size, best_sets
        if p_mask == 0 and x_mask == 0:
            size = r_mask.bit_count()
            if size < best_size:
                return
            clique = tuple(_iter_bits(r_mask))
            if size > best_size:
                best_size = size
                best_sets = [clique]
            elif clique not in best_sets:
                best_sets.append(clique)
                best_sets.sort()
                if len(best_sets) > max_output:
                    best_sets = best_sets[:max_output]
            return

        if r_mask.bit_count() + p_mask.bit_count() < best_size:
            return

        union_mask = p_mask | x_mask
        if union_mask:
            pivot = max(_iter_bits(union_mask), key=lambda idx: (p_mask & coexist_adjacency[idx]).bit_count())
            candidates = p_mask & ~coexist_adjacency[pivot]
        else:
            candidates = p_mask

        while candidates:
            v_bit = candidates & -candidates
            v = v_bit.bit_length() - 1
            bronk(r_mask | v_bit, p_mask & coexist_adjacency[v], x_mask & coexist_adjacency[v])
            p_mask ^= v_bit
            x_mask |= v_bit
            candidates ^= v_bit

    bronk(0, (1 << len(coexist_adjacency)) - 1, 0)
    return best_sets


def enumerate_cliques_with_min_size(
    coexist_adjacency: list[int],
    min_size: int,
    max_output: int | None = None,
) -> list[tuple[int, ...]]:
    results: list[tuple[int, ...]] = []
    seen: set[tuple[int, ...]] = set()
    n = len(coexist_adjacency)

    def dfs(current: tuple[int, ...], candidates_mask: int) -> None:
        if max_output is not None and len(results) >= max_output:
            return
        current_size = len(current)
        if current_size >= min_size and current not in seen:
            seen.add(current)
            results.append(current)
            if max_output is not None and len(results) >= max_output:
                return
        if current_size + candidates_mask.bit_count() < min_size:
            return

        remaining = candidates_mask
        while remaining:
            if max_output is not None and len(results) >= max_output:
                return
            v_bit = remaining & -remaining
            remaining ^= v_bit
            v = v_bit.bit_length() - 1
            next_candidates = remaining & coexist_adjacency[v]
            dfs(current + (v,), next_candidates)

    dfs(tuple(), (1 << n) - 1)
    return results


def _subset_pair_rows(subset_modes: tuple[int, ...], subset_positions: dict[int, float], distance_matrix: np.ndarray) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, mode_i in enumerate(subset_modes):
        for j in range(i + 1, len(subset_modes)):
            mode_j = subset_modes[j]
            rows.append(
                {
                    "mode_i": mode_i,
                    "mode_j": mode_j,
                    "pos_i": subset_positions[mode_i],
                    "pos_j": subset_positions[mode_j],
                    "s_ij": distance_matrix[i, j],
                }
            )
    return rows


def _score_tuple(solution_like: dict[str, Any], priorities: list[dict[str, str]]) -> tuple[float, ...]:
    values: list[float] = []
    for item in priorities:
        key = item["key"]
        direction = item["direction"]
        value = float(solution_like[key])
        values.append(value if direction == "desc" else -value)
    return tuple(values)


def _geometry_gap(config: ProblemConfig, L_over_R: float) -> float:
    target = config.geometry_preference.target_L_over_R
    if target is None:
        return 0.0
    return abs(L_over_R - target)


def _passes_hard_geometry(config: ProblemConfig, L_over_R: float) -> bool:
    target = config.geometry_preference.target_L_over_R
    tol = config.geometry_preference.hard_tolerance
    if target is None or tol is None:
        return True
    return abs(L_over_R - target) <= tol + EPS


def evaluate_subset(
    subset_modes: tuple[int, ...],
    positions_all: dict[int, float],
    config: ProblemConfig,
    k: float,
    L_over_R: float,
    feasible_under_budget: bool,
    tau_min_at_budget: float | None,
    is_max_subset_for_k: bool,
    max_subset_size_for_k: int,
) -> QuickSolution:
    subset_positions = {mode: positions_all[mode] for mode in subset_modes}
    subset_distance_matrix = circular_distance_matrix(list(subset_modes), subset_positions)
    positive_distances = subset_distance_matrix[np.triu_indices(len(subset_modes), k=1)]
    s_min = float(np.min(positive_distances)) if positive_distances.size else 0.5
    F_min = config.evaluation.tau_0 / s_min if s_min > EPS else float("inf")
    F_eval_used = resolve_F_eval(config, F_min)

    raw_response = airy_response(subset_distance_matrix, F_eval_used)
    np.fill_diagonal(raw_response, 1.0)
    col_sums = raw_response.sum(axis=0)
    condition = raw_response / col_sums[np.newaxis, :]

    leakage = col_sums - 1.0
    with np.errstate(divide="ignore", invalid="ignore"):
        er_sum_db = 10.0 * np.log10(1.0 / leakage)
    efficiency = 1.0 / col_sums

    score_input = {
        "subset_size": len(subset_modes),
        "s_min": s_min,
        "F_min": F_min,
        "geometry_gap": _geometry_gap(config, L_over_R),
        "k": k,
    }
    return QuickSolution(
        subset_modes=subset_modes,
        subset_signature="[" + ",".join(str(mode) for mode in subset_modes) + "]",
        subset_size=len(subset_modes),
        k=k,
        L_over_R=L_over_R,
        geometry_gap=score_input["geometry_gap"],
        s_min=s_min,
        F_min=F_min,
        F_eval_used=F_eval_used,
        avg_ER_sum_dB=float(np.nanmean(er_sum_db)),
        avg_efficiency=float(np.mean(efficiency)),
        min_ER_sum_dB=float(np.nanmin(er_sum_db)),
        min_efficiency=float(np.min(efficiency)),
        sorting_score=_score_tuple(score_input, config.sort_priorities),
        pos_all=positions_all,
        feasible_under_budget=feasible_under_budget,
        tau_min_at_budget=tau_min_at_budget,
        is_max_subset_for_k=is_max_subset_for_k,
        max_subset_size_for_k=max_subset_size_for_k,
        subset_size_gap_to_k_max=max_subset_size_for_k - len(subset_modes),
    )


def evaluate_k(config: ProblemConfig, k: float) -> tuple[list[QuickSolution], list[QuickSolution], dict[str, Any]]:
    modes = config.candidate_modes
    positions = compute_positions(modes, k)
    distance_matrix = circular_distance_matrix(modes, positions)
    adjacency = build_conflict_adjacency(distance_matrix=distance_matrix, tau_0=config.evaluation.tau_0, feasibility_finesse=config.evaluation.feasibility_finesse)
    coexist_adjacency = complement_adjacency(adjacency, len(modes))
    best_subsets_idx = enumerate_max_cliques(coexist_adjacency, max_output=config.output.max_subsets_per_k)
    L_over_R = math.sin(math.pi * k) ** 2
    if not _passes_hard_geometry(config, L_over_R):
        return [], [], {"k": k, "L_over_R": L_over_R, "best_subset_size": 0, "best_s_min": float("nan"), "best_F_min": float("nan"), "feasible_solution_count": 0, "near_optimal_solution_count": 0}

    max_subset_size = max((len(subset_idx) for subset_idx in best_subsets_idx), default=0)
    min_candidate_subset_size = (
        min(
            max_subset_size,
            max(config.output.near_optimal_min_subset_size, max_subset_size - config.output.near_optimal_size_drop),
        )
        if max_subset_size
        else 0
    )
    candidate_subsets_idx = enumerate_cliques_with_min_size(
        coexist_adjacency,
        min_size=min_candidate_subset_size,
        max_output=None,
    ) if min_candidate_subset_size > 0 else []

    main_signatures = {tuple(subset_idx) for subset_idx in best_subsets_idx}
    candidate_idx_sets: list[tuple[int, ...]] = []
    seen_candidate_signatures: set[tuple[int, ...]] = set()
    for subset_idx in list(best_subsets_idx) + candidate_subsets_idx:
        if subset_idx in seen_candidate_signatures:
            continue
        seen_candidate_signatures.add(subset_idx)
        candidate_idx_sets.append(subset_idx)

    main_solutions: list[QuickSolution] = []
    candidate_solutions: list[QuickSolution] = []
    for subset_idx in candidate_idx_sets:
        subset_modes = tuple(modes[idx] for idx in subset_idx)
        subset_distance = distance_matrix[np.ix_(subset_idx, subset_idx)]
        upper = subset_distance[np.triu_indices(len(subset_idx), k=1)]
        s_min = float(np.min(upper)) if upper.size else 0.5
        tau_min_at_budget = None
        feasible = True
        if config.evaluation.feasibility_finesse is not None:
            tau_min_at_budget = config.evaluation.feasibility_finesse * s_min
            feasible = tau_min_at_budget + EPS >= config.evaluation.tau_0
        solution = evaluate_subset(
            subset_modes,
            positions,
            config,
            k,
            L_over_R,
            feasible,
            tau_min_at_budget,
            is_max_subset_for_k=subset_idx in main_signatures,
            max_subset_size_for_k=max_subset_size,
        )
        candidate_solutions.append(solution)
        if subset_idx in main_signatures:
            main_solutions.append(solution)

    main_solutions.sort(key=lambda item: item.sorting_score, reverse=True)
    candidate_solutions.sort(key=lambda item: item.sorting_score, reverse=True)
    if len(candidate_solutions) > config.output.max_near_optimal_subsets_per_k:
        candidate_solutions = candidate_solutions[: config.output.max_near_optimal_subsets_per_k]
    best = main_solutions[0] if main_solutions else None
    return main_solutions, candidate_solutions, {
        "k": k,
        "L_over_R": L_over_R,
        "best_subset_size": best.subset_size if best else 0,
        "best_s_min": best.s_min if best else float("nan"),
        "best_F_min": best.F_min if best else float("nan"),
        "best_subset_signature": best.subset_signature if best else "",
        "best_avg_ER_sum_dB": best.avg_ER_sum_dB if best else float("nan"),
        "best_avg_efficiency": best.avg_efficiency if best else float("nan"),
        "feasible_solution_count": len(main_solutions),
        "near_optimal_solution_count": len(candidate_solutions),
    }


def select_refine_seeds(all_solutions: list[QuickSolution], seed_count: int, min_spacing: float) -> list[QuickSolution]:
    ordered = sorted(all_solutions, key=lambda item: item.sorting_score, reverse=True)
    seeds: list[QuickSolution] = []
    for solution in ordered:
        if any(abs(solution.k - existing.k) < min_spacing for existing in seeds):
            continue
        seeds.append(solution)
        if len(seeds) >= seed_count:
            break
    return seeds


def extract_region_representatives(solutions: list[QuickSolution], coarse_step: float, config: ProblemConfig) -> list[RegionRepresentative]:
    grouped: dict[str, list[QuickSolution]] = {}
    for solution in solutions:
        grouped.setdefault(solution.subset_signature, []).append(solution)

    regions: list[RegionRepresentative] = []
    region_counter = 1
    max_gap = coarse_step * 1.6
    for subset_signature, group in sorted(grouped.items()):
        group_sorted = sorted(group, key=lambda item: item.k)
        current: list[QuickSolution] = []
        for solution in group_sorted:
            if not current:
                current.append(solution)
                continue
            if solution.k - current[-1].k <= max_gap:
                current.append(solution)
            else:
                best = max(current, key=lambda item: item.sorting_score)
                regions.append(RegionRepresentative(f"R{region_counter:03d}", subset_signature, best.subset_modes, current[0].k, current[-1].k, len(current), best))
                region_counter += 1
                current = [solution]
        if current:
            best = max(current, key=lambda item: item.sorting_score)
            regions.append(RegionRepresentative(f"R{region_counter:03d}", subset_signature, best.subset_modes, current[0].k, current[-1].k, len(current), best))
            region_counter += 1

    regions.sort(key=lambda item: item.best_solution.sorting_score, reverse=True)
    return regions


def build_detailed_solution(config: ProblemConfig, quick: QuickSolution) -> DetailedSolution:
    subset_positions = {mode: quick.pos_all[mode] for mode in quick.subset_modes}
    pairwise_distance_matrix = circular_distance_matrix(list(quick.subset_modes), subset_positions)
    raw_response = airy_response(pairwise_distance_matrix, quick.F_eval_used)
    np.fill_diagonal(raw_response, 1.0)
    condition_matrix = raw_response / raw_response.sum(axis=0)[np.newaxis, :]
    pairwise_rows = _subset_pair_rows(quick.subset_modes, subset_positions, pairwise_distance_matrix)

    per_mode_records: list[dict[str, Any]] = []
    for col_idx, mode in enumerate(quick.subset_modes):
        raw_column = raw_response[:, col_idx]
        cond_column = condition_matrix[:, col_idx]
        leakage_sum = float(np.sum(raw_column) - 1.0)
        efficiency = float(cond_column[col_idx])
        er_sum = 10.0 * math.log10(1.0 / leakage_sum) if leakage_sum > 0 else float("inf")
        per_mode_records.append({"mode": mode, "pos": subset_positions[mode], "background_leakage_raw_sum": leakage_sum, "ER_sum_dB": er_sum, "separation_efficiency": efficiency})

    return DetailedSolution(quick, pairwise_distance_matrix, raw_response, condition_matrix, per_mode_records, pairwise_rows)


def quick_solution_to_row(rank: int, region_id: str, region: RegionRepresentative | None, solution: QuickSolution) -> dict[str, Any]:
    row = {
        "rank": rank,
        "region_id": region_id,
        "k": solution.k,
        "L_over_R": solution.L_over_R,
        "candidate_set_size": len(solution.pos_all),
        "max_subset_size": solution.subset_size,
        "subset_modes": solution.subset_signature,
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
    if region is not None:
        row.update({"k_region_start": region.k_start, "k_region_end": region.k_end, "region_point_count": region.point_count})
    return row
