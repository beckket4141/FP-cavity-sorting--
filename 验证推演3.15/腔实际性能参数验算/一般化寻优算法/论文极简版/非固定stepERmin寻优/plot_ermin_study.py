from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def find_workspace_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        probe = candidate / "oe_paper" / "simulation" / "scripts" / "fp_design" / "core.py"
        if probe.exists():
            return candidate
    raise FileNotFoundError("Could not locate thesis workspace root from current script path.")


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = find_workspace_root(SCRIPT_DIR)
SIM_SCRIPTS_DIR = WORKSPACE_ROOT / "oe_paper" / "simulation" / "scripts"
if str(SIM_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_SCRIPTS_DIR))

from fp_design.core import evaluate_response_metrics  # noqa: E402


TABLES_DIR = SCRIPT_DIR / "tables"
FIGURES_DIR = SCRIPT_DIR / "figures"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    return json.loads((SCRIPT_DIR / "case_config.json").read_text(encoding="utf-8"))


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "mathtext.fontset": "cm",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.unicode_minus": False,
            "font.size": 8.5,
            "axes.labelsize": 9.0,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "axes.linewidth": 0.8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "legend.frameon": False,
            "figure.dpi": 300,
        }
    )


def save_figure(fig: plt.Figure, output_stem: Path) -> None:
    fig.savefig(output_stem.with_suffix(".png"), dpi=260, bbox_inches="tight")
    fig.savefig(output_stem.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def plot_frontier(config: dict, all_df: pd.DataFrame, frontier_df: pd.DataFrame) -> None:
    pareto_label = str(config["pareto_reference_finesse"])
    er_col = f"ER_min_dB_{pareto_label}"
    f_eval = float(config["fixed_finesse_values"][pareto_label])
    reps = set(config["representative_candidates_for_plot"])

    fig, ax = plt.subplots(figsize=(7.2, 4.8), constrained_layout=True)
    ax.scatter(
        all_df["F_min_tau0"],
        all_df[er_col],
        s=20,
        color="#cbd5e1",
        alpha=0.75,
        edgecolors="none",
        label="All exact candidates",
        zorder=1,
    )
    ax.plot(
        frontier_df["F_min_tau0"],
        frontier_df[er_col],
        color="#0f766e",
        lw=1.6,
        marker="o",
        ms=4.5,
        label="Pareto frontier",
        zorder=3,
    )

    highlight_styles = {
        "6/29": {"color": "#b45309", "marker": "s"},
        "7/29": {"color": "#b91c1c", "marker": "o"},
        "10/37": {"color": "#1d4ed8", "marker": "^"},
    }
    for _, row in all_df.loc[all_df["k_fraction"].isin(reps)].iterrows():
        style = highlight_styles.get(str(row["k_fraction"]), {"color": "#111827", "marker": "D"})
        ax.scatter(
            [row["F_min_tau0"]],
            [row[er_col]],
            s=55,
            color=style["color"],
            marker=style["marker"],
            edgecolors="white",
            linewidths=0.6,
            zorder=4,
        )
        ax.annotate(
            str(row["k_fraction"]),
            xy=(row["F_min_tau0"], row[er_col]),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=8,
            color=style["color"],
        )

    ax.set_xlabel(r"Required finesse $F_{\min}$ at $\tau_0=3$")
    ax.set_ylabel(rf"Worst-channel $\mathrm{{ER}}_{{\mathrm{{sum}}}}$ at $F={f_eval:.0f}$ (dB)")
    ax.set_title("Nonuniform design trade-off: required finesse vs fixed-F worst-channel ER")
    ax.grid(alpha=0.25, linestyle=":")
    ax.legend(loc="lower right")

    save_figure(fig, FIGURES_DIR / "ermin_frontier")


def plot_representative_comparison(config: dict, all_df: pd.DataFrame) -> None:
    reps = list(config["representative_candidates_for_plot"])
    f_eval = float(config["fixed_finesse_values"]["F87"])
    modes = [int(value) for value in config["target_modes"]]

    metrics_by_candidate: dict[str, np.ndarray] = {}
    lr_by_candidate: dict[str, float] = {}
    for candidate_key in reps:
        row = all_df.loc[all_df["k_fraction"] == candidate_key]
        if row.empty:
            raise AssertionError(f"Representative candidate {candidate_key} missing from all_candidate_metrics.csv.")
        k_value = float(row.iloc[0]["k"])
        lr_by_candidate[candidate_key] = float(row.iloc[0]["L_over_R"])
        metrics = evaluate_response_metrics(modes, k_value, f_eval)
        metrics_by_candidate[candidate_key] = metrics.er_sum_db

    x = np.arange(len(modes))
    width = 0.24
    colors = {"6/29": "#b45309", "7/29": "#b91c1c", "10/37": "#1d4ed8"}

    fig, ax = plt.subplots(figsize=(8.0, 4.8), constrained_layout=True)
    for idx, candidate_key in enumerate(reps):
        offset = (idx - 1) * width
        label = f"{candidate_key}  (L/R={lr_by_candidate[candidate_key]:.3f})"
        ax.bar(
            x + offset,
            metrics_by_candidate[candidate_key],
            width=width,
            color=colors.get(candidate_key, "#475569"),
            edgecolor="white",
            linewidth=0.4,
            label=label,
            zorder=3,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([str(mode) for mode in modes], rotation=45, ha="right")
    ax.set_xlabel("Mode index")
    ax.set_ylabel(r"$\mathrm{ER}_{\mathrm{sum}}$ (dB)")
    ax.set_title(r"Representative candidates compared at fixed finesse $F=87$")
    ax.grid(axis="y", alpha=0.25, linestyle=":")
    ax.set_axisbelow(True)
    ax.legend(ncol=1, loc="upper left")

    save_figure(fig, FIGURES_DIR / "representative_candidate_comparison_F87")


def main() -> None:
    ensure_dir(FIGURES_DIR)
    configure_style()

    config = load_config()
    all_df = pd.read_csv(TABLES_DIR / "all_candidate_metrics.csv")
    frontier_df = pd.read_csv(TABLES_DIR / "pareto_frontier_Fmin_vs_ERmin.csv")

    plot_frontier(config, all_df, frontier_df)
    plot_representative_comparison(config, all_df)

    print(f"Figures written to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
