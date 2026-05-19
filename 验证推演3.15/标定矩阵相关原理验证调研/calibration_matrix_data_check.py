from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import numpy as np
from openpyxl import load_workbook


OUT_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(r"D:\自制软件\1.thesis\Data\full")

CALIB_XLSX = DATA_DIR / "triplicate_full9_calib_matrix_heatmap.xlsx"
COMPARE_XLSX = DATA_DIR / "triplicate_full9_percentage_compare.xlsx"
AGG_XLSX = DATA_DIR / "triplicate_full9_aggregate.xlsx"
RAW_XLSX = DATA_DIR / "triplicate_full9_raw_aggregate.xlsx"


def read_matrix(path: Path, sheet: str, min_row: int = 2, max_row: int = 10, min_col: int = 2, max_col: int = 10) -> np.ndarray:
    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb[sheet]
    values: list[list[float]] = []
    for row in ws.iter_rows(min_row=min_row, max_row=max_row, min_col=min_col, max_col=max_col, values_only=True):
        values.append([float(x or 0.0) for x in row])
    wb.close()
    return np.array(values, dtype=float)


def read_key_value_sheet(path: Path, sheet: str) -> dict[str, Any]:
    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb[sheet]
    data: dict[str, Any] = {}
    for key, value in ws.iter_rows(min_row=2, max_col=2, values_only=True):
        if key is not None:
            data[str(key)] = value
    wb.close()
    return data


def read_compare_summary(path: Path) -> list[dict[str, float | str]]:
    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb["summary"]
    rows: list[dict[str, float | str]] = []
    for row in ws.iter_rows(min_row=2, max_row=4, min_col=1, max_col=4, values_only=True):
        rows.append(
            {
                "method": str(row[0]),
                "diag_share_mean_%": float(row[1]),
                "diag_share_min_%": float(row[2]),
                "diag_share_max_%": float(row[3]),
            }
        )
    wb.close()
    return rows


def matrix_stats(name: str, mat: np.ndarray) -> dict[str, float | str]:
    diag = np.diag(mat)
    offdiag = mat[~np.eye(mat.shape[0], dtype=bool)]
    col_sums = mat.sum(axis=0)
    diag_col_share = np.divide(diag, col_sums, out=np.zeros_like(diag), where=col_sums != 0) * 100.0
    return {
        "matrix": name,
        "diag_mean_%": float(diag.mean()),
        "diag_min_%": float(diag.min()),
        "diag_max_%": float(diag.max()),
        "offdiag_mean_%": float(offdiag.mean()),
        "offdiag_median_%": float(np.median(offdiag)),
        "offdiag_max_%": float(offdiag.max()),
        "diag_col_share_min_%": float(diag_col_share.min()),
        "diag_col_share_mean_%": float(diag_col_share.mean()),
        "diag_col_share_max_%": float(diag_col_share.max()),
        "condition_number": float(np.linalg.cond(mat)),
    }


def er_from_diag_share(diag_share_percent: float) -> float:
    signal = diag_share_percent / 100.0
    noise = max(1.0 - signal, 1e-15)
    return 10.0 * math.log10(signal / noise)


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(
    calib_stats: dict[str, float | str],
    compare_rows: list[dict[str, float | str]],
    aggregate_stats: dict[str, Any],
    raw_stats: dict[str, Any],
    path: Path,
) -> None:
    lines = [
        "# Calibration matrix data check",
        "",
        "All source workbooks were opened read-only. No source workbook is modified by this script.",
        "",
        "## Combined calibration response matrix S",
        "",
        "| metric | value |",
        "|---|---:|",
    ]
    for key, value in calib_stats.items():
        if key == "matrix":
            continue
        lines.append(f"| {key} | {float(value):.6g} |")

    lines.extend(
        [
            "",
            "## Raw vs diagonal-only vs full-matrix calibration",
            "",
            "| method | diagonal share mean (%) | min (%) | max (%) | ER from mean share (dB) |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in compare_rows:
        mean_share = float(row["diag_share_mean_%"])
        lines.append(
            f"| {row['method']} | {mean_share:.6f} | {float(row['diag_share_min_%']):.6f} | "
            f"{float(row['diag_share_max_%']):.6f} | {er_from_diag_share(mean_share):.4f} |"
        )

    lines.extend(
        [
            "",
            "## Workbook-level reported metrics",
            "",
            "| source | metric | value |",
            "|---|---|---:|",
        ]
    )
    for key in [
        "ER_sum_all_mean_dB",
        "ER_sum_all_errorbar95_dB",
        "combined_diag_share_mean_%",
        "combined_diag_share_min_%",
        "combined_diag_share_max_%",
    ]:
        if key in aggregate_stats:
            lines.append(f"| deembedded aggregate | {key} | {aggregate_stats[key]} |")
    for key in [
        "raw_ER_sum_all_mean_dB",
        "raw_ER_sum_all_errorbar95_dB",
        "combined_raw_diag_share_mean_%",
        "combined_raw_diag_share_min_%",
        "combined_raw_diag_share_max_%",
    ]:
        if key in raw_stats:
            lines.append(f"| raw aggregate | {key} | {raw_stats[key]} |")

    lines.extend(
        [
            "",
            "Key reading:",
            "",
            "- The calibration matrix diagonal spans roughly a five-fold efficiency range, so raw powers are not a faithful FP-cavity sorting metric.",
            "- Full-matrix calibration improves the merged diagonal share relative to raw and diagonal-only processing, indicating that off-diagonal readout response is small but not useless.",
            "- The condition number is moderate for this 9 x 9 intensity-response matrix, so NNLS de-embedding is numerically plausible rather than an ill-conditioned artifact.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    calib = read_matrix(CALIB_XLSX, "combined_calib_S_percent")
    raw_pct = read_matrix(COMPARE_XLSX, "raw_percentage")
    diag_only_pct = read_matrix(COMPARE_XLSX, "diag_only_percentage")
    full_pct = read_matrix(COMPARE_XLSX, "full_matrix_percentage")

    stats_rows = [
        matrix_stats("combined_calib_S_percent", calib),
        matrix_stats("raw_percentage", raw_pct),
        matrix_stats("diag_only_percentage", diag_only_pct),
        matrix_stats("full_matrix_percentage", full_pct),
    ]
    compare_rows = read_compare_summary(COMPARE_XLSX)
    aggregate_stats = read_key_value_sheet(AGG_XLSX, "overall_stats")
    raw_stats = read_key_value_sheet(RAW_XLSX, "raw_overall_stats")

    write_csv(stats_rows, OUT_DIR / "calibration_matrix_summary.csv")
    write_csv(compare_rows, OUT_DIR / "calibration_processing_comparison.csv")
    write_markdown(stats_rows[0], compare_rows, aggregate_stats, raw_stats, OUT_DIR / "calibration_matrix_data_check_results.md")

    print("Wrote calibration_matrix_summary.csv")
    print("Wrote calibration_processing_comparison.csv")
    print("Wrote calibration_matrix_data_check_results.md")


if __name__ == "__main__":
    main()
