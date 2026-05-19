from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_widths, savgol_filter


@dataclass(frozen=True)
class PeakRecord:
    peak_id: int
    index: int
    lambda_nm: float
    power_raw_uW: float
    power_smooth_uW: float
    prominence_uW: float
    width_points: float
    distance_to_left_nm: float
    distance_to_right_nm: float
    is_left_edge_candidate: bool
    is_right_edge_candidate: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Identify major peaks and a small crosstalk-like bump in a symmetrized cavity scan CSV."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("DATA77_l7_symmetrized_l7_final.csv"),
        help="Input CSV with columns Lambda_aligned and Power_uW.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to the CSV folder.",
    )
    parser.add_argument(
        "--smooth-window",
        type=int,
        default=21,
        help="Savitzky-Golay window length. Must be odd.",
    )
    parser.add_argument(
        "--smooth-polyorder",
        type=int,
        default=3,
        help="Savitzky-Golay polynomial order.",
    )
    parser.add_argument(
        "--prominence-frac",
        type=float,
        default=0.01,
        help="Minimum prominence as a fraction of the smoothed max power.",
    )
    parser.add_argument(
        "--prominence-abs",
        type=float,
        default=1.0,
        help="Absolute lower bound for the prominence threshold in uW.",
    )
    parser.add_argument(
        "--height-frac",
        type=float,
        default=0.02,
        help="Minimum height as a fraction of the smoothed max power.",
    )
    parser.add_argument(
        "--height-abs",
        type=float,
        default=3.0,
        help="Absolute lower bound for the height threshold in uW.",
    )
    parser.add_argument(
        "--distance-points",
        type=int,
        default=20,
        help="Minimum point distance between adjacent peaks.",
    )
    parser.add_argument(
        "--min-width-points",
        type=float,
        default=3.0,
        help="Minimum fitted peak width in sample points.",
    )
    parser.add_argument(
        "--edge-margin-frac",
        type=float,
        default=0.18,
        help="Fraction of full lambda span treated as a wrapped edge region.",
    )
    parser.add_argument(
        "--main-family-count",
        type=int,
        default=2,
        help="How many strongest peak families to mark as major peaks.",
    )
    return parser.parse_args()


def _validate_window(length: int, polyorder: int, n_samples: int) -> int:
    if length < 3:
        raise ValueError("--smooth-window must be at least 3.")
    if length % 2 == 0:
        length += 1
    if length > n_samples:
        length = n_samples if n_samples % 2 == 1 else n_samples - 1
    if length <= polyorder:
        raise ValueError("Savitzky-Golay window must be larger than polyorder.")
    return length


def load_trace(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required = {"Lambda_aligned", "Power_uW"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return df.sort_values("Lambda_aligned").reset_index(drop=True)


def detect_peaks(df: pd.DataFrame, args: argparse.Namespace) -> tuple[np.ndarray, np.ndarray, list[PeakRecord], float]:
    x = df["Lambda_aligned"].to_numpy(dtype=float)
    y = df["Power_uW"].to_numpy(dtype=float)
    smooth_window = _validate_window(args.smooth_window, args.smooth_polyorder, len(df))
    y_smooth = savgol_filter(y, smooth_window, args.smooth_polyorder)

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
    widths = peak_widths(y_smooth, peaks, rel_height=0.5)[0]

    if len(peaks) == 0:
        raise RuntimeError("No peaks were detected. Try lowering the thresholds.")

    x_span = float(x[-1] - x[0])
    edge_margin_nm = args.edge_margin_frac * x_span
    peak_records: list[PeakRecord] = []
    for peak_id, peak_index in enumerate(peaks, start=1):
        idx = int(peak_index)
        left_dist = float(x[idx] - x[0])
        right_dist = float(x[-1] - x[idx])
        peak_records.append(
            PeakRecord(
                peak_id=peak_id,
                index=idx,
                lambda_nm=float(x[idx]),
                power_raw_uW=float(y[idx]),
                power_smooth_uW=float(y_smooth[idx]),
                prominence_uW=float(properties["prominences"][peak_id - 1]),
                width_points=float(widths[peak_id - 1]),
                distance_to_left_nm=left_dist,
                distance_to_right_nm=right_dist,
                is_left_edge_candidate=left_dist <= edge_margin_nm,
                is_right_edge_candidate=right_dist <= edge_margin_nm,
            )
        )

    return x, y_smooth, peak_records, edge_margin_nm


def peak_records_to_frame(peak_records: list[PeakRecord]) -> pd.DataFrame:
    rows = []
    for record in peak_records:
        rows.append(
            {
                "peak_id": record.peak_id,
                "index": record.index,
                "lambda_nm": record.lambda_nm,
                "power_raw_uW": record.power_raw_uW,
                "power_smooth_uW": record.power_smooth_uW,
                "prominence_uW": record.prominence_uW,
                "width_points": record.width_points,
                "distance_to_left_nm": record.distance_to_left_nm,
                "distance_to_right_nm": record.distance_to_right_nm,
                "is_left_edge_candidate": record.is_left_edge_candidate,
                "is_right_edge_candidate": record.is_right_edge_candidate,
            }
        )
    return pd.DataFrame(rows).sort_values("lambda_nm").reset_index(drop=True)


def assign_family_roles(
    family_df: pd.DataFrame,
    main_family_count: int,
    *,
    crosstalk_threshold_ratio: float = 0.5,
) -> pd.DataFrame:
    family_df = family_df.copy()
    family_df["role"] = "other"
    if family_df.empty:
        return family_df

    global_peak_idx = int(family_df["power_smooth_uW"].idxmax())
    family_df.loc[global_peak_idx, "role"] = "major_peak_1"
    global_peak_power = float(family_df.loc[global_peak_idx, "power_smooth_uW"])
    crosstalk_threshold = global_peak_power * crosstalk_threshold_ratio

    crosstalk_candidates = family_df.loc[
        family_df["power_smooth_uW"] < crosstalk_threshold
    ].sort_values(["power_smooth_uW", "representative_lambda_nm"], ascending=[False, True])
    if not crosstalk_candidates.empty:
        crosstalk_idx = int(crosstalk_candidates.index[0])
        family_df.loc[crosstalk_idx, "role"] = "crosstalk_candidate"

    remaining_major_labels = [f"major_peak_{idx}" for idx in range(2, main_family_count + 1)]
    if remaining_major_labels:
        remaining_rows = family_df.loc[family_df["role"] == "other"].sort_values(
            ["power_smooth_uW", "representative_lambda_nm"], ascending=[False, True]
        )
        for label, idx in zip(remaining_major_labels, remaining_rows.index):
            family_df.loc[int(idx), "role"] = label

    return family_df


def build_peak_families(
    peak_df: pd.DataFrame,
    edge_margin_nm: float,
    main_family_count: int,
) -> tuple[pd.DataFrame, dict[str, object]]:
    family_rows: list[dict[str, object]] = []
    used_peak_ids: set[int] = set()

    left_edge = peak_df.loc[peak_df["is_left_edge_candidate"]].sort_values("power_smooth_uW", ascending=False)
    right_edge = peak_df.loc[peak_df["is_right_edge_candidate"]].sort_values("power_smooth_uW", ascending=False)
    if not left_edge.empty and not right_edge.empty:
        left_row = left_edge.iloc[0]
        right_row = right_edge.iloc[0]
        if int(left_row["peak_id"]) != int(right_row["peak_id"]):
            used_peak_ids.update({int(left_row["peak_id"]), int(right_row["peak_id"])})
            family_rows.append(
                {
                    "family_id": 1,
                    "family_type": "wrapped_edge_family",
                    "representative_lambda_nm": float(right_row["lambda_nm"]),
                    "power_raw_uW": float(max(left_row["power_raw_uW"], right_row["power_raw_uW"])),
                    "power_smooth_uW": float(max(left_row["power_smooth_uW"], right_row["power_smooth_uW"])),
                    "member_peak_ids": json.dumps([int(left_row["peak_id"]), int(right_row["peak_id"])]),
                    "member_lambdas_nm": json.dumps(
                        [float(left_row["lambda_nm"]), float(right_row["lambda_nm"])]
                    ),
                    "edge_margin_nm": edge_margin_nm,
                }
            )

    for _, row in peak_df.sort_values("power_smooth_uW", ascending=False).iterrows():
        peak_id = int(row["peak_id"])
        if peak_id in used_peak_ids:
            continue
        family_rows.append(
            {
                "family_id": len(family_rows) + 1,
                "family_type": "single_peak_family",
                "representative_lambda_nm": float(row["lambda_nm"]),
                "power_raw_uW": float(row["power_raw_uW"]),
                "power_smooth_uW": float(row["power_smooth_uW"]),
                "member_peak_ids": json.dumps([peak_id]),
                "member_lambdas_nm": json.dumps([float(row["lambda_nm"])]),
                "edge_margin_nm": edge_margin_nm,
            }
        )

    family_df = pd.DataFrame(family_rows).sort_values(
        ["power_smooth_uW", "representative_lambda_nm"], ascending=[False, True]
    ).reset_index(drop=True)
    family_df["family_rank"] = np.arange(1, len(family_df) + 1)
    family_df = assign_family_roles(family_df, main_family_count=main_family_count)

    summary = {
        "edge_margin_nm": edge_margin_nm,
        "n_detected_peaks": int(len(peak_df)),
        "n_families": int(len(family_df)),
    }
    return family_df, summary


def plot_trace(
    df: pd.DataFrame,
    y_smooth: np.ndarray,
    peak_df: pd.DataFrame,
    family_df: pd.DataFrame,
    output_path: Path,
) -> None:
    x = df["Lambda_aligned"].to_numpy(dtype=float)
    y = df["Power_uW"].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    ax.plot(x, y, color="#9ca3af", lw=1.0, alpha=0.75, label="raw")
    ax.plot(x, y_smooth, color="#ea580c", lw=1.8, label="smooth")
    ax.scatter(
        peak_df["lambda_nm"],
        peak_df["power_smooth_uW"],
        color="#2563eb",
        s=42,
        zorder=3,
        label="detected peaks",
    )

    for _, row in peak_df.iterrows():
        ax.annotate(
            f"P{int(row['peak_id'])}",
            (float(row["lambda_nm"]), float(row["power_smooth_uW"])),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8,
            color="#1d4ed8",
        )

    role_colors = {
        "major_peak_1": "#dc2626",
        "major_peak_2": "#7c3aed",
        "crosstalk_candidate": "#059669",
        "other": "#374151",
    }
    for _, row in family_df.iterrows():
        role = str(row["role"])
        label_text = f"{role}: {row['representative_lambda_nm']:.6f} nm"
        ax.axvline(
            float(row["representative_lambda_nm"]),
            color=role_colors.get(role, "#374151"),
            lw=1.2,
            ls="--",
            alpha=0.85,
        )
        ax.text(
            float(row["representative_lambda_nm"]),
            float(ax.get_ylim()[1] * 0.94),
            label_text,
            rotation=90,
            va="top",
            ha="right",
            fontsize=8,
            color=role_colors.get(role, "#374151"),
            bbox={"boxstyle": "round,pad=0.15", "facecolor": "white", "edgecolor": "none", "alpha": 0.75},
        )

    ax.set_xlabel("Lambda_aligned (nm)")
    ax.set_ylabel("Power_uW")
    ax.set_title("Peak identification for symmetrized scan")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def print_summary(csv_path: Path, peak_df: pd.DataFrame, family_df: pd.DataFrame) -> None:
    print(f"input_csv={csv_path}")
    print(f"detected_peaks={len(peak_df)}")
    print(f"peak_families={len(family_df)}")
    for _, row in family_df.iterrows():
        role = row["role"]
        lambdas = json.loads(str(row["member_lambdas_nm"]))
        lambda_text = ", ".join(f"{value:.6f}" for value in lambdas)
        print(
            f"{role}: lambda={float(row['representative_lambda_nm']):.6f} nm | "
            f"power={float(row['power_raw_uW']):.3f} uW | members=[{lambda_text}] | "
            f"type={row['family_type']}"
        )


def main() -> None:
    args = parse_args()
    csv_path = args.input_csv.resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    output_dir = args.output_dir.resolve() if args.output_dir else csv_path.parent
    df = load_trace(csv_path)
    _, y_smooth, peak_records, edge_margin_nm = detect_peaks(df, args)
    peak_df = peak_records_to_frame(peak_records)
    family_df, summary = build_peak_families(
        peak_df=peak_df,
        edge_margin_nm=edge_margin_nm,
        main_family_count=args.main_family_count,
    )

    stem = csv_path.stem
    peak_csv = output_dir / f"{stem}_detected_peaks.csv"
    family_csv = output_dir / f"{stem}_selected_peak_families.csv"
    plot_path = output_dir / f"{stem}_peak_overview.png"
    summary_path = output_dir / f"{stem}_peak_summary.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    peak_df.to_csv(peak_csv, index=False, encoding="utf-8-sig")
    family_df.to_csv(family_csv, index=False, encoding="utf-8-sig")
    plot_trace(df=df, y_smooth=y_smooth, peak_df=peak_df, family_df=family_df, output_path=plot_path)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print_summary(csv_path, peak_df, family_df)
    print(f"detected_peaks_csv={peak_csv}")
    print(f"selected_families_csv={family_csv}")
    print(f"overview_plot={plot_path}")
    print(f"summary_json={summary_path}")


if __name__ == "__main__":
    main()
