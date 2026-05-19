from __future__ import annotations

from engineering_screening_common import (
    CURRENT_PLATFORM,
    N_SCAN_VALUES,
    OUTPUT_ROOT,
    analytic_branch_rows,
    ensure_dir,
    scenario_summary_rows,
    write_csv,
)


def main() -> None:
    outdir = ensure_dir(OUTPUT_ROOT / "04_geometry_engineering_screen")
    rows = analytic_branch_rows(CURRENT_PLATFORM)
    summary_rows = scenario_summary_rows(rows, CURRENT_PLATFORM.name)

    csv_path = outdir / "geometry_branch_details.csv"
    summary_csv_path = outdir / "geometry_branch_summary.csv"
    write_csv(csv_path, list(rows[0].keys()), rows)
    write_csv(summary_csv_path, list(summary_rows[0].keys()), summary_rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})
    fig, axes = plt.subplots(2, 1, figsize=(8.4, 8.0), dpi=220, sharex=True)

    for ax, metric_key, threshold, ylabel, title in [
        (
            axes[0],
            "w0_um",
            CURRENT_PLATFORM.w0_experimental_min_um,
            r"plane-mirror waist $w_0$ ($\mu$m)",
            "Plane-mirror waist across analytic branches (soft-band screening)",
        ),
        (
            axes[1],
            "w_curved_um",
            CURRENT_PLATFORM.w_curved_max_um,
            r"curved-mirror spot size $w_2$ ($\mu$m)",
            "Curved-mirror spot size near the hemispherical boundary",
        ),
    ]:
        for row in rows:
            n_modes = int(row["N"])
            x = n_modes + 0.08 * (int(row["m"]) - 0.5 * n_modes) / n_modes
            y = float(row[metric_key])
            if row["geometry_screen_status"] == "hard_fail":
                color = "tab:gray"
            elif row["geometry_screen_status"] == "warning":
                color = "tab:orange"
            else:
                color = "tab:blue"
            ax.scatter([x], [y], color=color, s=28, alpha=0.9)
        if metric_key == "w0_um":
            ax.axhline(
                CURRENT_PLATFORM.w0_experimental_min_um,
                color="tab:orange",
                linestyle="--",
                linewidth=1.1,
            )
            ax.axhline(
                CURRENT_PLATFORM.w0_comfortable_min_um,
                color="tab:green",
                linestyle=":",
                linewidth=1.2,
            )
        else:
            ax.axhline(threshold, color="tab:red", linestyle="--", linewidth=1.1)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.20)

    axes[1].set_xlabel("continuous mode count N")
    axes[1].set_xticks([5, 10, 15, 20, 25, 30, 35, 40, 45, 50])

    legend_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:blue", markersize=7, label="pass"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:orange", markersize=7, label="warning"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="tab:gray", markersize=7, label="hard fail"),
        Line2D([0], [0], color="tab:orange", linestyle="--", linewidth=1.1, label=r"$w_0=47\,\mu$m"),
        Line2D([0], [0], color="tab:green", linestyle=":", linewidth=1.2, label=r"$w_0=50\,\mu$m"),
        Line2D([0], [0], color="tab:red", linestyle="--", linewidth=1.1, label=r"$w_2$ threshold"),
    ]
    axes[0].legend(handles=legend_handles, frameon=False, loc="upper right")

    fig.tight_layout()
    fig.savefig(outdir / "geometry_branch_scales.png")
    plt.close(fig)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {summary_csv_path}")
    print(f"Wrote: {outdir / 'geometry_branch_scales.png'}")


if __name__ == "__main__":
    main()
