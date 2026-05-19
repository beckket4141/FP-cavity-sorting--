#!/usr/bin/env python3
"""Check the real Q3 sensitivity of the weak l=8 calibration channel.

What this script answers
------------------------
1. How unstable is S88 across the 3 independent runs?
2. What does the thesis number "93.19 +/- 0.37%" actually mean?
3. If we deliberately perturb the l=8 calibration, how much do the final
   success-rate and ER results really move?

This script does not modify any thesis source or raw data file.
It only reads the existing workbooks and writes summary files in the current
folder.
"""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from openpyxl import load_workbook
from scipy.optimize import nnls


PERTURB_FACTORS = [0.99, 1.01, 0.95, 1.05, 0.90, 1.10]


@dataclass
class BaselineRunMetrics:
    run: str
    s88: float
    s55: float
    s11: float
    diag_mean_percent: float
    diag_l8_percent: float
    er_mean_db: float
    er_l8_db: float
    x88_uW: float


@dataclass
class ScenarioMetrics:
    factor: float
    diag_mean_percent: float
    diag_l8_percent: float
    er_mean_db: float
    er_l8_db: float
    x88_uW: float
    delta_diag_mean_percent_point: float
    delta_diag_l8_percent_point: float
    delta_er_mean_db: float
    delta_er_l8_db: float
    delta_x88_percent: float


@dataclass
class ScenarioFamily:
    scenario: str
    results: list[ScenarioMetrics]


def load_matrix(workbook: Path, sheet: str, row_start: int = 2) -> np.ndarray:
    wb = load_workbook(workbook, data_only=True, read_only=True)
    rows = list(wb[sheet].iter_rows(values_only=True))
    wb.close()
    return np.asarray([[float(v) for v in row[1:10]] for row in rows[row_start - 1 : row_start - 1 + 9]], dtype=float)


def solve_nnls(s_matrix: np.ndarray, y_matrix: np.ndarray) -> np.ndarray:
    x_matrix = np.zeros_like(y_matrix, dtype=float)
    for col in range(y_matrix.shape[1]):
        x_matrix[:, col], _ = nnls(s_matrix, np.clip(y_matrix[:, col], 0.0, None))
    return x_matrix


def compute_metrics(x_matrix: np.ndarray) -> dict[str, float]:
    p_matrix = x_matrix / np.sum(x_matrix, axis=0, keepdims=True)
    diag = np.diag(p_matrix) * 100.0

    er_sum = []
    for lock in range(x_matrix.shape[1]):
        signal = float(x_matrix[lock, lock])
        leak = float(np.sum(x_matrix[:, lock]) - signal)
        er_sum.append(10.0 * math.log10(signal / leak))

    return {
        "diag_mean_percent": float(np.mean(diag)),
        "diag_l8_percent": float(diag[8]),
        "er_mean_db": float(np.mean(er_sum)),
        "er_l8_db": float(er_sum[8]),
        "x88_uW": float(x_matrix[8, 8] * 1e6),
    }


def perturb_s88_only(s_matrix: np.ndarray, factor: float) -> np.ndarray:
    out = s_matrix.copy()
    out[8, 8] *= factor
    return out


def perturb_col8_all(s_matrix: np.ndarray, factor: float) -> np.ndarray:
    out = s_matrix.copy()
    out[:, 8] *= factor
    return out


def summarize_family(
    base_metrics_runs: list[BaselineRunMetrics],
    scenario_name: str,
    modifier,
    s_matrices: dict[str, np.ndarray],
    y_matrices: dict[str, np.ndarray],
) -> ScenarioFamily:
    base_diag_mean = statistics.mean(item.diag_mean_percent for item in base_metrics_runs)
    base_diag_l8 = statistics.mean(item.diag_l8_percent for item in base_metrics_runs)
    base_er_mean = statistics.mean(item.er_mean_db for item in base_metrics_runs)
    base_er_l8 = statistics.mean(item.er_l8_db for item in base_metrics_runs)
    base_x88 = statistics.mean(item.x88_uW for item in base_metrics_runs)

    results: list[ScenarioMetrics] = []
    for factor in PERTURB_FACTORS:
        run_metrics = []
        for run in ("1", "2", "3"):
            x_matrix = solve_nnls(modifier(s_matrices[run], factor), y_matrices[run])
            run_metrics.append(compute_metrics(x_matrix))

        diag_mean = statistics.mean(item["diag_mean_percent"] for item in run_metrics)
        diag_l8 = statistics.mean(item["diag_l8_percent"] for item in run_metrics)
        er_mean = statistics.mean(item["er_mean_db"] for item in run_metrics)
        er_l8 = statistics.mean(item["er_l8_db"] for item in run_metrics)
        x88 = statistics.mean(item["x88_uW"] for item in run_metrics)

        results.append(
            ScenarioMetrics(
                factor=factor,
                diag_mean_percent=diag_mean,
                diag_l8_percent=diag_l8,
                er_mean_db=er_mean,
                er_l8_db=er_l8,
                x88_uW=x88,
                delta_diag_mean_percent_point=diag_mean - base_diag_mean,
                delta_diag_l8_percent_point=diag_l8 - base_diag_l8,
                delta_er_mean_db=er_mean - base_er_mean,
                delta_er_l8_db=er_l8 - base_er_l8,
                delta_x88_percent=(x88 / base_x88 - 1.0) * 100.0,
            )
        )

    return ScenarioFamily(scenario=scenario_name, results=results)


def build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Q3: l=8 通道到底有多危险")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Data root: `{payload['data_root']}`")
    lines.append("")
    lines.append("## 先说结论")
    lines.append("")
    lines.append("1. `l=8` 的标定通道确实是最弱的，也确实比中低阶通道更不稳。")
    lines.append("2. 但“通道效率低”不等于“最终成功率一定被 25 倍放大地搞坏”。")
    lines.append("3. 真正的情况是：`l=8` 的绝对去嵌入功率会比较敏感，但论文最后报的成功率是列归一化后的百分比，所以敏感度被大幅压下来了。")
    lines.append("4. `93.19 +/- 0.37%` 这个数，本质上是 3 次独立 run 的结果离散，不是把所有标定系统误差完整传播后的总不确定度。")
    lines.append("")
    lines.append("## 1. l=8 本身到底稳不稳")
    lines.append("")

    for run in payload["baseline_runs"]:
        lines.append(
            f"- Run {run['run']}: "
            f"`S88={run['s88']*100:.2f}%`, `S55={run['s55']*100:.2f}%`, `S11={run['s11']*100:.2f}%`, "
            f"`l=8` 成功率 `{run['diag_l8_percent']:.2f}%`, `l=8` 的 `ER_sum` `{run['er_l8_db']:.3f} dB`"
        )

    s88_stats = payload["s88_stats"]
    lines.append("")
    lines.append(
        f"- `S88` 在 3 次 run 中的均值是 `{s88_stats['mean_percent']:.2f}%`，"
        f"标准差是 `{s88_stats['std_percent']:.2f}%`，相对标准差是 `{s88_stats['rel_std_percent']:.2f}%`。"
    )
    lines.append(
        f"- 对比一下，`S55` 的相对标准差只有 `{payload['s55_stats']['rel_std_percent']:.2f}%`，"
        f"所以 Q3 里“高阶弱通道更脆弱”的直觉是对的。"
    )
    lines.append("")
    lines.append("## 2. `93.19 +/- 0.37%` 这个数到底是什么")
    lines.append("")
    lines.append("- 聚合工作簿 `triplicate_full9_aggregate.xlsx` 的 meta 已经写明：combined error bars 来自 3 次独立 run 的统计。")
    lines.append("- 所以正文里的 `93.19 +/- 0.37%`，更准确地说，是“3 次独立实验得到的最终平均成功率的 run-to-run 离散”。")
    lines.append("- 它不是“把 l=8 的标定系统误差完整传播进去之后的总误差预算”。")
    lines.append("")
    lines.append("这句话很重要，因为它直接回答了审稿人的第一刀：")
    lines.append("")
    lines.append("> 你这个 `+/-0.37%` 不能简单理解成“已经证明弱通道的所有标定误差都只有 0.37%”。")
    lines.append("")
    lines.append("## 3. 但审稿人的“25 倍放大”是不是就成立")
    lines.append("")
    lines.append("不成立，至少不能这样粗暴地成立。")
    lines.append("")
    lines.append("原因很简单：")
    lines.append("")
    lines.append("- 论文最后报的成功率不是绝对功率，而是每一列归一化后的百分比。")
    lines.append("- 所以就算 `x88` 的绝对值受 `S88` 影响比较大，最后百分比也会被列归一化压回来。")
    lines.append("- 再加上反演不是单独看一个数，而是 9 个通道一起解，所以不会变成“某个 1% 误差直接乘上 25”。")
    lines.append("")
    lines.append("## 4. 我实际做了什么敏感度测试")
    lines.append("")
    lines.append("我保持原始 `Y` 不变，只故意把 `l=8` 的标定改坏，再重新做 NNLS 反演。做了两类测试：")
    lines.append("")
    lines.append("- 只改 `S88` 这个对角元。")
    lines.append("- 把整列 `S[:,8]` 一起缩放。")
    lines.append("")
    lines.append("这两类都很符合 Q3 的直觉追问：如果 `l=8` 标定真的有偏，最后结果会被拉偏多少？")
    lines.append("")

    for family in payload["scenario_families"]:
        lines.append(f"## 5. {family['scenario']} 的结果")
        lines.append("")
        for item in family["results"]:
            lines.append(
                f"- 因子 `{item['factor']:.2f}`: "
                f"整体平均成功率变化 `{item['delta_diag_mean_percent_point']:+.3f}` pct-pt, "
                f"`l=8` 成功率变化 `{item['delta_diag_l8_percent_point']:+.3f}` pct-pt, "
                f"整体平均 `ER_sum` 变化 `{item['delta_er_mean_db']:+.3f} dB`, "
                f"`l=8` 的 `ER_sum` 变化 `{item['delta_er_l8_db']:+.3f} dB`, "
                f"`x88` 绝对值变化 `{item['delta_x88_percent']:+.2f}%`"
            )
        lines.append("")

    lines.append("## 6. 这些数字到底说明什么")
    lines.append("")
    lines.append("最关键的是两点：")
    lines.append("")
    lines.append("- 就算把 `S88` 人为改坏 `10%`，整体平均成功率也几乎不动，变化量只有几百分之一个百分点。")
    lines.append("- 受影响最大的确是 `l=8` 自己，但即便这样，它的成功率变化也不到 `1` 个百分点。")
    lines.append("")
    lines.append("所以，Q3 里最夸张的说法：")
    lines.append("")
    lines.append("> “因为 `l=8` 要放大 25 倍，所以 1% 标定误差必然导致 25% 最终结果误差”")
    lines.append("")
    lines.append("和现在这套真实数据处理流程并不相符。")
    lines.append("")
    lines.append("更接近事实的说法应该是：")
    lines.append("")
    lines.append("> `l=8` 确实是最脆弱通道，绝对去嵌入功率对标定更敏感；但论文最后报的成功率和热图是列归一化后的结果，因此这种敏感度不会按“1/S88”那样直接放大到最终百分比指标上。")
    lines.append("")
    lines.append("## 7. Q3 现在能回到什么程度")
    lines.append("")
    lines.append("现在可以比较稳地回三句话：")
    lines.append("")
    lines.append("1. `l=8` 确实是最弱、最需要小心的标定通道。")
    lines.append("2. 但现有数据表明，`l=8` 标定偏差对最终百分比成功率的影响，比“25 倍放大”那种粗略直觉要小得多。")
    lines.append("3. 不过，正文里的 `+/-0.37%` 只能代表 3 次 run 的统计离散，不能包装成已经完整覆盖了 `l=8` 标定系统误差。")
    lines.append("")
    lines.append("## 8. 最后的判断")
    lines.append("")
    lines.append("Q3 不能被回成“审稿人完全错了”。")
    lines.append("")
    lines.append("更实事求是的判断是：")
    lines.append("")
    lines.append("- 审稿人指出了一个真实薄弱点：`l=8` 的确最脆弱。")
    lines.append("- 但审稿人如果把这种脆弱直接夸大成“最终成功率肯定完全不可信”，那也不符合现有数据。")
    lines.append("- 现有数据支持的最稳口径，是“`l=8` 通道确实更敏感，但这种敏感性在最终列归一化结果上被明显压低；真正需要补的是把 `+/-0.37%` 的含义说清楚，而不是任由读者误会成总系统误差。”")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    data_root = script_dir.parent / "最终数据"

    s_matrices: dict[str, np.ndarray] = {}
    y_matrices: dict[str, np.ndarray] = {}
    baseline_runs: list[BaselineRunMetrics] = []

    for run in ("1", "2", "3"):
        run_dir = data_root / run
        s_matrix = load_matrix(run_dir / "calib_matrix_with_uncertainty.xlsx", "mean")
        y_matrix = load_matrix(run_dir / "full9_matrix_with_uncertainty.xlsx", "raw_y_mean")
        x_matrix = solve_nnls(s_matrix, y_matrix)
        metrics = compute_metrics(x_matrix)

        s_matrices[run] = s_matrix
        y_matrices[run] = y_matrix
        baseline_runs.append(
            BaselineRunMetrics(
                run=run,
                s88=float(s_matrix[8, 8]),
                s55=float(s_matrix[5, 5]),
                s11=float(s_matrix[1, 1]),
                diag_mean_percent=metrics["diag_mean_percent"],
                diag_l8_percent=metrics["diag_l8_percent"],
                er_mean_db=metrics["er_mean_db"],
                er_l8_db=metrics["er_l8_db"],
                x88_uW=metrics["x88_uW"],
            )
        )

    s88_values = [item.s88 for item in baseline_runs]
    s55_values = [item.s55 for item in baseline_runs]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "data_root": str(data_root),
        "baseline_runs": [asdict(item) for item in baseline_runs],
        "s88_stats": {
            "mean_percent": statistics.mean(s88_values) * 100.0,
            "std_percent": statistics.stdev(s88_values) * 100.0,
            "rel_std_percent": statistics.stdev(s88_values) / statistics.mean(s88_values) * 100.0,
        },
        "s55_stats": {
            "mean_percent": statistics.mean(s55_values) * 100.0,
            "std_percent": statistics.stdev(s55_values) * 100.0,
            "rel_std_percent": statistics.stdev(s55_values) / statistics.mean(s55_values) * 100.0,
        },
        "scenario_families": [
            asdict(
                summarize_family(
                    base_metrics_runs=baseline_runs,
                    scenario_name="只改 S88",
                    modifier=perturb_s88_only,
                    s_matrices=s_matrices,
                    y_matrices=y_matrices,
                )
            ),
            asdict(
                summarize_family(
                    base_metrics_runs=baseline_runs,
                    scenario_name="整列 S[:,8] 一起改",
                    modifier=perturb_col8_all,
                    s_matrices=s_matrices,
                    y_matrices=y_matrices,
                )
            ),
        ],
    }

    json_path = script_dir / "q3_l8_sensitivity_results.json"
    md_path = script_dir / "Q3_l8敏感度_详细报告.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(payload) + "\n", encoding="utf-8")

    print(f"JSON: {json_path}")
    print(f"MD  : {md_path}")


if __name__ == "__main__":
    main()
