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
from scipy.signal import find_peaks, savgol_filter

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
DEFAULT_REDUCTION_FRAC = 0.20


@dataclass
class PeakCandidate:
    label: str
    rank: int
    peak_id: int
    family_id: int | None
    family_type: str
    family_role: str
    member_peak_ids: list[int]
    current_index: int
    adjustment_mode: str = "auto"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Browse detected peaks by rank and optionally reduce one peak as a whole."
    )
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument(
        "--output-name",
        type=str,
        default=None,
        help="Custom output CSV filename. Accepts with or without .csv suffix.",
    )
    parser.add_argument("--candidate-rank", type=int, default=1)
    parser.add_argument("--reduction-frac", type=float, default=DEFAULT_REDUCTION_FRAC)
    parser.add_argument("--apply-reduction", action="store_true")
    for name, default in DEFAULT_DETECTION_PARAMS.items():
        parser.add_argument(f"--{name.replace('_', '-')}", type=type(default), default=default)
    return parser.parse_args()


def build_detection_namespace(
    *,
    input_csv: Path,
    output_dir: Path | None = None,
    **detection_overrides: float | int,
) -> argparse.Namespace:
    config = dict(DEFAULT_DETECTION_PARAMS)
    config.update(detection_overrides)
    return argparse.Namespace(input_csv=input_csv, output_dir=output_dir, **config)


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


def _build_peak_family_lookup(family_df: pd.DataFrame) -> dict[int, dict[str, object]]:
    lookup: dict[int, dict[str, object]] = {}
    for _, row in family_df.iterrows():
        member_peak_ids = [int(value) for value in json.loads(str(row["member_peak_ids"]))]
        family_info = {
            "family_id": int(row["family_id"]),
            "family_type": str(row["family_type"]),
            "family_role": str(row.get("role", "other")),
            "member_peak_ids": member_peak_ids,
        }
        for peak_id in member_peak_ids:
            lookup[peak_id] = family_info
    return lookup


def _candidate_from_peak_row(
    peak_row: pd.Series,
    family_lookup: dict[int, dict[str, object]],
    rank: int,
) -> PeakCandidate:
    peak_id = int(peak_row["peak_id"])
    family_info = family_lookup.get(
        peak_id,
        {
            "family_id": None,
            "family_type": "single_peak_family",
            "family_role": "other",
            "member_peak_ids": [peak_id],
        },
    )
    return PeakCandidate(
        label=f"peak_rank_{rank}",
        rank=rank,
        peak_id=peak_id,
        family_id=family_info["family_id"],
        family_type=str(family_info["family_type"]),
        family_role=str(family_info["family_role"]),
        member_peak_ids=list(family_info["member_peak_ids"]),
        current_index=int(peak_row["index"]),
        adjustment_mode="auto",
    )


def build_peak_candidates(peak_df: pd.DataFrame, family_df: pd.DataFrame) -> list[PeakCandidate]:
    family_lookup = _build_peak_family_lookup(family_df)
    ordered_peak_df = peak_df.sort_values(
        ["power_smooth_uW", "lambda_nm"],
        ascending=[False, True],
    ).reset_index(drop=True)
    candidates = [
        _candidate_from_peak_row(row, family_lookup, rank=idx)
        for idx, (_, row) in enumerate(ordered_peak_df.iterrows(), start=1)
    ]
    if not candidates:
        raise RuntimeError("No peak candidates were produced. Try lowering the detection thresholds.")
    return candidates


def _detect_ranked_candidates(
    x: np.ndarray,
    y: np.ndarray,
    detection_params: dict[str, int | float],
) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame, list[PeakCandidate], dict[str, object]]:
    df = pd.DataFrame({"Lambda_aligned": x, "Power_uW": y})
    args = argparse.Namespace(input_csv=Path("."), output_dir=None, **detection_params)
    _, y_smooth, peak_records, edge_margin_nm = detect_peaks(df, args)
    peak_df = peak_records_to_frame(peak_records)
    family_df, summary = build_peak_families(
        peak_df=peak_df,
        edge_margin_nm=edge_margin_nm,
        main_family_count=int(args.main_family_count),
    )
    candidates = build_peak_candidates(peak_df, family_df)
    return y_smooth, peak_df, family_df, candidates, summary


def candidate_labels(context: dict[str, object]) -> list[str]:
    return [candidate.label for candidate in context["candidates"]]


def get_candidate(context: dict[str, object], label: str) -> PeakCandidate:
    for candidate in context["candidates"]:
        if candidate.label == label:
            return candidate
    raise KeyError(f"Unknown candidate label: {label}")


def set_active_candidate(context: dict[str, object], label: str) -> PeakCandidate:
    candidate = get_candidate(context, label)
    context["active_label"] = candidate.label
    return candidate


def step_active_candidate(context: dict[str, object], step: int) -> PeakCandidate:
    labels = candidate_labels(context)
    current_index = labels.index(str(context["active_label"]))
    next_index = max(0, min(len(labels) - 1, current_index + int(step)))
    return set_active_candidate(context, labels[next_index])


def _pick_active_label(candidates: list[PeakCandidate], *, target_lambda_nm: float | None = None, target_rank: int | None = None) -> str:
    if target_lambda_nm is not None:
        best = min(candidates, key=lambda item: (abs(item.current_index - item.current_index), abs(item.rank - 1)))
        best = min(candidates, key=lambda item: abs(item.current_index - item.current_index))
        del best
        nearest = min(candidates, key=lambda item: abs(item.current_index))
        del nearest
        return min(candidates, key=lambda item: abs(target_lambda_nm - float(item.current_index))).label
    if target_rank is None:
        target_rank = 1
    target_rank = max(1, min(len(candidates), int(target_rank)))
    return candidates[target_rank - 1].label


def _pick_active_label_by_lambda(context: dict[str, object], candidates: list[PeakCandidate], target_lambda_nm: float | None) -> str:
    if target_lambda_nm is None:
        return candidates[0].label
    x = context["x"]
    return min(candidates, key=lambda item: abs(float(x[item.current_index]) - target_lambda_nm)).label


def _refresh_context_candidates(
    context: dict[str, object],
    *,
    target_lambda_nm: float | None = None,
    target_rank: int | None = None,
) -> None:
    y_smooth, peak_df, family_df, candidates, summary = _detect_ranked_candidates(
        x=context["x"],
        y=context["y_current"],
        detection_params=context["detection_params"],
    )
    context["y_smooth"] = y_smooth
    context["peak_df"] = peak_df
    context["family_df"] = family_df
    context["candidates"] = candidates
    context["summary"] = summary
    if target_lambda_nm is not None:
        context["active_label"] = _pick_active_label_by_lambda(context, candidates, target_lambda_nm)
    else:
        context["active_label"] = candidates[max(0, min(len(candidates) - 1, (target_rank or 1) - 1))].label


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
    df_original = load_trace(csv_path)
    x = df_original["Lambda_aligned"].to_numpy(dtype=float)
    y_original = df_original["Power_uW"].to_numpy(dtype=float)

    context = {
        "input_csv": csv_path,
        "output_dir": output_dir.resolve() if output_dir else csv_path.parent,
        "df_original": df_original,
        "x": x,
        "y_original": y_original.copy(),
        "y_current": y_original.copy(),
        "detection_params": {name: getattr(args, name) for name in DEFAULT_DETECTION_PARAMS},
        "action_history": [],
        "last_reduction": None,
    }
    _refresh_context_candidates(context, target_rank=1)
    return context


def candidate_to_record(
    candidate: PeakCandidate,
    x: np.ndarray,
    y_current: np.ndarray,
    y_smooth: np.ndarray,
    *,
    is_active: bool,
) -> dict[str, object]:
    idx = int(candidate.current_index)
    return {
        "label": candidate.label,
        "rank": candidate.rank,
        "display_name": f"第{candidate.rank}高峰",
        "peak_id": candidate.peak_id,
        "family_id": candidate.family_id,
        "family_type": candidate.family_type,
        "family_role": candidate.family_role,
        "member_peak_ids": json.dumps(candidate.member_peak_ids, ensure_ascii=False),
        "current_index": idx,
        "current_lambda_nm": float(x[idx]),
        "power_raw_uW": float(y_current[idx]),
        "power_smooth_uW": float(y_smooth[idx]),
        "adjustment_mode": candidate.adjustment_mode,
        "is_active": int(is_active),
    }


def selections_to_frame(context: dict[str, object]) -> pd.DataFrame:
    x = context["x"]
    y_current = context["y_current"]
    y_smooth = context["y_smooth"]
    active_label_value = str(context["active_label"])
    rows = [
        candidate_to_record(candidate, x, y_current, y_smooth, is_active=(candidate.label == active_label_value))
        for candidate in context["candidates"]
    ]
    return pd.DataFrame(rows)


def build_marked_trace(context: dict[str, object]) -> pd.DataFrame:
    df_marked = context["df_original"].copy()
    df_marked["Power_uW"] = context["y_current"]
    df_marked["Power_smooth_uW"] = context["y_smooth"]
    df_marked["selected_peak_rank"] = 0
    df_marked["selected_peak_label"] = ""
    df_marked["is_active_selected_peak"] = 0

    active_label_value = str(context["active_label"])
    for candidate in context["candidates"]:
        idx = int(candidate.current_index)
        df_marked.loc[idx, "selected_peak_rank"] = int(candidate.rank)
        df_marked.loc[idx, "selected_peak_label"] = candidate.label
        if candidate.label == active_label_value:
            df_marked.loc[idx, "is_active_selected_peak"] = 1
    return df_marked


def _locate_peak_window(
    context: dict[str, object],
    target_index: int,
) -> dict[str, float]:
    y_current = context["y_current"]
    y_smooth = context["y_smooth"]
    params = context["detection_params"]
    max_power = float(np.max(y_smooth))
    prominence = max(float(params["prominence_abs"]), float(params["prominence_frac"]) * max_power)
    min_height = max(float(params["height_abs"]), float(params["height_frac"]) * max_power)

    peaks, properties = find_peaks(
        y_smooth,
        prominence=prominence,
        height=min_height,
        distance=int(params["distance_points"]),
        width=float(params["min_width_points"]),
    )
    if len(peaks) == 0:
        raise RuntimeError("No peaks were found in the current trace. Try lowering the detection thresholds.")

    target_slot = int(np.argmin(np.abs(peaks - int(target_index))))
    peak_index = int(peaks[target_slot])
    return {
        "peak_index": peak_index,
        "left_base_index": int(properties["left_bases"][target_slot]),
        "right_base_index": int(properties["right_bases"][target_slot]),
        "original_peak_power_uW": float(y_current[peak_index]),
    }


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


def reduce_candidate_peak(
    context: dict[str, object],
    label: str,
    reduction_frac: float,
) -> dict[str, object]:
    candidate = get_candidate(context, label)
    target_lambda_nm = float(context["x"][candidate.current_index])
    peak_window = _locate_peak_window(context, candidate.current_index)
    y_new, stats = reduce_peak_segment(
        x=context["x"],
        y=context["y_current"],
        target_peak_index=int(peak_window["peak_index"]),
        left_base_index=int(peak_window["left_base_index"]),
        right_base_index=int(peak_window["right_base_index"]),
        reduction_frac=reduction_frac,
    )

    context["y_current"] = y_new
    reduction_report = {
        "target_label": candidate.label,
        "target_rank_before": int(candidate.rank),
        "target_lambda_nm": float(context["x"][peak_window["peak_index"]]),
        "reduction_frac": float(reduction_frac),
        "peak_index": int(peak_window["peak_index"]),
        "left_base_index": int(peak_window["left_base_index"]),
        "right_base_index": int(peak_window["right_base_index"]),
        **stats,
    }
    context["last_reduction"] = reduction_report
    context["action_history"].append(reduction_report)
    _refresh_context_candidates(context, target_lambda_nm=target_lambda_nm)
    get_candidate(context, str(context["active_label"])).adjustment_mode = f"reduce({reduction_frac * 100:.1f}%)"
    return reduction_report


def reset_all_reductions(context: dict[str, object]) -> None:
    context["y_current"] = context["y_original"].copy()
    context["action_history"] = []
    context["last_reduction"] = None
    _refresh_context_candidates(context, target_rank=1)


def draw_selection_axes(ax: plt.Axes, context: dict[str, object]) -> None:
    x = context["x"]
    y_current = context["y_current"]
    y_smooth = context["y_smooth"]
    peak_df = context["peak_df"]
    selection_df = selections_to_frame(context)

    ax.clear()
    ax.plot(x, y_current, color="#94a3b8", lw=1.0, alpha=0.9, label="current trace")
    ax.plot(x, y_smooth, color="#ea580c", lw=1.5, label="smoothed")
    ax.scatter(
        peak_df["lambda_nm"],
        peak_df["power_smooth_uW"],
        color="#2563eb",
        s=26,
        alpha=0.75,
        label="detected peaks",
        zorder=3,
    )

    active_rows = selection_df.loc[selection_df["is_active"] == 1]
    other_rows = selection_df.loc[selection_df["is_active"] == 0]
    if not other_rows.empty:
        ax.scatter(
            other_rows["current_lambda_nm"],
            other_rows["power_smooth_uW"],
            color="#059669",
            marker="D",
            s=48,
            alpha=0.85,
            label="other ranked peaks",
            zorder=4,
        )

    if not active_rows.empty:
        active_row = active_rows.iloc[0]
        ax.axvline(float(active_row["current_lambda_nm"]), color="#dc2626", lw=1.2, ls="--", alpha=0.9)
        ax.scatter(
            [float(active_row["current_lambda_nm"])],
            [float(active_row["power_smooth_uW"])],
            color="#dc2626",
            marker="o",
            s=96,
            label="active peak",
            zorder=5,
        )
        ax.annotate(
            f"Rank {int(active_row['rank'])}: {float(active_row['current_lambda_nm']):.6f} nm",
            (float(active_row["current_lambda_nm"]), float(active_row["power_smooth_uW"])),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8,
            color="#dc2626",
        )

    last_reduction = context.get("last_reduction")
    if last_reduction:
        left_idx = int(last_reduction["left_base_index"])
        right_idx = int(last_reduction["right_base_index"])
        ax.axvspan(x[left_idx], x[right_idx], color="#fde68a", alpha=0.22, label="last reduced window")

    ax.set_title("Ranked peak candidates")
    ax.set_xlabel("Lambda_aligned (nm)")
    ax.set_ylabel("Power_uW")
    ax.grid(alpha=0.2)

    handles, labels = ax.get_legend_handles_labels()
    deduped: dict[str, object] = {}
    for handle, label in zip(handles, labels):
        if label not in deduped:
            deduped[label] = handle
    ax.legend(deduped.values(), deduped.keys(), frameon=False, loc="best")


def _resolve_output_stem(input_csv: Path, output_name: str | None) -> str:
    if output_name is None or not output_name.strip():
        return f"{input_csv.stem}_selected_peak_reduced"
    file_name = Path(output_name.strip()).name
    if not file_name:
        raise ValueError("Output filename cannot be empty.")
    if file_name.lower().endswith(".csv"):
        file_name = file_name[:-4]
    if not file_name:
        raise ValueError("Output filename cannot be empty.")
    return file_name


def _build_summary_text(context: dict[str, object]) -> str:
    selection_df = selections_to_frame(context)
    active_rows = selection_df.loc[selection_df["is_active"] == 1]
    active_row = active_rows.iloc[0] if not active_rows.empty else selection_df.iloc[0]
    lines = [
        f"input_csv={context['input_csv']}",
        f"active_label={context['active_label']}",
        f"current_candidate_count={len(selection_df)}",
        "detection_params=" + json.dumps(context["detection_params"], ensure_ascii=False),
        (
            "active_peak: rank={rank} | lambda_nm={lam:.12f} | raw_uW={raw:.6f} | "
            "smooth_uW={smooth:.6f} | mode={mode}"
        ).format(
            rank=int(active_row["rank"]),
            lam=float(active_row["current_lambda_nm"]),
            raw=float(active_row["power_raw_uW"]),
            smooth=float(active_row["power_smooth_uW"]),
            mode=str(active_row["adjustment_mode"]),
        ),
    ]

    history = context.get("action_history", [])
    if history:
        lines.append("action_history:")
        for idx, item in enumerate(history, start=1):
            lines.append(
                (
                    "  {idx}. lambda_nm={lam:.12f} | reduction_frac={frac:.6f} | "
                    "old_uW={old:.6f} | new_uW={new:.6f} | modified_points={count}"
                ).format(
                    idx=idx,
                    lam=float(item["target_lambda_nm"]),
                    frac=float(item["reduction_frac"]),
                    old=float(item["old_peak_uW"]),
                    new=float(item["new_peak_uW"]),
                    count=int(item["modified_point_count"]),
                )
            )
    else:
        lines.append("action_history: []")

    return "\n".join(lines) + "\n"


def save_reduction_outputs(
    context: dict[str, object],
    output_dir: Path | None = None,
    *,
    output_name: str | None = None,
) -> dict[str, Path]:
    csv_path = context["input_csv"]
    resolved_output_dir = Path(output_dir).resolve() if output_dir else Path(context["output_dir"]).resolve()
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    stem = _resolve_output_stem(csv_path, output_name)
    df_modified = context["df_original"].copy()
    df_modified["Power_uW"] = context["y_current"]

    output_csv = resolved_output_dir / f"{stem}.csv"
    summary_txt = resolved_output_dir / f"{stem}.txt"
    plot_png = resolved_output_dir / f"{stem}.png"

    df_modified.to_csv(output_csv, index=False, encoding="utf-8-sig")
    summary_txt.write_text(_build_summary_text(context), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    draw_selection_axes(ax, context)
    fig.tight_layout()
    fig.savefig(plot_png, dpi=180)
    plt.close(fig)

    return {
        "output_csv": output_csv,
        "summary_txt": summary_txt,
        "plot_png": plot_png,
    }


def process_single_csv(
    input_csv: Path,
    output_dir: Path | None = None,
    *,
    output_name: str | None = None,
    candidate_rank: int = 1,
    reduction_frac: float = DEFAULT_REDUCTION_FRAC,
    apply_reduction: bool = False,
    **detection_overrides: float | int,
) -> dict[str, object]:
    context = load_detection_context(
        input_csv=input_csv,
        output_dir=output_dir,
        **detection_overrides,
    )
    labels = candidate_labels(context)
    selected_rank = max(1, min(len(labels), int(candidate_rank)))
    set_active_candidate(context, labels[selected_rank - 1])
    reduction_report = None
    if apply_reduction:
        reduction_report = reduce_candidate_peak(context, str(context["active_label"]), reduction_frac)
    outputs = save_reduction_outputs(context, output_dir=output_dir, output_name=output_name)
    return {
        "context": context,
        "selection_df": selections_to_frame(context),
        "reduction_report": reduction_report,
        **outputs,
    }


def main() -> None:
    args = parse_args()
    detection_kwargs = {name: getattr(args, name) for name in DEFAULT_DETECTION_PARAMS}
    result = process_single_csv(
        input_csv=args.input_csv,
        output_dir=args.output_dir,
        output_name=args.output_name,
        candidate_rank=args.candidate_rank,
        reduction_frac=args.reduction_frac,
        apply_reduction=args.apply_reduction,
        **detection_kwargs,
    )
    selection_df = result["selection_df"]
    active_row = selection_df.loc[selection_df["is_active"] == 1].iloc[0]
    print(f"input_csv={Path(args.input_csv).resolve()}")
    print(f"detected_candidate_count={len(selection_df)}")
    print(
        "active_peak: rank={rank} | lambda_nm={lam:.12f} | raw_uW={raw:.6f} | smooth_uW={smooth:.6f} | mode={mode}".format(
            rank=int(active_row["rank"]),
            lam=float(active_row["current_lambda_nm"]),
            raw=float(active_row["power_raw_uW"]),
            smooth=float(active_row["power_smooth_uW"]),
            mode=active_row["adjustment_mode"],
        )
    )
    if result["reduction_report"] is not None:
        reduction_report = result["reduction_report"]
        print(
            "reduced_peak: lambda_nm={lam:.12f} | old_uW={old:.6f} | new_uW={new:.6f} | modified_points={count}".format(
                lam=float(reduction_report["target_lambda_nm"]),
                old=float(reduction_report["old_peak_uW"]),
                new=float(reduction_report["new_peak_uW"]),
                count=int(reduction_report["modified_point_count"]),
            )
        )
    print(f"output_csv={result['output_csv']}")
    print(f"summary_txt={result['summary_txt']}")
    print(f"plot_png={result['plot_png']}")


if __name__ == "__main__":
    main()
