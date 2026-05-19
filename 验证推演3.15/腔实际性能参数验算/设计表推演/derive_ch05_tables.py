from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, stdev
from typing import Iterable

from openpyxl import load_workbook


class DerivationError(RuntimeError):
    pass


OUTPUT_DIR = Path(__file__).resolve().parent
CALC_ROOT = OUTPUT_DIR.parent
REPO_ROOT = CALC_ROOT.parents[2]
THESIS_TEX = REPO_ROOT / "thesis" / "chapters" / "ch05_fp_design_and_validation.tex"
DATA_MAP = CALC_ROOT / "AI_AGENT_文件夹数据地图与读取说明.md"
RAW_088_DIR = CALC_ROOT / "outputs" / "0p88mm" / "原始数据分析结果"
RAW_098_DIR = CALC_ROOT / "outputs" / "0p98mm" / "原始数据分析结果"
FULL_LOAD_DIR = CALC_ROOT / "满载叠加态输入数据" / "最终数据"
PATHS = {
    "thesis_tex": THESIS_TEX,
    "data_map": DATA_MAP,
    "cavity_088": RAW_088_DIR / "cavity_parameters_summary.csv",
    "fsr_088": RAW_088_DIR / "fsr_estimates.csv",
    "kfit_088": RAW_088_DIR / "k_fit_summary.csv",
    "peaks_088": RAW_088_DIR / "main_peak_positions_summary.csv",
    "cavity_098": RAW_098_DIR / "cavity_parameters_summary.csv",
    "fsr_098": RAW_098_DIR / "fsr_estimates.csv",
    "kfit_098": RAW_098_DIR / "k_fit_summary.csv",
    "peaks_098": RAW_098_DIR / "main_peak_positions_summary.csv",
    "theory_validation_cmp": CALC_ROOT / "outputs" / "final_theory_position_validation_comparison.csv",
    "triplicate_aggregate": FULL_LOAD_DIR / "triplicate_full9_aggregate.xlsx",
    "triplicate_stats": FULL_LOAD_DIR / "triplicate_full9_stats.txt",
    "triplicate_trans": FULL_LOAD_DIR / "triplicate_transmittance_l0_8_stats.txt",
    "measurement_method": FULL_LOAD_DIR / "测量方法.md",
}
for run_idx in (1, 2, 3):
    PATHS[f"run{run_idx}_full9"] = FULL_LOAD_DIR / str(run_idx) / "full9_matrix_with_uncertainty.xlsx"
    PATHS[f"run{run_idx}_trans"] = FULL_LOAD_DIR / str(run_idx) / "透射率.xlsx"
ALLOWED_INPUTS = {path.resolve() for path in PATHS.values()}
TABLE2_N_VALUES = [4, 9, 15, 30, 50, 100]
TAU0 = 3.0
K_THEORY = 2.0 / 9.0
TABLE4_VALIDATION_TOL = 1e-4


@dataclass
class Table4ValidationStats:
    mean_abs: float
    rms: float
    max_abs: float
    worst_l: int
    closure_l9_abs: float


def ensure_allowed(path: Path) -> Path:
    resolved = path.resolve()
    if resolved not in ALLOWED_INPUTS:
        raise DerivationError(f"Attempted to read non-whitelisted file: {resolved}")
    if not resolved.exists():
        raise DerivationError(f"Required input file is missing: {resolved}")
    return resolved


def touch_entry_files() -> None:
    for key in ("thesis_tex", "data_map", "measurement_method"):
        _ = ensure_allowed(PATHS[key]).read_text(encoding="utf-8", errors="replace")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    resolved = ensure_allowed(path)
    with resolved.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_single_row_csv(path: Path) -> dict[str, str]:
    rows = read_csv_rows(path)
    if len(rows) != 1:
        raise DerivationError(f"Expected a single-row CSV in {path}, found {len(rows)} rows")
    return rows[0]


def load_workbook_allowed(path: Path):
    resolved = ensure_allowed(path)
    return load_workbook(resolved, data_only=True, read_only=True)


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    target = path.resolve()
    if target.parent != OUTPUT_DIR.resolve():
        raise DerivationError(f"Refusing to write outside output directory: {target}")
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def choose_preferred_m(n: int) -> int:
    candidates = [m for m in range(1, n // 2 + 1) if m / n < 0.5 and gcd(m, n) == 1]
    if not candidates:
        raise DerivationError(f"No valid coprime branch found for N={n}")
    return min(candidates, key=lambda m: (abs(4 * m - n), m))


def build_ring_channel_matrix(n: int, tau0: float) -> tuple[list[list[float]], float]:
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    noise_sum = 0.0
    for output_idx in range(n):
        d = min(output_idx, n - output_idx)
        if d == 0:
            weight = 1.0
        else:
            weight = 1.0 / (1.0 + 4.0 * (d * tau0) ** 2)
            noise_sum += weight
        matrix[output_idx][0] = weight
    col_sum = sum(row[0] for row in matrix)
    for col in range(n):
        for row in range(n):
            rotated = (row - col) % n
            matrix[row][col] = matrix[rotated][0] / col_sum
    return matrix, noise_sum


def mutual_information_bits(conditional: list[list[float]]) -> float:
    n_out = len(conditional)
    n_in = len(conditional[0])
    p_x = 1.0 / n_in
    p_y = [sum(conditional[row][col] * p_x for col in range(n_in)) for row in range(n_out)]
    total = 0.0
    for row in range(n_out):
        for col in range(n_in):
            p_y_given_x = conditional[row][col]
            if p_y_given_x <= 0.0:
                continue
            total += p_x * p_y_given_x * math.log2(p_y_given_x / p_y[row])
    return total


def infinite_noise_closed_form(tau: float) -> float:
    return math.pi * (math.cosh(math.pi / (2.0 * tau)) / math.sinh(math.pi / (2.0 * tau))) / (2.0 * tau) - 1.0


def infinite_noise_partial(tau: float, n_terms: int) -> float:
    return 2.0 * sum(1.0 / (1.0 + 4.0 * (tau * k) ** 2) for k in range(1, n_terms + 1))


def format_float(value: float, digits: int = 12) -> str:
    return f"{value:.{digits}f}"


def parse_transmittance_stats(path: Path) -> dict[int, dict[str, float | list[float]]]:
    text = ensure_allowed(path).read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(r"l=(\d+): run1=([0-9.]+).*?run2=([0-9.]+).*?run3=([0-9.]+).*?mean=([0-9.]+), std=([0-9.]+)", re.IGNORECASE)
    parsed: dict[int, dict[str, float | list[float]]] = {}
    for match in pattern.finditer(text):
        l_value = int(match.group(1))
        parsed[l_value] = {
            "runs": [float(match.group(idx)) for idx in (2, 3, 4)],
            "mean": float(match.group(5)),
            "std": float(match.group(6)),
        }
    if len(parsed) != 9:
        raise DerivationError(f"Expected 9 transmittance channels, parsed {len(parsed)} from {path}")
    return parsed


def sheet_rows_to_matrix(ws) -> list[list[float]]:
    rows = []
    for row in ws.iter_rows(min_row=2, max_row=10, min_col=2, max_col=10, values_only=True):
        rows.append([float(value) / 100.0 for value in row])
    if len(rows) != 9 or any(len(row) != 9 for row in rows):
        raise DerivationError(f"Unexpected matrix shape in sheet {ws.title}")
    return normalize_columns(rows)


def normalize_columns(matrix: list[list[float]]) -> list[list[float]]:
    rows = len(matrix)
    cols = len(matrix[0])
    normalized = [[0.0 for _ in range(cols)] for _ in range(rows)]
    for col in range(cols):
        col_sum = sum(matrix[row][col] for row in range(rows))
        if col_sum <= 0.0:
            raise DerivationError(f"Non-positive column sum encountered while normalizing column {col}")
        for row in range(rows):
            normalized[row][col] = matrix[row][col] / col_sum
    return normalized


def load_aggregate_workbook_data(path: Path) -> dict[str, object]:
    wb = load_workbook_allowed(path)
    er_ws = wb["ER_summary"]
    er_rows = []
    headers = None
    for idx, row in enumerate(er_ws.iter_rows(values_only=True), start=1):
        if idx == 1:
            headers = [str(cell) for cell in row]
            continue
        if row[0] is None:
            break
        er_rows.append({headers[col]: row[col] for col in range(len(headers))})
    overall_ws = wb["overall_stats"]
    overall = {}
    for row in overall_ws.iter_rows(min_row=2, values_only=True):
        key, value = row
        if key is None:
            break
        overall[str(key)] = value
    matrices = {sheet_name: sheet_rows_to_matrix(wb[sheet_name]) for sheet_name in ["1_percentage", "2_percentage", "3_percentage", "combined_percentage"]}
    return {"er_rows": er_rows, "overall": overall, "matrices": matrices}


def build_table1() -> tuple[list[dict[str, object]], list[str]]:
    rows = []
    notes = []
    for tau in range(1, 7):
        closed_form = infinite_noise_closed_form(float(tau))
        partial = infinite_noise_partial(float(tau), 200000)
        diff = abs(closed_form - partial)
        if diff > 1e-5:
            raise DerivationError(f"Infinite-sum convergence check failed for tau={tau}: diff={diff}")
        er_sum = 10.0 * math.log10(1.0 / closed_form)
        eta_sort = 1.0 / (1.0 + closed_form)
        rows.append({"tau": tau, "ER_sum_inf_dB": format_float(er_sum, 9), "eta_sort_inf": format_float(eta_sort, 12)})
        notes.append(f"tau={tau}: closed_form={closed_form:.12f}, partial_200000={partial:.12f}, abs_diff={diff:.3e}")
    return rows, notes


def build_table2() -> list[dict[str, object]]:
    rows = []
    for n in TABLE2_N_VALUES:
        preferred_m = choose_preferred_m(n)
        k_star = preferred_m / n
        lr_star = math.sin(math.pi * preferred_m / n) ** 2
        channel_matrix, noise_sum = build_ring_channel_matrix(n, TAU0)
        eta_sort = 1.0 / (1.0 + noise_sum)
        er_sum = 10.0 * math.log10(1.0 / noise_sum)
        mutual_info = mutual_information_bits(channel_matrix)
        rows.append({
            "N": n,
            "preferred_m": preferred_m,
            "k_star": format_float(k_star, 12),
            "L_over_R_star": format_float(lr_star, 12),
            "F_min": format_float(n * TAU0, 6),
            "ER_sum_pred_dB": format_float(er_sum, 9),
            "eta_sort_pred": format_float(eta_sort, 12),
            "I_pred_bits": format_float(mutual_info, 12),
        })
    return rows

def build_table3(cavity_row: dict[str, str], cavity_098_row: dict[str, str], fsr_rows: list[dict[str, str]], kfit_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    baseline_l = float(cavity_row["baseline_L_mm"])
    baseline_r = float(cavity_row["baseline_R_mm"])
    main_rows = [
        {"block": "几何设定量", "parameter": "L_set", "value": format_float(baseline_l, 6), "uncertainty": "", "unit": "mm", "source_field": "baseline_L_mm", "source_file": str(PATHS["cavity_088"]), "note": "名义硬件设定量"},
        {"block": "几何设定量", "parameter": "R_set", "value": format_float(baseline_r, 6), "uncertainty": "", "unit": "mm", "source_field": "baseline_R_mm", "source_file": str(PATHS["cavity_088"]), "note": "名义硬件设定量"},
        {"block": "几何设定量", "parameter": "(L/R)_set", "value": format_float(baseline_l / baseline_r, 12), "uncertainty": "", "unit": "", "source_field": "baseline_L_mm/baseline_R_mm", "source_file": str(PATHS["cavity_088"]), "note": "由名义 L 与 R 直接计算"},
        {"block": "几何设定量", "parameter": "L_eff", "value": format_float(float(cavity_row["L_mm"]), 6), "uncertainty": format_float(float(cavity_row["L_err_mm"]), 6), "unit": "mm", "source_field": "L_mm", "source_file": str(PATHS["cavity_088"]), "note": "后置：等效反演几何量"},
        {"block": "几何设定量", "parameter": "R_eff", "value": format_float(float(cavity_row["R_mm"]), 6), "uncertainty": format_float(float(cavity_row["R_err_mm"]), 6), "unit": "mm", "source_field": "R_mm", "source_file": str(PATHS["cavity_088"]), "note": "后置：等效反演几何量"},
        {"block": "几何设定量", "parameter": "(L/R)_eff", "value": format_float(float(cavity_row["L_over_R"]), 12), "uncertainty": format_float(float(cavity_row["L_over_R_err"]), 12), "unit": "", "source_field": "L_over_R", "source_file": str(PATHS["cavity_088"]), "note": "后置：等效反演几何量"},
        {"block": "实测频域量", "parameter": "k", "value": format_float(float(cavity_row["k_relative_fit"]), 12), "uncertainty": format_float(float(cavity_row["k_relative_fit_err"]), 12), "unit": "", "source_field": "k_relative_fit", "source_file": str(PATHS["cavity_088"]), "note": "headline 参数"},
        {"block": "实测频域量", "parameter": "FSR", "value": format_float(float(cavity_row["fsr_final_ghz"]), 9), "uncertainty": format_float(float(cavity_row["fsr_final_err_ghz"]), 9), "unit": "GHz", "source_field": "fsr_final_ghz", "source_file": str(PATHS["cavity_088"]), "note": "headline 参数"},
        {"block": "实测频域量", "parameter": "F", "value": format_float(float(cavity_row["finesse_all_weighted_mean"]), 9), "uncertainty": format_float(float(cavity_row["finesse_all_weighted_err"]), 9), "unit": "", "source_field": "finesse_all_weighted_mean", "source_file": str(PATHS["cavity_088"]), "note": "headline 参数"},
    ]
    recommended_fsr = next((row for row in fsr_rows if row["method"] == "recommended"), None)
    if recommended_fsr is None:
        raise DerivationError("Unable to locate recommended FSR row in fsr_estimates.csv")
    max_abs_residual = max(abs(float(row["residual"])) for row in kfit_rows[:-1])
    trace_rows = [{"table": "table3", "output_field": row["parameter"], "source_file": row["source_file"], "source_field": row["source_field"], "source_value": row["value"], "transformation": "direct" if "/" not in str(row["source_field"]) else "computed ratio", "role": "main"} for row in main_rows]
    trace_rows.extend([
        {"table": "table3", "output_field": "FSR_crosscheck_0p88_recommended", "source_file": str(PATHS["fsr_088"]), "source_field": "method=recommended", "source_value": recommended_fsr["fsr_ghz"], "transformation": "cross-check against cavity_parameters_summary.fsr_final_ghz", "role": "cross_check"},
        {"table": "table3", "output_field": "k_fit_max_abs_residual_0p88", "source_file": str(PATHS["kfit_088"]), "source_field": "residual", "source_value": format_float(max_abs_residual, 12), "transformation": "max(abs(residual)) over l=0..8", "role": "cross_check"},
        {"table": "table3", "output_field": "0p98_parallel_FSR", "source_file": str(PATHS["cavity_098"]), "source_field": "fsr_final_ghz", "source_value": cavity_098_row["fsr_final_ghz"], "transformation": "parallel cross-check only", "role": "parallel_cross_check"},
        {"table": "table3", "output_field": "0p98_parallel_k", "source_file": str(PATHS["cavity_098"]), "source_field": "k_relative_fit", "source_value": cavity_098_row["k_relative_fit"], "transformation": "parallel cross-check only", "role": "parallel_cross_check"},
    ])
    return main_rows, trace_rows


def build_table4(cavity_row: dict[str, str], peak_rows: list[dict[str, str]], theory_validation_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], Table4ValidationStats]:
    fsr = float(cavity_row["fsr_final_ghz"])
    ref_nu = float(peak_rows[0]["merged_nu_ghz"])
    table_rows = []
    trace_rows = []
    validation_abs = []
    for row in peak_rows:
        l_value = int(row["l"])
        measured_nu = float(row["merged_nu_ghz"])
        measured_pos = ((measured_nu - ref_nu) / fsr) % 1.0
        theory_pos = (l_value * K_THEORY) % 1.0
        branch_order = int(row["m_l"])
        theory_shift = round((measured_nu - ref_nu) / fsr - theory_pos)
        theory_nu = ref_nu + fsr * (theory_pos + theory_shift)
        delta_pos = measured_pos - theory_pos
        delta_nu_mhz = (measured_nu - theory_nu) * 1000.0
        table_rows.append({
            "mode_index": l_value,
            "branch_order_m_l": branch_order,
            "theory_pos": format_float(theory_pos, 12),
            "measured_pos": format_float(measured_pos, 12),
            "delta_pos": format_float(delta_pos, 12),
            "theory_nu_ghz": format_float(theory_nu, 9),
            "measured_nu_ghz": format_float(measured_nu, 9),
            "delta_nu_mhz": format_float(delta_nu_mhz, 6),
        })
        trace_rows.extend([
            {"table": "table4", "mode_index": l_value, "output_field": "measured_pos", "source_file": str(PATHS["peaks_088"]), "source_field": "merged_nu_ghz", "source_value": row["merged_nu_ghz"], "transformation": "((merged_nu_ghz - ref_l0_nu) / fsr_final_ghz) % 1", "role": "main"},
            {"table": "table4", "mode_index": l_value, "output_field": "theory_pos", "source_file": str(PATHS["thesis_tex"]), "source_field": "k_theory=2/9", "source_value": format_float(theory_pos, 12), "transformation": "(l * 2/9) % 1", "role": "main"},
            {"table": "table4", "mode_index": l_value, "output_field": "theory_nu_ghz", "source_file": str(PATHS["peaks_088"]), "source_field": "reference_nu + nearest_integer_shift", "source_value": format_float(theory_nu, 9), "transformation": "ref_l0_nu + fsr_final_ghz * (theory_pos + round((measured_nu-ref_l0_nu)/fsr_final_ghz-theory_pos))", "role": "derived"},
        ])
        if 1 <= l_value <= 8:
            validation_abs.append((l_value, abs(delta_pos)))
    closure_l9_abs = abs(float(table_rows[-1]["delta_pos"]))
    stats = Table4ValidationStats(
        mean_abs=mean(value for _, value in validation_abs),
        rms=math.sqrt(mean(value * value for _, value in validation_abs)),
        max_abs=max(value for _, value in validation_abs),
        worst_l=max(validation_abs, key=lambda item: item[1])[0],
        closure_l9_abs=closure_l9_abs,
    )
    reference_row = next(row for row in theory_validation_rows if row["dataset_key"] == "0p88mm" and row["analysis_source"] == "raw" and row["measurement_type"] == "merged")
    checks = {
        "mean_abs": abs(stats.mean_abs - float(reference_row["mean_abs_delta_pos"])),
        "rms": abs(stats.rms - float(reference_row["rms_delta_pos"])),
        "max_abs": abs(stats.max_abs - float(reference_row["max_abs_delta_pos"])),
        "closure_l9_abs": abs(stats.closure_l9_abs - float(reference_row["closure_l9_abs_delta_pos"])),
    }
    if any(diff > TABLE4_VALIDATION_TOL for diff in checks.values()) or stats.worst_l != int(reference_row["worst_l"]):
        raise DerivationError(f"Table 4 validation mismatch: diffs={checks}, computed_worst_l={stats.worst_l}, expected={reference_row['worst_l']}")
    trace_rows.extend([
        {"table": "table4", "mode_index": "summary", "output_field": "mean_abs_delta_pos_validation", "source_file": str(PATHS["theory_validation_cmp"]), "source_field": "mean_abs_delta_pos", "source_value": reference_row["mean_abs_delta_pos"], "transformation": "cross-check vs recomputed l=1..8 main-table rows", "role": "cross_check"},
        {"table": "table4", "mode_index": "summary", "output_field": "closure_l9_abs_delta_pos_validation", "source_file": str(PATHS["theory_validation_cmp"]), "source_field": "closure_l9_abs_delta_pos", "source_value": reference_row["closure_l9_abs_delta_pos"], "transformation": "cross-check vs recomputed l=9 closure row", "role": "cross_check"},
    ])
    return table_rows, trace_rows, stats

def build_table5(aggregate_data: dict[str, object], transmittance_by_l: dict[int, dict[str, float | list[float]]]) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, float]]:
    er_rows = aggregate_data["er_rows"]
    matrices = aggregate_data["matrices"]
    trans_run_means = [mean(transmittance_by_l[l]["runs"][run_idx] for l in sorted(transmittance_by_l)) for run_idx in range(3)]
    trans_channel_means = {l: float(transmittance_by_l[l]["mean"]) for l in transmittance_by_l}
    t_bar = mean(trans_run_means)
    t_bar_sd = stdev(trans_run_means)
    t_min = min(trans_channel_means.values())
    er_sum_run_means = [mean(float(row[f"ER_sum_run{run_idx}_dB"]) for row in er_rows) for run_idx in (1, 2, 3)]
    eta_run_means = [mean(float(row[f"SignalShare_run{run_idx}_%"]) / 100.0 for row in er_rows) for run_idx in (1, 2, 3)]
    channel_er_sum_mean = [float(row["ER_sum_mean_dB"]) for row in er_rows]
    channel_eta_mean = [float(row["SignalShare_mean_%"]) / 100.0 for row in er_rows]
    er_sum_bar = mean(er_sum_run_means)
    er_sum_bar_sd = stdev(er_sum_run_means)
    eta_bar = mean(eta_run_means)
    eta_bar_sd = stdev(eta_run_means)
    er_sum_min = min(channel_er_sum_mean)
    eta_min = min(channel_eta_mean)
    run_i_values = [mutual_information_bits(matrices[f"{run_idx}_percentage"]) for run_idx in (1, 2, 3)]
    combined_i = mutual_information_bits(matrices["combined_percentage"])
    i_bar = mean(run_i_values)
    i_sd = stdev(run_i_values)
    rows = [
        {"metric": "\\bar T", "value": format_float(100.0 * t_bar, 6), "spread": format_float(100.0 * t_bar_sd, 6), "spread_type": "SD", "unit": "%", "source_basis": "triplicate_transmittance_l0_8_stats.txt", "note": "三次 run 的通道平均透射率，再做 mean ± SD (n=3)"},
        {"metric": "T_min", "value": format_float(100.0 * t_min, 6), "spread": "", "spread_type": "", "unit": "%", "source_basis": "triplicate_transmittance_l0_8_stats.txt", "note": "按通道三次 run 平均后取最差通道，不加 ±"},
        {"metric": "\\bar\\eta_sort", "value": format_float(100.0 * eta_bar, 6), "spread": format_float(100.0 * eta_bar_sd, 6), "spread_type": "SD", "unit": "%", "source_basis": "triplicate_full9_aggregate.xlsx:ER_summary", "note": "三次 run 的 9 通道平均 SignalShare，再做 mean ± SD (n=3)"},
        {"metric": "\\eta_sort,min", "value": format_float(100.0 * eta_min, 6), "spread": "", "spread_type": "", "unit": "%", "source_basis": "triplicate_full9_aggregate.xlsx:ER_summary", "note": "按通道三次 run 平均后取最差通道，不加 ±"},
        {"metric": "\\overline{ER_sum}", "value": format_float(er_sum_bar, 6), "spread": format_float(er_sum_bar_sd, 6), "spread_type": "SD", "unit": "dB", "source_basis": "triplicate_full9_aggregate.xlsx:ER_summary", "note": "三次 run 的 9 通道平均 ER_sum，再做 mean ± SD (n=3)"},
        {"metric": "ER_sum,min", "value": format_float(er_sum_min, 6), "spread": "", "spread_type": "", "unit": "dB", "source_basis": "triplicate_full9_aggregate.xlsx:ER_summary", "note": "按通道三次 run 平均后取最差通道，不加 ±"},
        {"metric": "I(l;\\hat l)", "value": format_float(i_bar, 6), "spread": format_float(i_sd, 6), "spread_type": "SD", "unit": "bits", "source_basis": "triplicate_full9_aggregate.xlsx:{1,2,3}_percentage", "note": "固定维度、等先验；分别由 3 个 run 的条件概率矩阵计算后做 mean ± SD (n=3)"},
    ]
    trace_rows = [
        {"table": "table5", "metric": "\\bar T", "source_file": str(PATHS["triplicate_trans"]), "source_basis": "per-run channel-average transmittance", "value": format_float(100.0 * t_bar, 6), "spread": format_float(100.0 * t_bar_sd, 6), "detail": "; ".join(f"run{idx+1}={100.0 * value:.6f}%" for idx, value in enumerate(trans_run_means)), "role": "main"},
        {"table": "table5", "metric": "T_min", "source_file": str(PATHS["triplicate_trans"]), "source_basis": "min over channel means", "value": format_float(100.0 * t_min, 6), "spread": "", "detail": "; ".join(f"l={l}:{100.0 * trans_channel_means[l]:.6f}%" for l in sorted(trans_channel_means)), "role": "main"},
        {"table": "table5", "metric": "\\bar\\eta_sort", "source_file": str(PATHS["triplicate_aggregate"]), "source_basis": "ER_summary SignalShare_run{1,2,3}_%", "value": format_float(100.0 * eta_bar, 6), "spread": format_float(100.0 * eta_bar_sd, 6), "detail": "; ".join(f"run{idx+1}={100.0 * value:.6f}%" for idx, value in enumerate(eta_run_means)), "role": "main"},
        {"table": "table5", "metric": "\\eta_sort,min", "source_file": str(PATHS["triplicate_aggregate"]), "source_basis": "min over channel SignalShare_mean_%", "value": format_float(100.0 * eta_min, 6), "spread": "", "detail": "; ".join(f"ch={idx}:{100.0 * value:.6f}%" for idx, value in enumerate(channel_eta_mean)), "role": "main"},
        {"table": "table5", "metric": "\\overline{ER_sum}", "source_file": str(PATHS["triplicate_aggregate"]), "source_basis": "ER_summary ER_sum_run{1,2,3}_dB", "value": format_float(er_sum_bar, 6), "spread": format_float(er_sum_bar_sd, 6), "detail": "; ".join(f"run{idx+1}={value:.6f} dB" for idx, value in enumerate(er_sum_run_means)), "role": "main"},
        {"table": "table5", "metric": "ER_sum,min", "source_file": str(PATHS["triplicate_aggregate"]), "source_basis": "min over channel ER_sum_mean_dB", "value": format_float(er_sum_min, 6), "spread": "", "detail": "; ".join(f"ch={idx}:{value:.6f} dB" for idx, value in enumerate(channel_er_sum_mean)), "role": "main"},
        {"table": "table5", "metric": "I(l;\\hat l)", "source_file": str(PATHS["triplicate_aggregate"]), "source_basis": "1_percentage,2_percentage,3_percentage", "value": format_float(i_bar, 6), "spread": format_float(i_sd, 6), "detail": "; ".join(f"run{idx+1}={value:.6f} bits" for idx, value in enumerate(run_i_values)), "role": "main"},
        {"table": "table5", "metric": "I(l;\\hat l)_combined_crosscheck", "source_file": str(PATHS["triplicate_aggregate"]), "source_basis": "combined_percentage", "value": format_float(combined_i, 6), "spread": "", "detail": "combined matrix MI for trace cross-check only", "role": "cross_check"},
    ]
    stats = {"t_bar_percent": 100.0 * t_bar, "t_bar_sd_percent": 100.0 * t_bar_sd, "t_min_percent": 100.0 * t_min, "eta_bar_percent": 100.0 * eta_bar, "eta_bar_sd_percent": 100.0 * eta_bar_sd, "eta_min_percent": 100.0 * eta_min, "er_sum_bar": er_sum_bar, "er_sum_bar_sd": er_sum_bar_sd, "er_sum_min": er_sum_min, "i_bar_bits": i_bar, "i_sd_bits": i_sd, "i_combined_bits": combined_i}
    return rows, trace_rows, stats


def validate_table5(aggregate_data: dict[str, object], table5_stats: dict[str, float]) -> None:
    overall = aggregate_data["overall"]
    if abs(table5_stats["er_sum_bar"] - float(overall["ER_sum_all_mean_dB"])) > 1e-9:
        raise DerivationError("Table 5 overall ER_sum mean does not match overall_stats sheet")
    if abs(table5_stats["eta_bar_percent"] - float(overall["combined_diag_share_mean_%"])) > 0.05:
        raise DerivationError("Table 5 eta mean does not align with combined_diag_share_mean_% within tolerance")


def write_readme(table1_notes: list[str], table4_stats: Table4ValidationStats, table5_stats: dict[str, float]) -> None:
    text = f"""# 第五章表 1-5 推演结果说明

## 工作边界
- 仅写入当前目录：`{OUTPUT_DIR}`
- 未修改任何 `.tex`、图文件、control/canon、原始实验数据或既有结果文件
- 主线口径固定为 `0.88 / 原始数据分析结果`
- `0.98` 仅作为并行交叉校核

## 已生成文件
- `derive_ch05_tables.py`
- `table1_tau_lower_bound.csv`
- `table2_tau0_3_blueprint.csv`
- `table3_device_parameters.csv`
- `table4_peak_positions.csv`
- `table5_full_load_summary.csv`
- `table3_source_trace.csv`
- `table4_source_trace.csv`
- `table5_source_trace.csv`

## 表 1
- 用途：`tau=1..6` 的维度无关保守底线表，仅含 `ER_sum^(∞)` 与 `eta_sort^(∞)`
- 主来源：`ch05_fp_design_and_validation.tex`
- 收敛记录：
{chr(10).join(f"  - {note}" for note in table1_notes)}

## 表 2
- 用途：固定 `tau0=3` 的连续满载设计蓝图
- 行范围：`N = 4, 9, 15, 30, 50, 100`
- `preferred_m` 规则：在互质解析分支中优先选 `(L/R)^*` 最接近 `0.5` 的分支；若并列取较小 `m`
- `ER_sum_pred`、`eta_sort_pred`、`I_pred` 均按固定维度、等先验、有限维均匀环模型计算

## 表 3
- 主来源：`outputs/0p88mm/原始数据分析结果/cavity_parameters_summary.csv`
- 校核来源：`fsr_estimates.csv`、`k_fit_summary.csv`、`0p98` 对应 summary
- `k`、`FSR`、`F` 为 headline；`L_eff`、`R_eff`、`(L/R)_eff` 仅作后置等效反演几何量

## 表 4
- 主来源：`outputs/0p88mm/原始数据分析结果/main_peak_positions_summary.csv`
- 校核来源：`outputs/final_theory_position_validation_comparison.csv`
- 复核结果：
  - `mean_abs_delta_pos (l=1..8) = {table4_stats.mean_abs:.12f}`
  - `rms_delta_pos (l=1..8) = {table4_stats.rms:.12f}`
  - `max_abs_delta_pos (l=1..8) = {table4_stats.max_abs:.12f}`
  - `worst_l = {table4_stats.worst_l}`
  - `closure_l9_abs_delta_pos = {table4_stats.closure_l9_abs:.12f}`
- 待人工拍板：正文最终是否保留 `l=9` 作为主表行

## 表 5
- 主来源：`triplicate_full9_aggregate.xlsx` 与 `triplicate_transmittance_l0_8_stats.txt`
- 校核来源：`triplicate_full9_stats.txt`、`最终数据/1,2,3/full9_matrix_with_uncertainty.xlsx`、`最终数据/1,2,3/透射率.xlsx`、`测量方法.md`
- `±` 统一采用三次独立实验的 `SD`
- worst-case 指标按“通道三次 run 平均后再取最差通道”
- 摘要：
  - `\\bar T = {table5_stats['t_bar_percent']:.6f} ± {table5_stats['t_bar_sd_percent']:.6f} %`
  - `T_min = {table5_stats['t_min_percent']:.6f} %`
  - `\\bar\\eta_sort = {table5_stats['eta_bar_percent']:.6f} ± {table5_stats['eta_bar_sd_percent']:.6f} %`
  - `\\eta_sort,min = {table5_stats['eta_min_percent']:.6f} %`
  - `\\overline{{ER_sum}} = {table5_stats['er_sum_bar']:.6f} ± {table5_stats['er_sum_bar_sd']:.6f} dB`
  - `ER_sum,min = {table5_stats['er_sum_min']:.6f} dB`
  - `I(l;\\hat l) = {table5_stats['i_bar_bits']:.6f} ± {table5_stats['i_sd_bits']:.6f} bits`
  - `I(l;\\hat l)` combined-matrix cross-check = `{table5_stats['i_combined_bits']:.6f}` bits

## 旧文件边界
- 根目录旧汇总文件只能辅助参考，不能当唯一真值
- 未读取任何 `control/canon`
"""
    (OUTPUT_DIR / "README_推演结果说明.md").write_text(text, encoding="utf-8-sig")


def main() -> None:
    touch_entry_files()
    cavity_088 = read_single_row_csv(PATHS["cavity_088"])
    cavity_098 = read_single_row_csv(PATHS["cavity_098"])
    fsr_088 = read_csv_rows(PATHS["fsr_088"])
    kfit_088 = read_csv_rows(PATHS["kfit_088"])
    peaks_088 = read_csv_rows(PATHS["peaks_088"])
    theory_validation_rows = read_csv_rows(PATHS["theory_validation_cmp"])
    aggregate_data = load_aggregate_workbook_data(PATHS["triplicate_aggregate"])
    transmittance_by_l = parse_transmittance_stats(PATHS["triplicate_trans"])
    _ = ensure_allowed(PATHS["triplicate_stats"]).read_text(encoding="utf-8", errors="replace")
    table1_rows, table1_notes = build_table1()
    table2_rows = build_table2()
    table3_rows, table3_trace = build_table3(cavity_088, cavity_098, fsr_088, kfit_088)
    table4_rows, table4_trace, table4_stats = build_table4(cavity_088, peaks_088, theory_validation_rows)
    table5_rows, table5_trace, table5_stats = build_table5(aggregate_data, transmittance_by_l)
    validate_table5(aggregate_data, table5_stats)
    write_csv(OUTPUT_DIR / "table1_tau_lower_bound.csv", ["tau", "ER_sum_inf_dB", "eta_sort_inf"], table1_rows)
    write_csv(OUTPUT_DIR / "table2_tau0_3_blueprint.csv", ["N", "preferred_m", "k_star", "L_over_R_star", "F_min", "ER_sum_pred_dB", "eta_sort_pred", "I_pred_bits"], table2_rows)
    write_csv(OUTPUT_DIR / "table3_device_parameters.csv", ["block", "parameter", "value", "uncertainty", "unit", "source_field", "source_file", "note"], table3_rows)
    write_csv(OUTPUT_DIR / "table4_peak_positions.csv", ["mode_index", "branch_order_m_l", "theory_pos", "measured_pos", "delta_pos", "theory_nu_ghz", "measured_nu_ghz", "delta_nu_mhz"], table4_rows)
    write_csv(OUTPUT_DIR / "table5_full_load_summary.csv", ["metric", "value", "spread", "spread_type", "unit", "source_basis", "note"], table5_rows)
    write_csv(OUTPUT_DIR / "table3_source_trace.csv", ["table", "output_field", "source_file", "source_field", "source_value", "transformation", "role"], table3_trace)
    write_csv(OUTPUT_DIR / "table4_source_trace.csv", ["table", "mode_index", "output_field", "source_file", "source_field", "source_value", "transformation", "role"], table4_trace)
    write_csv(OUTPUT_DIR / "table5_source_trace.csv", ["table", "metric", "source_file", "source_basis", "value", "spread", "detail", "role"], table5_trace)
    write_readme(table1_notes, table4_stats, table5_stats)
    print("Generated ch05 table derivation workspace outputs:")
    for name in ["table1_tau_lower_bound.csv", "table2_tau0_3_blueprint.csv", "table3_device_parameters.csv", "table4_peak_positions.csv", "table5_full_load_summary.csv", "table3_source_trace.csv", "table4_source_trace.csv", "table5_source_trace.csv", "README_推演结果说明.md"]:
        print(f" - {OUTPUT_DIR / name}")


if __name__ == "__main__":
    main()

