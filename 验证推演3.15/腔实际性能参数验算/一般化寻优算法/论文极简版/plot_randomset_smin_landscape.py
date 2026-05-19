from __future__ import annotations

import argparse
import csv
from pathlib import Path

from run_minimal_fullset_search import (
    evaluate_k,
    linspace,
    load_config,
    passes_geometry_constraints,
    rational_hint,
    rank_key,
    snap_best_to_clean_rational,
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "k",
                "k_rational_hint",
                "L_over_R",
                "s_min",
                "limiting_mode_i",
                "limiting_mode_j",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot the s_min landscape for the random mode set used in thesis Section 5.4."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent / "minimal_example_config.json",
        help="Path to the minimal example config.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path(__file__).resolve().parent / "results" / "figures",
        help="Directory for figure outputs.",
    )
    parser.add_argument(
        "--stem",
        default="randomset_smin_landscape",
        help="Output filename stem.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=600,
        help="PNG DPI.",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Also export the plotted curve to CSV.",
    )
    args = parser.parse_args()

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("matplotlib is required to generate the landscape figure.") from exc

    config = load_config(args.config)

    rows = []
    best = None
    for k in linspace(config.search.k_min, config.search.k_max, config.search.coarse_samples):
        row = evaluate_k(config.candidate_modes, k)
        if not passes_geometry_constraints(row, config.geometry_constraints):
            continue
        rows.append(row)
        if best is None or rank_key(row, config.geometry_constraints) > rank_key(best, config.geometry_constraints):
            best = row

    if best is None:
        raise RuntimeError("No feasible point survived the configured geometry constraints.")

    best = snap_best_to_clean_rational(best, config.candidate_modes, config)

    lr_values = [row.L_over_R for row in rows]
    s_values = [row.s_min for row in rows]
    ymax = max(s_values) * 1.15

    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.labelsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "mathtext.fontset": "cm",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.unicode_minus": False,
        }
    )

    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    ax.plot(lr_values, s_values, color="black", linewidth=1.3, alpha=0.95, zorder=3)
    ax.plot(best.L_over_R, best.s_min, "o", color="red", markersize=4.5, zorder=5)
    ax.axvline(best.L_over_R, linestyle=":", color="red", linewidth=1.0, alpha=0.65, zorder=2)
    ax.axhline(best.s_min, linestyle="--", color="tab:blue", linewidth=1.0, alpha=0.45, zorder=1)

    best_text = (
        rf"best: $k^*={rational_hint(best.k) or f'{best.k:.6f}'}$" + "\n"
        rf"$(L/R)^*={best.L_over_R:.4f}$" + "\n"
        rf"$s_{{\min}}^*={best.s_min:.4f}$"
    )
    ax.annotate(
        best_text,
        xy=(best.L_over_R, best.s_min),
        xytext=(10, -8),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=9,
        color="red",
    )

    ax.set_xlabel(r"$L/R$")
    ax.set_ylabel(r"$s_{\min}$")
    ax.set_xlim(min(lr_values), max(lr_values))
    ax.set_ylim(0.0, ymax)
    ax.grid(True, which="both", alpha=0.22)

    args.outdir.mkdir(parents=True, exist_ok=True)
    png_path = args.outdir / f"{args.stem}.png"
    pdf_path = args.outdir / f"{args.stem}.pdf"
    fig.tight_layout()
    fig.savefig(png_path, dpi=args.dpi)
    fig.savefig(pdf_path)
    plt.close(fig)

    if args.csv:
        csv_rows = [
            {
                "k": row.k,
                "k_rational_hint": rational_hint(row.k),
                "L_over_R": row.L_over_R,
                "s_min": row.s_min,
                "limiting_mode_i": row.limiting_pair[0],
                "limiting_mode_j": row.limiting_pair[1],
            }
            for row in rows
        ]
        write_csv(args.outdir / f"{args.stem}.csv", csv_rows)

    print("Completed random-set s_min landscape plot.")
    print(f"PNG : {png_path}")
    print(f"PDF : {pdf_path}")
    print(f"Best k*: {best.k:.15f}")
    print(f"Best L/R*: {best.L_over_R:.15f}")
    print(f"Best s_min*: {best.s_min:.15f}")


if __name__ == "__main__":
    main()
