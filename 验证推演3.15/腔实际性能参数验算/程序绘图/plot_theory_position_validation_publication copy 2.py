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

    fig = plt.figure(figsize=(4.65, 4.45))
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_rlim(0.0, 1.25)
    
    # 清理坐标轴：Nature/Optica 风格通常去掉无关的网格线和角度标签，仅保留物理意义的刻画
    ax.set_rticks([])
    ax.set_thetagrids([])  
    ax.spines['polar'].set_visible(False)
    
    # 绘制基础 FSR 环
    theta_ring = np.linspace(0, 2*np.pi, 300)
    ax.plot(theta_ring, np.ones_like(theta_ring), color="#94a3b8", linewidth=1.0, linestyle="-", zorder=1)

    # 理论点：使用横跨在圆环上的刻度线表示（类似表盘刻度）
    # 彻底杜绝原先由于标记重叠产生的径向偏移视错觉
    for i, t in enumerate(theory_theta):
        label_val = l_values[i]
        # 刻度线
        ax.plot([t, t], [0.93, 1.07], color="#334155", linewidth=1.8, zorder=2)
        # 将 l 标签放在刻度线外侧
        ax.text(t, 1.15, f"$l={label_val}$", ha="center", va="center", fontsize=8.5, color="#1e293b")

    # 实验点：绘制在圆环上的实心点
    ax.scatter(
        exp_theta,
        np.full_like(exp_theta, 1.00),
        s=45,
        color="#0f766e",
        edgecolors="white",  
        linewidths=0.5,
        zorder=4,
    )

    # 自定义图例
    from matplotlib.lines import Line2D
    custom_lines = [
        Line2D([0], [0], color="#334155", linewidth=1.8, label="Theory"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#0f766e", markersize=7, markeredgecolor="white", markeredgewidth=0.5, label="Experiment")
    ]
    ax.legend(handles=custom_lines, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False)
    export_figure(fig, output_dir, "peak_validation_polar", dpi)


def plot_combined_linear_and_residual(plot_df: pd.DataFrame, summary_row: pd.Series, output_dir: Path, dpi: int) -> None:
    x = plot_df["l"].to_numpy(dtype=int)
    theory_y = plot_df["pos_theory_2_over_9"].to_numpy(dtype=float)
    exp_y = plot_df["pos_meas_merged"].to_numpy(dtype=float)
    residual = plot_df["delta_pos_merged_percent_fsr"].to_numpy(dtype=float)

    # 创建上下子图，共享 X 轴
    fig, (ax_main, ax_res) = plt.subplots(
        2,
        1,
        figsize=(5.55, 4.15),
        gridspec_kw={"height_ratios": [2.35, 1]},
        sharex=True,
    )

    theory_color = "#395a5c"
    measured_color = "#10188a"
    residual_color = "#c12a26"

    # --- 绘制主图 (理论 vs 实验) ---
    # 使用虚线绘制理论值，使得实验实心点更加突出，模仿参考图风格
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
    
    ax_main.set_ylim(-0.05, 1.05)
    ax_main.set_ylabel("Normalized position", labelpad=18)
    ax_main.set_yticks(np.arange(0.0, 1.01, 0.2))
    ax_main.tick_params(labelbottom=False)
    ax_main.legend(loc="lower right", handlelength=2.0, borderaxespad=0.4)

    # --- 绘制残差图 ---
    max_abs = max(float(np.max(np.abs(residual))), float(summary_row["max_abs_delta_percent_fsr"]))
    ylim_res = max(0.42, max_abs * 1.30)

    ax_res.axhline(0.0, color="#bdbdbd", linewidth=1.0, zorder=1)
    
    # 模拟 Stem Plot，使用带有警示感的红色
    ax_res.vlines(x, 0, residual, color=residual_color, linewidth=1.0, alpha=0.7, zorder=2)
    ax_res.scatter(x, residual, s=60, color=residual_color, edgecolors="white", linewidths=0.45, zorder=3)

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

    export_figure(fig, output_dir, "peak_validation_combined", dpi)


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
    
    # 用新整合的绘图函数替代旧的两个函数
    plot_combined_linear_and_residual(plot_df, summary_row, args.output_dir, args.dpi)

    print(f"Saved figures to: {args.output_dir.resolve()}")
    print("Generated: peak_validation_polar.[pdf|png]")
    print("Generated: peak_validation_combined.[pdf|png]")


if __name__ == "__main__":
    main()
