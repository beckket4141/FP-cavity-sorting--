from __future__ import annotations

import math
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from analysis_common import analytic_peak_families, ensure_dir, local_platform_formula, write_csv


OUTPUT_DIR = ensure_dir(BASE_DIR / "outputs" / "03_relative_margin_filter")
N_VALUES = [9, 15, 30, 50]
RADIUS_MM = 25.0
LR_WINDOW = (0.20, 0.80)
ETA = 0.90
MIN_PLATFORM_L_MM = 0.10


def geometry_status(lr_star: float) -> str:
    if lr_star < LR_WINDOW[0]:
        return "too_short"
    if lr_star > LR_WINDOW[1]:
        return "near_hemispherical_boundary"
    return "in_window"


def main() -> None:
    rows: list[dict[str, object]] = []

    for n_modes in N_VALUES:
        delta = ETA / n_modes
        for peak in analytic_peak_families(n_modes, k_upper=0.5):
            interval = local_platform_formula(n_modes, peak.m, delta)
            if interval is None:
                raise RuntimeError(f"No platform for N={n_modes}, m={peak.m}, delta={delta}")
            lr_star = peak.lr_star
            g_status = geometry_status(lr_star)
            width_lr = interval.width_lr
            width_l = RADIUS_MM * width_lr
            passes_geometry = g_status == "in_window"
            passes_platform = width_l >= MIN_PLATFORM_L_MM
            final_status = "engineering_feasible" if passes_geometry and passes_platform else "screened_out"
            rows.append(
                {
                    "N": n_modes,
                    "m": peak.m,
                    "eta": f"{ETA:.6f}",
                    "delta": f"{delta:.12f}",
                    "k_star": f"{peak.k_star:.12f}",
                    "lr_star": f"{lr_star:.12f}",
                    "L_star_mm": f"{RADIUS_MM * lr_star:.9f}",
                    "geometry_status": g_status,
                    "platform_left_lr": f"{interval.left_lr:.12f}",
                    "platform_right_lr": f"{interval.right_lr:.12f}",
                    "platform_width_lr": f"{width_lr:.12f}",
                    "platform_width_L_mm": f"{width_l:.9f}",
                    "passes_min_platform_width": "yes" if passes_platform else "no",
                    "final_status": final_status,
                }
            )

    csv_path = OUTPUT_DIR / "relative_margin_filter.csv"
    write_csv(csv_path, list(rows[0].keys()), rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})
    fig, ax = plt.subplots(figsize=(7.8, 4.5), dpi=220)
    ax.axhline(MIN_PLATFORM_L_MM, color="tab:red", linestyle="--", linewidth=1.1, label="minimum practical platform width")

    rows_by_n: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        rows_by_n.setdefault(int(row["N"]), []).append(row)

    for n_modes in N_VALUES:
        group = rows_by_n[n_modes]
        count = len(group)
        for idx, row in enumerate(group):
            offset = 0.11 * (idx - 0.5 * (count - 1))
            x = n_modes + offset
            y = float(row["platform_width_L_mm"])
            color = "tab:blue" if row["final_status"] == "engineering_feasible" else "tab:gray"
            ax.scatter([x], [y], color=color, s=42, zorder=3)
            ax.text(x + 0.13, y, f"m={row['m']}", fontsize=8, va="center")

    ax.set_xticks(N_VALUES)
    ax.set_xlabel("continuous mode count N")
    ax.set_ylabel("platform width in L (mm)")
    ax.set_title(r"Engineering-screened optimal branches at fixed relative margin $\eta=N\delta=0.9$")
    ax.grid(True, alpha=0.20)

    from matplotlib.lines import Line2D

    legend_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:blue", markersize=7, label="passes geometry + width filter"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:gray", markersize=7, label="screened out"),
    ]
    ax.legend(handles=legend_handles, frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "relative_margin_filter.png")
    plt.close(fig)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {OUTPUT_DIR / 'relative_margin_filter.png'}")


if __name__ == "__main__":
    main()
