from __future__ import annotations

import math

from fp_theory_core import (
    DATA_DIR,
    ensure_output_dirs,
    k_eff_from_geometry,
    numerical_sensitivity_length,
    plane_concave_k_from_rho,
    plane_concave_rho_from_k,
    plane_concave_sensitivity,
    symmetric_k_from_rho,
    symmetric_rho_from_k,
    symmetric_sensitivity,
    asymmetric_lengths_from_k,
    write_csv,
    write_json,
)


def build_mapping_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx in range(1, 40):
        rho = idx / 40.0
        k_pc = plane_concave_k_from_rho(rho)
        k_dc = symmetric_k_from_rho(rho)
        rows.append(
            {
                "rho_L_over_R": rho,
                "k_plane_concave": k_pc,
                "k_symmetric_double_concave_near_planar": k_dc,
                "naive_2x_k_plane_concave": 2.0 * k_pc,
                "k_dc_over_k_pc": k_dc / k_pc,
                "k_dc_over_naive_2kpc": k_dc / (2.0 * k_pc),
            }
        )
    return rows


def build_backsubstitution_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    targets = sorted({1 / 9, 2 / 9, 4 / 9, 1 / 12, 5 / 18, 7 / 29})
    r1, r2 = 30.0, 45.0
    for k_value in targets:
        rho_pc = plane_concave_rho_from_k(k_value)
        rows.append(
            {
                "case": "plane_concave",
                "branch": "single",
                "target_k_eff": k_value,
                "length": rho_pc,
                "R1": "inf",
                "R2": 1.0,
                "recovered_k_eff": k_eff_from_geometry(rho_pc, math.inf, 1.0),
                "abs_error": abs(k_eff_from_geometry(rho_pc, math.inf, 1.0) - k_value),
                "geometry_parameter": f"L/R={rho_pc:.12f}",
                "sensitivity": plane_concave_sensitivity(rho_pc),
            }
        )
        for branch in ("near_planar", "near_concentric"):
            rho_dc = symmetric_rho_from_k(k_value, branch)
            rows.append(
                {
                    "case": "symmetric_double_concave",
                    "branch": branch,
                    "target_k_eff": k_value,
                    "length": rho_dc,
                    "R1": 1.0,
                    "R2": 1.0,
                    "recovered_k_eff": k_eff_from_geometry(rho_dc, 1.0, 1.0),
                    "abs_error": abs(k_eff_from_geometry(rho_dc, 1.0, 1.0) - k_value),
                    "geometry_parameter": f"L/R={rho_dc:.12f}",
                    "sensitivity": symmetric_sensitivity(rho_dc),
                }
            )
        for branch, length in zip(("short_root", "long_root"), asymmetric_lengths_from_k(k_value, r1, r2)):
            recovered = k_eff_from_geometry(length, r1, r2)
            rows.append(
                {
                    "case": "asymmetric_two_mirror",
                    "branch": branch,
                    "target_k_eff": k_value,
                    "length": length,
                    "R1": r1,
                    "R2": r2,
                    "recovered_k_eff": recovered,
                    "abs_error": abs(recovered - k_value),
                    "geometry_parameter": f"L={length:.12f}, R1={r1:.1f}, R2={r2:.1f}",
                    "sensitivity": numerical_sensitivity_length(length, r1, r2),
                }
            )
    return rows


def build_m9_branch_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for m in (1, 2, 4):
        k_value = m / 9.0
        rho = plane_concave_rho_from_k(k_value)
        rows.append(
            {
                "geometry": "plane_concave",
                "branch": "single",
                "M": 9,
                "m": m,
                "k_star": k_value,
                "rho_L_over_R": rho,
                "sensitivity": plane_concave_sensitivity(rho),
                "robustness_rank_note": "best for plane-concave is smallest sensitivity; m=2",
            }
        )
        for branch in ("near_planar", "near_concentric"):
            rho = symmetric_rho_from_k(k_value, branch)
            rows.append(
                {
                    "geometry": "symmetric_double_concave",
                    "branch": branch,
                    "M": 9,
                    "m": m,
                    "k_star": k_value,
                    "rho_L_over_R": rho,
                    "sensitivity": symmetric_sensitivity(rho),
                    "robustness_rank_note": "best for symmetric double-concave is smallest sensitivity; m=4",
                }
            )
    return rows


def main() -> None:
    ensure_output_dirs()
    mapping = build_mapping_rows()
    back = build_backsubstitution_rows()
    branch = build_m9_branch_rows()
    write_csv(DATA_DIR / "general_cavity_mapping.csv", mapping)
    write_csv(DATA_DIR / "general_cavity_backsubstitution_checks.csv", back)
    write_csv(DATA_DIR / "m9_general_cavity_branch_sensitivity.csv", branch)
    write_json(
        DATA_DIR / "general_cavity_summary.json",
        {
            "max_backsubstitution_abs_error": max(float(row["abs_error"]) for row in back),
            "small_rho_limit": "symmetric double-concave / plane-concave -> sqrt(2), not 2",
            "m9_plane_concave_preferred_m": 2,
            "m9_symmetric_double_concave_preferred_m": 4,
            "asymmetric_example": {"R1": 30.0, "R2": 45.0},
        },
    )
    print("wrote general cavity case tables")


if __name__ == "__main__":
    main()
