from __future__ import annotations

import csv
import importlib.util
import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
OUTPUT_ROOT = BASE_DIR / "outputs"
PLOT_SMIN_PATH = REPO_ROOT / "tools" / "plot_smin.py"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_plot_smin():
    spec = importlib.util.spec_from_file_location("plot_smin_analysis", PLOT_SMIN_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {PLOT_SMIN_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PLOT_SMIN = _load_plot_smin()
k_from_lr = PLOT_SMIN.k_from_lr
positions_for_k = PLOT_SMIN.positions_for_k
smin_for_lr = PLOT_SMIN.smin_for_lr
smin_sorted_gaps = PLOT_SMIN.smin_sorted_gaps


@dataclass(frozen=True)
class AnalyticPeak:
    n_modes: int
    m: int
    k_star: float
    lr_star: float
    smin_star: float
    family_index: int


@dataclass(frozen=True)
class PlatformInterval:
    left_k: float
    right_k: float
    left_lr: float
    right_lr: float

    @property
    def width_k(self) -> float:
        return self.right_k - self.left_k

    @property
    def width_lr(self) -> float:
        return self.right_lr - self.left_lr


def tau_delta(finesse: float, tau0: float) -> float:
    return float(tau0) / float(finesse)


def lr_from_k(k: float) -> float:
    return math.sin(math.pi * float(k)) ** 2


def circular_distance(a: float, b: float) -> float:
    d = abs(float(a) - float(b))
    return d if d <= 0.5 else 1.0 - d


def continuous_set_smin(k: float, n_modes: int) -> float:
    return min(circular_distance((k * d) % 1.0, 0.0) for d in range(1, n_modes))


def analytic_peak_families(n_modes: int, k_upper: float = 0.5) -> list[AnalyticPeak]:
    peaks: list[AnalyticPeak] = []
    family_index = 0
    for m in range(1, n_modes):
        if math.gcd(m, n_modes) != 1:
            continue
        k_star = m / n_modes
        if k_star >= k_upper:
            continue
        family_index += 1
        peaks.append(
            AnalyticPeak(
                n_modes=n_modes,
                m=m,
                k_star=k_star,
                lr_star=lr_from_k(k_star),
                smin_star=1.0 / n_modes,
                family_index=family_index,
            )
        )
    return peaks


def modular_inverse(m: int, n: int) -> int:
    for candidate in range(1, n):
        if (candidate * m) % n == 1:
            return candidate
    raise ValueError(f"No modular inverse for m={m}, n={n}")


def local_platform_formula(n_modes: int, m: int, delta: float) -> PlatformInterval | None:
    peak_height = 1.0 / n_modes
    if delta >= peak_height:
        return None
    a = modular_inverse(m, n_modes)
    k_star = m / n_modes
    left_k = k_star - (peak_height - delta) / a
    right_k = k_star + (peak_height - delta) / (n_modes - a)
    return PlatformInterval(
        left_k=left_k,
        right_k=right_k,
        left_lr=lr_from_k(left_k),
        right_lr=lr_from_k(right_k),
    )


def numeric_local_platform(
    n_modes: int,
    m: int,
    delta: float,
    *,
    half_width: float = 0.05,
    steps: int = 400_000,
) -> PlatformInterval | None:
    peak_height = 1.0 / n_modes
    if delta >= peak_height:
        return None
    k_star = m / n_modes
    left = max(1.0e-8, k_star - half_width)
    right = min(0.5 - 1.0e-8, k_star + half_width)
    grid = [left + (right - left) * i / steps for i in range(steps + 1)]
    values = [continuous_set_smin(k, n_modes) for k in grid]
    idx = min(range(len(grid)), key=lambda i: abs(grid[i] - k_star))
    if values[idx] < delta:
        return None
    lo = idx
    while lo > 0 and values[lo - 1] >= delta:
        lo -= 1
    hi = idx
    while hi < len(grid) - 1 and values[hi + 1] >= delta:
        hi += 1
    return PlatformInterval(
        left_k=grid[lo],
        right_k=grid[hi],
        left_lr=lr_from_k(grid[lo]),
        right_lr=lr_from_k(grid[hi]),
    )


def global_numeric_peak(n_modes: int, *, steps: int = 120_000) -> tuple[float, float]:
    k_min = 1.0e-6
    k_max = 0.5 - 1.0e-6
    best_k = k_min
    best_s = -1.0
    for i in range(steps + 1):
        k = k_min + (k_max - k_min) * i / steps
        s = continuous_set_smin(k, n_modes)
        if s > best_s:
            best_k = k
            best_s = s
    return best_k, best_s


def nearest_peak_family(n_modes: int, k_value: float) -> AnalyticPeak:
    peaks = analytic_peak_families(n_modes, k_upper=0.5)
    return min(peaks, key=lambda peak: abs(peak.k_star - k_value))


def build_conflict_bitmasks(k: float, n_scan: int, delta: float) -> tuple[list[int], list[float]]:
    pos = positions_for_k(k, 1, n_scan)
    adj = [0] * n_scan
    for i in range(n_scan):
        mask = 0
        for j in range(n_scan):
            if i == j:
                continue
            if circular_distance(pos[i], pos[j]) < delta:
                mask |= 1 << j
        adj[i] = mask
    return adj, pos


def mis_maximum_set(adj: Sequence[int]) -> tuple[int, tuple[int, ...]]:
    n_vertices = len(adj)

    @lru_cache(maxsize=None)
    def solve(mask: int) -> tuple[int, ...]:
        if mask == 0:
            return ()
        vertices = [i for i in range(n_vertices) if (mask >> i) & 1]
        pivot = max(vertices, key=lambda i: (adj[i] & mask).bit_count())
        mask_without_pivot = mask & ~(1 << pivot)
        exclude = solve(mask_without_pivot)
        include = (pivot,) + solve(mask_without_pivot & ~adj[pivot])
        return include if len(include) > len(exclude) else exclude

    chosen = solve((1 << n_vertices) - 1)
    return len(chosen), tuple(v + 1 for v in chosen)


def max_consecutive_prefix_size(k: float, n_scan: int, delta: float) -> int:
    pos = positions_for_k(k, 1, n_scan)
    best = 0
    for stop in range(1, n_scan + 1):
        valid = True
        for i in range(stop):
            for j in range(i + 1, stop):
                if circular_distance(pos[i], pos[j]) < delta:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            best = stop
        else:
            break
    return best


def best_consecutive_block(k: float, n_scan: int, delta: float) -> tuple[int, tuple[int, int]]:
    pos = positions_for_k(k, 1, n_scan)
    best = 0
    best_block = (1, 1)
    for start in range(n_scan):
        for stop in range(start, n_scan):
            valid = True
            for i in range(start, stop + 1):
                for j in range(i + 1, stop + 1):
                    if circular_distance(pos[i], pos[j]) < delta:
                        valid = False
                        break
                if not valid:
                    break
            if valid and stop - start + 1 > best:
                best = stop - start + 1
                best_block = (start + 1, stop + 1)
    return best, best_block


def sample_smin_curve_lr(
    n_modes: int,
    lr_min: float,
    lr_max: float,
    steps: int,
) -> list[tuple[float, float]]:
    rows: list[tuple[float, float]] = []
    for i in range(steps + 1):
        lr = lr_min + (lr_max - lr_min) * i / steps
        rows.append((lr, smin_for_lr(lr, 1, n_modes)))
    return rows


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, object]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
