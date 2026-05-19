from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from cavity_recalc_common import (
    ROOM_TEMP_C,
    TARGET_TEMP_C,
    BranchSelectionResult,
    PeakFitResult,
    compare_scan_sets,
    derive_cavity_params,
    discover_datasets,
    estimate_fsr_direct,
    export_tables_and_plots,
    find_matching_peak_in_window,
    find_peak_candidates,
    fit_global_fsr_k,
    fit_k_from_positions,
    format_value,
    fused_silica_index,
    load_scan_csv,
    malitson_index_20c,
    merge_direction_results,
    save_csv,
    select_main_branch,
)


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
THESIS_BASELINE = {"L_mm": 10.25, "R_mm": 25.0, "k": 0.221, "F": 29.8}
K_WORKING_FIT_MAX_L = 8
SOURCE_CONFIGS = {
    "raw": {"folder_name": "原始数据分析结果", "display_name": "原始数据", "other": "final"},
    "final": {"folder_name": "FSR补全分析结果", "display_name": "FSR补全后数据", "other": "raw"},
}


def peak_to_row(result: PeakFitResult, adopted_fsr_ghz: float | None = None) -> Dict[str, Any]:
    finesse = adopted_fsr_ghz / result.fwhm_ghz if adopted_fsr_ghz and result.fwhm_ghz > 0 else np.nan
    return {
        "dataset_key": result.dataset_key,
        "l": result.l_index,
        "scan_direction": result.scan_direction,
        "source": result.source,
        "candidate_rank": result.candidate_rank,
        "fit_model": result.fit_model,
        "selected": result.selected,
        "branch_role": result.branch_role,
        "lambda_center_nm": result.lambda_center_nm,
        "lambda_center_err_nm": result.lambda_center_err_nm,
        "nu_center_ghz": result.nu_center_ghz,
        "nu_center_err_ghz": result.nu_center_err_ghz,
        "fwhm_nm": result.fwhm_nm,
        "fwhm_err_nm": result.fwhm_err_nm,
        "fwhm_ghz": result.fwhm_ghz,
        "fwhm_err_ghz": result.fwhm_err_ghz,
        "finesse_with_final_fsr": finesse,
        "peak_power_uw": result.peak_power_uw,
        "baseline_uw": result.baseline_uw,
        "amplitude_uw": result.amplitude_uw,
        "prominence_uw": result.prominence_uw,
        "r_squared": result.r_squared,
        "residual_rms_uw": result.residual_rms_uw,
        "window_lambda_min_nm": result.window_lambda_min_nm,
        "window_lambda_max_nm": result.window_lambda_max_nm,
        "peak_index": result.peak_index,
    }


def _weighted_mean(values: np.ndarray, sigmas: np.ndarray) -> tuple[float, float]:
    mask = np.isfinite(values) & np.isfinite(sigmas) & (sigmas > 0)
    if not np.any(mask):
        return float(np.mean(values)), np.nan
    weights = 1.0 / sigmas[mask] ** 2
    mean = float(np.sum(weights * values[mask]) / np.sum(weights))
    sigma = float(np.sqrt(1.0 / np.sum(weights)))
    return mean, sigma


def _mode_finesse_stats(selected_peak_df: pd.DataFrame) -> Dict[str, float]:
    l_values = selected_peak_df["l"].to_numpy(dtype=int)
    finesse_values = selected_peak_df["finesse"].to_numpy(dtype=float)
    finite_mask = np.isfinite(finesse_values)
    finite_finesse = finesse_values[finite_mask]
    finite_l = l_values[finite_mask]
    if finite_finesse.size == 0:
        return {
            "l_min": np.nan,
            "l_max": np.nan,
            "count": 0,
            "mean": np.nan,
            "sd": np.nan,
            "min": np.nan,
            "max": np.nan,
        }
    sd = float(np.std(finite_finesse, ddof=1)) if finite_finesse.size > 1 else 0.0
    return {
        "l_min": int(np.min(finite_l)),
        "l_max": int(np.max(finite_l)),
        "count": int(finite_finesse.size),
        "mean": float(np.mean(finite_finesse)),
        "sd": sd,
        "min": float(np.min(finite_finesse)),
        "max": float(np.max(finite_finesse)),
    }


def _selected_main_peak_positions(
    merged_peaks: Dict[int, Dict[str, Any]],
    global_fit_merged: Dict[str, Any],
    k_fit_used_by_l: Dict[int, bool],
) -> pd.DataFrame:
    rows = []
    for l in sorted(merged_peaks):
        merged = merged_peaks[l]
        rising: PeakFitResult = merged["rising"]
        falling: PeakFitResult = merged["falling"]
        rows.append(
            {
                "l": l,
                "rising_lambda_nm": rising.lambda_center_nm,
                "falling_lambda_nm": falling.lambda_center_nm,
                "merged_lambda_nm": merged["lambda_center_nm"],
                "rising_nu_ghz": rising.nu_center_ghz,
                "falling_nu_ghz": falling.nu_center_ghz,
                "merged_nu_ghz": merged["nu_center_ghz"],
                "rising_falling_lambda_diff_nm": merged["lambda_center_diff_nm"],
                "rising_falling_nu_diff_ghz": merged["nu_center_diff_ghz"],
                "falling_branch_shift_fsr": merged["falling_branch_shift_fsr"],
                "m_l": global_fit_merged["m_indices"][l],
                "k_fit_role": "reference" if l == 0 else ("anchor" if k_fit_used_by_l.get(l, False) else "holdout"),
                "used_in_k_relative_fit": bool(k_fit_used_by_l.get(l, False)),
            }
        )
    return pd.DataFrame(rows)


def _k_working_fit_mask(l_values: np.ndarray) -> np.ndarray:
    l_arr = np.asarray(l_values, dtype=int)
    mask = (l_arr > 0) & (l_arr <= K_WORKING_FIT_MAX_L)
    if not np.any(mask):
        raise ValueError("No positive l values are available for the working-point k fit.")
    return mask


def _build_cross_source_validation(
    dataset_key: str,
    primary_label: str,
    reference_label: str,
    primary_scans: Dict[int, pd.DataFrame],
    reference_scans: Dict[int, pd.DataFrame],
    branch_results: Dict[str, BranchSelectionResult],
) -> tuple[pd.DataFrame, List[PeakFitResult]]:
    comparison_frames = []
    reference_validation_rows: List[PeakFitResult] = []
    for l_index in sorted(primary_scans):
        selected_for_l = [
            branch_results["Rising"].selected_candidates[l_index],
            branch_results["Falling"].selected_candidates[l_index],
        ]
        comparison_frames.append(
            compare_scan_sets(
                dataset_key=dataset_key,
                primary_scan_df=primary_scans[l_index],
                reference_scan_df=reference_scans[l_index],
                chosen_peak_windows=selected_for_l,
                primary_label=primary_label,
                reference_label=reference_label,
            )
        )
        for primary_peak in selected_for_l:
            reference_peak = find_matching_peak_in_window(
                df=reference_scans[l_index],
                dataset_key=dataset_key,
                l_index=l_index,
                scan_direction=primary_peak.scan_direction,
                source=reference_label,
                lambda_min_nm=primary_peak.window_lambda_min_nm,
                lambda_max_nm=primary_peak.window_lambda_max_nm,
                expected_center_nm=primary_peak.lambda_center_nm,
            )
            if reference_peak is not None:
                reference_peak.selected = True
                reference_peak.branch_role = f"{reference_label}_validation"
                reference_validation_rows.append(reference_peak)
    return pd.concat(comparison_frames, ignore_index=True), reference_validation_rows


def _analyze_dataset_source(dataset, source_kind: str) -> Dict[str, Any]:
    source_cfg = SOURCE_CONFIGS[source_kind]
    other_kind = source_cfg["other"]
    scans_by_source = {
        "raw": {l: load_scan_csv(path) for l, path in dataset.raw_files.items()},
        "final": {l: load_scan_csv(path) for l, path in dataset.final_files.items()},
    }
    primary_scans = scans_by_source[source_kind]
    reference_scans = scans_by_source[other_kind]

    fsr_a = estimate_fsr_direct(f"{dataset.key}_{source_kind}", primary_scans[0])
    fsr_hint_ghz = fsr_a["combined_fsr_ghz"]

    candidates_by_direction: Dict[str, Dict[int, List[PeakFitResult]]] = {"Rising": {}, "Falling": {}}
    all_primary_candidates: List[PeakFitResult] = []
    for l_index, primary_df in primary_scans.items():
        for direction in ["Rising", "Falling"]:
            sub = primary_df[primary_df["Scan_Direction"] == direction]
            candidates = find_peak_candidates(
                sub,
                dataset_key=f"{dataset.key}_{source_kind}",
                l_index=l_index,
                scan_direction=direction,
                source=source_kind,
                max_candidates=3,
            )
            candidates_by_direction[direction][l_index] = candidates
            all_primary_candidates.extend(candidates)

    branch_results: Dict[str, BranchSelectionResult] = {}
    for direction in ["Rising", "Falling"]:
        branch_results[direction] = select_main_branch(
            dataset_key=f"{dataset.key}_{source_kind}",
            scan_direction=direction,
            candidates_by_l=candidates_by_direction[direction],
            fsr_hint_ghz=fsr_hint_ghz,
        )

    merged_peaks = merge_direction_results(branch_results, fsr_hint_ghz=fsr_hint_ghz)
    global_fit_merged = fit_global_fsr_k(
        l_values=sorted(merged_peaks.keys()),
        nu_values_ghz=[merged_peaks[l]["nu_center_ghz"] for l in sorted(merged_peaks)],
        fsr_guess_ghz=fsr_hint_ghz,
    )
    global_fit_by_direction = {}
    for direction in ["Rising", "Falling"]:
        direction_selected = branch_results[direction].selected_candidates
        global_fit_by_direction[direction] = fit_global_fsr_k(
            l_values=sorted(direction_selected.keys()),
            nu_values_ghz=[direction_selected[l].nu_center_ghz for l in sorted(direction_selected)],
            fsr_guess_ghz=fsr_hint_ghz,
        )

    direct_vals = np.asarray([item["fsr_ghz"] for item in fsr_a["by_direction"].values()], dtype=float)
    direct_rel_diff = abs(direct_vals[0] - direct_vals[1]) / np.mean(direct_vals)
    fsr_choice = "A_direct" if direct_rel_diff <= 0.01 else "B_global"
    fsr_final = fsr_a["combined_fsr_ghz"] if fsr_choice == "A_direct" else global_fit_merged["fsr_ghz"]
    fsr_final_err = fsr_a["combined_fsr_err_ghz"] if fsr_choice == "A_direct" else max(
        global_fit_merged["fsr_err_ghz"],
        float(np.std([global_fit_by_direction["Rising"]["fsr_ghz"], global_fit_by_direction["Falling"]["fsr_ghz"]], ddof=1)),
    )

    l_values = np.asarray(sorted(merged_peaks.keys()), dtype=int)
    nu_values = np.asarray([merged_peaks[l]["nu_center_ghz"] for l in l_values], dtype=float)
    nu0 = float(nu_values[l_values == 0][0])
    pos_meas = np.mod((nu_values - nu0) / fsr_final, 1.0)
    working_fit_mask = _k_working_fit_mask(l_values)
    k_fit_used_by_l = {int(l): bool(use_for_fit) for l, use_for_fit in zip(l_values, working_fit_mask)}
    k_fit_merged = fit_k_from_positions(l_values, pos_meas, fit_mask=working_fit_mask)
    k_by_direction = {}
    for direction in ["Rising", "Falling"]:
        direction_selected = branch_results[direction].selected_candidates
        nu_dir = np.asarray([direction_selected[l].nu_center_ghz for l in l_values], dtype=float)
        pos_dir = np.mod((nu_dir - nu_dir[l_values == 0][0]) / fsr_final, 1.0)
        k_by_direction[direction] = fit_k_from_positions(l_values, pos_dir, fit_mask=working_fit_mask)
    k_final = k_fit_merged["k"]
    k_direction_scatter = float(np.std([k_by_direction["Rising"]["k"], k_by_direction["Falling"]["k"]], ddof=1))
    k_final_err = max(
        k_fit_merged["sigma_k"] if np.isfinite(k_fit_merged["sigma_k"]) else 0.0,
        k_direction_scatter,
        global_fit_merged["k_err"] if np.isfinite(global_fit_merged["k_err"]) else 0.0,
    )
    working_l_values = l_values[working_fit_mask]
    holdout_indices = np.where((l_values > 0) & (~working_fit_mask))[0]
    holdout_l_values = l_values[holdout_indices]
    holdout_abs_delta_pos = np.abs(k_fit_merged["residuals"][holdout_indices]) if holdout_indices.size else np.asarray([], dtype=float)
    holdout_abs_delta_mhz = holdout_abs_delta_pos * fsr_final * 1000.0
    if holdout_indices.size == 1:
        holdout_idx = int(holdout_indices[0])
        holdout_l = int(l_values[holdout_idx])
        holdout_pos_meas = float(pos_meas[holdout_idx])
        holdout_pos_fit = float(k_fit_merged["predicted"][holdout_idx])
        holdout_abs_delta_pos_single = float(abs(k_fit_merged["residuals"][holdout_idx]))
        holdout_abs_delta_mhz_single = holdout_abs_delta_pos_single * fsr_final * 1000.0
    else:
        holdout_l = np.nan
        holdout_pos_meas = np.nan
        holdout_pos_fit = np.nan
        holdout_abs_delta_pos_single = np.nan
        holdout_abs_delta_mhz_single = np.nan

    ref_lambda_nm = merged_peaks[0]["lambda_center_nm"]
    ref_lambda_um = ref_lambda_nm / 1000.0
    n_room_sellmeier = fused_silica_index(ref_lambda_um, ROOM_TEMP_C)
    n_target = fused_silica_index(ref_lambda_um, TARGET_TEMP_C)
    n_malitson = malitson_index_20c(ref_lambda_um)
    cavity_params = derive_cavity_params(
        fsr_ghz=fsr_final,
        k=k_final,
        n_value=n_target,
        fsr_err_ghz=fsr_final_err,
        k_err=k_final_err,
    )

    cross_source_df, reference_validation_rows = _build_cross_source_validation(
        dataset_key=f"{dataset.key}_{source_kind}",
        primary_label=source_kind,
        reference_label=other_kind,
        primary_scans=primary_scans,
        reference_scans=reference_scans,
        branch_results=branch_results,
    )

    selected_primary_rows = [
        item
        for direction in ["Rising", "Falling"]
        for item in branch_results[direction].selected_candidates.values()
    ]
    peak_summary_rows = [peak_to_row(item, fsr_final) for item in all_primary_candidates]
    peak_summary_rows.extend(peak_to_row(item, fsr_final) for item in selected_primary_rows)
    peak_summary_rows.extend(peak_to_row(item, fsr_final) for item in reference_validation_rows)
    peak_fit_summary_df = pd.DataFrame(peak_summary_rows).sort_values(
        ["l", "scan_direction", "source", "selected", "candidate_rank"],
        ascending=[True, True, True, False, True],
    )

    selected_merged_df = pd.DataFrame(
        [
            {
                "l": l,
                "lambda_center_nm": merged_peaks[l]["lambda_center_nm"],
                "nu_center_ghz": merged_peaks[l]["nu_center_ghz"],
                "fwhm_ghz": merged_peaks[l]["fwhm_ghz"],
                "fwhm_nm": merged_peaks[l]["fwhm_nm"],
                "finesse": fsr_final / merged_peaks[l]["fwhm_ghz"],
                "falling_branch_shift_fsr": merged_peaks[l]["falling_branch_shift_fsr"],
                "rising_falling_lambda_diff_nm": merged_peaks[l]["lambda_center_diff_nm"],
                "rising_falling_fwhm_diff_ghz": merged_peaks[l]["fwhm_diff_ghz"],
            }
            for l in sorted(merged_peaks)
        ]
    )
    main_peak_positions_df = _selected_main_peak_positions(merged_peaks, global_fit_merged, k_fit_used_by_l)

    l0_row = selected_merged_df[selected_merged_df["l"] == 0].iloc[0]
    mode_finesse_stats = _mode_finesse_stats(selected_merged_df)
    all_finesse_mean, all_finesse_err = _weighted_mean(
        selected_merged_df["finesse"].to_numpy(dtype=float),
        np.maximum(selected_merged_df["rising_falling_fwhm_diff_ghz"].to_numpy(dtype=float), 1e-6),
    )

    k_summary_df = pd.DataFrame(
        [
            {
                "l": int(l),
                "fit_role": "reference" if int(l) == 0 else ("anchor" if working_fit_mask[i] else "holdout"),
                "used_in_k_relative_fit": bool(working_fit_mask[i]),
                "pos_meas": float(pos_meas[i]),
                "pos_fit": float(k_fit_merged["predicted"][i]),
                "residual": float(k_fit_merged["residuals"][i]),
                "residual_percent_fsr": float(k_fit_merged["residuals"][i] * 100.0),
                "residual_mhz": float(k_fit_merged["residuals"][i] * fsr_final * 1000.0),
                "m_l": int(global_fit_merged["m_indices"][int(l)]),
            }
            for i, l in enumerate(l_values)
        ]
    )

    fsr_estimates_rows = fsr_a["summary_df"].to_dict("records")
    for label, fit_result in [
        ("B_global_merged", global_fit_merged),
        ("B_global_rising", global_fit_by_direction["Rising"]),
        ("B_global_falling", global_fit_by_direction["Falling"]),
    ]:
        fsr_estimates_rows.append(
            {
                "dataset_key": f"{dataset.key}_{source_kind}",
                "method": label,
                "scan_direction": label.split("_")[-1],
                "fsr_ghz": fit_result["fsr_ghz"],
                "fsr_err_ghz": fit_result["fsr_err_ghz"],
                "peak1_lambda_nm": np.nan,
                "peak2_lambda_nm": np.nan,
                "peak1_nu_ghz": np.nan,
                "peak2_nu_ghz": np.nan,
            }
        )
    fsr_estimates_rows.append(
        {
            "dataset_key": f"{dataset.key}_{source_kind}",
            "method": "recommended",
            "scan_direction": fsr_choice,
            "fsr_ghz": fsr_final,
            "fsr_err_ghz": fsr_final_err,
            "peak1_lambda_nm": np.nan,
            "peak2_lambda_nm": np.nan,
            "peak1_nu_ghz": np.nan,
            "peak2_nu_ghz": np.nan,
        }
    )
    fsr_estimates_rows.append(
        {
            "dataset_key": f"{dataset.key}_{source_kind}",
            "method": "A_minus_B",
            "scan_direction": "difference",
            "fsr_ghz": fsr_a["combined_fsr_ghz"] - global_fit_merged["fsr_ghz"],
            "fsr_err_ghz": np.nan,
            "peak1_lambda_nm": np.nan,
            "peak2_lambda_nm": np.nan,
            "peak1_nu_ghz": np.nan,
            "peak2_nu_ghz": np.nan,
        }
    )
    fsr_estimates_df = pd.DataFrame(fsr_estimates_rows)

    cavity_summary_df = pd.DataFrame(
        [
            {
                "dataset_key": dataset.key,
                "analysis_source": source_kind,
                "analysis_source_label": source_cfg["display_name"],
                "reference_source": other_kind,
                "reference_peak_l": 0,
                "reference_peak_lambda_nm": ref_lambda_nm,
                "reference_peak_nu_ghz": merged_peaks[0]["nu_center_ghz"],
                "n_sellmeier_20p00C": n_room_sellmeier,
                "n_sellmeier_20p18C": n_target,
                "delta_n_temp_20p18_minus_20p00": n_target - n_room_sellmeier,
                "n_malitson_20C": n_malitson,
                "delta_n_sellmeier20_minus_malitson20": n_room_sellmeier - n_malitson,
                "fsr_method_A_ghz": fsr_a["combined_fsr_ghz"],
                "fsr_method_B_ghz": global_fit_merged["fsr_ghz"],
                "fsr_final_ghz": fsr_final,
                "fsr_final_err_ghz": fsr_final_err,
                "fwhm_l0_ghz": l0_row["fwhm_ghz"],
                "fwhm_l0_nm": l0_row["fwhm_nm"],
                "finesse_l0": l0_row["finesse"],
                "finesse_mode_l_min": mode_finesse_stats["l_min"],
                "finesse_mode_l_max": mode_finesse_stats["l_max"],
                "finesse_mode_count": mode_finesse_stats["count"],
                "finesse_mode_mean": mode_finesse_stats["mean"],
                "finesse_mode_sd": mode_finesse_stats["sd"],
                "finesse_mode_min": mode_finesse_stats["min"],
                "finesse_mode_max": mode_finesse_stats["max"],
                "finesse_all_weighted_mean": all_finesse_mean,
                "finesse_all_weighted_err": all_finesse_err,
                "k_relative_fit": k_final,
                "k_relative_fit_err": k_final_err,
                "k_relative_fit_mode_count": int(k_fit_merged["fit_mode_count"]),
                "k_relative_fit_fit_l_values": ",".join(str(int(l)) for l in working_l_values),
                "k_relative_fit_holdout_l_values": ",".join(str(int(l)) for l in holdout_l_values),
                "k_relative_fit_band_min": k_fit_merged["band_min"],
                "k_relative_fit_band_max": k_fit_merged["band_max"],
                "k_relative_fit_holdout_l": holdout_l,
                "k_relative_fit_holdout_pos_meas": holdout_pos_meas,
                "k_relative_fit_holdout_pos_fit": holdout_pos_fit,
                "k_relative_fit_holdout_abs_delta_pos": holdout_abs_delta_pos_single,
                "k_relative_fit_holdout_abs_delta_mhz": holdout_abs_delta_mhz_single,
                "k_relative_fit_holdout_abs_delta_pos_max": float(np.max(holdout_abs_delta_pos)) if holdout_abs_delta_pos.size else np.nan,
                "k_relative_fit_holdout_abs_delta_mhz_max": float(np.max(holdout_abs_delta_mhz)) if holdout_abs_delta_mhz.size else np.nan,
                "k_relative_fit_strategy": "reference l=0, fit l=1..8, hold out l=9",
                "k_joint_method_B": global_fit_merged["k"],
                "k_joint_method_B_err": global_fit_merged["k_err"],
                "k_joint_method_B_mode_count": int(max(len(l_values) - 1, 0)),
                "k_joint_method_B_band_min": global_fit_merged["k"] - global_fit_merged["k_err"] if np.isfinite(global_fit_merged["k_err"]) else np.nan,
                "k_joint_method_B_band_max": global_fit_merged["k"] + global_fit_merged["k_err"] if np.isfinite(global_fit_merged["k_err"]) else np.nan,
                "delta_k_relative_fit_minus_joint_method_B": k_final - global_fit_merged["k"],
                "L_mm": cavity_params["L_mm"],
                "L_err_mm": cavity_params["L_err_mm"],
                "L_over_R": cavity_params["L_over_R"],
                "L_over_R_err": cavity_params["L_over_R_err"],
                "R_mm": cavity_params["R_mm"],
                "R_err_mm": cavity_params["R_err_mm"],
                "baseline_L_mm": THESIS_BASELINE["L_mm"],
                "baseline_R_mm": THESIS_BASELINE["R_mm"],
                "baseline_k": THESIS_BASELINE["k"],
                "baseline_F": THESIS_BASELINE["F"],
                "delta_L_mm_vs_thesis": cavity_params["L_mm"] - THESIS_BASELINE["L_mm"],
                "delta_R_mm_vs_thesis": cavity_params["R_mm"] - THESIS_BASELINE["R_mm"],
                "delta_k_vs_thesis": k_final - THESIS_BASELINE["k"],
                "delta_F_vs_thesis": mode_finesse_stats["mean"] - THESIS_BASELINE["F"],
                "fsr_choice": fsr_choice,
                "fsr_choice_reason": "Method A selected because rising/falling direct FSR agree within 1%"
                if fsr_choice == "A_direct"
                else "Method B selected because direct FSR rising/falling mismatch exceeds 1%",
            }
        ]
    )

    output_subdir = OUTPUT_DIR / dataset.key / source_cfg["folder_name"]
    report_md = build_dataset_report(
        dataset_name=dataset.name,
        source_label=source_cfg["display_name"],
        cavity_summary=cavity_summary_df.iloc[0].to_dict(),
        cross_source_df=cross_source_df,
    )
    export_tables_and_plots(
        dataset_output_dir=output_subdir,
        tables={
            "peak_fit_summary.csv": peak_fit_summary_df,
            "fsr_estimates.csv": fsr_estimates_df,
            "k_fit_summary.csv": k_summary_df,
            "cavity_parameters_summary.csv": cavity_summary_df,
            "cross_source_comparison.csv": cross_source_df,
            "selected_peak_summary.csv": selected_merged_df,
            "main_peak_positions_summary.csv": main_peak_positions_df,
        },
        primary_scans=primary_scans,
        reference_scans=reference_scans,
        merged_peaks=merged_peaks,
        k_summary_df=k_summary_df,
        k_best=k_final,
        primary_label=source_kind,
        reference_label=other_kind,
    )
    (output_subdir / "report.md").write_text(report_md, encoding="utf-8")

    return {
        "dataset_key": dataset.key,
        "analysis_source": source_kind,
        "output_dir": output_subdir,
        "cavity_summary": cavity_summary_df,
        "fsr_estimates": fsr_estimates_df,
        "k_summary": k_summary_df,
        "cross_source_comparison": cross_source_df,
        "main_peak_positions": main_peak_positions_df,
    }


def build_dataset_report(dataset_name: str, source_label: str, cavity_summary: Dict[str, Any], cross_source_df: pd.DataFrame) -> str:
    cross_abs = cross_source_df[["delta_lambda_nm", "delta_fwhm_ghz"]].abs().mean()
    return f"""# {dataset_name} - {source_label}

## 主结果

- FSR(A) = {format_value(cavity_summary['fsr_method_A_ghz'], 6, ' GHz')}
- FSR(B) = {format_value(cavity_summary['fsr_method_B_ghz'], 6, ' GHz')}
- 最终 FSR = {format_value(cavity_summary['fsr_final_ghz'], 6, ' GHz')}
- `l=0` FWHM = {format_value(cavity_summary['fwhm_l0_ghz'] * 1000.0, 3, ' MHz')}
- 主精细度（`l={int(cavity_summary['finesse_mode_l_min'])}~{int(cavity_summary['finesse_mode_l_max'])}`，`n={int(cavity_summary['finesse_mode_count'])}`） = {format_value(cavity_summary['finesse_mode_mean'], 4)} ± {format_value(cavity_summary['finesse_mode_sd'], 4)}
- 模式间精细度范围 = {format_value(cavity_summary['finesse_mode_min'], 4)} ~ {format_value(cavity_summary['finesse_mode_max'], 4)}
- `l=0` 精细度（审计值） = {format_value(cavity_summary['finesse_l0'], 4)}
- `k（以 l=0 为参考、拟合 {cavity_summary['k_relative_fit_fit_l_values']}） = {format_value(cavity_summary['k_relative_fit'], 6)} ± {format_value(cavity_summary['k_relative_fit_err'], 6)}`
- `k` 局部低分带 = [{format_value(cavity_summary['k_relative_fit_band_min'], 6)}, {format_value(cavity_summary['k_relative_fit_band_max'], 6)}]
- 留出模式（`l={cavity_summary['k_relative_fit_holdout_l_values']}`）闭合偏差 = {format_value(cavity_summary['k_relative_fit_holdout_abs_delta_pos_max'], 6)} FSR = {format_value(cavity_summary['k_relative_fit_holdout_abs_delta_mhz_max'], 3, ' MHz')}
- `k（Method B，全模审计值） = {format_value(cavity_summary['k_joint_method_B'], 6)} ± {format_value(cavity_summary['k_joint_method_B_err'], 6)}`
- `n(20.18 °C) = {format_value(cavity_summary['n_sellmeier_20p18C'], 9)}`
- `L = {format_value(cavity_summary['L_mm'], 6, ' mm')}`
- `L/R = {format_value(cavity_summary['L_over_R'], 6)}`
- `R = {format_value(cavity_summary['R_mm'], 6, ' mm')}`

## 与另一数据源的交叉检查

- 当前主分析数据源：`{source_label}`
- 对照数据源：`{SOURCE_CONFIGS[cavity_summary['reference_source']]['display_name']}`
- 平均峰心差值 = {format_value(cross_abs['delta_lambda_nm'], 6, ' nm')}
- 平均 FWHM 差值 = {format_value(cross_abs['delta_fwhm_ghz'] * 1000.0, 3, ' MHz')}

## 与正文当前参数比较

- 正文基线：`L = 10.25 mm`，`R = 25.0 mm`，`k ≈ 0.221`，`F ≈ 29.8`
- `ΔL = {format_value(cavity_summary['delta_L_mm_vs_thesis'], 6, ' mm')}`
- `ΔR = {format_value(cavity_summary['delta_R_mm_vs_thesis'], 6, ' mm')}`
- `Δk = {format_value(cavity_summary['delta_k_vs_thesis'], 6)}`
- `ΔF = {format_value(cavity_summary['delta_F_vs_thesis'], 4)}`
"""


def build_final_report(comparison_df: pd.DataFrame) -> str:
    lines = ["# 四套独立分析结果汇总", "", "## 主结果表", ""]
    for _, row in comparison_df.iterrows():
        lines.append(
            f"- `{row['dataset_key']} / {row['analysis_source_label']}`: "
            f"FSR={format_value(row['fsr_final_ghz'], 6, ' GHz')}，"
            f"F(l={int(row['finesse_mode_l_min'])}~{int(row['finesse_mode_l_max'])})="
            f"{format_value(row['finesse_mode_mean'], 4)} ± {format_value(row['finesse_mode_sd'], 4)}，"
            f"k={format_value(row['k_relative_fit'], 6)}，"
            f"L={format_value(row['L_mm'], 6, ' mm')}，"
            f"R={format_value(row['R_mm'], 6, ' mm')}"
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 每套光腰数据都分别对原始数据和 FSR 补全后数据独立跑了一遍。",
            "- 各自的主峰位置汇总表见对应目录下的 `main_peak_positions_summary.csv`。",
            "- 此处报告的 `k_relative_fit` 统一采用“以 `l=0` 为参考、由 `l=1..8` 锁定工作点、将 `l=9` 留作闭合检验”的口径。",
            "- `k_joint_method_B` 仍保留为全模 Method B 审计值，用于和工作点口径交叉核对。",
            "- 总对比表已把四套独立结果都列入，便于直接比较“原始 vs 补全”以及“0.88 vs 0.98”。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    datasets = discover_datasets(BASE_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results: List[Dict[str, Any]] = []
    for dataset in datasets.values():
        for source_kind in ["raw", "final"]:
            all_results.append(_analyze_dataset_source(dataset, source_kind))

    comparison_rows = [result["cavity_summary"].iloc[0].to_dict() for result in all_results]
    comparison_df = pd.DataFrame(comparison_rows)
    save_csv(comparison_df, OUTPUT_DIR / "final_cavity_parameter_comparison.csv")
    (OUTPUT_DIR / "final_report.md").write_text(build_final_report(comparison_df), encoding="utf-8")
    print("Completed cavity recalculation for 4 analysis branches.")


if __name__ == "__main__":
    main()
