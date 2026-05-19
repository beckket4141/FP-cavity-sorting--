from __future__ import annotations

import math

from fp_theory_core import DATA_DIR, ensure_output_dirs, write_csv, write_json


def radial_waist_mismatch_power(l_abs: int, p: int, eta: float) -> float:
    prefactor = math.comb(p + l_abs, p)
    scale = (2.0 * eta / (1.0 + eta * eta)) ** (2 * l_abs + 2)
    leak = ((1.0 - eta * eta) / (1.0 + eta * eta)) ** (2 * p)
    return prefactor * scale * leak


def build_oam_mapping_rows(M: int = 12) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for l_value in range(0, M):
        rows.append(
            {
                "case": "single_sign_p0_OAM",
                "p": 0,
                "l": l_value,
                "abs_l": abs(l_value),
                "N": 2 * 0 + abs(l_value) + 1,
                "note": "For p=0 and one sign of l, sorting by N is equivalent to consecutive OAM sorting.",
            }
        )
    for l_value in range(1, M):
        rows.append(
            {
                "case": "signed_OAM_degeneracy",
                "p": 0,
                "l": -l_value,
                "abs_l": abs(l_value),
                "N": 2 * 0 + abs(l_value) + 1,
                "note": "+l and -l share the same N in an isotropic FP cavity.",
            }
        )
    return rows


def build_radial_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for l_abs in (0, 4, 8, 12):
        for eta in (0.99, 0.98, 0.95, 0.90):
            partial = 0.0
            for p in range(0, 7):
                power = radial_waist_mismatch_power(l_abs, p, eta)
                partial += power
                rows.append(
                    {
                        "abs_l": l_abs,
                        "eta_w_in_over_w0": eta,
                        "p": p,
                        "power": power,
                        "partial_sum_p0_to_p6": "",
                    }
                )
            rows.append(
                {
                    "abs_l": l_abs,
                    "eta_w_in_over_w0": eta,
                    "p": "partial_sum_0_to_6",
                    "power": "",
                    "partial_sum_p0_to_p6": partial,
                }
            )
    return rows


def build_satellite_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for l_abs in (2, 4, 6, 8):
        for p in (0, 1, 2):
            N = 2 * p + l_abs + 1
            rows.append(
                {
                    "component": f"LG_p={p}_abs_l={l_abs}",
                    "p": p,
                    "abs_l": l_abs,
                    "N": N,
                    "degenerate_p0_abs_l": N - 1,
                    "interpretation": "A parasitic radial component appears at the same FP resonance as a p=0 mode with abs(l)=N-1.",
                }
            )
    return rows


def main() -> None:
    ensure_output_dirs()
    oam_rows = build_oam_mapping_rows()
    radial_rows = build_radial_rows()
    satellite_rows = build_satellite_rows()
    write_csv(DATA_DIR / "oam_as_N_special_case.csv", oam_rows)
    write_csv(DATA_DIR / "radial_waist_mismatch_scan.csv", radial_rows)
    write_csv(DATA_DIR / "satellite_peak_degeneracy_examples.csv", satellite_rows)
    p1_l8_eta095 = radial_waist_mismatch_power(8, 1, 0.95)
    write_json(
        DATA_DIR / "oam_error_boundary_summary.json",
        {
            "main_scope": "Use N as the primary sorting variable; p=0 single-sign OAM is a special consecutive-N case.",
            "signed_OAM_boundary": "An isotropic FP cavity depends on N=2p+|l|+1 and cannot distinguish +l from -l by itself.",
            "radial_error_boundary": "Axisymmetric waist mismatch preserves l and redistributes power over p.",
            "p1_power_abs_l8_eta095": p1_l8_eta095,
            "satellite_peak_rule": "LG_p^l shares resonance with any mode of the same N=2p+|l|+1.",
        },
    )
    print("wrote OAM special-case and error-boundary simulations")


if __name__ == "__main__":
    main()
