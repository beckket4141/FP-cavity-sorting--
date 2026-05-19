from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, savgol_filter

from identify_symmetrized_peaks import build_peak_families, peak_records_to_frame
from identify_symmetrized_peaks import detect_peaks as detect_symmetrized_peaks
from identify_symmetrized_peaks import load_trace

DEFAULT_DETECTION_PARAMS = {
    "smooth_window": 21,
    "smooth_polyorder": 3,
    "prominence_frac": 0.01,
    "prominence_abs": 1.0,
    "height_frac": 0.02,
    "height_abs": 3.0,
    "distance_points": 20,
    "min_width_points": 3.0,
    "edge_margin_frac": 0.18,
    "main_family_count": 2,
}
DEFAULT_REDUCTION_FRAC = 0.20
DEFAULT_TARGET_ROLE = "crosstalk_candidate"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reduce the crosstalk-candidate peak in a symmetrized scan CSV while preserving the local baseline."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("DATA77_l7_symmetrized_l7_final.csv"),
        help="Input CSV with Lambda_aligned and Power_uW columns.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to the CSV folder.",
    )
    parser.add_argument(
        "--reduction-frac",
        type=float,
        default=DEFAULT_REDUCTION_FRAC,
        help="Fraction by which the peak envelope above the local baseline is reduced.",
    )
    parser.add_argument(
        "--target-role",
        type=str,
        default=DEFAULT_TARGET_ROLE,
        help="Role from selected peak families to modify.",
    )
    parser.add_argument(
        "--smooth-window",
        type=int,
        default=DEFAULT_DETECTION_PARAMS["smooth_window"],
        help="Savitzky-Golay window length used for peak finding.",
    )
    parser.add_argument(
        "--smooth-polyorder",
        type=int,
        default=DEFAULT_DETECTION_PARAMS["smooth_polyorder"],
        help="Savitzky-Golay polynomial order used for peak finding.",
    )
    parser.add_argument(
        "--prominence-frac",
        type=float,
        default=DEFAULT_DETECTION_PARAMS["prominence_frac"],
        help="Minimum prominence as a fraction of the smoothed max power.",
    )
    parser.add_argument(
        "--prominence-abs",
        type=float,
        default=DEFAULT_DETECTION_PARAMS["prominence_abs"],
        help="Absolute lower bound for the prominence threshold in uW.",
    )
    parser.add_argument(
        "--height-frac",
        type=float,
        default=DEFAULT_DETECTION_PARAMS["height_frac"],
        help="Minimum height as a fraction of the smoothed max power.",
    )
    parser.add_argument(
        "--height-abs",
        type=float,
        default=DEFAULT_DETECTION_PARAMS["height_abs"],
        help="Absolute lower bound for the height threshold in uW.",
    )
    parser.add_argument(
        "--distance-points",
        type=int,
        default=DEFAULT_DETECTION_PARAMS["distance_points"],
        help="Minimum point distance between adjacent peaks.",
    )
    parser.add_argument(
        "--min-width-points",
        type=float,
        default=DEFAULT_DETECTION_PARAMS["min_width_points"],
        help="Minimum fitted peak width in sample points.",
    )
    parser.add_argument(
        "--edge-margin-frac",
        type=float,
        default=DEFAULT_DETECTION_PARAMS["edge_margin_frac"],
        help="Fraction of full lambda span treated as a wrapped edge region.",
    )
    parser.add_argument(
        "--main-family-count",
        type=int,
        default=DEFAULT_DETECTION_PARAMS["main_family_count"],
        help="How many strongest peak families to mark as major peaks before the candidate peak.",
    )
    return parser.parse_args()


def build_processing_namespace(
    *,
    input_csv: Path,
    output_dir: Path | None = None,
    reduction_frac: float = DEFAULT_REDUCTION_FRAC,
    target_role: str = DEFAULT_TARGET_ROLE,
    **detection_overrides: float | int,
) -> argparse.Namespace:
    config = dict(DEFAULT_DETECTION_PARAMS)
    config.update(detection_overrides)
    return argparse.Namespace(
        input_csv=input_csv,
        output_dir=output_dir,
        reduction_frac=reduction_frac,
        target_role=target_role,
        **config,
    )


def _build_detection_namespace(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        smooth_window=args.smooth_window,
        smooth_polyorder=args.smooth_polyorder,
        prominence_frac=args.prominence_frac,
        prominence_abs=args.prominence_abs,
        height_frac=args.height_frac,
        height_abs=args.height_abs,
        distance_points=args.distance_points,
        min_width_points=args.min_width_points,
        edge_margin_frac=args.edge_margin_frac,
        main_family_count=args.main_family_count,
    )


def _validated_smooth_trace(y: np.ndarray, smooth_window: int, smooth_polyorder: int) -> np.ndarray:
    window = int(smooth_window)
    if window < 3:
        raise ValueError("--smooth-window must be at least 3.")
    if window % 2 == 0:
        window += 1
    if window > len(y):
        window = len(y) if len(y) % 2 == 1 else len(y) - 1
    if window <= smooth_polyorder:
        raise ValueError("Savitzky-Golay window must be larger than polyorder.")
    return savgol_filter(y, window, smooth_polyorder)


def select_target_peak(
    df: pd.DataFrame,
    x: np.ndarray,
    y: np.ndarray,
    y_smooth: np.ndarray,
    args: argparse.Namespace,
) -> tuple[pd.DataFrame, pd.DataFrame, int, dict[str, float]]:
    detection_args = _build_detection_namespace(args)
    _, _, peak_records, edge_margin_nm = detect_symmetrized_peaks(df, detection_args)
    peak_df = peak_records_to_frame(peak_records)
    family_df, _ = build_peak_families(
        peak_df=peak_df,
        edge_margin_nm=edge_margin_nm,
        main_family_count=args.main_family_count,
    )

    target_rows = family_df.loc[family_df["role"] == args.target_role]
    if target_rows.empty:
        raise RuntimeError(f"No peak family found for role '{args.target_role}'.")
    target_row = target_rows.iloc[0]
    target_lambda = float(target_row["representative_lambda_nm"])
    target_peak_index = int(np.argmin(np.abs(x - target_lambda)))

    max_power = float(np.max(y_smooth))
    prominence = max(args.prominence_abs, args.prominence_frac * max_power)
    min_height = max(args.height_abs, args.height_frac * max_power)
    peaks, properties = find_peaks(
        y_smooth,
        prominence=prominence,
        height=min_height,
        distance=args.distance_points,
        width=args.min_width_points,
    )
    target_peak_slot = int(np.argmin(np.abs(peaks - target_peak_index)))
    target_peak_index = int(peaks[target_peak_slot])

    info = {
        "target_peak_id": int(peak_df.iloc[target_peak_slot]["peak_id"]),
        "target_lambda_nm": float(x[target_peak_index]),
        "left_base_index": int(properties["left_bases"][target_peak_slot]),
        "right_base_index": int(properties["right_bases"][target_peak_slot]),
        "original_peak_power_uW": float(y[target_peak_index]),
    }
    return peak_df, family_df, target_peak_index, info


def reduce_peak_segment(
    x: np.ndarray,
    y: np.ndarray,
    target_peak_index: int,
    left_base_index: int,
    right_base_index: int,
    reduction_frac: float,
) -> tuple[np.ndarray, dict[str, float]]:
    if not (0.0 <= reduction_frac <= 1.0):
        raise ValueError("--reduction-frac must be between 0 and 1.")
    if not (0 <= left_base_index < target_peak_index < right_base_index < len(y)):
        raise ValueError("Invalid peak/baseline indices.")

    y_new = y.copy()
    segment_slice = slice(left_base_index, right_base_index + 1)
    x_seg = x[segment_slice]
    y_seg = y[segment_slice]

    baseline_seg = np.interp(
        x_seg,
        [x[left_base_index], x[right_base_index]],
        [y[left_base_index], y[right_base_index]],
    )
    envelope_above_baseline = np.maximum(y_seg - baseline_seg, 0.0)
    y_new[segment_slice] = baseline_seg + envelope_above_baseline * (1.0 - reduction_frac)

    local_peak_offset = target_peak_index - left_base_index
    stats = {
        "left_base_lambda_nm": float(x[left_base_index]),
        "right_base_lambda_nm": float(x[right_base_index]),
        "baseline_at_peak_uW": float(baseline_seg[local_peak_offset]),
        "old_peak_uW": float(y[target_peak_index]),
        "new_peak_uW": float(y_new[target_peak_index]),
        "left_base_power_uW": float(y[left_base_index]),
        "right_base_power_uW": float(y[right_base_index]),
        "modified_point_count": int(right_base_index - left_base_index + 1),
    }
    return y_new, stats


def save_outputs(
    df_original: pd.DataFrame,
    y_new: np.ndarray,
    peak_df: pd.DataFrame,
    family_df: pd.DataFrame,
    target_peak_index: int,
    info: dict[str, float],
    stats: dict[str, float],
    output_dir: Path,
    stem: str,
    *,
    export_reference_tables: bool = True,
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    df_modified = df_original.copy()
    df_modified["Power_uW"] = y_new
    output_csv = output_dir / f"{stem}_crosstalk_reduced.csv"
    df_modified.to_csv(output_csv, index=False, encoding="utf-8-sig")

    report = {
        "target_role": "crosstalk_candidate",
        "target_peak_index": int(target_peak_index),
        "target_peak_lambda_nm": float(info["target_lambda_nm"]),
        "target_peak_id": int(info["target_peak_id"]),
        **info,
        **stats,
    }
    report_path = output_dir / f"{stem}_crosstalk_reduction_summary.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    plot_path = output_dir / f"{stem}_crosstalk_reduction_comparison.png"
    x = df_original["Lambda_aligned"].to_numpy(dtype=float)
    y = df_original["Power_uW"].to_numpy(dtype=float)
    left_base_index = int(info["left_base_index"])
    right_base_index = int(info["right_base_index"])

    fig, (ax_all, ax_zoom) = plt.subplots(2, 1, figsize=(11.2, 7.2), height_ratios=[2.2, 1.5])
    ax_all.plot(x, y, color="#94a3b8", lw=1.0, label="original")
    ax_all.plot(x, y_new, color="#dc2626", lw=1.2, label="modified")
    ax_all.axvspan(
        x[left_base_index],
        x[right_base_index],
        color="#fde68a",
        alpha=0.25,
        label="modified window",
    )
    ax_all.scatter([x[target_peak_index]], [y[target_peak_index]], color="#2563eb", s=48, zorder=3, label="target peak")
    ax_all.set_title("Crosstalk-peak reduction: full trace")
    ax_all.set_xlabel("Lambda_aligned (nm)")
    ax_all.set_ylabel("Power_uW")
    ax_all.grid(alpha=0.2)
    ax_all.legend(frameon=False)

    pad = max(6, int(0.25 * (right_base_index - left_base_index + 1)))
    view_left = max(0, left_base_index - pad)
    view_right = min(len(x) - 1, right_base_index + pad)
    ax_zoom.plot(x[view_left : view_right + 1], y[view_left : view_right + 1], color="#94a3b8", lw=1.2, label="original")
    ax_zoom.plot(x[view_left : view_right + 1], y_new[view_left : view_right + 1], color="#dc2626", lw=1.4, label="modified")
    baseline_zoom = np.interp(
        x[left_base_index : right_base_index + 1],
        [x[left_base_index], x[right_base_index]],
        [y[left_base_index], y[right_base_index]],
    )
    ax_zoom.plot(
        x[left_base_index : right_base_index + 1],
        baseline_zoom,
        color="#059669",
        lw=1.2,
        ls="--",
        label="local baseline",
    )
    ax_zoom.axvspan(x[left_base_index], x[right_base_index], color="#fde68a", alpha=0.25)
    ax_zoom.scatter([x[target_peak_index]], [y[target_peak_index]], color="#2563eb", s=48)
    ax_zoom.scatter([x[target_peak_index]], [y_new[target_peak_index]], color="#dc2626", s=48)
    ax_zoom.set_title("Zoom on the modified crosstalk candidate")
    ax_zoom.set_xlabel("Lambda_aligned (nm)")
    ax_zoom.set_ylabel("Power_uW")
    ax_zoom.grid(alpha=0.2)
    ax_zoom.legend(frameon=False)

    fig.tight_layout()
    fig.savefig(plot_path, dpi=180)
    plt.close(fig)

    if export_reference_tables:
        peak_df.to_csv(output_dir / f"{stem}_reduction_reference_detected_peaks.csv", index=False, encoding="utf-8-sig")
        family_df.to_csv(output_dir / f"{stem}_reduction_reference_peak_families.csv", index=False, encoding="utf-8-sig")

    return output_csv, report_path, plot_path


def process_single_csv(
    input_csv: Path,
    output_dir: Path | None = None,
    *,
    reduction_frac: float = DEFAULT_REDUCTION_FRAC,
    target_role: str = DEFAULT_TARGET_ROLE,
    export_reference_tables: bool = True,
    **detection_overrides: float | int,
) -> dict[str, object]:
    csv_path = Path(input_csv).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    args = build_processing_namespace(
        input_csv=csv_path,
        output_dir=output_dir,
        reduction_frac=reduction_frac,
        target_role=target_role,
        **detection_overrides,
    )
    resolved_output_dir = args.output_dir.resolve() if args.output_dir else csv_path.parent

    df = load_trace(csv_path)
    x = df["Lambda_aligned"].to_numpy(dtype=float)
    y = df["Power_uW"].to_numpy(dtype=float)
    y_smooth = _validated_smooth_trace(y, args.smooth_window, args.smooth_polyorder)

    peak_df, family_df, target_peak_index, info = select_target_peak(df, x, y, y_smooth, args)
    y_new, stats = reduce_peak_segment(
        x=x,
        y=y,
        target_peak_index=target_peak_index,
        left_base_index=int(info["left_base_index"]),
        right_base_index=int(info["right_base_index"]),
        reduction_frac=args.reduction_frac,
    )
    output_csv, report_path, plot_path = save_outputs(
        df_original=df,
        y_new=y_new,
        peak_df=peak_df,
        family_df=family_df,
        target_peak_index=target_peak_index,
        info=info,
        stats=stats,
        output_dir=resolved_output_dir,
        stem=csv_path.stem,
        export_reference_tables=export_reference_tables,
    )

    return {
        "input_csv": csv_path,
        "output_csv": output_csv,
        "summary_json": report_path,
        "comparison_plot": plot_path,
        "peak_df": peak_df,
        "family_df": family_df,
        "target_peak_index": target_peak_index,
        "info": info,
        "stats": stats,
    }


def main() -> None:
    args = parse_args()
    result = process_single_csv(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        reduction_frac=args.reduction_frac,
        target_role=args.target_role,
        export_reference_tables=True,
        smooth_window=args.smooth_window,
        smooth_polyorder=args.smooth_polyorder,
        prominence_frac=args.prominence_frac,
        prominence_abs=args.prominence_abs,
        height_frac=args.height_frac,
        height_abs=args.height_abs,
        distance_points=args.distance_points,
        min_width_points=args.min_width_points,
        edge_margin_frac=args.edge_margin_frac,
        main_family_count=args.main_family_count,
    )

    info = result["info"]
    stats = result["stats"]
    print(f"input_csv={result['input_csv']}")
    print(f"target_lambda_nm={info['target_lambda_nm']:.12f}")
    print(f"left_base_index={int(info['left_base_index'])}, right_base_index={int(info['right_base_index'])}")
    print(f"old_peak_uW={stats['old_peak_uW']:.6f}")
    print(f"new_peak_uW={stats['new_peak_uW']:.6f}")
    print(f"baseline_at_peak_uW={stats['baseline_at_peak_uW']:.6f}")
    print(f"modified_point_count={stats['modified_point_count']}")
    print(f"output_csv={result['output_csv']}")
    print(f"summary_json={result['summary_json']}")
    print(f"comparison_plot={result['comparison_plot']}")


if __name__ == "__main__":
    main()
