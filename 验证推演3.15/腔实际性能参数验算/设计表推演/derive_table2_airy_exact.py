from __future__ import annotations

import csv
import math
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_CSV = OUTPUT_DIR / "table2_tau0_3_blueprint_airy_exact.csv"

TABLE2_N_VALUES = [4, 9, 15, 30, 50, 100]
TAU0 = 3.0


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)


def choose_preferred_m(n: int) -> int:
    candidates = [m for m in range(1, n // 2 + 1) if m / n < 0.5 and gcd(m, n) == 1]
    if not candidates:
        raise ValueError(f"No valid coprime branch found for N={n}")
    return min(candidates, key=lambda m: (abs(4 * m - n), m))


def format_float(value: float, digits: int = 12) -> str:
    return f"{value:.{digits}f}"


def normalize_columns(matrix: list[list[float]]) -> list[list[float]]:
    rows = len(matrix)
    cols = len(matrix[0])
    normalized = [[0.0 for _ in range(cols)] for _ in range(rows)]
    for col in range(cols):
        col_sum = sum(matrix[row][col] for row in range(rows))
        if col_sum <= 0.0:
            raise ValueError(f"Non-positive column sum at col={col}")
        for row in range(rows):
            normalized[row][col] = matrix[row][col] / col_sum
    return normalized


def mutual_information_bits(conditional: list[list[float]]) -> float:
    n_out = len(conditional)
    n_in = len(conditional[0])
    p_x = 1.0 / n_in
    p_y = [sum(conditional[row][col] * p_x for col in range(n_in)) for row in range(n_out)]
    total = 0.0
    for row in range(n_out):
        for col in range(n_in):
            p_y_given_x = conditional[row][col]
            if p_y_given_x <= 0.0:
                continue
            total += p_x * p_y_given_x * math.log2(p_y_given_x / p_y[row])
    return total


def lorentz_weight(d: int, tau0: float) -> float:
    if d == 0:
        return 1.0
    return 1.0 / (1.0 + 4.0 * (d * tau0) ** 2)


def airy_weight(d: int, n: int, finesse: float) -> float:
    if d == 0:
        return 1.0
    s = d / n
    return 1.0 / (1.0 + ((2.0 * finesse / math.pi) ** 2) * (math.sin(math.pi * s) ** 2))


def build_ring_channel_matrix_lorentz(n: int, tau0: float) -> tuple[list[list[float]], float]:
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    noise_sum = 0.0
    for output_idx in range(n):
        d = min(output_idx, n - output_idx)
        weight = lorentz_weight(d, tau0)
        if d != 0:
            noise_sum += weight
        matrix[output_idx][0] = weight
    for col in range(n):
        for row in range(n):
            matrix[row][col] = matrix[(row - col) % n][0]
    return normalize_columns(matrix), noise_sum


def build_ring_channel_matrix_airy(n: int, tau0: float) -> tuple[list[list[float]], float]:
    finesse = n * tau0
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    noise_sum = 0.0
    for output_idx in range(n):
        d = min(output_idx, n - output_idx)
        weight = airy_weight(d, n, finesse)
        if d != 0:
            noise_sum += weight
        matrix[output_idx][0] = weight
    for col in range(n):
        for row in range(n):
            matrix[row][col] = matrix[(row - col) % n][0]
    return normalize_columns(matrix), noise_sum


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for n in TABLE2_N_VALUES:
        preferred_m = choose_preferred_m(n)
        k_star = preferred_m / n
        lr_star = math.sin(math.pi * preferred_m / n) ** 2
        finesse = n * TAU0

        lorentz_matrix, lorentz_noise = build_ring_channel_matrix_lorentz(n, TAU0)
        airy_matrix, airy_noise = build_ring_channel_matrix_airy(n, TAU0)

        lorentz_eta = 1.0 / (1.0 + lorentz_noise)
        lorentz_er = 10.0 * math.log10(1.0 / lorentz_noise)
        lorentz_mi = mutual_information_bits(lorentz_matrix)

        airy_eta = 1.0 / (1.0 + airy_noise)
        airy_er = 10.0 * math.log10(1.0 / airy_noise)
        airy_mi = mutual_information_bits(airy_matrix)

        rows.append(
            {
                "N": str(n),
                "preferred_m": str(preferred_m),
                "k_star": format_float(k_star, 12),
                "L_over_R_star": format_float(lr_star, 12),
                "F_min": format_float(finesse, 6),
                "ER_sum_lorentz_ring_dB": format_float(lorentz_er, 9),
                "eta_sort_lorentz_ring": format_float(lorentz_eta, 12),
                "I_lorentz_ring_bits": format_float(lorentz_mi, 12),
                "ER_sum_airy_exact_dB": format_float(airy_er, 9),
                "eta_sort_airy_exact": format_float(airy_eta, 12),
                "I_airy_exact_bits": format_float(airy_mi, 12),
                "delta_ER_sum_airy_minus_lorentz_dB": format_float(airy_er - lorentz_er, 9),
                "delta_eta_airy_minus_lorentz": format_float(airy_eta - lorentz_eta, 12),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "N",
        "preferred_m",
        "k_star",
        "L_over_R_star",
        "F_min",
        "ER_sum_lorentz_ring_dB",
        "eta_sort_lorentz_ring",
        "I_lorentz_ring_bits",
        "ER_sum_airy_exact_dB",
        "eta_sort_airy_exact",
        "I_airy_exact_bits",
        "delta_ER_sum_airy_minus_lorentz_dB",
        "delta_eta_airy_minus_lorentz",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_rows()
    write_csv(OUTPUT_CSV, rows)
    print(f"Saved: {OUTPUT_CSV}")
    for row in rows:
        print(
            "N={N}, ER_lor={ER_sum_lorentz_ring_dB} dB, ER_airy={ER_sum_airy_exact_dB} dB, "
            "eta_airy={eta_sort_airy_exact}, I_airy={I_airy_exact_bits}".format(**row)
        )


if __name__ == "__main__":
    main()
