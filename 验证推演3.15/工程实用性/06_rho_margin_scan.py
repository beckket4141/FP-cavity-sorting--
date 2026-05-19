from __future__ import annotations

import math

from engineering_screening_common import (
    N_SCAN_VALUES,
    OUTPUT_ROOT,
    SCENARIOS,
    analytic_branch_rows,
    ceiling_with_tolerance,
    ensure_dir,
    peak_headroom_ratio,
    platform_height_margin,
    required_finesse,
    scenario_with_quality,
    write_csv,
)


RHO_VALUES = [1.00, 1.02, 1.05, 1.10, 1.15, 1.20, 1.30]
TAU0_VALUES = [3.0, 4.0, 5.0, 6.0]
REPRESENTATIVE_N_VALUES = [9, 12, 30, 50]


def summary_rows_for_scan(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary_rows: list[dict[str, object]] = []
    keys: set[tuple[str, float, float, int]] = {
        (
            str(row["scenario"]),
            float(row["tau0"]),
            float(row["rho"]),
            int(row["N"]),
        )
        for row in rows
    }
    for scenario_name, tau0_value, rho_value_text, n_modes in sorted(
        keys,
        key=lambda item: (item[0], item[1], item[2], item[3]),
    ):
        subset = [
            row
            for row in rows
            if row["scenario"] == scenario_name
            and abs(float(row["tau0"]) - tau0_value) < 1.0e-9
            and abs(float(row["rho"]) - rho_value_text) < 1.0e-9
            and int(row["N"]) == n_modes
        ]
        geometry_rows = [row for row in subset if row["geometry_pass"] == "yes"]
        geometry_warning_rows = [row for row in subset if row["geometry_warning"] == "yes"]
        w0_experimental_rows = [row for row in subset if row["w0_band"] == "experimental_ok"]
        w0_high_risk_rows = [row for row in subset if row["w0_band"] == "high_risk"]
        final_rows = [row for row in subset if row["final_engineering_pass"] == "yes"]
        final_widths = [float(row["platform_width_L_mm"]) for row in final_rows]
        pairwise_er_db = float(subset[0]["pairwise_er_db"])
        conservative_er_db = float(subset[0]["conservative_er_db"])
        finesse = float(subset[0]["finesse"])
        tau0 = float(subset[0]["tau0"])
        rho = float(subset[0]["rho"])
        summary_rows.append(
            {
                "scenario": scenario_name,
                "N": n_modes,
                "tau0": f"{tau0:.12f}",
                "rho": f"{rho:.12f}",
                "finesse": f"{finesse:.12f}",
                "finesse_ceiling": ceiling_with_tolerance(finesse),
                "delta": subset[0]["delta"],
                "tau_eff": subset[0]["tau_eff"],
                "tau_margin": subset[0]["tau_margin"],
                "peak_headroom_ratio": subset[0]["peak_headroom_ratio"],
                "platform_height_margin": subset[0]["platform_height_margin"],
                "math_optimal_branches": len(subset),
                "geometry_engineering_branches": len(geometry_rows),
                "geometry_warning_branches": len(geometry_warning_rows),
                "w0_experimental_ok_branches": len(w0_experimental_rows),
                "w0_high_risk_branches": len(w0_high_risk_rows),
                "final_engineering_branches": len(final_rows),
                "geometry_branch_list": ",".join(str(row["m"]) for row in geometry_rows) if geometry_rows else "-",
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
                "min_final_platform_width_L_mm": f"{min(final_widths):.9f}" if final_widths else "0.000000000",
                "mean_final_platform_width_L_mm": (
                    f"{(sum(final_widths) / len(final_widths)):.9f}" if final_widths else "0.000000000"
                ),
                "pairwise_er_db": f"{pairwise_er_db:.6f}",
                "conservative_er_db": f"{conservative_er_db:.6f}",
                "rho_is_boundary": "yes" if math.isclose(rho, 1.0) else "no",
                "final_exists": "yes" if final_rows else "no",
            }
        )
    return summary_rows


def main() -> None:
    outdir = ensure_dir(OUTPUT_ROOT / "06_rho_margin_scan")

    rows: list[dict[str, object]] = []
    for scenario_template in SCENARIOS:
        for tau0 in TAU0_VALUES:
            for rho in RHO_VALUES:
                for n_modes in N_SCAN_VALUES:
                    scenario = scenario_with_quality(
                        scenario_template,
                        finesse=required_finesse(n_modes, tau0, rho),
                        tau0=tau0,
                    )
                    scenario_rows = analytic_branch_rows(scenario, n_values=[n_modes])
                    for row in scenario_rows:
                        row["rho_design"] = row["rho"]
                        row["finesse_ceiling"] = str(ceiling_with_tolerance(float(row["finesse"])))
                        row["peak_headroom_ratio_formula"] = f"{peak_headroom_ratio(rho):.12f}"
                        row["platform_height_margin_formula"] = (
                            f"{platform_height_margin(n_modes, float(row['finesse']), tau0):.12f}"
                        )
                        row["rho_is_boundary"] = "yes" if math.isclose(rho, 1.0) else "no"
                        row["scenario_family"] = scenario_template.name
                    rows.extend(scenario_rows)

    summary_rows = summary_rows_for_scan(rows)
    representative_rows = [row for row in rows if int(row["N"]) in REPRESENTATIVE_N_VALUES]

    details_csv_path = outdir / "rho_margin_scan_details.csv"
    summary_csv_path = outdir / "rho_margin_scan_summary.csv"
    representative_csv_path = outdir / "rho_representative_cases.csv"

    write_csv(details_csv_path, list(rows[0].keys()), rows)
    write_csv(summary_csv_path, list(summary_rows[0].keys()), summary_rows)
    write_csv(representative_csv_path, list(representative_rows[0].keys()), representative_rows)

    print(f"Wrote: {details_csv_path}")
    print(f"Wrote: {summary_csv_path}")
    print(f"Wrote: {representative_csv_path}")


if __name__ == "__main__":
    main()
