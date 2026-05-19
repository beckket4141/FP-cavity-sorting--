from __future__ import annotations

import math

import numpy as np

from fp_theory_core import (
    DATA_DIR,
    continuous_orders,
    coprime_branches,
    distance_matrix_for_orders,
    ensure_output_dirs,
    er_sum_from_noise,
    eta_from_noise,
    finite_airy_noise_closed,
    finite_airy_noise_sum,
    airy_limit_noise,
    plane_concave_rho_from_k,
    response_for_orders,
    s_min_for_orders,
    summarize_metrics,
    write_csv,
    write_json,
    write_matrix_csv,
)


def landscape_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for M in (4, 9, 15, 30):
        orders = continuous_orders(M)
        for k_value in np.linspace(0.001, 0.499, 2491):
            rows.append({"M": M, "k": float(k_value), "s_min": s_min_for_orders(orders, float(k_value))})
    return rows


def optimal_branch_rows(tau_0: float = 3.0) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for M in range(2, 51):
        branches = coprime_branches(M)
        if not branches:
            continue
        for m in branches:
            k_star = m / M
            s_min = s_min_for_orders(continuous_orders(M), k_star)
            finesse_min = M * tau_0
            noise = finite_airy_noise_closed(M, finesse_min)
            rows.append(
                {
                    "M": M,
                    "m": m,
                    "k_star": k_star,
                    "s_min": s_min,
                    "analytic_s_min": 1.0 / M,
                    "s_min_abs_error": abs(s_min - 1.0 / M),
                    "F_min_tau0_3": finesse_min,
                    "plane_concave_L_over_R": plane_concave_rho_from_k(k_star),
                    "P_noise_at_boundary": noise,
                    "ER_sum_dB_at_boundary": er_sum_from_noise(noise),
                    "eta_sort_at_boundary": eta_from_noise(noise),
                }
            )
    return rows


def response_case_rows(M: int = 9, finesse: float = 32.21, k_value: float = 2 / 9) -> dict[str, object]:
    orders = continuous_orders(M)
    distance, raw, condition = response_for_orders(orders, k_value, finesse)
    metrics = summarize_metrics(raw, condition)
    write_matrix_csv(DATA_DIR / "continuous_M9_distance_matrix.csv", distance, orders, orders)
    write_matrix_csv(DATA_DIR / "continuous_M9_raw_airy_response_matrix.csv", raw, orders, orders)
    write_matrix_csv(DATA_DIR / "continuous_M9_condition_probability_matrix.csv", condition, orders, orders)
    return {
        "M": M,
        "finesse": finesse,
        "k": k_value,
        "s_min": s_min_for_orders(orders, k_value),
        "tau_min": finesse * s_min_for_orders(orders, k_value),
        "eta_sort": metrics.eta_sort,
        "e_sort": metrics.e_sort,
        "mutual_information_bits": metrics.mutual_information_bits,
        "mean_ER_sum_dB": metrics.mean_er_sum_db,
        "min_ER_sum_dB": metrics.min_er_sum_db,
        "diag_min": metrics.diag_min,
        "diag_max": metrics.diag_max,
        "column_sum_error": metrics.col_sum_error,
        "finite_airy_noise_sum": finite_airy_noise_sum(M, finesse),
        "finite_airy_noise_closed": finite_airy_noise_closed(M, finesse),
        "finite_airy_ER_sum_dB": er_sum_from_noise(finite_airy_noise_closed(M, finesse)),
        "finite_airy_eta_sort": eta_from_noise(finite_airy_noise_closed(M, finesse)),
    }


def capacity_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for tau_0 in (2.0, 3.0, 4.0, 5.0):
        limit_noise = airy_limit_noise(tau_0)
        for M in range(2, 61):
            finesse_min = M * tau_0
            finite_noise = finite_airy_noise_closed(M, finesse_min)
            rows.append(
                {
                    "tau_0": tau_0,
                    "M": M,
                    "F_min": finesse_min,
                    "finite_noise": finite_noise,
                    "finite_ER_sum_dB": er_sum_from_noise(finite_noise),
                    "finite_eta_sort": eta_from_noise(finite_noise),
                    "large_M_noise": limit_noise,
                    "large_M_ER_sum_dB": er_sum_from_noise(limit_noise),
                    "large_M_eta_sort": eta_from_noise(limit_noise),
                }
            )
    return rows


def symmetry_check_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for M in (5, 9, 17):
        orders = continuous_orders(M)
        for k_value in (1 / M, 2 / M if 2 < M / 2 else 1 / M):
            d1 = distance_matrix_for_orders(orders, k_value)
            d2 = distance_matrix_for_orders(orders, 1.0 - k_value)
            rows.append(
                {
                    "M": M,
                    "k": k_value,
                    "one_minus_k": 1.0 - k_value,
                    "max_distance_matrix_difference": float(np.max(np.abs(d1 - d2))),
                }
            )
    return rows


def main() -> None:
    ensure_output_dirs()
    landscape = landscape_rows()
    branches = optimal_branch_rows()
    response = response_case_rows()
    capacity = capacity_rows()
    symmetry = symmetry_check_rows()
    write_csv(DATA_DIR / "continuous_N_smin_landscape.csv", landscape)
    write_csv(DATA_DIR / "continuous_N_optimal_branches.csv", branches)
    write_csv(DATA_DIR / "continuous_capacity_boundary.csv", capacity)
    write_csv(DATA_DIR / "k_vs_one_minus_k_checks.csv", symmetry)
    write_json(
        DATA_DIR / "continuous_M9_response_summary.json",
        {
            **response,
            "large_M_tau0_3_noise": airy_limit_noise(3.0),
            "large_M_tau0_3_ER_sum_dB": er_sum_from_noise(airy_limit_noise(3.0)),
            "large_M_tau0_3_eta_sort": eta_from_noise(airy_limit_noise(3.0)),
            "max_smin_optimal_error_M2_to_M50": max(float(row["s_min_abs_error"]) for row in branches),
            "max_k_symmetry_distance_error": max(float(row["max_distance_matrix_difference"]) for row in symmetry),
        },
    )
    print("wrote continuous N sorting simulations")


if __name__ == "__main__":
    main()
