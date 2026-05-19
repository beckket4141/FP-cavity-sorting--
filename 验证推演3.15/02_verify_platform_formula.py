from __future__ import annotations

from analysis_common import (
    OUTPUT_ROOT,
    ensure_dir,
    local_platform_formula,
    numeric_local_platform,
    sample_smin_curve_lr,
    tau_delta,
    write_csv,
)


N_MODES = 9
F_NOM = 29.8
TAU0 = 3.0
PEAKS = [1, 2, 4]


def main() -> None:
    outdir = ensure_dir(OUTPUT_ROOT / "02_platform_formula")
    delta = tau_delta(F_NOM, TAU0)
    rows: list[dict[str, object]] = []

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.6), dpi=220, sharey=True)

    for axis, m in zip(axes, PEAKS):
        analytic = local_platform_formula(N_MODES, m, delta)
        numeric = numeric_local_platform(N_MODES, m, delta)
        if analytic is None or numeric is None:
            raise RuntimeError("Expected non-empty platform for N=9 at the chosen delta")
        rows.append(
            {
                "N": N_MODES,
                "m": m,
                "delta": f"{delta:.12f}",
                "analytic_left_k": f"{analytic.left_k:.12f}",
                "analytic_right_k": f"{analytic.right_k:.12f}",
                "numeric_left_k": f"{numeric.left_k:.12f}",
                "numeric_right_k": f"{numeric.right_k:.12f}",
                "analytic_left_lr": f"{analytic.left_lr:.12f}",
                "analytic_right_lr": f"{analytic.right_lr:.12f}",
                "numeric_left_lr": f"{numeric.left_lr:.12f}",
                "numeric_right_lr": f"{numeric.right_lr:.12f}",
                "abs_error_left_lr": f"{abs(analytic.left_lr - numeric.left_lr):.12e}",
                "abs_error_right_lr": f"{abs(analytic.right_lr - numeric.right_lr):.12e}",
            }
        )

        left = min(analytic.left_lr, numeric.left_lr)
        right = max(analytic.right_lr, numeric.right_lr)
        margin = max(0.01, 0.25 * (right - left))
        curve = sample_smin_curve_lr(N_MODES, left - margin, right + margin, steps=1800)
        xs = [lr for lr, _ in curve]
        ys = [s for _, s in curve]

        axis.plot(xs, ys, color="black", linewidth=1.4)
        axis.axhline(delta, color="tab:blue", linestyle="--", linewidth=1.1)
        axis.axvspan(
            analytic.left_lr,
            analytic.right_lr,
            color="tab:green",
            alpha=0.12,
            label="analytic platform",
        )
        axis.axvspan(
            numeric.left_lr,
            numeric.right_lr,
            color="tab:orange",
            alpha=0.12,
            label="numeric platform",
        )
        axis.set_title(rf"$k^*={m}/{N_MODES}$")
        axis.set_xlabel(r"$L/R$")
        axis.grid(True, alpha=0.20)

    axes[0].set_ylabel(r"$s_{\min}$")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.suptitle("Local platform formula vs fine numeric scan for N=9", y=1.02)
    fig.tight_layout()
    fig.savefig(outdir / "platform_formula_vs_numeric_n9.png", bbox_inches="tight")
    plt.close(fig)

    csv_path = outdir / "platform_formula_vs_numeric_n9.csv"
    write_csv(csv_path, list(rows[0].keys()), rows)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {outdir / 'platform_formula_vs_numeric_n9.png'}")


if __name__ == "__main__":
    main()
