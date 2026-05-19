from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from fractions import Fraction
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


def smin_consecutive_k(k: float, m_modes: int) -> float:
    return min(torus_distance(q * k) for q in range(1, m_modes))


def lr_from_k(k: float) -> float:
    return math.sin(math.pi * float(k)) ** 2


@dataclass(frozen=True)
class FareyInterval:
    left_num: int
    left_den: int
    right_num: int
    right_den: int
    order_q: int

    @property
    def left(self) -> Fraction:
        return Fraction(self.left_num, self.left_den)

    @property
    def right(self) -> Fraction:
        return Fraction(self.right_num, self.right_den)

    @property
    def mediant(self) -> Fraction:
        return Fraction(self.left_num + self.right_num, self.left_den + self.right_den)

    @property
    def peak_height(self) -> Fraction:
        return Fraction(1, self.left_den + self.right_den)

    def envelope_value(self, k: float) -> float:
        return min(self.left_den * k - self.left_num, self.right_num - self.right_den * k)


@dataclass(frozen=True)
class VerificationStat:
    m_modes: int
    max_abs_error: float
    mean_abs_error: float
    n_intervals: int


def farey_sequence(order_q: int) -> list[Fraction]:
    fracs = {Fraction(0, 1), Fraction(1, 2)}
    for den in range(1, order_q + 1):
        limit_num = den // 2
        for num in range(limit_num + 1):
            frac = Fraction(num, den)
            if 0 <= frac <= Fraction(1, 2):
                fracs.add(frac)
    return sorted(fracs)


def build_farey_intervals(order_q: int) -> list[FareyInterval]:
    seq = farey_sequence(order_q)
    intervals: list[FareyInterval] = []
    for left, right in zip(seq, seq[1:]):
        if left.denominator > order_q or right.denominator > order_q:
            continue
        if left.numerator * right.denominator + 1 != right.numerator * left.denominator:
            continue
        intervals.append(
            FareyInterval(
                left_num=left.numerator,
                left_den=left.denominator,
                right_num=right.numerator,
                right_den=right.denominator,
                order_q=order_q,
            )
        )
    return intervals


def skeleton_value(k: float, intervals: list[FareyInterval]) -> float:
    for item in intervals:
        if float(item.left) - 1.0e-15 <= k <= float(item.right) + 1.0e-15:
            return item.envelope_value(k)
    raise ValueError(f"k={k} is outside all Farey intervals")


def verify_for_m(m_modes: int, steps: int = 25001) -> tuple[VerificationStat, np.ndarray, np.ndarray, np.ndarray]:
    order_q = m_modes - 1
    intervals = build_farey_intervals(order_q)
    ks = np.linspace(0.0, 0.5, steps)
    y_numeric = np.array([smin_consecutive_k(float(k), m_modes) for k in ks])
    y_skeleton = np.array([skeleton_value(float(k), intervals) for k in ks])
    error = np.abs(y_numeric - y_skeleton)
    stat = VerificationStat(
        m_modes=m_modes,
        max_abs_error=float(np.max(error)),
        mean_abs_error=float(np.mean(error)),
        n_intervals=len(intervals),
    )
    return stat, ks, y_numeric, y_skeleton


def write_interval_csv(intervals: list[FareyInterval], filename: str) -> None:
    path = OUTPUT_DIR / filename
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "left_fraction",
                "right_fraction",
                "left_den",
                "right_den",
                "mediant_fraction",
                "peak_height",
                "denominator_sum",
                "left_L_over_R",
                "right_L_over_R",
                "peak_L_over_R",
            ],
        )
        writer.writeheader()
        for item in intervals:
            writer.writerow(
                {
                    "left_fraction": f"{item.left.numerator}/{item.left.denominator}",
                    "right_fraction": f"{item.right.numerator}/{item.right.denominator}",
                    "left_den": item.left_den,
                    "right_den": item.right_den,
                    "mediant_fraction": f"{item.mediant.numerator}/{item.mediant.denominator}",
                    "peak_height": f"{float(item.peak_height):.12f}",
                    "denominator_sum": item.left_den + item.right_den,
                    "left_L_over_R": f"{lr_from_k(float(item.left)):.12f}",
                    "right_L_over_R": f"{lr_from_k(float(item.right)):.12f}",
                    "peak_L_over_R": f"{lr_from_k(float(item.mediant)):.12f}",
                }
            )


def write_stats_csv(stats: list[VerificationStat]) -> None:
    path = OUTPUT_DIR / "farey_skeleton_verification.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["M", "farey_order_Q", "n_intervals", "max_abs_error", "mean_abs_error"],
        )
        writer.writeheader()
        for row in stats:
            writer.writerow(
                {
                    "M": row.m_modes,
                    "farey_order_Q": row.m_modes - 1,
                    "n_intervals": row.n_intervals,
                    "max_abs_error": f"{row.max_abs_error:.12e}",
                    "mean_abs_error": f"{row.mean_abs_error:.12e}",
                }
            )


def plot_summary() -> None:
    stats: list[VerificationStat] = []
    curves: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for m_modes in (4, 9, 15):
        stat, ks, y_numeric, y_skeleton = verify_for_m(m_modes)
        stats.append(stat)
        curves[m_modes] = (ks, y_numeric, y_skeleton)

    write_stats_csv(stats)
    write_interval_csv(build_farey_intervals(8), "farey_intervals_M9.csv")
    write_interval_csv(build_farey_intervals(14), "farey_intervals_M15.csv")

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

    fig, axes = plt.subplots(3, 1, figsize=(7.5, 9.0), constrained_layout=True)

    clr = {4: "#1565C0", 9: "#E65100", 15: "#2E7D32"}

    ax = axes[0]
    for m_modes in (4, 9, 15):
        ks, y_numeric, y_skeleton = curves[m_modes]
        ax.plot(ks, y_numeric, color=clr[m_modes], lw=1.5, label=rf"$M={m_modes}$ numeric")
        ax.plot(ks, y_skeleton, color=clr[m_modes], lw=0.9, ls="--", alpha=0.75)
    ax.set_xlim(0.0, 0.5)
    ax.set_ylim(0.0, 0.27)
    ax.set_xlabel(r"Gouy step $k$")
    ax.set_ylabel(r"$s_{\min}(k)$")
    ax.set_title("Numeric landscape matches Farey-interval skeleton")
    ax.grid(True, alpha=0.18)
    ax.legend(loc="upper right")

    ax = axes[1]
    ks, y_numeric, y_skeleton = curves[9]
    intervals = build_farey_intervals(8)
    ax.plot(ks, y_numeric, color=clr[9], lw=1.6, label=r"$M=9$ numeric")
    ax.plot(ks, y_skeleton, color="black", lw=1.0, ls="--", label="Farey skeleton")
    for item in intervals:
        peak_k = float(item.mediant)
        peak_h = float(item.peak_height)
        if peak_h >= 0.06:
            ax.text(peak_k, peak_h + 0.008, f"{item.mediant.numerator}/{item.mediant.denominator}", fontsize=8, ha="center")
    ax.set_xlim(0.0, 0.5)
    ax.set_ylim(0.0, 0.13)
    ax.set_xlabel(r"Gouy step $k$")
    ax.set_ylabel(r"$s_9(k)$")
    ax.set_title("Peaks sit at Farey mediants with height 1/(b+d)")
    ax.grid(True, alpha=0.18)
    ax.legend(loc="upper right")

    ax = axes[2]
    peak_ks = [float(item.mediant) for item in intervals]
    peak_k_heights = [float(item.peak_height) for item in intervals]
    peak_lrs = [lr_from_k(k) for k in peak_ks]
    ax.plot(peak_ks, peak_k_heights, "o-", color="#616161", lw=1.0, markersize=4, label="k-space peak sequence")
    ax.plot(peak_lrs, peak_k_heights, "o-", color=clr[9], lw=1.2, markersize=4, label="same peaks after L/R transform")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 0.13)
    ax.set_xlabel(r"horizontal coordinate")
    ax.set_ylabel("peak height")
    ax.set_title(r"$L/R=\sin^2(\pi k)$ stretches the center and compresses edges")
    ax.grid(True, alpha=0.18)
    ax.legend(loc="upper right")

    out_path = OUTPUT_DIR / "farey_skeleton_summary.png"
    fig.savefig(out_path, dpi=220, facecolor="white")
    plt.close(fig)


def main() -> None:
    plot_summary()
    print("Farey-skeleton verification completed.")


if __name__ == "__main__":
    main()
