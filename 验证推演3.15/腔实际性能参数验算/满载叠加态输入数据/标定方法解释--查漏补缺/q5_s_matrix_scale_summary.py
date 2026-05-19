#!/usr/bin/env python3
"""Summarize the scale of diagonal and off-diagonal entries in S for Q5.

This script keeps thesis sources, raw data files, and existing workbooks
untouched. It reads the three calibration workbooks under the existing
"最终数据" folder and writes a compact Q5 summary table in the current folder.

Why this script exists
----------------------
Q5 asks for the missing scale information of the off-diagonal entries in the
calibration matrix S:

* How large are the detection-chain cross responses?
* Is S nearly diagonal, or does it contain many large off-axis terms?
* Is the correction mainly diagonal normalization, or does the full matrix
  matter in a visible way?

To answer that without dumping the full 9x9 matrix into the appendix, this
script reports a compact summary table.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from openpyxl import load_workbook


@dataclass
class SummaryBlock:
    diag_range_percent: list[float]
    offdiag_median_percent: float
    offdiag_max_percent: float
    column_offdiag_sum_range_percent: list[float]
    target_share_range_percent: list[float]


@dataclass
class RunBlock:
    run: str
    diag_range_percent: list[float]
    offdiag_median_percent: float
    offdiag_max_percent: float
    column_offdiag_sum_range_percent: list[float]
    target_share_range_percent: list[float]


def discover_run_dirs(data_root: Path) -> list[Path]:
    run_dirs = []
    for path in data_root.rglob("calib_matrix_with_uncertainty.xlsx"):
        if path.parent.name in {"1", "2", "3"} and (path.parent / "full9_matrix_with_uncertainty.xlsx").exists():
            run_dirs.append(path.parent)
    return sorted(run_dirs, key=lambda p: p.name)


def read_s_matrix(run_dir: Path) -> np.ndarray:
    workbook = run_dir / "calib_matrix_with_uncertainty.xlsx"
    wb = load_workbook(workbook, data_only=True, read_only=True)
    rows = list(wb["mean"].iter_rows(values_only=True))
    wb.close()
    return np.asarray([[float(v) for v in row[1:10]] for row in rows[1:10]], dtype=float)


def summarize_matrix(s_matrix: np.ndarray) -> SummaryBlock:
    diag = np.diag(s_matrix)
    off = s_matrix[~np.eye(s_matrix.shape[0], dtype=bool)]

    col_off_sums = []
    target_shares = []
    for col_idx in range(s_matrix.shape[1]):
        col = s_matrix[:, col_idx]
        diag_val = float(col[col_idx])
        off_sum = float(np.sum(col) - diag_val)
        col_off_sums.append(off_sum)
        target_shares.append(diag_val / float(np.sum(col)))

    return SummaryBlock(
        diag_range_percent=[100.0 * float(np.min(diag)), 100.0 * float(np.max(diag))],
        offdiag_median_percent=100.0 * float(np.median(off)),
        offdiag_max_percent=100.0 * float(np.max(off)),
        column_offdiag_sum_range_percent=[
            100.0 * float(np.min(col_off_sums)),
            100.0 * float(np.max(col_off_sums)),
        ],
        target_share_range_percent=[
            100.0 * float(np.min(target_shares)),
            100.0 * float(np.max(target_shares)),
        ],
    )


def build_markdown(payload: dict) -> str:
    main = payload["mean_matrix_summary"]
    pooled = payload["pooled_runs_summary"]

    lines: list[str] = []
    lines.append("# Q5: S 矩阵对角与非对角项量级摘要")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Data root: `{payload['data_root']}`")
    lines.append("")
    lines.append("## 建议放附录的主表")
    lines.append("")
    lines.append("口径：先对 3 次独立标定的 `S` 矩阵逐元素取平均，再对该平均矩阵做摘要。")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---:|")
    lines.append(
        f"| 对角元范围 `$S_{{jj}}$` | `{main['diag_range_percent'][0]:.2f}% – {main['diag_range_percent'][1]:.2f}%` |"
    )
    lines.append(
        f"| 非对角元中位数 `$|S_{{ij}}|,\\ i\\neq j$` | `{main['offdiag_median_percent']:.4f}%` |"
    )
    lines.append(
        f"| 最大非对角元 `$\\max |S_{{ij}}|,\\ i\\neq j$` | `{main['offdiag_max_percent']:.4f}%` |"
    )
    lines.append(
        f"| 每列非对角元总和 `$\\sum_{{i\\neq j}} S_{{ij}}$` | `{main['column_offdiag_sum_range_percent'][0]:.4f}% – {main['column_offdiag_sum_range_percent'][1]:.4f}%` |"
    )
    lines.append(
        f"| 各列目标通道占总响应比例 `$S_{{jj}} / \\sum_i S_{{ij}}$` | `{main['target_share_range_percent'][0]:.2f}% – {main['target_share_range_percent'][1]:.2f}%` |"
    )
    lines.append("")
    lines.append("## 更保守的单次标定最宽范围")
    lines.append("")
    lines.append("口径：不先平均，直接把 3 次独立标定全部合并后统计，可作为更保守的备注。")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|---|---:|")
    lines.append(
        f"| 对角元范围 `$S_{{jj}}$` | `{pooled['diag_range_percent'][0]:.2f}% – {pooled['diag_range_percent'][1]:.2f}%` |"
    )
    lines.append(
        f"| 非对角元中位数 `$|S_{{ij}}|,\\ i\\neq j$` | `{pooled['offdiag_median_percent']:.4f}%` |"
    )
    lines.append(
        f"| 最大非对角元 `$\\max |S_{{ij}}|,\\ i\\neq j$` | `{pooled['offdiag_max_percent']:.4f}%` |"
    )
    lines.append(
        f"| 每列非对角元总和 `$\\sum_{{i\\neq j}} S_{{ij}}$` | `{pooled['column_offdiag_sum_range_percent'][0]:.4f}% – {pooled['column_offdiag_sum_range_percent'][1]:.4f}%` |"
    )
    lines.append(
        f"| 各列目标通道占总响应比例 `$S_{{jj}} / \\sum_i S_{{ij}}$` | `{pooled['target_share_range_percent'][0]:.2f}% – {pooled['target_share_range_percent'][1]:.2f}%` |"
    )
    lines.append("")
    lines.append("## 建议配套文字")
    lines.append("")
    lines.append(
        "可见，响应矩阵 $\\mathbf{S}$ 整体保持明显的对角占优：非对角元的典型量级仅为 "
        f"`{main['offdiag_median_percent']:.4f}%`，最大非对角元约为 `{main['offdiag_max_percent']:.4f}%`，"
        "各列非对角项总和不超过 "
        f"`{main['column_offdiag_sum_range_percent'][1]:.4f}%`；"
        "因此正文采用完整矩阵反演并非针对“大量离轴元素”的病态校正，而是为了去除检测链路中虽小但非零的通道间响应差异。"
    )
    lines.append("")
    lines.append("## 附：逐次独立标定摘要")
    lines.append("")
    for run in payload["runs"]:
        lines.append(
            f"- Run {run['run']}: "
            f"`Sjj={run['diag_range_percent'][0]:.2f}%–{run['diag_range_percent'][1]:.2f}%`, "
            f"非对角元中位数 `{run['offdiag_median_percent']:.4f}%`, "
            f"最大非对角元 `{run['offdiag_max_percent']:.4f}%`, "
            f"列非对角和 `{run['column_offdiag_sum_range_percent'][0]:.4f}%–{run['column_offdiag_sum_range_percent'][1]:.4f}%`, "
            f"目标通道占比 `{run['target_share_range_percent'][0]:.2f}%–{run['target_share_range_percent'][1]:.2f}%`。"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    output_dir = Path(__file__).resolve().parent
    data_root = output_dir.parent / "最终数据"
    run_dirs = discover_run_dirs(data_root)
    if len(run_dirs) != 3:
        raise RuntimeError(f"Expected 3 run directories under {data_root}, found: {run_dirs}")

    run_matrices = [read_s_matrix(run_dir) for run_dir in run_dirs]
    mean_matrix = np.mean(run_matrices, axis=0)

    run_blocks = [
        RunBlock(run=run_dir.name, **asdict(summarize_matrix(s_matrix)))
        for run_dir, s_matrix in zip(run_dirs, run_matrices)
    ]

    pooled_entries = np.stack(run_matrices, axis=0)
    pooled_diag = np.concatenate([np.diag(s_matrix) for s_matrix in run_matrices])
    pooled_off = np.concatenate([s_matrix[~np.eye(9, dtype=bool)] for s_matrix in run_matrices])
    pooled_col_off_sums = []
    pooled_target_shares = []
    for s_matrix in run_matrices:
        for col_idx in range(s_matrix.shape[1]):
            col = s_matrix[:, col_idx]
            diag_val = float(col[col_idx])
            pooled_col_off_sums.append(float(np.sum(col) - diag_val))
            pooled_target_shares.append(diag_val / float(np.sum(col)))

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data_root": str(data_root),
        "mean_matrix_summary": asdict(summarize_matrix(mean_matrix)),
        "pooled_runs_summary": asdict(
            SummaryBlock(
                diag_range_percent=[100.0 * float(np.min(pooled_diag)), 100.0 * float(np.max(pooled_diag))],
                offdiag_median_percent=100.0 * float(np.median(pooled_off)),
                offdiag_max_percent=100.0 * float(np.max(pooled_off)),
                column_offdiag_sum_range_percent=[
                    100.0 * float(np.min(pooled_col_off_sums)),
                    100.0 * float(np.max(pooled_col_off_sums)),
                ],
                target_share_range_percent=[
                    100.0 * float(np.min(pooled_target_shares)),
                    100.0 * float(np.max(pooled_target_shares)),
                ],
            )
        ),
        "runs": [asdict(run_block) for run_block in run_blocks],
    }

    json_path = output_dir / "q5_s_matrix_scale_summary.json"
    md_path = output_dir / "Q5_S矩阵量级摘要.md"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(payload), encoding="utf-8")

    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")


if __name__ == "__main__":
    main()
