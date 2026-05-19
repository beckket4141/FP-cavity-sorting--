from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np


ROOT = Path(r"D:\自制软件\1.thesis\最终提交版本\Sorting in FP cavities\南大学报")
WORKSPACE = ROOT.parent
EXPORT_DIR = ROOT / "figures" / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

SRC_PNG = WORKSPACE / "png图片"
SRC_GENERAL = WORKSPACE / "验证推演3.15" / "FP腔一般化理论推导_双凹"
SRC_FRACTAL = WORKSPACE / "验证推演3.15" / "分形验证"
SRC_RADIAL = WORKSPACE / "验证推演3.15" / "腔实际性能参数验算" / "径向模式串扰推演计算"


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Microsoft YaHei",
            "axes.unicode_minus": False,
            "figure.dpi": 180,
            "savefig.dpi": 240,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
        }
    )


def read_csv_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(value: str) -> float:
    return float(value)


def fig01_unified_framework() -> None:
    img = mpimg.imread(SRC_PNG / "fig01_cavity_gouy_spiral.png")
    fig = plt.figure(figsize=(13, 5.8))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0])
    ax0 = fig.add_subplot(gs[0, 0])
    ax1 = fig.add_subplot(gs[0, 1])

    ax0.imshow(img)
    ax0.axis("off")
    ax0.set_title("(a) 折叠谱的单 FSR 圆周表示", loc="left", pad=10, fontsize=13)

    ax1.axis("off")
    ax1.set_title("(b) 统一步长与几何回代", loc="left", pad=10, fontsize=13)

    node_specs = [
        (0.12, 0.78, 0.76, 0.11, "稳定双镜几何", r"$g_i=1-L/R_i$"),
        (
            0.12,
            0.56,
            0.76,
            0.13,
            "有效归一化 Gouy 步长",
            r"$k_{\mathrm{eff}}=\pi^{-1}\arccos\sqrt{g_1g_2}$",
        ),
        (0.12, 0.34, 0.76, 0.11, "折叠谱排布", r"$s_{\min}(k)=\min\|qk\|$"),
        (0.12, 0.12, 0.34, 0.12, "平凹腔", r"$L/R=\sin^2(\pi k_{\mathrm{eff}})$"),
        (0.54, 0.12, 0.34, 0.12, "对称双凹腔", r"$L/R=1\pm\cos(\pi k_{\mathrm{eff}})$"),
    ]
    for x, y, w, h, title, eq in node_specs:
        ax1.add_patch(
            plt.Rectangle(
                (x, y),
                w,
                h,
                transform=ax1.transAxes,
                facecolor="#f7f7f7",
                edgecolor="#333333",
                linewidth=1.0,
            )
        )
        ax1.text(x + 0.03, y + h * 0.62, title, transform=ax1.transAxes, fontsize=11.5, va="center")
        ax1.text(x + 0.03, y + h * 0.28, eq, transform=ax1.transAxes, fontsize=11.5, va="center")

    arrow_pairs = [
        ((0.50, 0.78), (0.50, 0.69)),
        ((0.50, 0.56), (0.50, 0.45)),
        ((0.50, 0.34), (0.30, 0.24)),
        ((0.50, 0.34), (0.70, 0.24)),
    ]
    for start, end in arrow_pairs:
        ax1.annotate(
            "",
            xy=end,
            xytext=start,
            xycoords=ax1.transAxes,
            textcoords=ax1.transAxes,
            arrowprops=dict(arrowstyle="->", lw=1.2, color="#333333"),
        )
    ax1.text(
        0.12,
        0.02,
        r"同一 $k_{\mathrm{eff}}$ 控制谱排布；腔型差异进入几何回代与鲁棒性排序。",
        transform=ax1.transAxes,
        fontsize=10.8,
        color="#222222",
    )

    fig.tight_layout()
    fig.savefig(EXPORT_DIR / "fig01_unified_framework.png", bbox_inches="tight")
    plt.close(fig)


def fig02_landscape_structure() -> None:
    img_farey = mpimg.imread(SRC_FRACTAL / "outputs" / "farey_skeleton_summary.png")
    img_refine = mpimg.imread(SRC_FRACTAL / "outputs" / "fractal_refinement_summary.png")

    farey_stats = read_csv_dicts(SRC_FRACTAL / "outputs" / "farey_skeleton_verification.csv")
    nesting = read_csv_dicts(SRC_FRACTAL / "outputs" / "fractal_refinement_nesting_stats.csv")

    fig = plt.figure(figsize=(13.5, 7.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.26])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    ax1.imshow(img_farey)
    ax1.axis("off")
    ax1.set_title("(a) Farey 骨架控制局部峰值与斜率", loc="left")

    ax2.imshow(img_refine)
    ax2.axis("off")
    ax2.set_title("(b) 随 $M$ 增大呈现层级细化而非严格分形", loc="left")

    ax3.axis("off")
    farey_lines = []
    for row in farey_stats:
        farey_lines.append(
            f"M={row['M']}: Farey 阶数 Q={row['farey_order_Q']}，区间数={row['n_intervals']}，最大误差={float(row['max_abs_error']):.1e}"
        )
    nesting_lines = []
    for row in nesting:
        nesting_lines.append(
            f"M={row['coarse_M']}→{row['fine_M']}: 细景观从不高于粗景观，重合比例约 {100*float(row['equality_fraction']):.1f}%"
        )

    ax3.text(
        0.01,
        0.75,
        "结论：$s_{min}(k)$ 的“分形感”本质上来自 Farey 邻分数骨架下的层级细化，而不是单一缩放律生成的严格自相似分形。",
        fontsize=12.5,
        weight="bold",
    )
    ax3.text(0.01, 0.42, "\n".join(farey_lines), fontsize=11)
    ax3.text(0.01, 0.08, "\n".join(nesting_lines), fontsize=11)

    fig.tight_layout()
    fig.savefig(EXPORT_DIR / "fig02_landscape_structure.png", bbox_inches="tight")
    plt.close(fig)


def fig03_geometry_robustness() -> None:
    rows_map = read_csv_dicts(SRC_GENERAL / "outputs" / "geometry_mapping_comparison.csv")
    rho = np.array([to_float(r["rho"]) for r in rows_map])
    k_pc = np.array([to_float(r["k_plane_concave"]) for r in rows_map])
    k_2x = np.array([to_float(r["naive_2x_k_plane_concave"]) for r in rows_map])
    k_cc = np.array([to_float(r["k_double_concave_effective"]) for r in rows_map])

    rows_s = read_csv_dicts(SRC_GENERAL / "outputs" / "m9_branch_sensitivity.csv")
    colors = {
        "plane_concave": "#1565c0",
        "symmetric_double_concave": "#d84315",
    }
    markers = {
        "single_branch": "o",
        "near_planar": "^",
        "near_concentric": "s",
    }

    fig = plt.figure(figsize=(13, 5.8))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.1, 1.0])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    ax1.plot(rho, k_pc, color="#1565c0", lw=2.3, label="平凹腔")
    ax1.plot(rho, k_cc, color="#d84315", lw=2.3, label="对称双凹腔")
    ax1.plot(rho, k_2x, color="#6d4c41", lw=1.8, ls="--", label="错误的 2x 直觉")
    ax1.set_xlabel(r"几何比 $\rho=L/R$")
    ax1.set_ylabel(r"有效步长 $k_{\mathrm{eff}}$")
    ax1.set_title("(a) 平凹与对称双凹的几何映射并不等价", loc="left")
    ax1.grid(alpha=0.25)
    ax1.legend(frameon=False)
    ax1.annotate(
        r"$k_{cc}/k_{pc}\to \sqrt{2}$",
        xy=(0.08, k_cc[1]),
        xytext=(0.18, 0.36),
        arrowprops=dict(arrowstyle="->", lw=1.2),
        fontsize=11,
    )

    for row in rows_s:
        geom = row["geometry"]
        branch = row["branch"]
        m = int(row["m"])
        x = to_float(row["rho"])
        y = to_float(row["abs_dk_d_rho"])
        label = None
        if geom == "plane_concave" and branch == "single_branch":
            label = "平凹腔"
        elif geom == "symmetric_double_concave" and branch == "near_planar":
            label = "双凹腔（近平面支）"
        elif geom == "symmetric_double_concave" and branch == "near_concentric":
            label = "双凹腔（近同心支）"
        ax2.scatter(
            x,
            y,
            color=colors[geom],
            marker=markers[branch],
            s=90,
            label=label,
            edgecolor="black",
            linewidth=0.5,
        )
        ax2.text(x + 0.015, y + 0.01, f"m={m}", fontsize=10)

    ax2.axvline(0.5, color="#1565c0", ls=":", lw=1.2)
    ax2.axvline(1.0, color="#d84315", ls=":", lw=1.2)
    ax2.text(0.51, 0.965, "平凹最稳区", color="#1565c0", fontsize=10, va="top")
    ax2.text(1.01, 0.965, "双凹共焦区", color="#d84315", fontsize=10, va="top")
    ax2.set_xlabel(r"几何比 $\rho=L/R$")
    ax2.set_ylabel(r"几何灵敏度 $|dk/d\rho|$")
    ax2.set_title("(b) `M=9` 时鲁棒代表支由 $m=2$ 迁移到 $m=4$", loc="left")
    ax2.grid(alpha=0.25)
    handles, labels = ax2.get_legend_handles_labels()
    uniq = []
    uniq_labels = []
    for h, l in zip(handles, labels):
        if l and l not in uniq_labels:
            uniq.append(h)
            uniq_labels.append(l)
    ax2.legend(uniq, uniq_labels, frameon=False, loc="upper right")

    fig.tight_layout()
    fig.savefig(EXPORT_DIR / "fig03_geometry_robustness.png", bbox_inches="tight")
    plt.close(fig)


def fig04_radial_leakage() -> None:
    rows = read_csv_dicts(SRC_RADIAL / "radial_order_lmix_radial_table.csv")
    l_values = [0, 4, 8]
    eta_values = [0.98, 0.95, 0.90]

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2), sharey=True)
    colors = ["#1565c0", "#ef6c00", "#8e24aa"]

    for ax, l_val in zip(axes, l_values):
        p0 = []
        p1 = []
        p2plus = []
        for eta in eta_values:
            matches = [r for r in rows if int(r["l"]) == l_val and abs(float(r["eta"]) - eta) < 1e-9]
            p0.append(sum(float(r["power"]) for r in matches if r["p"] == "0"))
            p1.append(sum(float(r["power"]) for r in matches if r["p"] == "1"))
            p2plus.append(sum(float(r["power"]) for r in matches if r["p"] not in {"0", "1", "partial_sum_0_to_pmax"}))
        x = np.arange(len(eta_values))
        ax.bar(x, p0, color=colors[0], label="$p=0$")
        ax.bar(x, p1, bottom=p0, color=colors[1], label="$p=1$")
        ax.bar(x, p2plus, bottom=np.array(p0) + np.array(p1), color=colors[2], label="$p\\geq 2$")
        ax.set_xticks(x, [str(e) for e in eta_values])
        ax.set_ylim(0, 1.02)
        ax.set_title(fr"$l={l_val}$")
        ax.set_xlabel(r"$\eta=w_{\mathrm{in}}/w_0$")
        ax.grid(axis="y", alpha=0.22)
        for xi, val in zip(x, p1):
            ax.text(xi, min(0.98, p0[xi] + val + 0.015), f"{100*val:.2f}%", ha="center", fontsize=9)

    axes[0].set_ylabel("功率占比")
    axes[0].legend(frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(EXPORT_DIR / "fig04_radial_leakage.png", bbox_inches="tight")
    plt.close(fig)


def fig05_error_classification() -> None:
    rows = read_csv_dicts(SRC_RADIAL / "radial_order_lmix_lmix_table.csv")

    fig = plt.figure(figsize=(13.8, 5.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 1.18], wspace=0.36)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])

    # Panel (a): axisymmetric z-offset -> p leakage but no other-l
    for l_val, color in zip([0, 4, 8], ["#1565c0", "#2e7d32", "#c62828"]):
        sel = [r for r in rows if r["case"] == "axisymmetric_z_offset" and int(r["l_target"]) == l_val]
        x = np.array([float(r["control"]) for r in sel])
        y = np.array([float(r["p1_weight"]) for r in sel])
        ax1.plot(x, 100 * y, marker="o", color=color, label=fr"$l={l_val}$")
    ax1.set_title("(a) 轴对称失配", loc="left", fontsize=12)
    ax1.set_xlabel(r"归一化轴向偏差")
    ax1.set_ylabel(r"$p=1$ 功率占比 (%)")
    ax1.grid(alpha=0.25)
    ax1.legend(frameon=False)

    # Panel (b): symmetry breaking -> other-l grows
    for case, color, marker, label in [
        ("lateral_shift", "#6a1b9a", "s", "横向偏移"),
        ("phase_tilt_x", "#ef6c00", "^", "相位倾斜"),
    ]:
        sel = [r for r in rows if r["case"] == case and int(r["l_target"]) == 8]
        x = np.array([float(r["control"]) for r in sel])
        y = np.array([float(r["other_l_weight"]) for r in sel])
        ax2.plot(x, 100 * y, marker=marker, color=color, lw=2, label=label)
    ax2.set_title("(b) 破坏圆对称误差", loc="left", fontsize=12)
    ax2.set_xlabel("误差控制参数")
    ax2.set_ylabel(r"$other$-$l$ 功率占比 (%)")
    ax2.grid(alpha=0.25)
    ax2.legend(frameon=False)

    # Panel (c): satellite schematic
    ax3.axis("off")
    ax3.set_title("(c) 卫星峰示意", loc="left", fontsize=12)
    ax3.text(
        0.05,
        0.88,
        r"目标分量：$LG_0^4 \Rightarrow N=2\times 0 + 4 + 1 = 5$",
        fontsize=11.5,
        transform=ax3.transAxes,
    )
    ax3.text(
        0.05,
        0.70,
        r"寄生分量：$LG_1^4 \Rightarrow N=2\times 1 + 4 + 1 = 7$",
        fontsize=11.5,
        color="#d84315",
        transform=ax3.transAxes,
    )
    ax3.text(
        0.05,
        0.52,
        r"频率简并：$LG_1^4$ 与 $LG_0^6$ 具有相同总阶 $N=7$",
        fontsize=11.5,
        transform=ax3.transAxes,
    )

    x0 = 0.08
    y0 = 0.18
    width = 0.78
    ax3.plot([x0, x0 + width], [y0, y0], color="black", lw=1.2, transform=ax3.transAxes)
    positions = [0.18, 0.40, 0.68]
    labels = ["主峰\n$N=5$", "卫星峰\n$N=7$", "更高阶\n$N>7$"]
    colors = ["#1565c0", "#d84315", "#616161"]
    heights = [0.22, 0.11, 0.05]
    for p, h, lab, col in zip(positions, heights, labels, colors):
        ax3.add_patch(
            plt.Rectangle((p, y0), 0.06, h, transform=ax3.transAxes, color=col, alpha=0.9)
        )
        ax3.text(p + 0.03, y0 + h + 0.03, lab, transform=ax3.transAxes, ha="center", fontsize=10)
    ax3.text(
        0.05,
        0.02,
        "若误差主要保持圆对称，频谱小峰更自然地理解为同一 $l$ 子空间内的 $p>0$ 分量被共振选出，而不是角向模式被大幅转换。",
        transform=ax3.transAxes,
        fontsize=10.0,
        wrap=True,
    )

    fig.savefig(EXPORT_DIR / "fig05_error_classification.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    setup_style()
    fig01_unified_framework()
    fig02_landscape_structure()
    fig03_geometry_robustness()
    fig04_radial_leakage()
    fig05_error_classification()
    print(f"Exported figures to: {EXPORT_DIR}")


if __name__ == "__main__":
    main()
