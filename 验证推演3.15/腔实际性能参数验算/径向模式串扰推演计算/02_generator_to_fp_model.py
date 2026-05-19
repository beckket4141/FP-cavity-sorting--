from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lg_mode_tools import (
    apply_aperture,
    canonical_scaled_eta,
    format_pct,
    inner_product,
    lg_mode_cartesian,
    make_square_grid,
    normalize_field,
    parse_float_list,
    phase_only_vortex_cartesian,
    pixelate_field,
    write_csv,
)


REFERENCE_W0_MM = 0.88
P_MAX = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare complex-amplitude and phase-only LG generation before FP-cavity injection."
    )
    parser.add_argument("--mode", choices=["bolduc", "yang_phase_only", "both"], default="both")
    parser.add_argument("--l-max", type=int, default=8)
    parser.add_argument("--grid-size", type=int, default=384)
    parser.add_argument(
        "--aperture-mm",
        type=float,
        default=2.45,
        help="Effective circular aperture radius in mm at the generation plane.",
    )
    parser.add_argument(
        "--pixel-pitch-um",
        type=float,
        default=8.0,
        help="Effective pixel pitch for blocky sampling at the generation plane.",
    )
    parser.add_argument(
        "--misalignment-scan",
        type=str,
        default="0.00,0.08,0.16",
        help="Comma-separated lateral shifts in units of the cavity w0.",
    )
    parser.add_argument("--output-prefix", type=str, default="generator_model_")
    return parser.parse_args()


def requested_models(mode: str) -> list[str]:
    if mode == "both":
        return ["bolduc", "yang_phase_only"]
    return [mode]


def strategy_ratio(strategy: str, l: int) -> float:
    if strategy == "same_w0":
        return 1.0
    return canonical_scaled_eta(l)


def build_basis_cache(x: np.ndarray, y: np.ndarray, dx: float, l_max: int) -> dict[tuple[int, int], np.ndarray]:
    cache: dict[tuple[int, int], np.ndarray] = {}
    for l in range(l_max + 1):
        for p in range(P_MAX + 1):
            cache[(p, l)] = normalize_field(lg_mode_cartesian(x, y, p=p, l=l, w0=1.0), dx)
    return cache


def basis_field(
    x: np.ndarray,
    y: np.ndarray,
    dx: float,
    p: int,
    l: int,
    w_basis: float,
    cache: dict[tuple[int, int, float], np.ndarray],
) -> np.ndarray:
    key = (p, l, round(float(w_basis), 8))
    if key not in cache:
        cache[key] = normalize_field(lg_mode_cartesian(x, y, p=p, l=l, w0=w_basis), dx)
    return cache[key]


def generate_field(
    model: str,
    strategy: str,
    l: int,
    x: np.ndarray,
    y: np.ndarray,
    dx: float,
    aperture_radius_w: float,
    pixel_size_w: float,
    shift_w: float,
) -> tuple[np.ndarray, float]:
    if model == "bolduc":
        w_input = strategy_ratio(strategy, l)
        field = normalize_field(
            lg_mode_cartesian(x, y, p=0, l=l, w0=w_input, shift_x=shift_w, shift_y=0.0),
            dx,
        )
    else:
        w_input = 1.0
        field = normalize_field(
            phase_only_vortex_cartesian(x, y, l=l, w_phase=w_input, shift_x=shift_w, shift_y=0.0),
            dx,
        )

    field = apply_aperture(field, x, y, aperture_radius_w)
    field = pixelate_field(field, pixel_size_w, dx)
    retained_power = float(np.sum(np.abs(field) ** 2) * dx * dx)
    return field, retained_power


def analyze_field(
    field: np.ndarray,
    retained_power: float,
    dx: float,
    cavity_basis_cache: dict[tuple[int, int], np.ndarray],
    variable_basis_cache: dict[tuple[int, int, float], np.ndarray],
    x: np.ndarray,
    y: np.ndarray,
    l: int,
    analysis_basis_w: float,
) -> dict[str, float | int]:
    target = cavity_basis_cache[(0, l)]
    c0 = inner_product(target, field, dx)
    target_overlap_power = float(abs(c0) ** 2)

    if retained_power <= 1e-15:
        return {
            "retained_power": retained_power,
            "target_overlap_power": target_overlap_power,
            "p0_modal_weight": 0.0,
            "p1_modal_weight": 0.0,
            "leakage_modal_weight": 0.0,
            "dominant_p": -1,
        }

    normalized = field / math.sqrt(retained_power)
    weights = []
    for p in range(P_MAX + 1):
        basis = basis_field(x, y, dx, p, l, analysis_basis_w, variable_basis_cache)
        coeff = inner_product(basis, normalized, dx)
        weights.append(float(abs(coeff) ** 2))

    dominant_p = int(np.argmax(weights))
    p0 = weights[0]
    p1 = weights[1] if len(weights) > 1 else 0.0
    leakage = max(0.0, 1.0 - p0)
    return {
        "retained_power": retained_power,
        "target_overlap_power": target_overlap_power,
        "p0_modal_weight": p0,
        "p1_modal_weight": p1,
        "leakage_modal_weight": leakage,
        "dominant_p": dominant_p,
    }


def build_rows(args: argparse.Namespace) -> list[dict]:
    aperture_radius_w = args.aperture_mm / REFERENCE_W0_MM
    pixel_size_w = (args.pixel_pitch_um / 1000.0) / REFERENCE_W0_MM
    shift_values = parse_float_list(args.misalignment_scan, default=[0.0, 0.04, 0.08])
    extent = max(5.0, aperture_radius_w * 1.25)
    x, y, dx = make_square_grid(extent=extent, grid_size=args.grid_size)
    basis_cache = build_basis_cache(x, y, dx, args.l_max)
    variable_basis_cache: dict[tuple[int, int, float], np.ndarray] = {}

    rows: list[dict] = []
    for model in requested_models(args.mode):
        for strategy in ["same_w0", "scaled_w0"]:
            for shift_w in shift_values:
                for l in range(args.l_max + 1):
                    analysis_basis_w = 1.0 if model == "bolduc" else strategy_ratio(strategy, l)
                    w_input = strategy_ratio(strategy, l) if model == "bolduc" else 1.0
                    field, retained_power = generate_field(
                        model=model,
                        strategy=strategy,
                        l=l,
                        x=x,
                        y=y,
                        dx=dx,
                        aperture_radius_w=aperture_radius_w,
                        pixel_size_w=pixel_size_w,
                        shift_w=shift_w,
                    )
                    analysis = analyze_field(
                        field=field,
                        retained_power=retained_power,
                        dx=dx,
                        cavity_basis_cache=basis_cache,
                        variable_basis_cache=variable_basis_cache,
                        x=x,
                        y=y,
                        l=l,
                        analysis_basis_w=analysis_basis_w,
                    )
                    rows.append(
                        {
                            "model": model,
                            "strategy": strategy,
                            "l": l,
                            "shift_w0": shift_w,
                            "w_input_over_w_cav": w_input,
                            "analysis_basis_over_w_cav": analysis_basis_w,
                            "retained_power": analysis["retained_power"],
                            "target_overlap_power": analysis["target_overlap_power"],
                            "p0_modal_weight": analysis["p0_modal_weight"],
                            "p1_modal_weight": analysis["p1_modal_weight"],
                            "leakage_modal_weight": analysis["leakage_modal_weight"],
                            "dominant_p": analysis["dominant_p"],
                        }
                    )
    return rows


def representative_shift(rows: list[dict]) -> float:
    shifts = sorted({float(row["shift_w0"]) for row in rows})
    return float(np.median(shifts))


def subset(rows: list[dict], model: str, strategy: str, shift_w0: float) -> list[dict]:
    return [
        row
        for row in rows
        if row["model"] == model and row["strategy"] == strategy and abs(float(row["shift_w0"]) - shift_w0) < 1e-12
    ]


def build_figure(out_path: Path, rows: list[dict], mode: str) -> None:
    rep_shift = representative_shift(rows)
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    ax1, ax2, ax3, ax4 = axes.flat

    models = requested_models(mode)

    if "bolduc" in models:
        same = subset(rows, "bolduc", "same_w0", rep_shift)
        scaled = subset(rows, "bolduc", "scaled_w0", rep_shift)
        ax1.plot([row["l"] for row in same], [row["target_overlap_power"] for row in same], "o-", label="Bolduc same w0")
        ax1.plot([row["l"] for row in scaled], [row["target_overlap_power"] for row in scaled], "s-", label="Bolduc scaled w0")
    ax1.set_title(f"Complex-Amplitude Input vs l (shift={rep_shift:.2f} w0)")
    ax1.set_xlabel(r"$l$")
    ax1.set_ylabel("Actual target coupling")
    ax1.set_ylim(-0.02, 1.05)
    ax1.grid(alpha=0.3)
    ax1.legend()

    if "yang_phase_only" in models:
        same = subset(rows, "yang_phase_only", "same_w0", rep_shift)
        scaled = subset(rows, "yang_phase_only", "scaled_w0", rep_shift)
        ax2.plot(
            [row["l"] for row in same],
            [row["target_overlap_power"] for row in same],
            "o-",
            label="Actual cavity coupling",
        )
        ax2.plot(
            [row["l"] for row in scaled],
            [row["p0_modal_weight"] for row in scaled],
            "s--",
            label=r"Best-fit $p=0$ weight with scaled LG basis",
        )
    ax2.set_title(f"Phase-Only Context Split (shift={rep_shift:.2f} w0)")
    ax2.set_xlabel(r"$l$")
    ax2.set_ylabel("Power / modal weight")
    ax2.set_ylim(-0.02, 1.05)
    ax2.grid(alpha=0.3)
    ax2.legend()

    if "yang_phase_only" in models:
        same = subset(rows, "yang_phase_only", "same_w0", rep_shift)
        scaled = subset(rows, "yang_phase_only", "scaled_w0", rep_shift)
        ax3.plot([row["l"] for row in same], [row["p0_modal_weight"] for row in same], "o-", label="Phase-only same w0")
        ax3.plot(
            [row["l"] for row in scaled],
            [row["p0_modal_weight"] for row in scaled],
            "s-",
            label="Phase-only scaled w0",
        )
    ax3.set_title("Modal purity inside the retained light")
    ax3.set_xlabel(r"$l$")
    ax3.set_ylabel(r"$p=0$ modal weight")
    ax3.set_ylim(-0.02, 1.05)
    ax3.grid(alpha=0.3)
    ax3.legend()

    if "bolduc" in models:
        for shift in sorted({float(row["shift_w0"]) for row in rows}):
            same = subset(rows, "bolduc", "same_w0", shift)
            ax4.plot(
                [row["l"] for row in same],
                [row["target_overlap_power"] for row in same],
                marker="o",
                label=fr"shift={shift:.2f}$w_0$",
            )
    ax4.set_title("Complex-amplitude same-w0 sensitivity")
    ax4.set_xlabel(r"$l$")
    ax4.set_ylabel("Actual target coupling")
    ax4.set_ylim(-0.02, 1.05)
    ax4.grid(alpha=0.3)
    ax4.legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def build_summary(out_path: Path, rows: list[dict], mode: str, args: argparse.Namespace) -> None:
    rep_shift = representative_shift(rows)
    lines = [
        "Generator-to-FP model summary",
        "",
        "Model assumptions:",
        f"  Reference cavity waist: w0 = 1 (mapped to {REFERENCE_W0_MM:.2f} mm for aperture and pixel scales).",
        f"  Effective aperture radius: {args.aperture_mm:.2f} mm = {args.aperture_mm / REFERENCE_W0_MM:.3f} w0.",
        f"  Effective pixel pitch: {args.pixel_pitch_um:.2f} um = {(args.pixel_pitch_um / 1000.0) / REFERENCE_W0_MM:.4f} w0.",
        f"  Misalignment scan (w0 units): {args.misalignment_scan}",
        f"  Representative shift for plots: {rep_shift:.2f} w0.",
        "",
    ]

    for model in requested_models(mode):
        lines.append(f"{model}:")
        for strategy in ["same_w0", "scaled_w0"]:
            rows_ms = subset(rows, model, strategy, rep_shift)
            lines.append(f"  {strategy}:")
            for row in rows_ms:
                lines.append(
                    f"    l={int(row['l'])}: retained={format_pct(float(row['retained_power']))}, "
                    f"target={format_pct(float(row['target_overlap_power']))}, "
                    f"p0|retained={format_pct(float(row['p0_modal_weight']))}, "
                    f"dominant_p={int(row['dominant_p'])}"
                )
        lines.append("")

    lines.append("Interpretation:")
    lines.append("  1. For complex-amplitude generation, same w0 keeps the field close to the cavity LG_{0}^{l} family; scaled w0 destroys the target overlap.")
    lines.append("  2. For phase-only generation, the Yang/Sroor scaling improves the best-fit LG p=0 content when one changes the decomposition scale, even though the real cavity target basis is unchanged.")
    lines.append("  3. Phase-only best-fit purity and FP-cavity q matching are therefore not the same statement.")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = build_rows(args)
    write_csv(Path(f"{args.output_prefix}table.csv"), rows)
    build_figure(Path(f"{args.output_prefix}curves.png"), rows, args.mode)
    build_summary(Path(f"{args.output_prefix}summary.txt"), rows, args.mode, args)


if __name__ == "__main__":
    main()
