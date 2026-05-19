from __future__ import annotations

import math

from analysis_common import OUTPUT_ROOT, ensure_dir, tau_delta, write_csv


F_NOM = 29.8
TAU0 = 3.0
N_VALUES = list(range(1, 16))


def main() -> None:
    outdir = ensure_dir(OUTPUT_ROOT / "04_n9_vs_n10_boundary")
    delta = tau_delta(F_NOM, TAU0)
    rows: list[dict[str, object]] = []
    for n in N_VALUES:
        inv_n = 1.0 / n
        rows.append(
            {
                "N": n,
                "one_over_N": f"{inv_n:.12f}",
                "delta": f"{delta:.12f}",
                "margin": f"{inv_n - delta:.12f}",
                "continuous_full_load_feasible": "yes" if inv_n >= delta else "no",
                "M_max_floor(F/tau0)": math.floor(F_NOM / TAU0),
            }
        )

    csv_path = outdir / "n9_vs_n10_boundary.csv"
    write_csv(csv_path, list(rows[0].keys()), rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})
    fig, ax = plt.subplots(figsize=(6.6, 4.0), dpi=220)
    xs = [row["N"] for row in rows]
    ys = [float(row["one_over_N"]) for row in rows]
    ax.plot(xs, ys, "o-", linewidth=1.5, label=r"$1/N$")
    ax.axhline(delta, color="tab:red", linestyle="--", linewidth=1.2, label=rf"$\delta=\tau_0/\mathcal{{F}}={delta:.6f}$")
    ax.axvline(9, color="tab:green", linestyle=":", linewidth=1.1)
    ax.axvline(10, color="tab:orange", linestyle=":", linewidth=1.1)
    ax.text(9.05, ys[8] + 0.003, "N=9 feasible", fontsize=9, color="tab:green")
    ax.text(10.05, ys[9] - 0.006, "N=10 infeasible", fontsize=9, color="tab:orange")
    ax.set_xlabel("continuous mode count N")
    ax.set_ylabel("benchmark spacing")
    ax.set_title("Continuous full-load boundary for F=29.8 and tau0=3")
    ax.grid(True, alpha=0.20)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outdir / "n9_vs_n10_boundary.png")
    plt.close(fig)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {outdir / 'n9_vs_n10_boundary.png'}")


if __name__ == "__main__":
    main()

