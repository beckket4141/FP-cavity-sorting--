from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def torus_distance(x: float) -> float:
    frac = float(x) % 1.0
    return min(frac, 1.0 - frac)


def lr_from_k(k: float) -> float:
    return math.sin(math.pi * float(k)) ** 2


def smin_consecutive_k(k: float, m_modes: int) -> float:
    return min(torus_distance(q * k) for q in range(1, m_modes))


def smin_consecutive_lr(lr: float, m_modes: int) -> float:
    k = math.acos(math.sqrt(1.0 - float(lr))) / math.pi
    return smin_consecutive_k(k, m_modes)


def modular_inverse(m: int, modulus: int) -> int:
    for candidate in range(1, modulus):
        if (candidate * m) % modulus == 1:
            return candidate
    raise ValueError(f"No inverse exists for m={m} mod {modulus}")


@dataclass(frozen=True)
class NestingStat:
    coarse_m: int
    fine_m: int
    max_fine_minus_coarse: float
    min_fine_minus_coarse: float
    equality_fraction: float


@dataclass(frozen=True)
class LocalSlopeStat:
    m_modes: int
    branch_m: int
    inverse_a: int
    k_star: float
    lr_star: float
    left_slope_numeric: float
    right_slope_numeric: float
    left_slope_theory: float
    right_slope_theory: float


def compute_curves(m_list: list[int], steps: int = 20001) -> tuple[np.ndarray, dict[int, np.ndarray]]:
    ks = np.linspace(1.0e-6, 0.5 - 1.0e-6, steps)
    curves = {
        m_modes: np.array([smin_consecutive_k(k, m_modes) for k in ks])
        for m_modes in m_list
    }
    return ks, curves


def compute_nesting_stats(ks: np.ndarray, curves: dict[int, np.ndarray]) -> list[NestingStat]:
    _ = ks
    pairs = [(4, 9), (9, 15), (4, 15)]
    stats: list[NestingStat] = []
    for coarse_m, fine_m in pairs:
        diff = curves[fine_m] - curves[coarse_m]
        stats.append(
            NestingStat(
                coarse_m=coarse_m,
                fine_m=fine_m,
                max_fine_minus_coarse=float(np.max(diff)),
                min_fine_minus_coarse=float(np.min(diff)),
                equality_fraction=float(np.mean(np.isclose(diff, 0.0, atol=1.0e-10))),
            )
        )
    return stats


def compute_local_slope_stats() -> list[LocalSlopeStat]:
    slope_stats: list[LocalSlopeStat] = []
    eps = 1.0e-7
    for m_modes in (4, 9, 15):
        for branch_m in range(1, m_modes):
            if math.gcd(branch_m, m_modes) != 1:
                continue
            if branch_m / m_modes >= 0.5:
                continue
            k_star = branch_m / m_modes
            s_star = smin_consecutive_k(k_star, m_modes)
            left_slope = (s_star - smin_consecutive_k(k_star - eps, m_modes)) / eps
            right_slope = (smin_consecutive_k(k_star + eps, m_modes) - s_star) / eps
            inverse_a = modular_inverse(branch_m, m_modes)
            slope_stats.append(
                LocalSlopeStat(
                    m_modes=m_modes,
                    branch_m=branch_m,
                    inverse_a=inverse_a,
                    k_star=k_star,
                    lr_star=lr_from_k(k_star),
                    left_slope_numeric=float(left_slope),
                    right_slope_numeric=float(right_slope),
                    left_slope_theory=float(inverse_a),
                    right_slope_theory=float(-(m_modes - inverse_a)),
                )
            )
    return slope_stats


def write_curve_csv(ks: np.ndarray, curves: dict[int, np.ndarray]) -> None:
    path = OUTPUT_DIR / "fractal_refinement_curves.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["k", "L_over_R", "s_M4", "s_M9", "s_M15"])
        writer.writeheader()
        for idx, k in enumerate(ks):
            writer.writerow(
                {
                    "k": f"{k:.12f}",
                    "L_over_R": f"{lr_from_k(float(k)):.12f}",
                    "s_M4": f"{curves[4][idx]:.12f}",
                    "s_M9": f"{curves[9][idx]:.12f}",
                    "s_M15": f"{curves[15][idx]:.12f}",
                }
            )


def write_stats_csv(nesting_stats: list[NestingStat], slope_stats: list[LocalSlopeStat]) -> None:
    nesting_path = OUTPUT_DIR / "fractal_refinement_nesting_stats.csv"
    with nesting_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "coarse_M",
                "fine_M",
                "max_fine_minus_coarse",
                "min_fine_minus_coarse",
                "equality_fraction",
            ],
        )
        writer.writeheader()
        for row in nesting_stats:
            writer.writerow(
                {
                    "coarse_M": row.coarse_m,
                    "fine_M": row.fine_m,
                    "max_fine_minus_coarse": f"{row.max_fine_minus_coarse:.12e}",
                    "min_fine_minus_coarse": f"{row.min_fine_minus_coarse:.12e}",
                    "equality_fraction": f"{row.equality_fraction:.12f}",
                }
            )

    slope_path = OUTPUT_DIR / "fractal_refinement_local_slopes.csv"
    with slope_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "M",
                "m",
                "inverse_a",
                "k_star",
                "L_over_R_star",
                "left_slope_numeric",
                "right_slope_numeric",
                "left_slope_theory",
                "right_slope_theory",
            ],
        )
        writer.writeheader()
        for row in slope_stats:
            writer.writerow(
                {
                    "M": row.m_modes,
                    "m": row.branch_m,
                    "inverse_a": row.inverse_a,
                    "k_star": f"{row.k_star:.12f}",
                    "L_over_R_star": f"{row.lr_star:.12f}",
                    "left_slope_numeric": f"{row.left_slope_numeric:.9f}",
                    "right_slope_numeric": f"{row.right_slope_numeric:.9f}",
                    "left_slope_theory": f"{row.left_slope_theory:.9f}",
                    "right_slope_theory": f"{row.right_slope_theory:.9f}",
                }
            )


def plot_results(ks: np.ndarray, curves: dict[int, np.ndarray]) -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "mathtext.fontset": "cm",
            "font.size": 10,
            "axes.labelsize": 11,
            "legend.fontsize": 9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.unicode_minus": False,
        }
    )

    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.4), constrained_layout=True)

    clr = {4: "#1565C0", 9: "#E65100", 15: "#2E7D32"}

    ax = axes[0]
    for m_modes in (4, 9, 15):
        ax.plot(ks, curves[m_modes], color=clr[m_modes], lw=1.3, label=rf"$M={m_modes}$")
    ax.set_xlim(0.0, 0.5)
    ax.set_ylim(0.0, 0.27)
    ax.set_xlabel(r"Gouy step $k$")
    ax.set_ylabel(r"$s_{\min}(k)$")
    ax.set_title("Nested envelopes in k-space")
    ax.grid(True, alpha=0.18)
    ax.legend(loc="upper right")

    ax = axes[1]
    q_values = range(1, 9)
    for q in q_values:
        component = np.array([torus_distance(q * k) for k in ks])
        ax.plot(ks, component, color="#9E9E9E", lw=0.8, alpha=0.35)
    ax.plot(ks, curves[9], color=clr[9], lw=1.8, label="s9(k) = min over q = 1...8")
    ax.plot(ks, curves[4], color=clr[4], lw=1.0, alpha=0.75, ls="--", label=r"$s_4(k)$")
    ax.set_xlim(0.0, 0.5)
    ax.set_ylim(0.0, 0.27)
    ax.set_xlabel(r"Gouy step $k$")
    ax.set_ylabel("component / envelope")
    ax.set_title("M=9 is built by adding new sawtooth constraints")
    ax.grid(True, alpha=0.18)
    ax.legend(loc="upper right")

    ax = axes[2]
    k_star = 2.0 / 9.0
    eps = np.linspace(-0.03, 0.03, 3001)
    k_zoom = k_star + eps
    y_numeric = np.array([smin_consecutive_k(k, 9) for k in k_zoom])
    a = modular_inverse(2, 9)
    y_local = np.minimum(1.0 / 9.0 + a * eps, 1.0 / 9.0 - (9 - a) * eps)
    ax.plot(k_zoom, y_numeric, color=clr[9], lw=1.8, label="numeric envelope")
    ax.plot(k_zoom, y_local, color="black", lw=1.0, ls="--", label=r"local law: $\min(1/9+5\varepsilon,\,1/9-4\varepsilon)$")
    ax.axvline(k_star, color="#616161", lw=0.9, ls=":")
    ax.set_xlim(k_star - 0.03, k_star + 0.03)
    ax.set_ylim(0.0, 0.13)
    ax.set_xlabel(r"$k$")
    ax.set_ylabel(r"$s_9(k)$")
    ax.set_title(r"Local peak near $k^*=2/9$ is a skew tent, not a symmetric copy")
    ax.grid(True, alpha=0.18)
    ax.legend(loc="upper right")

    out_path = OUTPUT_DIR / "fractal_refinement_summary.png"
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def main() -> None:
    ks, curves = compute_curves([4, 9, 15])
    nesting_stats = compute_nesting_stats(ks, curves)
    slope_stats = compute_local_slope_stats()
    write_curve_csv(ks, curves)
    write_stats_csv(nesting_stats, slope_stats)
    plot_results(ks, curves)

    print("Fractal-refinement verification completed.")
    for row in nesting_stats:
        print(
            f"M={row.fine_m} vs M={row.coarse_m}: "
            f"max diff={row.max_fine_minus_coarse:.3e}, "
            f"min diff={row.min_fine_minus_coarse:.3e}, "
            f"equality fraction={row.equality_fraction:.4f}"
        )


if __name__ == "__main__":
    main()
