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

from identify_symmetrized_peaks import build_peak_families, detect_peaks, load_trace, peak_records_to_frame

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

TARGET_ROLES = (
    ("major_peak_1", "highest_peak"),
    ("major_peak_2", "second_highest_peak"),
)


@dataclass
class PeakSelection:
    role: str
    label: str
    family_id: int
    family_type: str
    member_peak_ids: list[int]
    auto_index: int
    current_index: int
    auto_lambda_nm: float
    adjustment_mode: str = "auto"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Identify the highest and second-highest peak families in a CSV and optionally fine-tune them."
    )
    parser.add_argument(
        "--input-csv",
        type=Path,
        required=True,
        help="Input CSV with Lambda_aligned and Power_uW columns.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to the CSV folder.",
    )
    parser.add_argument(
        "--highest-offset-points",
        type=int,
        default=0,
        help="Apply a signed point offset to the automatically detected highest peak after optional local refinement.",
    )
    parser.add_argument(
        "--second-offset-points",
        type=int,
        default=0,
        help="Apply a signed point offset to the automatically detected second-highest peak after optional local refinement.",
    )
    parser.add_argument(
        "--highest-refine-window",
        type=int,
        default=0,
        help="If positive, re-lock the highest peak to the local maximum within +/- this many points.",
    )
    parser.add_argument(
        "--second-refine-window",
        type=int,
        default=0,
        help="If positive, re-lock the second-highest peak to the local maximum within +/- this many points.",
    )
    for name, default in DEFAULT_DETECTION_PARAMS.items():
        option = f"--{name.replace('_', '-')}"
        parser.add_argument(option, type=type(default), default=default)
    return parser.parse_args()


def build_detection_namespace(
    *,
    input_csv: Path,
    output_dir: Path | None = None,
    **detection_overrides: float | int,
) -> argparse.Namespace:
    config = dict(DEFAULT_DETECTION_PARAMS)
    config.update(detection_overrides)
    return argparse.Namespace(
        input_csv=input_csv,
        output_dir=output_dir,
        **config,
    )


def _selection_from_family_row(
    role: str,
    label: str,
    family_row: pd.Series,
    peak_df: pd.DataFrame,
) -> PeakSelection:
    member_peak_ids = [int(value) for value in json.loads(str(family_row["member_peak_ids"]))]
    member_rows = peak_df.loc[peak_df["peak_id"].isin(member_peak_ids)].sort_values(
        ["power_smooth_uW", "lambda_nm"],
        ascending=[False, True],
    )
    if member_rows.empty:
        raise RuntimeError(f"Peak family {int(family_row['family_id'])} has no selectable member peaks.")
    member_row = member_rows.iloc[0]
    return PeakSelection(
        role=role,
        label=label,
        family_id=int(family_row["family_id"]),
        family_type=str(family_row["family_type"]),
        member_peak_ids=member_peak_ids,
        auto_index=int(member_row["index"]),
        current_index=int(member_row["index"]),
        auto_lambda_nm=float(member_row["lambda_nm"]),
    )


def build_initial_selections(peak_df: pd.DataFrame, family_df: pd.DataFrame) -> dict[str, PeakSelection]:
    selections: dict[str, PeakSelection] = {}
    for role, label in TARGET_ROLES:
        rows = family_df.loc[family_df["role"] == role]
        if rows.empty:
            raise RuntimeError(f"Could not find {role}. Try lowering the detection thresholds.")
        selections[label] = _selection_from_family_row(role, label, rows.iloc[0], peak_df)
    return selections


def load_detection_context(
    input_csv: Path,
    output_dir: Path | None = None,
    **detection_overrides: float | int,
) -> dict[str, object]:
    csv_path = Path(input_csv).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    args = build_detection_namespace(
        input_csv=csv_path,
        output_dir=output_dir,
        **detection_overrides,
    )
    df = load_trace(csv_path)
    x, y_smooth, peak_records, edge_margin_nm = detect_peaks(df, args)
    peak_df = peak_records_to_frame(peak_records)
    family_df, summary = build_peak_families(
        peak_df=peak_df,
        edge_margin_nm=edge_margin_nm,
        main_family_count=int(args.main_family_count),
    )
    selections = build_initial_selections(peak_df, family_df)

    return {
        "input_csv": csv_path,
        "output_dir": output_dir.resolve() if output_dir else csv_path.parent,
        "df": df,
        "x": x,
        "y": df["Power_uW"].to_numpy(dtype=float),
        "y_smooth": y_smooth,
        "peak_df": peak_df,
        "family_df": family_df,
        "selections": selections,
        "summary": summary,
        "detection_params": {name: getattr(args, name) for name in DEFAULT_DETECTION_PARAMS},
    }


def _clamp_index(index: int, size: int) -> int:
    return max(0, min(size - 1, int(index)))


def shift_selection(context: dict[str, object], label: str, offset_points: int) -> PeakSelection:
    selection = context["selections"][label]
    x = context["x"]
    selection.current_index = _clamp_index(selection.current_index + int(offset_points), len(x))
    selection.adjustment_mode = f"shift({int(offset_points):+d})"
    return selection


def refine_selection_to_local_max(
    context: dict[str, object],
    label: str,
    window_points: int,
    *,
    use_smoothed_trace: bool = True,
) -> PeakSelection:
    selection = context["selections"][label]
    if window_points < 1:
        return selection

    ref_trace = context["y_smooth"] if use_smoothed_trace else context["y"]
    current_index = int(selection.current_index)
    left = max(0, current_index - int(window_points))
    right = min(len(ref_trace) - 1, current_index + int(window_points))
    local_trace = ref_trace[left : right + 1]
    best_value = float(np.max(local_trace))
    candidate_offsets = np.flatnonzero(np.isclose(local_trace, best_value))
    best_offset = min(candidate_offsets.tolist(), key=lambda item: (abs((left + item) - current_index), item))

    selection.current_index = int(left + best_offset)
    basis = "smoothed" if use_smoothed_trace else "raw"
    selection.adjustment_mode = f"local_max_{basis}(+/-{int(window_points)})"
    return selection


def reset_selection(context: dict[str, object], label: str) -> PeakSelection:
    selection = context["selections"][label]
    selection.current_index = int(selection.auto_index)
    selection.adjustment_mode = "reset_to_auto"
    return selection


def selection_to_record(
    selection: PeakSelection,
    x: np.ndarray,
    y: np.ndarray,
    y_smooth: np.ndarray,
) -> dict[str, object]:
    idx = int(selection.current_index)
    auto_idx = int(selection.auto_index)
    return {
        "label": selection.label,
        "role": selection.role,
        "family_id": selection.family_id,
        "family_type": selection.family_type,
        "member_peak_ids": json.dumps(selection.member_peak_ids, ensure_ascii=False),
        "auto_index": auto_idx,
        "current_index": idx,
        "auto_lambda_nm": float(x[auto_idx]),
        "current_lambda_nm": float(x[idx]),
        "index_offset_points": idx - auto_idx,
        "lambda_offset_nm": float(x[idx] - x[auto_idx]),
        "power_raw_uW": float(y[idx]),
        "power_smooth_uW": float(y_smooth[idx]),
        "adjustment_mode": selection.adjustment_mode,
    }


def selections_to_frame(context: dict[str, object]) -> pd.DataFrame:
    x = context["x"]
    y = context["y"]
    y_smooth = context["y_smooth"]
    rows = [
        selection_to_record(context["selections"][label], x, y, y_smooth)
        for _, label in TARGET_ROLES
    ]
    return pd.DataFrame(rows)


def build_marked_trace(context: dict[str, object]) -> pd.DataFrame:
    df_marked = context["df"].copy()
    df_marked["Power_smooth_uW"] = context["y_smooth"]
    df_marked["selected_peak_role"] = ""
    df_marked["is_highest_peak"] = 0
    df_marked["is_second_highest_peak"] = 0

    highest_index = int(context["selections"]["highest_peak"].current_index)
    second_index = int(context["selections"]["second_highest_peak"].current_index)
    df_marked.loc[highest_index, "selected_peak_role"] = "highest_peak"
    df_marked.loc[second_index, "selected_peak_role"] = "second_highest_peak"
    df_marked.loc[highest_index, "is_highest_peak"] = 1
    df_marked.loc[second_index, "is_second_highest_peak"] = 1
    return df_marked


def draw_selection_axes(ax: plt.Axes, context: dict[str, object]) -> None:
    x = context["x"]
    y = context["y"]
    y_smooth = context["y_smooth"]
    peak_df = context["peak_df"]
    selection_df = selections_to_frame(context)

    ax.clear()
    ax.plot(x, y, color="#94a3b8", lw=1.0, alpha=0.8, label="raw")
    ax.plot(x, y_smooth, color="#ea580c", lw=1.5, label="smoothed")
    ax.scatter(
        peak_df["lambda_nm"],
        peak_df["power_smooth_uW"],
        color="#2563eb",
        s=28,
        alpha=0.85,
        label="detected peaks",
        zorder=3,
    )

    marker_styles = {
        "highest_peak": {"color": "#dc2626", "marker": "o", "text": "H"},
        "second_highest_peak": {"color": "#059669", "marker": "D", "text": "2"},
    }
    for _, row in selection_df.iterrows():
        style = marker_styles[str(row["label"])]
        ax.axvline(float(row["current_lambda_nm"]), color=style["color"], lw=1.1, ls="--", alpha=0.85)
        ax.scatter(
            [float(row["current_lambda_nm"])],
            [float(row["power_smooth_uW"])],
            color=style["color"],
            marker=style["marker"],
            s=76,
            zorder=4,
            label=str(row["label"]),
        )
        ax.annotate(
            f"{style['text']} {float(row['current_lambda_nm']):.6f} nm",
            (float(row["current_lambda_nm"]), float(row["power_smooth_uW"])),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8,
            color=style["color"],
        )

    ax.set_title("Top-2 peak selection")
    ax.set_xlabel("Lambda_aligned (nm)")
    ax.set_ylabel("Power_uW")
    ax.grid(alpha=0.2)

    handles, labels = ax.get_legend_handles_labels()
    deduped: dict[str, object] = {}
    for handle, label in zip(handles, labels):
        if label not in deduped:
            deduped[label] = handle
    ax.legend(deduped.values(), deduped.keys(), frameon=False, loc="best")


def save_selection_outputs(
    context: dict[str, object],
    output_dir: Path | None = None,
) -> dict[str, Path]:
    csv_path = context["input_csv"]
    resolved_output_dir = Path(output_dir).resolve() if output_dir else Path(context["output_dir"]).resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    stem = csv_path.stem
    selection_df = selections_to_frame(context)
    marked_df = build_marked_trace(context)

    selected_csv = resolved_output_dir / f"{stem}_top2_selected_peaks.csv"
    marked_csv = resolved_output_dir / f"{stem}_top2_peak_marked_trace.csv"
    summary_json = resolved_output_dir / f"{stem}_top2_selected_peaks_summary.json"
    plot_png = resolved_output_dir / f"{stem}_top2_selected_peaks.png"

    selection_df.to_csv(selected_csv, index=False, encoding="utf-8-sig")
    marked_df.to_csv(marked_csv, index=False, encoding="utf-8-sig")

    report = {
        "input_csv": str(csv_path),
        "detection_params": context["detection_params"],
        "selection_summary": context["summary"],
        "selected_peaks": selection_df.to_dict(orient="records"),
    }
    summary_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    draw_selection_axes(ax, context)
    fig.tight_layout()
    fig.savefig(plot_png, dpi=180)
    plt.close(fig)

    return {
        "selected_csv": selected_csv,
        "marked_trace_csv": marked_csv,
        "summary_json": summary_json,
        "plot_png": plot_png,
    }


def process_single_csv(
    input_csv: Path,
    output_dir: Path | None = None,
    *,
    highest_offset_points: int = 0,
    second_offset_points: int = 0,
    highest_refine_window: int = 0,
    second_refine_window: int = 0,
    **detection_overrides: float | int,
) -> dict[str, object]:
    context = load_detection_context(
        input_csv=input_csv,
        output_dir=output_dir,
        **detection_overrides,
    )

    if highest_refine_window > 0:
        refine_selection_to_local_max(context, "highest_peak", highest_refine_window)
    if second_refine_window > 0:
        refine_selection_to_local_max(context, "second_highest_peak", second_refine_window)

    if highest_offset_points != 0:
        shift_selection(context, "highest_peak", highest_offset_points)
    if second_offset_points != 0:
        shift_selection(context, "second_highest_peak", second_offset_points)

    outputs = save_selection_outputs(context, output_dir=output_dir)
    return {
        "context": context,
        "selection_df": selections_to_frame(context),
        **outputs,
    }


def main() -> None:
    args = parse_args()
    detection_kwargs = {name: getattr(args, name) for name in DEFAULT_DETECTION_PARAMS}
    result = process_single_csv(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        highest_offset_points=args.highest_offset_points,
        second_offset_points=args.second_offset_points,
        highest_refine_window=args.highest_refine_window,
        second_refine_window=args.second_refine_window,
        **detection_kwargs,
    )
    selection_df = result["selection_df"]
    print(f"input_csv={Path(args.input_csv).resolve()}")
    for _, row in selection_df.iterrows():
        print(
            f"{row['label']}: lambda_nm={float(row['current_lambda_nm']):.12f} | "
            f"raw_uW={float(row['power_raw_uW']):.6f} | smooth_uW={float(row['power_smooth_uW']):.6f} | "
            f"mode={row['adjustment_mode']}"
        )
    print(f"selected_csv={result['selected_csv']}")
    print(f"marked_trace_csv={result['marked_trace_csv']}")
    print(f"summary_json={result['summary_json']}")
    print(f"plot_png={result['plot_png']}")


if __name__ == "__main__":
    main()
