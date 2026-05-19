from __future__ import annotations

import math
import sys
from dataclasses import dataclass, replace
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from analysis_common import analytic_peak_families, ensure_dir, local_platform_formula, lr_from_k, write_csv


OUTPUT_ROOT = ensure_dir(BASE_DIR / "outputs")
N_SCAN_VALUES = list(range(5, 51))
REPRESENTATIVE_N_VALUES = [9, 12, 15, 30, 50]


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    radius_mm: float
    vacuum_wavelength_mm: float
    refractive_index: float
    finesse: float
    tau0: float
    L_min_mm: float
    w0_experimental_min_um: float
    w0_comfortable_min_um: float
    w_curved_max_um: float
    platform_min_L_mm: float


@dataclass(frozen=True)
class GeometryMetrics:
    n_modes: int
    m: int
    k_star: float
    lr_star: float
    L_mm: float
    zR_mm: float
    medium_wavelength_mm: float
    w0_um: float
    w_curved_um: float
    g2: float
    lr_edge_margin: float
    hemispherical_gap_mm: float


@dataclass(frozen=True)
class QualityMetrics:
    delta: float
    tau_eff: float
    tau_margin: float
    rho: float
    peak_headroom_ratio: float
    platform_height_margin: float
    platform_exists: bool
    platform_width_k: float
    platform_width_lr: float
    platform_width_L_mm: float
    pairwise_er_db: float
    conservative_er_db: float


CURRENT_PLATFORM = Scenario(
    name="CURRENT_PLATFORM",
    description="Current monolithic crystal plane-concave hardware and nominal quality threshold",
    radius_mm=25.0,
    vacuum_wavelength_mm=795.0e-6,
    refractive_index=1.453371,
    finesse=29.8,
    tau0=3.0,
    L_min_mm=3.0,
    w0_experimental_min_um=47.0,
    w0_comfortable_min_um=50.0,
    w_curved_max_um=180.0,
    platform_min_L_mm=0.10,
)

COMPARISON_RELAXED = Scenario(
    name="COMPARISON_RELAXED",
    description="Relaxed comparison window with the same monolithic crystal cavity and tau target",
    radius_mm=25.0,
    vacuum_wavelength_mm=795.0e-6,
    refractive_index=1.453371,
    finesse=29.8,
    tau0=3.0,
    L_min_mm=2.5,
    w0_experimental_min_um=47.0,
    w0_comfortable_min_um=50.0,
    w_curved_max_um=220.0,
    platform_min_L_mm=0.05,
)

SCENARIOS = [CURRENT_PLATFORM, COMPARISON_RELAXED]


def rho_value(finesse: float, n_modes: int, tau0: float) -> float:
    return float(finesse) / (float(n_modes) * float(tau0))


def required_finesse(n_modes: int, tau0: float, rho: float) -> float:
    return float(rho) * float(n_modes) * float(tau0)


def symmetric_finesse_from_reflectivity(reflectivity: float) -> float:
    reflectivity = float(reflectivity)
    if not 0.0 < reflectivity < 1.0:
        raise ValueError("reflectivity must lie strictly between 0 and 1")
    return math.pi * math.sqrt(reflectivity) / (1.0 - reflectivity)


def reflectivity_from_symmetric_finesse(finesse: float) -> float:
    finesse = float(finesse)
    if finesse <= 0.0:
        raise ValueError("finesse must be positive")
    sqrt_reflectivity = (-math.pi + math.sqrt(math.pi**2 + 4.0 * finesse**2)) / (2.0 * finesse)
    return sqrt_reflectivity**2


def finesse_scale_from_relative_error(rel_error: float) -> float:
    scale = 1.0 + float(rel_error)
    if scale <= 0.0:
        raise ValueError("relative error makes finesse non-positive")
    return scale


def rho_after_finesse_scale(rho_nominal: float, finesse_scale: float) -> float:
    return float(rho_nominal) * float(finesse_scale)


def required_nominal_rho(rho_actual_floor: float, worst_case_finesse_shortfall: float) -> float:
    worst_case_finesse_shortfall = float(worst_case_finesse_shortfall)
    if worst_case_finesse_shortfall < 0.0:
        raise ValueError("worst-case finesse shortfall must be non-negative")
    actual_scale_floor = 1.0 - worst_case_finesse_shortfall
    if actual_scale_floor <= 0.0:
        raise ValueError("worst-case finesse shortfall must be smaller than 1")
    return float(rho_actual_floor) / actual_scale_floor


def ceiling_with_tolerance(value: float, tol: float = 1.0e-9) -> int:
    return math.ceil(float(value) - tol)


def peak_headroom_ratio(rho: float) -> float:
    return 1.0 - 1.0 / float(rho)


def platform_height_margin(n_modes: int, finesse: float, tau0: float) -> float:
    return 1.0 / float(n_modes) - float(tau0) / float(finesse)


def scenario_with_quality(scenario: Scenario, finesse: float, tau0: float) -> Scenario:
    return replace(scenario, finesse=float(finesse), tau0=float(tau0))


def branch_geometry_metrics(
    n_modes: int,
    m: int,
    radius_mm: float,
    vacuum_wavelength_mm: float,
    refractive_index: float,
) -> GeometryMetrics:
    k_star = m / n_modes
    lr_star = lr_from_k(k_star)
    L_mm = radius_mm * lr_star
    zR_mm = math.sqrt(L_mm * (radius_mm - L_mm))
    medium_wavelength_mm = float(vacuum_wavelength_mm) / float(refractive_index)
    w0_mm = math.sqrt(medium_wavelength_mm / math.pi * zR_mm)
    w_curved_mm = w0_mm * math.sqrt(1.0 + (L_mm / zR_mm) ** 2)
    return GeometryMetrics(
        n_modes=n_modes,
        m=m,
        k_star=k_star,
        lr_star=lr_star,
        L_mm=L_mm,
        zR_mm=zR_mm,
        medium_wavelength_mm=medium_wavelength_mm,
        w0_um=w0_mm * 1.0e3,
        w_curved_um=w_curved_mm * 1.0e3,
        g2=1.0 - lr_star,
        lr_edge_margin=min(lr_star, 1.0 - lr_star),
        hemispherical_gap_mm=radius_mm - L_mm,
    )


def classify_w0_band(w0_um: float, scenario: Scenario) -> str:
    if scenario.w0_comfortable_min_um < scenario.w0_experimental_min_um:
        raise ValueError("w0 comfortable threshold must not be smaller than experimental threshold")
    if w0_um >= scenario.w0_comfortable_min_um:
        return "comfortable"
    if w0_um >= scenario.w0_experimental_min_um:
        return "experimental_ok"
    return "high_risk"


def geometry_warning_reasons(geometry: GeometryMetrics, scenario: Scenario) -> tuple[str, list[str]]:
    w0_band = classify_w0_band(geometry.w0_um, scenario)
    reasons: list[str] = []
    if w0_band == "experimental_ok":
        reasons.append("w0_experimental_ok")
    elif w0_band == "high_risk":
        reasons.append("w0_high_risk")
    return w0_band, reasons


def conservative_noise_sum(n_modes: int, tau: float) -> float:
    left_neighbors = (n_modes - 1) // 2
    right_neighbors = (n_modes - 1) - left_neighbors
    noise = 0.0
    for k in range(1, left_neighbors + 1):
        noise += 1.0 / (1.0 + 4.0 * (k * tau) ** 2)
    for k in range(1, right_neighbors + 1):
        noise += 1.0 / (1.0 + 4.0 * (k * tau) ** 2)
    return noise


def quality_metrics(n_modes: int, m: int, scenario: Scenario) -> QualityMetrics:
    delta = scenario.tau0 / scenario.finesse
    tau_eff = scenario.finesse / n_modes
    tau_margin = tau_eff - scenario.tau0
    rho = rho_value(scenario.finesse, n_modes, scenario.tau0)
    headroom_ratio = peak_headroom_ratio(rho)
    height_margin = platform_height_margin(n_modes, scenario.finesse, scenario.tau0)
    interval = local_platform_formula(n_modes, m, delta)
    if interval is None:
        width_k = 0.0
        width_lr = 0.0
        width_L_mm = 0.0
        platform_exists = False
    else:
        width_k = interval.width_k
        width_lr = interval.width_lr
        width_L_mm = scenario.radius_mm * width_lr
        platform_exists = True
    pairwise_er_db = 10.0 * math.log10(1.0 + 4.0 * tau_eff**2)
    conservative_er_db = 10.0 * math.log10(1.0 / conservative_noise_sum(n_modes, tau_eff))
    return QualityMetrics(
        delta=delta,
        tau_eff=tau_eff,
        tau_margin=tau_margin,
        rho=rho,
        peak_headroom_ratio=headroom_ratio,
        platform_height_margin=height_margin,
        platform_exists=platform_exists,
        platform_width_k=width_k,
        platform_width_lr=width_lr,
        platform_width_L_mm=width_L_mm,
        pairwise_er_db=pairwise_er_db,
        conservative_er_db=conservative_er_db,
    )


def geometry_fail_reasons(geometry: GeometryMetrics, scenario: Scenario) -> list[str]:
    reasons: list[str] = []
    if geometry.L_mm < scenario.L_min_mm:
        reasons.append("short_cavity")
    if geometry.w_curved_um > scenario.w_curved_max_um:
        reasons.append("large_curved_mirror_spot")
    return reasons


def quality_fail_reasons(quality: QualityMetrics, scenario: Scenario) -> list[str]:
    reasons: list[str] = []
    if quality.tau_eff < scenario.tau0 or not quality.platform_exists:
        reasons.append("below_tau_threshold")
    if quality.platform_width_L_mm < scenario.platform_min_L_mm:
        reasons.append("platform_too_narrow")
    return reasons


def analytic_branch_rows(
    scenario: Scenario,
    *,
    n_values: list[int] | None = None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    scan_values = n_values if n_values is not None else N_SCAN_VALUES
    for n_modes in scan_values:
        for peak in analytic_peak_families(n_modes, k_upper=0.5):
            geometry = branch_geometry_metrics(
                n_modes,
                peak.m,
                scenario.radius_mm,
                scenario.vacuum_wavelength_mm,
                scenario.refractive_index,
            )
            quality = quality_metrics(n_modes, peak.m, scenario)
            w0_band, g_warning_reasons = geometry_warning_reasons(geometry, scenario)
            g_reasons = geometry_fail_reasons(geometry, scenario)
            q_reasons = quality_fail_reasons(quality, scenario)
            geometry_pass = not g_reasons
            geometry_warning = geometry_pass and bool(g_warning_reasons)
            geometry_screen_status = "hard_fail" if not geometry_pass else ("warning" if geometry_warning else "pass")
            quality_pass = not q_reasons
            rows.append(
                {
                    "scenario": scenario.name,
                    "finesse": f"{scenario.finesse:.12f}",
                    "tau0": f"{scenario.tau0:.12f}",
                    "vacuum_wavelength_nm": f"{scenario.vacuum_wavelength_mm * 1.0e6:.6f}",
                    "refractive_index": f"{scenario.refractive_index:.12f}",
                    "medium_wavelength_nm": f"{geometry.medium_wavelength_mm * 1.0e6:.6f}",
                    "w0_experimental_min_um": f"{scenario.w0_experimental_min_um:.6f}",
                    "w0_comfortable_min_um": f"{scenario.w0_comfortable_min_um:.6f}",
                    "N": n_modes,
                    "m": peak.m,
                    "k_star": f"{geometry.k_star:.12f}",
                    "lr_star": f"{geometry.lr_star:.12f}",
                    "L_mm": f"{geometry.L_mm:.9f}",
                    "zR_mm": f"{geometry.zR_mm:.9f}",
                    "w0_um": f"{geometry.w0_um:.6f}",
                    "w_curved_um": f"{geometry.w_curved_um:.6f}",
                    "g2": f"{geometry.g2:.12f}",
                    "lr_edge_margin": f"{geometry.lr_edge_margin:.12f}",
                    "hemispherical_gap_mm": f"{geometry.hemispherical_gap_mm:.9f}",
                    "delta": f"{quality.delta:.12f}",
                    "tau_eff": f"{quality.tau_eff:.12f}",
                    "tau_margin": f"{quality.tau_margin:.12f}",
                    "rho": f"{quality.rho:.12f}",
                    "peak_headroom_ratio": f"{quality.peak_headroom_ratio:.12f}",
                    "platform_height_margin": f"{quality.platform_height_margin:.12f}",
                    "platform_exists": "yes" if quality.platform_exists else "no",
                    "platform_width_k": f"{quality.platform_width_k:.12f}",
                    "platform_width_lr": f"{quality.platform_width_lr:.12f}",
                    "platform_width_L_mm": f"{quality.platform_width_L_mm:.9f}",
                    "pairwise_er_db": f"{quality.pairwise_er_db:.6f}",
                    "conservative_er_db": f"{quality.conservative_er_db:.6f}",
                    "w0_band": w0_band,
                    "geometry_warning": "yes" if geometry_warning else "no",
                    "geometry_warning_reasons": ";".join(g_warning_reasons) if g_warning_reasons else "pass",
                    "geometry_screen_status": geometry_screen_status,
                    "geometry_pass": "yes" if geometry_pass else "no",
                    "geometry_fail_reasons": ";".join(g_reasons) if g_reasons else "pass",
                    "quality_pass": "yes" if quality_pass else "no",
                    "quality_fail_reasons": ";".join(q_reasons) if q_reasons else "pass",
                    "final_engineering_pass": "yes" if geometry_pass and quality_pass else "no",
                }
            )
    return rows


def scenario_summary_rows(rows: list[dict[str, object]], scenario_name: str) -> list[dict[str, object]]:
    summary_rows: list[dict[str, object]] = []
    for n_modes in N_SCAN_VALUES:
        subset = [row for row in rows if row["scenario"] == scenario_name and int(row["N"]) == n_modes]
        geometry_branches = [row["m"] for row in subset if row["geometry_pass"] == "yes"]
        final_branches = [row["m"] for row in subset if row["final_engineering_pass"] == "yes"]
        geometry_warning_branches = [row["m"] for row in subset if row["geometry_warning"] == "yes"]
        geometry_hard_fail_branches = [row["m"] for row in subset if row["geometry_screen_status"] == "hard_fail"]
        w0_experimental_ok_branches = [row["m"] for row in subset if row["w0_band"] == "experimental_ok"]
        w0_high_risk_branches = [row["m"] for row in subset if row["w0_band"] == "high_risk"]
        w0_comfortable_branches = [row["m"] for row in subset if row["w0_band"] == "comfortable"]
        summary_rows.append(
            {
                "scenario": scenario_name,
                "N": n_modes,
                "math_optimal_branches": len(subset),
                "geometry_engineering_branches": len(geometry_branches),
                "geometry_warning_branches": len(geometry_warning_branches),
                "geometry_hard_fail_branches": len(geometry_hard_fail_branches),
                "w0_comfortable_branches": len(w0_comfortable_branches),
                "w0_experimental_ok_branches": len(w0_experimental_ok_branches),
                "w0_high_risk_branches": len(w0_high_risk_branches),
                "final_engineering_branches": len(final_branches),
                "geometry_branch_list": ",".join(str(m) for m in geometry_branches) if geometry_branches else "-",
                "geometry_warning_branch_list": (
                    ",".join(str(m) for m in geometry_warning_branches) if geometry_warning_branches else "-"
                ),
                "geometry_hard_fail_branch_list": (
                    ",".join(str(m) for m in geometry_hard_fail_branches) if geometry_hard_fail_branches else "-"
                ),
                "w0_comfortable_branch_list": (
                    ",".join(str(m) for m in w0_comfortable_branches) if w0_comfortable_branches else "-"
                ),
                "w0_experimental_ok_branch_list": (
                    ",".join(str(m) for m in w0_experimental_ok_branches) if w0_experimental_ok_branches else "-"
                ),
                "w0_high_risk_branch_list": (
                    ",".join(str(m) for m in w0_high_risk_branches) if w0_high_risk_branches else "-"
                ),
                "final_branch_list": ",".join(str(m) for m in final_branches) if final_branches else "-",
            }
        )
    return summary_rows
