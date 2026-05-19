"""Plot 9D full-load percentage heatmap with per-cell error bars.

Data source:
  - triplicate_full9_aggregate.xlsx
    - 1_percentage
    - 2_percentage
    - 3_percentage

Output:
  - 输出图/9维满载百分比热图_含误差条.pdf
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import seaborn as sns
from openpyxl import load_workbook


LOCK_RE = re.compile(r"lock\s*=\s*(\d+)", re.IGNORECASE)
CH_RE = re.compile(r"ch\s*=\s*(\d+)", re.IGNORECASE)
T975_DF2 = 4.302652729911275  # t(0.975, df=2), n=3 independent runs
ERRORBAR_MODES = ("ci95_t", "sd", "sem", "minmax")
MODE_TO_SUFFIX = {
    "ci95_t": "CI95_t",
    "sd": "SD",
    "sem": "SEM",
    "minmax": "MinMax",
}
MODE_TO_TITLE = {
    "ci95_t": r"mean $\pm$ 95\%CI (t-distribution, $n=3$)",
    "sd": r"mean $\pm$ SD ($n=3$)",
    "sem": r"mean $\pm$ SEM ($n=3$)",
    "minmax": r"mean with Min-Max envelope ($n=3$)",
}


def configure_plot_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIX Two Text", "STIXGeneral", "Times New Roman"],
            "mathtext.fontset": "stix",
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.linewidth": 0.6,
            "xtick.labelsize": 8.8,
            "ytick.labelsize": 8.8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.width": 0.5,
            "ytick.major.width": 0.5,
            "xtick.major.size": 3.0,
            "ytick.major.size": 3.0,
            "figure.dpi": 150,
        }
    )


def parse_percentage_sheet(path: Path, sheet_name: str) -> tuple[list[int], list[int], np.ndarray]:
    wb = load_workbook(path, read_only=True, data_only=True)
    if sheet_name not in wb.sheetnames:
        wb.close()
        raise KeyError(f"Missing sheet '{sheet_name}' in {path.name}")

    ws = wb[sheet_name]
    header = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    locks: list[int] = []
    for hv in header[1:]:
        if hv is None:
            continue
        m = LOCK_RE.search(str(hv))
        if m:
            locks.append(int(m.group(1)))

    if not locks:
        wb.close()
        raise ValueError(f"Sheet {sheet_name} has no lock headers")

    channels: list[int] = []
    rows: list[list[float]] = []

    for r in range(2, ws.max_row + 1):
        lv = ws.cell(r, 1).value
        if lv is None:
            break
        m = CH_RE.search(str(lv))
        if not m:
            continue
        ch = int(m.group(1))
        vals = []
        for c in range(2, 2 + len(locks)):
            v = ws.cell(r, c).value
            vals.append(float(v) if v is not None else float("nan"))
        channels.append(ch)
        rows.append(vals)
        if len(channels) == len(locks):
            break

    wb.close()

    if len(channels) != len(locks):
        raise ValueError(f"{sheet_name} parsed shape is not square: {len(channels)}x{len(locks)}")

    return channels, locks, np.asarray(rows, dtype=float)


def build_statistics(agg_xlsx: Path) -> tuple[list[int], list[int], np.ndarray]:
    sheet_names = ["1_percentage", "2_percentage", "3_percentage"]
    mats = []
    ref_channels: list[int] | None = None
    ref_locks: list[int] | None = None

    for sn in sheet_names:
        channels, locks, mat = parse_percentage_sheet(agg_xlsx, sn)
        if ref_channels is None:
            ref_channels = channels
            ref_locks = locks
        else:
            if channels != ref_channels or locks != ref_locks:
                raise ValueError(f"Axis mismatch in sheet {sn}")
        mats.append(mat)

    stack = np.stack(mats, axis=0)  # (3, 9, 9)
    return ref_channels or [], ref_locks or [], stack


def compute_error_stats(stack: np.ndarray) -> dict[str, np.ndarray]:
    n = stack.shape[0]
    mean = np.mean(stack, axis=0)
    sd = np.std(stack, axis=0, ddof=1)
    sem = sd / np.sqrt(n)
    ci95_t = T975_DF2 * sem
    min_v = np.min(stack, axis=0)
    max_v = np.max(stack, axis=0)
    return {
        "mean": mean,
        "sd": sd,
        "sem": sem,
        "ci95_t": ci95_t,
        "min": min_v,
        "max": max_v,
    }


def plot_heatmap(
    channels: list[int],
    locks: list[int],
    stats: dict[str, np.ndarray],
    mode: str,
    out_pdf: Path,
    dpi: int,
) -> None:
    mean_pct = stats["mean"]
    annot = np.empty_like(mean_pct, dtype=object)
    for i in range(mean_pct.shape[0]):
        for j in range(mean_pct.shape[1]):
            # 只有对角线（主要信号）标注完整误差范围，非对角线（近0串扰）仅标注均值
            if i == j:
                if mode == "minmax":
                    annot[i, j] = f"{mean_pct[i, j]:.2f}%\n[{stats['min'][i, j]:.2f}, {stats['max'][i, j]:.2f}]%"
                else:
                    annot[i, j] = f"{mean_pct[i, j]:.2f}\n±{stats[mode][i, j]:.2f}%"
            else:
                annot[i, j] = f"{mean_pct[i, j]:.2f}"

    fig, ax = plt.subplots(figsize=(7.0, 6.0), dpi=dpi)
    cmap_name = "YlGnBu"
    vmin, vmax = 0.0, 100.0
    from matplotlib.colors import LogNorm

    # Clip lower bound to 0.1 for log scale to avoid log(0) issues, max to 100.
    # Alternatively use PowerNorm(gamma=0.5) but LogNorm is very standard for scientific heatmaps
    norm = LogNorm(vmin=0.1, vmax=100.0)

    # Note: We need to clip mean_pct so LogNorm doesn't complain about 0 or negative values if any exist
    mean_pct_clipped = np.clip(mean_pct, 0.1, 100.0)

    hm = sns.heatmap(
        mean_pct_clipped,
        ax=ax,
        cmap="viridis", # "viridis", "magma" or "YlGnBu" - viridis is often considered more scientific
        norm=norm,
        square=True,
        linewidths=0.5,
        linecolor="#999999", # gray lines to make cell boundaries visible
        annot=annot,
        fmt="",
        annot_kws={"size": 6.2},
        xticklabels=[f"${l}$" for l in locks],
        yticklabels=[f"${c}$" for c in channels],
        cbar_kws={
            "label": r"Intensity share (%)",
            "shrink": 0.83,
            "aspect": 26,
            "ticks": [0.1, 1, 10, 100],
            "format": ticker.FuncFormatter(lambda y, pos: f"{y:g}"),
        },
    )

    # Adaptive annotation color for readability.
    cmap = plt.get_cmap("viridis")
    for txt in ax.texts:
        x, y = txt.get_position()
        j, i = int(x), int(y)
        if 0 <= i < mean_pct.shape[0] and 0 <= j < mean_pct.shape[1]:
            # Use real value for color mapping matching
            val = max(0.1, mean_pct[i, j])
            rgba = cmap(norm(val))
            lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
            txt.set_color("black" if lum > 0.48 else "white")

    ax.set_xlabel(r"Target mode $l$ (lock state)")
    ax.set_ylabel(r"Detection channel $l$")
    ax.tick_params(axis="both", length=0)

    cbar = hm.collections[0].colorbar
    
    # Remove minor ticks (the small black lines) on the colorbar
    cbar.ax.minorticks_off()
    cbar.ax.tick_params(direction="in", width=0.5, length=3.0)

    fig.tight_layout(pad=0.5)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, format="pdf", dpi=dpi, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Plot 9D full-load percentage heatmap with per-cell error bars.")
    parser.add_argument(
        "--agg-xlsx",
        type=Path,
        default=script_dir.parent / "triplicate_full9_aggregate.xlsx",
        help="Path to triplicate aggregate workbook.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=script_dir / "输出图",
        help="Output directory.",
    )
    parser.add_argument(
        "--errorbar-mode",
        type=str,
        default="all",
        choices=["all", *ERRORBAR_MODES],
        help="Errorbar mode: all | ci95_t | sd | sem | minmax (default: all).",
    )
    parser.add_argument("--dpi", type=int, default=300, help="Figure DPI (default: 300).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.agg_xlsx.exists():
        raise FileNotFoundError(f"Missing aggregate workbook: {args.agg_xlsx}")

    configure_plot_style()
    channels, locks, stack = build_statistics(args.agg_xlsx)
    stats = compute_error_stats(stack)

    modes = ERRORBAR_MODES if args.errorbar_mode == "all" else (args.errorbar_mode,)
    saved_paths: list[Path] = []
    for mode in modes:
        out_pdf = args.out_dir / f"9维满载百分比热图_含误差条_{MODE_TO_SUFFIX[mode]}.pdf"
        plot_heatmap(channels, locks, stats, mode, out_pdf, args.dpi)
        saved_paths.append(out_pdf)

        # Keep legacy output name mapped to CI95(t) for compatibility.
        if mode == "ci95_t":
            legacy_pdf = args.out_dir / "9维满载百分比热图_含误差条.pdf"
            plot_heatmap(channels, locks, stats, mode, legacy_pdf, args.dpi)
            saved_paths.append(legacy_pdf)

    for p in saved_paths:
        print(f"Saved: {p.resolve()}")


if __name__ == "__main__":
    main()
