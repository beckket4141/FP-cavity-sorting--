from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def g_parameter(length: float, radius: float) -> float:
    if math.isinf(radius):
        return 1.0
    return 1.0 - length / radius


def k_general_effective(length: float, radius_1: float, radius_2: float) -> float:
    g1 = g_parameter(length, radius_1)
    g2 = g_parameter(length, radius_2)
    product = g1 * g2
    if not (0.0 <= product <= 1.0):
        raise ValueError(f"unstable geometry: g1*g2={product}")
    product = min(1.0, max(0.0, product))
    return math.acos(math.sqrt(product)) / math.pi


def k_plane_concave(rho: float) -> float:
    if not (0.0 < rho < 1.0):
        raise ValueError("plane-concave rho must be in (0, 1)")
    return math.acos(math.sqrt(1.0 - rho)) / math.pi


def k_symmetric_double_concave_effective(rho: float) -> float:
    if not (0.0 < rho < 2.0):
        raise ValueError("symmetric double-concave rho must be in (0, 2)")
    return math.acos(abs(1.0 - rho)) / math.pi


def rho_plane_concave_from_k(step: float) -> float:
    return math.sin(math.pi * step) ** 2


def rho_symmetric_from_k(step: float, branch: str) -> float:
    cosine = math.cos(math.pi * step)
    if branch == "near_planar":
        return 1.0 - cosine
    if branch == "near_concentric":
        return 1.0 + cosine
    raise ValueError(f"unknown branch: {branch}")


def plane_concave_sensitivity(rho: float) -> float:
    return 1.0 / (2.0 * math.pi * math.sqrt(rho * (1.0 - rho)))


def symmetric_sensitivity(rho: float) -> float:
    return 1.0 / (math.pi * math.sqrt(rho * (2.0 - rho)))


def verify_limit_relations() -> list[str]:
    checks: list[str] = []

    for step in (1 / 9, 2 / 9, 4 / 9):
        rho_pc = rho_plane_concave_from_k(step)
        k_from_general = k_general_effective(rho_pc, math.inf, 1.0)
        checks.append(
            "plane-concave limit: "
            f"k={step:.12f}, recovered={k_from_general:.12f}, "
            f"abs_err={abs(k_from_general - step):.3e}"
        )

        for branch in ("near_planar", "near_concentric"):
            rho_cc = rho_symmetric_from_k(step, branch)
            k_from_general = k_general_effective(rho_cc, 1.0, 1.0)
            checks.append(
                "symmetric double-concave branch: "
                f"branch={branch}, k={step:.12f}, recovered={k_from_general:.12f}, "
                f"abs_err={abs(k_from_general - step):.3e}"
            )

    return checks


def write_geometry_comparison() -> Path:
    path = OUTPUT_DIR / "geometry_mapping_comparison.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "rho",
                "k_plane_concave",
                "naive_2x_k_plane_concave",
                "k_double_concave_effective",
                "k_cc_over_k_pc",
                "k_cc_over_naive_2kpc",
            ]
        )
        for index in range(1, 20):
            rho = index / 20.0
            k_pc = k_plane_concave(rho)
            naive = 2.0 * k_pc
            k_cc = k_symmetric_double_concave_effective(rho)
            writer.writerow(
                [
                    f"{rho:.2f}",
                    f"{k_pc:.12f}",
                    f"{naive:.12f}",
                    f"{k_cc:.12f}",
                    f"{k_cc / k_pc:.12f}",
                    f"{k_cc / naive:.12f}",
                ]
            )
    return path


def write_m9_branch_sensitivity() -> Path:
    path = OUTPUT_DIR / "m9_branch_sensitivity.csv"
    ms = (1, 2, 4)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["geometry", "branch", "m", "k_star", "rho", "abs_dk_d_rho"])

        for m in ms:
            step = m / 9.0
            rho = rho_plane_concave_from_k(step)
            writer.writerow(
                [
                    "plane_concave",
                    "single_branch",
                    m,
                    f"{step:.12f}",
                    f"{rho:.12f}",
                    f"{plane_concave_sensitivity(rho):.12f}",
                ]
            )

        for branch in ("near_planar", "near_concentric"):
            for m in ms:
                step = m / 9.0
                rho = rho_symmetric_from_k(step, branch)
                writer.writerow(
                    [
                        "symmetric_double_concave",
                        branch,
                        m,
                        f"{step:.12f}",
                        f"{rho:.12f}",
                        f"{symmetric_sensitivity(rho):.12f}",
                    ]
                )
    return path


def write_summary() -> Path:
    path = OUTPUT_DIR / "general_fp_summary.txt"

    rho_example = rho_plane_concave_from_k(2 / 9)
    k_pc_example = k_plane_concave(rho_example)
    k_cc_example = k_symmetric_double_concave_effective(rho_example)

    lines = [
        "General FP cavity extension summary",
        "==================================",
        "",
        "1. The folded-spectrum framework remains unchanged once the effective step",
        "   k_eff = arccos(sqrt(g1*g2))/pi is used.",
        "",
        "2. The plane-concave mapping is",
        "   rho = L/R = sin^2(pi k_eff).",
        "",
        "3. The symmetric double-concave mapping is",
        "   rho = L/R = 1 +/- cos(pi k_eff).",
        "",
        "4. Therefore, the symmetric double-concave cavity is not obtained by",
        "   replacing L with 2L in the plane-concave formula.",
        "",
        f"5. At the plane-concave M=9 design point rho={rho_example:.12f},",
        f"   k_pc={k_pc_example:.12f}, k_cc={k_cc_example:.12f},",
        f"   k_cc/k_pc={k_cc_example / k_pc_example:.12f}.",
        "",
        "6. In the small-rho limit, k_cc / k_pc -> sqrt(2), not 2.",
        "",
        "7. For M=9, the most robust representative branch changes:",
        "   plane-concave prefers m=2, while symmetric double-concave prefers m=4",
        "   because the robustness optimum moves toward the confocal point rho=1.",
        "",
    ]

    lines.extend(verify_limit_relations())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    comparison = write_geometry_comparison()
    sensitivity = write_m9_branch_sensitivity()
    summary = write_summary()

    print(f"wrote: {comparison}")
    print(f"wrote: {sensitivity}")
    print(f"wrote: {summary}")


if __name__ == "__main__":
    main()
