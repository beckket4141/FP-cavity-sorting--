from __future__ import annotations

from fractions import Fraction

from fp_theory_core import (
    DATA_DIR,
    ensure_output_dirs,
    er_sum_from_noise,
    eta_from_noise,
    exact_rational_search,
    finite_airy_noise_closed,
    plane_concave_rho_from_k,
    response_for_orders,
    summarize_metrics,
    write_csv,
    write_json,
    write_matrix_csv,
)


DEFAULT_GENERAL_SET = [1, 4, 6, 10, 15, 18, 22, 27, 31, 37, 40, 46]


def main() -> None:
    ensure_output_dirs()
    window = (Fraction(1, 5), Fraction(3, 10))
    result = exact_rational_search(DEFAULT_GENERAL_SET, window=window, target_k=0.25)
    best = result["best"]
    k_best = float(best["k"])
    s_min = float(best["s_min"])
    tau_0 = 3.0
    finesse_min = tau_0 / s_min
    finesse_eval = max(32.21, finesse_min)
    distance, raw, condition = response_for_orders(DEFAULT_GENERAL_SET, k_best, finesse_eval)
    metrics = summarize_metrics(raw, condition)
    write_csv(DATA_DIR / "general_set_exact_rational_top_candidates.csv", result["top_candidates"])
    write_matrix_csv(DATA_DIR / "general_set_distance_matrix.csv", distance, DEFAULT_GENERAL_SET, DEFAULT_GENERAL_SET)
    write_matrix_csv(DATA_DIR / "general_set_raw_airy_response_matrix.csv", raw, DEFAULT_GENERAL_SET, DEFAULT_GENERAL_SET)
    write_matrix_csv(DATA_DIR / "general_set_condition_probability_matrix.csv", condition, DEFAULT_GENERAL_SET, DEFAULT_GENERAL_SET)

    boundary_noise = finite_airy_noise_closed(len(DEFAULT_GENERAL_SET), finesse_min)
    summary = {
        "orders": DEFAULT_GENERAL_SET,
        "window": result["window"],
        "D_max": result["D_max"],
        "q_bound": result["q_bound"],
        "best_k_fraction": best["k_fraction"],
        "best_k": k_best,
        "best_s_min": s_min,
        "limiting_differences": best["limiting_differences"],
        "plane_concave_L_over_R_if_realized": plane_concave_rho_from_k(k_best),
        "tau_0": tau_0,
        "F_min": finesse_min,
        "F_eval_used": finesse_eval,
        "eta_sort_at_F_eval": metrics.eta_sort,
        "mean_ER_sum_dB_at_F_eval": metrics.mean_er_sum_db,
        "min_ER_sum_dB_at_F_eval": metrics.min_er_sum_db,
        "mutual_information_bits_at_F_eval": metrics.mutual_information_bits,
        "finite_M_uniform_reference_ER_at_F_min": er_sum_from_noise(boundary_noise),
        "finite_M_uniform_reference_eta_at_F_min": eta_from_noise(boundary_noise),
        "column_sum_error": metrics.col_sum_error,
    }
    write_json(DATA_DIR / "general_set_search_summary.json", summary)
    print("wrote general set rational search simulation")


if __name__ == "__main__":
    main()
