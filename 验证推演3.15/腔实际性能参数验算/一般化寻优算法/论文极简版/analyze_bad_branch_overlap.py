from __future__ import annotations

import csv
import math
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

from analyze_q_counting_bounds import difference_set, modular_distance
from run_minimal_fullset_search import load_config


TARGET_QS = (29, 32, 35, 73)


def units(q: int) -> list[int]:
    return [m for m in range(1, q) if math.gcd(m, q) == 1]


def allowed_ms(q: int, a: Fraction, b: Fraction) -> list[int]:
    return [m for m in units(q) if a <= Fraction(m, q) <= b]


def exact_best_rho_for_q(diffs: tuple[int, ...], q: int, allowed: list[int]) -> int | None:
    if not allowed:
        return None
    best: int | None = None
    for m in allowed:
        rho = min(modular_distance(d * m, q) for d in diffs)
        if best is None or rho > best:
            best = rho
    return best


def residue_to_diffs_map(diffs: tuple[int, ...], q: int) -> dict[int, tuple[int, ...]]:
    mapping: dict[int, list[int]] = defaultdict(list)
    for d in diffs:
        residue = d % q
        if residue == 0:
            continue
        mapping[residue].append(d)
    return {residue: tuple(sorted(values)) for residue, values in sorted(mapping.items())}


def bad_set_for_residue(residue: int, q: int, allowed: list[int], r: int) -> tuple[int, ...]:
    members = tuple(sorted(m for m in allowed if modular_distance(m * residue, q) < r))
    return members


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def tuple_to_string(values: tuple[int, ...]) -> str:
    return ",".join(str(v) for v in values)


def main() -> None:
    root = Path(__file__).resolve().parent
    config = load_config(root / "minimal_example_config.json")
    out_dir = root / "results" / "bad_branch_overlap"
    out_dir.mkdir(parents=True, exist_ok=True)

    diffs = difference_set(config.candidate_modes)
    a = Fraction(str(config.search.k_min))
    b = Fraction(str(config.search.k_max))

    residue_rows: list[dict[str, object]] = []
    pattern_rows: list[dict[str, object]] = []
    union_rows: list[dict[str, object]] = []

    summary_lines: list[str] = []
    summary_lines.append("# Bad Branch Overlap Summary")
    summary_lines.append("")
    summary_lines.append(f"- Window: `[a,b]=[{a},{b}]`")
    summary_lines.append(f"- Target denominators: `{', '.join(str(q) for q in TARGET_QS)}`")
    summary_lines.append("")

    for q in TARGET_QS:
        allowed = allowed_ms(q, a, b)
        exact_rho = exact_best_rho_for_q(diffs, q, allowed)
        if exact_rho is None:
            continue

        residue_map = residue_to_diffs_map(diffs, q)
        radii = sorted({exact_rho, exact_rho + 1})

        summary_lines.append(f"## q={q}")
        summary_lines.append("")
        summary_lines.append(f"- Allowed branches: `{tuple_to_string(tuple(allowed))}`")
        summary_lines.append(f"- Exact best rho: `{exact_rho}`")

        for r in radii:
            pattern_map: dict[tuple[int, ...], list[int]] = defaultdict(list)
            covered_branches: set[int] = set()

            for residue, source_diffs in residue_map.items():
                bad_set = bad_set_for_residue(residue, q, allowed, r)
                pattern_map[bad_set].append(residue)
                covered_branches.update(bad_set)
                residue_rows.append(
                    {
                        "q": q,
                        "r": r,
                        "residue": residue,
                        "source_diffs": tuple_to_string(source_diffs),
                        "bad_branches": tuple_to_string(bad_set),
                        "bad_branch_count": len(bad_set),
                    }
                )

            for pattern, residues in sorted(pattern_map.items(), key=lambda item: (len(item[0]), item[0], item[1][0])):
                diffs_support = sorted(
                    {
                        d
                        for residue in residues
                        for d in residue_map[residue]
                    }
                )
                pattern_rows.append(
                    {
                        "q": q,
                        "r": r,
                        "pattern": tuple_to_string(pattern),
                        "pattern_size": len(pattern),
                        "support_residues": tuple_to_string(tuple(sorted(residues))),
                        "support_count": len(residues),
                        "support_diffs": tuple_to_string(tuple(diffs_support)),
                    }
                )

            survivors = tuple(sorted(set(allowed) - covered_branches))
            union_rows.append(
                {
                    "q": q,
                    "r": r,
                    "allowed_branches": tuple_to_string(tuple(allowed)),
                    "mu_q": len(allowed),
                    "covered_branches": tuple_to_string(tuple(sorted(covered_branches))),
                    "covered_count": len(covered_branches),
                    "surviving_branches": tuple_to_string(survivors),
                    "surviving_count": len(survivors),
                }
            )

            summary_lines.append(
                f"- `r={r}`: covered `{tuple_to_string(tuple(sorted(covered_branches)))}` / `{tuple_to_string(tuple(allowed))}`, "
                f"survivors `{tuple_to_string(survivors) if survivors else 'none'}`."
            )

            interesting_patterns = [
                (pattern, residues)
                for pattern, residues in pattern_map.items()
                if pattern
            ]
            for pattern, residues in sorted(interesting_patterns, key=lambda item: (len(item[0]), item[0], item[1][0])):
                summary_lines.append(
                    f"  pattern `{tuple_to_string(pattern)}` <= residues `{tuple_to_string(tuple(sorted(residues)))}`"
                )
        summary_lines.append("")

    write_csv(
        out_dir / "residue_bad_sets.csv",
        residue_rows,
        ["q", "r", "residue", "source_diffs", "bad_branches", "bad_branch_count"],
    )
    write_csv(
        out_dir / "pattern_classes.csv",
        pattern_rows,
        ["q", "r", "pattern", "pattern_size", "support_residues", "support_count", "support_diffs"],
    )
    write_csv(
        out_dir / "union_summary.csv",
        union_rows,
        ["q", "r", "allowed_branches", "mu_q", "covered_branches", "covered_count", "surviving_branches", "surviving_count"],
    )
    (out_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print("Completed bad-branch-overlap analysis.")
    print(f"Output directory: {out_dir}")


if __name__ == "__main__":
    main()
