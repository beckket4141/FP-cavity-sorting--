#!/usr/bin/env python3
"""Trace the provenance of the appendix repeatability claim:

    "平均 0.97%，最大 2.58%（l=5）"

This script only reads existing files. It does not modify any raw data.
It checks:
1. Where the exact numbers appear in the current workspace.
2. Whether the current usable data directory contains an independent
   single-mode repeatability dataset matching that wording.
3. Whether common candidate comparisons from current final workbooks can
   reproduce those numbers.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from openpyxl import load_workbook


@dataclass
class RunMeta:
    run: str
    source_matrix_xlsx: str
    source_trans_xlsx: str
    final_root_dir: str
    workbook_sheets: list[str]


@dataclass
class CandidateMetric:
    name: str
    mean_percent: float
    max_percent: float
    max_at_l: int
    details: list[float]


def load_diag_s(run_dir: Path) -> np.ndarray:
    wb = load_workbook(run_dir / "calib_matrix_with_uncertainty.xlsx", data_only=True, read_only=True)
    ws = wb["mean"]
    rows = list(ws.iter_rows(values_only=True))
    mat = np.asarray([[float(v) for v in row[1:10]] for row in rows[1:10]], dtype=float)
    wb.close()
    return np.diag(mat)


def load_meta(run_dir: Path, run: str) -> RunMeta:
    wb = load_workbook(run_dir / "calib_matrix_with_uncertainty.xlsx", data_only=True, read_only=True)
    sheets = list(wb.sheetnames)
    ws = wb["meta"]
    rows = list(ws.iter_rows(values_only=True))
    meta = {str(k): str(v) for k, v in rows[1:] if k is not None}
    wb.close()

    wb2 = load_workbook(run_dir / "final_matrix_summary.xlsx", data_only=True, read_only=True)
    ws2 = wb2["meta"]
    rows2 = list(ws2.iter_rows(values_only=True))
    meta2 = {str(k): str(v) for k, v in rows2[1:] if k is not None}
    wb2.close()

    return RunMeta(
        run=run,
        source_matrix_xlsx=meta.get("source_matrix_xlsx", ""),
        source_trans_xlsx=meta.get("source_trans_xlsx", ""),
        final_root_dir=meta2.get("root_dir", ""),
        workbook_sheets=sheets,
    )


def generation_summary_diag_target_vs_mean(csv_path: Path) -> CandidateMetric:
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        for row in rd:
            if row["matrix_type"] == "calib" and row["folder_l"] == row["channel"]:
                l = int(row["folder_l"])
                target_uW = float(row["target_uW"])
                mean_uW = float(row["mean_W"]) * 1e6
                rel = 0.0 if target_uW == mean_uW == 0 else abs(mean_uW - target_uW) / (target_uW if target_uW != 0 else mean_uW) * 100.0
                rows.append((l, rel))

    vals = [v for _, v in rows]
    max_l, max_v = max(rows, key=lambda x: x[1])
    return CandidateMetric(
        name="run2 generation_summary diagonal target_uW vs mean_uW",
        mean_percent=float(np.mean(vals)),
        max_percent=float(max_v),
        max_at_l=int(max_l),
        details=[float(v) for _, v in rows],
    )


def run_to_mean_deviation(diag_s: np.ndarray) -> CandidateMetric:
    mean_diag = np.mean(diag_s, axis=0)
    rel = np.abs(diag_s - mean_diag[None, :]) / mean_diag[None, :] * 100.0
    idx = np.unravel_index(np.argmax(rel), rel.shape)
    return CandidateMetric(
        name="27 entries: each run Sjj vs 3-run mean Sjj",
        mean_percent=float(np.mean(rel)),
        max_percent=float(rel[idx]),
        max_at_l=int(idx[1]),
        details=[float(x) for x in np.max(rel, axis=0)],
    )


def pairwise_run_deviation(diag_s: np.ndarray) -> CandidateMetric:
    pairs = [(0, 1), (0, 2), (1, 2)]
    rels = []
    for a, b in pairs:
        rels.append(np.abs(diag_s[a] - diag_s[b]) / ((diag_s[a] + diag_s[b]) / 2.0) * 100.0)
    arr = np.asarray(rels)
    idx = np.unravel_index(np.argmax(arr), arr.shape)
    return CandidateMetric(
        name="27 pairwise entries: Sjj(run_a) vs Sjj(run_b)",
        mean_percent=float(np.mean(arr)),
        max_percent=float(arr[idx]),
        max_at_l=int(idx[1]),
        details=[float(x) for x in np.max(arr, axis=0)],
    )


def search_exact_occurrences(base_dir: Path) -> list[str]:
    hits: list[str] = []
    for path in base_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".txt", ".py", ".tex", ".csv", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for token in ("0.97%", "2.58%", "0.97", "2.58"):
            if token in text:
                hits.append(str(path))
                break
    return sorted(set(hits))


def build_markdown(payload: dict) -> str:
    lines: list[str] = []
    lines.append("# 附录“0.97% / 2.58%”口径溯源检查")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Data root: `{payload['data_root']}`")
    lines.append("")
    lines.append("## 先说结论")
    lines.append("")
    lines.append("1. 当前可用数据目录里，没有发现一份可以直接指认为“独立单模效率复测”的独立原始表或独立工作簿。")
    lines.append("2. 这组数字目前只在附录正文和旧版 `测量方法.md` 里以结论形式出现，没有在当前最终数据目录中找到明确、可复算、可回溯的直接来源。")
    lines.append("3. 用当前三次 `calib_matrix_with_uncertainty.xlsx` 的对角元去做常见的几种比较，算不出“平均 0.97%”这句话；最接近的是 `l=5` 的某种 run-to-mean 偏差约 `2.62%`，和附录中的 `2.58% (l=5)` 很接近，但并不完全一致。")
    lines.append("4. 因此，在当前可用数据口径下，这句附录表述应视为“来源不可追溯”，高度疑似旧数据或旧处理链残留，不应继续当作已被当前最终数据严格支持的事实。")
    lines.append("")
    lines.append("## 1. 它现在出现在哪里")
    lines.append("")
    for p in payload["exact_occurrence_files"]:
        lines.append(f"- `{p}`")
    lines.append("")
    lines.append("可以看到，这组数字并没有在当前最终结果工作簿的显式统计输出里反复出现，而是主要停留在说明性文字中。")
    lines.append("")
    lines.append("## 2. 当前最终工作簿里有没有“独立复测表”")
    lines.append("")
    for meta in payload["run_meta"]:
        lines.append(f"- Run {meta['run']}:")
        lines.append(f"  source_matrix_xlsx = `{meta['source_matrix_xlsx']}`")
        lines.append(f"  source_trans_xlsx = `{meta['source_trans_xlsx']}`")
        lines.append(f"  final_matrix_summary.root_dir = `{meta['final_root_dir']}`")
        lines.append(f"  calib workbook sheets = `{', '.join(meta['workbook_sheets'])}`")
    lines.append("")
    lines.append("从现有 `calib_matrix_with_uncertainty.xlsx`、`final_matrix_summary.xlsx`、`透射率.xlsx` 的 sheet 和 meta 看，只能确认：")
    lines.append("")
    lines.append("- 当前最终结果来自若干旧原始目录整理后的矩阵汇总。")
    lines.append("- 这些工作簿里有标定矩阵、满载矩阵、透射率表。")
    lines.append("- 但没有一张 sheet 明确对应“另一时段、独立开展、仅测单通道耦合效率”的复测表。")
    lines.append("")
    lines.append("也就是说，附录里那句“在完整标定矩阵之外，另外在不同时段进行了一组独立单模效率测量”，至少在当前可用目录里是找不到直接证据链的。")
    lines.append("")
    lines.append("## 3. 现有数据能不能复现这组数")
    lines.append("")
    for item in payload["candidate_metrics"]:
        lines.append(
            f"- {item['name']}: "
            f"mean = `{item['mean_percent']:.4f}%`, "
            f"max = `{item['max_percent']:.4f}%`, "
            f"max at `l={item['max_at_l']}`"
        )
    lines.append("")
    lines.append("这里最值得注意的是：")
    lines.append("")
    lines.append("- 如果只用当前三次标定矩阵的对角元互相比，平均相对偏差大约是 `1.98%`，不是 `0.97%`。")
    lines.append("- 在这种比较口径下，`l=5` 的最大偏差约为 `2.62%`，和附录写的 `2.58% (l=5)` 很接近。")
    lines.append("- 但全局最大值其实出现在 `l=8`，大约 `5.74%`。")
    lines.append("- 如果看 `run2/generation_summary.csv` 里的对角校准目标值与均值，它们本身是完全一致的，平均偏差约等于 `0`，更不可能给出 `0.97%`。")
    lines.append("")
    lines.append("这说明附录里的那组数不是当前最终数据工作簿里自然会冒出来的标准统计结果。")
    lines.append("")
    lines.append("## 4. 旧数据残留的迹象")
    lines.append("")
    lines.append("当前最终数据里已经能看到明显的旧处理链痕迹：")
    lines.append("")
    lines.append("- Run 1 的 `final_matrix_summary.xlsx` 指向旧根目录 `final2`。")
    lines.append("- Run 2 指向旧根目录 `新3\\最终数据2\\连续测量`。")
    lines.append("- Run 3 指向旧根目录 `final`。")
    lines.append("- `run2/generation_summary.csv` 里的原始文件路径直接写着旧目录 `D:\\自制软件\\thesis\\数据内容\\对比度数据\\新3\\2\\连续测量\\...`。")
    lines.append("")
    lines.append("因此，当前最终数据目录本身就不是一份“从零开始、只有一套新鲜口径”的纯净仓库，而是整理过的结果目录。")
    lines.append("")
    lines.append("在这种情况下，附录中的 `0.97% / 2.58%` 非常像是从上游旧阶段带下来的说明性结论，但那组独立复测原始数据并没有跟着当前最终数据一起沉淀下来。")
    lines.append("")
    lines.append("## 5. 当前最稳妥的判断")
    lines.append("")
    lines.append("在不调用当前目录之外旧原始目录的前提下，最稳妥的判断是：")
    lines.append("")
    lines.append("1. 这句附录表述在当前可用数据范围内不可追溯。")
    lines.append("2. 它不能算作“被当前最终数据严格支撑的现行事实”。")
    lines.append("3. 它高度疑似旧数据或旧处理中间结论残留。")
    lines.append("4. 如果后续要保留这句话，必须先把那组“独立单模效率复测”的原始来源找出来并重新核算。")
    lines.append("5. 如果找不出来，更稳的做法是把这句删掉，或者改成仅依据当前三次标定矩阵自身可验证的统计说法。")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    data_root = script_dir.parent / "最终数据"

    diag_s = np.asarray([load_diag_s(data_root / run) for run in ("1", "2", "3")])
    run_meta = [asdict(load_meta(data_root / run, run)) for run in ("1", "2", "3")]

    candidate_metrics = [
        asdict(run_to_mean_deviation(diag_s)),
        asdict(pairwise_run_deviation(diag_s)),
        asdict(generation_summary_diag_target_vs_mean(data_root / "2" / "generation_summary.csv")),
    ]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data_root": str(data_root),
        "exact_occurrence_files": search_exact_occurrences(data_root),
        "run_meta": run_meta,
        "candidate_metrics": candidate_metrics,
    }

    json_path = script_dir / "q3_repeatability_claim_trace.json"
    md_path = script_dir / "Q3_附录重复性口径溯源报告.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(payload), encoding="utf-8")
    print(f"JSON: {json_path}")
    print(f"MD  : {md_path}")


if __name__ == "__main__":
    main()
