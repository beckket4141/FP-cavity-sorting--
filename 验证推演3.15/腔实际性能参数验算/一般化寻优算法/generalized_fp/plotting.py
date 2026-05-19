from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .core import DetailedSolution


def plot_search_landscape(landscape_df: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True, sharex=True)
    ax1, ax2, ax3 = axes
    colors = landscape_df["best_subset_size"].to_numpy(dtype=float)
    scatter = ax1.scatter(landscape_df["k"], landscape_df["best_subset_size"], c=colors, cmap="viridis", s=15, edgecolors="none")
    ax1.set_ylabel("Best subset size")
    ax1.set_title("Search landscape")
    ax1.grid(alpha=0.25)
    cbar = fig.colorbar(scatter, ax=ax1, pad=0.01)
    cbar.set_label("Subset size")
    ax2.plot(landscape_df["k"], landscape_df["best_s_min"], color="#0f766e", lw=1.4)
    ax2.set_ylabel("Best s_min")
    ax2.grid(alpha=0.25)
    ax3.plot(landscape_df["k"], landscape_df["best_F_min"], color="#b45309", lw=1.4)
    ax3.set_ylabel("Best F_min")
    ax3.set_xlabel("k")
    ax3.grid(alpha=0.25)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_solution_circle(detail: DetailedSolution, output_path: Path) -> None:
    fig = plt.figure(figsize=(7.2, 7.0), constrained_layout=True)
    ax = fig.add_subplot(111, projection="polar")
    quick = detail.quick
    theta_all = [2.0 * math.pi * quick.pos_all[mode] for mode in sorted(quick.pos_all)]
    theta_subset = [2.0 * math.pi * quick.pos_all[mode] for mode in quick.subset_modes]
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_rticks([])
    ax.set_rlim(0.0, 1.15)
    ax.grid(alpha=0.22)
    ax.scatter(theta_all, np.full(len(theta_all), 0.92), s=60, color="#cbd5e1", label="candidate modes")
    ax.scatter(theta_subset, np.full(len(theta_subset), 1.0), s=95, color="#0f766e", label="selected subset")
    for mode in sorted(quick.pos_all):
        angle = 2.0 * math.pi * quick.pos_all[mode]
        radius = 1.08 if mode in quick.subset_modes else 0.84
        ax.text(angle, radius, str(mode), ha="center", va="center", fontsize=8)
    ax.set_title("Mode positions on the normalized FP ring", fontsize=12)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.08, -0.02), frameon=False)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_conflict_graph(detail: DetailedSolution, output_path: Path, tau_0: float, feasibility_finesse: float | None) -> None:
    quick = detail.quick
    modes = sorted(quick.pos_all)
    pos = {mode: quick.pos_all[mode] for mode in modes}
    xy = {mode: (math.cos(2.0 * math.pi * pos[mode] - math.pi / 2.0), math.sin(2.0 * math.pi * pos[mode] - math.pi / 2.0)) for mode in modes}
    fig, ax = plt.subplots(figsize=(7.8, 7.4), constrained_layout=True)
    ax.add_patch(plt.Circle((0.0, 0.0), 1.0, fill=False, color="#94a3b8", lw=1.2))
    threshold = None if feasibility_finesse is None else tau_0 / feasibility_finesse
    for i, mode_i in enumerate(modes):
        for j in range(i + 1, len(modes)):
            mode_j = modes[j]
            s_ij = min(abs(pos[mode_i] - pos[mode_j]), 1.0 - abs(pos[mode_i] - pos[mode_j]))
            if threshold is not None and s_ij < threshold:
                x1, y1 = xy[mode_i]
                x2, y2 = xy[mode_j]
                ax.plot([x1, x2], [y1, y2], color="#dc2626", lw=1.0, alpha=0.65)
    for mode in modes:
        x, y = xy[mode]
        selected = mode in quick.subset_modes
        ax.scatter([x], [y], s=150 if selected else 85, color="#0f766e" if selected else "#cbd5e1", edgecolors="black", linewidths=1.0, zorder=3)
        ax.text(x, y, str(mode), ha="center", va="center", fontsize=8, zorder=4)
    title_suffix = "exact overlaps only" if threshold is None else f"threshold s < {threshold:.4f}"
    ax.set_title(f"Conflict graph ({title_suffix})", fontsize=12)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_condition_matrix(detail: DetailedSolution, output_path: Path) -> None:
    modes = [str(mode) for mode in detail.quick.subset_modes]
    matrix = detail.condition_matrix
    fig, ax = plt.subplots(figsize=(7.5, 6.6), constrained_layout=True)
    im = ax.imshow(matrix, cmap="YlGnBu", vmin=0.0, vmax=1.0)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=7, color="black" if value < 0.65 else "white")
    ax.set_xticks(range(len(modes)), modes)
    ax.set_yticks(range(len(modes)), modes)
    ax.set_xlabel("Input target mode")
    ax.set_ylabel("Detected output channel")
    ax.set_title("Conditional probability / crosstalk matrix")
    fig.colorbar(im, ax=ax, pad=0.02, label="Probability")
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_mode_metrics(detail: DetailedSolution, output_path: Path) -> None:
    df = pd.DataFrame(detail.per_mode_records)
    fig, axes = plt.subplots(2, 1, figsize=(9.2, 7.0), constrained_layout=True, sharex=True)
    ax1, ax2 = axes
    x = np.arange(len(df))
    ax1.bar(x, df["ER_sum_dB"], color="#0f766e", alpha=0.9)
    ax1.set_ylabel("ER_sum (dB)")
    ax1.grid(axis="y", alpha=0.24)
    ax2.bar(x, df["separation_efficiency"] * 100.0, color="#1d4ed8", alpha=0.85)
    ax2.set_ylabel("Separation efficiency (%)")
    ax2.set_xlabel("Mode")
    ax2.grid(axis="y", alpha=0.24)
    ax2.set_xticks(x, [str(v) for v in df["mode"]])
    fig.suptitle("Per-mode physical performance at F_eval", fontsize=12)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
