#!/usr/bin/env python3
"""Check the exact finite-dimensional Airy circular sum and its large-M limit.

This script verifies three facts for the threshold-scaled consecutive family
F = M * tau0:

1. The direct finite Airy circular sum matches a closed-form expression.
2. As M -> infinity, the exact Airy sum converges to
      pi/(2*tau0) * coth(pi/(2*tau0)) - 1
   which is also the Lorentzian infinite-line sum.
3. For representative tau0 and M, the finite Airy sum stays below that limit.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent
OUTPUT_CSV = OUTPUT_DIR / "airy_circle_limit_check.csv"
OUTPUT_TXT = OUTPUT_DIR / "airy_circle_limit_check.txt"

TAU0_VALUES = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
M_VALUES = [4, 5, 6, 7, 8, 9, 10, 15, 30, 50, 100, 300, 1000]


def airy_noise_direct(m: int, tau0: float) -> float:
    finesse = m * tau0
    total = 0.0
    prefactor = (2.0 * finesse / math.pi) ** 2
    for n in range(1, m):
        total += 1.0 / (1.0 + prefactor * (math.sin(math.pi * n / m) ** 2))
    return total


def airy_noise_closed_form(m: int, tau0: float) -> float:
    a = (2.0 * m * tau0 / math.pi) ** 2
    delta = math.sqrt(1.0 + a)
    q = (delta - 1.0) / (delta + 1.0)
    return (m / delta) * ((1.0 + q**m) / (1.0 - q**m)) - 1.0


def lorentz_infinite_sum_closed_form(tau0: float) -> float:
    x = math.pi / (2.0 * tau0)
    return x * (math.cosh(x) / math.sinh(x)) - 1.0


def er_db_from_noise(noise: float) -> float:
    return 10.0 * math.log10(1.0 / noise)


def main() -> None:
    rows: list[dict[str, str]] = []
    lines: list[str] = []

    lines.append("Exact finite-dimensional Airy circular sum vs. its large-M limit")
    lines.append("")
    lines.append(
        "Model: consecutive M-mode family at fixed threshold tau0, with F = M * tau0."
    )
    lines.append(
        "The direct Airy sum on the circle is compared with an exact closed form and with"
    )
    lines.append(
        "the large-M limit pi/(2*tau0) * coth(pi/(2*tau0)) - 1, which equals the Lorentzian"
    )
    lines.append("infinite-line sum.")
    lines.append("")

    for tau0 in TAU0_VALUES:
        limit_noise = lorentz_infinite_sum_closed_form(tau0)
        limit_er = er_db_from_noise(limit_noise)
        lines.append(
            f"tau0={tau0:.1f}: limit_noise={limit_noise:.12f}, limit_ER={limit_er:.9f} dB"
        )
        monotone_ok = True
        previous = -1.0
        for m in M_VALUES:
            direct = airy_noise_direct(m, tau0)
            closed = airy_noise_closed_form(m, tau0)
            if previous >= 0.0 and direct + 1e-12 < previous:
                monotone_ok = False
            previous = direct
            rows.append(
                {
                    "tau0": f"{tau0:.1f}",
                    "M": str(m),
                    "noise_direct": f"{direct:.15f}",
                    "noise_closed_form": f"{closed:.15f}",
                    "abs_diff_direct_vs_closed": f"{abs(direct - closed):.3e}",
                    "limit_noise": f"{limit_noise:.15f}",
                    "limit_minus_direct": f"{limit_noise - direct:.15f}",
                    "ER_direct_dB": f"{er_db_from_noise(direct):.9f}",
                    "ER_limit_dB": f"{limit_er:.9f}",
                }
            )
        lines.append(f"  monotone_in_M_on_test_grid = {monotone_ok}")
        sample_ms = [4, 9, 30, 100, 1000]
        for m in sample_ms:
            direct = airy_noise_direct(m, tau0)
            lines.append(
                f"  M={m:4d}: noise={direct:.12f}, limit-direct={limit_noise - direct:.12e}, "
                f"ER={er_db_from_noise(direct):.9f} dB"
            )
        lines.append("")

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "tau0",
                "M",
                "noise_direct",
                "noise_closed_form",
                "abs_diff_direct_vs_closed",
                "limit_noise",
                "limit_minus_direct",
                "ER_direct_dB",
                "ER_limit_dB",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    OUTPUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUTPUT_CSV}")
    print(f"Wrote {OUTPUT_TXT}")


if __name__ == "__main__":
    main()
