#!/usr/bin/env python3
"""Build a tau-based Lorentz kernel and the corresponding theory matrix."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from _tau_metric_common import (
    build_lorentz_probability_matrix,
    column_sums,
    default_output_dir,
    eta_sort,
    format_float,
    k_from_lr,
    mode_labels,
    mutual_information_bits,
    write_matrix_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the tau-based theory probability matrix.")
    parser.add_argument("--finesse", type=float, default=31.35, help="Experimental finesse.")
    parser.add_argument("--L-mm", dest="length_mm", type=float, default=10.25, help="Cavity length in mm.")
    parser.add_argument("--R-mm", dest="radius_mm", type=float, default=25.0, help="Mirror radius in mm.")
    parser.add_argument("--lmin", type=int, default=0, help="Minimum OAM index.")
    parser.add_argument("--lmax", type=int, default=8, help="Maximum OAM index.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for generated outputs. Defaults to the script directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = default_output_dir(args.output_dir)
    l_values = mode_labels(args.lmin, args.lmax)
    k_value = k_from_lr(args.length_mm, args.radius_mm)

    theory_matrix, pairwise, s_min, tau_eff = build_lorentz_probability_matrix(
        l_values=l_values,
        finesse=args.finesse,
        k_value=k_value,
    )

    pairwise_csv = out_dir / "tau_pairwise_table.csv"
    with pairwise_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "detector_l",
                "lock_l",
                "detector_N",
                "lock_N",
                "s_ij_fsr",
                "tau_ij",
                "kernel_K_ij",
                "is_diagonal",
            ]
        )
        for det_l in theory_matrix.row_labels:
            for lock_l in theory_matrix.col_labels:
                s_ij, tau_ij, kernel = pairwise[(det_l, lock_l)]
                writer.writerow(
                    [
                        det_l,
                        lock_l,
                        det_l + 1,
                        lock_l + 1,
                        format_float(s_ij, 12),
                        format_float(tau_ij, 12),
                        format_float(kernel, 12),
                        int(det_l == lock_l),
                    ]
                )

    theory_csv = out_dir / "theory_probability_matrix.csv"
    write_matrix_csv(theory_csv, theory_matrix)

    summary_path = out_dir / "theory_summary.txt"
    col_sums = column_sums(theory_matrix)
    diag_values = [theory_matrix.values[idx][idx] for idx in range(len(theory_matrix.row_labels))]
    with summary_path.open("w", encoding="utf-8") as handle:
        handle.write("Tau kernel -> theory probability matrix summary\n")
        handle.write(f"finesse = {args.finesse:.6f}\n")
        handle.write(f"L_mm = {args.length_mm:.6f}\n")
        handle.write(f"R_mm = {args.radius_mm:.6f}\n")
        handle.write(f"k = {k_value:.10f}\n")
        handle.write(f"l_range = {args.lmin}..{args.lmax}\n")
        handle.write(f"s_min = {s_min:.12f}\n")
        handle.write(f"tau_eff = {tau_eff:.12f}\n")
        handle.write(f"eta_sort = {100.0 * eta_sort(theory_matrix):.6f}%\n")
        handle.write(f"e_sort = {100.0 * (1.0 - eta_sort(theory_matrix)):.6f}%\n")
        handle.write(f"mutual_information_bits = {mutual_information_bits(theory_matrix):.6f}\n")
        handle.write(
            "diag_range_percent = "
            f"{100.0 * min(diag_values):.6f}% .. {100.0 * max(diag_values):.6f}%\n"
        )
        handle.write(
            "column_sums = " + ", ".join(f"lock_l={label}:{col_sum:.12f}" for label, col_sum in zip(theory_matrix.col_labels, col_sums)) + "\n"
        )

    print(f"Wrote {pairwise_csv}")
    print(f"Wrote {theory_csv}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
