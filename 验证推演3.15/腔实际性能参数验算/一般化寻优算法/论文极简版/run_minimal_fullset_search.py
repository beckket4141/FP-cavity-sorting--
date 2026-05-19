from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


@dataclass(frozen=True)
class SearchConfig:
    k_min: float
    k_max: float
    coarse_samples: int
    refine_half_window: float
    refine_samples: int
    local_optima_to_export: int
    export_stride: int = 10


@dataclass(frozen=True)
class GeometryConstraints:
    L_over_R_min: float | None
    L_over_R_max: float | None
    target_L_over_R: float | None = 0.5


@dataclass(frozen=True)
class ProblemConfig:
    scenario_name: str
    wavelength_nm: float
    refractive_index_note: str
    candidate_modes: tuple[int, ...]
    tau_targets: tuple[float, ...]
    search: SearchConfig
    geometry_constraints: GeometryConstraints
    notes: str


@dataclass(frozen=True)
class ScanRow:
    k: float
    L_over_R: float
    s_min: float
    limiting_pair: tuple[int, int]


def limiting_pairs_and_diffs(
    modes: tuple[int, ...],
    k: float,
    s_min: float,
    tolerance: float = 1e-12,
) -> tuple[tuple[tuple[int, int], ...], tuple[int, ...]]:
    pairs: list[tuple[int, int]] = []
    diffs: set[int] = set()
    for i, mode_i in enumerate(modes):
        for mode_j in modes[i + 1 :]:
            distance = circular_distance((mode_i * k) % 1.0, (mode_j * k) % 1.0)
            if abs(distance - s_min) <= tolerance:
                pairs.append((mode_i, mode_j))
                diffs.add(mode_j - mode_i)
    return tuple(pairs), tuple(sorted(diffs))


def load_config(path: Path) -> ProblemConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    search = SearchConfig(**raw["search"])
    geometry_constraints = GeometryConstraints(**raw["geometry_constraints"])
    return ProblemConfig(
        scenario_name=str(raw["scenario_name"]),
        wavelength_nm=float(raw["wavelength_nm"]),
        refractive_index_note=str(raw["refractive_index_note"]),
        candidate_modes=tuple(int(v) for v in raw["candidate_modes"]),
        tau_targets=tuple(float(v) for v in raw["tau_targets"]),
        search=search,
        geometry_constraints=geometry_constraints,
        notes=str(raw.get("notes", "")),
    )


def linspace(start: float, stop: float, samples: int) -> list[float]:
    if samples <= 1:
        return [start]
    step = (stop - start) / (samples - 1)
    return [start + i * step for i in range(samples)]


def k_to_L_over_R(k: float) -> float:
    return math.sin(math.pi * k) ** 2


def circular_distance(a: float, b: float) -> float:
    delta = abs(a - b)
    return min(delta, 1.0 - delta)


def evaluate_k(modes: tuple[int, ...], k: float) -> ScanRow:
    positions = {mode: (mode * k) % 1.0 for mode in modes}
    best_distance = 0.5
    best_pair = (modes[0], modes[0])
    for i, mode_i in enumerate(modes):
        for mode_j in modes[i + 1 :]:
            distance = circular_distance(positions[mode_i], positions[mode_j])
            if distance < best_distance:
                best_distance = distance
                best_pair = (mode_i, mode_j)
    return ScanRow(
        k=k,
        L_over_R=k_to_L_over_R(k),
        s_min=best_distance,
        limiting_pair=best_pair,
    )


def passes_geometry_constraints(row: ScanRow, constraints: GeometryConstraints) -> bool:
    if constraints.L_over_R_min is not None and row.L_over_R < constraints.L_over_R_min:
        return False
    if constraints.L_over_R_max is not None and row.L_over_R > constraints.L_over_R_max:
        return False
    return True


def geometry_gap(row: ScanRow, constraints: GeometryConstraints) -> float:
    if constraints.target_L_over_R is None:
        return 0.0
    return abs(row.L_over_R - constraints.target_L_over_R)


def rank_key(row: ScanRow, constraints: GeometryConstraints) -> tuple[float, float, float]:
    return (round(row.s_min, 12), -geometry_gap(row, constraints), -abs(row.k - 0.25))


def top_local_optima(rows: list[ScanRow], limit: int, constraints: GeometryConstraints) -> list[ScanRow]:
    if len(rows) < 3:
        return sorted(rows, key=lambda item: rank_key(item, constraints), reverse=True)[:limit]
    local_rows: list[ScanRow] = []
    for idx in range(1, len(rows) - 1):
        left = rows[idx - 1]
        mid = rows[idx]
        right = rows[idx + 1]
        if mid.s_min >= left.s_min and mid.s_min >= right.s_min:
            local_rows.append(mid)
    return sorted(local_rows, key=lambda item: rank_key(item, constraints), reverse=True)[:limit]


def refine_best(modes: tuple[int, ...], coarse_best: ScanRow, config: ProblemConfig) -> ScanRow:
    k_lo = max(config.search.k_min, coarse_best.k - config.search.refine_half_window)
    k_hi = min(config.search.k_max, coarse_best.k + config.search.refine_half_window)
    best = coarse_best
    for k in linspace(k_lo, k_hi, config.search.refine_samples):
        row = evaluate_k(modes, k)
        if not passes_geometry_constraints(row, config.geometry_constraints):
            continue
        if rank_key(row, config.geometry_constraints) > rank_key(best, config.geometry_constraints):
            best = row
    return best


def snap_best_to_clean_rational(best: ScanRow, modes: tuple[int, ...], config: ProblemConfig) -> ScanRow:
    candidate_best = best
    k_min = config.search.k_min
    k_max = config.search.k_max
    for denominator in range(1, 501):
        start = math.ceil(k_min * denominator)
        end = math.floor(k_max * denominator)
        for numerator in range(start, end + 1):
            frac = Fraction(numerator, denominator)
            k_value = float(frac)
            if not (k_min <= k_value <= k_max):
                continue
            candidate_row = evaluate_k(modes, k_value)
            if not passes_geometry_constraints(candidate_row, config.geometry_constraints):
                continue
            if rank_key(candidate_row, config.geometry_constraints) > rank_key(candidate_best, config.geometry_constraints):
                candidate_best = candidate_row
    return candidate_best


def rational_hint(value: float, max_denominator: int = 500) -> str:
    frac = Fraction(value).limit_denominator(max_denominator)
    if abs(float(frac) - value) < 1e-8:
        return f"{frac.numerator}/{frac.denominator}"
    return ""


def tau_lower_bound_metrics(tau: float) -> tuple[float, float]:
    x = math.pi / (2.0 * tau)
    coth_x = math.cosh(x) / math.sinh(x)
    p_noise = (math.pi / (2.0 * tau)) * coth_x - 1.0
    eta_sort = 1.0 / (1.0 + p_noise)
    er_sum_db = 10.0 * math.log10(1.0 / p_noise)
    return eta_sort, er_sum_db


def required_finesse(tau: float, s_min: float) -> float:
    if s_min <= 0.0:
        return float("inf")
    return tau / s_min


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(
    path: Path,
    config: ProblemConfig,
    best: ScanRow,
    tau_rows: list[dict[str, object]],
    local_rows: list[ScanRow],
) -> None:
    lines: list[str] = []
    lines.append("# 第五章 5.4 极简示例结果")
    lines.append("")
    lines.append(f"- 场景名：`{config.scenario_name}`")
    lines.append(f"- 波长元信息：`{config.wavelength_nm:.1f} nm`")
    lines.append(f"- 模式集合：`{list(config.candidate_modes)}`")
    lines.append("- 求解目标：让该 12 模随机集合整体同时可分辨，而不是再做子集筛选。")
    lines.append("")
    lines.append("## 全局最优工作点")
    lines.append("")
    lines.append(f"- 最优 `k*`：`{best.k:.15f}`")
    lines.append(f"- `k*` 的有理近似：`{rational_hint(best.k) or '无明显低阶分数'}`")
    lines.append(f"- 最优几何比 `(L/R)*`：`{best.L_over_R:.15f}`")
    lines.append(f"- 最大最小间距 `s_min^*`：`{best.s_min:.15f}`")
    limiting_pairs, limiting_diffs = limiting_pairs_and_diffs(config.candidate_modes, best.k, best.s_min)
    lines.append(f"- 限制性差分：`{list(limiting_diffs)}`")
    lines.append(f"- 并列限制模式对：`{list(limiting_pairs)}`")
    lines.append("")
    lines.append("## tau 结果")
    lines.append("")
    for row in tau_rows:
        lines.append(
            "- "
            f"`tau_0={row['tau_0']:.1f}` 时，"
            f"`F_min={row['F_min']:.6f}`，"
            f"无穷维保守下界成功率约为 `{100.0 * row['eta_sort_infty_lower_bound']:.4f}%`，"
            f"`ER_sum^(inf)` 约为 `{row['ER_sum_infty_lower_bound_dB']:.4f} dB`。"
        )
    lines.append("")
    lines.append("## 备注")
    lines.append("")
    lines.append("- 由于 `F_min = tau_0 / s_min`，所以在不附加额外工程约束时，`tau=3` 与 `tau=5` 的最优几何比相同，只是所需精细度按比例缩放。")
    lines.append("- 当前默认结果已经按第五章正文口径把搜索限制在 `k in [0.2, 0.3]` 的适中主分支内，因此不会再落到 `m=1` 式的极端小几何比解。")
    lines.append("- 在该适中分支内，多个有理点会给出非常接近的 `s_min`；本脚本在这类近等价解中，额外优先选择更接近 `L/R=0.5` 的代表工作点。")
    lines.append("")
    lines.append("## 前几名局部优点")
    lines.append("")
    for idx, row in enumerate(local_rows[:5], start=1):
        lines.append(
            f"- 第 {idx} 名：`k={row.k:.15f}`，`L/R={row.L_over_R:.15f}`，"
            f"`s_min={row.s_min:.15f}`，限制对 `{row.limiting_pair}`。"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parent
    config = load_config(root / "minimal_example_config.json")
    results_dir = root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    coarse_rows: list[ScanRow] = []
    coarse_best: ScanRow | None = None
    for k in linspace(config.search.k_min, config.search.k_max, config.search.coarse_samples):
        row = evaluate_k(config.candidate_modes, k)
        if not passes_geometry_constraints(row, config.geometry_constraints):
            continue
        coarse_rows.append(row)
        if coarse_best is None or rank_key(row, config.geometry_constraints) > rank_key(coarse_best, config.geometry_constraints):
            coarse_best = row

    if coarse_best is None:
        raise RuntimeError("No feasible point survived the configured geometry constraints.")

    best = refine_best(config.candidate_modes, coarse_best, config)
    best = snap_best_to_clean_rational(best, config.candidate_modes, config)
    local_rows = top_local_optima(coarse_rows, config.search.local_optima_to_export, config.geometry_constraints)

    tau_rows: list[dict[str, object]] = []
    for tau in config.tau_targets:
        eta_sort, er_sum_db = tau_lower_bound_metrics(tau)
        tau_rows.append(
            {
                "tau_0": tau,
                "best_k": best.k,
                "best_k_rational_hint": rational_hint(best.k),
                "best_L_over_R": best.L_over_R,
                "s_min_star": best.s_min,
                "F_min": tau / best.s_min,
                "limiting_mode_i": best.limiting_pair[0],
                "limiting_mode_j": best.limiting_pair[1],
                "eta_sort_infty_lower_bound": eta_sort,
                "ER_sum_infty_lower_bound_dB": er_sum_db,
            }
        )

    full_scan_rows = []
    for idx, row in enumerate(coarse_rows):
        if idx % max(1, config.search.export_stride) != 0:
            continue
        full_scan_rows.append(
            {
                "k": row.k,
                "k_rational_hint": rational_hint(row.k),
                "L_over_R": row.L_over_R,
                "s_min": row.s_min,
                "limiting_mode_i": row.limiting_pair[0],
                "limiting_mode_j": row.limiting_pair[1],
                "F_min_tau3": required_finesse(3.0, row.s_min),
                "F_min_tau5": required_finesse(5.0, row.s_min),
            }
        )
    write_csv(
        results_dir / "full_scan.csv",
        full_scan_rows,
        [
            "k",
            "k_rational_hint",
            "L_over_R",
            "s_min",
            "limiting_mode_i",
            "limiting_mode_j",
            "F_min_tau3",
            "F_min_tau5",
        ],
    )

    write_csv(
        results_dir / "tau_results.csv",
        tau_rows,
        [
            "tau_0",
            "best_k",
            "best_k_rational_hint",
            "best_L_over_R",
            "s_min_star",
            "F_min",
            "limiting_mode_i",
            "limiting_mode_j",
            "eta_sort_infty_lower_bound",
            "ER_sum_infty_lower_bound_dB",
        ],
    )

    local_optima_rows = [
        {
            "rank": rank,
            "k": row.k,
            "k_rational_hint": rational_hint(row.k),
            "L_over_R": row.L_over_R,
            "s_min": row.s_min,
            "F_min_tau3": required_finesse(3.0, row.s_min),
            "F_min_tau5": required_finesse(5.0, row.s_min),
            "limiting_mode_i": row.limiting_pair[0],
            "limiting_mode_j": row.limiting_pair[1],
        }
        for rank, row in enumerate(local_rows, start=1)
    ]
    write_csv(
        results_dir / "top_local_optima.csv",
        local_optima_rows,
        [
            "rank",
            "k",
            "k_rational_hint",
            "L_over_R",
            "s_min",
            "F_min_tau3",
            "F_min_tau5",
            "limiting_mode_i",
            "limiting_mode_j",
        ],
    )

    write_summary(results_dir / "summary.md", config, best, tau_rows, local_rows)

    print("Completed minimal full-set search.")
    print(f"Output directory: {results_dir}")
    print(f"Best k*: {best.k:.15f}")
    print(f"Best L/R*: {best.L_over_R:.15f}")
    print(f"s_min*: {best.s_min:.15f}")
    for row in tau_rows:
        print(f"tau={row['tau_0']:.1f} -> F_min={row['F_min']:.6f}")


if __name__ == "__main__":
    main()
