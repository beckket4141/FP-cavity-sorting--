from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def data_root() -> Path:
    return script_dir().parent / "满载叠加态输入数据" / "最终数据"


def find_transmittance_file(run_dir: Path) -> Path:
    excluded = {
        "calib_matrix_with_uncertainty.xlsx",
        "channel_snr_analysis.xlsx",
        "final_matrix_summary.xlsx",
        "full4_matrix_with_uncertainty.xlsx",
        "full9_matrix_with_uncertainty.xlsx",
    }
    candidates = [path for path in run_dir.iterdir() if path.suffix.lower() == ".xlsx" and path.name not in excluded]
    if not candidates:
        raise FileNotFoundError(f"No transmittance workbook found in {run_dir}")
    return candidates[0]


def read_experiment_table() -> pd.DataFrame:
    rows = []
    for run in ["1", "2", "3"]:
        workbook = find_transmittance_file(data_root() / run)
        df = pd.read_excel(workbook)
        before = pd.to_numeric(df.iloc[:, 2], errors="coerce")
        after = pd.to_numeric(df.iloc[:, 3].astype(str).str.replace("_x000d_", "", regex=False), errors="coerce")
        ratios = after / before
        for idx, ratio in enumerate(ratios):
            rows.append({"run": run, "l": idx, "transmittance": float(ratio)})
    raw = pd.DataFrame(rows)
    summary = raw.groupby("l")["transmittance"].agg(["mean", "std"]).reset_index()
    summary = summary.rename(columns={"mean": "experiment_mean", "std": "experiment_std"})
    return summary


def representative_shift(generator_df: pd.DataFrame) -> float:
    return float(generator_df["shift_w0"].median())


def scale_to_experiment_l0(series: pd.Series, experiment_l0: float) -> pd.Series:
    return experiment_l0 * series / float(series.iloc[0])


def main() -> None:
    exp = read_experiment_table()
    ideal = pd.read_csv(script_dir() / "ideal_overlap_table.csv")
    gen = pd.read_csv(script_dir() / "generator_model_table.csv")

    rep_shift = representative_shift(gen)
    exp_l0 = float(exp.loc[exp["l"] == 0, "experiment_mean"].iloc[0])

    ideal_same = ideal[ideal["scenario"] == "same_w0"].sort_values("l").reset_index(drop=True)
    bolduc_same = gen[
        (gen["model"] == "bolduc") & (gen["strategy"] == "same_w0") & (gen["shift_w0"] == rep_shift)
    ].sort_values("l").reset_index(drop=True)
    bolduc_scaled = gen[
        (gen["model"] == "bolduc") & (gen["strategy"] == "scaled_w0") & (gen["shift_w0"] == rep_shift)
    ].sort_values("l").reset_index(drop=True)
    yang_same = gen[
        (gen["model"] == "yang_phase_only") & (gen["strategy"] == "same_w0") & (gen["shift_w0"] == rep_shift)
    ].sort_values("l").reset_index(drop=True)
    yang_scaled = gen[
        (gen["model"] == "yang_phase_only") & (gen["strategy"] == "scaled_w0") & (gen["shift_w0"] == rep_shift)
    ].sort_values("l").reset_index(drop=True)

    compare = exp.copy()
    compare["ideal_same_scaled_to_l0"] = scale_to_experiment_l0(ideal_same["target_overlap_power"], exp_l0)
    compare["bolduc_same_scaled_to_l0"] = scale_to_experiment_l0(bolduc_same["target_overlap_power"], exp_l0)
    compare["bolduc_scaled_scaled_to_l0"] = scale_to_experiment_l0(bolduc_scaled["target_overlap_power"], exp_l0)
    compare["yang_actual_scaled_to_l0"] = scale_to_experiment_l0(yang_same["target_overlap_power"], exp_l0)
    compare["yang_bestfit_p0_scaled_to_l0"] = scale_to_experiment_l0(yang_scaled["p0_modal_weight"], exp_l0)
    compare["rep_shift_w0"] = rep_shift
    compare["effective_aperture_mm"] = 2.45

    compare.to_csv(script_dir() / "ch5_comparison.csv", index=False, encoding="utf-8-sig")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

    ax1.errorbar(
        compare["l"],
        compare["experiment_mean"],
        yerr=compare["experiment_std"],
        fmt="o",
        capsize=4,
        label="Experiment (chapter 5)",
    )
    ax1.plot(compare["l"], compare["ideal_same_scaled_to_l0"], "--", label="Ideal same w0 (flat reference)")
    ax1.plot(compare["l"], compare["bolduc_same_scaled_to_l0"], "o-", label="Complex-amplitude same w0")
    ax1.plot(compare["l"], compare["bolduc_scaled_scaled_to_l0"], "s-", label=r"Complex-amplitude scaled $w_l$")
    ax1.set_ylabel("Scaled transmittance")
    ax1.set_title("Chapter-5 Comparison: Experiment vs Cavity-Matching Models")
    ax1.grid(alpha=0.3)
    ax1.legend()

    ax2.errorbar(
        compare["l"],
        compare["experiment_mean"],
        yerr=compare["experiment_std"],
        fmt="o",
        capsize=4,
        label="Experiment (chapter 5)",
    )
    ax2.plot(compare["l"], compare["yang_actual_scaled_to_l0"], "o-", label="Phase-only actual cavity coupling")
    ax2.plot(
        compare["l"],
        compare["yang_bestfit_p0_scaled_to_l0"],
        "s--",
        label=r"Phase-only best-fit $p=0$ weight (scaled LG basis)",
    )
    ax2.set_xlabel(r"$l$")
    ax2.set_ylabel("Scaled transmittance")
    ax2.set_title("Yang/Sroor Context: Generation-End Purity vs Real Cavity Coupling")
    ax2.grid(alpha=0.3)
    ax2.legend()

    fig.tight_layout()
    fig.savefig(script_dir() / "ch5_comparison.png", dpi=200)
    plt.close(fig)

    lines = [
        "Chapter-5 comparison summary",
        "",
        f"Representative shift used from generator model: {rep_shift:.2f} w0",
        "Effective aperture radius used from generator model: 2.45 mm",
        "",
        "Key values (scaled to the experimental l=0 transmittance):",
    ]
    for _, row in compare.iterrows():
        lines.append(
            f"  l={int(row['l'])}: exp={row['experiment_mean']:.4f} +/- {row['experiment_std']:.4f}, "
            f"Bolduc same={row['bolduc_same_scaled_to_l0']:.4f}, "
            f"Bolduc scaled={row['bolduc_scaled_scaled_to_l0']:.4f}, "
            f"Yang actual={row['yang_actual_scaled_to_l0']:.4f}, "
            f"Yang best-fit p0={row['yang_bestfit_p0_scaled_to_l0']:.4f}"
        )
    lines.extend(
        [
            "",
            "Interpretation:",
            "  1. The measured high transmission for same w0 aligns with the complex-amplitude same-w0 model, not with the scaled-w0 cavity-matching hypothesis.",
            "  2. The sharp collapse under scaled w_l follows directly from q mismatch, even before one adds realistic losses.",
            "  3. The Yang/Sroor scaled basis helps explain phase-only generation purity, but it still does not reproduce the actual cavity-coupling behavior seen in your complex-amplitude experiment.",
        ]
    )
    (script_dir() / "ch5_comparison_summary.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
