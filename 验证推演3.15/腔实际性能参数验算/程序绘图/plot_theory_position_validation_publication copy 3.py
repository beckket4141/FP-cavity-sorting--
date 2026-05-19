from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


ANALYTIC_K = 2.0 / 9.0


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


def load_position_data(
    input_csv: Path,
    summary_csv: Path,
    main_peaks_csv: Path,
    peak_fit_csv: Path,
    cavity_summary_csv: Path,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.DataFrame, pd.Series]:
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
    return detail_df, merged_summary.iloc[0], main_peaks_df, linewidth_df, cavity_row


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
        ax.plot([angle, angle], [0.93, 1.07], color="#334155", linewidth=1.8, zorder=2)
        ax.text(angle, 1.15, f"$l={label}$", ha="center", va="center", fontsize=8.5, color="#1e293b")

    highlight_mask = l_values == 9
    ax.scatter(
        exp_theta[~highlight_mask],
        np.full(np.count_nonzero(~highlight_mask), 1.00),
        s=45,
        color="#0f766e",
        edgecolors="white",
        linewidths=0.5,
        zorder=4,
    )
    ax.scatter(
        exp_theta[highlight_mask],
        np.full(np.count_nonzero(highlight_mask), 1.00),
        s=58,
        color="#b91c1c",
        edgecolors="white",
        linewidths=0.6,
        zorder=5,
    )

    from matplotlib.lines import Line2D

    custom_lines = [
        Line2D([0], [0], color="#334155", linewidth=1.8, label="Theory"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#0f766e", markersize=7, markeredgecolor="white", markeredgewidth=0.5, label="Experiment"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#b91c1c", markersize=7.5, markeredgecolor="white", markeredgewidth=0.5, label=r"Experiment $l=9$"),
    ]
    ax.legend(handles=custom_lines, loc="lower center", bbox_to_anchor=(0.5, -0.10), ncol=3)
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

    ax_main.plot(x, theory_y, color=theory_color, linestyle="--", linewidth=1.6, label="Predicted", zorder=2)
    ax_main.scatter(
        x,
        exp_y,
        s=72,
        color=measured_color,
        edgecolors="white",
        linewidths=0.55,
        label="Measured",
        zorder=3,
    )
    idx_l9 = int(np.where(x == 9)[0][0])
    ax_main.scatter(
        [x[idx_l9]],
        [exp_y[idx_l9]],
        s=84,
        color="#b91c1c",
        edgecolors="white",
        linewidths=0.65,
        label=r"Measured $l=9$",
        zorder=4,
    )

    ax_main.set_ylim(-0.05, 1.05)
    ax_main.set_ylabel("Normalized position", labelpad=18)
    ax_main.set_yticks(np.arange(0.0, 1.01, 0.2))
    ax_main.tick_params(labelbottom=False)
    ax_main.legend(loc="lower right", handlelength=2.0, borderaxespad=0.4)

    max_abs = max(float(np.max(np.abs(residual))), float(summary_row["max_abs_delta_percent_fsr"]))
    ylim_res = max(0.42, max_abs * 1.30)
    ax_res.axhline(0.0, color="#bdbdbd", linewidth=1.0, zorder=1)
    ax_res.vlines(x, 0, residual, color=residual_color, linewidth=1.0, alpha=0.7, zorder=2)
    ax_res.scatter(x, residual, s=60, color=residual_color, edgecolors="white", linewidths=0.45, zorder=3)
    ax_res.scatter([x[idx_l9]], [residual[idx_l9]], s=72, color="#7f1d1d", edgecolors="white", linewidths=0.5, zorder=4)

    ax_res.set_xlim(x.min() - 0.35, x.max() + 0.35)
    ax_res.set_ylim(-ylim_res, ylim_res)
    ax_res.set_xticks(x)
    ax_res.set_xlabel(r"Azimuthal index $l$")
    ax_res.set_ylabel("Error (%FSR)", labelpad=10)

    for ax in (ax_main, ax_res):
        ax.tick_params(axis="both", which="major", direction="in", top=True, right=True, pad=6)
        for spine in ax.spines.values():
            spine.set_linewidth(0.8)

    ax_main.text(
        0.015,
        0.97,
        build_stats_text(summary_row),
        transform=ax_main.transAxes,
        va="top",
        ha="left",
        fontsize=8.8,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.94},
    )

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
    ax.scatter([0.0], [1.0], s=46, color="#1d4ed8", edgecolors="white", linewidths=0.45, zorder=5)
    ax.scatter([0.0], [t9_at_l0], s=46, color="#b91c1c", edgecolors="white", linewidths=0.45, zorder=5)
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel(r"Detuning from $l=0$ peak (FSR)")
    ax.set_ylabel("Normalized transmittance")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.20)
    ax.text(
        0.015,
        0.97,
        build_overlap_text(metrics_row),
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=8.7,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.94},
    )

    inset = inset_axes(ax, width="34%", height="42%", loc="center right", borderpad=2.0)
    inset.plot(x, t0, color="#1d4ed8", linewidth=1.35)
    inset.plot(x, t9, color="#b91c1c", linewidth=1.35)
    inset.axvline(0.0, color="#334155", linestyle=":", linewidth=1.0, alpha=0.9)
    inset.scatter([0.0], [1.0], s=28, color="#1d4ed8", edgecolors="white", linewidths=0.35, zorder=5)
    inset.scatter([0.0], [t9_at_l0], s=28, color="#b91c1c", edgecolors="white", linewidths=0.35, zorder=5)
    inset.set_xlim(-0.25 * delta_fsr, 1.55 * delta_fsr)
    inset.set_ylim(min(t9_at_l0 - 0.03, 0.965), 1.005)
    inset.set_xticks([0.0, delta_fsr])
    inset.set_xticklabels(["0", rf"$\Delta$"])
    inset.set_yticks([round(t9_at_l0, 3), 1.0])
    inset.tick_params(axis="both", which="major", direction="in", labelsize=7, pad=2)
    inset.grid(alpha=0.18)
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
    ax.scatter([0.0], [1.0], s=46, color="#1d4ed8", edgecolors="white", linewidths=0.45, zorder=5)
    ax.scatter([0.0], [t9_at_l0], s=46, color="#b91c1c", edgecolors="white", linewidths=0.45, zorder=5)
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel(r"Detuning from $l=0$ peak (MHz)")
    ax.set_ylabel("Normalized transmittance")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.20)
    ax.text(
        0.015,
        0.97,
        build_overlap_text(metrics_row),
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=8.7,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.94},
    )

    inset = inset_axes(ax, width="34%", height="42%", loc="center right", borderpad=2.0)
    inset.plot(x, t0, color="#1d4ed8", linewidth=1.35)
    inset.plot(x, t9, color="#b91c1c", linewidth=1.35)
    inset.axvline(0.0, color="#334155", linestyle=":", linewidth=1.0, alpha=0.9)
    inset.scatter([0.0], [1.0], s=28, color="#1d4ed8", edgecolors="white", linewidths=0.35, zorder=5)
    inset.scatter([0.0], [t9_at_l0], s=28, color="#b91c1c", edgecolors="white", linewidths=0.35, zorder=5)
    inset.set_xlim(-0.25 * delta_mhz, 1.55 * delta_mhz)
    inset.set_ylim(min(t9_at_l0 - 0.03, 0.965), 1.005)
    inset.set_xticks([0.0, delta_mhz])
    inset.set_xticklabels(["0", rf"$\Delta \nu$"])
    inset.set_yticks([round(t9_at_l0, 3), 1.0])
    inset.tick_params(axis="both", which="major", direction="in", labelsize=7, pad=2)
    inset.grid(alpha=0.18)
    for spine in inset.spines.values():
        spine.set_linewidth(0.7)
    export_figure(fig, output_dir, "l0_l9_overlap_mhz", dpi)


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
            args.cavity_summary_csv,
        ]
    )

    detail_df, summary_row, main_peaks_df, linewidth_df, cavity_row = load_position_data(
        input_csv=args.input_csv,
        summary_csv=args.summary_csv,
        main_peaks_csv=args.main_peaks_csv,
        peak_fit_csv=args.peak_fit_csv,
        cavity_summary_csv=args.cavity_summary_csv,
    )
    per_mode_df = build_per_mode_metrics(detail_df, main_peaks_df, linewidth_df)
    curve_df, overlap_metrics_df = build_overlap_curves_and_metrics(per_mode_df, cavity_row)
    overlap_metrics_row = overlap_metrics_df.iloc[0]

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    per_mode_df.to_csv(output_dir / "ten_mode_position_metrics.csv", index=False, encoding="utf-8-sig")
    overlap_metrics_df.to_csv(output_dir / "l0_l9_overlap_metrics.csv", index=False, encoding="utf-8-sig")
    curve_df.to_csv(output_dir / "l0_l9_overlap_curves.csv", index=False, encoding="utf-8-sig")
    write_summary_text(output_dir, summary_row, overlap_metrics_row, per_mode_df, cavity_row)

    plot_polar_positions(detail_df, output_dir, args.dpi)
    plot_combined_linear_and_residual(detail_df, summary_row, output_dir, args.dpi)
    plot_overlap_fsr(curve_df, overlap_metrics_row, output_dir, args.dpi)
    plot_overlap_mhz(curve_df, overlap_metrics_row, output_dir, args.dpi)

    print(f"Saved figures and tables to: {output_dir.resolve()}")
    print("Generated: peak_validation_polar_l0_to_l9.[pdf|png]")
    print("Generated: peak_validation_combined_l0_to_l9.[pdf|png]")
    print("Generated: l0_l9_overlap_normalized_fsr.[pdf|png]")
    print("Generated: l0_l9_overlap_mhz.[pdf|png]")
    print("Generated: ten_mode_position_metrics.csv")
    print("Generated: l0_l9_overlap_metrics.csv")
    print("Generated: l0_l9_overlap_curves.csv")
    print("Generated: ten_mode_summary.txt")


if __name__ == "__main__":
    main()
