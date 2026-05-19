from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from scipy.special import eval_genlaguerre


def parse_float_list(text: str | None, default: Sequence[float]) -> list[float]:
    if text is None or not text.strip():
        return list(default)
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def make_square_grid(extent: float, grid_size: int) -> tuple[np.ndarray, np.ndarray, float]:
    axis = np.linspace(-extent, extent, grid_size, dtype=float)
    dx = float(axis[1] - axis[0])
    x, y = np.meshgrid(axis, axis, indexing="xy")
    return x, y, dx


def _lg_norm(p: int, l_abs: int, w: float) -> float:
    return math.sqrt(2.0 * math.factorial(p) / (math.pi * math.factorial(p + l_abs))) / w


def lg_mode_cartesian(
    x: np.ndarray,
    y: np.ndarray,
    p: int,
    l: int,
    w0: float,
    z: float = 0.0,
    wavelength: float = 1.0,
    shift_x: float = 0.0,
    shift_y: float = 0.0,
) -> np.ndarray:
    l_abs = abs(l)
    xs = x - shift_x
    ys = y - shift_y
    r = np.hypot(xs, ys)
    phi = np.arctan2(ys, xs)

    z_r = math.pi * w0 * w0 / wavelength
    wz = w0 * math.sqrt(1.0 + (z / z_r) ** 2)
    psi = math.atan2(z, z_r)

    if abs(z) < 1e-15:
        curvature_phase = np.ones_like(r, dtype=complex)
    else:
        r_curv = z * (1.0 + (z_r / z) ** 2)
        curvature_phase = np.exp(-1j * math.pi * (r**2) / (wavelength * r_curv))

    laguerre = eval_genlaguerre(p, l_abs, 2.0 * (r**2) / (wz**2))
    radial = (np.sqrt(2.0) * r / wz) ** l_abs
    amplitude = _lg_norm(p, l_abs, wz) * radial * laguerre * np.exp(-(r**2) / (wz**2))
    gouy = np.exp(1j * (2 * p + l_abs + 1) * psi)
    azimuth = np.exp(1j * l * phi)
    return amplitude * curvature_phase * gouy * azimuth


def phase_only_vortex_cartesian(
    x: np.ndarray,
    y: np.ndarray,
    l: int,
    w_phase: float,
    shift_x: float = 0.0,
    shift_y: float = 0.0,
) -> np.ndarray:
    xs = x - shift_x
    ys = y - shift_y
    r = np.hypot(xs, ys)
    phi = np.arctan2(ys, xs)
    return np.exp(-(r**2) / (w_phase**2)) * np.exp(1j * l * phi)


def normalize_field(field: np.ndarray, dx: float) -> np.ndarray:
    norm = math.sqrt(float(np.sum(np.abs(field) ** 2) * dx * dx))
    if norm == 0.0:
        return field
    return field / norm


def inner_product(field_a: np.ndarray, field_b: np.ndarray, dx: float) -> complex:
    return np.sum(np.conj(field_a) * field_b) * dx * dx


def overlap_power(field_a: np.ndarray, field_b: np.ndarray, dx: float) -> float:
    a = normalize_field(field_a, dx)
    b = normalize_field(field_b, dx)
    return float(abs(inner_product(a, b, dx)) ** 2)


def circular_aperture_mask(x: np.ndarray, y: np.ndarray, radius: float) -> np.ndarray:
    return (np.hypot(x, y) <= radius).astype(float)


def apply_aperture(field: np.ndarray, x: np.ndarray, y: np.ndarray, radius: float | None) -> np.ndarray:
    if radius is None or radius <= 0.0:
        return field
    return field * circular_aperture_mask(x, y, radius)


def pixelate_field(field: np.ndarray, pixel_size: float, dx: float) -> np.ndarray:
    if pixel_size <= 0.0:
        return field
    block = max(1, int(round(pixel_size / dx)))
    if block <= 1:
        return field

    ny, nx = field.shape
    trim_y = ny - (ny % block)
    trim_x = nx - (nx % block)
    if trim_y == 0 or trim_x == 0:
        return field

    trimmed = field[:trim_y, :trim_x]
    coarse = trimmed.reshape(trim_y // block, block, trim_x // block, block).mean(axis=(1, 3))
    blocky = np.repeat(np.repeat(coarse, block, axis=0), block, axis=1)
    out = field.copy()
    out[:trim_y, :trim_x] = blocky
    return out


def radial_decomposition(
    field: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    dx: float,
    l: int,
    w_basis: float,
    p_max: int,
) -> list[complex]:
    normalized = normalize_field(field, dx)
    coeffs: list[complex] = []
    for p in range(p_max + 1):
        basis = normalize_field(lg_mode_cartesian(x, y, p=p, l=l, w0=w_basis), dx)
        coeffs.append(inner_product(basis, normalized, dx))
    return coeffs


def ideal_target_overlap_amplitude(l: int, eta: float) -> float:
    l_abs = abs(l)
    return (2.0 * eta / (1.0 + eta * eta)) ** (l_abs + 1)


def ideal_target_overlap_power(l: int, eta: float) -> float:
    amplitude = ideal_target_overlap_amplitude(l, eta)
    return amplitude * amplitude


def ideal_p1_leakage_amplitude(l: int, eta: float) -> float:
    l_abs = abs(l)
    prefactor = math.sqrt(l_abs + 1.0)
    return prefactor * ideal_target_overlap_amplitude(l, eta) * (1.0 - eta * eta) / (1.0 + eta * eta)


def ideal_p1_leakage_power(l: int, eta: float) -> float:
    amplitude = ideal_p1_leakage_amplitude(l, eta)
    return amplitude * amplitude


def canonical_scaled_eta(l: int) -> float:
    return 1.0 / math.sqrt(abs(l) + 1.0)


def ring_peak_radius(l: int, w: float) -> float:
    l_abs = abs(l)
    if l_abs == 0:
        return 0.0
    return w * math.sqrt(l_abs / 2.0)


def rms_radius(l: int, w: float) -> float:
    return w * math.sqrt((abs(l) + 1.0) / 2.0)


def write_csv(path: Path, rows: Iterable[dict]) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"
