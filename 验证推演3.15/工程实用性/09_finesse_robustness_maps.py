from __future__ import annotations

import csv
from pathlib import Path

from engineering_screening_common import (
    OUTPUT_ROOT,
    ensure_dir,
    required_nominal_rho,
)


RHO_ACTUAL_FLOORS = [1.00, 1.05]
RHO_NOMINAL_VALUES = [1.05, 1.10, 1.15, 1.20]
SHORTFALL_EXAMPLES = [0.02, 0.05, 0.10]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_band_justification_table(outdir: Path) -> None:
    rows: list[dict[str, object]] = []
    for rho_actual_floor in [1.00, 1.05]:
        for shortfall in SHORTFALL_EXAMPLES:
            required_rho = required_nominal_rho(rho_actual_floor, shortfall)
            rows.append(
                {
                    "rho_actual_floor": f"{rho_actual_floor:.12f}",
                    "worst_case_finesse_shortfall": f"{shortfall:.12f}",
                    "required_nominal_rho": f"{required_rho:.12f}",
                }
            )

    outpath = outdir / "rho_band_justification_table.csv"
    with outpath.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    scan_dir = OUTPUT_ROOT / "08_finesse_robustness_scan"
    reflectivity_rows = load_rows(scan_dir / "reflectivity_to_finesse_scan.csv")
    anchor_rows = load_rows(scan_dir / "current_design_finesse_anchor.csv")

    outdir = ensure_dir(OUTPUT_ROOT / "09_finesse_robustness_maps")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=220)
    shortfalls = [0.001 * idx for idx in range(0, 151)]
    for rho_actual_floor, color in zip(RHO_ACTUAL_FLOORS, ["tab:blue", "tab:green"], strict=True):
        required_values = [required_nominal_rho(rho_actual_floor, shortfall) for shortfall in shortfalls]
        ax.plot(
            [100.0 * shortfall for shortfall in shortfalls],
            required_values,
            linewidth=1.8,
            color=color,
            label=rf"require $\rho_{{actual}} \geq {rho_actual_floor:.2f}$",
        )
    for nominal_rho in RHO_NOMINAL_VALUES:
        ax.axhline(nominal_rho, color="0.82", linestyle="--", linewidth=0.9)
        ax.text(11.8, nominal_rho + 0.002, rf"$\rho_{{nom}}={nominal_rho:.2f}$", fontsize=8, va="bottom")
    ax.set_xlabel("worst-case finesse shortfall (%)")
    ax.set_ylabel(r"required nominal $\rho$")
    ax.set_title(r"Nominal $\rho$ must cover the finesse shortfall budget")
    ax.grid(True, alpha=0.20)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(outdir / "rho_required_vs_finesse_shortfall.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=220)
    target_finesse_values = sorted({float(row["finesse_nominal"]) for row in reflectivity_rows})
    colors = ["tab:blue", "tab:green", "tab:orange", "tab:red", "tab:purple"]
    for finesse_nominal, color in zip(target_finesse_values, colors, strict=True):
        subset = [
            row
            for row in reflectivity_rows
            if abs(float(row["finesse_nominal"]) - finesse_nominal) < 1.0e-9
        ]
        subset.sort(key=lambda row: float(row["reflectivity_abs_error"]))
        ax.plot(
            [100.0 * float(row["reflectivity_abs_error"]) for row in subset],
            [100.0 * float(row["finesse_relative_error"]) for row in subset],
            linewidth=1.7,
            marker="o",
            markersize=3.5,
            color=color,
            label=rf"$\mathcal{{F}}_{{target}}={finesse_nominal:g}$",
        )
    ax.axhline(0.0, color="black", linewidth=0.9)
    ax.axvline(0.0, color="black", linewidth=0.9)
    ax.set_xlabel("reflectivity error (percentage points)")
    ax.set_ylabel(r"relative finesse error $\Delta \mathcal{F}/\mathcal{F}$ (%)")
    ax.set_title(r"The same $\Delta R$ amplifies more strongly at higher target finesse")
    ax.grid(True, alpha=0.20)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(outdir / "reflectivity_error_to_finesse_gain.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=220)
    rel_errors = [-0.10 + 0.001 * idx for idx in range(201)]
    colors = ["tab:blue", "tab:green", "tab:orange", "tab:red"]
    for rho_nominal, color in zip(RHO_NOMINAL_VALUES, colors, strict=True):
        rho_actual_values = [rho_nominal * (1.0 + rel_error) for rel_error in rel_errors]
        ax.plot(
            [100.0 * rel_error for rel_error in rel_errors],
            rho_actual_values,
            linewidth=1.8,
            color=color,
            label=rf"$\rho_{{nom}}={rho_nominal:.2f}$",
        )
    for threshold in [1.00, 1.05, 1.10]:
        ax.axhline(threshold, color="0.82", linestyle="--", linewidth=0.9)
        ax.text(7.8, threshold + 0.002, rf"$\rho={threshold:.2f}$", fontsize=8, va="bottom")
    ax.set_xlabel("achieved finesse relative error (%)")
    ax.set_ylabel(r"actual $\rho$")
    ax.set_title(r"How achieved finesse drift moves the actual $\rho$ band")
    ax.grid(True, alpha=0.20)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(outdir / "rho_nominal_to_rho_actual_bands.png")
    plt.close(fig)

    anchor = anchor_rows[0]
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.9), dpi=220)

    finesse_values = [float(anchor["finesse_nominal"]), float(anchor["finesse_measured"])]
    axes[0].bar(["nominal", "measured"], finesse_values, color=["tab:blue", "tab:green"])
    axes[0].set_ylabel(r"$\mathcal{F}$")
    axes[0].set_title(r"Current 9-mode finesse anchor")
    axes[0].grid(True, axis="y", alpha=0.20)
    for idx, value in enumerate(finesse_values):
        axes[0].text(idx, value + 0.5, f"{value:.2f}", ha="center", va="bottom", fontsize=9)

    rho_values = [float(anchor["rho_nominal"]), float(anchor["rho_measured"])]
    axes[1].bar(["nominal", "measured"], rho_values, color=["tab:blue", "tab:green"])
    axes[1].set_ylabel(r"$\rho$")
    axes[1].set_title(r"$\rho = \mathcal{F}/(N\tau_0)$ for $N=9$, $\tau_0=3$")
    axes[1].grid(True, axis="y", alpha=0.20)
    for idx, value in enumerate(rho_values):
        axes[1].text(idx, value + 0.02, f"{value:.3f}", ha="center", va="bottom", fontsize=9)

    fig.suptitle(
        (
            f"Measured finesse is {100.0 * float(anchor['finesse_relative_error']):.1f}% above nominal; "
            f"equivalent delta R = {float(anchor['reflectivity_abs_error']):.4f}"
        ),
        fontsize=10,
    )
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.92])
    fig.savefig(outdir / "current_design_29p8_vs_31p35_anchor.png")
    plt.close(fig)

    build_band_justification_table(outdir)

    print(f"Wrote: {outdir / 'rho_required_vs_finesse_shortfall.png'}")
    print(f"Wrote: {outdir / 'reflectivity_error_to_finesse_gain.png'}")
    print(f"Wrote: {outdir / 'rho_nominal_to_rho_actual_bands.png'}")
    print(f"Wrote: {outdir / 'current_design_29p8_vs_31p35_anchor.png'}")
    print(f"Wrote: {outdir / 'rho_band_justification_table.csv'}")


if __name__ == "__main__":
    main()
