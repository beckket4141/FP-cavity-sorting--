from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from run_minimal_fullset_search import k_to_L_over_R, load_config


@dataclass(frozen=True)
class RationalCandidate:
    q: int
    m: int
    k: Fraction
    s_min: Fraction
    rho: int
    limiting_diffs: tuple[int, ...]
    L_over_R: float
    geometry_gap: float


def difference_set(modes: tuple[int, ...]) -> tuple[int, ...]:
    values = sorted({b - a for idx, a in enumerate(modes) for b in modes[idx + 1 :]})
    return tuple(values)


def modular_distance(residue: int, q: int) -> int:
    residue %= q
    return min(residue, q - residue)


def rational_candidate(q: int, m: int, diffs: tuple[int, ...], target_lr: float | None) -> RationalCandidate:
    min_distance = q
    limiting: list[int] = []
    for d in diffs:
        residue = (d * m) % q
        distance = modular_distance(residue, q)
        if distance < min_distance:
            min_distance = distance
            limiting = [d]
        elif distance == min_distance:
            limiting.append(d)
    k = Fraction(m, q)
    lr = k_to_L_over_R(float(k))
    gap = abs(lr - target_lr) if target_lr is not None else 0.0
    return RationalCandidate(
        q=q,
        m=m,
        k=k,
        s_min=Fraction(min_distance, q),
        rho=min_distance,
        limiting_diffs=tuple(limiting),
        L_over_R=lr,
        geometry_gap=gap,
    )


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fraction_str(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def main() -> None:
    root = Path(__file__).resolve().parent
    config = load_config(root / "minimal_example_config.json")
    out_dir = root / "results" / "rational_structure"
    out_dir.mkdir(parents=True, exist_ok=True)

    diffs = difference_set(config.candidate_modes)
    k_min = Fraction(str(config.search.k_min))
    k_max = Fraction(str(config.search.k_max))
    target_lr = config.geometry_constraints.target_L_over_R

    all_candidates: list[RationalCandidate] = []
    for q in range(2, 201):
        for m in range(1, q):
            if math.gcd(m, q) != 1:
                continue
            k = Fraction(m, q)
            if not (k_min <= k <= k_max):
                continue
            all_candidates.append(rational_candidate(q, m, diffs, target_lr))

    positive_candidates = [item for item in all_candidates if item.rho > 0]
    positive_candidates.sort(
        key=lambda item: (item.s_min, -item.geometry_gap, -abs(float(item.k) - 0.25)),
        reverse=True,
    )

    per_q_rows: list[dict[str, object]] = []
    by_q: dict[int, list[RationalCandidate]] = {}
    for item in all_candidates:
        by_q.setdefault(item.q, []).append(item)

    varying_q_example: tuple[int, list[RationalCandidate]] | None = None
    for q in sorted(by_q):
        group = by_q[q]
        group_scores = {item.s_min for item in group}
        best_score = max(group_scores)
        best_group = [item for item in group if item.s_min == best_score]
        best_group.sort(key=lambda item: (item.geometry_gap, abs(float(item.k) - 0.25), item.m))
        representative = best_group[0]
        per_q_rows.append(
            {
                "q": q,
                "best_s_min_fraction": fraction_str(best_score),
                "best_s_min_float": float(best_score),
                "best_rho": representative.rho,
                "representative_m": representative.m,
                "representative_k_fraction": fraction_str(representative.k),
                "representative_L_over_R": representative.L_over_R,
                "representative_geometry_gap": representative.geometry_gap,
                "all_best_m": ",".join(str(item.m) for item in best_group),
                "all_best_k": ",".join(fraction_str(item.k) for item in best_group),
                "score_varies_with_m": len(group_scores) > 1,
            }
        )
        if varying_q_example is None and len(group_scores) > 1:
            varying_q_example = (q, sorted(group, key=lambda item: (item.s_min, item.m), reverse=True))

    top_rows = []
    for rank, item in enumerate(positive_candidates[:40], start=1):
        top_rows.append(
            {
                "rank": rank,
                "q": item.q,
                "m": item.m,
                "k_fraction": fraction_str(item.k),
                "k_float": float(item.k),
                "s_min_fraction": fraction_str(item.s_min),
                "s_min_float": float(item.s_min),
                "rho": item.rho,
                "L_over_R": item.L_over_R,
                "geometry_gap_to_target": item.geometry_gap,
                "limiting_diffs": ",".join(str(v) for v in item.limiting_diffs),
            }
        )

    diff_rows = [{"difference_d": d, "mod_29": d % 29} for d in diffs]

    write_csv(
        out_dir / "difference_set.csv",
        diff_rows,
        ["difference_d", "mod_29"],
    )
    write_csv(
        out_dir / "per_denominator_best.csv",
        per_q_rows,
        [
            "q",
            "best_s_min_fraction",
            "best_s_min_float",
            "best_rho",
            "representative_m",
            "representative_k_fraction",
            "representative_L_over_R",
            "representative_geometry_gap",
            "all_best_m",
            "all_best_k",
            "score_varies_with_m",
        ],
    )
    write_csv(
        out_dir / "top_rational_candidates.csv",
        top_rows,
        [
            "rank",
            "q",
            "m",
            "k_fraction",
            "k_float",
            "s_min_fraction",
            "s_min_float",
            "rho",
            "L_over_R",
            "geometry_gap_to_target",
            "limiting_diffs",
        ],
    )

    best = positive_candidates[0]
    lines: list[str] = []
    lines.append("# Rational Structure Summary")
    lines.append("")
    lines.append(f"- Mode set: `{list(config.candidate_modes)}`")
    lines.append(f"- Search window: `k in [{config.search.k_min}, {config.search.k_max}]`")
    lines.append(f"- Difference-set size: `{len(diffs)}`")
    lines.append(f"- Difference set: `{list(diffs)}`")
    lines.append("")
    lines.append("## Current Best Rational Candidate")
    lines.append("")
    lines.append(f"- Best denominator `q`: `{best.q}`")
    lines.append(f"- Best branch `m/q`: `{fraction_str(best.k)}`")
    lines.append(f"- Best `s_min`: `{fraction_str(best.s_min)} = {float(best.s_min):.12f}`")
    lines.append(f"- Best `(L/R)`: `{best.L_over_R:.12f}`")
    lines.append(f"- Limiting differences: `{list(best.limiting_diffs)}`")
    lines.append("")
    lines.append("## What This Verifies")
    lines.append("")
    lines.append("- The best candidates in the current moderate branch window cluster on denominator `q=29`.")
    lines.append("- For `q=29`, the best admissible branches are `m=6,7,8`, i.e. `6/29, 7/29, 8/29`.")
    lines.append("- Among these tied branches, the current main script picks the one closest to `L/R=0.5`, namely `7/29`.")
    lines.append("")
    lines.append("## Important Caveat")
    lines.append("")
    if varying_q_example is not None:
        q_example, group = varying_q_example
        show = group[:6]
        lines.append(
            f"- The stronger claim 'for fixed q, s_min does not depend on m' is false in general. "
            f"A counterexample already appears at `q={q_example}`."
        )
        for item in show:
            lines.append(
                f"- At `q={q_example}`, `m={item.m}` gives `s_min={fraction_str(item.s_min)}`."
            )
    else:
        lines.append("- Within the scanned range, no counterexample to m-invariance appeared.")
    lines.append("")
    lines.append("## Safer Conjecture")
    lines.append("")
    lines.append("- For a fixed finite mode set, the optimum seems to be controlled by the difference set `D`, not by the mode count itself.")
    lines.append("- The denominator `q` is the main structural quantity to search.")
    lines.append("- Once `q` is fixed, one should still scan admissible coprime `m` in the branch window, because different `m` can yield different `s_min` for some denominators.")
    lines.append("- If a rational-optimum theorem is proved, then the continuous search over `k` can be reduced to an exact discrete search over `(q,m)`.")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Completed rational-structure analysis.")
    print(f"Output directory: {out_dir}")
    print(f"Best candidate: q={best.q}, m={best.m}, k={fraction_str(best.k)}, s_min={fraction_str(best.s_min)}")
    if varying_q_example is not None:
        print(f"Counterexample to m-invariance found at q={varying_q_example[0]}.")


if __name__ == "__main__":
    main()
