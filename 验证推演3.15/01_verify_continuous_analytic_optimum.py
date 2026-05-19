from __future__ import annotations

from pathlib import Path

from analysis_common import (
    OUTPUT_ROOT,
    analytic_peak_families,
    ensure_dir,
    global_numeric_peak,
    lr_from_k,
    nearest_peak_family,
    write_csv,
)


N_VALUES = [9, 10, 30, 50, 100]
NUMERIC_SCAN_STEPS = 120_000


def main() -> None:
    outdir = ensure_dir(OUTPUT_ROOT / "01_continuous_analytic_optimum")
    rows: list[dict[str, object]] = []

    for n_modes in N_VALUES:
        k_num, s_num = global_numeric_peak(n_modes, steps=NUMERIC_SCAN_STEPS)
        nearest = nearest_peak_family(n_modes, k_num)
        rows.append(
            {
                "N": n_modes,
                "numeric_k_peak": f"{k_num:.12f}",
                "numeric_lr_peak": f"{lr_from_k(k_num):.12f}",
                "numeric_smin_peak": f"{s_num:.12f}",
                "analytic_smin_peak": f"{1.0 / n_modes:.12f}",
                "matched_family_m": nearest.m,
                "matched_family_k": f"{nearest.k_star:.12f}",
                "matched_family_lr": f"{nearest.lr_star:.12f}",
                "abs_error_smin": f"{abs(s_num - 1.0 / n_modes):.12e}",
                "abs_error_k": f"{abs(k_num - nearest.k_star):.12e}",
                "visible_peak_families": len(analytic_peak_families(n_modes)),
            }
        )

    csv_path = outdir / "continuous_analytic_optimum_summary.csv"
    write_csv(csv_path, list(rows[0].keys()), rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs = [row["N"] for row in rows]
    ys_numeric = [float(row["numeric_smin_peak"]) for row in rows]
    ys_analytic = [float(row["analytic_smin_peak"]) for row in rows]

    plt.rcParams.update({"font.size": 11, "mathtext.fontset": "cm"})
    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=220)
    ax.plot(xs, ys_analytic, "o-", linewidth=1.8, label=r"analytic optimum $1/N$")
    ax.plot(xs, ys_numeric, "s--", linewidth=1.6, label="numeric scan maximum")
    ax.set_xlabel("continuous mode count N")
    ax.set_ylabel(r"peak $s_{\min}$")
    ax.set_title("Continuous-set optimum: analytic benchmark vs numeric scan")
    ax.grid(True, alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outdir / "continuous_analytic_optimum_vs_numeric.png")
    plt.close(fig)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {outdir / 'continuous_analytic_optimum_vs_numeric.png'}")


if __name__ == "__main__":
    main()

