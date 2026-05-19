from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


LINE_RE = re.compile(
    r"l=(?P<l>\d+):.*?mean=(?P<mean>\d+\.\d+), std=(?P<std>\d+\.\d+), "
    r"mean\+std format: (?P<mean_pct>\d+\.\d+)% \+/- (?P<std_pct>\d+\.\d+)%",
    re.IGNORECASE,
)
OVERALL_RE = re.compile(
    r"mean=(?P<mean>\d+\.\d+), std=(?P<std>\d+\.\d+), "
    r"mean\+std format: (?P<mean_pct>\d+\.\d+)% \+/- (?P<std_pct>\d+\.\d+)%",
    re.IGNORECASE,
)


def default_stats_txt(script_dir: Path) -> Path:
    data_dir = script_dir.parent / "满载叠加态输入数据" / "最终数据"
    candidates = [
        data_dir / "triplicate_transmittance_l0_9_stats.txt",
        data_dir / "triplicate_transmittance_l0_8_stats.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


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
            "legend.fontsize": 8.3,
            "figure.dpi": 150,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Create a publication-style pure-mode transmittance plot.")
    parser.add_argument(
        "--stats-txt",
        type=Path,
        default=default_stats_txt(script_dir),
        help="Path to the triplicate transmittance stats txt file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(script_dir),
        help="Directory to save the figure.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Output DPI for PNG export.",
    )
    return parser.parse_args()


def parse_stats_txt(stats_txt: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    if not stats_txt.exists():
        raise FileNotFoundError(f"Missing stats txt: {stats_txt}")

    rows: list[dict[str, float]] = []
    overall: dict[str, float] = {}
    in_overall_section = False

    for raw_line in stats_txt.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = LINE_RE.search(line)
        if match:
            rows.append(
                {
                    "l": int(match.group("l")),
                    "mean_ratio": float(match.group("mean")),
                    "std_ratio": float(match.group("std")),
                    "mean_percent": float(match.group("mean_pct")),
                    "std_percent": float(match.group("std_pct")),
                }
            )
            continue
        if line.lower().startswith("overall"):
            in_overall_section = True
            continue
        if in_overall_section:
            overall_match = OVERALL_RE.search(line)
            if overall_match:
                overall = {
                    "mean_ratio": float(overall_match.group("mean")),
                    "std_ratio": float(overall_match.group("std")),
                    "mean_percent": float(overall_match.group("mean_pct")),
                    "std_percent": float(overall_match.group("std_pct")),
                }
                in_overall_section = False

    if not rows:
        raise ValueError(f"Could not parse any per-mode summary rows from: {stats_txt}")
    if not overall:
        raise ValueError(f"Could not parse overall summary from: {stats_txt}")

    df = pd.DataFrame(rows).sort_values("l").reset_index(drop=True)
    return df, overall


def export_figure(fig: plt.Figure, output_dir: Path, stem: str, dpi: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / f"{stem}.pdf")
    fig.savefig(output_dir / f"{stem}.png", dpi=dpi)
    plt.close(fig)


def plot_transmittance(df: pd.DataFrame, overall: dict[str, float], output_dir: Path, dpi: int) -> None:
    x = df["l"].to_numpy(dtype=int)
    y = df["mean_ratio"].to_numpy(dtype=float)
    yerr = df["std_ratio"].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(5.35, 3.55))

    # 高级学术配色：深海军蓝(主体) + 勃艮第红(均值参考线)
    bar_color = "#2878b5"
    edge_color = "#143d5c"
    err_color = "#143d5c"
    mean_color = "#c23a33"

    ax.bar(
        x,
        y,
        width=0.58,
        color=bar_color,
        edgecolor=edge_color,
        linewidth=1.0,
        zorder=2,
    )
    ax.errorbar(
        x,
        y,
        yerr=yerr,
        fmt="none",
        ecolor=err_color,
        elinewidth=1.2,
        capsize=2.8,
        capthick=1.2,
        zorder=3,
    )
    ax.axhline(
        overall["mean_ratio"],
        color=mean_color,
        linewidth=1.2,
        linestyle=(0, (4, 3)),
        zorder=1,
    )

    ax.set_xlim(x.min() - 0.45, x.max() + 0.45)
    ax.set_xticks(x)
    ax.set_xlabel(r"Azimuthal index $l$")
    ax.set_ylabel("Transmittance", labelpad=10)
    ax.set_ylim(0.0, 1.05)  # 顶部留出 5% 空隙，防止误差棒触顶显得拥挤
    ax.set_yticks([0.0, 0.25, 0.50, 0.75, 1.0])

    for spine in ax.spines.values():
        spine.set_linewidth(0.8)
    ax.tick_params(axis="both", which="major", direction="in", top=True, right=True, pad=6)
    ax.text(
        0.985,
        0.96,
        rf"$\overline{{T}} \approx {overall['mean_ratio']:.2f}$",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9.0,
        color=mean_color,
    )

    export_figure(fig, output_dir, "puremode_transmittance", dpi)


def main() -> None:
    args = parse_args()
    configure_plot_style()
    df, overall = parse_stats_txt(args.stats_txt)
    plot_transmittance(df, overall, args.output_dir, args.dpi)
    print(f"Saved figures to: {args.output_dir.resolve()}")
    print("Generated: puremode_transmittance.[pdf|png]")


if __name__ == "__main__":
    main()
