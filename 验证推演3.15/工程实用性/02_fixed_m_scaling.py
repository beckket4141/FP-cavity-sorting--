from __future__ import annotations

import math
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from analysis_common import ensure_dir, lr_from_k, write_csv


OUTPUT_DIR = ensure_dir(BASE_DIR / "outputs" / "02_fixed_m_scaling")
RADIUS_MM = 25.0
N_MIN = 6
N_MAX = 80
FIXED_M_VALUES = [1, 2, 4, 8]
FIXED_R_VALUES = [1, 2, 4, 8]


def main() -> None:
    rows: list[dict[str, object]] = []

    for n_modes in range(N_MIN, N_MAX + 1):
        for m in FIXED_M_VALUES:
            if m >= n_modes / 2:
                continue
            k_star = m / n_modes
            lr_exact = lr_from_k(k_star)
            lr_asymptotic = (math.pi * m / n_modes) ** 2
            rows.append(
                {
                    "family": "fixed_m",
                    "N": n_modes,
                    "parameter": m,
                    "k_star": f"{k_star:.12f}",
                    "lr_exact": f"{lr_exact:.12f}",
                    "lr_asymptotic": f"{lr_asymptotic:.12f}",
                    "relative_error": f"{abs(lr_exact - lr_asymptotic) / lr_exact:.12f}",
                    "L_exact_mm": f"{RADIUS_MM * lr_exact:.9f}",
                }
            )

        if n_modes % 2 == 0:
            for r in FIXED_R_VALUES:
                m = n_modes // 2 - r
                if m <= 0:
                    continue
                k_star = m / n_modes
                lr_exact = lr_from_k(k_star)
                gap_exact = 1.0 - lr_exact
                gap_asymptotic = (math.pi * r / n_modes) ** 2
                rows.append(
                    {
                        "family": "fixed_r_to_half",
                        "N": n_modes,
                        "parameter": r,
                        "k_star": f"{k_star:.12f}",
                        "lr_exact": f"{lr_exact:.12f}",
                        "lr_asymptotic": f"{1.0 - gap_asymptotic:.12f}",
                        "relative_error": f"{abs(gap_exact - gap_asymptotic) / gap_exact:.12f}",
                        "L_exact_mm": f"{RADIUS_MM * lr_exact:.9f}",
                    }
                )

    csv_path = OUTPUT_DIR / "fixed_m_scaling.csv"
    write_csv(csv_path, list(rows[0].keys()), rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.2), dpi=220)

    ax = axes[0]
    for m in FIXED_M_VALUES:
        xs = []
        ys_exact = []
        ys_asym = []
        for n_modes in range(N_MIN, N_MAX + 1):
            if m >= n_modes / 2:
                continue
            xs.append(n_modes)
            ys_exact.append(lr_from_k(m / n_modes))
            ys_asym.append((math.pi * m / n_modes) ** 2)
        ax.plot(xs, ys_exact, linewidth=1.5, label=rf"exact $m={m}$")
        ax.plot(xs, ys_asym, linestyle="--", linewidth=1.0, alpha=0.75)
    ax.set_yscale("log")
    ax.set_xlabel("N")
    ax.set_ylabel(r"$L/R$")
    ax.set_title(r"Small fixed-$m$ branches: $L/R \sim (\pi m/N)^2$")
    ax.grid(True, alpha=0.20)
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    for r in FIXED_R_VALUES:
        xs = []
        ys_exact = []
        ys_asym = []
        for n_modes in range(N_MIN, N_MAX + 1):
            if n_modes % 2 != 0:
                continue
            m = n_modes // 2 - r
            if m <= 0:
                continue
            xs.append(n_modes)
            ys_exact.append(1.0 - lr_from_k(m / n_modes))
            ys_asym.append((math.pi * r / n_modes) ** 2)
        ax.plot(xs, ys_exact, linewidth=1.5, label=rf"exact $N/2-m={r}$")
        ax.plot(xs, ys_asym, linestyle="--", linewidth=1.0, alpha=0.75)
    ax.set_yscale("log")
    ax.set_xlabel("N")
    ax.set_ylabel(r"$1-L/R$")
    ax.set_title(r"Edge branches: $1-L/R \sim (\pi r/N)^2$")
    ax.grid(True, alpha=0.20)
    ax.legend(frameon=False, fontsize=8)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fixed_m_scaling.png")
    plt.close(fig)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {OUTPUT_DIR / 'fixed_m_scaling.png'}")


if __name__ == "__main__":
    main()
