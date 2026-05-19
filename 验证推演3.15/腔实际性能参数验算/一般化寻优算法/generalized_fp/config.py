from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_SORT_PRIORITIES = [
    {"key": "subset_size", "direction": "desc"},
    {"key": "s_min", "direction": "desc"},
    {"key": "F_min", "direction": "asc"},
    {"key": "geometry_gap", "direction": "asc"},
    {"key": "k", "direction": "asc"},
]


@dataclass
class SearchConfig:
    k_min: float
    k_max: float
    coarse_samples: int
    refine_enabled: bool = True
    refine_seed_count: int = 24
    refine_half_window: float = 0.002
    refine_samples: int = 121
    min_seed_spacing: float = 0.002


@dataclass
class GeometryPreference:
    target_L_over_R: float | None = None
    hard_tolerance: float | None = None


@dataclass
class EvaluationConfig:
    tau_0: float
    feasibility_finesse: float | None = None
    F_eval: float | str = "use_feasibility"
    airy_model: str = "exact_periodic"


@dataclass
class OutputConfig:
    case_name: str
    top_solution_details: int = 8
    max_subsets_per_k: int = 6
    near_optimal_size_drop: int = 1
    near_optimal_min_subset_size: int = 5
    max_near_optimal_subsets_per_k: int = 80
    export_excel: bool = True


@dataclass
class ProblemConfig:
    candidate_modes: list[int]
    search: SearchConfig
    geometry_preference: GeometryPreference
    evaluation: EvaluationConfig
    output: OutputConfig
    sort_priorities: list[dict[str, str]] = field(default_factory=lambda: list(DEFAULT_SORT_PRIORITIES))
    notes: str = ""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _coerce_float_or_mode(value: Any, field_name: str) -> float | str | None:
    if value is None:
        return None
    if isinstance(value, str):
        mode = value.strip()
        if mode not in {"use_F_min", "use_feasibility"}:
            raise ValueError(f"{field_name} must be a number, null, 'use_F_min', or 'use_feasibility'.")
        return mode
    return float(value)


def _coerce_candidate_modes(values: Any) -> list[int]:
    _require(isinstance(values, list), "candidate_modes must be a JSON list of positive integers.")
    modes: list[int] = []
    for idx, value in enumerate(values):
        if isinstance(value, bool):
            raise ValueError(f"candidate_modes[{idx}] must be a positive integer, not bool.")
        if isinstance(value, int):
            mode = value
        elif isinstance(value, float) and value.is_integer():
            mode = int(value)
        else:
            raise ValueError(f"candidate_modes[{idx}] must be an integer literal >= 1.")
        _require(mode >= 1, f"candidate_modes[{idx}] must be >= 1; got {mode}.")
        modes.append(mode)
    return modes


def load_config(path: Path) -> ProblemConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    candidate_modes = _coerce_candidate_modes(raw["candidate_modes"])
    _require(candidate_modes, "candidate_modes cannot be empty.")
    _require(len(set(candidate_modes)) == len(candidate_modes), "candidate_modes must be unique.")
    candidate_modes = sorted(candidate_modes)

    search_raw = raw["search"]
    search = SearchConfig(
        k_min=float(search_raw["k_min"]),
        k_max=float(search_raw["k_max"]),
        coarse_samples=int(search_raw["coarse_samples"]),
        refine_enabled=bool(search_raw.get("refine_enabled", True)),
        refine_seed_count=int(search_raw.get("refine_seed_count", 24)),
        refine_half_window=float(search_raw.get("refine_half_window", 0.002)),
        refine_samples=int(search_raw.get("refine_samples", 121)),
        min_seed_spacing=float(search_raw.get("min_seed_spacing", 0.002)),
    )
    _require(0.0 < search.k_min < 0.5, "search.k_min must be in (0, 0.5).")
    _require(0.0 < search.k_max < 0.5, "search.k_max must be in (0, 0.5).")
    _require(search.k_min < search.k_max, "search.k_min must be less than search.k_max.")
    _require(search.coarse_samples >= 5, "search.coarse_samples must be >= 5.")

    geom_raw = raw.get("geometry_preference", {})
    geometry_preference = GeometryPreference(
        target_L_over_R=None if geom_raw.get("target_L_over_R") is None else float(geom_raw["target_L_over_R"]),
        hard_tolerance=None if geom_raw.get("hard_tolerance") is None else float(geom_raw["hard_tolerance"]),
    )

    eval_raw = raw["evaluation"]
    evaluation = EvaluationConfig(
        tau_0=float(eval_raw["tau_0"]),
        feasibility_finesse=None if eval_raw.get("feasibility_finesse") is None else float(eval_raw["feasibility_finesse"]),
        F_eval=_coerce_float_or_mode(eval_raw.get("F_eval", "use_feasibility"), "evaluation.F_eval"),
        airy_model=str(eval_raw.get("airy_model", "exact_periodic")),
    )
    _require(evaluation.tau_0 > 0, "evaluation.tau_0 must be positive.")
    if evaluation.feasibility_finesse is not None:
        _require(evaluation.feasibility_finesse > 0, "evaluation.feasibility_finesse must be positive.")
    if isinstance(evaluation.F_eval, float):
        _require(evaluation.F_eval > 0, "evaluation.F_eval must be positive when numeric.")

    output_raw = raw["output"]
    output = OutputConfig(
        case_name=str(output_raw["case_name"]),
        top_solution_details=int(output_raw.get("top_solution_details", 8)),
        max_subsets_per_k=int(output_raw.get("max_subsets_per_k", 6)),
        near_optimal_size_drop=int(output_raw.get("near_optimal_size_drop", 1)),
        near_optimal_min_subset_size=int(output_raw.get("near_optimal_min_subset_size", 5)),
        max_near_optimal_subsets_per_k=int(output_raw.get("max_near_optimal_subsets_per_k", 80)),
        export_excel=bool(output_raw.get("export_excel", True)),
    )
    _require(output.case_name.strip() != "", "output.case_name cannot be empty.")
    _require(output.top_solution_details >= 1, "output.top_solution_details must be >= 1.")
    _require(output.max_subsets_per_k >= 1, "output.max_subsets_per_k must be >= 1.")
    _require(output.near_optimal_size_drop >= 0, "output.near_optimal_size_drop must be >= 0.")
    _require(output.near_optimal_min_subset_size >= 1, "output.near_optimal_min_subset_size must be >= 1.")
    _require(output.max_near_optimal_subsets_per_k >= 1, "output.max_near_optimal_subsets_per_k must be >= 1.")

    priorities = raw.get("sort_priorities", DEFAULT_SORT_PRIORITIES)
    normalized_priorities: list[dict[str, str]] = []
    for item in priorities:
        key = str(item["key"])
        direction = str(item["direction"]).lower()
        _require(direction in {"asc", "desc"}, f"Invalid sort direction for {key}: {direction}")
        normalized_priorities.append({"key": key, "direction": direction})

    return ProblemConfig(
        candidate_modes=candidate_modes,
        search=search,
        geometry_preference=geometry_preference,
        evaluation=evaluation,
        output=output,
        sort_priorities=normalized_priorities,
        notes=str(raw.get("notes", "")),
    )
