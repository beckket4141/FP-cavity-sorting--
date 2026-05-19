from __future__ import annotations

import csv
import json
from pathlib import Path

from build_jns_theory_figures import main as build_figures
from fp_theory_core import DATA_DIR, FIGURE_DIR, REPORT_DIR, ensure_output_dirs, write_csv


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def export_manuscript_tables() -> None:
    branch_rows = read_rows(DATA_DIR / "continuous_N_optimal_branches.csv")
    chosen = []
    for M in (4, 6, 9, 12, 15, 20, 30, 50):
        rows = [row for row in branch_rows if int(row["M"]) == M]
        if not rows:
            continue
        # Prefer the branch whose plane-concave L/R is closest to 0.5.
        best = min(rows, key=lambda row: abs(float(row["plane_concave_L_over_R"]) - 0.5))
        chosen.append(
            {
                "M": M,
                "recommended_m": best["m"],
                "k_star": best["k_star"],
                "s_min": best["s_min"],
                "F_min_tau0_3": best["F_min_tau0_3"],
                "plane_concave_L_over_R": best["plane_concave_L_over_R"],
                "ER_sum_dB_at_boundary": best["ER_sum_dB_at_boundary"],
                "eta_sort_at_boundary": best["eta_sort_at_boundary"],
            }
        )
    write_csv(REPORT_DIR / "table_continuous_design_blueprint_tau0_3.csv", chosen)

    cavity_rows = read_rows(DATA_DIR / "m9_general_cavity_branch_sensitivity.csv")
    write_csv(REPORT_DIR / "table_m9_cavity_branch_sensitivity.csv", cavity_rows)


def build_report_text() -> str:
    cavity = read_json(DATA_DIR / "general_cavity_summary.json")
    cont = read_json(DATA_DIR / "continuous_M9_response_summary.json")
    general = read_json(DATA_DIR / "general_set_search_summary.json")
    oam = read_json(DATA_DIR / "oam_error_boundary_summary.json")

    figure_items = [
        ("图1", "fig01_general_cavity_framework", "一般稳定腔统一 k_eff 框架与平凹/双凹/非对称腔回代", "general_cavity_mapping.csv, general_cavity_backsubstitution_checks.csv"),
        ("图2", "fig02_continuous_N_landscape", "连续 N 集合的 s_min 景观与解析最优分支", "continuous_N_smin_landscape.csv, continuous_N_optimal_branches.csv"),
        ("图3", "fig03_airy_response_matrix", "周期 Airy 原始响应矩阵与条件概率矩阵", "continuous_M9_raw_airy_response_matrix.csv, continuous_M9_condition_probability_matrix.csv"),
        ("图4", "fig04_capacity_performance", "容量边界与有限维 Airy 成功率", "continuous_capacity_boundary.csv"),
        ("图5", "fig05_oam_special_case_errors", "OAM 特例、signed-OAM 退化与径向寄生峰来源", "oam_as_N_special_case.csv, radial_waist_mismatch_scan.csv"),
    ]
    fig_lines = []
    for label, stem, meaning, data in figure_items:
        fig_lines.append(f"- {label} `{stem}.png/.pdf`：{meaning}。数据源：`{data}`。")

    return f"""# 南大学报一般稳定 FP 腔理论仿真报告

## 定稿口径

- 本文主变量采用横向总阶 `N=2p+|l|+1`，OAM 只是 `N` 序列的物理特例。
- 单个各向同性 FP 腔按总阶 `N` 分选，不能单独区分 `+l` 与 `-l`。
- 响应串扰分析是理论闭环的一部分，不是附加图；主模型采用周期 Airy 核。
- 对称双凹腔不是平凹腔作 `L -> 2L`，小几何比增强因子趋近 `sqrt(2)`。
- 连续集容量界与 Airy 串扰只依赖 `k_eff` 和 finesse，腔型只改变几何回代与鲁棒性排序。

## 关键数值核对

- 一般腔几何回代最大误差：`{cavity["max_backsubstitution_abs_error"]:.3e}`。
- M=9、F=32.21、k=2/9 时，有限维 Airy 参考 `ER_sum={cont["finite_airy_ER_sum_dB"]:.4f} dB`，`eta={100*cont["finite_airy_eta_sort"]:.4f}%`。
- 同一条件下条件概率矩阵列和最大误差：`{cont["column_sum_error"]:.3e}`。
- tau0=3 的大 M 极限：`ER_sum={cont["large_M_tau0_3_ER_sum_dB"]:.4f} dB`，`eta={100*cont["large_M_tau0_3_eta_sort"]:.4f}%`。
- 连续集 M=2..50 的解析最优 `s_min=1/M` 最大误差：`{cont["max_smin_optimal_error_M2_to_M50"]:.3e}`。
- `k` 与 `1-k` 的距离矩阵最大差异：`{cont["max_k_symmetry_distance_error"]:.3e}`。
- 一般非连续示例最优点：`k={general["best_k_fraction"]}`，`s_min={general["best_s_min"]:.8f}`，`F_min(tau0=3)={general["F_min"]:.4f}`。
- OAM 边界：{oam["signed_OAM_boundary"]}
- 径向寄生示例：`|l|=8, eta=0.95` 时 `p=1` 权重约 `{100*oam["p1_power_abs_l8_eta095"]:.3f}%`。

## 主图与数据

{chr(10).join(fig_lines)}

## 正文可用结论

1. 稳定两镜 FP 腔的分选设计可分为两层：折叠谱层只依赖 `k_eff`，几何实现层由具体腔型给出回代关系。
2. 对连续总阶集合 `S_M={{1,...,M}}`，最优条件为 `k*=m/M` 且 `gcd(m,M)=1`，此时 `s_min=1/M`。
3. 周期 Airy 响应矩阵把几何间距直接转化为条件概率矩阵，因此 `eta_sort` 和 `ER_sum` 是设计理论的自然输出。
4. 容量边界 `M <= floor(F/tau0)` 来自 `tau_min=F*s_min` 与 `s_min<=1/M`，不依赖平凹腔这一特定构型。
5. 平凹和对称双凹在相同 `k_eff` 下具有相同谱排布与串扰矩阵，但对应几何点和鲁棒性排序不同；M=9 时平凹偏向 `m=2`，对称双凹偏向 `m=4`。
6. 对一般非连续总阶集合，最优 `k` 可在有限有理候选中精确搜索；这部分适合作为方法扩展或附录，不必抢主线。
7. OAM 连续分选应表述为 `p=0` 单符号 OAM 集合的总阶连续特例；径向寄生峰则用相同 `N` 的模式简并解释。
"""


def main() -> None:
    ensure_output_dirs()
    build_figures()
    export_manuscript_tables()
    report = build_report_text()
    (REPORT_DIR / "simulation_report.md").write_text(report, encoding="utf-8")
    print(f"wrote report to {REPORT_DIR / 'simulation_report.md'}")


if __name__ == "__main__":
    main()
