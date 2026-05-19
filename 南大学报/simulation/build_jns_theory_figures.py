from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from derive_general_cavity_cases import main as derive_general_cavity_cases
from fp_theory_core import DATA_DIR, FIGURE_DIR, ensure_output_dirs
from simulate_continuous_N_sorting import main as simulate_continuous_N_sorting
from simulate_general_set_search import main as simulate_general_set_search
from simulate_oam_special_case_and_errors import main as simulate_oam_special_case_and_errors


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Microsoft YaHei",
            "axes.unicode_minus": False,
            "figure.dpi": 180,
            "savefig.dpi": 260,
            "axes.titlesize": 12,
            "axes.labelsize": 10.5,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
        }
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_matrix(path: Path) -> tuple[list[str], list[str], np.ndarray]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        col_labels = header[1:]
        row_labels = []
        rows = []
        for row in reader:
            row_labels.append(row[0])
            rows.append([float(value) for value in row[1:]])
    return row_labels, col_labels, np.asarray(rows, dtype=float)


def ensure_data() -> None:
    required = [
        DATA_DIR / "general_cavity_mapping.csv",
        DATA_DIR / "continuous_N_smin_landscape.csv",
        DATA_DIR / "continuous_M9_condition_probability_matrix.csv",
        DATA_DIR / "continuous_capacity_boundary.csv",
        DATA_DIR / "oam_as_N_special_case.csv",
    ]
    if all(path.exists() for path in required):
        return
    derive_general_cavity_cases()
    simulate_continuous_N_sorting()
    simulate_general_set_search()
    simulate_oam_special_case_and_errors()


def save(fig: plt.Figure, name: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / f"{name}.png", bbox_inches="tight")
    fig.savefig(FIGURE_DIR / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def fig01_general_cavity_framework() -> None:
    mapping = read_rows(DATA_DIR / "general_cavity_mapping.csv")
    back = read_rows(DATA_DIR / "general_cavity_backsubstitution_checks.csv")
    rho = np.array([float(row["rho_L_over_R"]) for row in mapping])
    k_pc = np.array([float(row["k_plane_concave"]) for row in mapping])
    k_dc = np.array([float(row["k_symmetric_double_concave_near_planar"]) for row in mapping])
    k_2x = np.array([float(row["naive_2x_k_plane_concave"]) for row in mapping])
    max_err = max(float(row["abs_error"]) for row in back)

    fig = plt.figure(figsize=(12.5, 5.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.0])
    ax = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    ax.plot(rho, k_pc, lw=2.2, label="平凹腔")
    ax.plot(rho, k_dc, lw=2.2, label="对称双凹腔")
    ax.plot(rho, k_2x, "--", lw=1.6, label="错误的 2 倍直觉")
    ax.set_xlabel(r"$\rho=L/R$")
    ax.set_ylabel(r"$k_{\mathrm{eff}}$")
    ax.set_title("(a) 同一几何比下的有效 Gouy 步长", loc="left")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    ax.annotate(r"$k_{\rm dc}/k_{\rm pc}\to\sqrt{2}$", xy=(0.08, 0.13), xytext=(0.22, 0.38), arrowprops={"arrowstyle": "->"})

    ax2.axis("off")
    blocks = [
        ("一般稳定两镜腔", r"$g_i=1-L/R_i,\quad k_{\rm eff}=\pi^{-1}\arccos\sqrt{g_1g_2}$"),
        ("平凹腔回代", r"$L/R=\sin^2(\pi k_{\rm eff})$"),
        ("对称双凹腔回代", r"$L/R=1\pm\cos(\pi k_{\rm eff})$"),
        ("一般非对称双镜腔", r"$L^2-(R_1+R_2)L+R_1R_2\sin^2(\pi k_{\rm eff})=0$"),
    ]
    for idx, (title, eq) in enumerate(blocks):
        y = 0.82 - idx * 0.22
        ax2.add_patch(plt.Rectangle((0.02, y - 0.10), 0.96, 0.15, transform=ax2.transAxes, fc="#f7f7f7", ec="#333333", lw=0.9))
        ax2.text(0.05, y, title, transform=ax2.transAxes, fontsize=11.5, weight="bold", va="center")
        ax2.text(0.05, y - 0.06, eq, transform=ax2.transAxes, fontsize=10.5, va="center")
    ax2.text(0.02, 0.02, f"回代核对最大误差：{max_err:.2e}", transform=ax2.transAxes, fontsize=10.5)
    ax2.set_title("(b) 腔型只改变几何回代", loc="left")
    fig.tight_layout()
    save(fig, "fig01_general_cavity_framework")


def fig02_continuous_landscape() -> None:
    rows = read_rows(DATA_DIR / "continuous_N_smin_landscape.csv")
    branches = read_rows(DATA_DIR / "continuous_N_optimal_branches.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.9))
    for M, color in [(4, "#1565c0"), (9, "#d84315"), (15, "#2e7d32"), (30, "#6a1b9a")]:
        sel = [row for row in rows if int(row["M"]) == M]
        axes[0].plot([float(row["k"]) for row in sel], [float(row["s_min"]) for row in sel], lw=1.6, color=color, label=f"M={M}")
    axes[0].set_xlabel(r"$k_{\mathrm{eff}}$")
    axes[0].set_ylabel(r"$s_{\min}$")
    axes[0].set_title("(a) 连续总阶集合的最小间距景观", loc="left")
    axes[0].grid(alpha=0.25)
    axes[0].legend(frameon=False)

    M = 9
    sel9 = [row for row in rows if int(row["M"]) == M]
    axes[1].plot([float(row["k"]) for row in sel9], [float(row["s_min"]) for row in sel9], color="#d84315", lw=1.8)
    for row in branches:
        if int(row["M"]) == M:
            axes[1].axvline(float(row["k_star"]), color="#555555", ls="--", lw=1.0)
            axes[1].text(float(row["k_star"]), 0.118, f"m={row['m']}", ha="center", fontsize=9)
    axes[1].axhline(1 / M, color="#333333", ls=":", lw=1.2, label=r"$1/M$")
    axes[1].set_ylim(0, 0.13)
    axes[1].set_xlabel(r"$k_{\mathrm{eff}}$")
    axes[1].set_ylabel(r"$s_{\min}$")
    axes[1].set_title("(b) M=9 的解析最优分支", loc="left")
    axes[1].grid(alpha=0.25)
    axes[1].legend(frameon=False)
    fig.tight_layout()
    save(fig, "fig02_continuous_N_landscape")


def fig03_airy_response_matrix() -> None:
    labels, cols, raw = read_matrix(DATA_DIR / "continuous_M9_raw_airy_response_matrix.csv")
    _, _, cond = read_matrix(DATA_DIR / "continuous_M9_condition_probability_matrix.csv")
    with (DATA_DIR / "continuous_M9_response_summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 5.0))
    im0 = axes[0].imshow(raw, cmap="magma", vmin=0, vmax=1)
    axes[0].set_title("(a) 周期 Airy 原始响应矩阵", loc="left")
    im1 = axes[1].imshow(100 * cond, cmap="viridis", vmin=0, vmax=100)
    axes[1].set_title("(b) 列归一化条件概率矩阵 (%)", loc="left")
    for ax in axes:
        ax.set_xticks(range(len(cols)), cols)
        ax.set_yticks(range(len(labels)), labels)
        ax.set_xlabel("输入/锁定总阶 N")
        ax.set_ylabel("输出判决总阶 N")
    for i in range(cond.shape[0]):
        for j in range(cond.shape[1]):
            if i == j or cond[i, j] > 0.015:
                axes[1].text(j, i, f"{100*cond[i,j]:.1f}", ha="center", va="center", color="white" if cond[i, j] < 0.5 else "black", fontsize=7.8)
    fig.colorbar(im0, ax=axes[0], fraction=0.046)
    fig.colorbar(im1, ax=axes[1], fraction=0.046)
    fig.text(
        0.5,
        -0.02,
        f"M=9, F=32.21, k=2/9: eta={100*summary['eta_sort']:.2f}%, ER_sum={summary['finite_airy_ER_sum_dB']:.2f} dB, I={summary['mutual_information_bits']:.2f} bits",
        ha="center",
        fontsize=10.5,
    )
    fig.tight_layout()
    save(fig, "fig03_airy_response_matrix")


def fig04_capacity_phase_map() -> None:
    rows = read_rows(DATA_DIR / "continuous_capacity_boundary.csv")
    tau_values = sorted({float(row["tau_0"]) for row in rows})
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    for tau in tau_values:
        sel = [row for row in rows if abs(float(row["tau_0"]) - tau) < 1e-12]
        axes[0].plot([int(row["M"]) for row in sel], [float(row["F_min"]) for row in sel], lw=1.8, label=fr"$\tau_0={tau:g}$")
        axes[1].plot([int(row["M"]) for row in sel], [100 * float(row["finite_eta_sort"]) for row in sel], lw=1.8, label=fr"$\tau_0={tau:g}$")
    axes[0].set_xlabel("连续目标数 M")
    axes[0].set_ylabel(r"最低精细度 $\mathcal{F}_{\min}=M\tau_0$")
    axes[0].set_title("(a) 容量边界", loc="left")
    axes[0].grid(alpha=0.25)
    axes[0].legend(frameon=False)
    axes[1].set_xlabel("连续目标数 M")
    axes[1].set_ylabel(r"边界处分选成功率 $\eta_{\rm sort}$ (%)")
    axes[1].set_title("(b) 有限维 Airy 成功率逼近大 M 极限", loc="left")
    axes[1].grid(alpha=0.25)
    axes[1].legend(frameon=False)
    fig.tight_layout()
    save(fig, "fig04_capacity_performance")


def fig05_oam_error_boundary() -> None:
    radial = read_rows(DATA_DIR / "radial_waist_mismatch_scan.csv")
    satellite = read_rows(DATA_DIR / "satellite_peak_degeneracy_examples.csv")
    fig = plt.figure(figsize=(12.5, 5.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 1.05])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[0, 2])

    x = np.arange(10)
    ax0.plot(x, x + 1, "o-", lw=2)
    ax0.set_xlabel(r"单符号 OAM $l$ (p=0)")
    ax0.set_ylabel(r"横向总阶 $N=|l|+1$")
    ax0.set_title("(a) OAM 连续集是 N 连续集特例", loc="left")
    ax0.grid(alpha=0.25)
    ax0.text(0.05, 0.88, r"$+l$ 与 $-l$ 在单腔中简并", transform=ax0.transAxes, fontsize=10.5)

    for l_abs, color in [(0, "#1565c0"), (4, "#2e7d32"), (8, "#d84315"), (12, "#6a1b9a")]:
        xs, ys = [], []
        for row in radial:
            if str(row["p"]) == "1" and int(row["abs_l"]) == l_abs:
                xs.append(float(row["eta_w_in_over_w0"]))
                ys.append(100 * float(row["power"]))
        ax1.plot(xs, ys, "o-", color=color, label=fr"$|l|={l_abs}$")
    ax1.set_xlabel(r"束腰比 $\eta=w_{\rm in}/w_0$")
    ax1.set_ylabel(r"$p=1$ 径向寄生功率 (%)")
    ax1.set_title("(b) 轴对称失配主要泄漏到同一 l 的 p=1", loc="left")
    ax1.grid(alpha=0.25)
    ax1.legend(frameon=False)

    ax2.axis("off")
    ax2.set_title("(c) 卫星峰来自相同总阶 N", loc="left")
    examples = [row for row in satellite if row["component"] in {"LG_p=1_abs_l=4", "LG_p=1_abs_l=6", "LG_p=2_abs_l=4"}]
    y = 0.78
    for row in examples:
        ax2.text(
            0.02,
            y,
            rf"{row['component']}: $N={row['N']}$, 与 $p=0, |l|={row['degenerate_p0_abs_l']}$ 同频",
            transform=ax2.transAxes,
            fontsize=10.5,
        )
        y -= 0.18
    ax2.text(
        0.02,
        0.15,
        "正文建议：主理论用 N；误差分析再展开到 l,p。单个各向同性 FP 腔不声称完成 signed-OAM 全判别。",
        transform=ax2.transAxes,
        fontsize=10.5,
        wrap=True,
    )
    fig.tight_layout()
    save(fig, "fig05_oam_special_case_errors")


def main() -> None:
    ensure_output_dirs()
    setup_style()
    ensure_data()
    fig01_general_cavity_framework()
    fig02_continuous_landscape()
    fig03_airy_response_matrix()
    fig04_capacity_phase_map()
    fig05_oam_error_boundary()
    print(f"wrote figures to {FIGURE_DIR}")


if __name__ == "__main__":
    main()
