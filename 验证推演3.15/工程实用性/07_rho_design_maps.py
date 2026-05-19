from __future__ import annotations

import csv
from pathlib import Path

from engineering_screening_common import (
    OUTPUT_ROOT,
    ceiling_with_tolerance,
    ensure_dir,
    peak_headroom_ratio,
    required_finesse,
)


RHO_VALUES = [1.00, 1.02, 1.05, 1.10, 1.15, 1.20, 1.30]
TAU0_VALUES = [3.0, 4.0, 5.0, 6.0]
REPRESENTATIVE_N_VALUES = [9, 12, 30, 50]
RECOMMENDED_RHOS = [1.05, 1.10, 1.20]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def summary_lookup(rows: list[dict[str, str]], scenario: str, n_modes: int, tau0: float, rho: float) -> dict[str, str]:
    for row in rows:
        if (
            row["scenario"] == scenario
            and int(row["N"]) == n_modes
            and abs(float(row["tau0"]) - tau0) < 1.0e-9
            and abs(float(row["rho"]) - rho) < 1.0e-9
        ):
            return row
    raise KeyError((scenario, n_modes, tau0, rho))


def build_design_table(summary_rows: list[dict[str, str]], outdir: Path) -> None:
    table_rows: list[dict[str, object]] = []
    for tau0 in TAU0_VALUES:
        for n_modes in REPRESENTATIVE_N_VALUES:
            current_row = summary_lookup(summary_rows, "CURRENT_PLATFORM", n_modes, tau0, 1.10)
            relaxed_row = summary_lookup(summary_rows, "COMPARISON_RELAXED", n_modes, tau0, 1.10)
            table_rows.append(
                {
                    "N": n_modes,
                    "tau0": f"{tau0:.1f}",
                    "F_min_exact": f"{required_finesse(n_modes, tau0, 1.00):.3f}",
                    "F_rho_1p05_exact": f"{required_finesse(n_modes, tau0, 1.05):.3f}",
                    "F_rho_1p10_exact": f"{required_finesse(n_modes, tau0, 1.10):.3f}",
                    "F_rho_1p20_exact": f"{required_finesse(n_modes, tau0, 1.20):.3f}",
                    "F_min_ceiling": ceiling_with_tolerance(required_finesse(n_modes, tau0, 1.00)),
                    "F_rho_1p05_ceiling": ceiling_with_tolerance(required_finesse(n_modes, tau0, 1.05)),
                    "F_rho_1p10_ceiling": ceiling_with_tolerance(required_finesse(n_modes, tau0, 1.10)),
                    "F_rho_1p20_ceiling": ceiling_with_tolerance(required_finesse(n_modes, tau0, 1.20)),
                    "current_geometry_branches_at_rho_1p10": current_row["geometry_engineering_branches"],
                    "current_final_branches_at_rho_1p10": current_row["final_engineering_branches"],
                    "current_final_branch_list_at_rho_1p10": current_row["final_branch_list"],
                    "relaxed_geometry_branches_at_rho_1p10": relaxed_row["geometry_engineering_branches"],
                    "relaxed_final_branches_at_rho_1p10": relaxed_row["final_engineering_branches"],
                    "relaxed_final_branch_list_at_rho_1p10": relaxed_row["final_branch_list"],
                }
            )

    import csv as csv_module

    outpath = outdir / "rho_design_table.csv"
    with outpath.open("w", encoding="utf-8", newline="") as handle:
        writer = csv_module.DictWriter(handle, fieldnames=list(table_rows[0].keys()))
        writer.writeheader()
        writer.writerows(table_rows)


def main() -> None:
    scan_dir = OUTPUT_ROOT / "06_rho_margin_scan"
    summary_path = scan_dir / "rho_margin_scan_summary.csv"
    summary_rows = load_rows(summary_path)

    outdir = ensure_dir(OUTPUT_ROOT / "07_rho_design_maps")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.0), dpi=220, sharex=True, sharey=True)
    n_values = list(range(5, 51))
    for ax, tau0 in zip(axes.flat, TAU0_VALUES, strict=True):
        ax.plot(n_values, [required_finesse(n_modes, tau0, 1.00) for n_modes in n_values], color="black", linewidth=1.6, label=r"$\rho=1.00$")
        ax.plot(n_values, [required_finesse(n_modes, tau0, 1.05) for n_modes in n_values], color="tab:blue", linestyle="--", linewidth=1.3, label=r"$\rho=1.05$")
        ax.plot(n_values, [required_finesse(n_modes, tau0, 1.10) for n_modes in n_values], color="tab:green", linestyle="-.", linewidth=1.3, label=r"$\rho=1.10$")
        ax.plot(n_values, [required_finesse(n_modes, tau0, 1.20) for n_modes in n_values], color="tab:red", linestyle=":", linewidth=1.5, label=r"$\rho=1.20$")
        for n_modes in REPRESENTATIVE_N_VALUES:
            ax.axvline(n_modes, color="0.85", linewidth=0.8)
        ax.set_title(rf"$\tau_0={tau0:.0f}$")
        ax.grid(True, alpha=0.20)
        ax.set_xlabel("continuous mode count $N$")
    axes[0, 0].set_ylabel("required finesse $\\mathcal{F}$")
    axes[1, 0].set_ylabel("required finesse $\\mathcal{F}$")
    axes[0, 1].legend(frameon=False, loc="upper left")
    fig.suptitle("Required finesse lines for fixed $\\rho$")
    fig.tight_layout()
    fig.savefig(outdir / "required_finesse_lines.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.0, 4.4), dpi=220)
    rho_dense = [1.0 + 0.0015 * idx for idx in range(int((1.30 - 1.0) / 0.0015) + 1)]
    ax.plot(rho_dense, [100.0 * peak_headroom_ratio(rho) for rho in rho_dense], color="tab:blue", linewidth=1.8)
    for rho in RECOMMENDED_RHOS:
        ax.axvline(rho, color="0.80", linestyle="--", linewidth=0.9)
        ax.scatter([rho], [100.0 * peak_headroom_ratio(rho)], color="tab:blue", s=18, zorder=3)
    ax.set_xlabel(r"design margin factor $\rho$")
    ax.set_ylabel(r"relative peak headroom $100(1-1/\rho)$ (%)")
    ax.set_title(r"$\rho$ compresses distance above the analytic boundary")
    ax.grid(True, alpha=0.20)
    fig.tight_layout()
    fig.savefig(outdir / "rho_headroom_curve.png")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2), dpi=220, sharey=True)
    plot_rhos = [0.95] + RHO_VALUES
    for ax, scenario_name in zip(axes, ["CURRENT_PLATFORM", "COMPARISON_RELAXED"], strict=True):
        for n_modes, color in zip(REPRESENTATIVE_N_VALUES, ["tab:blue", "tab:green", "tab:orange", "tab:red"], strict=True):
            values = [0]
            for rho in RHO_VALUES:
                row = summary_lookup(summary_rows, scenario_name, n_modes, 3.0, rho)
                values.append(int(row["final_engineering_branches"]))
            ax.plot(plot_rhos, values, marker="o", linewidth=1.5, markersize=3.5, color=color, label=rf"$N={n_modes}$")
        ax.axvline(1.0, color="black", linestyle="--", linewidth=1.0)
        ax.set_title(scenario_name)
        ax.set_xlabel(r"design margin factor $\rho$")
        ax.grid(True, alpha=0.20)
    axes[0].set_ylabel("final engineering branches")
    axes[1].legend(frameon=False, loc="upper left")
    fig.suptitle(r"Final branch counts for $\tau_0=3$ under fixed $\rho$")
    fig.tight_layout()
    fig.savefig(outdir / "rho_branch_counts.png")
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.0), dpi=220, sharex=True, sharey=True)
    for ax, n_modes in zip(axes.flat, REPRESENTATIVE_N_VALUES, strict=True):
        for scenario_name, color in [("CURRENT_PLATFORM", "tab:blue"), ("COMPARISON_RELAXED", "tab:green")]:
            widths = []
            for rho in RHO_VALUES:
                row = summary_lookup(summary_rows, scenario_name, n_modes, 3.0, rho)
                widths.append(float(row["max_final_platform_width_L_mm"]))
            ax.plot(RHO_VALUES, widths, marker="o", linewidth=1.5, markersize=3.5, color=color, label=scenario_name)
        ax.set_title(rf"$N={n_modes}$, $\tau_0=3$")
        ax.grid(True, alpha=0.20)
        ax.set_xlabel(r"design margin factor $\rho$")
    axes[0, 0].set_ylabel("max final platform width $\\Delta L$ (mm)")
    axes[1, 0].set_ylabel("max final platform width $\\Delta L$ (mm)")
    axes[0, 1].legend(frameon=False, loc="upper left")
    fig.suptitle(r"Representative platform widths grow with $\rho$ but remain $N$-dependent")
    fig.tight_layout()
    fig.savefig(outdir / "rho_platform_width_representatives.png")
    plt.close(fig)

    build_design_table(summary_rows, outdir)

    print(f"Wrote: {outdir / 'required_finesse_lines.png'}")
    print(f"Wrote: {outdir / 'rho_headroom_curve.png'}")
    print(f"Wrote: {outdir / 'rho_branch_counts.png'}")
    print(f"Wrote: {outdir / 'rho_platform_width_representatives.png'}")
    print(f"Wrote: {outdir / 'rho_design_table.csv'}")


if __name__ == "__main__":
    main()
