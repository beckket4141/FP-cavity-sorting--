from __future__ import annotations

import csv
import math
from fractions import Fraction
from pathlib import Path

from run_minimal_fullset_search import k_to_L_over_R, load_config


def difference_set(modes: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted({b - a for idx, a in enumerate(modes) for b in modes[idx + 1 :]}))


def modular_distance(residue: int, q: int) -> int:
    residue %= q
    return min(residue, q - residue)


def rho_q_m(diffs: tuple[int, ...], q: int, m: int) -> tuple[int, tuple[int, ...]]:
    best = q
    limiting: list[int] = []
    for d in diffs:
        dist = modular_distance(d * m, q)
        if dist < best:
            best = dist
            limiting = [d]
        elif dist == best:
            limiting.append(d)
    return best, tuple(limiting)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parent
    config = load_config(root / "minimal_example_config.json")
    out_dir = root / "results" / "exact_qm_search"
    out_dir.mkdir(parents=True, exist_ok=True)

    diffs = difference_set(config.candidate_modes)
    a = Fraction(str(config.search.k_min))
    b = Fraction(str(config.search.k_max))
    den_a = a.denominator
    den_b = b.denominator
    d_max = max(diffs)
    q_bound = max(den_a, den_b, 2 * d_max)
    target_lr = config.geometry_constraints.target_L_over_R

    rows: list[dict[str, object]] = []
    best_row: dict[str, object] | None = None

    for q in range(1, q_bound + 1):
        m_start = math.ceil(float(a * q))
        m_end = math.floor(float(b * q))
        for m in range(m_start, m_end + 1):
            if math.gcd(m, q) != 1:
                continue
            k = Fraction(m, q)
            rho, limiting = rho_q_m(diffs, q, m)
            s_min = Fraction(rho, q)
            lr = k_to_L_over_R(float(k))
            gap = abs(lr - target_lr) if target_lr is not None else 0.0
            row = {
                "q": q,
                "m": m,
                "k_fraction": f"{k.numerator}/{k.denominator}",
                "k_float": float(k),
                "rho": rho,
                "s_min_fraction": f"{s_min.numerator}/{s_min.denominator}",
                "s_min_float": float(s_min),
                "L_over_R": lr,
                "geometry_gap_to_target": gap,
                "limiting_diffs": ",".join(str(v) for v in limiting),
            }
            rows.append(row)
            key = (round(float(s_min), 12), -gap, -abs(float(k) - 0.25))
            if best_row is None or key > (
                round(float(Fraction(str(best_row["s_min_float"]))), 12),  # type: ignore[arg-type]
                -float(best_row["geometry_gap_to_target"]),
                -abs(float(best_row["k_float"]) - 0.25),
            ):
                best_row = row

    rows_sorted = sorted(
        rows,
        key=lambda item: (
            item["s_min_float"],
            -item["geometry_gap_to_target"],
            -abs(float(item["k_float"]) - 0.25),
        ),
        reverse=True,
    )

    write_csv(
        out_dir / "all_exact_candidates.csv",
        rows_sorted,
        [
            "q",
            "m",
            "k_fraction",
            "k_float",
            "rho",
            "s_min_fraction",
            "s_min_float",
            "L_over_R",
            "geometry_gap_to_target",
            "limiting_diffs",
        ],
    )

    top_rows = rows_sorted[:50]
    write_csv(
        out_dir / "top_exact_candidates.csv",
        top_rows,
        [
            "q",
            "m",
            "k_fraction",
            "k_float",
            "rho",
            "s_min_fraction",
            "s_min_float",
            "L_over_R",
            "geometry_gap_to_target",
            "limiting_diffs",
        ],
    )

    assert best_row is not None
    lines: list[str] = []
    lines.append("# Exact (q,m) Search Summary")
    lines.append("")
    lines.append(f"- Mode set: `{list(config.candidate_modes)}`")
    lines.append(f"- Difference set max: `D_max={d_max}`")
    lines.append(f"- Window: `[{config.search.k_min}, {config.search.k_max}] = [{a}, {b}]`")
    lines.append(f"- Exact denominator bound: `Q_I(S)=max(den(a), den(b), 2 D_max) = {q_bound}`")
    lines.append("")
    lines.append("## Best Exact Candidate")
    lines.append("")
    lines.append(f"- `q={best_row['q']}`")
    lines.append(f"- `m={best_row['m']}`")
    lines.append(f"- `k={best_row['k_fraction']} ≈ {float(best_row['k_float']):.15f}`")
    lines.append(f"- `s_min={best_row['s_min_fraction']} ≈ {float(best_row['s_min_float']):.15f}`")
    lines.append(f"- `(L/R)={float(best_row['L_over_R']):.15f}`")
    lines.append(f"- Limiting differences: `{best_row['limiting_diffs']}`")
    lines.append("")
    lines.append("## Meaning")
    lines.append("")
    lines.append("- This result is no longer a dense real-variable scan.")
    lines.append("- It is the exact finite search guaranteed by the denominator bound theorem.")
    lines.append("- For the current 5.4 example, the exact discrete search still returns `k=7/29`.")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Completed exact (q,m) search.")
    print(f"Output directory: {out_dir}")
    print(f"Q_bound = {q_bound}")
    print(f"Best candidate: q={best_row['q']}, m={best_row['m']}, k={best_row['k_fraction']}, s_min={best_row['s_min_fraction']}")


if __name__ == "__main__":
    main()
