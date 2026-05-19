from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lg_mode_tools import (
    canonical_scaled_eta,
    format_pct,
    ideal_p1_leakage_power,
    ideal_target_overlap_power,
    lg_mode_cartesian,
    make_square_grid,
    overlap_power,
    ring_peak_radius,
    rms_radius,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ideal LG_{0}^{l} to FP-cavity LG_{0}^{l} overlap and radial leakage."
    )
    parser.add_argument("--l-max", type=int, default=8)
    parser.add_argument("--strategy", choices=["same_w0", "scaled_w0"], default="same_w0")
    parser.add_argument(
        "--eta-list",
        type=str,
        default="0.40,0.55,0.70,0.85,1.00,1.15,1.30",
        help="Comma-separated eta = w_in / w_cav values for the custom scan.",
    )
    parser.add_argument(
        "--include-z-offset",
        action="store_true",
        help="Additionally compute a numerical overlap scan for waist-position offsets.",
    )
    parser.add_argument("--output-prefix", type=str, default="ideal_")
    return parser.parse_args()


def canonical_rows(l_max: int) -> list[dict]:
    rows: list[dict] = []
    for l in range(l_max + 1):
        for scenario, eta in [("same_w0", 1.0), ("scaled_w0", canonical_scaled_eta(l))]:
            rows.append(
                {
                    "scenario": scenario,
                    "l": l,
                    "eta": eta,
                    "target_overlap_power": ideal_target_overlap_power(l, eta),
                    "p1_leakage_power": ideal_p1_leakage_power(l, eta),
                    "ring_peak_over_w_cav": ring_peak_radius(l, 1.0),
                    "rms_radius_over_w_cav": rms_radius(l, 1.0),
                }
            )
    return rows


def custom_scan_rows(l_max: int, strategy: str, eta_values: list[float]) -> list[dict]:
    rows: list[dict] = []
    sampled_l = sorted({0, 1, 2, min(4, l_max), l_max})
    sampled_l = [l for l in sampled_l if 0 <= l <= l_max]
    for l in sampled_l:
        for eta in eta_values:
            rows.append(
                {
                    "scenario": f"custom_eta_scan::{strategy}",
                    "l": l,
                    "eta": eta,
                    "target_overlap_power": ideal_target_overlap_power(l, eta),
                    "p1_leakage_power": ideal_p1_leakage_power(l, eta),
                    "ring_peak_over_w_cav": ring_peak_radius(l, 1.0),
                    "rms_radius_over_w_cav": rms_radius(l, 1.0),
                }
            )
    return rows


def z_offset_rows(l_max: int) -> list[dict]:
    rows: list[dict] = []
    sampled_l = sorted({0, min(4, l_max), l_max})
    wavelength = 1.0
    w_cav = 1.0
    z_r = math.pi * w_cav * w_cav / wavelength
    x, y, dx = make_square_grid(extent=6.0, grid_size=512)

    for l in sampled_l:
        cavity = lg_mode_cartesian(x, y, p=0, l=l, w0=w_cav, z=0.0, wavelength=wavelength)
        for z_norm in [0.0, 0.25, 0.50, 1.00]:
            field = lg_mode_cartesian(
                x,
                y,
                p=0,
                l=l,
                w0=w_cav,
                z=z_norm * z_r,
                wavelength=wavelength,
            )
            rows.append(
                {
                    "scenario": "zoffset_scan",
                    "l": l,
                    "eta": 1.0,
                    "z_offset_over_zR": z_norm,
                    "target_overlap_power": overlap_power(field, cavity, dx),
                    "p1_leakage_power": "",
                    "ring_peak_over_w_cav": ring_peak_radius(l, math.sqrt(1.0 + z_norm**2)),
                    "rms_radius_over_w_cav": rms_radius(l, math.sqrt(1.0 + z_norm**2)),
                }
            )
    return rows


def build_figure(
    out_path: Path,
    l_max: int,
    strategy: str,
    eta_values: list[float],
    canonical: list[dict],
    z_rows: list[dict],
) -> None:
    same_rows = [row for row in canonical if row["scenario"] == "same_w0"]
    scaled_rows = [row for row in canonical if row["scenario"] == "scaled_w0"]
    sampled_l = sorted({0, 1, 2, min(4, l_max), l_max})
    sampled_l = [l for l in sampled_l if 0 <= l <= l_max]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    ax1, ax2, ax3, ax4 = axes.flat

    ax1.plot([row["l"] for row in same_rows], [row["target_overlap_power"] for row in same_rows], "o-", label="same w0")
    ax1.plot(
        [row["l"] for row in scaled_rows],
        [row["target_overlap_power"] for row in scaled_rows],
        "s-",
        label=r"scaled $w_l=w_0/\sqrt{|l|+1}$",
    )
    ax1.set_title("Target-Mode Coupling")
    ax1.set_xlabel(r"$l$")
    ax1.set_ylabel(r"$|c_{0,l}|^2$")
    ax1.set_ylim(-0.02, 1.05)
    ax1.grid(alpha=0.3)
    ax1.legend()

    ax2.plot([row["l"] for row in same_rows], [row["p1_leakage_power"] for row in same_rows], "o-", label="same w0")
    ax2.plot(
        [row["l"] for row in scaled_rows],
        [row["p1_leakage_power"] for row in scaled_rows],
        "s-",
        label=r"scaled $w_l=w_0/\sqrt{|l|+1}$",
    )
    ax2.set_title(r"Exact $p=1$ Leakage")
    ax2.set_xlabel(r"$l$")
    ax2.set_ylabel(r"$|c_{1,l}|^2$")
    ax2.grid(alpha=0.3)
    ax2.legend()

    for l in sampled_l:
        y_values = [ideal_target_overlap_power(l, eta) for eta in eta_values]
        ax3.plot(eta_values, y_values, marker="o", label=fr"$l={l}$")
    ax3.set_title(f"Custom eta Scan ({strategy})")
    ax3.set_xlabel(r"$\eta=w_{\mathrm{in}}/w_{\mathrm{cav}}$")
    ax3.set_ylabel(r"$|c_{0,l}|^2$")
    ax3.set_ylim(-0.02, 1.05)
    ax3.grid(alpha=0.3)
    ax3.legend(ncol=2)

    if z_rows:
        for l in sorted({int(row["l"]) for row in z_rows}):
            rows_l = [row for row in z_rows if int(row["l"]) == l]
            ax4.plot(
                [float(row["z_offset_over_zR"]) for row in rows_l],
                [float(row["target_overlap_power"]) for row in rows_l],
                marker="o",
                label=fr"$l={l}$",
            )
        ax4.set_title(r"Numerical Waist-Position Mismatch Scan")
        ax4.set_xlabel(r"$\Delta z / z_R$")
        ax4.set_ylabel(r"$|c_{0,l}|^2$")
        ax4.set_ylim(-0.02, 1.05)
        ax4.grid(alpha=0.3)
        ax4.legend()
    else:
        l_values = [row["l"] for row in same_rows]
        ax4.plot(l_values, [row["ring_peak_over_w_cav"] for row in same_rows], "o-", label=r"$r_{\mathrm{peak}}/w$")
        ax4.plot(l_values, [row["rms_radius_over_w_cav"] for row in same_rows], "s-", label=r"$r_{\mathrm{rms}}/w$")
        ax4.set_title("Two Different 'Spot-Size' Measures")
        ax4.set_xlabel(r"$l$")
        ax4.set_ylabel("Radius / w")
        ax4.grid(alpha=0.3)
        ax4.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def build_summary(
    out_path: Path,
    canonical: list[dict],
    eta_values: list[float],
    strategy: str,
    z_rows: list[dict],
) -> None:
    same_rows = [row for row in canonical if row["scenario"] == "same_w0"]
    scaled_rows = [row for row in canonical if row["scenario"] == "scaled_w0"]

    lines = [
        "Ideal LG-FP overlap summary",
        "",
        "Definitions:",
        "  LG target overlap power: |c_{0,l}|^2 = [2 eta / (1 + eta^2)]^(2|l|+2), eta = w_in / w_cav.",
        "  Exact p=1 leakage power:",
        "  |c_{1,l}|^2 = (|l|+1) * [2 eta / (1 + eta^2)]^(2|l|+2) * [(1-eta^2)/(1+eta^2)]^2.",
        "  Ring radius for LG_{0}^{l}: r_peak = w * sqrt(|l| / 2).",
        "  RMS radius: r_rms = w * sqrt((|l|+1) / 2).",
        "",
        "Canonical same-w0 strategy:",
    ]

    for row in same_rows:
        lines.append(
            f"  l={int(row['l'])}: eta=1.0000, target={format_pct(float(row['target_overlap_power']))}, "
            f"p1={format_pct(float(row['p1_leakage_power']))}"
        )

    lines.append("")
    lines.append("Canonical scaled-w0 strategy (w_l = w0 / sqrt(|l|+1)):")
    for row in scaled_rows:
        lines.append(
            f"  l={int(row['l'])}: eta={float(row['eta']):.4f}, target={format_pct(float(row['target_overlap_power']))}, "
            f"p1={format_pct(float(row['p1_leakage_power']))}"
        )

    lines.append("")
    lines.append(f"Custom eta scan strategy: {strategy}")
    lines.append("  eta list: " + ", ".join(f"{eta:.3f}" for eta in eta_values))

    if z_rows:
        lines.append("")
        lines.append("Numerical z-offset scan (same w0, same l, same cavity q family except waist position):")
        for row in z_rows:
            lines.append(
                f"  l={int(row['l'])}, Dz/zR={float(row['z_offset_over_zR']):.2f}: "
                f"target={format_pct(float(row['target_overlap_power']))}"
            )

    lines.append("")
    lines.append("Takeaway:")
    lines.append("  1. Keeping the same w0 preserves perfect ideal coupling for every l when the input mode is already a pure LG_{0}^{l}.")
    lines.append("  2. Shrinking w0 by 1/sqrt(|l|+1) keeps an l-dependent spot-size proxy fixed, but it destroys q matching to the cavity family.")
    lines.append("  3. The current thesis formula that only keeps ((1-eta^2)/(1+eta^2))^2 captures mismatch scaling at best, not the exact p=1 projection.")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_prefix = args.output_prefix
    eta_values = [float(item.strip()) for item in args.eta_list.split(",") if item.strip()]

    canonical = canonical_rows(args.l_max)
    custom_rows = custom_scan_rows(args.l_max, args.strategy, eta_values)
    z_rows = z_offset_rows(args.l_max) if args.include_z_offset else []
    all_rows = canonical + custom_rows + z_rows

    write_csv(Path(f"{output_prefix}overlap_table.csv"), all_rows)
    build_figure(
        Path(f"{output_prefix}overlap_curves.png"),
        args.l_max,
        args.strategy,
        eta_values,
        canonical,
        z_rows,
    )
    build_summary(
        Path(f"{output_prefix}overlap_summary.txt"),
        canonical,
        eta_values,
        args.strategy,
        z_rows,
    )


if __name__ == "__main__":
    main()
