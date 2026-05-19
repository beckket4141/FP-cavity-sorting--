from __future__ import annotations

from engineering_screening_common import (
    OUTPUT_ROOT,
    REPRESENTATIVE_N_VALUES,
    SCENARIOS,
    analytic_branch_rows,
    ensure_dir,
    scenario_summary_rows,
    write_csv,
)


def main() -> None:
    outdir = ensure_dir(OUTPUT_ROOT / "05_dual_scenario_effective_branches")

    rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        scenario_rows = analytic_branch_rows(scenario)
        rows.extend(scenario_rows)
        summary_rows.extend(scenario_summary_rows(scenario_rows, scenario.name))

    details_csv_path = outdir / "dual_scenario_branch_details.csv"
    summary_csv_path = outdir / "dual_scenario_branch_summary.csv"
    representative_rows = [row for row in rows if int(row["N"]) in REPRESENTATIVE_N_VALUES]
    representative_csv_path = outdir / "representative_case_branches.csv"
    write_csv(details_csv_path, list(rows[0].keys()), rows)
    write_csv(summary_csv_path, list(summary_rows[0].keys()), summary_rows)
    write_csv(representative_csv_path, list(representative_rows[0].keys()), representative_rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2), dpi=220, sharey=True)

    for ax, scenario in zip(axes, SCENARIOS, strict=True):
        subset = [row for row in summary_rows if row["scenario"] == scenario.name]
        xs = [int(row["N"]) for row in subset]
        math_counts = [int(row["math_optimal_branches"]) for row in subset]
        geometry_counts = [int(row["geometry_engineering_branches"]) for row in subset]
        final_counts = [int(row["final_engineering_branches"]) for row in subset]
        ax.plot(xs, math_counts, color="black", linewidth=1.5, label="mathematical branches")
        ax.plot(xs, geometry_counts, color="tab:blue", linewidth=1.5, label="geometry-screened branches")
        ax.plot(xs, final_counts, color="tab:green", linewidth=1.5, label="final engineering branches")
        ax.axvline(int(scenario.finesse // scenario.tau0), color="tab:red", linestyle="--", linewidth=1.0)
        ax.set_title(scenario.name)
        ax.set_xlabel("continuous mode count N")
        ax.grid(True, alpha=0.20)

    axes[0].set_ylabel("branch count")
    axes[1].legend(frameon=False, loc="upper right")
    fig.suptitle("Mathematical branches vs engineering-effective branches")
    fig.tight_layout()
    fig.savefig(outdir / "branch_count_comparison.png")
    plt.close(fig)

    print(f"Wrote: {details_csv_path}")
    print(f"Wrote: {summary_csv_path}")
    print(f"Wrote: {representative_csv_path}")
    print(f"Wrote: {outdir / 'branch_count_comparison.png'}")


if __name__ == "__main__":
    main()
