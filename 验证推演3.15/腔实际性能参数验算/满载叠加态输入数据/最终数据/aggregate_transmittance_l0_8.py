#!/usr/bin/env python3
"""Aggregate transmittance (l=0..8) across triplicate runs and export a txt report."""

from __future__ import annotations

import argparse
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from openpyxl import load_workbook

L_RE = re.compile(r"l\s*=\s*(-?\d+)", re.IGNORECASE)
NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def parse_float(value) -> float:
    if value is None:
        return float("nan")
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace("_x000d_", "")
    match = NUM_RE.search(text)
    if not match:
        return float("nan")
    try:
        return float(match.group(0))
    except ValueError:
        return float("nan")


def parse_l_index(value) -> int | None:
    if value is None:
        return None
    match = L_RE.search(str(value))
    if not match:
        return None
    return int(match.group(1))


def find_column(headers: list[str], keyword: str) -> int:
    for idx, header in enumerate(headers):
        if keyword in header:
            return idx
    raise ValueError(f"Cannot find column containing keyword: {keyword}")


def read_run_transmittance(run_dir: Path, xlsx_name: str) -> dict[int, float]:
    xlsx_path = run_dir / xlsx_name
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Missing file: {xlsx_path}")

    wb = load_workbook(xlsx_path, data_only=True, read_only=True)
    ws = wb[wb.sheetnames[0]]

    headers = [str(ws.cell(1, c).value or "").strip() for c in range(1, ws.max_column + 1)]
    l_col = 0
    before_col = find_column(headers, "入射fp腔前功率")
    after_col = find_column(headers, "透射fp腔后功率")

    result: dict[int, float] = {}
    for r in range(2, ws.max_row + 1):
        l_val = ws.cell(r, l_col + 1).value
        l_idx = parse_l_index(l_val)
        if l_idx is None:
            continue

        p_before = parse_float(ws.cell(r, before_col + 1).value)
        p_after = parse_float(ws.cell(r, after_col + 1).value)
        if not math.isfinite(p_before) or p_before <= 0 or not math.isfinite(p_after):
            result[l_idx] = float("nan")
            continue

        result[l_idx] = p_after / p_before

    wb.close()
    return result


def mean_std(values: list[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan"), float("nan")
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
    return mean, std


def build_report(
    base_dir: Path,
    runs: list[str],
    xlsx_name: str,
    output_txt: Path,
    l_min: int,
    l_max: int,
) -> None:
    run_trans: dict[str, dict[int, float]] = {}
    aggregate: dict[int, list[float]] = defaultdict(list)

    for run in runs:
        run_dir = base_dir / run
        trans = read_run_transmittance(run_dir, xlsx_name)
        run_trans[run] = trans
        for l_idx, t in trans.items():
            if l_min <= l_idx <= l_max and math.isfinite(t):
                aggregate[l_idx].append(t)

    lines: list[str] = []
    lines.append(f"Triplicate Transmittance Aggregation (l={l_min}..{l_max})")
    lines.append(f"Generated at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("Base directory: current script directory")
    lines.append(f"Input runs: {', '.join(runs)}")
    lines.append("Formula: transmittance = P_after / P_before")
    lines.append("")
    lines.append("Per-l summary (ratio and percentage):")

    for l_idx in range(l_min, l_max + 1):
        vals = [run_trans[run].get(l_idx, float('nan')) for run in runs]
        mean, std = mean_std(vals)

        run_parts: list[str] = []
        for run, value in zip(runs, vals):
            if math.isfinite(value):
                run_parts.append(f"run{run}={value:.6f} ({value * 100:.2f}%)")
            else:
                run_parts.append(f"run{run}=NaN")

        if math.isfinite(mean) and math.isfinite(std):
            summary = (
                f"mean={mean:.6f}, std={std:.6f}, "
                f"mean+std format: {mean * 100:.2f}% +/- {std * 100:.2f}%"
            )
        else:
            summary = "mean=NaN, std=NaN"

        lines.append(f"  l={l_idx}: {', '.join(run_parts)}; {summary}")

    all_vals = [value for l_idx in range(l_min, l_max + 1) for value in aggregate.get(l_idx, [])]
    overall_mean, overall_std = mean_std(all_vals)
    lines.append("")
    lines.append("Overall (all l and all runs):")
    if math.isfinite(overall_mean) and math.isfinite(overall_std):
        lines.append(
            f"  mean={overall_mean:.6f}, std={overall_std:.6f}, "
            f"mean+std format: {overall_mean * 100:.2f}% +/- {overall_std * 100:.2f}%"
        )
    else:
        lines.append("  mean=NaN, std=NaN")

    lines.append("")
    lines.append("Output file:")
    lines.append(f"  - TXT: {output_txt.name}")

    output_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate l=0..8 transmittance from triplicate xlsx files.")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Base directory containing run folders (default: script directory).",
    )
    parser.add_argument(
        "--runs",
        nargs="+",
        default=["1", "2", "3"],
        help="Run folder names (default: 1 2 3).",
    )
    parser.add_argument(
        "--xlsx-name",
        default="透射率.xlsx",
        help="Input xlsx filename inside each run folder (default: 透射率.xlsx).",
    )
    parser.add_argument("--l-min", type=int, default=0, help="Minimum l to include (default: 0).")
    parser.add_argument("--l-max", type=int, default=8, help="Maximum l to include (default: 8).")
    parser.add_argument(
        "--output-txt",
        type=Path,
        default=Path(__file__).resolve().parent / "triplicate_transmittance_l0_8_stats.txt",
        help="Output txt report path (default: script directory).",
    )
    args = parser.parse_args()

    build_report(
        base_dir=args.base_dir,
        runs=args.runs,
        xlsx_name=args.xlsx_name,
        output_txt=args.output_txt,
        l_min=args.l_min,
        l_max=args.l_max,
    )

    print("Done.")
    print(f"TXT : {args.output_txt.name}")


if __name__ == "__main__":
    main()
