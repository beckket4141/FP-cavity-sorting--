from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parent
OUTPUT_DIR = SIM_DIR / "outputs"
DATA_DIR = OUTPUT_DIR / "data"
FIGURE_DIR = OUTPUT_DIR / "figures"
REPORT_DIR = OUTPUT_DIR / "reports"

EPS = 1e-12


@dataclass(frozen=True)
class Metrics:
    eta_sort: float
    e_sort: float
    mutual_information_bits: float
    mean_er_sum_db: float
    min_er_sum_db: float
    mean_er_max_db: float
    min_er_max_db: float
    diag_min: float
    diag_max: float
    col_sum_error: float


def ensure_output_dirs() -> None:
    for path in (DATA_DIR, FIGURE_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: Sequence[dict[str, object]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_matrix_csv(path: Path, matrix: np.ndarray, row_labels: Sequence[int], col_labels: Sequence[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row\\col"] + [str(label) for label in col_labels])
        for label, row in zip(row_labels, matrix):
            writer.writerow([str(label)] + [f"{float(value):.12g}" for value in row])


def g_parameter(length: float, radius: float) -> float:
    if math.isinf(radius):
        return 1.0
    return 1.0 - length / radius


def k_eff_from_g(g1: float, g2: float) -> float:
    product = g1 * g2
    if product < -EPS or product > 1.0 + EPS:
        raise ValueError(f"unstable geometry: g1*g2={product}")
    product = min(1.0, max(0.0, product))
    return math.acos(math.sqrt(product)) / math.pi


def k_eff_from_geometry(length: float, radius_1: float, radius_2: float) -> float:
    return k_eff_from_g(g_parameter(length, radius_1), g_parameter(length, radius_2))


def plane_concave_rho_from_k(k_value: float) -> float:
    return math.sin(math.pi * k_value) ** 2


def plane_concave_k_from_rho(rho: float) -> float:
    if not (0.0 < rho < 1.0):
        raise ValueError(f"plane-concave rho must be in (0, 1), got {rho}")
    return math.acos(math.sqrt(1.0 - rho)) / math.pi


def symmetric_rho_from_k(k_value: float, branch: str) -> float:
    c = math.cos(math.pi * k_value)
    if branch == "near_planar":
        return 1.0 - c
    if branch == "near_concentric":
        return 1.0 + c
    raise ValueError(f"unknown symmetric branch: {branch}")


def symmetric_k_from_rho(rho: float) -> float:
    if not (0.0 < rho < 2.0):
        raise ValueError(f"symmetric rho must be in (0, 2), got {rho}")
    return math.acos(abs(1.0 - rho)) / math.pi


def asymmetric_lengths_from_k(k_value: float, radius_1: float, radius_2: float) -> tuple[float, float]:
    s2 = math.sin(math.pi * k_value) ** 2
    disc = (radius_1 + radius_2) ** 2 - 4.0 * radius_1 * radius_2 * s2
    if disc < -EPS:
        raise ValueError("no real asymmetric two-mirror realization")
    root = math.sqrt(max(0.0, disc))
    return ((radius_1 + radius_2 - root) / 2.0, (radius_1 + radius_2 + root) / 2.0)


def plane_concave_sensitivity(rho: float) -> float:
    return 1.0 / (2.0 * math.pi * math.sqrt(rho * (1.0 - rho)))


def symmetric_sensitivity(rho: float) -> float:
    return 1.0 / (math.pi * math.sqrt(rho * (2.0 - rho)))


def numerical_sensitivity_length(length: float, radius_1: float, radius_2: float, step: float = 1e-6) -> float:
    lo = max(EPS, length - step)
    hi = length + step
    return abs(k_eff_from_geometry(hi, radius_1, radius_2) - k_eff_from_geometry(lo, radius_1, radius_2)) / (hi - lo)


def positions_for_orders(orders: Sequence[int], k_value: float, origin: int = 0) -> np.ndarray:
    return np.mod((np.asarray(orders, dtype=float) - float(origin)) * float(k_value), 1.0)


def circular_distance(a: float, b: float) -> float:
    diff = abs(float(a) - float(b))
    return min(diff, 1.0 - diff)


def distance_matrix_from_positions(positions: Sequence[float]) -> np.ndarray:
    pos = np.asarray(positions, dtype=float)
    diff = np.abs(pos[:, None] - pos[None, :])
    return np.minimum(diff, 1.0 - diff)


def distance_matrix_for_orders(orders: Sequence[int], k_value: float, origin: int = 0) -> np.ndarray:
    return distance_matrix_from_positions(positions_for_orders(orders, k_value, origin=origin))


def s_min_from_distance_matrix(distance_matrix: np.ndarray) -> float:
    if distance_matrix.shape[0] < 2:
        return 0.5
    values = distance_matrix[np.triu_indices(distance_matrix.shape[0], k=1)]
    return float(np.min(values))


def s_min_for_orders(orders: Sequence[int], k_value: float) -> float:
    return s_min_from_distance_matrix(distance_matrix_for_orders(orders, k_value))


def airy_response_matrix(distance_matrix: np.ndarray, finesse: float) -> np.ndarray:
    response = 1.0 / (1.0 + ((2.0 * finesse / math.pi) ** 2) * np.sin(math.pi * distance_matrix) ** 2)
    np.fill_diagonal(response, 1.0)
    return response


def condition_probability_matrix(raw_response: np.ndarray) -> np.ndarray:
    col_sums = raw_response.sum(axis=0)
    if np.any(col_sums <= 0.0):
        raise ValueError("raw response matrix contains a non-positive column sum")
    return raw_response / col_sums[None, :]


def response_for_orders(orders: Sequence[int], k_value: float, finesse: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    distance = distance_matrix_for_orders(orders, k_value)
    raw = airy_response_matrix(distance, finesse)
    condition = condition_probability_matrix(raw)
    return distance, raw, condition


def per_channel_records(orders: Sequence[int], raw_response: np.ndarray, condition: np.ndarray) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx, order in enumerate(orders):
        diag = float(condition[idx, idx])
        off = [float(condition[row, idx]) for row in range(len(orders)) if row != idx]
        raw_leak_sum = float(np.sum(raw_response[:, idx]) - 1.0)
        raw_leak_max = float(max(raw_response[row, idx] for row in range(len(orders)) if row != idx)) if len(orders) > 1 else 0.0
        er_sum = 10.0 * math.log10(1.0 / raw_leak_sum) if raw_leak_sum > 0.0 else float("inf")
        er_max = 10.0 * math.log10(1.0 / raw_leak_max) if raw_leak_max > 0.0 else float("inf")
        rows.append(
            {
                "order_N": float(order),
                "success_probability": diag,
                "error_probability": 1.0 - diag,
                "largest_offdiag_probability": max(off) if off else 0.0,
                "ER_sum_dB": er_sum,
                "ER_max_dB": er_max,
            }
        )
    return rows


def mutual_information_bits(condition: np.ndarray) -> float:
    d = condition.shape[0]
    prior = 1.0 / d
    output_probs = condition.sum(axis=1) * prior
    info = 0.0
    for col in range(d):
        for row in range(d):
            p = float(condition[row, col])
            if p > 0.0 and output_probs[row] > 0.0:
                info += prior * p * math.log2(p / float(output_probs[row]))
    return info


def summarize_metrics(raw_response: np.ndarray, condition: np.ndarray) -> Metrics:
    diag = np.diag(condition)
    per = per_channel_records(list(range(condition.shape[0])), raw_response, condition)
    er_sum = [row["ER_sum_dB"] for row in per]
    er_max = [row["ER_max_dB"] for row in per]
    col_sums = condition.sum(axis=0)
    return Metrics(
        eta_sort=float(np.mean(diag)),
        e_sort=float(1.0 - np.mean(diag)),
        mutual_information_bits=mutual_information_bits(condition),
        mean_er_sum_db=float(np.mean(er_sum)),
        min_er_sum_db=float(np.min(er_sum)),
        mean_er_max_db=float(np.mean(er_max)),
        min_er_max_db=float(np.min(er_max)),
        diag_min=float(np.min(diag)),
        diag_max=float(np.max(diag)),
        col_sum_error=float(np.max(np.abs(col_sums - 1.0))),
    )


def coprime_branches(M: int) -> list[int]:
    return [m for m in range(1, M) if math.gcd(m, M) == 1 and m < M / 2]


def continuous_orders(M: int) -> list[int]:
    return list(range(1, M + 1))


def finite_airy_noise_sum(M: int, finesse: float) -> float:
    total = 0.0
    for n in range(1, M):
        total += 1.0 / (1.0 + ((2.0 * finesse / math.pi) ** 2) * (math.sin(math.pi * n / M) ** 2))
    return total


def finite_airy_noise_closed(M: int, finesse: float) -> float:
    a = (2.0 * finesse / math.pi) ** 2
    q = (math.sqrt(1.0 + a) - 1.0) / (math.sqrt(1.0 + a) + 1.0)
    return M / math.sqrt(1.0 + a) * ((1.0 + q**M) / (1.0 - q**M)) - 1.0


def airy_limit_noise(tau_0: float) -> float:
    x = math.pi / (2.0 * tau_0)
    return x / math.tanh(x) - 1.0


def er_sum_from_noise(noise: float) -> float:
    return 10.0 * math.log10(1.0 / noise)


def eta_from_noise(noise: float) -> float:
    return 1.0 / (1.0 + noise)


def exact_rational_search(
    orders: Sequence[int],
    window: tuple[Fraction, Fraction],
    target_k: float | None = None,
) -> dict[str, object]:
    diffs = sorted({abs(b - a) for i, a in enumerate(orders) for b in orders[i + 1 :] if abs(b - a) > 0})
    if not diffs:
        raise ValueError("at least two distinct orders are required")
    d_max = max(diffs)
    q_bound = max(window[0].denominator, window[1].denominator, 2 * d_max)
    best: dict[str, object] | None = None
    candidates: list[dict[str, object]] = []
    for q in range(1, q_bound + 1):
        p_min = math.ceil(float(window[0]) * q - EPS)
        p_max = math.floor(float(window[1]) * q + EPS)
        for p in range(p_min, p_max + 1):
            if p <= 0 or p >= q or math.gcd(p, q) != 1:
                continue
            frac = Fraction(p, q)
            if frac < window[0] or frac > window[1]:
                continue
            k_value = float(frac)
            exact_distances: dict[int, Fraction] = {}
            for d in diffs:
                residue = (d * frac) % 1
                exact_distances[d] = min(residue, 1 - residue)
            s_min_exact = min(exact_distances.values())
            s_min = float(s_min_exact)
            limiting = [d for d, dist in exact_distances.items() if dist == s_min_exact]
            row = {
                "p": p,
                "q": q,
                "k_fraction": f"{p}/{q}",
                "k": k_value,
                "s_min": s_min,
                "limiting_differences": ",".join(str(d) for d in limiting),
            }
            candidates.append(row)
            tie_gap = abs(k_value - target_k) if target_k is not None else 0.0
            score = (s_min_exact, -tie_gap, -q)
            if best is None or score > best["_score"]:
                best = {**row, "_score": score}
    if best is None:
        raise RuntimeError("no rational candidates found")
    best_public = {key: value for key, value in best.items() if key != "_score"}
    candidates.sort(key=lambda item: (float(item["s_min"]), -int(item["q"])), reverse=True)
    return {
        "orders": list(orders),
        "window": [str(window[0]), str(window[1])],
        "D_max": d_max,
        "q_bound": q_bound,
        "best": best_public,
        "top_candidates": candidates[:30],
    }
