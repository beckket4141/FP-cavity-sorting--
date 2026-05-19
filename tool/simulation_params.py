"""
Extract and verify all simulation-relevant parameters from the thesis.
This serves as the authoritative parameter source for any subsequent simulations.

Key model equations (referenced from main.tex / supplement.tex):
  - Resonance: nu_{q,N} = FSR * (q + N * phi/pi)
  - Gouy step: k = phi/pi = (1/pi) * arccos(sqrt(1 - L/R))
  - Folded position: pos(N) = ((N-1)*k) mod 1
  - Spacing: s_ij = min(|pos_i - pos_j|, 1 - |pos_i - pos_j|)
  - Resolvability: tau_min = F * s_min
  - Capacity boundary: M <= floor(F / tau_0)
  - Airy transmittance: T(nu) = 1 / (1 + (2F/pi)^2 * sin^2(pi*nu/FSR))
"""
import math
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ============================================================
# Canonical parameters extracted from the thesis
# ============================================================
THESIS_PARAMS = {
    # --- Wavelength and cavity ---
    "wavelength_nm": 795.0,          # operating wavelength
    "FSR_GHz": 9.915,                # free spectral range (measured)
    "FSR_GHz_uncertainty": 0.004,
    "finesse": 32.21,                # measured finesse
    "finesse_uncertainty": 0.19,
    "finesse_threshold": 27.0,       # minimum finesse (M * tau_0)

    # --- Design geometry ---
    "k_star": 2/9,                   # optimal normalized Gouy step
    "k_star_decimal": 0.2222222222222222,
    "k_measured": 0.2228,            # fitted from experiment
    "k_measured_uncertainty": 0.0003,
    "LR_star": math.sin(math.pi * 2/9)**2,  # ~0.4132
    "LR_effective": 0.4146,          # fitted from experiment
    "m_branch": 2,                   # coprime branch m=2
    "M_target": 9,                   # number of target modes

    # --- Target mode set ---
    "p_values": [0],                 # radial index (p=0 subspace)
    "l_values": list(range(0, 9)),   # azimuthal: l = 0,1,...,8
    "N_values": [2*p + abs(l) + 1 for l in range(0, 9) for p in [0]],
    "Delta_ord": 1,                  # consecutive (uniform step = 1)

    # --- Design threshold ---
    "tau_0": 3.0,                    # minimum linewidth separation
    "s_min_geometric": 1/9,          # = 1/M for uniform spacing
    "tau_min_measured": 3.50,        # ~ F * s_min_meas

    # --- Performance bounds (at tau_0 = 3) ---
    "ER_sum_conservative_dB": 10.47,  # large-M limit bound
    "eta_sort_conservative_pct": 91.76,
    "ER_sum_M9_airy_dB": 10.53,      # exact M=9 at F=27
    "eta_sort_M9_airy_pct": 91.9,
    "ER_sum_M9_measured_dB": 12.04,  # exact M=9 at F=32.21

    # --- Measured performance ---
    "eta_sort_measured_mean_pct": 93.19,
    "eta_sort_measured_ci95_pct": 0.37,
    "eta_sort_range_pct": [92.08, 94.41],
    "ER_sum_measured_mean_dB": 11.41,
    "ER_sum_measured_std_dB": 0.25,
    "ER_worst_mode_dB": 10.66,
    "T_peak_mean": 0.88,              # mean single-mode peak transmittance

    # --- Linewidth ---
    "FWHM_MHz": 9.915e3 / 32.21,     # FSR / F ~ 307.9 MHz
    "FWHM_MHz_approx": 307.9,

    # --- Measured peak deviation ---
    "peak_deviation_MHz": 28.0,       # mean deviation from predictions
    "l9_offset_MHz": 23.0,            # l=9 return offset from l=0
    "l9_offset_pct_FSR": 0.23,        # 0.23% of FSR
}


# ============================================================
# Core simulation functions
# ============================================================

def gouy_step_from_LR(L_over_R):
    """Eq. (2): k = (1/pi) * arccos(sqrt(1 - L/R))"""
    if not 0 <= L_over_R <= 1:
        raise ValueError(f"L/R = {L_over_R} is outside [0,1] for plane-concave")
    return math.acos(math.sqrt(1 - L_over_R)) / math.pi


def LR_from_gouy_step(k):
    """Inverse: L/R = sin^2(pi * k)"""
    return math.sin(math.pi * k) ** 2


def folded_position(N, k):
    """Eq. (4-5): pos(N) = ((N-1)*k) mod 1"""
    return ((N - 1) * k) % 1.0


def circular_spacing(pos_i, pos_j):
    """Eq. (6): s_ij = min(|pos_i - pos_j|, 1 - |pos_i - pos_j|)"""
    d = abs(pos_i - pos_j)
    return min(d, 1.0 - d)


def min_spacing(N_orders, k):
    """Eq. (7): s_min = min_{i<j} s_ij for a target set."""
    positions = [folded_position(N, k) for N in N_orders]
    s_min = 1.0
    worst_pair = None
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            s = circular_spacing(positions[i], positions[j])
            if s < s_min:
                s_min = s
                worst_pair = (N_orders[i], N_orders[j])
    return s_min, worst_pair, positions


def airy_transmittance(delta_nu_over_FSR, finesse):
    """Eq. (11): Airy function for detuning delta_nu (in units of FSR)."""
    arg = math.pi * delta_nu_over_FSR
    return 1.0 / (1.0 + (2.0 * finesse / math.pi) ** 2 * math.sin(arg) ** 2)


def crosstalk_sum_M(M, finesse):
    """Eq. (7, main text) / Supp A.1: P_noise for M equally spaced modes."""
    a = (2.0 * finesse / math.pi) ** 2
    total = 0.0
    for n in range(1, M):
        total += airy_transmittance(n / M, finesse)
    return total


def crosstalk_sum_closed(M, finesse):
    """Closed-form from Supp Eq. (S4-S5)."""
    import math
    a = (2.0 * finesse / math.pi) ** 2
    q = (math.sqrt(1 + a) - 1) / (math.sqrt(1 + a) + 1)
    P = M / math.sqrt(1 + a) * (1 + q**M) / (1 - q**M) - 1.0
    return P


def crosstalk_limit(tau_0):
    """Eq. (8): P_noise^inf = pi/(2*tau_0) * coth(pi/(2*tau_0)) - 1"""
    x = math.pi / (2.0 * tau_0)
    return x / math.tanh(x) - 1.0


def er_from_crosstalk(P_noise):
    """ER_sum = 10 * log10(1 / P_noise)"""
    return 10.0 * math.log10(1.0 / P_noise)


def eta_from_crosstalk(P_noise):
    """eta_sort = 1 / (1 + P_noise)"""
    return 1.0 / (1.0 + P_noise)


def design_blueprint(M, tau_0=3.0, branch_strategy="lowest_sensitivity"):
    """
    Generate the design blueprint for a consecutive target set of size M.
    Returns: {M, finesse_min, m_branch, k_star, LR_star, ER, eta}
    """
    F_min = M * tau_0

    # Find coprime branch
    candidates = []
    for m in range(1, M):
        if math.gcd(m, M) == 1:
            k = m / M
            LR = math.sin(math.pi * k) ** 2
            # sensitivity: dk/d(LR) = 1 / (2*pi*sqrt(LR*(1-LR)))
            sens = 1.0 / (2.0 * math.pi * math.sqrt(LR * (1 - LR)))
            candidates.append((m, k, LR, sens))

    if branch_strategy == "lowest_sensitivity":
        candidates.sort(key=lambda x: x[3])
    else:
        candidates.sort(key=lambda x: x[2])  # by LR proximity to 0.5

    best = candidates[0]
    P = crosstalk_sum_closed(M, F_min)
    ER = er_from_crosstalk(P)
    eta = eta_from_crosstalk(P) * 100

    return {
        "M": M,
        "finesse_min": F_min,
        "m_branch": best[0],
        "k_star": best[1],
        "LR_star": best[2],
        "sensitivity": best[3],
        "ER_sum_dB": round(ER, 2),
        "eta_sort_pct": round(eta, 1),
        "num_coprime_branches": len(candidates),
    }


# ============================================================
# Verification and display
# ============================================================

def verify_params():
    """Check that computed values match thesis-reported values."""
    p = THESIS_PARAMS
    results = []

    # k* matches LR*
    k_calc = gouy_step_from_LR(p["LR_star"])
    ok_k = abs(k_calc - p["k_star"]) < 1e-12
    results.append(("k* <-> L/R* consistency", ok_k, k_calc))

    # s_min = 1/M
    N_set = list(range(1, p["M_target"] + 1))
    smin, pair, positions = min_spacing(N_set, p["k_star"])
    ok_smin = abs(smin - 1/p["M_target"]) < 1e-12
    results.append(("s_min = 1/M at k*", ok_smin, smin))

    # tau_min at threshold
    tau_min = p["finesse_threshold"] * smin
    ok_tau = abs(tau_min - p["tau_0"]) < 1e-12
    results.append(("tau_min = tau_0 at F=F_min", ok_tau, tau_min))

    # FWHM
    fwhm = p["FSR_GHz"] * 1e3 / p["finesse"]
    ok_fwhm = abs(fwhm - p["FWHM_MHz_approx"]) < 1.0
    results.append(("FWHM ≈ 307.9 MHz", ok_fwhm, fwhm))

    # Crosstalk conservative bound
    P_inf = crosstalk_limit(p["tau_0"])
    ER_inf = er_from_crosstalk(P_inf)
    ok_ER = abs(ER_inf - p["ER_sum_conservative_dB"]) < 0.01
    results.append(("ER_sum^(inf) conservative bound", ok_ER, ER_inf))

    # Closed-form M=9 at F_min
    P9 = crosstalk_sum_closed(9, 27.0)
    ER9 = er_from_crosstalk(P9)
    ok_ER9 = abs(ER9 - p["ER_sum_M9_airy_dB"]) < 0.01
    results.append(("ER_sum^(9) at F=27", ok_ER9, ER9))

    return results


def print_params():
    """Pretty-print all canonical parameters."""
    print("=" * 70)
    print("  THESIS SIMULATION PARAMETERS")
    print("  Spectral-Folding Model for LG Mode Sorting in FP Cavities")
    print("=" * 70)

    sections = {
        "Cavity & Wavelength": [
            "wavelength_nm", "FSR_GHz", "finesse", "finesse_threshold",
            "FWHM_MHz_approx",
        ],
        "Design Geometry (M=9)": [
            "k_star", "k_measured", "LR_star", "LR_effective",
            "m_branch", "M_target",
        ],
        "Target Modes": ["p_values", "l_values", "Delta_ord"],
        "Resolvability Criterion": [
            "tau_0", "s_min_geometric", "tau_min_measured",
        ],
        "Performance Bounds": [
            "ER_sum_conservative_dB", "eta_sort_conservative_pct",
            "ER_sum_M9_airy_dB", "eta_sort_M9_airy_pct",
            "ER_sum_M9_measured_dB",
        ],
        "Measured Performance": [
            "eta_sort_measured_mean_pct", "eta_sort_range_pct",
            "ER_sum_measured_mean_dB", "ER_worst_mode_dB",
            "T_peak_mean",
        ],
        "Peak Deviations": [
            "peak_deviation_MHz", "l9_offset_MHz", "l9_offset_pct_FSR",
        ],
    }

    for section, keys in sections.items():
        print(f"\n  [{section}]")
        for key in keys:
            val = THESIS_PARAMS.get(key)
            if val is not None:
                if isinstance(val, float):
                    print(f"    {key:35s} = {val:.6g}")
                else:
                    print(f"    {key:35s} = {val}")


def print_verification():
    """Run and display parameter consistency verification."""
    print("\n" + "=" * 70)
    print("  PARAMETER VERIFICATION")
    print("=" * 70)
    all_ok = True
    for name, ok, val in verify_params():
        status = "OK" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"  [{status}] {name}: {val:.6g}")
    if all_ok:
        print("\n  All checks passed.")
    else:
        print("\n  Some checks FAILED - review parameters.")


def print_blueprint_table(M_max=100):
    """Print the design blueprint table for various M (replicates Table 2)."""
    print("\n" + "=" * 70)
    print("  DESIGN BLUEPRINT (tau_0 = 3)")
    print("=" * 70)
    print(f"  {'M':>4s}  {'F_min':>6s}  {'m':>3s}  {'k*':>8s}  {'(L/R)*':>8s}  {'ER(dB)':>8s}  {'eta(%)':>8s}")
    print(f"  {'-'*4}  {'-'*6}  {'-'*3}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}")

    M_list = [4, 9, 15, 30, 50, 100]
    for M in M_list:
        bp = design_blueprint(M)
        print(
            f"  {bp['M']:4d}  {bp['finesse_min']:6.0f}  {bp['m_branch']:3d}  "
            f"{bp['k_star']:8.4f}  {bp['LR_star']:8.4f}  "
            f"{bp['ER_sum_dB']:8.2f}  {bp['eta_sort_pct']:8.1f}"
        )


if __name__ == "__main__":
    print_params()
    print_verification()
    print_blueprint_table()
