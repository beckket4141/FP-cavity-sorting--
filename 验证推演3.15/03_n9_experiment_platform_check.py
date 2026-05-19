from __future__ import annotations

import math

from analysis_common import (
    OUTPUT_ROOT,
    ensure_dir,
    local_platform_formula,
    numeric_local_platform,
    sample_smin_curve_lr,
    smin_for_lr,
    tau_delta,
    write_csv,
)


N_MODES = 9
M_BRANCH = 2
RADIUS_MM = 25.0
L_NOM_MM = 10.25
LR_NOM = L_NOM_MM / RADIUS_MM
TAU0 = 3.0
F_CASES = [("design_nominal", 29.8), ("experiment_finesse", 31.35)]


def main() -> None:
    outdir = ensure_dir(OUTPUT_ROOT / "03_n9_experiment_platform_check")
    rows: list[dict[str, object]] = []

    for case_name, finesse in F_CASES:
        delta = tau_delta(finesse, TAU0)
        analytic = local_platform_formula(N_MODES, M_BRANCH, delta)
        numeric = numeric_local_platform(N_MODES, M_BRANCH, delta)
        if analytic is None or numeric is None:
            raise RuntimeError(f"No platform found for {case_name}")
        s_nom = smin_for_lr(LR_NOM, 1, N_MODES)
        lr_star = math.sin(math.pi * (M_BRANCH / N_MODES)) ** 2
        rows.append(
            {
                "case": case_name,
                "F": f"{finesse:.6f}",
                "tau0": f"{TAU0:.6f}",
                "delta": f"{delta:.12f}",
                "k_star": f"{M_BRANCH / N_MODES:.12f}",
                "lr_star": f"{lr_star:.12f}",
                "L_star_mm": f"{RADIUS_MM * lr_star:.9f}",
                "analytic_left_lr": f"{analytic.left_lr:.12f}",
                "analytic_right_lr": f"{analytic.right_lr:.12f}",
                "analytic_left_L_mm": f"{RADIUS_MM * analytic.left_lr:.9f}",
                "analytic_right_L_mm": f"{RADIUS_MM * analytic.right_lr:.9f}",
                "numeric_left_lr": f"{numeric.left_lr:.12f}",
                "numeric_right_lr": f"{numeric.right_lr:.12f}",
                "L_nom_mm": f"{L_NOM_MM:.9f}",
                "lr_nom": f"{LR_NOM:.12f}",
                "smin_at_nominal_lr": f"{s_nom:.12f}",
                "tau_eff_at_nominal_lr": f"{finesse * s_nom:.12f}",
                "nominal_offset_from_peak_mm": f"{L_NOM_MM - RADIUS_MM * lr_star:.9f}",
                "margin_to_left_mm": f"{L_NOM_MM - RADIUS_MM * analytic.left_lr:.9f}",
                "margin_to_right_mm": f"{RADIUS_MM * analytic.right_lr - L_NOM_MM:.9f}",
            }
        )

    csv_path = outdir / "n9_experiment_platform_check.csv"
    write_csv(csv_path, list(rows[0].keys()), rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=220)
    curve = sample_smin_curve_lr(N_MODES, 0.38, 0.44, steps=2400)
    xs = [lr for lr, _ in curve]
    ys = [s for _, s in curve]
    ax.plot(xs, ys, color="black", linewidth=1.5, label=r"$s_{\min}$ for $N=1\sim 9$")

    colors = {"design_nominal": "tab:blue", "experiment_finesse": "tab:green"}
    labels = {
        "design_nominal": r"design threshold $\delta=3/29.8$",
        "experiment_finesse": r"experimental threshold $\delta=3/31.35$",
    }
    for row in rows:
        color = colors[str(row["case"])]
        delta = float(row["delta"])
        left_lr = float(row["analytic_left_lr"])
        right_lr = float(row["analytic_right_lr"])
        ax.axhline(delta, color=color, linestyle="--", linewidth=1.1, label=labels[str(row["case"])])
        ax.axvspan(left_lr, right_lr, color=color, alpha=0.10)

    lr_star = float(rows[0]["lr_star"])
    ax.axvline(lr_star, color="tab:red", linestyle=":", linewidth=1.2, label=r"analytic peak $L/R=\sin^2(2\pi/9)$")
    ax.plot([LR_NOM], [smin_for_lr(LR_NOM, 1, N_MODES)], "o", color="tab:red", markersize=5, label=r"nominal point $L/R=0.410$")
    ax.set_xlim(0.38, 0.44)
    ax.set_ylim(0.095, 0.1155)
    ax.set_xlabel(r"$L/R$")
    ax.set_ylabel(r"$s_{\min}$")
    ax.set_title("N=9: analytic design peak, tau thresholds, and platform width")
    ax.grid(True, alpha=0.20)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(outdir / "n9_experiment_platform_check.png")
    plt.close(fig)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {outdir / 'n9_experiment_platform_check.png'}")


if __name__ == "__main__":
    main()
