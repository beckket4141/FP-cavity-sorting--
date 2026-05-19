from __future__ import annotations

from engineering_screening_common import (
    OUTPUT_ROOT,
    SCENARIOS,
    analytic_branch_rows,
    ceiling_with_tolerance,
    ensure_dir,
    finesse_scale_from_relative_error,
    reflectivity_from_symmetric_finesse,
    required_finesse,
    required_nominal_rho,
    rho_after_finesse_scale,
    scenario_with_quality,
    symmetric_finesse_from_reflectivity,
    write_csv,
)


RHO_NOMINAL_VALUES = [1.05, 1.10, 1.15, 1.20]
FINESSE_RELATIVE_ERRORS = [-0.10, -0.05, -0.02, 0.00, 0.02, 0.05, 0.10]
TARGET_FINESSE_VALUES = [29.8, 40.0, 95.0, 160.0, 180.0]
REFLECTIVITY_ABS_ERRORS = [-0.010, -0.005, -0.002, -0.001, 0.000, 0.001, 0.002, 0.005, 0.010]
REPRESENTATIVE_N_VALUES = [9, 12, 30, 50]
TAU0_VALUES = [3.0, 4.0, 5.0, 6.0]
RHO_ACTUAL_FLOORS = [1.00, 1.05, 1.10]
WORST_CASE_SHORTFALLS = [0.00, 0.02, 0.05, 0.10]
ANCHOR_FINESSE_NOMINAL = 29.8
ANCHOR_FINESSE_MEASURED = 31.35
ANCHOR_N_MODES = 9
ANCHOR_TAU0 = 3.0


def summarize_engineering_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    geometry_rows = [row for row in rows if row["geometry_pass"] == "yes"]
    geometry_warning_rows = [row for row in rows if row["geometry_warning"] == "yes"]
    w0_experimental_rows = [row for row in rows if row["w0_band"] == "experimental_ok"]
    w0_high_risk_rows = [row for row in rows if row["w0_band"] == "high_risk"]
    final_rows = [row for row in rows if row["final_engineering_pass"] == "yes"]
    final_widths = [float(row["platform_width_L_mm"]) for row in final_rows]
    return {
        "math_optimal_branches": len(rows),
        "geometry_engineering_branches": len(geometry_rows),
        "geometry_warning_branches": len(geometry_warning_rows),
        "w0_experimental_ok_branches": len(w0_experimental_rows),
        "w0_high_risk_branches": len(w0_high_risk_rows),
        "final_engineering_branches": len(final_rows),
        "geometry_warning_branch_list": (
            ",".join(str(row["m"]) for row in geometry_warning_rows) if geometry_warning_rows else "-"
        ),
        "w0_experimental_ok_branch_list": (
            ",".join(str(row["m"]) for row in w0_experimental_rows) if w0_experimental_rows else "-"
        ),
        "w0_high_risk_branch_list": (
            ",".join(str(row["m"]) for row in w0_high_risk_rows) if w0_high_risk_rows else "-"
        ),
        "final_branch_list": ",".join(str(row["m"]) for row in final_rows) if final_rows else "-",
        "max_final_platform_width_L_mm": f"{max(final_widths):.9f}" if final_widths else "0.000000000",
        "mean_final_platform_width_L_mm": (
            f"{(sum(final_widths) / len(final_widths)):.9f}" if final_widths else "0.000000000"
        ),
    }


def build_finesse_relative_error_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for scenario_template in SCENARIOS:
        for tau0 in TAU0_VALUES:
            for n_modes in REPRESENTATIVE_N_VALUES:
                for rho_nominal in RHO_NOMINAL_VALUES:
                    finesse_nominal = required_finesse(n_modes, tau0, rho_nominal)
                    reflectivity_nominal = reflectivity_from_symmetric_finesse(finesse_nominal)
                    for rel_error in FINESSE_RELATIVE_ERRORS:
                        finesse_scale = finesse_scale_from_relative_error(rel_error)
                        finesse_actual = finesse_nominal * finesse_scale
                        rho_actual = rho_after_finesse_scale(rho_nominal, finesse_scale)
                        reflectivity_actual = reflectivity_from_symmetric_finesse(finesse_actual)
                        scenario = scenario_with_quality(
                            scenario_template,
                            finesse=finesse_actual,
                            tau0=tau0,
                        )
                        branch_rows = analytic_branch_rows(scenario, n_values=[n_modes])
                        summary = summarize_engineering_rows(branch_rows)
                        rows.append(
                            {
                                "scenario": scenario_template.name,
                                "N": n_modes,
                                "tau0": f"{tau0:.12f}",
                                "finesse_nominal": f"{finesse_nominal:.12f}",
                                "finesse_nominal_ceiling": ceiling_with_tolerance(finesse_nominal),
                                "finesse_actual": f"{finesse_actual:.12f}",
                                "finesse_actual_ceiling": ceiling_with_tolerance(finesse_actual),
                                "finesse_scale": f"{finesse_scale:.12f}",
                                "finesse_relative_error": f"{rel_error:.12f}",
                                "rho_nominal": f"{rho_nominal:.12f}",
                                "rho_actual": f"{rho_actual:.12f}",
                                "reflectivity_nominal": f"{reflectivity_nominal:.12f}",
                                "reflectivity_actual": f"{reflectivity_actual:.12f}",
                                "reflectivity_abs_error": f"{(reflectivity_actual - reflectivity_nominal):.12f}",
                                "rho_crosses_1p00": "yes" if rho_actual >= 1.00 else "no",
                                "rho_crosses_1p05": "yes" if rho_actual >= 1.05 else "no",
                                "rho_crosses_1p10": "yes" if rho_actual >= 1.10 else "no",
                                **summary,
                            }
                        )
    return rows


def build_reflectivity_to_finesse_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for finesse_nominal in TARGET_FINESSE_VALUES:
        reflectivity_nominal = reflectivity_from_symmetric_finesse(finesse_nominal)
        for reflectivity_abs_error in REFLECTIVITY_ABS_ERRORS:
            reflectivity_actual = reflectivity_nominal + reflectivity_abs_error
            if not 0.0 < reflectivity_actual < 1.0:
                continue
            finesse_actual = symmetric_finesse_from_reflectivity(reflectivity_actual)
            finesse_relative_error = finesse_actual / finesse_nominal - 1.0
            rows.append(
                {
                    "reference_n_modes": ANCHOR_N_MODES,
                    "reference_tau0": f"{ANCHOR_TAU0:.12f}",
                    "finesse_nominal": f"{finesse_nominal:.12f}",
                    "finesse_actual": f"{finesse_actual:.12f}",
                    "finesse_scale": f"{(finesse_actual / finesse_nominal):.12f}",
                    "finesse_relative_error": f"{finesse_relative_error:.12f}",
                    "rho_nominal": f"{(finesse_nominal / (ANCHOR_N_MODES * ANCHOR_TAU0)):.12f}",
                    "rho_actual": f"{(finesse_actual / (ANCHOR_N_MODES * ANCHOR_TAU0)):.12f}",
                    "reflectivity_nominal": f"{reflectivity_nominal:.12f}",
                    "reflectivity_actual": f"{reflectivity_actual:.12f}",
                    "reflectivity_abs_error": f"{reflectivity_abs_error:.12f}",
                    "reflectivity_abs_error_pct_points": f"{(100.0 * reflectivity_abs_error):.3f}",
                    "rho_crosses_1p00": "yes" if finesse_actual / (ANCHOR_N_MODES * ANCHOR_TAU0) >= 1.00 else "no",
                    "rho_crosses_1p05": "yes" if finesse_actual / (ANCHOR_N_MODES * ANCHOR_TAU0) >= 1.05 else "no",
                    "rho_crosses_1p10": "yes" if finesse_actual / (ANCHOR_N_MODES * ANCHOR_TAU0) >= 1.10 else "no",
                }
            )
    return rows


def build_current_design_anchor_rows() -> list[dict[str, object]]:
    anchor_rho_nominal = ANCHOR_FINESSE_NOMINAL / (ANCHOR_N_MODES * ANCHOR_TAU0)
    anchor_rho_measured = ANCHOR_FINESSE_MEASURED / (ANCHOR_N_MODES * ANCHOR_TAU0)
    reflectivity_nominal = reflectivity_from_symmetric_finesse(ANCHOR_FINESSE_NOMINAL)
    reflectivity_measured = reflectivity_from_symmetric_finesse(ANCHOR_FINESSE_MEASURED)
    return [
        {
            "anchor_n_modes": ANCHOR_N_MODES,
            "anchor_tau0": f"{ANCHOR_TAU0:.12f}",
            "finesse_nominal": f"{ANCHOR_FINESSE_NOMINAL:.12f}",
            "finesse_measured": f"{ANCHOR_FINESSE_MEASURED:.12f}",
            "finesse_relative_error": f"{(ANCHOR_FINESSE_MEASURED / ANCHOR_FINESSE_NOMINAL - 1.0):.12f}",
            "rho_nominal": f"{anchor_rho_nominal:.12f}",
            "rho_measured": f"{anchor_rho_measured:.12f}",
            "rho_gain": f"{(anchor_rho_measured / anchor_rho_nominal):.12f}",
            "reflectivity_nominal": f"{reflectivity_nominal:.12f}",
            "reflectivity_equivalent_measured": f"{reflectivity_measured:.12f}",
            "reflectivity_abs_error": f"{(reflectivity_measured - reflectivity_nominal):.12f}",
        }
    ]


def build_required_rho_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rho_actual_floor in RHO_ACTUAL_FLOORS:
        for shortfall in WORST_CASE_SHORTFALLS:
            required_rho = required_nominal_rho(rho_actual_floor, shortfall)
            rows.append(
                {
                    "rho_actual_floor": f"{rho_actual_floor:.12f}",
                    "worst_case_finesse_shortfall": f"{shortfall:.12f}",
                    "required_nominal_rho": f"{required_rho:.12f}",
                }
            )
    return rows


def main() -> None:
    outdir = ensure_dir(OUTPUT_ROOT / "08_finesse_robustness_scan")

    finesse_relative_rows = build_finesse_relative_error_rows()
    reflectivity_rows = build_reflectivity_to_finesse_rows()
    current_anchor_rows = build_current_design_anchor_rows()
    required_rho_rows = build_required_rho_rows()

    finesse_relative_path = outdir / "finesse_relative_error_scan.csv"
    reflectivity_path = outdir / "reflectivity_to_finesse_scan.csv"
    current_anchor_path = outdir / "current_design_finesse_anchor.csv"
    required_rho_path = outdir / "rho_required_under_finesse_shortfall.csv"

    write_csv(finesse_relative_path, list(finesse_relative_rows[0].keys()), finesse_relative_rows)
    write_csv(reflectivity_path, list(reflectivity_rows[0].keys()), reflectivity_rows)
    write_csv(current_anchor_path, list(current_anchor_rows[0].keys()), current_anchor_rows)
    write_csv(required_rho_path, list(required_rho_rows[0].keys()), required_rho_rows)

    print(f"Wrote: {finesse_relative_path}")
    print(f"Wrote: {reflectivity_path}")
    print(f"Wrote: {current_anchor_path}")
    print(f"Wrote: {required_rho_path}")


if __name__ == "__main__":
    main()
