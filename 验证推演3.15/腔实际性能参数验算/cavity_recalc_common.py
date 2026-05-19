from __future__ import annotations

import itertools
import math
import re
import warnings
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, peak_widths, savgol_filter


C_M_PER_S = 299792458.0
EXPECTED_COLUMNS = ["Time_ms", "Lambda_aligned", "Power_uW", "Scan_Direction"]
ROOM_TEMP_C = 20.0
TARGET_TEMP_C = 20.18


@dataclass
class DatasetInfo:
    name: str
    key: str
    root_dir: Path
    raw_dir: Path
    final_dir: Path
    raw_files: Dict[int, Path]
    final_files: Dict[int, Path]
    sanity_file: Optional[Path]


@dataclass
class PeakFitResult:
    dataset_key: str
    l_index: int
    scan_direction: str
    source: str
    candidate_rank: int
    fit_model: str
    selected: bool
    branch_role: str
    lambda_center_nm: float
    lambda_center_err_nm: float
    nu_center_ghz: float
    nu_center_err_ghz: float
    fwhm_nm: float
    fwhm_err_nm: float
    fwhm_ghz: float
    fwhm_err_ghz: float
    peak_power_uw: float
    baseline_uw: float
    amplitude_uw: float
    prominence_uw: float
    r_squared: float
    residual_rms_uw: float
    window_lambda_min_nm: float
    window_lambda_max_nm: float
    peak_index: int


@dataclass
class BranchSelectionResult:
    dataset_key: str
    scan_direction: str
    fsr_hint_ghz: float
    best_k: float
    score: float
    selected_candidates: Dict[int, PeakFitResult]
    pos_meas: Dict[int, float]
    pos_fit: Dict[int, float]
    m_indices: Dict[int, int]
    residuals_ghz: Dict[int, float]


def parse_l_index(path: Path) -> Optional[int]:
    match = re.search(r"l[=_]?(\d+)", path.stem, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def discover_datasets(base_dir: Path) -> Dict[str, DatasetInfo]:
    datasets: Dict[str, DatasetInfo] = {}
    for dataset_dir in sorted(base_dir.iterdir()):
        if not dataset_dir.is_dir():
            continue
        raw_dir = dataset_dir / "原始数据"
        final_dir = dataset_dir / "FSR补全后数据"
        if not raw_dir.exists() or not final_dir.exists():
            continue
        match = re.search(r"(\d+\.\d+)", dataset_dir.name)
        if match:
            key = match.group(1).replace(".", "p") + "mm"
        else:
            key = re.sub(r"\W+", "_", dataset_dir.name)
        raw_files = {
            idx: path
            for path in sorted(raw_dir.glob("*.csv"))
            if (idx := parse_l_index(path)) is not None
        }
        final_files = {
            idx: path
            for path in sorted(final_dir.glob("*.csv"))
            if (idx := parse_l_index(path)) is not None
        }
        sanity_files = [p for p in sorted(final_dir.glob("*.csv")) if parse_l_index(p) is None]
        datasets[key] = DatasetInfo(
            name=dataset_dir.name,
            key=key,
            root_dir=dataset_dir,
            raw_dir=raw_dir,
            final_dir=final_dir,
            raw_files=raw_files,
            final_files=final_files,
            sanity_file=sanity_files[0] if sanity_files else None,
        )
    if not datasets:
        raise FileNotFoundError(f"No datasets discovered under {base_dir}")
    return datasets


def load_scan_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"{path} missing columns: {missing}")
    df = df[EXPECTED_COLUMNS].copy()
    df["Time_ms"] = pd.to_numeric(df["Time_ms"], errors="coerce")
    df["Lambda_aligned"] = pd.to_numeric(df["Lambda_aligned"], errors="coerce")
    df["Power_uW"] = pd.to_numeric(df["Power_uW"], errors="coerce")
    df["Scan_Direction"] = df["Scan_Direction"].astype(str).astype("category")
    df = df.dropna(subset=["Lambda_aligned", "Power_uW", "Scan_Direction"])
    return df


def wavelength_to_frequency(lambda_nm: np.ndarray | float) -> np.ndarray | float:
    return C_M_PER_S / (np.asarray(lambda_nm) * 1e-9)


def lambda_unc_to_nu_unc(lambda_nm: float, lambda_err_nm: float) -> float:
    deriv = C_M_PER_S / ((lambda_nm * 1e-9) ** 2)
    return abs(deriv * lambda_err_nm * 1e-9)


def delta_lambda_to_delta_nu_ghz(lambda_nm: float, delta_lambda_nm: float) -> float:
    nu_err_hz = lambda_unc_to_nu_unc(lambda_nm, delta_lambda_nm)
    return nu_err_hz / 1e9


def _lorentzian_with_offset(x: np.ndarray, offset: float, amplitude: float, x0: float, gamma: float) -> np.ndarray:
    gamma = np.maximum(np.abs(gamma), 1e-15)
    return offset + amplitude / (1.0 + ((x - x0) / gamma) ** 2)


def _gaussian_with_offset(x: np.ndarray, offset: float, amplitude: float, x0: float, sigma: float) -> np.ndarray:
    sigma = np.maximum(np.abs(sigma), 1e-15)
    return offset + amplitude * np.exp(-0.5 * ((x - x0) / sigma) ** 2)


def fit_peak_local(
    x: np.ndarray,
    y: np.ndarray,
    dataset_key: str,
    l_index: int,
    scan_direction: str,
    source: str,
    candidate_rank: int,
    prominence_uw: float,
    peak_index: int,
    model: str = "lorentz",
) -> PeakFitResult:
    if len(x) < 7:
        raise ValueError("Need at least 7 points for local peak fitting.")
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    y_min = float(np.nanmin(y))
    y_max = float(np.nanmax(y))
    x0_guess = float(x[np.nanargmax(y)])
    offset_guess = float(np.nanpercentile(y, 10))
    amplitude_guess = max(y_max - offset_guess, 1e-6)
    span = max(float(x[-1] - x[0]), 1e-9)
    width_guess = max(span / 10.0, 1e-6)
    if model == "gaussian":
        func = _gaussian_with_offset
        p0 = [offset_guess, amplitude_guess, x0_guess, width_guess / 2.355]
        lower = [y_min - abs(amplitude_guess), 0.0, x.min(), 1e-8]
        upper = [y_max, amplitude_guess * 5.0 + 1e-6, x.max(), span]
    else:
        func = _lorentzian_with_offset
        p0 = [offset_guess, amplitude_guess, x0_guess, width_guess / 2.0]
        lower = [y_min - abs(amplitude_guess), 0.0, x.min(), 1e-8]
        upper = [y_max, amplitude_guess * 5.0 + 1e-6, x.max(), span]

    try:
        popt, pcov = curve_fit(
            func,
            x,
            y,
            p0=p0,
            bounds=(lower, upper),
            maxfev=20000,
        )
    except Exception:
        popt = np.asarray(p0, dtype=float)
        pcov = np.full((4, 4), np.nan)

    y_fit = func(x, *popt)
    residual = y - y_fit
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    residual_rms = float(np.sqrt(np.mean(residual**2)))
    if model == "gaussian":
        fwhm_nm = float(2.354820045 * abs(popt[3]))
        fwhm_err_nm = (
            float(2.354820045 * math.sqrt(abs(pcov[3, 3]))) if np.isfinite(pcov[3, 3]) else np.nan
        )
    else:
        fwhm_nm = float(2.0 * abs(popt[3]))
        fwhm_err_nm = float(2.0 * math.sqrt(abs(pcov[3, 3]))) if np.isfinite(pcov[3, 3]) else np.nan
    lambda_center_nm = float(popt[2])
    lambda_center_err_nm = float(math.sqrt(abs(pcov[2, 2]))) if np.isfinite(pcov[2, 2]) else np.nan
    nu_center_ghz = float(wavelength_to_frequency(lambda_center_nm) / 1e9)
    nu_center_err_ghz = delta_lambda_to_delta_nu_ghz(lambda_center_nm, lambda_center_err_nm) if np.isfinite(lambda_center_err_nm) else np.nan
    fwhm_ghz = delta_lambda_to_delta_nu_ghz(lambda_center_nm, fwhm_nm)
    fwhm_err_ghz = delta_lambda_to_delta_nu_ghz(lambda_center_nm, fwhm_err_nm) if np.isfinite(fwhm_err_nm) else np.nan

    return PeakFitResult(
        dataset_key=dataset_key,
        l_index=l_index,
        scan_direction=scan_direction,
        source=source,
        candidate_rank=candidate_rank,
        fit_model=model,
        selected=False,
        branch_role="candidate",
        lambda_center_nm=lambda_center_nm,
        lambda_center_err_nm=lambda_center_err_nm,
        nu_center_ghz=nu_center_ghz,
        nu_center_err_ghz=nu_center_err_ghz,
        fwhm_nm=fwhm_nm,
        fwhm_err_nm=fwhm_err_nm,
        fwhm_ghz=fwhm_ghz,
        fwhm_err_ghz=fwhm_err_ghz,
        peak_power_uw=float(np.max(y_fit)),
        baseline_uw=float(popt[0]),
        amplitude_uw=float(popt[1]),
        prominence_uw=float(prominence_uw),
        r_squared=float(r_squared),
        residual_rms_uw=residual_rms,
        window_lambda_min_nm=float(x.min()),
        window_lambda_max_nm=float(x.max()),
        peak_index=int(peak_index),
    )


def _smooth_signal(y: np.ndarray) -> np.ndarray:
    if len(y) < 11:
        return y.copy()
    win = min(len(y) // 5 * 2 + 1, 401)
    win = max(11, win)
    if win >= len(y):
        win = len(y) - 1 if len(y) % 2 == 0 else len(y)
    if win < 11:
        return y.copy()
    if win % 2 == 0:
        win -= 1
    polyorder = 3 if win >= 7 else 2
    return savgol_filter(y, window_length=win, polyorder=polyorder, mode="interp")


def _candidate_sort_score(item: PeakFitResult) -> Tuple[float, float, float]:
    r2 = item.r_squared if np.isfinite(item.r_squared) else -1.0
    return (item.prominence_uw, r2, item.peak_power_uw)


def find_peak_candidates(
    df_dir: pd.DataFrame,
    dataset_key: str,
    l_index: int,
    scan_direction: str,
    source: str,
    max_candidates: int = 4,
) -> List[PeakFitResult]:
    sub = df_dir.sort_values("Lambda_aligned").reset_index(drop=True)
    x = sub["Lambda_aligned"].to_numpy(dtype=float)
    y = sub["Power_uW"].to_numpy(dtype=float)
    total_span = max(float(x[-1] - x[0]), 1e-6)
    y_smooth = _smooth_signal(y)
    p50 = float(np.nanpercentile(y_smooth, 50))
    p95 = float(np.nanpercentile(y_smooth, 95))
    p995 = float(np.nanpercentile(y_smooth, 99.5))
    spread = max(p95 - p50, p995 - p50, np.std(y_smooth))
    prominence = max(spread * 0.08, np.std(y_smooth) * 0.4, 1e-6)
    distance = max(5, len(y_smooth) // 250)
    peaks, props = find_peaks(y_smooth, prominence=prominence, distance=distance)
    if len(peaks) == 0:
        peaks, props = find_peaks(y_smooth, prominence=max(prominence * 0.5, 1e-7), distance=max(3, distance // 2))
    edge_len = max(5, len(y_smooth) // 4)
    edge_candidates = [int(np.argmax(y_smooth[:edge_len])), len(y_smooth) - edge_len + int(np.argmax(y_smooth[-edge_len:]))]
    if len(peaks):
        peak_set = set(int(p) for p in peaks)
        for edge_peak in edge_candidates:
            if min(abs(edge_peak - p) for p in peak_set) > distance:
                peaks = np.append(peaks, edge_peak)
                peak_set.add(edge_peak)
    else:
        peaks = np.asarray(edge_candidates, dtype=int)
    peaks = np.asarray(sorted(set(int(p) for p in peaks)), dtype=int)
    if len(peaks) == 0:
        peak_index = int(np.argmax(y_smooth))
        peaks = np.asarray([peak_index], dtype=int)
    props = {"prominences": np.asarray([max(float(y_smooth[p] - np.median(y_smooth)), 0.0) for p in peaks])}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        widths = peak_widths(y_smooth, peaks, rel_height=0.5)
    candidates: List[PeakFitResult] = []
    for idx, peak_index in enumerate(peaks):
        width_pts = widths[0][idx] if len(widths[0]) > idx else max(10, len(x) * 0.001)
        center_x = x[peak_index]
        half_width_nm = min(total_span / 8.0, max(total_span / 25.0, 0.0010))
        mask = (x >= center_x - half_width_nm) & (x <= center_x + half_width_nm)
        if mask.sum() < 7:
            pad = int(max(8, min(len(x) // 8, math.ceil(width_pts * 2.0))))
            left = max(0, int(peak_index - pad))
            right = min(len(x), int(peak_index + pad + 1))
            if right - left < 7:
                continue
            local_x = x[left:right]
            local_y = y[left:right]
        else:
            local_x = x[mask]
            local_y = y[mask]
        try:
            lorentz_fit = fit_peak_local(
                local_x,
                local_y,
                dataset_key=dataset_key,
                l_index=l_index,
                scan_direction=scan_direction,
                source=source,
                candidate_rank=idx + 1,
                prominence_uw=float(props["prominences"][idx]) if "prominences" in props else 0.0,
                peak_index=int(peak_index),
                model="lorentz",
            )
            candidates.append(lorentz_fit)
        except Exception:
            continue
    candidates.sort(key=_candidate_sort_score, reverse=True)
    return candidates[:max_candidates]


def circular_distance(a: np.ndarray | float, b: np.ndarray | float) -> np.ndarray | float:
    diff = np.abs(np.asarray(a) - np.asarray(b))
    return np.minimum(diff, 1.0 - diff)


def _score_band_tolerance(min_score: float, floor: float = 1.0e-6, relative: float = 5.0e-2) -> float:
    return float(max(floor, abs(min_score) * relative))


def _contiguous_low_score_band(values: np.ndarray, scores: np.ndarray, threshold: float) -> np.ndarray:
    if values.size == 0 or scores.size == 0:
        return np.asarray([], dtype=float)
    best_idx = int(np.argmin(scores))
    left = best_idx
    right = best_idx
    while left > 0 and scores[left - 1] <= threshold:
        left -= 1
    while right + 1 < scores.size and scores[right + 1] <= threshold:
        right += 1
    return np.asarray(values[left : right + 1], dtype=float)


def _k_candidates_from_positions(l_values: Sequence[int], pos_values: Sequence[float]) -> np.ndarray:
    candidates = {0.221}
    for l_val, pos in zip(l_values, pos_values):
        if l_val <= 0:
            continue
        max_n = int(math.ceil(0.5 * l_val))
        for n in range(max_n + 1):
            k = (pos + n) / l_val
            if 0.0 <= k <= 0.5:
                candidates.add(round(float(k), 12))
    return np.asarray(sorted(candidates), dtype=float)


def fit_k_from_positions(
    l_values: Sequence[int],
    pos_values: Sequence[float],
    pos_sigmas: Optional[Sequence[float]] = None,
    refine: bool = True,
    fit_mask: Optional[Sequence[bool]] = None,
    score_band_floor: float = 1.0e-6,
    score_band_relative: float = 5.0e-2,
) -> Dict[str, Any]:
    l_arr = np.asarray(l_values, dtype=int)
    pos_arr = np.mod(np.asarray(pos_values, dtype=float), 1.0)
    valid = l_arr > 0
    if fit_mask is not None:
        fit_mask_arr = np.asarray(fit_mask, dtype=bool)
        if fit_mask_arr.shape != l_arr.shape:
            raise ValueError("fit_mask must have the same shape as l_values")
        valid &= fit_mask_arr
    l_fit = l_arr[valid]
    pos_fit_arr = pos_arr[valid]
    if len(l_fit) == 0:
        return {
            "k": 0.0,
            "sigma_k": np.nan,
            "predicted": np.zeros_like(pos_arr),
            "residuals": np.zeros_like(pos_arr),
            "fit_l_values": np.asarray([], dtype=int),
            "fit_mode_count": 0,
            "band_min": np.nan,
            "band_max": np.nan,
        }
    weights = np.ones_like(pos_fit_arr)
    if pos_sigmas is not None:
        sigma_arr = np.asarray(pos_sigmas, dtype=float)[valid]
        weights = 1.0 / np.maximum(sigma_arr, 1e-6) ** 2
    k_candidates = _k_candidates_from_positions(l_fit.tolist(), pos_fit_arr.tolist())
    best_k = 0.0
    best_score = float("inf")
    for k_val in k_candidates:
        pred = np.mod(l_fit * k_val, 1.0)
        resid = circular_distance(pos_fit_arr, pred)
        score = float(np.sum(weights * resid**2))
        if score < best_score:
            best_score = score
            best_k = float(k_val)
    if refine:
        refine_grid = np.linspace(max(0.0, best_k - 0.01), min(0.5, best_k + 0.01), 801)
        for k_val in refine_grid:
            pred = np.mod(l_fit * k_val, 1.0)
            resid = circular_distance(pos_fit_arr, pred)
            score = float(np.sum(weights * resid**2))
            if score < best_score:
                best_score = score
                best_k = float(k_val)
    pred_all = np.mod(l_arr * best_k, 1.0)
    resid_all = circular_distance(pos_arr, pred_all)
    grid = np.linspace(max(0.0, best_k - 0.01), min(0.5, best_k + 0.01), 801 if refine else 101)
    scores = []
    for k_val in grid:
        pred = np.mod(l_fit * k_val, 1.0)
        resid = circular_distance(pos_fit_arr, pred)
        scores.append(float(np.sum(weights * resid**2)))
    scores_arr = np.asarray(scores)
    min_score = float(scores_arr.min())
    score_tol = _score_band_tolerance(min_score, floor=score_band_floor, relative=score_band_relative)
    within = _contiguous_low_score_band(grid, scores_arr, min_score + score_tol)
    sigma_k = float(np.std(within)) if len(within) > 1 else np.nan
    return {
        "k": best_k,
        "sigma_k": sigma_k,
        "predicted": pred_all,
        "residuals": resid_all,
        "score": best_score,
        "fit_l_values": l_fit.copy(),
        "fit_mode_count": int(len(l_fit)),
        "band_min": float(within[0]) if len(within) else np.nan,
        "band_max": float(within[-1]) if len(within) else np.nan,
    }


def _estimate_combo_score(
    combo: Sequence[PeakFitResult],
    fsr_hint_ghz: float,
) -> Tuple[float, float, np.ndarray, np.ndarray, np.ndarray]:
    l_values = np.asarray([item.l_index for item in combo], dtype=int)
    nu_values = np.asarray([item.nu_center_ghz for item in combo], dtype=float)
    nu0 = nu_values[0]
    delta = nu_values - nu0
    pos = np.mod(delta / fsr_hint_ghz, 1.0)
    k_result = fit_k_from_positions(l_values, pos, refine=False)
    k_val = float(k_result["k"])
    pos_pred = np.mod(l_values * k_val, 1.0)
    m_vals = np.rint(delta / fsr_hint_ghz - l_values * k_val).astype(int)
    resid_ghz = delta - (m_vals + l_values * k_val) * fsr_hint_ghz
    resid_pos = circular_distance(pos, pos_pred)
    fit_penalty = np.mean([max(0.0, 0.98 - item.r_squared) ** 2 for item in combo])
    score = float(np.mean((resid_ghz / max(fsr_hint_ghz, 1e-9)) ** 2) + np.mean(resid_pos**2) + fit_penalty)
    return score, k_val, pos, pos_pred, resid_ghz


def select_main_branch(
    dataset_key: str,
    scan_direction: str,
    candidates_by_l: Dict[int, List[PeakFitResult]],
    fsr_hint_ghz: float,
) -> BranchSelectionResult:
    l_keys = sorted(candidates_by_l.keys())
    candidate_lists = [candidates_by_l[l_key] for l_key in l_keys]
    if any(len(items) == 0 for items in candidate_lists):
        missing = [l for l in l_keys if len(candidates_by_l[l]) == 0]
        raise ValueError(f"Missing candidates for l={missing} in {dataset_key} {scan_direction}")
    best_combo: Optional[Sequence[PeakFitResult]] = None
    best_score = float("inf")
    best_k = np.nan
    best_pos = np.array([])
    best_pred = np.array([])
    best_resid = np.array([])
    for combo in itertools.product(*candidate_lists):
        score, k_val, pos, pos_pred, resid_ghz = _estimate_combo_score(combo, fsr_hint_ghz)
        if score < best_score:
            best_score = score
            best_combo = combo
            best_k = k_val
            best_pos = pos
            best_pred = pos_pred
            best_resid = resid_ghz
    if best_combo is None:
        raise RuntimeError("Branch selection failed.")
    selected_candidates: Dict[int, PeakFitResult] = {}
    m_indices: Dict[int, int] = {}
    residuals_ghz: Dict[int, float] = {}
    for i, item in enumerate(best_combo):
        selected = PeakFitResult(**{**asdict(item), "selected": True, "branch_role": "selected"})
        selected_candidates[item.l_index] = selected
        delta = item.nu_center_ghz - best_combo[0].nu_center_ghz
        m_indices[item.l_index] = int(round(delta / fsr_hint_ghz - item.l_index * best_k))
        residuals_ghz[item.l_index] = float(best_resid[i])
    pos_meas = {l: float(best_pos[i]) for i, l in enumerate(l_keys)}
    pos_fit = {l: float(best_pred[i]) for i, l in enumerate(l_keys)}
    return BranchSelectionResult(
        dataset_key=dataset_key,
        scan_direction=scan_direction,
        fsr_hint_ghz=float(fsr_hint_ghz),
        best_k=float(best_k),
        score=float(best_score),
        selected_candidates=selected_candidates,
        pos_meas=pos_meas,
        pos_fit=pos_fit,
        m_indices=m_indices,
        residuals_ghz=residuals_ghz,
    )


def estimate_fsr_direct(
    dataset_key: str,
    l0_final_df: pd.DataFrame,
    max_candidates: int = 3,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    direction_results: Dict[str, Any] = {}
    for scan_direction, sub in l0_final_df.groupby("Scan_Direction", observed=False):
        candidates = find_peak_candidates(
            sub,
            dataset_key=dataset_key,
            l_index=0,
            scan_direction=scan_direction,
            source="final",
            max_candidates=max(6, max_candidates),
        )
        if len(candidates) < 2:
            raise ValueError(f"Need at least two l=0 peaks for direct FSR in {dataset_key} {scan_direction}")
        best_pair = None
        best_sep = -1.0
        for peak_a, peak_b in itertools.combinations(candidates, 2):
            sep = abs(peak_a.nu_center_ghz - peak_b.nu_center_ghz)
            if sep > best_sep:
                best_sep = sep
                best_pair = (peak_a, peak_b)
        peaks = sorted(best_pair, key=lambda item: item.lambda_center_nm)
        fsr_ghz = abs(peaks[1].nu_center_ghz - peaks[0].nu_center_ghz)
        fsr_err = math.sqrt(
            sum(
                (item.nu_center_err_ghz if np.isfinite(item.nu_center_err_ghz) else 0.0) ** 2
                for item in peaks
            )
        )
        direction_results[scan_direction] = {"fsr_ghz": fsr_ghz, "fsr_err_ghz": fsr_err, "peaks": peaks}
        rows.append(
            {
                "dataset_key": dataset_key,
                "method": "A_direct_l0_adjacent_modes",
                "scan_direction": scan_direction,
                "fsr_ghz": fsr_ghz,
                "fsr_err_ghz": fsr_err,
                "peak1_lambda_nm": peaks[0].lambda_center_nm,
                "peak2_lambda_nm": peaks[1].lambda_center_nm,
                "peak1_nu_ghz": peaks[0].nu_center_ghz,
                "peak2_nu_ghz": peaks[1].nu_center_ghz,
            }
        )
    fsr_values = np.asarray([item["fsr_ghz"] for item in direction_results.values()], dtype=float)
    fsr_combined = float(np.mean(fsr_values))
    fsr_scatter = float(np.std(fsr_values, ddof=1)) if len(fsr_values) > 1 else 0.0
    fsr_stat = float(np.mean([item["fsr_err_ghz"] for item in direction_results.values()]))
    fsr_sigma = max(fsr_scatter, fsr_stat)
    rows.append(
        {
            "dataset_key": dataset_key,
            "method": "A_direct_l0_adjacent_modes",
            "scan_direction": "combined",
            "fsr_ghz": fsr_combined,
            "fsr_err_ghz": fsr_sigma,
            "peak1_lambda_nm": np.nan,
            "peak2_lambda_nm": np.nan,
            "peak1_nu_ghz": np.nan,
            "peak2_nu_ghz": np.nan,
        }
    )
    return {"summary_df": pd.DataFrame(rows), "by_direction": direction_results, "combined_fsr_ghz": fsr_combined, "combined_fsr_err_ghz": fsr_sigma}


def fit_global_fsr_k(
    l_values: Sequence[int],
    nu_values_ghz: Sequence[float],
    fsr_guess_ghz: float,
) -> Dict[str, Any]:
    l_arr = np.asarray(l_values, dtype=int)
    nu_arr = np.asarray(nu_values_ghz, dtype=float)
    order = np.argsort(l_arr)
    l_arr = l_arr[order]
    nu_arr = nu_arr[order]
    nu0 = float(nu_arr[l_arr == 0][0])
    delta = nu_arr - nu0
    fsr_grid = np.linspace(fsr_guess_ghz * 0.85, fsr_guess_ghz * 1.15, 1201)
    best: Dict[str, Any] = {"score": float("inf")}
    for fsr_val in fsr_grid:
        pos = np.mod(delta / fsr_val, 1.0)
        k_fit = fit_k_from_positions(l_arr, pos, refine=False)
        k_val = float(k_fit["k"])
        m_vals = np.rint(delta / fsr_val - l_arr * k_val).astype(int)
        resid_ghz = delta - (m_vals + l_arr * k_val) * fsr_val
        score = float(np.mean((resid_ghz / fsr_val) ** 2) + np.mean(k_fit["residuals"] ** 2))
        if score < best["score"]:
            best = {
                "score": score,
                "fsr_ghz": float(fsr_val),
                "k": k_val,
                "m_indices": m_vals,
                "residuals_ghz": resid_ghz,
                "pos_meas": pos,
                "pos_fit": np.mod(l_arr * k_val, 1.0),
            }
    refine_center = best["fsr_ghz"]
    refine_grid = np.linspace(max(0.1, refine_center - 0.2), refine_center + 0.2, 1601)
    for fsr_val in refine_grid:
        pos = np.mod(delta / fsr_val, 1.0)
        k_fit = fit_k_from_positions(l_arr, pos, refine=False)
        k_val = float(k_fit["k"])
        m_vals = np.rint(delta / fsr_val - l_arr * k_val).astype(int)
        resid_ghz = delta - (m_vals + l_arr * k_val) * fsr_val
        score = float(np.mean((resid_ghz / fsr_val) ** 2) + np.mean(k_fit["residuals"] ** 2))
        if score < best["score"]:
            best = {
                "score": score,
                "fsr_ghz": float(fsr_val),
                "k": k_val,
                "m_indices": m_vals,
                "residuals_ghz": resid_ghz,
                "pos_meas": pos,
                "pos_fit": np.mod(l_arr * k_val, 1.0),
            }
    fsr_near = np.linspace(max(0.1, best["fsr_ghz"] - 0.05), best["fsr_ghz"] + 0.05, 401)
    fsr_scores = []
    k_vals = []
    for fsr_val in fsr_near:
        pos = np.mod(delta / fsr_val, 1.0)
        k_fit = fit_k_from_positions(l_arr, pos, refine=False)
        k_val = float(k_fit["k"])
        m_vals = np.rint(delta / fsr_val - l_arr * k_val).astype(int)
        resid_ghz = delta - (m_vals + l_arr * k_val) * fsr_val
        fsr_scores.append(float(np.mean((resid_ghz / fsr_val) ** 2) + np.mean(k_fit["residuals"] ** 2)))
        k_vals.append(k_val)
    fsr_scores_arr = np.asarray(fsr_scores)
    fsr_score_tol = _score_band_tolerance(float(fsr_scores_arr.min()))
    fsr_band = _contiguous_low_score_band(fsr_near, fsr_scores_arr, float(fsr_scores_arr.min()) + fsr_score_tol)
    fsr_sigma = float(np.std(fsr_band)) if len(fsr_band) > 1 else np.nan
    k_band = _contiguous_low_score_band(np.asarray(k_vals, dtype=float), fsr_scores_arr, float(fsr_scores_arr.min()) + fsr_score_tol)
    k_sigma = float(np.std(k_band)) if len(k_band) > 1 else np.nan
    final_pos = np.mod(delta / best["fsr_ghz"], 1.0)
    final_k_fit = fit_k_from_positions(l_arr, final_pos, refine=True)
    final_k = float(final_k_fit["k"])
    final_m = np.rint(delta / best["fsr_ghz"] - l_arr * final_k).astype(int)
    final_resid = delta - (final_m + l_arr * final_k) * best["fsr_ghz"]
    return {
        "l_values": l_arr,
        "nu_values_ghz": nu_arr,
        "nu_ref_ghz": nu0,
        "fsr_ghz": best["fsr_ghz"],
        "fsr_err_ghz": fsr_sigma,
        "k": final_k,
        "k_err": max(k_sigma, final_k_fit["sigma_k"]) if np.isfinite(final_k_fit["sigma_k"]) else k_sigma,
        "m_indices": {int(l): int(m) for l, m in zip(l_arr, final_m)},
        "residuals_ghz": {int(l): float(r) for l, r in zip(l_arr, final_resid)},
        "pos_meas": {int(l): float(p) for l, p in zip(l_arr, final_pos)},
        "pos_fit": {int(l): float(p) for l, p in zip(l_arr, final_k_fit["predicted"])},
        "score": best["score"],
    }


def malitson_index_20c(lambda_um: float) -> float:
    lam2 = float(lambda_um) ** 2
    b1, b2, b3 = 0.6961663, 0.4079426, 0.8974794
    c1, c2, c3 = 0.0684043**2, 0.1162414**2, 9.896161**2
    n2 = 1.0 + (b1 * lam2) / (lam2 - c1) + (b2 * lam2) / (lam2 - c2) + (b3 * lam2) / (lam2 - c3)
    return float(math.sqrt(n2))


def fused_silica_index(lambda_um: float, temp_c: float) -> float:
    temp_k = float(temp_c) + 273.15
    s_coeffs = np.asarray(
        [
            [1.10127e00, -4.94251e-05, 5.27414e-07, -1.59700e-09, 1.75949e-12],
            [1.78752e-05, 4.76391e-05, -4.49019e-07, 1.44546e-09, -1.57223e-12],
            [7.93552e-01, -1.27815e-03, 1.84595e-05, -9.20275e-08, 1.48829e-10],
        ],
        dtype=float,
    )
    lambda_coeffs = np.asarray(
        [
            [-8.90600e-02, 9.08730e-06, -6.53638e-08, 7.77072e-11, 6.84605e-14],
            [2.97562e-01, -8.59578e-04, 6.59069e-06, -1.09482e-08, 7.85145e-13],
            [9.34454e00, -7.09788e-03, 1.01968e-04, -5.07660e-07, 8.21348e-10],
        ],
        dtype=float,
    )
    powers = np.asarray([temp_k**0, temp_k, temp_k**2, temp_k**3, temp_k**4], dtype=float)
    strengths = s_coeffs @ powers
    resonance = lambda_coeffs @ powers
    lam2 = float(lambda_um) ** 2
    n2 = 1.0
    for s_i, lam_i in zip(strengths, resonance):
        n2 += (s_i * lam2) / (lam2 - lam_i**2)
    return float(math.sqrt(n2))


def derive_cavity_params(
    fsr_ghz: float,
    k: float,
    n_value: float,
    fsr_err_ghz: float = np.nan,
    k_err: float = np.nan,
) -> Dict[str, float]:
    fsr_hz = fsr_ghz * 1e9
    length_m = C_M_PER_S / (2.0 * n_value * fsr_hz)
    length_mm = length_m * 1e3
    lr_ratio = math.sin(math.pi * k) ** 2
    radius_mm = length_mm / lr_ratio
    if np.isfinite(fsr_err_ghz):
        dL_dfsr = -C_M_PER_S / (2.0 * n_value * (fsr_hz**2)) * 1e12
        sigma_L_mm = abs(dL_dfsr) * fsr_err_ghz
    else:
        sigma_L_mm = np.nan
    if np.isfinite(k_err):
        d_lr_dk = math.pi * math.sin(2.0 * math.pi * k)
        sigma_lr = abs(d_lr_dk) * k_err
    else:
        sigma_lr = np.nan
    if np.isfinite(sigma_L_mm) and np.isfinite(sigma_lr):
        sigma_R_mm = math.sqrt((sigma_L_mm / lr_ratio) ** 2 + (length_mm * sigma_lr / (lr_ratio**2)) ** 2)
    else:
        sigma_R_mm = np.nan
    return {
        "L_mm": float(length_mm),
        "L_err_mm": float(sigma_L_mm),
        "L_over_R": float(lr_ratio),
        "L_over_R_err": float(sigma_lr),
        "R_mm": float(radius_mm),
        "R_err_mm": float(sigma_R_mm),
    }


def merge_direction_results(
    branch_results: Dict[str, BranchSelectionResult],
    fsr_hint_ghz: float,
) -> Dict[int, Dict[str, Any]]:
    merged: Dict[int, Dict[str, Any]] = {}
    all_l = sorted(branch_results[next(iter(branch_results))].selected_candidates.keys())
    for l_index in all_l:
        rising = branch_results["Rising"].selected_candidates[l_index]
        falling = branch_results["Falling"].selected_candidates[l_index]
        shift_choices = np.arange(-2, 3, dtype=int)
        shift_idx = int(
            shift_choices[
                np.argmin(np.abs(falling.nu_center_ghz + shift_choices * fsr_hint_ghz - rising.nu_center_ghz))
            ]
        )
        falling_nu_aligned = falling.nu_center_ghz + shift_idx * fsr_hint_ghz
        nu_center = float(np.mean([rising.nu_center_ghz, falling_nu_aligned]))
        lambda_center = float(C_M_PER_S / (nu_center * 1e9) / 1e-9)
        fwhm_ghz = float(np.mean([rising.fwhm_ghz, falling.fwhm_ghz]))
        fwhm_nm = float(np.mean([rising.fwhm_nm, falling.fwhm_nm]))
        aligned_lambda_falling = float(C_M_PER_S / (falling_nu_aligned * 1e9) / 1e-9)
        merged[l_index] = {
            "l": l_index,
            "lambda_center_nm": lambda_center,
            "lambda_center_diff_nm": abs(rising.lambda_center_nm - aligned_lambda_falling),
            "nu_center_ghz": nu_center,
            "nu_center_diff_ghz": abs(rising.nu_center_ghz - falling_nu_aligned),
            "fwhm_nm": fwhm_nm,
            "fwhm_diff_nm": abs(rising.fwhm_nm - falling.fwhm_nm),
            "fwhm_ghz": fwhm_ghz,
            "fwhm_diff_ghz": abs(rising.fwhm_ghz - falling.fwhm_ghz),
            "peak_power_uw_mean": float(np.mean([rising.peak_power_uw, falling.peak_power_uw])),
            "peak_power_uw_diff": abs(rising.peak_power_uw - falling.peak_power_uw),
            "r2_mean": float(np.mean([rising.r_squared, falling.r_squared])),
            "falling_branch_shift_fsr": shift_idx,
            "rising": rising,
            "falling": falling,
        }
    return merged


def find_matching_peak_in_window(
    df: pd.DataFrame,
    dataset_key: str,
    l_index: int,
    scan_direction: str,
    source: str,
    lambda_min_nm: float,
    lambda_max_nm: float,
    expected_center_nm: float,
) -> Optional[PeakFitResult]:
    sub = df[df["Scan_Direction"] == scan_direction].sort_values("Lambda_aligned").reset_index(drop=True)
    window = sub[(sub["Lambda_aligned"] >= lambda_min_nm) & (sub["Lambda_aligned"] <= lambda_max_nm)].copy()
    if len(window) < 7:
        return None
    x = window["Lambda_aligned"].to_numpy(dtype=float)
    y = window["Power_uW"].to_numpy(dtype=float)
    y_smooth = _smooth_signal(y)
    peaks, props = find_peaks(y_smooth, prominence=max(np.std(y_smooth) * 0.2, 1e-8), distance=max(3, len(y) // 20))
    if len(peaks) == 0:
        peak_index = int(np.argmax(y_smooth))
        peaks = np.asarray([peak_index], dtype=int)
        props = {"prominences": np.asarray([max(y_smooth[peak_index] - np.median(y_smooth), 0.0)])}
    nearest_idx = int(np.argmin(np.abs(x[peaks] - expected_center_nm)))
    peak_index = int(peaks[nearest_idx])
    try:
        return fit_peak_local(
            x=x,
            y=y,
            dataset_key=dataset_key,
            l_index=l_index,
            scan_direction=scan_direction,
            source=source,
            candidate_rank=1,
            prominence_uw=float(props["prominences"][nearest_idx]) if "prominences" in props else 0.0,
            peak_index=peak_index,
            model="lorentz",
        )
    except Exception:
        return None


def compare_scan_sets(
    dataset_key: str,
    primary_scan_df: pd.DataFrame,
    reference_scan_df: pd.DataFrame,
    chosen_peak_windows: Iterable[PeakFitResult],
    primary_label: str,
    reference_label: str,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for primary_peak in chosen_peak_windows:
        reference_peak = find_matching_peak_in_window(
            df=reference_scan_df,
            dataset_key=dataset_key,
            l_index=primary_peak.l_index,
            scan_direction=primary_peak.scan_direction,
            source=reference_label,
            lambda_min_nm=primary_peak.window_lambda_min_nm,
            lambda_max_nm=primary_peak.window_lambda_max_nm,
            expected_center_nm=primary_peak.lambda_center_nm,
        )
        if reference_peak is None:
            continue
        rows.append(
            {
                "dataset_key": dataset_key,
                "l": primary_peak.l_index,
                "scan_direction": primary_peak.scan_direction,
                "primary_label": primary_label,
                "reference_label": reference_label,
                f"{primary_label}_lambda_center_nm": primary_peak.lambda_center_nm,
                f"{reference_label}_lambda_center_nm": reference_peak.lambda_center_nm,
                "delta_lambda_nm": reference_peak.lambda_center_nm - primary_peak.lambda_center_nm,
                f"{primary_label}_nu_center_ghz": primary_peak.nu_center_ghz,
                f"{reference_label}_nu_center_ghz": reference_peak.nu_center_ghz,
                "delta_nu_ghz": reference_peak.nu_center_ghz - primary_peak.nu_center_ghz,
                f"{primary_label}_fwhm_ghz": primary_peak.fwhm_ghz,
                f"{reference_label}_fwhm_ghz": reference_peak.fwhm_ghz,
                "delta_fwhm_ghz": reference_peak.fwhm_ghz - primary_peak.fwhm_ghz,
                f"{primary_label}_peak_power_uw": primary_peak.peak_power_uw,
                f"{reference_label}_peak_power_uw": reference_peak.peak_power_uw,
                "delta_peak_power_uw": reference_peak.peak_power_uw - primary_peak.peak_power_uw,
                f"{primary_label}_r_squared": primary_peak.r_squared,
                f"{reference_label}_r_squared": reference_peak.r_squared,
            }
        )
    return pd.DataFrame(rows)


def save_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def _sample_for_plot(x: np.ndarray, y: np.ndarray, max_points: int = 500) -> Tuple[np.ndarray, np.ndarray]:
    if len(x) <= max_points:
        return x, y
    idx = np.linspace(0, len(x) - 1, max_points).astype(int)
    return x[idx], y[idx]


def plot_peak_fits_overview(
    output_path: Path,
    dataset_key: str,
    primary_scans: Dict[int, pd.DataFrame],
    reference_scans: Dict[int, pd.DataFrame],
    merged_peaks: Dict[int, Dict[str, Any]],
    primary_label: str,
    reference_label: str,
) -> None:
    fig, axes = plt.subplots(2, 5, figsize=(18, 7), constrained_layout=True)
    axes = axes.ravel()
    for ax, l_index in zip(axes, sorted(merged_peaks.keys())):
        merged = merged_peaks[l_index]
        for direction, color in [("Rising", "tab:blue"), ("Falling", "tab:orange")]:
            selected_peak: PeakFitResult = merged[direction.lower()]
            primary_df = primary_scans[l_index]
            sub_primary = primary_df[primary_df["Scan_Direction"] == direction]
            mask = (
                (sub_primary["Lambda_aligned"] >= selected_peak.window_lambda_min_nm)
                & (sub_primary["Lambda_aligned"] <= selected_peak.window_lambda_max_nm)
            )
            x_primary = sub_primary.loc[mask, "Lambda_aligned"].to_numpy(dtype=float)
            y_primary = sub_primary.loc[mask, "Power_uW"].to_numpy(dtype=float)
            x_plot, y_plot = _sample_for_plot(x_primary, y_primary)
            ax.plot(x_plot, y_plot, ".", ms=2, alpha=0.55, color=color, label=f"{direction} {primary_label}" if l_index == 0 else None)
            x_fit = np.linspace(selected_peak.window_lambda_min_nm, selected_peak.window_lambda_max_nm, 300)
            y_fit = _lorentzian_with_offset(
                x_fit,
                selected_peak.baseline_uw,
                selected_peak.amplitude_uw,
                selected_peak.lambda_center_nm,
                selected_peak.fwhm_nm / 2.0,
            )
            ax.plot(x_fit, y_fit, "-", lw=1.4, color=color)
            ax.axvline(selected_peak.lambda_center_nm, ls="--", lw=0.8, color=color, alpha=0.8)
            reference_df = reference_scans[l_index]
            sub_reference = reference_df[reference_df["Scan_Direction"] == direction]
            reference_mask = (
                (sub_reference["Lambda_aligned"] >= selected_peak.window_lambda_min_nm)
                & (sub_reference["Lambda_aligned"] <= selected_peak.window_lambda_max_nm)
            )
            x_reference = sub_reference.loc[reference_mask, "Lambda_aligned"].to_numpy(dtype=float)
            y_reference = sub_reference.loc[reference_mask, "Power_uW"].to_numpy(dtype=float)
            if len(x_reference):
                x_reference_plot, y_reference_plot = _sample_for_plot(x_reference, y_reference)
                ax.plot(
                    x_reference_plot,
                    y_reference_plot,
                    ".",
                    ms=1.4,
                    alpha=0.18,
                    color=color,
                    label=f"{direction} {reference_label}" if l_index == 0 else None,
                )
        ax.set_title(f"l={l_index}")
        ax.set_xlabel("Lambda (nm)")
        ax.set_ylabel("Power (uW)")
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=2)
    fig.suptitle(f"{dataset_key} selected peak fits", fontsize=14)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_position_fit(
    output_path: Path,
    dataset_key: str,
    k_summary_df: pd.DataFrame,
    k_best: float,
) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True, constrained_layout=True)
    ax1.plot(k_summary_df["l"], k_summary_df["pos_meas"], "o", label="measured", color="tab:blue")
    ax1.plot(k_summary_df["l"], k_summary_df["pos_fit"], "-", label=f"fit k={k_best:.6f}", color="tab:red")
    ax1.set_ylabel("Position in FSR")
    ax1.set_ylim(-0.05, 1.05)
    ax1.legend()
    ax1.grid(alpha=0.25)

    ax2.axhline(0.0, color="black", lw=0.8)
    ax2.bar(k_summary_df["l"], k_summary_df["residual"], color="tab:green", alpha=0.75)
    ax2.set_xlabel("l")
    ax2.set_ylabel("Residual")
    ax2.grid(alpha=0.25)

    fig.suptitle(f"{dataset_key} position fit")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def export_tables_and_plots(
    dataset_output_dir: Path,
    tables: Dict[str, pd.DataFrame],
    primary_scans: Dict[int, pd.DataFrame],
    reference_scans: Dict[int, pd.DataFrame],
    merged_peaks: Dict[int, Dict[str, Any]],
    k_summary_df: pd.DataFrame,
    k_best: float,
    primary_label: str,
    reference_label: str,
) -> None:
    dataset_output_dir.mkdir(parents=True, exist_ok=True)
    for filename, df in tables.items():
        save_csv(df, dataset_output_dir / filename)
    plot_peak_fits_overview(
        output_path=dataset_output_dir / "peak_fits_overview.png",
        dataset_key=dataset_output_dir.name,
        primary_scans=primary_scans,
        reference_scans=reference_scans,
        merged_peaks=merged_peaks,
        primary_label=primary_label,
        reference_label=reference_label,
    )
    plot_position_fit(
        output_path=dataset_output_dir / "position_fit.png",
        dataset_key=dataset_output_dir.name,
        k_summary_df=k_summary_df,
        k_best=k_best,
    )


def wrap_fsr_position_delta(measured_pos: np.ndarray | float, reference_pos: np.ndarray | float) -> np.ndarray | float:
    delta = np.mod(np.asarray(measured_pos) - np.asarray(reference_pos) + 0.5, 1.0) - 0.5
    if np.isscalar(measured_pos) and np.isscalar(reference_pos):
        return float(delta)
    return delta


def analytic_branch_geometry(branch_numerator: int, branch_denominator: int) -> Dict[str, float]:
    if branch_denominator <= 0:
        raise ValueError("branch_denominator must be positive")
    k_theory = branch_numerator / branch_denominator
    l_over_r = math.sin(math.pi * k_theory) ** 2
    phi_rad = math.pi * k_theory
    return {
        "branch_numerator": float(branch_numerator),
        "branch_denominator": float(branch_denominator),
        "k_theory": float(k_theory),
        "L_over_R_theory": float(l_over_r),
        "phi_rad": float(phi_rad),
    }


def format_value(value: float, digits: int = 6, unit: str = "") -> str:
    if value is None or not np.isfinite(value):
        return "NaN"
    return f"{value:.{digits}f}{unit}"
