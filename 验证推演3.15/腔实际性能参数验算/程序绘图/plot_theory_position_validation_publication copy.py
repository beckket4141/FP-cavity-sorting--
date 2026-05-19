from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


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


def default_output_dir(script_dir: Path) -> Path:
    return script_dir / "输出图"


def configure_plot_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIX Two Text", "Times New Roman", "STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 10.5,
            "axes.linewidth": 0.7,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.size": 3.0,
            "ytick.major.size": 3.0,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "legend.frameon": False,
            "legend.fontsize": 8.5,
            "figure.dpi": 150,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Create publication-style validation plots for theory vs experiment peak positions."
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
        "--output-dir",
        type=Path,
        default=default_output_dir(script_dir),
        help="Directory to save the figures.",
    )
    parser.add_argument(
        "--include-closure-l9",
        action="store_true",
        help="Include l=9 closure point in the plotted data.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Output DPI for PNG export.",
    )
    return parser.parse_args()


def validate_inputs(input_csv: Path, summary_csv: Path) -> None:
    if not input_csv.exists():
        raise FileNotFoundError(f"Missing input CSV: {input_csv}")
    if not summary_csv.exists():
        raise FileNotFoundError(f"Missing summary CSV: {summary_csv}")


def load_data(input_csv: Path, summary_csv: Path, include_closure_l9: bool) -> tuple[pd.DataFrame, pd.Series]:
    detail_df = pd.read_csv(input_csv)
    summary_df = pd.read_csv(summary_csv)

    required_detail_columns = {
        "l",
        "pos_theory_2_over_9",
        "pos_meas_merged",
        "delta_pos_merged_percent_fsr",
    }
    required_summary_columns = {
        "measurement_type",
        "rms_delta_percent_fsr",
        "max_abs_delta_percent_fsr",
        "worst_l",
        "closure_l9_abs_delta_pos",
    }

    missing_detail = sorted(required_detail_columns - set(detail_df.columns))
    missing_summary = sorted(required_summary_columns - set(summary_df.columns))
    if missing_detail:
        raise KeyError(f"Input CSV missing columns: {missing_detail}")
    if missing_summary:
        raise KeyError(f"Summary CSV missing columns: {missing_summary}")

    plot_df = detail_df.sort_values("l").reset_index(drop=True).copy()
    if not include_closure_l9:
        plot_df = plot_df.loc[plot_df["l"] <= 8].reset_index(drop=True)

    merged_summary = summary_df.loc[summary_df["measurement_type"] == "merged"]
    if merged_summary.empty:
        raise ValueError("Summary CSV does not contain a merged row.")

    return plot_df, merged_summary.iloc[0]


def export_figure(fig: plt.Figure, output_dir: Path, stem: str, dpi: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=dpi)
    plt.close(fig)


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


def plot_polar_positions(plot_df: pd.DataFrame, output_dir: Path, dpi: int) -> None:
    theory_theta = 2.0 * np.pi * plot_df["pos_theory_2_over_9"].to_numpy(dtype=float)
    exp_theta = 2.0 * np.pi * plot_df["pos_meas_merged"].to_numpy(dtype=float)
    l_values = plot_df["l"].to_numpy(dtype=int)

    fig = plt.figure(figsize=(4.2, 4.2), constrained_layout=True)
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_rlim(0.0, 1.14)
    ax.set_rticks([])
    ax.grid(alpha=0.18, linewidth=0.5)

    ax.scatter(
        theory_theta,
        np.full_like(theory_theta, 1.00),
        s=72,
        facecolors="white",
        edgecolors="black",
        linewidths=1.0,
        label="Theory",
        zorder=3,
    )
    ax.scatter(
        exp_theta,
        np.full_like(exp_theta, 0.93),
        s=44,
        color="#0f766e",
        edgecolors="white",
        linewidths=0.35,
        label="Experiment",
        zorder=4,
    )

    for angle, label in zip(theory_theta, l_values):
        ax.text(angle, 1.08, f"$l={label}$", ha="center", va="center", fontsize=7.8)

    ax.set_title("Peak positions on the normalized FSR ring", pad=14)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.08, -0.04))
    export_figure(fig, output_dir, "peak_validation_polar", dpi)


def plot_linear_positions(plot_df: pd.DataFrame, output_dir: Path, dpi: int) -> None:
    x = plot_df["l"].to_numpy(dtype=int)
    theory_y = plot_df["pos_theory_2_over_9"].to_numpy(dtype=float)
    exp_y = plot_df["pos_meas_merged"].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(4.9, 3.2), constrained_layout=True)
    ax.plot(x, theory_y, color="black", linewidth=1.25, label="Theory", zorder=2)
    ax.scatter(
        x,
        exp_y,
        s=28,
        color="#0f766e",
        edgecolors="white",
        linewidths=0.35,
        label="Experiment",
        zorder=3,
    )
    ax.set_xlim(x.min() - 0.35, x.max() + 0.35)
    ax.set_ylim(-0.035, 1.035)
    ax.set_xlabel(r"Mode index $l$")
    ax.set_ylabel("Position in one FSR")
    ax.set_title("Theory and experiment on a linear axis")
    ax.grid(axis="y", alpha=0.18, linewidth=0.5)
    ax.legend(loc="upper left")
    export_figure(fig, output_dir, "peak_validation_linear", dpi)


def plot_residuals(plot_df: pd.DataFrame, summary_row: pd.Series, output_dir: Path, dpi: int) -> None:
    x = plot_df["l"].to_numpy(dtype=int)
    residual = plot_df["delta_pos_merged_percent_fsr"].to_numpy(dtype=float)
    max_abs = max(float(np.max(np.abs(residual))), float(summary_row["max_abs_delta_percent_fsr"]))
    ylim = max(0.42, max_abs * 1.30)

    fig, ax = plt.subplots(figsize=(5.2, 3.35), constrained_layout=True)
    ax.axhline(0.0, color="black", linewidth=0.8, zorder=1)
    ax.axhspan(-0.5, 0.5, color="#dff3e4", alpha=0.8, zorder=0)
    ax.plot(x, residual, color="#0f766e", linewidth=1.4, zorder=2)
    ax.scatter(
        x,
        residual,
        s=28,
        color="#0f766e",
        edgecolors="white",
        linewidths=0.35,
        zorder=3,
    )

    ax.set_xlim(x.min() - 0.35, x.max() + 0.35)
    ax.set_ylim(-ylim, ylim)
    ax.set_xlabel(r"Mode index $l$")
    ax.set_ylabel("Residual (%FSR)")
    ax.set_title("Experiment residual on the circular metric")
    ax.grid(axis="y", alpha=0.18, linewidth=0.5)

    ax.text(
        0.02,
        0.97,
        build_stats_text(summary_row),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.2,
        bbox={
            "boxstyle": "round,pad=0.28",
            "facecolor": "white",
            "edgecolor": "#cbd5e1",
            "linewidth": 0.7,
            "alpha": 0.96,
        },
    )
    export_figure(fig, output_dir, "peak_validation_residual", dpi)


def main() -> None:
    args = parse_args()
    configure_plot_style()
    validate_inputs(args.input_csv, args.summary_csv)
    plot_df, summary_row = load_data(
        input_csv=args.input_csv,
        summary_csv=args.summary_csv,
        include_closure_l9=args.include_closure_l9,
    )

    plot_polar_positions(plot_df, args.output_dir, args.dpi)
    plot_linear_positions(plot_df, args.output_dir, args.dpi)
    plot_residuals(plot_df, summary_row, args.output_dir, args.dpi)

    print(f"Saved figures to: {args.output_dir.resolve()}")
    print("Generated: peak_validation_polar.[pdf|png]")
    print("Generated: peak_validation_linear.[pdf|png]")
    print("Generated: peak_validation_residual.[pdf|png]")


if __name__ == "__main__":
    main()
