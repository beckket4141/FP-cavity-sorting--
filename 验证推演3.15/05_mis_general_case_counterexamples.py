from __future__ import annotations

from analysis_common import (
    OUTPUT_ROOT,
    best_consecutive_block,
    build_conflict_bitmasks,
    ensure_dir,
    lr_from_k,
    max_consecutive_prefix_size,
    mis_maximum_set,
    tau_delta,
    write_csv,
)


F_NOM = 29.8
TAU0 = 3.0
N_SCAN = 15
K_GRID_STEPS = 180


def main() -> None:
    outdir = ensure_dir(OUTPUT_ROOT / "05_mis_general_case_counterexamples")
    delta = tau_delta(F_NOM, TAU0)
    rows: list[dict[str, object]] = []

    for idx in range(1, K_GRID_STEPS):
        k_value = 0.5 * idx / K_GRID_STEPS
        adj, _ = build_conflict_bitmasks(k_value, N_SCAN, delta)
        alpha_size, alpha_set = mis_maximum_set(adj)
        prefix = max_consecutive_prefix_size(k_value, N_SCAN, delta)
        consecutive_size, consecutive_block = best_consecutive_block(k_value, N_SCAN, delta)
        rows.append(
            {
                "k": f"{k_value:.12f}",
                "lr": f"{lr_from_k(k_value):.12f}",
                "mis_size": alpha_size,
                "mis_set": " ".join(str(v) for v in alpha_set),
                "prefix_size": prefix,
                "best_consecutive_block_size": consecutive_size,
                "best_consecutive_block": f"{consecutive_block[0]}-{consecutive_block[1]}",
                "gap_vs_prefix": alpha_size - prefix,
                "gap_vs_best_consecutive": alpha_size - consecutive_size,
            }
        )

    csv_path = outdir / "mis_counterexamples_scan.csv"
    write_csv(csv_path, list(rows[0].keys()), rows)

    sorted_rows = sorted(rows, key=lambda row: (row["gap_vs_best_consecutive"], row["gap_vs_prefix"]), reverse=True)
    top_rows = sorted_rows[:12]
    top_csv_path = outdir / "mis_counterexamples_top12.csv"
    write_csv(top_csv_path, list(top_rows[0].keys()), top_rows)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "mathtext.fontset": "cm"})
    fig, ax = plt.subplots(figsize=(7.8, 4.2), dpi=220)
    xs = [float(row["k"]) for row in rows]
    ys_mis = [int(row["mis_size"]) for row in rows]
    ys_prefix = [int(row["prefix_size"]) for row in rows]
    ys_block = [int(row["best_consecutive_block_size"]) for row in rows]
    ax.plot(xs, ys_mis, linewidth=1.4, label="MIS size")
    ax.plot(xs, ys_prefix, linewidth=1.2, label="continuous prefix size")
    ax.plot(xs, ys_block, linewidth=1.2, label="best consecutive block size")
    ax.set_xlabel("k")
    ax.set_ylabel("resolvable mode count")
    ax.set_title("General-case capacity: MIS vs continuous-only selections")
    ax.grid(True, alpha=0.20)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(outdir / "mis_vs_continuous_capacity.png")
    plt.close(fig)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {top_csv_path}")
    print(f"Wrote: {outdir / 'mis_vs_continuous_capacity.png'}")


if __name__ == "__main__":
    main()
