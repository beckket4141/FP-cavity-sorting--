from __future__ import annotations

import math
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from analysis_common import analytic_peak_families, ensure_dir, write_csv


OUTPUT_DIR = ensure_dir(BASE_DIR / "outputs" / "01_branch_window_screen")
N_VALUES = [9, 15, 30, 50]
RADIUS_MM = 25.0
LR_WINDOW = (0.20, 0.80)


def classify_branch(lr_star: float) -> str:
    if lr_star < LR_WINDOW[0]:
        return "too_short"
    if lr_star > LR_WINDOW[1]:
        return "near_hemispherical_boundary"
    return "practical"


def main() -> None:
    rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for n_modes in N_VALUES:
        peaks = analytic_peak_families(n_modes, k_upper=0.5)
        practical_count = 0
        for peak in peaks:
            lr_star = peak.lr_star
            status = classify_branch(lr_star)
            if status == "practical":
                practical_count += 1
            rows.append(
                {
                    "N": n_modes,
                    "m": peak.m,
                    "k_star": f"{peak.k_star:.12f}",
                    "lr_star": f"{lr_star:.12f}",
                    "L_star_mm": f"{RADIUS_MM * lr_star:.9f}",
                    "status": status,
                }
            )
        summary_rows.append(
            {
                "N": n_modes,
                "math_optimal_branches_under_half_interval": len(peaks),
                "practical_branches_in_lr_window": practical_count,
                "lr_window_min": LR_WINDOW[0],
                "lr_window_max": LR_WINDOW[1],
            }
        )

    csv_path = OUTPUT_DIR / "branch_window_screen.csv"
    summary_csv_path = OUTPUT_DIR / "branch_window_summary.csv"
    write_csv(csv_path, list(rows[0].keys()), rows)
    write_csv(summary_csv_path, list(summary_rows[0].keys()), summary_rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})
    fig, ax = plt.subplots(figsize=(7.6, 4.5), dpi=220)
    ax.axhspan(LR_WINDOW[0], LR_WINDOW[1], color="tab:green", alpha=0.10, label="practical L/R window")
    ax.axhline(LR_WINDOW[0], color="tab:green", linestyle="--", linewidth=1.0)
    ax.axhline(LR_WINDOW[1], color="tab:green", linestyle="--", linewidth=1.0)

    rows_by_n: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        rows_by_n.setdefault(int(row["N"]), []).append(row)

    for n_modes in N_VALUES:
        group = rows_by_n[n_modes]
        count = len(group)
        for idx, row in enumerate(group):
            offset = 0.11 * (idx - 0.5 * (count - 1))
            x = n_modes + offset
            y = float(row["lr_star"])
            status = str(row["status"])
            color = {
                "practical": "tab:blue",
                "too_short": "tab:orange",
                "near_hemispherical_boundary": "tab:red",
            }[status]
            ax.scatter([x], [y], color=color, s=42, zorder=3)
            ax.text(x + 0.13, y, f"m={row['m']}", fontsize=8, va="center")

    ax.set_xticks(N_VALUES)
    ax.set_xlabel("continuous mode count N")
    ax.set_ylabel(r"analytic branch location $L/R=\sin^2(\pi m/N)$")
    ax.set_title("Optimal branches after a practical cavity-length window")
    ax.grid(True, alpha=0.20)

    from matplotlib.lines import Line2D

    legend_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:blue", markersize=7, label="practical"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:orange", markersize=7, label="too short"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:red", markersize=7, label="near hemispherical boundary"),
    ]
    ax.legend(handles=legend_handles, frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "branch_window_screen.png")
    plt.close(fig)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {summary_csv_path}")
    print(f"Wrote: {OUTPUT_DIR / 'branch_window_screen.png'}")


if __name__ == "__main__":
    main()
