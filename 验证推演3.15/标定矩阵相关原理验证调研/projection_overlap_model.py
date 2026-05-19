from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np


OUT_DIR = Path(__file__).resolve().parent


def lg_p0_radial(l: int, r: np.ndarray, w: float) -> np.ndarray:
    """Normalized p=0 LG radial amplitude without the azimuthal phase."""
    l_abs = abs(l)
    prefactor = math.sqrt(2.0 / (math.pi * math.factorial(l_abs))) / w
    return prefactor * (math.sqrt(2.0) * r / w) ** l_abs * np.exp(-(r / w) ** 2)


def gaussian_radial(r: np.ndarray, w: float) -> np.ndarray:
    """Normalized Gaussian fundamental amplitude in the same convention as LG_0^0."""
    return math.sqrt(2.0 / math.pi) / w * np.exp(-(r / w) ** 2)


def radial_inner(a: np.ndarray, b: np.ndarray, r: np.ndarray) -> float:
    return float(2.0 * math.pi * np.trapezoid(a * b * r, r))


def radial_power(a: np.ndarray, r: np.ndarray) -> float:
    return float(2.0 * math.pi * np.trapezoid(np.abs(a) ** 2 * r, r))


def second_moment_radius(a: np.ndarray, r: np.ndarray) -> float:
    power = radial_power(a, r)
    if power <= 0:
        return float("nan")
    r2 = float(2.0 * math.pi * np.trapezoid(np.abs(a) ** 2 * r**3, r) / power)
    return math.sqrt(max(r2, 0.0))


def mode_metrics(l: int, r: np.ndarray, w_in: float, w_holo: float, w_smf: float) -> dict[str, float]:
    u_in = lg_p0_radial(l, r, w_in)
    holo_amp_raw = lg_p0_radial(l, r, w_holo)
    holo_amp = holo_amp_raw / np.max(holo_amp_raw)
    smf = gaussian_radial(r, w_smf)

    phase_flattened = u_in
    phase_flat_coupling = radial_inner(smf, phase_flattened, r) ** 2

    complex_restored = u_in * holo_amp
    complex_power = radial_power(complex_restored, r)
    complex_total_coupling = radial_inner(smf, complex_restored, r) ** 2
    complex_cond_coupling = complex_total_coupling / complex_power if complex_power > 0 else 0.0

    return {
        "l": float(l),
        "phase_flatten_smf_coupling": phase_flat_coupling,
        "complex_hologram_power_factor": complex_power,
        "complex_conditional_smf_coupling": complex_cond_coupling,
        "complex_total_detected_fraction": complex_total_coupling,
        "complex_restored_r_rms_over_w": second_moment_radius(complex_restored, r) / w_holo,
    }


def scan_best_smf(l: int, r: np.ndarray, w_in: float, w_holo: float) -> tuple[float, float]:
    ratios = np.linspace(0.35, 4.0, 251)
    best_ratio = 0.0
    best_total = -1.0
    for ratio in ratios:
        total = mode_metrics(l, r, w_in, w_holo, ratio * w_holo)["complex_total_detected_fraction"]
        if total > best_total:
            best_total = total
            best_ratio = float(ratio)
    return best_ratio, best_total


def write_csv(rows: list[dict[str, float]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, float]], path: Path) -> None:
    lines = [
        "# Projection/SMF overlap lightweight model",
        "",
        "This script uses a deliberately simple multiplicative projection model:",
        "",
        "- incident field: normalized `LG_0^l(w_in)`;",
        "- phase-flattening reference: remove only the azimuthal phase and couple the remaining radial field to a fixed Gaussian SMF mode;",
        "- complex-amplitude restoration reference: multiply by the normalized radial amplitude of the conjugate `LG_0^l(w_holo)` hologram, then couple to the same fixed Gaussian;",
        "- fixed SMF waist is chosen as the l=0 optimum of the complex-amplitude product model, `w_smf = w_holo / sqrt(2)`.",
        "",
        "The model is not an end-to-end SLM/4f/fiber simulation. Its purpose is to test whether a matched conjugate-amplitude projection automatically produces the same Gaussian spot for every l. In this model it does not: the restored radial envelope still broadens roughly with the LG mode scale.",
        "",
        "| l | phase-flatten SMF | hologram power factor | conditional SMF | total detected | restored RMS / w | best SMF waist / w | best total |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {l:.0f} | {phase_flatten_smf_coupling:.6f} | {complex_hologram_power_factor:.6f} | "
            "{complex_conditional_smf_coupling:.6f} | {complex_total_detected_fraction:.6f} | "
            "{complex_restored_r_rms_over_w:.4f} | {best_smf_waist_over_w:.4f} | {best_total_detected_fraction:.6f} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "Key reading:",
            "",
            "- The fixed-SMF total detected fraction falls strongly with l in both phase-only and amplitude-weighted projection models.",
            "- The best SMF waist increases with l, which is a compact way to say that the matched restoration field is not a single l-independent Gaussian mode.",
            "- Therefore a real detection chain can easily have l-dependent diagonal response even when the input and restoration hologram labels match.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    w = 1.0
    r = np.linspace(0.0, 8.0 * w, 30_001)
    fixed_w_smf = w / math.sqrt(2.0)

    rows: list[dict[str, float]] = []
    for l in range(9):
        row = mode_metrics(l, r, w, w, fixed_w_smf)
        best_ratio, best_total = scan_best_smf(l, r, w, w)
        row["best_smf_waist_over_w"] = best_ratio
        row["best_total_detected_fraction"] = best_total
        rows.append(row)

    write_csv(rows, OUT_DIR / "projection_overlap_model_results.csv")
    write_markdown(rows, OUT_DIR / "projection_overlap_model_results.md")
    print("Wrote projection_overlap_model_results.csv")
    print("Wrote projection_overlap_model_results.md")


if __name__ == "__main__":
    main()
