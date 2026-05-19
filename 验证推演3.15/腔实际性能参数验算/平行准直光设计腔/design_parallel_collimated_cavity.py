from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = SCRIPT_DIR / "default_design_config.json"
OUTPUT_DIR = SCRIPT_DIR / "outputs"
EPS = 1e-12


@dataclass(frozen=True)
class BranchSpec:
    branch_m: int
    k_star: float
    L_over_R: float
    geometry_gap_to_half: float
    s_min: float
    F_min: float
    tau_min_at_budget: float
    tau_margin: float
    cavity_scale_factor: float
    nonredundant_rank: int
    is_recommended: bool
    feasible_by_tau: bool


def load_config(config_path: Path) -> dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    if config.get("mode_family") != "continuous":
        raise ValueError("Only mode_family='continuous' is supported in this simulator.")
    M = int(config["M"])
    if M < 2:
        raise ValueError("M must be >= 2.")
    tau_0 = float(config["tau_0"])
    finesse_budget = float(config["finesse_budget"])
    lambda0_nm = float(config["lambda0_nm"])
    n_medium = float(config["n_medium"])
    if tau_0 <= 0 or finesse_budget <= 0 or lambda0_nm <= 0 or n_medium <= 0:
        raise ValueError("tau_0, finesse_budget, lambda0_nm, and n_medium must be positive.")
    baseline = config["baseline_cavity"]
    if float(baseline["L_mm"]) <= 0 or float(baseline["R_mm"]) <= 0:
        raise ValueError("baseline_cavity L_mm and R_mm must be positive.")
    if float(baseline["L_mm"]) >= float(baseline["R_mm"]):
        raise ValueError("baseline_cavity must satisfy L_mm < R_mm for a stable plane-concave cavity.")
    targets = config.get("target_w0_um_list", [])
    if not targets:
        raise ValueError("target_w0_um_list must not be empty.")
    if any(float(value) <= 0 for value in targets):
        raise ValueError("All target w0 values must be positive.")
    size_limits = config.get("size_limits", {})
    for key in ("L_max_mm", "R_max_mm"):
        value = size_limits.get(key)
        if value is not None and float(value) <= 0:
            raise ValueError(f"{key} must be positive when provided.")


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def lambda_eff_m(lambda0_nm: float, n_medium: float) -> float:
    return lambda0_nm * 1e-9 / n_medium


def vacuum_lambda_m(lambda0_nm: float) -> float:
    return lambda0_nm * 1e-9


def k_from_geometry(alpha: float) -> float:
    alpha_clamped = min(max(alpha, 0.0), 1.0)
    return math.acos(math.sqrt(1.0 - alpha_clamped)) / math.pi


def s_min_continuous(k_value: float, M: int) -> float:
    distances = []
    for d in range(1, M):
        value = d * k_value
        distance = min(abs(value - round(value)), 1.0 - abs((value % 1.0) - 1.0))
        distance = min(distance, abs((value % 1.0) - 0.0))
        distances.append(distance)
    return float(min(distances)) if distances else 0.5


def baseline_metrics(config: dict[str, Any]) -> pd.DataFrame:
    baseline = config["baseline_cavity"]
    lambda0_nm = float(config["lambda0_nm"])
    n_medium = float(config["n_medium"])
    finesse_budget = float(config["finesse_budget"])
    tau_0 = float(config["tau_0"])
    M = int(config["M"])

    L_mm = float(baseline["L_mm"])
    R_mm = float(baseline["R_mm"])
    L_m = L_mm * 1e-3
    R_m = R_mm * 1e-3
    alpha = L_m / R_m
    k_value = k_from_geometry(alpha)
    zR_m = math.sqrt(L_m * (R_m - L_m))
    lambda_eff = lambda_eff_m(lambda0_nm, n_medium)
    lambda_vac = vacuum_lambda_m(lambda0_nm)
    w0_medium_m = math.sqrt(lambda_eff * zR_m / math.pi)
    w0_vac_m = math.sqrt(lambda_vac * zR_m / math.pi)
    w_curved_medium_m = w0_medium_m * math.sqrt(1.0 + (L_m / zR_m) ** 2)
    s_min_value = s_min_continuous(k_value, M)
    tau_min_value = finesse_budget * s_min_value
    F_min_required = tau_0 / s_min_value

    row = {
        "L_mm": L_mm,
        "R_mm": R_mm,
        "L_over_R": alpha,
        "k_from_geometry": k_value,
        "zR_mm": zR_m * 1e3,
        "w0_medium_um": w0_medium_m * 1e6,
        "w0_vacuum_um": w0_vac_m * 1e6,
        "w_curved_medium_um": w_curved_medium_m * 1e6,
        "s_min_for_continuous_M": s_min_value,
        "tau_min_at_budget": tau_min_value,
        "tau_margin_vs_tau0": tau_min_value - tau_0,
        "F_min_required_for_baseline_k": F_min_required,
        "finesse_budget": finesse_budget,
        "M": M,
        "tau_0": tau_0,
        "lambda0_nm": lambda0_nm,
        "n_medium": n_medium,
    }
    return pd.DataFrame([row])


def enumerate_branches(config: dict[str, Any]) -> list[BranchSpec]:
    M = int(config["M"])
    tau_0 = float(config["tau_0"])
    finesse_budget = float(config["finesse_budget"])
    candidates: list[BranchSpec] = []
    for m in range(1, M):
        if not (0 < m < M / 2):
            continue
        if gcd(m, M) != 1:
            continue
        k_star = m / M
        alpha = math.sin(math.pi * k_star) ** 2
        s_min = 1.0 / M
        F_min = tau_0 / s_min
        tau_min = finesse_budget * s_min
        cavity_scale_factor = 1.0 / math.sqrt(alpha * (1.0 - alpha))
        candidates.append(
            BranchSpec(
                branch_m=m,
                k_star=k_star,
                L_over_R=alpha,
                geometry_gap_to_half=abs(alpha - 0.5),
                s_min=s_min,
                F_min=F_min,
                tau_min_at_budget=tau_min,
                tau_margin=tau_min - tau_0,
                cavity_scale_factor=cavity_scale_factor,
                nonredundant_rank=0,
                is_recommended=False,
                feasible_by_tau=tau_min + EPS >= tau_0,
            )
        )
    ordered = sorted(candidates, key=lambda item: (item.geometry_gap_to_half, item.cavity_scale_factor, item.branch_m))
    result: list[BranchSpec] = []
    for idx, branch in enumerate(ordered, start=1):
        result.append(
            BranchSpec(
                branch_m=branch.branch_m,
                k_star=branch.k_star,
                L_over_R=branch.L_over_R,
                geometry_gap_to_half=branch.geometry_gap_to_half,
                s_min=branch.s_min,
                F_min=branch.F_min,
                tau_min_at_budget=branch.tau_min_at_budget,
                tau_margin=branch.tau_margin,
                cavity_scale_factor=branch.cavity_scale_factor,
                nonredundant_rank=idx,
                is_recommended=(idx == 1),
                feasible_by_tau=branch.feasible_by_tau,
            )
        )
    return result


def branch_summary_dataframe(branches: list[BranchSpec]) -> pd.DataFrame:
    rows = []
    for branch in branches:
        rows.append(
            {
                "branch_m": branch.branch_m,
                "nonredundant_rank": branch.nonredundant_rank,
                "is_recommended": branch.is_recommended,
                "k_star": branch.k_star,
                "L_over_R": branch.L_over_R,
                "geometry_gap_to_half": branch.geometry_gap_to_half,
                "s_min": branch.s_min,
                "F_min": branch.F_min,
                "tau_min_at_budget": branch.tau_min_at_budget,
                "tau_margin_vs_tau0": branch.tau_margin,
                "cavity_scale_factor": branch.cavity_scale_factor,
                "feasible_by_tau": branch.feasible_by_tau,
            }
        )
    return pd.DataFrame(rows)


def compute_inverse_design_rows(config: dict[str, Any], branches: list[BranchSpec]) -> pd.DataFrame:
    lambda_eff = lambda_eff_m(float(config["lambda0_nm"]), float(config["n_medium"]))
    size_limits = config.get("size_limits", {})
    L_max_mm = size_limits.get("L_max_mm")
    R_max_mm = size_limits.get("R_max_mm")

    rows = []
    for branch in branches:
        alpha = branch.L_over_R
        geom_term = math.sqrt(alpha * (1.0 - alpha))
        for target_w0_um in [float(v) for v in config["target_w0_um_list"]]:
            w0_m = target_w0_um * 1e-6
            zR_m = math.pi * w0_m**2 / lambda_eff
            R_m = zR_m / geom_term
            L_m = alpha * R_m
            w_curved_m = w0_m * math.sqrt(1.0 + (L_m / zR_m) ** 2)
            theta_div_mrad = lambda_eff / (math.pi * w0_m) * 1e3

            feasible_by_tau = branch.feasible_by_tau
            feasible_by_size = True
            failure_reasons: list[str] = []
            if not feasible_by_tau:
                failure_reasons.append("tau/finesse budget")
            if L_max_mm is not None and (L_m * 1e3) > float(L_max_mm) + EPS:
                feasible_by_size = False
                failure_reasons.append("L limit")
            if R_max_mm is not None and (R_m * 1e3) > float(R_max_mm) + EPS:
                feasible_by_size = False
                failure_reasons.append("R limit")
            if not failure_reasons and (L_max_mm is None and R_max_mm is None):
                failure_reason = "size limits not set"
            elif not failure_reasons:
                failure_reason = "none"
            else:
                failure_reason = " + ".join(failure_reasons)

            rows.append(
                {
                    "branch_m": branch.branch_m,
                    "nonredundant_rank": branch.nonredundant_rank,
                    "is_recommended": branch.is_recommended,
                    "k_star": branch.k_star,
                    "L_over_R": alpha,
                    "s_min": branch.s_min,
                    "F_min": branch.F_min,
                    "tau_min_at_budget": branch.tau_min_at_budget,
                    "tau_margin_vs_tau0": branch.tau_margin,
                    "target_w0_um": target_w0_um,
                    "zR_mm": zR_m * 1e3,
                    "L_mm": L_m * 1e3,
                    "R_mm": R_m * 1e3,
                    "w_curved_um": w_curved_m * 1e6,
                    "theta_div_mrad": theta_div_mrad,
                    "feasible_by_tau": feasible_by_tau,
                    "feasible_by_size": feasible_by_size,
                    "overall_feasible": bool(feasible_by_tau and feasible_by_size),
                    "failure_reason": failure_reason,
                }
            )
    return pd.DataFrame(rows)


def plot_w0_vs_geometry(output_path: Path, baseline_df: pd.DataFrame, solutions_df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), constrained_layout=True)
    ax_l, ax_r = axes

    colors = {1: "#b45309", 2: "#0f766e", 4: "#7c3aed"}
    for branch_m, group in solutions_df.groupby("branch_m"):
        group = group.sort_values("target_w0_um")
        label = f"m={branch_m}"
        lw = 2.2 if bool(group["is_recommended"].iloc[0]) else 1.6
        ax_l.plot(group["target_w0_um"], group["L_mm"], marker="o", lw=lw, color=colors.get(int(branch_m), None), label=label)
        ax_r.plot(group["target_w0_um"], group["R_mm"], marker="o", lw=lw, color=colors.get(int(branch_m), None), label=label)

    baseline = baseline_df.iloc[0]
    ax_l.scatter([baseline["w0_medium_um"]], [baseline["L_mm"]], color="black", s=55, zorder=5, label="current cavity")
    ax_r.scatter([baseline["w0_medium_um"]], [baseline["R_mm"]], color="black", s=55, zorder=5, label="current cavity")

    ax_l.set_xlabel("Target w0 (um)")
    ax_l.set_ylabel("Required L (mm)")
    ax_l.set_title("Geometry growth for larger w0")
    ax_l.grid(alpha=0.25)
    ax_l.legend(frameon=False, fontsize=8)

    ax_r.set_xlabel("Target w0 (um)")
    ax_r.set_ylabel("Required R (mm)")
    ax_r.set_title("Required mirror curvature radius")
    ax_r.grid(alpha=0.25)
    ax_r.legend(frameon=False, fontsize=8)

    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_divergence_vs_w0(output_path: Path, solutions_df: pd.DataFrame) -> None:
    recommended = solutions_df.loc[solutions_df["is_recommended"]].sort_values("target_w0_um")
    fig, ax1 = plt.subplots(figsize=(7.6, 4.8), constrained_layout=True)
    ax2 = ax1.twinx()

    ax1.plot(recommended["target_w0_um"], recommended["theta_div_mrad"], "-o", color="#0f766e", lw=2.0, label="theta_div")
    ax2.plot(recommended["target_w0_um"], recommended["zR_mm"], "-s", color="#1d4ed8", lw=1.8, label="zR")

    ax1.set_xlabel("Target w0 (um)")
    ax1.set_ylabel("Divergence half-angle (mrad)", color="#0f766e")
    ax2.set_ylabel("Rayleigh length zR (mm)", color="#1d4ed8")
    ax1.set_title("How close to collimated the beam becomes")
    ax1.grid(alpha=0.25)

    lines = ax1.get_lines() + ax2.get_lines()
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, frameon=False, fontsize=8, loc="upper right")

    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def plot_tau_margin_vs_w0(output_path: Path, config: dict[str, Any], solutions_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 4.8), constrained_layout=True)
    tau_0 = float(config["tau_0"])
    finesse_budget = float(config["finesse_budget"])
    x_values = sorted(float(v) for v in config["target_w0_um_list"])
    for branch_m, group in solutions_df.groupby("branch_m"):
        group = group.sort_values("target_w0_um")
        label = f"m={branch_m}"
        lw = 2.2 if bool(group["is_recommended"].iloc[0]) else 1.6
        ax.plot(group["target_w0_um"], group["tau_min_at_budget"], "-o", lw=lw, label=label)

    ax.axhline(tau_0, color="black", linestyle="--", lw=1.2, label=f"tau_0 = {tau_0:g}")
    ax.text(
        0.02,
        0.96,
        f"F_budget = {finesse_budget:.6f}\nFor continuous M={int(config['M'])}, tau_min = F_budget / M\nThis stays flat vs w0.",
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=8.7,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.92},
    )
    ax.set_xlabel("Target w0 (um)")
    ax.set_ylabel("tau_min at finesse budget")
    ax.set_title("Tau feasibility does not worsen when geometry is scaled up")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=8, loc="lower right")

    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def summarize_size_limited_case(solutions_df: pd.DataFrame, size_limits: dict[str, Any]) -> str:
    if size_limits.get("L_max_mm") is None and size_limits.get("R_max_mm") is None:
        lines = [
            "- 当前未设置 `L_max_mm/R_max_mm`。",
            "- 在自由缩放几何下，大 `w0` 并非被 `tau` 理论禁止；限制来自器件尺寸而非频域判据本身。",
        ]
        return "\n".join(lines)

    lines = [
        f"- 已设置尺寸上限：`L_max_mm={size_limits.get('L_max_mm')}`，`R_max_mm={size_limits.get('R_max_mm')}`。",
    ]
    for branch_m, group in solutions_df.groupby("branch_m"):
        group = group.sort_values("target_w0_um")
        feasible_group = group.loc[group["overall_feasible"]]
        if feasible_group.empty:
            first_failure = group.iloc[0]
            lines.append(
                f"- `m={int(branch_m)}` 分支在最小扫描点就失败；首个失效约束：{first_failure['failure_reason']}。"
            )
        else:
            max_row = feasible_group.iloc[-1]
            infeasible_after = group.loc[group["target_w0_um"] > max_row["target_w0_um"]]
            if infeasible_after.empty:
                lines.append(
                    f"- `m={int(branch_m)}` 分支在当前扫描上限内仍可行，最大可行 `w0={max_row['target_w0_um']:.1f} um`。"
                )
            else:
                first_failure = infeasible_after.iloc[0]
                lines.append(
                    f"- `m={int(branch_m)}` 分支最大可行 `w0={max_row['target_w0_um']:.1f} um`；再增大时首先受 `{first_failure['failure_reason']}` 限制。"
                )
    return "\n".join(lines)


def branch_solution_snapshot(solutions_df: pd.DataFrame, branch_m: int, target_w0_um: float) -> dict[str, Any] | None:
    subset = solutions_df.loc[
        (solutions_df["branch_m"] == branch_m) & np.isclose(solutions_df["target_w0_um"], target_w0_um, atol=1e-9)
    ]
    if subset.empty:
        return None
    return subset.iloc[0].to_dict()


def build_report(config: dict[str, Any], baseline_df: pd.DataFrame, branch_df: pd.DataFrame, solutions_df: pd.DataFrame) -> str:
    baseline = baseline_df.iloc[0]
    recommended_branch = branch_df.loc[branch_df["is_recommended"]].iloc[0]
    recommended_solutions = solutions_df.loc[solutions_df["is_recommended"]].sort_values("target_w0_um")
    size_limits = config.get("size_limits", {})

    snap_100 = branch_solution_snapshot(solutions_df, int(recommended_branch["branch_m"]), 100.0)
    snap_200 = branch_solution_snapshot(solutions_df, int(recommended_branch["branch_m"]), 200.0)
    snap_500 = branch_solution_snapshot(solutions_df, int(recommended_branch["branch_m"]), 500.0)

    lines = [
        "# 平行准直光设计腔仿真报告",
        "",
        "## 1. 当前腔基线",
        f"- 当前输入基线腔：`L={baseline['L_mm']:.6f} mm`，`R={baseline['R_mm']:.6f} mm`。",
        f"- 对应晶体腔本征光腰：`w0={baseline['w0_medium_um']:.3f} um`。",
        f"- 真空波长口径下的对照值：`w0_vac={baseline['w0_vacuum_um']:.3f} um`。",
        f"- 当前几何比：`L/R={baseline['L_over_R']:.6f}`，对应 `k={baseline['k_from_geometry']:.6f}`。",
        f"- 对连续 `M={int(config['M'])}` 模集合，当前工作点的 `s_min={baseline['s_min_for_continuous_M']:.6f}`，`tau_min={baseline['tau_min_at_budget']:.6f}`。",
        "",
        "## 2. 解析分支与 tau 判据",
        f"- 连续满载 `S_{int(config['M'])}` 的解析极值统一满足：`s_min=1/M={1/int(config['M']):.6f}`，`F_min=tau_0*M={float(config['tau_0']) * int(config['M']):.6f}`。",
        f"- 当前精细度预算 `F_budget={float(config['finesse_budget']):.6f}` 给出 `tau_min=F_budget/M={float(config['finesse_budget']) / int(config['M']):.6f}`。",
        f"- 非冗余分支共 {len(branch_df)} 个：`m={', '.join(str(int(v)) for v in branch_df['branch_m'])}`。",
        f"- 默认推荐分支是 `m={int(recommended_branch['branch_m'])}`，因为它的 `L/R={recommended_branch['L_over_R']:.6f}` 最接近 `0.5`，同等 `s_min` 下所需几何尺寸最小。",
        "",
        "## 3. 逆向设计结论",
        "- 在本模型里，`tau` 可行性只由 `M、tau_0、F_budget` 决定，不会因为把 `w0` 做大而自动变差。",
        "- 因此，大 `w0` 是否可做，关键不是频域理论本身，而是几何尺寸是否还能接受。",
    ]
    if snap_100 is not None:
        lines.append(
            f"- 推荐分支 `m={int(recommended_branch['branch_m'])}` 下，`w0=0.1 mm` 时约需 `L={snap_100['L_mm']:.3f} mm`，`R={snap_100['R_mm']:.3f} mm`。"
        )
    if snap_200 is not None:
        lines.append(
            f"- 同一分支下，`w0=0.2 mm` 时约需 `L={snap_200['L_mm']:.3f} mm`，`R={snap_200['R_mm']:.3f} mm`。"
        )
    if snap_500 is not None:
        lines.append(
            f"- 当 `w0=0.5 mm` 时，约需 `L={snap_500['L_mm']:.3f} mm`，`R={snap_500['R_mm']:.3f} mm`，已进入米级腔体量级。"
        )
    lines.extend(
        [
            "",
            "## 4. 尺寸约束解释",
            summarize_size_limited_case(solutions_df, size_limits),
            "",
            "## 5. 如何理解“近平行准直”",
            "- 本脚本不把“近平行”硬编码成单一阈值，而是同时看 `w0`、`zR` 和发散半角 `theta_div`。",
            "- `w0` 越大，`zR` 越长、`theta_div` 越小，光束越接近平行准直；但所需 `L、R` 会按平方量级迅速变大。",
            "- 因此，结论应该表述为：在连续 9 模和当前 `tau_0=3`、`F_budget≈32.32` 条件下，大光腰腔在理论上仍可设计，但工程上是否现实主要由腔体尺寸决定，而不是由 `tau` 判据否决。",
            "",
            "## 6. 输出文件",
            "- `current_cavity_baseline.csv`：当前实测腔的本征光腰与工作点复算。",
            "- `analytic_branch_summary.csv`：连续满载解析分支摘要。",
            "- `inverse_design_solutions.csv`：不同目标 `w0` 下的逆向设计结果表。",
            "- `w0_vs_geometry.png / divergence_vs_w0.png / tau_margin_vs_w0.png`：几何尺寸、准直程度和 `tau` 裕量图。",
        ]
    )
    return "\n".join(lines) + "\n"


def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def run_simulation(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_df = baseline_metrics(config)
    branch_specs = enumerate_branches(config)
    branch_df = branch_summary_dataframe(branch_specs)
    solutions_df = compute_inverse_design_rows(config, branch_specs)

    save_dataframe(baseline_df, output_dir / "current_cavity_baseline.csv")
    save_dataframe(branch_df, output_dir / "analytic_branch_summary.csv")
    save_dataframe(solutions_df, output_dir / "inverse_design_solutions.csv")

    plot_w0_vs_geometry(output_dir / "w0_vs_geometry.png", baseline_df, solutions_df)
    plot_divergence_vs_w0(output_dir / "divergence_vs_w0.png", solutions_df)
    plot_tau_margin_vs_w0(output_dir / "tau_margin_vs_w0.png", config, solutions_df)

    report_text = build_report(config, baseline_df, branch_df, solutions_df)
    (output_dir / "design_report.md").write_text(report_text, encoding="utf-8")

    return {
        "baseline_df": baseline_df,
        "branch_df": branch_df,
        "solutions_df": solutions_df,
        "report_text": report_text,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plane-concave cavity inverse design for larger waist / quasi-collimated operation.")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the JSON config file. Defaults to default_design_config.json in this folder.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for CSV/plot/report outputs. Defaults to ./outputs beside the script.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config.resolve())
    results = run_simulation(config, args.output_dir.resolve())
    baseline = results["baseline_df"].iloc[0]
    recommended_branch = results["branch_df"].loc[results["branch_df"]["is_recommended"]].iloc[0]
    print(f"Config: {args.config.resolve()}")
    print(f"Outputs: {args.output_dir.resolve()}")
    print(
        "Baseline cavity: "
        f"w0_medium={baseline['w0_medium_um']:.3f} um, "
        f"w0_vacuum={baseline['w0_vacuum_um']:.3f} um, "
        f"k={baseline['k_from_geometry']:.6f}"
    )
    print(
        "Recommended branch: "
        f"m={int(recommended_branch['branch_m'])}, "
        f"L/R={recommended_branch['L_over_R']:.6f}, "
        f"tau_min={recommended_branch['tau_min_at_budget']:.6f}"
    )


if __name__ == "__main__":
    main()
