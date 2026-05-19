from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


ANALYTIC_K = 2.0 / 9.0
SPEED_OF_LIGHT_NM_GHZ = 299792458.0
EXPERIMENT_SMOOTH_WINDOW = 9
RISING_DISPLAY_NORM_L0 = 0.9289
RISING_DISPLAY_NORM_L9 = 0.8154


def default_input_csv(script_dir: Path) -> Path:
    return (
        script_dir.parent
        / "outputs"
        / "0p88mm"
        / "原始数据分析结果"
        / "theory_position_validation.csv"
    )


def default_summary_csv(script_dir: Path) -> Path:
    return (
        script_dir.parent
        / "outputs"
        / "0p88mm"
        / "原始数据分析结果"
        / "theory_position_validation_summary.csv"
    )


def default_main_peaks_csv(script_dir: Path) -> Path:
    return (
        script_dir.parent
        / "outputs"
        / "0p88mm"
        / "原始数据分析结果"
        / "main_peak_positions_summary.csv"
    )


def default_peak_fit_csv(script_dir: Path) -> Path:
    return (
        script_dir.parent
        / "outputs"
        / "0p88mm"
        / "原始数据分析结果"
        / "peak_fit_summary.csv"
    )


def default_raw_l0_csv(script_dir: Path) -> Path:
    return (
        script_dir.parent
        / "光腰为0.88mm测得数据"
        / "原始数据"
        / "DATA70_l0_symmetrized.csv"
    )


def default_raw_l9_csv(script_dir: Path) -> Path:
    return (
        script_dir.parent
        / "光腰为0.88mm测得数据"
        / "原始数据"
        / "DATA79_l9_symmetrized.csv"
    )


def default_cavity_summary_csv(script_dir: Path) -> Path:
    return (
        script_dir.parent
        / "outputs"
        / "0p88mm"
        / "原始数据分析结果"
        / "cavity_parameters_summary.csv"
    )


def default_output_dir(script_dir: Path) -> Path:
    return script_dir / "10模输出图"


def configure_plot_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIX Two Text", "Times New Roman", "STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8.8,
            "axes.labelsize": 10,
            "axes.titlesize": 10.0,
            "axes.linewidth": 0.8,
            "xtick.labelsize": 8.6,
            "ytick.labelsize": 8.6,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.size": 3.3,
            "ytick.major.size": 3.3,
            "xtick.major.width": 0.75,
            "ytick.major.width": 0.75,
            "xtick.top": True,
            "ytick.right": True,
            "legend.frameon": False,
            "legend.fontsize": 8.4,
            "figure.dpi": 150,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Create publication-style validation and l=0/l=9 collision plots."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=default_input_csv(script_dir),
        help="Path to theory_position_validation.csv",
    )
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=default_summary_csv(script_dir),
        help="Path to theory_position_validation_summary.csv",
    )
    parser.add_argument(
        "--main-peaks-csv",
        type=Path,
        default=default_main_peaks_csv(script_dir),
        help="Path to main_peak_positions_summary.csv",
    )
    parser.add_argument(
        "--peak-fit-csv",
        type=Path,
        default=default_peak_fit_csv(script_dir),
        help="Path to peak_fit_summary.csv",
    )
    parser.add_argument(
        "--raw-l0-csv",
        type=Path,
        default=default_raw_l0_csv(script_dir),
        help="Path to the raw symmetrized CSV for l=0.",
    )
    parser.add_argument(
        "--raw-l9-csv",
        type=Path,
        default=default_raw_l9_csv(script_dir),
        help="Path to the raw symmetrized CSV for l=9.",
    )
    parser.add_argument(
        "--cavity-summary-csv",
        type=Path,
        default=default_cavity_summary_csv(script_dir),
        help="Path to cavity_parameters_summary.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(script_dir),
        help="Directory to save the figures and tables.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Output DPI for PNG export.",
    )
    return parser.parse_args()


def validate_inputs(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing input files:\n" + "\n".join(missing))


def export_figure(fig: plt.Figure, output_dir: Path, stem: str, dpi: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / f"{stem}.pdf")
    fig.savefig(output_dir / f"{stem}.png", dpi=dpi)
    plt.close(fig)


def lorentz_profile(nu_mhz: np.ndarray, center_mhz: float, fwhm_mhz: float) -> np.ndarray:
    return 1.0 / (1.0 + 4.0 * ((nu_mhz - center_mhz) / fwhm_mhz) ** 2)


def wavelength_nm_to_frequency_ghz(wavelength_nm: np.ndarray) -> np.ndarray:
    return SPEED_OF_LIGHT_NM_GHZ / wavelength_nm


def load_position_data(
    input_csv: Path,
    summary_csv: Path,
    main_peaks_csv: Path,
    peak_fit_csv: Path,
    cavity_summary_csv: Path,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series]:
    detail_df = pd.read_csv(input_csv).sort_values("l").reset_index(drop=True)
    summary_df = pd.read_csv(summary_csv)
    main_peaks_df = pd.read_csv(main_peaks_csv).sort_values("l").reset_index(drop=True)
    peak_fit_df = pd.read_csv(peak_fit_csv)
    cavity_df = pd.read_csv(cavity_summary_csv)

    merged_summary = summary_df.loc[summary_df["measurement_type"] == "merged"]
    if merged_summary.empty:
        raise ValueError("Summary CSV does not contain a merged row.")

    final_rows = peak_fit_df.loc[
        (peak_fit_df["source"] == "final")
        & (peak_fit_df["selected"].astype(str).str.lower() == "true")
    ].copy()
    if final_rows.empty:
        raise ValueError("peak_fit_summary.csv does not contain selected final rows.")

    linewidth_df = (
        final_rows.groupby("l", as_index=False)
        .agg(
            fwhm_ghz_mean=("fwhm_ghz", "mean"),
            fwhm_ghz_std=("fwhm_ghz", "std"),
            finesse_mean=("finesse_with_final_fsr", "mean"),
            rising_falling_count=("scan_direction", "count"),
        )
        .sort_values("l")
        .reset_index(drop=True)
    )
    linewidth_df["fwhm_mhz_mean"] = linewidth_df["fwhm_ghz_mean"] * 1000.0
    linewidth_df["fwhm_mhz_std"] = linewidth_df["fwhm_ghz_std"].fillna(0.0) * 1000.0

    cavity_row = cavity_df.iloc[0]
    return detail_df, merged_summary.iloc[0], main_peaks_df, linewidth_df, final_rows, cavity_row


def build_per_mode_metrics(
    detail_df: pd.DataFrame,
    main_peaks_df: pd.DataFrame,
    linewidth_df: pd.DataFrame,
) -> pd.DataFrame:
    merged = detail_df.merge(
        main_peaks_df[["l", "merged_lambda_nm", "merged_nu_ghz"]],
        on="l",
        how="left",
        suffixes=("", "_main"),
    ).merge(
        linewidth_df[["l", "fwhm_mhz_mean", "fwhm_mhz_std", "finesse_mean"]],
        on="l",
        how="left",
    )

    merged["delta_pos_signed_fsr"] = merged["delta_pos_merged"]
    merged["delta_pos_abs_fsr"] = merged["delta_pos_merged_abs"]
    merged["delta_pos_signed_percent_fsr"] = merged["delta_pos_merged_percent_fsr"]
    merged["delta_pos_abs_percent_fsr"] = merged["delta_pos_merged_abs"] * 100.0
    merged["delta_nu_signed_mhz"] = merged["delta_nu_merged_mhz"]
    merged["delta_nu_abs_mhz"] = merged["delta_nu_merged_mhz"].abs()
    merged["delta_over_fwhm_signed"] = merged["delta_nu_signed_mhz"] / merged["fwhm_mhz_mean"]
    merged["delta_over_fwhm_abs"] = merged["delta_nu_abs_mhz"] / merged["fwhm_mhz_mean"]

    columns = [
        "l",
        "pos_theory_2_over_9",
        "pos_meas_merged",
        "delta_pos_signed_fsr",
        "delta_pos_abs_fsr",
        "delta_pos_signed_percent_fsr",
        "delta_pos_abs_percent_fsr",
        "delta_nu_signed_mhz",
        "delta_nu_abs_mhz",
        "merged_lambda_nm",
        "merged_nu_ghz",
        "fwhm_mhz_mean",
        "fwhm_mhz_std",
        "finesse_mean",
        "delta_over_fwhm_signed",
        "delta_over_fwhm_abs",
    ]
    return merged[columns].copy()


def build_overlap_curves_and_metrics(
    per_mode_df: pd.DataFrame,
    cavity_row: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    row0 = per_mode_df.loc[per_mode_df["l"] == 0].iloc[0]
    row9 = per_mode_df.loc[per_mode_df["l"] == 9].iloc[0]

    fsr_mhz = float(cavity_row["fsr_final_ghz"]) * 1000.0
    nu0_mhz = float(row0["merged_nu_ghz"]) * 1000.0
    nu9_mhz = float(row9["merged_nu_ghz"]) * 1000.0
    fwhm0_mhz = float(row0["fwhm_mhz_mean"])
    fwhm9_mhz = float(row9["fwhm_mhz_mean"])

    center_mean_mhz = 0.5 * (nu0_mhz + nu9_mhz)
    span_mhz = max(4.0 * max(fwhm0_mhz, fwhm9_mhz), abs(nu9_mhz - nu0_mhz) + 3.5 * max(fwhm0_mhz, fwhm9_mhz))
    axis_mhz = np.linspace(center_mean_mhz - span_mhz, center_mean_mhz + span_mhz, 4001)
    axis_mhz = np.sort(np.unique(np.concatenate([axis_mhz, np.array([nu0_mhz, nu9_mhz])])))
    detuning_from_l0_mhz = axis_mhz - nu0_mhz
    detuning_from_l0_fsr = detuning_from_l0_mhz / fsr_mhz

    t0 = lorentz_profile(axis_mhz, nu0_mhz, fwhm0_mhz)
    t9 = lorentz_profile(axis_mhz, nu9_mhz, fwhm9_mhz)
    overlap = np.minimum(t0, t9)

    curve_df = pd.DataFrame(
        {
            "detuning_from_l0_peak_mhz": detuning_from_l0_mhz,
            "detuning_from_l0_peak_fsr": detuning_from_l0_fsr,
            "T_l0": t0,
            "T_l9": t9,
            "T_overlap_min": overlap,
        }
    )

    overlap_area_mhz = float(np.trapezoid(overlap, axis_mhz))
    single_area_l0_mhz = float(np.pi * fwhm0_mhz / 2.0)
    single_area_l9_mhz = float(np.pi * fwhm9_mhz / 2.0)
    separation_mhz = abs(nu9_mhz - nu0_mhz)
    separation_fsr = separation_mhz / fsr_mhz
    t9_at_l0 = float(lorentz_profile(np.array([nu0_mhz]), nu9_mhz, fwhm9_mhz)[0])
    t0_at_l9 = float(lorentz_profile(np.array([nu9_mhz]), nu0_mhz, fwhm0_mhz)[0])

    metrics_df = pd.DataFrame(
        [
            {
                "mode_pair": "l0_vs_l9",
                "nu_l0_ghz": nu0_mhz / 1000.0,
                "nu_l9_ghz": nu9_mhz / 1000.0,
                "delta_nu_mhz": separation_mhz,
                "delta_pos_fsr": separation_fsr,
                "fwhm_l0_mhz": fwhm0_mhz,
                "fwhm_l9_mhz": fwhm9_mhz,
                "delta_over_fwhm_l0": separation_mhz / fwhm0_mhz,
                "delta_over_fwhm_l9": separation_mhz / fwhm9_mhz,
                "relative_transmission_l9_at_l0_peak": t9_at_l0,
                "relative_transmission_l0_at_l9_peak": t0_at_l9,
                "single_peak_area_l0_mhz": single_area_l0_mhz,
                "single_peak_area_l9_mhz": single_area_l9_mhz,
                "overlap_area_mhz": overlap_area_mhz,
                "overlap_over_area_l0": overlap_area_mhz / single_area_l0_mhz,
                "overlap_over_area_l9": overlap_area_mhz / single_area_l9_mhz,
            }
        ]
    )
    return curve_df, metrics_df


def extract_mode_segments(
    raw_csv: Path,
    peak_fit_df: pd.DataFrame,
    main_peaks_df: pd.DataFrame,
    cavity_row: pd.Series,
    mode_l: int,
    scan_direction: str | None = None,
) -> tuple[list[pd.DataFrame], float]:
    raw_df = pd.read_csv(raw_csv)
    raw_df["Scan_Direction"] = raw_df["Scan_Direction"].astype(str)
    raw_df["Lambda_aligned"] = raw_df["Lambda_aligned"].astype(float)
    raw_df["Power_uW"] = raw_df["Power_uW"].astype(float)

    peak_rows = peak_fit_df.loc[peak_fit_df["l"] == mode_l].copy()
    if scan_direction is not None:
        peak_rows = peak_rows.loc[peak_rows["scan_direction"].astype(str).str.lower() == scan_direction.lower()]
    if peak_rows.empty:
        raise ValueError(f"No selected final peak-fit rows found for l={mode_l}.")

    merged_center_ghz = float(main_peaks_df.loc[main_peaks_df["l"] == mode_l, "merged_nu_ghz"].iloc[0])
    fsr_ghz = float(cavity_row["fsr_final_ghz"])

    segment_frames: list[pd.DataFrame] = []
    aligned_centers: list[float] = []

    for _, peak_row in peak_rows.iterrows():
        direction = str(peak_row["scan_direction"])
        seg = raw_df.loc[
            (raw_df["Scan_Direction"].str.lower() == direction.lower())
            & (raw_df["Lambda_aligned"] >= float(peak_row["window_lambda_min_nm"]))
            & (raw_df["Lambda_aligned"] <= float(peak_row["window_lambda_max_nm"]))
        ].copy()
        if seg.empty:
            continue

        seg["nu_ghz"] = wavelength_nm_to_frequency_ghz(seg["Lambda_aligned"].to_numpy(dtype=float))
        fitted_center_ghz = float(peak_row["nu_center_ghz"])
        branch_shift_fsr = int(round((merged_center_ghz - fitted_center_ghz) / fsr_ghz))
        seg["nu_aligned_ghz"] = seg["nu_ghz"] + branch_shift_fsr * fsr_ghz

        baseline_uw = float(peak_row["baseline_uw"])
        peak_power_uw = float(peak_row["peak_power_uw"])
        scale_uw = max(peak_power_uw - baseline_uw, 1e-12)
        seg["transmission_norm"] = (seg["Power_uW"] - baseline_uw) / scale_uw
        seg["transmission_norm"] = seg["transmission_norm"].clip(lower=0.0, upper=1.05)

        aligned_center_ghz = fitted_center_ghz + branch_shift_fsr * fsr_ghz
        segment_frames.append(
            seg.assign(aligned_center_ghz=aligned_center_ghz)[
                ["nu_aligned_ghz", "transmission_norm", "aligned_center_ghz"]
            ].copy()
        )
        aligned_centers.append(aligned_center_ghz)

    if not segment_frames:
        raise ValueError(f"No raw points were found inside the selected peak windows for l={mode_l}.")

    return segment_frames, float(np.mean(aligned_centers))


def extract_single_mode_segment(
    raw_csv: Path,
    peak_fit_df: pd.DataFrame,
    main_peaks_df: pd.DataFrame,
    cavity_row: pd.Series,
    mode_l: int,
    scan_direction: str,
) -> tuple[pd.DataFrame, float]:
    raw_df = pd.read_csv(raw_csv)
    raw_df["Scan_Direction"] = raw_df["Scan_Direction"].astype(str)
    raw_df["Lambda_aligned"] = raw_df["Lambda_aligned"].astype(float)
    raw_df["Power_uW"] = raw_df["Power_uW"].astype(float)

    peak_rows = peak_fit_df.loc[
        (peak_fit_df["l"] == mode_l)
        & (peak_fit_df["scan_direction"].astype(str).str.lower() == scan_direction.lower())
    ].copy()
    if peak_rows.empty:
        raise ValueError(f"No selected final {scan_direction} row found for l={mode_l}.")
    peak_row = peak_rows.iloc[0]

    merged_center_ghz = float(main_peaks_df.loc[main_peaks_df["l"] == mode_l, "merged_nu_ghz"].iloc[0])
    fsr_ghz = float(cavity_row["fsr_final_ghz"])
    fitted_center_ghz = float(peak_row["nu_center_ghz"])
    branch_shift_fsr = int(round((merged_center_ghz - fitted_center_ghz) / fsr_ghz))
    aligned_center_ghz = fitted_center_ghz + branch_shift_fsr * fsr_ghz

    edge_nu_ghz = wavelength_nm_to_frequency_ghz(
        np.array(
            [
                float(peak_row["window_lambda_min_nm"]),
                float(peak_row["window_lambda_max_nm"]),
            ],
            dtype=float,
        )
    ) + branch_shift_fsr * fsr_ghz
    half_span_ghz = float(np.max(np.abs(edge_nu_ghz - aligned_center_ghz)))

    direction_df = raw_df.loc[raw_df["Scan_Direction"].str.lower() == scan_direction.lower()].copy()
    direction_df["nu_ghz"] = wavelength_nm_to_frequency_ghz(direction_df["Lambda_aligned"].to_numpy(dtype=float))
    direction_df["nu_aligned_ghz"] = direction_df["nu_ghz"] + branch_shift_fsr * fsr_ghz
    seg = direction_df.loc[
        (direction_df["nu_aligned_ghz"] >= aligned_center_ghz - half_span_ghz)
        & (direction_df["nu_aligned_ghz"] <= aligned_center_ghz + half_span_ghz)
    ].copy()
    if seg.empty:
        raise ValueError(f"No raw points found in the symmetric {scan_direction} window for l={mode_l}.")

    baseline_uw = float(peak_row["baseline_uw"])
    peak_power_uw = float(peak_row["peak_power_uw"])
    scale_uw = max(peak_power_uw - baseline_uw, 1e-12)
    seg["transmission_norm"] = (seg["Power_uW"] - baseline_uw) / scale_uw
    seg["transmission_norm"] = seg["transmission_norm"].clip(lower=0.0, upper=1.05)

    return (
        seg.assign(aligned_center_ghz=aligned_center_ghz)[
            ["nu_aligned_ghz", "transmission_norm", "aligned_center_ghz"]
        ].copy(),
        aligned_center_ghz,
    )


def smooth_curve_with_nan(curve: np.ndarray, window: int = EXPERIMENT_SMOOTH_WINDOW) -> np.ndarray:
    if window <= 1:
        return curve.copy()

    if window % 2 == 0:
        window += 1

    kernel = np.ones(window, dtype=float)
    valid = np.isfinite(curve).astype(float)
    filled = np.where(np.isfinite(curve), curve, 0.0)
    numerator = np.convolve(filled, kernel, mode="same")
    denominator = np.convolve(valid, kernel, mode="same")
    return np.divide(
        numerator,
        denominator,
        out=np.full_like(curve, np.nan, dtype=float),
        where=denominator > 0,
    )


def build_smoothed_envelope_segments(
    segment_frames: list[pd.DataFrame],
    x_local_grid_mhz: np.ndarray,
) -> np.ndarray:
    sampled_curves: list[np.ndarray] = []
    zero_idx = int(np.argmin(np.abs(x_local_grid_mhz)))

    for segment_df in segment_frames:
        aligned_center_ghz = float(segment_df["aligned_center_ghz"].iloc[0])
        x_mhz = (segment_df["nu_aligned_ghz"].to_numpy(dtype=float) - aligned_center_ghz) * 1000.0
        y_norm = segment_df["transmission_norm"].to_numpy(dtype=float)
        x_mhz = np.concatenate([x_mhz, np.array([0.0])])
        y_norm = np.concatenate([y_norm, np.array([1.0])])
        order = np.argsort(x_mhz)
        ordered = pd.DataFrame({"x_mhz": x_mhz[order], "y_norm": y_norm[order]})
        averaged = ordered.groupby("x_mhz", as_index=False).mean()
        interpolated = np.interp(
            x_local_grid_mhz,
            averaged["x_mhz"].to_numpy(dtype=float),
            averaged["y_norm"].to_numpy(dtype=float),
            left=np.nan,
            right=np.nan,
        )
        smoothed = smooth_curve_with_nan(interpolated)
        smoothed[zero_idx] = 1.0
        sampled_curves.append(smoothed)

    curve_stack = np.vstack(sampled_curves)
    valid_counts = np.sum(np.isfinite(curve_stack), axis=0)
    masked = np.where(np.isfinite(curve_stack), curve_stack, -np.inf)
    envelope = np.max(masked, axis=0)
    envelope[valid_counts == 0] = np.nan
    envelope[zero_idx] = 1.0
    return envelope


def build_experimental_overlap_curves(
    raw_l0_csv: Path,
    raw_l9_csv: Path,
    peak_fit_df: pd.DataFrame,
    main_peaks_df: pd.DataFrame,
    cavity_row: pd.Series,
) -> tuple[pd.DataFrame, dict[str, float]]:
    segments_l0, center_l0_ghz = extract_mode_segments(raw_l0_csv, peak_fit_df, main_peaks_df, cavity_row, mode_l=0)
    segments_l9, center_l9_ghz = extract_mode_segments(raw_l9_csv, peak_fit_df, main_peaks_df, cavity_row, mode_l=9)

    all_local_detuning_mhz: list[np.ndarray] = []
    for segment_df in segments_l0 + segments_l9:
        aligned_center_ghz = float(segment_df["aligned_center_ghz"].iloc[0])
        local_detuning_mhz = (segment_df["nu_aligned_ghz"].to_numpy(dtype=float) - aligned_center_ghz) * 1000.0
        all_local_detuning_mhz.append(local_detuning_mhz)

    local_x_min = min(float(np.min(arr)) for arr in all_local_detuning_mhz)
    local_x_max = max(float(np.max(arr)) for arr in all_local_detuning_mhz)
    delta_mhz = (center_l9_ghz - center_l0_ghz) * 1000.0
    local_grid_mhz = np.linspace(local_x_min, local_x_max, 1801)
    local_grid_mhz = np.sort(np.unique(np.concatenate([local_grid_mhz, np.array([0.0])])))

    canonical_l0 = build_smoothed_envelope_segments(segments_l0, local_grid_mhz)
    canonical_l9 = build_smoothed_envelope_segments(segments_l9, local_grid_mhz)

    x_plot_min = min(local_x_min, delta_mhz + local_x_min)
    x_plot_max = max(local_x_max, delta_mhz + local_x_max)
    x_plot_mhz = np.linspace(x_plot_min, x_plot_max, 2401)
    x_plot_mhz = np.sort(np.unique(np.concatenate([x_plot_mhz, np.array([0.0, delta_mhz])])))

    t0_exp = np.interp(x_plot_mhz, local_grid_mhz, canonical_l0, left=np.nan, right=np.nan)
    t9_exp = np.interp(x_plot_mhz - delta_mhz, local_grid_mhz, canonical_l9, left=np.nan, right=np.nan)

    valid_mask = np.isfinite(t0_exp) & np.isfinite(t9_exp)
    x_valid = x_plot_mhz[valid_mask]
    t0_valid = t0_exp[valid_mask]
    t9_valid = t9_exp[valid_mask]
    overlap_valid = np.minimum(t0_valid, t9_valid)

    curve_df = pd.DataFrame(
        {
            "detuning_from_l0_peak_mhz": x_valid,
            "T_l0_exp": t0_valid,
            "T_l9_exp": t9_valid,
            "T_overlap_min_exp": overlap_valid,
        }
    )
    metrics = {
        "delta_nu_mhz": float(delta_mhz),
        "t0_at_l0": float(np.interp(0.0, x_valid, t0_valid)),
        "t9_at_l0": float(np.interp(0.0, x_valid, t9_valid)),
    }
    return curve_df, metrics


def build_single_segment_curve(
    segment_df: pd.DataFrame,
    x_local_grid_mhz: np.ndarray,
    *,
    smooth: bool,
) -> np.ndarray:
    aligned_center_ghz = float(segment_df["aligned_center_ghz"].iloc[0])
    x_mhz = (segment_df["nu_aligned_ghz"].to_numpy(dtype=float) - aligned_center_ghz) * 1000.0
    y_norm = segment_df["transmission_norm"].to_numpy(dtype=float)
    order = np.argsort(x_mhz)
    ordered = pd.DataFrame({"x_mhz": x_mhz[order], "y_norm": y_norm[order]})
    averaged = ordered.groupby("x_mhz", as_index=False).mean()
    curve = np.interp(
        x_local_grid_mhz,
        averaged["x_mhz"].to_numpy(dtype=float),
        averaged["y_norm"].to_numpy(dtype=float),
        left=np.nan,
        right=np.nan,
    )
    if not smooth:
        return curve

    curve = smooth_curve_with_nan(curve)
    return curve


def scale_curve_to_target_peak(curve: np.ndarray, target_peak: float) -> np.ndarray:
    finite_mask = np.isfinite(curve)
    if not np.any(finite_mask):
        return curve

    peak_value = float(np.nanmax(curve[finite_mask]))
    if not np.isfinite(peak_value) or peak_value <= 1e-12:
        return curve
    return curve / peak_value * target_peak


def build_rising_experimental_overlap_curves(
    raw_l0_csv: Path,
    raw_l9_csv: Path,
    peak_fit_df: pd.DataFrame,
    main_peaks_df: pd.DataFrame,
    cavity_row: pd.Series,
    *,
    smooth: bool,
) -> tuple[pd.DataFrame, dict[str, float]]:
    seg_l0, center_l0_ghz = extract_single_mode_segment(
        raw_csv=raw_l0_csv,
        peak_fit_df=peak_fit_df,
        main_peaks_df=main_peaks_df,
        cavity_row=cavity_row,
        mode_l=0,
        scan_direction="Rising",
    )
    seg_l9, center_l9_ghz = extract_single_mode_segment(
        raw_csv=raw_l9_csv,
        peak_fit_df=peak_fit_df,
        main_peaks_df=main_peaks_df,
        cavity_row=cavity_row,
        mode_l=9,
        scan_direction="Rising",
    )

    local_detuning_l0 = (seg_l0["nu_aligned_ghz"].to_numpy(dtype=float) - float(seg_l0["aligned_center_ghz"].iloc[0])) * 1000.0
    local_detuning_l9 = (seg_l9["nu_aligned_ghz"].to_numpy(dtype=float) - float(seg_l9["aligned_center_ghz"].iloc[0])) * 1000.0
    local_x_min = min(float(np.min(local_detuning_l0)), float(np.min(local_detuning_l9)))
    local_x_max = max(float(np.max(local_detuning_l0)), float(np.max(local_detuning_l9)))
    delta_mhz = (center_l9_ghz - center_l0_ghz) * 1000.0

    local_grid_mhz = np.linspace(local_x_min, local_x_max, 1801)
    local_grid_mhz = np.sort(np.unique(np.concatenate([local_grid_mhz, np.array([0.0])])))

    canonical_l0 = build_single_segment_curve(seg_l0, local_grid_mhz, smooth=smooth)
    canonical_l9 = build_single_segment_curve(seg_l9, local_grid_mhz, smooth=smooth)

    x_plot_min = min(local_x_min, delta_mhz + local_x_min)
    x_plot_max = max(local_x_max, delta_mhz + local_x_max)
    x_plot_mhz = np.linspace(x_plot_min, x_plot_max, 2401)
    x_plot_mhz = np.sort(np.unique(np.concatenate([x_plot_mhz, np.array([0.0, delta_mhz])])))

    t0_exp = np.interp(x_plot_mhz, local_grid_mhz, canonical_l0, left=np.nan, right=np.nan)
    t9_exp = np.interp(x_plot_mhz - delta_mhz, local_grid_mhz, canonical_l9, left=np.nan, right=np.nan)

    t0_exp = scale_curve_to_target_peak(t0_exp, RISING_DISPLAY_NORM_L0)
    t9_exp = scale_curve_to_target_peak(t9_exp, RISING_DISPLAY_NORM_L9)

    both_valid = np.isfinite(t0_exp) & np.isfinite(t9_exp)
    overlap_exp = np.where(both_valid, np.minimum(t0_exp, t9_exp), np.nan)

    suffix = "smooth" if smooth else "raw"
    curve_df = pd.DataFrame(
        {
            "detuning_from_l0_peak_mhz": x_plot_mhz,
            f"T_l0_exp_rising_{suffix}": t0_exp,
            f"T_l9_exp_rising_{suffix}": t9_exp,
            f"T_overlap_min_exp_rising_{suffix}": overlap_exp,
        }
    )
    t0_mask = np.isfinite(t0_exp)
    t9_mask = np.isfinite(t9_exp)
    metrics = {
        "delta_nu_mhz": float(delta_mhz),
        "t0_at_l0": float(np.interp(0.0, x_plot_mhz[t0_mask], t0_exp[t0_mask])),
        "t9_at_l0": float(np.interp(0.0, x_plot_mhz[t9_mask], t9_exp[t9_mask])),
        "curve_suffix": suffix,
        "display_norm_l0": RISING_DISPLAY_NORM_L0,
        "display_norm_l9": RISING_DISPLAY_NORM_L9,
    }
    return curve_df, metrics


def build_stats_text(summary_row: pd.Series) -> str:
    rms = float(summary_row["rms_delta_percent_fsr"])
    max_abs = float(summary_row["max_abs_delta_percent_fsr"])
    worst_l = int(summary_row["worst_l"])
    closure = float(summary_row["closure_l9_abs_delta_pos"]) * 100.0
    return "\n".join(
        [
            r"$k_{\mathrm{th}} = 2/9$",
            f"Experiment RMS = {rms:.3f}% FSR",
            f"Experiment max = {max_abs:.3f}% FSR at $l={worst_l}$",
            f"Closure at $l=9$ = {closure:.3f}% FSR",
        ]
    )


def build_overlap_text(metrics_row: pd.Series) -> str:
    return "\n".join(
        [
            rf"$\Delta \nu_{{0,9}} = {metrics_row['delta_nu_mhz']:.2f}$ MHz",
            rf"$\Delta/\mathrm{{FSR}} = {metrics_row['delta_pos_fsr'] * 100:.3f}$%",
            rf"$\Delta/\mathrm{{FWHM}}_0 = {metrics_row['delta_over_fwhm_l0']:.4f}$",
            rf"$\Delta/\mathrm{{FWHM}}_9 = {metrics_row['delta_over_fwhm_l9']:.4f}$",
            r"$T_0(\nu_0) = 1.0000$",
            rf"$T_9(\nu_0) = {metrics_row['relative_transmission_l9_at_l0_peak']:.4f}$",
        ]
    )


def plot_polar_positions(plot_df: pd.DataFrame, output_dir: Path, dpi: int) -> None:
    theory_theta = 2.0 * np.pi * plot_df["pos_theory_2_over_9"].to_numpy(dtype=float)
    exp_theta = 2.0 * np.pi * plot_df["pos_meas_merged"].to_numpy(dtype=float)
    l_values = plot_df["l"].to_numpy(dtype=int)

    fig = plt.figure(figsize=(4.80, 4.55))
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_rlim(0.0, 1.25)
    ax.set_rticks([])
    ax.set_thetagrids([])
    ax.spines["polar"].set_visible(False)

    theta_ring = np.linspace(0, 2 * np.pi, 300)
    ax.plot(theta_ring, np.ones_like(theta_ring), color="#94a3b8", linewidth=1.0, zorder=1)

    for angle, label in zip(theory_theta, l_values):
        ax.plot([angle, angle], [0.93, 1.07], color="#334155", linewidth=1.5, linestyle="--", alpha=0.6, zorder=2)
        # Avoid drawing text for l=9 here, we will do it custom to prevent overlap with l=0
        if label != 9:
            ax.text(angle, 1.15, f"$l={label}$", ha="center", va="center", fontsize=8.5, color="#1e293b")

    # Add custom text for l=9 slightly offset to prevent overlap
    theta_9_theory = theory_theta[l_values == 9][0]
    ax.text(theta_9_theory + 0.15, 1.15, "$l=9$", ha="left", va="center", fontsize=8.5, color="#b91c1c")

    highlight_mask = l_values == 9
    ax.scatter(
        exp_theta[~highlight_mask],
        np.full(np.count_nonzero(~highlight_mask), 1.00),
        s=60,
        facecolors="none",
        edgecolors="#0f766e",
        linewidths=1.5,
        zorder=4,
    )
    ax.scatter(
        exp_theta[highlight_mask],
        np.full(np.count_nonzero(highlight_mask), 1.00),
        s=120,
        color="#b91c1c",
        marker="*",
        edgecolors="white",
        linewidths=0.5,
        zorder=5,
    )

    from matplotlib.lines import Line2D

    custom_lines = [
        Line2D([0], [0], color="#334155", linewidth=1.5, linestyle="--", label="Theory (2/9 branch)"),
        Line2D([0], [0], marker="o", color="none", markeredgecolor="#0f766e", markersize=7, markeredgewidth=1.5, label=r"Experiment ($l=0 \dots 8$)"),
        Line2D([0], [0], marker="*", color="none", markerfacecolor="#b91c1c", markersize=10, markeredgecolor="white", markeredgewidth=0.5, label=r"Mode collision ($l=9$)"),
    ]
    ax.legend(handles=custom_lines, loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=3)

    # Add inset for 0 degree collision
    inset_ax = fig.add_axes([0.76, 0.80, 0.22, 0.22])  # Moved slightly higher and right
    inset_ax.axvline(0.0, color="#334155", linewidth=1.5, linestyle="--", alpha=0.6, zorder=2)
    
    theta_0 = exp_theta[l_values == 0][0]
    theta_9 = exp_theta[l_values == 9][0]
    t0_u = theta_0 if theta_0 <= np.pi else theta_0 - 2*np.pi
    t9_u = theta_9 if theta_9 <= np.pi else theta_9 - 2*np.pi
    
    inset_ax.scatter([t0_u], [1.0], s=80, facecolors="none", edgecolors="#0f766e", linewidths=1.5, zorder=4)
    inset_ax.scatter([t9_u], [1.0], s=140, color="#b91c1c", marker="*", edgecolors="white", linewidths=0.5, zorder=5)
    
    span = max(abs(t0_u), abs(t9_u)) * 1.8
    if span < 1e-5: span = 0.01
    inset_ax.set_xlim(-span, span)
    inset_ax.set_ylim(0.97, 1.03)
    inset_ax.set_yticks([])
    inset_ax.set_xticks([0.0])
    inset_ax.set_xticklabels([r"$0^\circ$"])
    inset_ax.tick_params(axis="x", direction="in", pad=2, labelsize=8)
    
    delta_percent = abs(plot_df.loc[plot_df["l"]==9, "delta_pos_merged_percent_fsr"].iloc[0])
    y_arrow = 1.012
    inset_ax.annotate(
        "",
        xy=(min(t0_u, t9_u), y_arrow),
        xytext=(max(t0_u, t9_u), y_arrow),
        arrowprops=dict(arrowstyle="<->", color="#475569", lw=1.0)
    )
    inset_ax.text(
        (t0_u + t9_u)/2, y_arrow + 0.005,
        f"$\\Delta \\approx {delta_percent:.2f}\\%$ FSR",
        ha="center", va="bottom", fontsize=7.5, color="#1e293b"
    )
    
    for spine in inset_ax.spines.values():
        spine.set_linewidth(0.8)
        spine.set_color("#94a3b8")

    export_figure(fig, output_dir, "peak_validation_polar_l0_to_l9", dpi)


def plot_combined_linear_and_residual(
    plot_df: pd.DataFrame,
    summary_row: pd.Series,
    output_dir: Path,
    dpi: int,
) -> None:
    x = plot_df["l"].to_numpy(dtype=int)
    theory_y = plot_df["pos_theory_2_over_9"].to_numpy(dtype=float)
    exp_y = plot_df["pos_meas_merged"].to_numpy(dtype=float)
    residual = plot_df["delta_pos_merged_percent_fsr"].to_numpy(dtype=float)

    fig, (ax_main, ax_res) = plt.subplots(
        2,
        1,
        figsize=(5.75, 4.25),
        gridspec_kw={"height_ratios": [2.35, 1.0]},
        sharex=True,
    )

    theory_color = "#395a5c"
    measured_color = "#10188a"
    residual_color = "#c12a26"

    ax_main.plot(x, theory_y, color=theory_color, linestyle="--", linewidth=1.2, alpha=0.7, label="Theory (2/9 branch)", zorder=2)
    
    mask_normal = x != 9
    ax_main.scatter(
        x[mask_normal],
        exp_y[mask_normal],
        s=72,
        facecolors="none",
        edgecolors=measured_color,
        linewidths=1.5,
        label=r"Experiment ($l=0 \dots 8$)",
        zorder=3,
    )
    idx_l9 = int(np.where(x == 9)[0][0])
    ax_main.scatter(
        [x[idx_l9]],
        [exp_y[idx_l9]],
        s=120,
        color="#b91c1c",
        marker="*",
        edgecolors="white",
        linewidths=0.5,
        label=r"Mode collision ($l=9$)",
        zorder=4,
    )

    ax_main.set_ylim(-0.05, 1.05)
    ax_main.set_ylabel("Normalized position", labelpad=18)
    ax_main.set_yticks(np.arange(0.0, 1.01, 0.2))
    ax_main.tick_params(labelbottom=False)
    
    # Place legend in top left corner with no frame
    ax_main.legend(loc="upper left", handlelength=2.0, borderaxespad=0.6)
    
    # Add an arrow pointing to the collision point
    ax_main.annotate(
        "Mode collision",
        xy=(x[idx_l9], exp_y[idx_l9]),
        xytext=(x[idx_l9] - 2.0, exp_y[idx_l9] + 0.15),
        arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.2),
        fontsize=9,
        color="#b91c1c",
        ha="center",
        va="center"
    )

    max_abs = max(float(np.max(np.abs(residual))), float(summary_row["max_abs_delta_percent_fsr"]))
    ylim_res = max(0.42, max_abs * 1.30)
    ax_res.axhline(0.0, color="#bdbdbd", linewidth=1.0, zorder=1)
    ax_res.vlines(x, 0, residual, color=residual_color, linewidth=1.0, alpha=0.5, zorder=2)
    ax_res.scatter(x[mask_normal], residual[mask_normal], s=60, facecolors="none", edgecolors=residual_color, linewidths=1.2, zorder=3)
    ax_res.scatter([x[idx_l9]], [residual[idx_l9]], s=100, color="#7f1d1d", marker="*", edgecolors="white", linewidths=0.5, zorder=4)

    ax_res.set_xlim(x.min() - 0.35, x.max() + 0.35)
    ax_res.set_ylim(-ylim_res, ylim_res)
    ax_res.set_xticks(x)
    ax_res.set_xlabel(r"Azimuthal index $l$")
    ax_res.set_ylabel("Error (%FSR)", labelpad=10)

    for ax in (ax_main, ax_res):
        ax.tick_params(axis="both", which="major", direction="in", top=True, right=True, pad=6)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)

    fig.subplots_adjust(left=0.14, right=0.985, bottom=0.105, top=0.985, hspace=0.04)
    export_figure(fig, output_dir, "peak_validation_combined_l0_to_l9", dpi)


def plot_overlap_fsr(curve_df: pd.DataFrame, metrics_row: pd.Series, output_dir: Path, dpi: int) -> None:
    fig, ax = plt.subplots(figsize=(5.75, 3.75))
    x = curve_df["detuning_from_l0_peak_fsr"].to_numpy(dtype=float)
    t0 = curve_df["T_l0"].to_numpy(dtype=float)
    t9 = curve_df["T_l9"].to_numpy(dtype=float)
    overlap = curve_df["T_overlap_min"].to_numpy(dtype=float)
    delta_fsr = float(metrics_row["delta_pos_fsr"])
    t9_at_l0 = float(metrics_row["relative_transmission_l9_at_l0_peak"])

    ax.plot(x, t0, color="#1d4ed8", linewidth=1.8, label=r"$l=0$")
    ax.plot(x, t9, color="#b91c1c", linewidth=1.8, label=r"$l=9$")
    ax.fill_between(x, 0.0, overlap, color="#f59e0b", alpha=0.28, label="overlap area")
    ax.axvline(0.0, color="#334155", linestyle=":", linewidth=1.2, alpha=0.9)
    ax.scatter([0.0], [1.0], s=60, facecolors="none", edgecolors="#1d4ed8", linewidths=1.5, zorder=5)
    ax.scatter([0.0], [t9_at_l0], s=80, color="#b91c1c", marker="*", edgecolors="white", linewidths=0.5, zorder=5)
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel(r"Detuning from $l=0$ peak (FSR)")
    ax.set_ylabel("Normalized transmittance")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.15, linestyle="--")

    inset = inset_axes(ax, width="34%", height="42%", loc="center right", borderpad=2.0)
    inset.plot(x, t0, color="#1d4ed8", linewidth=1.35)
    inset.plot(x, t9, color="#b91c1c", linewidth=1.35)
    inset.axvline(0.0, color="#334155", linestyle=":", linewidth=1.0, alpha=0.9)
    inset.scatter([0.0], [1.0], s=50, facecolors="none", edgecolors="#1d4ed8", linewidths=1.5, zorder=5)
    inset.scatter([0.0], [t9_at_l0], s=60, color="#b91c1c", marker="*", edgecolors="white", linewidths=0.5, zorder=5)
    inset.set_xlim(-0.25 * delta_fsr, 1.55 * delta_fsr)
    inset.set_ylim(min(t9_at_l0 - 0.03, 0.965), 1.005)
    inset.set_xticks([0.0, delta_fsr])
    inset.set_xticklabels(["0", rf"$\Delta$"])
    
    # Avoid ytick overlapping with data by using annotation instead
    inset.set_yticks([1.0])
    offset_x = -0.12 * delta_fsr
    inset.annotate(
        f"{t9_at_l0:.3f}",
        xy=(0.0, t9_at_l0),
        xytext=(offset_x, t9_at_l0),
        ha="right", va="center",
        fontsize=7.5,
        color="#b91c1c",
        arrowprops=dict(arrowstyle="-", color="#b91c1c", lw=0.8, alpha=0.6),
        bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=0.5)
    )
    
    inset.tick_params(axis="both", which="major", direction="in", labelsize=7, pad=2)
    inset.grid(alpha=0.15, linestyle="--")
    for spine in inset.spines.values():
        spine.set_linewidth(0.7)
    export_figure(fig, output_dir, "l0_l9_overlap_normalized_fsr", dpi)


def plot_overlap_mhz(curve_df: pd.DataFrame, metrics_row: pd.Series, output_dir: Path, dpi: int) -> None:
    fig, ax = plt.subplots(figsize=(5.75, 3.75))
    x = curve_df["detuning_from_l0_peak_mhz"].to_numpy(dtype=float)
    t0 = curve_df["T_l0"].to_numpy(dtype=float)
    t9 = curve_df["T_l9"].to_numpy(dtype=float)
    overlap = curve_df["T_overlap_min"].to_numpy(dtype=float)
    delta_mhz = float(metrics_row["delta_nu_mhz"])
    t9_at_l0 = float(metrics_row["relative_transmission_l9_at_l0_peak"])

    ax.plot(x, t0, color="#1d4ed8", linewidth=1.8, label=r"$l=0$")
    ax.plot(x, t9, color="#b91c1c", linewidth=1.8, label=r"$l=9$")
    ax.fill_between(x, 0.0, overlap, color="#f59e0b", alpha=0.28, label="overlap area")
    ax.axvline(0.0, color="#334155", linestyle=":", linewidth=1.2, alpha=0.9)
    ax.scatter([0.0], [1.0], s=60, facecolors="none", edgecolors="#1d4ed8", linewidths=1.5, zorder=5)
    ax.scatter([0.0], [t9_at_l0], s=80, color="#b91c1c", marker="*", edgecolors="white", linewidths=0.5, zorder=5)
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel(r"Detuning from $l=0$ peak (MHz)")
    ax.set_ylabel("Normalized transmittance")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.15, linestyle="--")

    inset = inset_axes(ax, width="34%", height="42%", loc="center right", borderpad=2.0)
    inset.plot(x, t0, color="#1d4ed8", linewidth=1.35)
    inset.plot(x, t9, color="#b91c1c", linewidth=1.35)
    inset.axvline(0.0, color="#334155", linestyle=":", linewidth=1.0, alpha=0.9)
    inset.scatter([0.0], [1.0], s=50, facecolors="none", edgecolors="#1d4ed8", linewidths=1.5, zorder=5)
    inset.scatter([0.0], [t9_at_l0], s=60, color="#b91c1c", marker="*", edgecolors="white", linewidths=0.5, zorder=5)
    inset.set_xlim(-0.25 * delta_mhz, 1.55 * delta_mhz)
    inset.set_ylim(min(t9_at_l0 - 0.03, 0.965), 1.005)
    inset.set_xticks([0.0, delta_mhz])
    inset.set_xticklabels(["0", rf"$\Delta \nu$"])
    
    # Avoid ytick overlapping with data by using annotation instead
    inset.set_yticks([1.0])
    offset_x = -0.12 * delta_mhz
    inset.annotate(
        f"{t9_at_l0:.3f}",
        xy=(0.0, t9_at_l0),
        xytext=(offset_x, t9_at_l0),
        ha="right", va="center",
        fontsize=7.5,
        color="#b91c1c",
        arrowprops=dict(arrowstyle="-", color="#b91c1c", lw=0.8, alpha=0.6),
        bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=0.5)
    )
    
    inset.tick_params(axis="both", which="major", direction="in", labelsize=7, pad=2)
    inset.grid(alpha=0.15, linestyle="--")
    for spine in inset.spines.values():
        spine.set_linewidth(0.7)
    export_figure(fig, output_dir, "l0_l9_overlap_mhz", dpi)


def plot_experimental_overlap_on_axes(
    ax: plt.Axes,
    curve_df: pd.DataFrame,
    metrics: dict[str, float],
    *,
    show_labels: bool,
    show_legend: bool,
    compact: bool,
) -> None:
    t0_col = next(col for col in curve_df.columns if col.startswith("T_l0"))
    t9_col = next(col for col in curve_df.columns if col.startswith("T_l9"))
    overlap_col = next(col for col in curve_df.columns if col.startswith("T_overlap_min"))
    x = curve_df["detuning_from_l0_peak_mhz"].to_numpy(dtype=float)
    t0 = curve_df[t0_col].to_numpy(dtype=float)
    t9 = curve_df[t9_col].to_numpy(dtype=float)
    overlap = curve_df[overlap_col].to_numpy(dtype=float)
    t0_at_l0 = float(metrics["t0_at_l0"])
    t9_at_l0 = float(metrics["t9_at_l0"])
    delta_mhz = float(metrics["delta_nu_mhz"])

    ax.plot(x, t0, color="#1d4ed8", linewidth=1.8 if not compact else 1.2, label=r"$l=0$")
    ax.plot(x, t9, color="#b91c1c", linewidth=1.8 if not compact else 1.2, label=r"$l=9$")
    ax.fill_between(x, 0.0, overlap, color="#f59e0b", alpha=0.22 if compact else 0.28, label="overlap area")
    ax.axvline(0.0, color="#334155", linestyle=":", linewidth=1.1 if compact else 1.2, alpha=0.9)
    ax.scatter([0.0], [t0_at_l0], s=36 if compact else 60, facecolors="none", edgecolors="#1d4ed8", linewidths=1.3 if compact else 1.5, zorder=5)
    ax.scatter([0.0], [t9_at_l0], s=46 if compact else 80, color="#b91c1c", marker="*", edgecolors="white", linewidths=0.4 if compact else 0.5, zorder=5)
    ax.set_xlim(x.min(), x.max())
    ymax = float(np.nanmax(np.concatenate([t0[np.isfinite(t0)], t9[np.isfinite(t9)]])))
    ax.set_ylim(0.0, max(1.05, ymax + 0.02))
    ax.grid(alpha=0.15, linestyle="--")

    if show_labels:
        ax.set_xlabel(r"Detuning from $l=0$ peak (MHz)")
        ax.set_ylabel("Normalized transmittance")
    else:
        ax.set_xlabel("")
        ax.set_ylabel("")

    if show_legend:
        ax.legend(loc="upper right")

    if compact:
        ax.set_xticks([0.0, delta_mhz])
        ax.set_xticklabels(["0", r"$\Delta \nu$"])
        ax.set_yticks([1.0])
        ax.set_yticklabels([])
        ax.tick_params(axis="both", which="major", direction="in", labelsize=7, pad=2)
        ax.text(
            0.04,
            0.92,
            "Experiment",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=7.5,
            color="#1e293b",
            bbox=dict(facecolor="white", alpha=0.82, edgecolor="none", pad=0.6),
        )
    else:
        ax.tick_params(axis="both", which="major", direction="in", top=True, right=True)


def plot_overlap_mhz_experiment_variant(
    curve_df: pd.DataFrame,
    metrics: dict[str, float],
    output_dir: Path,
    dpi: int,
    stem: str,
) -> None:
    fig, ax = plt.subplots(figsize=(5.75, 3.75))
    plot_experimental_overlap_on_axes(
        ax,
        curve_df,
        metrics,
        show_labels=True,
        show_legend=True,
        compact=False,
    )
    export_figure(fig, output_dir, stem, dpi)


def plot_overlap_mhz_experiment(
    curve_df: pd.DataFrame,
    metrics: dict[str, float],
    output_dir: Path,
    dpi: int,
) -> None:
    fig, ax = plt.subplots(figsize=(5.75, 3.75))
    plot_experimental_overlap_on_axes(
        ax,
        curve_df,
        metrics,
        show_labels=True,
        show_legend=True,
        compact=False,
    )

    delta_mhz = float(metrics["delta_nu_mhz"])
    t0_at_l0 = float(metrics["t0_at_l0"])
    t9_at_l0 = float(metrics["t9_at_l0"])
    x = curve_df["detuning_from_l0_peak_mhz"].to_numpy(dtype=float)
    t0 = curve_df["T_l0_exp"].to_numpy(dtype=float)
    t9 = curve_df["T_l9_exp"].to_numpy(dtype=float)
    inset = inset_axes(ax, width="34%", height="42%", loc="center right", borderpad=2.0)
    inset.plot(x, t0, color="#1d4ed8", linewidth=1.35)
    inset.plot(x, t9, color="#b91c1c", linewidth=1.35)
    inset.axvline(0.0, color="#334155", linestyle=":", linewidth=1.0, alpha=0.9)
    inset.scatter([0.0], [t0_at_l0], s=50, facecolors="none", edgecolors="#1d4ed8", linewidths=1.5, zorder=5)
    inset.scatter([0.0], [t9_at_l0], s=60, color="#b91c1c", marker="*", edgecolors="white", linewidths=0.5, zorder=5)
    inset.set_xlim(-0.25 * delta_mhz, 1.55 * delta_mhz)
    inset.set_ylim(min(t9_at_l0 - 0.03, t0_at_l0 - 0.02), max(1.005, t0_at_l0 + 0.005))
    inset.set_xticks([0.0, delta_mhz])
    inset.set_xticklabels(["0", rf"$\Delta \nu$"])
    inset.set_yticks([round(t0_at_l0, 3)])
    inset.annotate(
        f"{t9_at_l0:.3f}",
        xy=(0.0, t9_at_l0),
        xytext=(-0.12 * delta_mhz, t9_at_l0),
        ha="right",
        va="center",
        fontsize=7.5,
        color="#b91c1c",
        arrowprops=dict(arrowstyle="-", color="#b91c1c", lw=0.8, alpha=0.6),
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=0.5),
    )
    inset.tick_params(axis="both", which="major", direction="in", labelsize=7, pad=2)
    inset.grid(alpha=0.15, linestyle="--")
    for spine in inset.spines.values():
        spine.set_linewidth(0.7)

    export_figure(fig, output_dir, "l0_l9_overlap_mhz_experiment", dpi)


def plot_overlap_mhz_with_experiment_inset(
    curve_df: pd.DataFrame,
    metrics_row: pd.Series,
    exp_curve_df: pd.DataFrame,
    exp_metrics: dict[str, float],
    output_dir: Path,
    dpi: int,
) -> None:
    fig, ax = plt.subplots(figsize=(5.75, 3.75))
    x = curve_df["detuning_from_l0_peak_mhz"].to_numpy(dtype=float)
    t0 = curve_df["T_l0"].to_numpy(dtype=float)
    t9 = curve_df["T_l9"].to_numpy(dtype=float)
    overlap = curve_df["T_overlap_min"].to_numpy(dtype=float)
    delta_mhz = float(metrics_row["delta_nu_mhz"])
    t9_at_l0 = float(metrics_row["relative_transmission_l9_at_l0_peak"])

    ax.plot(x, t0, color="#1d4ed8", linewidth=1.8, label=r"$l=0$")
    ax.plot(x, t9, color="#b91c1c", linewidth=1.8, label=r"$l=9$")
    ax.fill_between(x, 0.0, overlap, color="#f59e0b", alpha=0.28, label="overlap area")
    ax.axvline(0.0, color="#334155", linestyle=":", linewidth=1.2, alpha=0.9)
    ax.scatter([0.0], [1.0], s=60, facecolors="none", edgecolors="#1d4ed8", linewidths=1.5, zorder=5)
    ax.scatter([0.0], [t9_at_l0], s=80, color="#b91c1c", marker="*", edgecolors="white", linewidths=0.5, zorder=5)
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel(r"Detuning from $l=0$ peak (MHz)")
    ax.set_ylabel("Normalized transmittance")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.15, linestyle="--")

    zoom_inset = ax.inset_axes([0.64, 0.58, 0.30, 0.30])
    zoom_inset.plot(x, t0, color="#1d4ed8", linewidth=1.35)
    zoom_inset.plot(x, t9, color="#b91c1c", linewidth=1.35)
    zoom_inset.axvline(0.0, color="#334155", linestyle=":", linewidth=1.0, alpha=0.9)
    zoom_inset.scatter([0.0], [1.0], s=50, facecolors="none", edgecolors="#1d4ed8", linewidths=1.5, zorder=5)
    zoom_inset.scatter([0.0], [t9_at_l0], s=60, color="#b91c1c", marker="*", edgecolors="white", linewidths=0.5, zorder=5)
    zoom_inset.set_xlim(-0.25 * delta_mhz, 1.55 * delta_mhz)
    zoom_inset.set_ylim(min(t9_at_l0 - 0.03, 0.965), 1.005)
    zoom_inset.set_xticks([0.0, delta_mhz])
    zoom_inset.set_xticklabels(["0", rf"$\Delta \nu$"])
    zoom_inset.set_yticks([1.0])
    zoom_inset.annotate(
        f"{t9_at_l0:.3f}",
        xy=(0.0, t9_at_l0),
        xytext=(-0.12 * delta_mhz, t9_at_l0),
        ha="right",
        va="center",
        fontsize=7.5,
        color="#b91c1c",
        arrowprops=dict(arrowstyle="-", color="#b91c1c", lw=0.8, alpha=0.6),
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=0.5),
    )
    zoom_inset.tick_params(axis="both", which="major", direction="in", labelsize=7, pad=2)
    zoom_inset.grid(alpha=0.15, linestyle="--")
    for spine in zoom_inset.spines.values():
        spine.set_linewidth(0.7)

    exp_inset = ax.inset_axes([0.64, 0.11, 0.30, 0.25])
    plot_experimental_overlap_on_axes(
        exp_inset,
        exp_curve_df,
        exp_metrics,
        show_labels=False,
        show_legend=False,
        compact=True,
    )
    for spine in exp_inset.spines.values():
        spine.set_linewidth(0.8)

    export_figure(fig, output_dir, "l0_l9_overlap_mhz_with_experiment_inset", dpi)


def write_summary_text(
    output_dir: Path,
    summary_row: pd.Series,
    metrics_row: pd.Series,
    per_mode_df: pd.DataFrame,
    cavity_row: pd.Series,
) -> None:
    row_l9 = per_mode_df.loc[per_mode_df["l"] == 9].iloc[0]
    row_l0 = per_mode_df.loc[per_mode_df["l"] == 0].iloc[0]
    text = f"""0.88 mm / 原始数据 / 十模闭合验证摘要

数据口径
- dataset_key = {cavity_row['dataset_key']}
- analysis_source_label = {cavity_row['analysis_source_label']}
- FSR_final = {float(cavity_row['fsr_final_ghz']):.9f} GHz
- k_theory = 2/9 = {ANALYTIC_K:.9f}

位置验证
- merged RMS residual = {float(summary_row['rms_delta_percent_fsr']):.3f}% FSR
- merged max residual = {float(summary_row['max_abs_delta_percent_fsr']):.3f}% FSR at l={int(summary_row['worst_l'])}
- l=9 closure residual = {float(summary_row['closure_l9_abs_delta_pos']) * 100.0:.3f}% FSR

l=0 与 l=9 冲突量
- nu(l=0) = {float(row_l0['merged_nu_ghz']):.9f} GHz
- nu(l=9) = {float(row_l9['merged_nu_ghz']):.9f} GHz
- delta_nu = {float(metrics_row['delta_nu_mhz']):.3f} MHz
- delta_pos = {float(metrics_row['delta_pos_fsr']) * 100.0:.3f}% FSR
- FWHM(l=0) = {float(metrics_row['fwhm_l0_mhz']):.3f} MHz
- FWHM(l=9) = {float(metrics_row['fwhm_l9_mhz']):.3f} MHz
- delta/FWHM(l=0) = {float(metrics_row['delta_over_fwhm_l0']):.4f}
- delta/FWHM(l=9) = {float(metrics_row['delta_over_fwhm_l9']):.4f}

基于归一化 Lorentz 峰模型的相对串扰
- T_9(nu_0) = {float(metrics_row['relative_transmission_l9_at_l0_peak']):.6f}
- T_0(nu_9) = {float(metrics_row['relative_transmission_l0_at_l9_peak']):.6f}

峰重叠面积
- overlap_area = {float(metrics_row['overlap_area_mhz']):.3f} MHz
- overlap / area(l=0) = {float(metrics_row['overlap_over_area_l0']):.6f}
- overlap / area(l=9) = {float(metrics_row['overlap_over_area_l9']):.6f}
"""
    (output_dir / "ten_mode_summary.txt").write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    configure_plot_style()
    validate_inputs(
        [
            args.input_csv,
            args.summary_csv,
            args.main_peaks_csv,
            args.peak_fit_csv,
            args.raw_l0_csv,
            args.raw_l9_csv,
            args.cavity_summary_csv,
        ]
    )

    detail_df, summary_row, main_peaks_df, linewidth_df, peak_fit_df, cavity_row = load_position_data(
        input_csv=args.input_csv,
        summary_csv=args.summary_csv,
        main_peaks_csv=args.main_peaks_csv,
        peak_fit_csv=args.peak_fit_csv,
        cavity_summary_csv=args.cavity_summary_csv,
    )
    per_mode_df = build_per_mode_metrics(detail_df, main_peaks_df, linewidth_df)
    curve_df, overlap_metrics_df = build_overlap_curves_and_metrics(per_mode_df, cavity_row)
    overlap_metrics_row = overlap_metrics_df.iloc[0]
    exp_curve_df, exp_metrics = build_experimental_overlap_curves(
        raw_l0_csv=args.raw_l0_csv,
        raw_l9_csv=args.raw_l9_csv,
        peak_fit_df=peak_fit_df,
        main_peaks_df=main_peaks_df,
        cavity_row=cavity_row,
    )
    rising_raw_curve_df, rising_raw_metrics = build_rising_experimental_overlap_curves(
        raw_l0_csv=args.raw_l0_csv,
        raw_l9_csv=args.raw_l9_csv,
        peak_fit_df=peak_fit_df,
        main_peaks_df=main_peaks_df,
        cavity_row=cavity_row,
        smooth=False,
    )
    rising_smooth_curve_df, rising_smooth_metrics = build_rising_experimental_overlap_curves(
        raw_l0_csv=args.raw_l0_csv,
        raw_l9_csv=args.raw_l9_csv,
        peak_fit_df=peak_fit_df,
        main_peaks_df=main_peaks_df,
        cavity_row=cavity_row,
        smooth=True,
    )

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    per_mode_df.to_csv(output_dir / "ten_mode_position_metrics.csv", index=False, encoding="utf-8-sig")
    overlap_metrics_df.to_csv(output_dir / "l0_l9_overlap_metrics.csv", index=False, encoding="utf-8-sig")
    curve_df.to_csv(output_dir / "l0_l9_overlap_curves.csv", index=False, encoding="utf-8-sig")
    exp_curve_df.to_csv(output_dir / "l0_l9_overlap_mhz_experiment_curves.csv", index=False, encoding="utf-8-sig")
    rising_raw_curve_df.to_csv(output_dir / "l0_l9_overlap_mhz_rising_raw_curves.csv", index=False, encoding="utf-8-sig")
    rising_smooth_curve_df.to_csv(output_dir / "l0_l9_overlap_mhz_rising_smooth_curves.csv", index=False, encoding="utf-8-sig")
    write_summary_text(output_dir, summary_row, overlap_metrics_row, per_mode_df, cavity_row)

    plot_polar_positions(detail_df, output_dir, args.dpi)
    plot_combined_linear_and_residual(detail_df, summary_row, output_dir, args.dpi)
    plot_overlap_fsr(curve_df, overlap_metrics_row, output_dir, args.dpi)
    plot_overlap_mhz(curve_df, overlap_metrics_row, output_dir, args.dpi)
    plot_overlap_mhz_experiment(exp_curve_df, exp_metrics, output_dir, args.dpi)
    plot_overlap_mhz_experiment_variant(
        rising_raw_curve_df,
        rising_raw_metrics,
        output_dir,
        args.dpi,
        "l0_l9_overlap_mhz_rising_raw",
    )
    plot_overlap_mhz_experiment_variant(
        rising_smooth_curve_df,
        rising_smooth_metrics,
        output_dir,
        args.dpi,
        "l0_l9_overlap_mhz_rising_smooth",
    )
    plot_overlap_mhz_with_experiment_inset(
        curve_df,
        overlap_metrics_row,
        exp_curve_df,
        exp_metrics,
        output_dir,
        args.dpi,
    )

    print(f"Saved figures and tables to: {output_dir.resolve()}")
    print("Generated: peak_validation_polar_l0_to_l9.[pdf|png]")
    print("Generated: peak_validation_combined_l0_to_l9.[pdf|png]")
    print("Generated: l0_l9_overlap_normalized_fsr.[pdf|png]")
    print("Generated: l0_l9_overlap_mhz.[pdf|png]")
    print("Generated: l0_l9_overlap_mhz_experiment.[pdf|png]")
    print("Generated: l0_l9_overlap_mhz_rising_raw.[pdf|png]")
    print("Generated: l0_l9_overlap_mhz_rising_smooth.[pdf|png]")
    print("Generated: l0_l9_overlap_mhz_with_experiment_inset.[pdf|png]")
    print("Generated: ten_mode_position_metrics.csv")
    print("Generated: l0_l9_overlap_metrics.csv")
    print("Generated: l0_l9_overlap_curves.csv")
    print("Generated: l0_l9_overlap_mhz_experiment_curves.csv")
    print("Generated: l0_l9_overlap_mhz_rising_raw_curves.csv")
    print("Generated: l0_l9_overlap_mhz_rising_smooth_curves.csv")
    print("Generated: ten_mode_summary.txt")


if __name__ == "__main__":
    main()
