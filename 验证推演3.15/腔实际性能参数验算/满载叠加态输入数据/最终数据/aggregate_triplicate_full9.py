#!/usr/bin/env python3
"""Aggregate triplicate 9D de-embedded FP matrices with error bars.

Input per run directory (default: 1,2,3):
  - full9_matrix_with_uncertainty.xlsx
  - calib_matrix_with_uncertainty.xlsx

Main outputs (written in current directory by default):
  - triplicate_full9_aggregate.xlsx
  - triplicate_full9_stats.txt

What this script produces:
1) De-embedded 9D full-load matrix (per run + merged) with error bars.
2) Percentage-form 9D matrix (column-normalized by I_total) with error bars.
3) ER_sum / ER_max merged across 3 runs (mean + error bars).
4) Additional QC and statistics in a standalone txt report.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

LOCK_RE = re.compile(r"lock\s*=\s*(\d+)", re.IGNORECASE)
CH_RE = re.compile(r"ch\s*=\s*(\d+)", re.IGNORECASE)


def normalize_run_name(raw: str) -> str:
    name = str(raw).strip()
    name = re.sub(r"\s+", "", name)
    name = re.sub(r"[-_]+$", "", name)
    return name


@dataclass
class MatrixAxes:
    channels: list[int]
    locks: list[int]


@dataclass
class MatrixBundle:
    axes: MatrixAxes
    mean: np.ndarray
    std: np.ndarray
    ci95: np.ndarray


@dataclass
class RunData:
    run_name: str
    bundle: MatrixBundle
    calib_mean: np.ndarray
    pct_mean: np.ndarray
    pct_std: np.ndarray
    pct_ci95: np.ndarray
    er_sum_db: dict[int, float]
    er_max_db: dict[int, float]
    signal_share: dict[int, float]
    calib_cond: float


def parse_float(v) -> float:
    if v is None:
        return float("nan")
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s in {"", "NaN", "nan"}:
        return float("nan")
    if s == "Inf":
        return float("inf")
    if s == "-Inf":
        return float("-inf")
    return float(s)


def parse_matrix_sheet(path: Path, sheet_name: str) -> tuple[MatrixAxes, np.ndarray]:
    wb = load_workbook(path, data_only=True, read_only=True)
    if sheet_name not in wb.sheetnames:
        wb.close()
        raise KeyError(f"{path.name} missing sheet: {sheet_name}")

    ws = wb[sheet_name]
    locks: list[int] = []
    for c in range(2, ws.max_column + 1):
        hv = ws.cell(1, c).value
        if hv is None:
            continue
        m = LOCK_RE.search(str(hv))
        if m:
            locks.append(int(m.group(1)))

    channels: list[int] = []
    rows: list[list[float]] = []
    for r in range(2, ws.max_row + 1):
        lv = ws.cell(r, 1).value
        if lv is None:
            continue
        m = CH_RE.search(str(lv))
        if not m:
            continue
        ch = int(m.group(1))
        channels.append(ch)
        row = [parse_float(ws.cell(r, c).value) for c in range(2, 2 + len(locks))]
        rows.append(row)

    wb.close()

    if not channels or not locks:
        raise ValueError(f"{path.name}:{sheet_name} has no valid matrix data.")

    axes = MatrixAxes(channels=channels, locks=locks)
    return axes, np.asarray(rows, dtype=float)


def read_full9_bundle(run_dir: Path) -> MatrixBundle:
    path = run_dir / "full9_matrix_with_uncertainty.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    axes_mean, mean = parse_matrix_sheet(path, "mean")
    axes_std, std = parse_matrix_sheet(path, "std")
    axes_ci95, ci95 = parse_matrix_sheet(path, "ci95")

    if axes_mean != axes_std or axes_mean != axes_ci95:
        raise ValueError(f"Axis mismatch in {path.name}")

    return MatrixBundle(axes=axes_mean, mean=mean, std=std, ci95=ci95)


def read_calib_mean(run_dir: Path) -> np.ndarray:
    path = run_dir / "calib_matrix_with_uncertainty.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    _, mean = parse_matrix_sheet(path, "mean")
    return mean


def safe_db10(num: float, den: float) -> float:
    if not math.isfinite(num) or not math.isfinite(den) or num <= 0 or den <= 0:
        return float("nan")
    return 10.0 * math.log10(num / den)


def compute_er_metrics(mean_matrix: np.ndarray, axes: MatrixAxes) -> tuple[dict[int, float], dict[int, float], dict[int, float]]:
    ch_to_row = {ch: i for i, ch in enumerate(axes.channels)}
    lock_to_col = {lk: j for j, lk in enumerate(axes.locks)}

    er_sum_db: dict[int, float] = {}
    er_max_db: dict[int, float] = {}
    signal_share: dict[int, float] = {}

    for lk in axes.locks:
        if lk not in ch_to_row:
            continue
        col = lock_to_col[lk]
        sig_row = ch_to_row[lk]
        col_vec = np.clip(mean_matrix[:, col], 0.0, None)
        signal = float(col_vec[sig_row])
        leak = np.delete(col_vec, sig_row)
        leak_sum = float(np.sum(leak)) if leak.size else float("nan")
        leak_max = float(np.max(leak)) if leak.size else float("nan")
        total = float(np.sum(col_vec))

        er_sum_db[lk] = safe_db10(signal, leak_sum)
        er_max_db[lk] = safe_db10(signal, leak_max)
        signal_share[lk] = signal / total if total > 0 else float("nan")

    return er_sum_db, er_max_db, signal_share


def pct_matrix_with_mc(mean: np.ndarray, std: np.ndarray, mc_samples: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    sample = rng.normal(loc=mean, scale=std, size=(mc_samples, *mean.shape))
    sample = np.clip(sample, 0.0, None)

    col_sums = np.sum(sample, axis=1, keepdims=True)  # (mc,1,locks)
    pct = np.divide(sample, col_sums, out=np.zeros_like(sample), where=col_sums > 0)

    pct_mean = np.mean(pct, axis=0)
    pct_std = np.std(pct, axis=0, ddof=1)
    pct_ci95 = 1.96 * pct_std
    return pct_mean, pct_std, pct_ci95


def validate_axes(run_data: list[RunData]) -> MatrixAxes:
    axes0 = run_data[0].bundle.axes
    for rd in run_data[1:]:
        if rd.bundle.axes != axes0:
            raise ValueError(f"Axis mismatch: run {rd.run_name}")
    return axes0


def clean_cell(v):
    if isinstance(v, float):
        if math.isnan(v):
            return "NaN"
        if math.isinf(v):
            return "Inf" if v > 0 else "-Inf"
    return v


def write_sheet(ws, headers: list[str], rows: Iterable[Iterable[object]]) -> None:
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill(fill_type="solid", start_color="D9E1F2", end_color="D9E1F2")
        c.alignment = Alignment(horizontal="center", vertical="center")
    ws.freeze_panes = "A2"

    for r in rows:
        ws.append([clean_cell(v) for v in r])

    for col in ws.columns:
        col_letter = col[0].column_letter
        width = 10
        for cell in col:
            if cell.value is None:
                continue
            width = max(width, len(str(cell.value)) + 2)
        ws.column_dimensions[col_letter].width = min(width, 42)


def matrix_rows(channels: list[int], mat: np.ndarray, scale: float = 1.0, ndigits: int = 6) -> list[list[object]]:
    rows: list[list[object]] = []
    for i, ch in enumerate(channels):
        row = [f"ch={ch}"]
        for v in mat[i, :]:
            vv = float(v) * scale
            row.append(round(vv, ndigits) if math.isfinite(vv) else vv)
        rows.append(row)
    return rows


def matrix_pm_rows(channels: list[int], mean: np.ndarray, err: np.ndarray, scale: float = 1.0, ndigits: int = 4, suffix: str = "") -> list[list[object]]:
    rows: list[list[object]] = []
    for i, ch in enumerate(channels):
        row = [f"ch={ch}"]
        for j in range(mean.shape[1]):
            mu = float(mean[i, j]) * scale
            er = float(err[i, j]) * scale
            if math.isfinite(mu) and math.isfinite(er):
                row.append(f"{mu:.{ndigits}f} +/- {er:.{ndigits}f}{suffix}")
            else:
                row.append("NaN")
        rows.append(row)
    return rows


def add_matrix_block(
    wb: Workbook,
    sheet_name: str,
    channels: list[int],
    locks: list[int],
    mean: np.ndarray,
    err95: np.ndarray,
    unit_label: str,
    scale: float,
    pm_suffix: str,
) -> None:
    ws = wb.create_sheet(sheet_name)
    lock_headers = [f"lock={lk}" for lk in locks]

    ws.append([f"{sheet_name} | mean ({unit_label})"] + lock_headers)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in matrix_rows(channels, mean, scale=scale, ndigits=6):
        ws.append(r)

    ws.append([])
    head2 = ws.max_row + 1
    ws.append([f"{sheet_name} | errorbar(95%CI) ({unit_label})"] + lock_headers)
    for c in ws[head2]:
        c.font = Font(bold=True)
    for r in matrix_rows(channels, err95, scale=scale, ndigits=6):
        ws.append(r)

    ws.append([])
    head3 = ws.max_row + 1
    ws.append([f"{sheet_name} | mean ± errorbar ({unit_label})"] + lock_headers)
    for c in ws[head3]:
        c.font = Font(bold=True)
    for r in matrix_pm_rows(channels, mean, err95, scale=scale, ndigits=4, suffix=pm_suffix):
        ws.append(r)

    for col in ws.columns:
        col_letter = col[0].column_letter
        width = 10
        for cell in col:
            if cell.value is None:
                continue
            width = max(width, len(str(cell.value)) + 2)
        ws.column_dimensions[col_letter].width = min(width, 42)

    ws.freeze_panes = "B2"


def agg_mean_std_sem_ci(values: list[float]) -> tuple[float, float, float, float]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return (float("nan"),) * 4
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
    sem = std / math.sqrt(arr.size) if arr.size > 0 else float("nan")
    ci95 = 1.96 * sem if math.isfinite(sem) else float("nan")
    return mean, std, sem, ci95


def build_outputs(run_data: list[RunData], output_xlsx: Path, output_txt: Path) -> None:
    axes = validate_axes(run_data)
    channels = axes.channels
    locks = axes.locks

    stack_mean = np.stack([rd.bundle.mean for rd in run_data], axis=0)
    combined_mean = np.mean(stack_mean, axis=0)
    combined_std = np.std(stack_mean, axis=0, ddof=1)
    combined_sem = combined_std / math.sqrt(stack_mean.shape[0])
    combined_ci95 = 1.96 * combined_sem

    stack_pct = np.stack([rd.pct_mean for rd in run_data], axis=0)
    combined_pct_mean = np.mean(stack_pct, axis=0)
    combined_pct_std = np.std(stack_pct, axis=0, ddof=1)
    combined_pct_sem = combined_pct_std / math.sqrt(stack_pct.shape[0])
    combined_pct_ci95 = 1.96 * combined_pct_sem

    wb = Workbook()
    wb.remove(wb.active)

    # Per-run de-embedded matrix with error bars
    for rd in run_data:
        add_matrix_block(
            wb=wb,
            sheet_name=f"{rd.run_name}_deembedded_uW",
            channels=channels,
            locks=locks,
            mean=rd.bundle.mean,
            err95=1.96 * np.nan_to_num(rd.bundle.std, nan=0.0),
            unit_label="uW",
            scale=1e6,
            pm_suffix=" uW",
        )

    # Combined de-embedded matrix across 3 runs
    add_matrix_block(
        wb=wb,
        sheet_name="combined_deembedded_uW",
        channels=channels,
        locks=locks,
        mean=combined_mean,
        err95=combined_ci95,
        unit_label="uW",
        scale=1e6,
        pm_suffix=" uW",
    )

    # Per-run percentage matrices with error bars
    for rd in run_data:
        add_matrix_block(
            wb=wb,
            sheet_name=f"{rd.run_name}_percentage",
            channels=channels,
            locks=locks,
            mean=rd.pct_mean,
            err95=rd.pct_ci95,
            unit_label="%",
            scale=100.0,
            pm_suffix="%",
        )

    # Combined percentage across runs
    add_matrix_block(
        wb=wb,
        sheet_name="combined_percentage",
        channels=channels,
        locks=locks,
        mean=combined_pct_mean,
        err95=combined_pct_ci95,
        unit_label="%",
        scale=100.0,
        pm_suffix="%",
    )

    # ER summary by channel
    er_rows: list[list[object]] = []
    for lk in locks:
        er_sum_vals = [rd.er_sum_db.get(lk, float("nan")) for rd in run_data]
        er_max_vals = [rd.er_max_db.get(lk, float("nan")) for rd in run_data]
        sig_share_vals = [rd.signal_share.get(lk, float("nan")) for rd in run_data]

        er_sum_mean, er_sum_std, er_sum_sem, er_sum_ci95 = agg_mean_std_sem_ci(er_sum_vals)
        er_max_mean, er_max_std, er_max_sem, er_max_ci95 = agg_mean_std_sem_ci(er_max_vals)
        share_mean, share_std, share_sem, share_ci95 = agg_mean_std_sem_ci(sig_share_vals)

        row = [
            lk,
            *er_sum_vals,
            er_sum_mean,
            er_sum_std,
            er_sum_sem,
            er_sum_ci95,
            *er_max_vals,
            er_max_mean,
            er_max_std,
            er_max_sem,
            er_max_ci95,
            *(float(v) * 100.0 if math.isfinite(v) else v for v in sig_share_vals),
            share_mean * 100.0 if math.isfinite(share_mean) else share_mean,
            share_std * 100.0 if math.isfinite(share_std) else share_std,
            share_sem * 100.0 if math.isfinite(share_sem) else share_sem,
            share_ci95 * 100.0 if math.isfinite(share_ci95) else share_ci95,
        ]
        er_rows.append(row)

    er_headers = [
        "channel(lock=l)",
        "ER_sum_run1_dB",
        "ER_sum_run2_dB",
        "ER_sum_run3_dB",
        "ER_sum_mean_dB",
        "ER_sum_std_dB",
        "ER_sum_sem_dB",
        "ER_sum_errorbar95_dB",
        "ER_max_run1_dB",
        "ER_max_run2_dB",
        "ER_max_run3_dB",
        "ER_max_mean_dB",
        "ER_max_std_dB",
        "ER_max_sem_dB",
        "ER_max_errorbar95_dB",
        "SignalShare_run1_%",
        "SignalShare_run2_%",
        "SignalShare_run3_%",
        "SignalShare_mean_%",
        "SignalShare_std_%",
        "SignalShare_sem_%",
        "SignalShare_errorbar95_%",
    ]
    ws_er = wb.create_sheet("ER_summary")
    write_sheet(ws_er, er_headers, er_rows)

    # Overall ER stats
    all_er_sum = []
    all_er_max = []
    for rd in run_data:
        all_er_sum.extend([v for v in rd.er_sum_db.values() if math.isfinite(v)])
        all_er_max.extend([v for v in rd.er_max_db.values() if math.isfinite(v)])
    er_sum_mean, er_sum_std, er_sum_sem, er_sum_ci95 = agg_mean_std_sem_ci(all_er_sum)
    er_max_mean, er_max_std, er_max_sem, er_max_ci95 = agg_mean_std_sem_ci(all_er_max)

    ws_overall = wb.create_sheet("overall_stats")
    overall_rows = [
        ("runs_used", ",".join(rd.run_name for rd in run_data)),
        ("channels_count", len(locks)),
        ("ER_sum_all_mean_dB", er_sum_mean),
        ("ER_sum_all_std_dB", er_sum_std),
        ("ER_sum_all_sem_dB", er_sum_sem),
        ("ER_sum_all_errorbar95_dB", er_sum_ci95),
        ("ER_max_all_mean_dB", er_max_mean),
        ("ER_max_all_std_dB", er_max_std),
        ("ER_max_all_sem_dB", er_max_sem),
        ("ER_max_all_errorbar95_dB", er_max_ci95),
        ("combined_diag_share_mean_%", float(np.nanmean(np.diag(combined_pct_mean) * 100.0))),
        ("combined_diag_share_min_%", float(np.nanmin(np.diag(combined_pct_mean) * 100.0))),
        ("combined_diag_share_max_%", float(np.nanmax(np.diag(combined_pct_mean) * 100.0))),
    ]
    write_sheet(ws_overall, ["metric", "value"], overall_rows)

    # Metadata
    ws_meta = wb.create_sheet("meta")
    meta_rows = [
        ("generated_at", datetime.now().isoformat(timespec="seconds")),
        ("note_1", "errorbar = 95%CI half-width"),
        ("note_2", "combined errorbars are computed from run-to-run statistics across 3 independent runs"),
        ("matrix_unit", "uW in *_deembedded_uW sheets"),
        ("percentage_definition", "each lock column normalized by I_total=sum(ch0..ch8)"),
    ]
    for rd in run_data:
        meta_rows.append((f"cond_calib_S_run_{rd.run_name}", rd.calib_cond))
    write_sheet(ws_meta, ["key", "value"], meta_rows)

    wb.save(output_xlsx)

    # TXT report
    lines: list[str] = []
    lines.append("Triplicate Full9 De-embedded Aggregation Report")
    lines.append(f"Generated at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("Per-run quick stats:")
    for rd in run_data:
        er_sum_vals = np.array([v for v in rd.er_sum_db.values() if math.isfinite(v)], dtype=float)
        er_max_vals = np.array([v for v in rd.er_max_db.values() if math.isfinite(v)], dtype=float)
        diag_pct = np.diag(rd.pct_mean) * 100.0
        lines.append(
            f"- Run {rd.run_name}: cond(S)={rd.calib_cond:.4f}, "
            f"ER_sum mean={np.mean(er_sum_vals):.3f} dB, "
            f"ER_max mean={np.mean(er_max_vals):.3f} dB, "
            f"diag share mean={np.mean(diag_pct):.2f}%"
        )

    lines.append("")
    lines.append("Merged (3-run) ER summary by channel:")
    for row in er_rows:
        lk = int(row[0])
        er_sum_mean_ch = float(row[4])
        er_sum_err = float(row[7])
        er_max_mean_ch = float(row[11])
        er_max_err = float(row[14])
        share_mean_ch = float(row[18])
        share_err = float(row[21])
        lines.append(
            f"  l={lk}: ER_sum={er_sum_mean_ch:.3f} +/- {er_sum_err:.3f} dB, "
            f"ER_max={er_max_mean_ch:.3f} +/- {er_max_err:.3f} dB, "
            f"SignalShare={share_mean_ch:.2f} +/- {share_err:.2f}%"
        )

    lines.append("")
    lines.append("Merged overall stats (all channels x all runs):")
    lines.append(f"  ER_sum mean +/- errorbar95 = {er_sum_mean:.3f} +/- {er_sum_ci95:.3f} dB")
    lines.append(f"  ER_max mean +/- errorbar95 = {er_max_mean:.3f} +/- {er_max_ci95:.3f} dB")
    lines.append(
        f"  Combined diagonal share (percentage matrix): "
        f"mean={float(np.nanmean(np.diag(combined_pct_mean) * 100.0)):.2f}%, "
        f"range=[{float(np.nanmin(np.diag(combined_pct_mean) * 100.0)):.2f}%, "
        f"{float(np.nanmax(np.diag(combined_pct_mean) * 100.0)):.2f}%]"
    )

    lines.append("")
    lines.append("Output files:")
    lines.append(f"  - XLSX: {output_xlsx.name}")
    lines.append(f"  - TXT : {output_txt.name}")
    output_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect_run_data(base_dir: Path, runs: list[str], pct_mc_samples: int, seed: int) -> list[RunData]:
    out: list[RunData] = []
    for idx, run_name in enumerate(runs):
        normalized_run_name = normalize_run_name(run_name)
        run_dir = base_dir / normalized_run_name
        if not run_dir.exists():
            available = ", ".join(sorted([p.name for p in base_dir.iterdir() if p.is_dir()]))
            raise FileNotFoundError(
                f"Missing run directory: {run_dir} (input run='{run_name}'). "
                f"Base dir: {base_dir.resolve()}. Available dirs: [{available}]"
            )

        bundle = read_full9_bundle(run_dir)
        calib_mean = read_calib_mean(run_dir)
        calib_cond = float(np.linalg.cond(calib_mean))

        pct_mean, pct_std, pct_ci95 = pct_matrix_with_mc(
            mean=bundle.mean,
            std=np.nan_to_num(bundle.std, nan=0.0),
            mc_samples=pct_mc_samples,
            seed=seed + idx,
        )
        er_sum_db, er_max_db, signal_share = compute_er_metrics(bundle.mean, bundle.axes)

        out.append(
            RunData(
                run_name=normalized_run_name,
                bundle=bundle,
                calib_mean=calib_mean,
                pct_mean=pct_mean,
                pct_std=pct_std,
                pct_ci95=pct_ci95,
                er_sum_db=er_sum_db,
                er_max_db=er_max_db,
                signal_share=signal_share,
                calib_cond=calib_cond,
            )
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate triplicate full9 de-embedded matrices, percentage matrices, and ER metrics."
    )
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
        "--pct-mc-samples",
        type=int,
        default=5000,
        help="Monte Carlo samples for percentage-matrix uncertainty (default: 5000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260314,
        help="Random seed (default: 20260314).",
    )
    parser.add_argument(
        "--output-xlsx",
        type=Path,
        default=Path(__file__).resolve().parent / "triplicate_full9_aggregate.xlsx",
        help="Output workbook path (default: script directory).",
    )
    parser.add_argument(
        "--output-txt",
        type=Path,
        default=Path(__file__).resolve().parent / "triplicate_full9_stats.txt",
        help="Output txt report path (default: script directory).",
    )
    args = parser.parse_args()

    run_data = collect_run_data(
        base_dir=args.base_dir,
        runs=args.runs,
        pct_mc_samples=args.pct_mc_samples,
        seed=args.seed,
    )
    build_outputs(run_data, args.output_xlsx, args.output_txt)

    print("Done.")
    print(f"XLSX: {args.output_xlsx.resolve()}")
    print(f"TXT : {args.output_txt.resolve()}")


if __name__ == "__main__":
    main()
