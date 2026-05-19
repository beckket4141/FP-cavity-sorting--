from __future__ import annotations

import csv
import math
from fractions import Fraction
from pathlib import Path
from collections import defaultdict


def arithmetic_progression_mode_set(
    n_start: int,
    delta_ord: int,
    mode_count: int,
) -> tuple[int, ...]:
    return tuple(n_start + delta_ord * t for t in range(mode_count))


def difference_set(modes: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted({b - a for idx, a in enumerate(modes) for b in modes[idx + 1 :]}))


def modular_distance(residue: int, q: int) -> int:
    residue %= q
    return min(residue, q - residue)


def exact_best_over_k(
    modes: tuple[int, ...],
    q_max: int = 800,
) -> tuple[Fraction, list[Fraction]]:
    diffs = difference_set(modes)
    best: Fraction | None = None
    best_ks: list[Fraction] = []

    for q in range(1, q_max + 1):
        for p in range(1, (q // 2) + 1):
            if math.gcd(p, q) != 1:
                continue
            rho = min(modular_distance(d * p, q) for d in diffs)
            s_min = Fraction(rho, q)
            if best is None or s_min > best:
                best = s_min
                best_ks = [Fraction(p, q)]
            elif s_min == best:
                best_ks.append(Fraction(p, q))

    assert best is not None
    return best, sorted(set(best_ks))


def predicted_full_optimal_k_family(
    mode_count: int,
    delta_ord: int,
) -> list[Fraction]:
    candidates: set[Fraction] = set()
    half = Fraction(1, 2)

    for branch in range(1, mode_count):
        if math.gcd(branch, mode_count) != 1:
            continue
        for n in range(delta_ord):
            k = Fraction(n * mode_count + branch, mode_count * delta_ord)
            if 0 < k < half:
                candidates.add(k)

    return sorted(candidates)


def predicted_minimal_subfamily(
    mode_count: int,
    delta_ord: int,
) -> list[Fraction]:
    candidates: list[Fraction] = []
    for branch in range(1, mode_count):
        if math.gcd(branch, mode_count) != 1:
            continue
        k = Fraction(branch, mode_count * delta_ord)
        if 0 < k < Fraction(1, 2):
            candidates.append(k)
    return sorted(set(candidates))


def fraction_list_to_string(values: list[Fraction]) -> str:
    return ",".join(str(value) for value in values)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parent
    out_dir = root / "results" / "arithmetic_progression_closed_form"
    out_dir.mkdir(parents=True, exist_ok=True)

    test_cases = [
        (1, 1, 5),
        (1, 2, 5),
        (1, 3, 5),
        (3, 3, 5),
        (1, 2, 9),
        (1, 3, 9),
        (1, 4, 9),
        (4, 4, 9),
        (1, 5, 7),
        (2, 5, 7),
        (1, 6, 8),
        (5, 6, 8),
    ]

    rows: list[dict[str, object]] = []
    lines: list[str] = []
    lines.append("# Arithmetic-Progression Closed-Form Verification")
    lines.append("")
    lines.append("This report verifies the closed-form claim for equally spaced mode-order sets")
    lines.append("`S_{N_\\mathrm{start},\\Delta_\\mathrm{ord},M}`.")
    lines.append("The exact search is compared against the predicted unconstrained optimum")
    lines.append("`s_min^*=1/M` and against the full optimal branch family")
    lines.append("`k^*=(n+m/M)/\\Delta_\\mathrm{ord}` with `gcd(m,M)=1` and `0<k^*<1/2`.")
    lines.append("")

    family_by_spacing_key: dict[tuple[int, int], list[dict[str, object]]] = defaultdict(list)
    best_value_match_count = 0
    full_family_match_count = 0
    minimal_contained_count = 0
    strict_full_family_cases: list[str] = []

    for n_start, delta_ord, mode_count in test_cases:
        modes = arithmetic_progression_mode_set(n_start, delta_ord, mode_count)
        exact_best, exact_best_ks = exact_best_over_k(modes)
        predicted_best = Fraction(1, mode_count)
        predicted_full = predicted_full_optimal_k_family(mode_count, delta_ord)
        predicted_minimal = predicted_minimal_subfamily(mode_count, delta_ord)

        best_value_match = exact_best == predicted_best
        full_match = exact_best_ks == predicted_full
        minimal_contained = all(k in exact_best_ks for k in predicted_minimal)
        strict_full_family = predicted_full != predicted_minimal

        if best_value_match:
            best_value_match_count += 1
        if full_match:
            full_family_match_count += 1
        if minimal_contained:
            minimal_contained_count += 1
        if strict_full_family:
            strict_full_family_cases.append(
                f"(N_start={n_start}, Delta_ord={delta_ord}, M={mode_count})"
            )

        rows.append(
            {
                "N_start": n_start,
                "Delta_ord": delta_ord,
                "M": mode_count,
                "mode_set": ",".join(str(v) for v in modes),
                "exact_best_s_min": str(exact_best),
                "predicted_best_s_min": str(predicted_best),
                "matches_best_value": best_value_match,
                "exact_best_branch_count": len(exact_best_ks),
                "exact_best_branch_family": fraction_list_to_string(exact_best_ks),
                "predicted_full_branch_count": len(predicted_full),
                "predicted_full_branch_family": fraction_list_to_string(predicted_full),
                "predicted_full_family_matches_exact_search": full_match,
                "predicted_minimal_subfamily_count": len(predicted_minimal),
                "predicted_minimal_subfamily": fraction_list_to_string(predicted_minimal),
                "minimal_subfamily_contained_in_exact_search": minimal_contained,
                "full_family_strictly_larger_than_minimal_subfamily": strict_full_family,
            }
        )

        family_by_spacing_key[(delta_ord, mode_count)].append(
            {
                "N_start": n_start,
                "exact_best_s_min": exact_best,
                "exact_best_ks": tuple(exact_best_ks),
            }
        )

        lines.append(
            f"## N_start={n_start}, Delta_ord={delta_ord}, M={mode_count}"
        )
        lines.append("")
        lines.append(f"- Mode set: `{list(modes)}`")
        lines.append(f"- Exact best `s_min`: `{exact_best}`")
        lines.append(f"- Predicted best `s_min`: `1/{mode_count}`")
        lines.append(f"- Exact best branch family: `{', '.join(str(v) for v in exact_best_ks)}`")
        lines.append(
            f"- Predicted full optimal family `k=(n+m/M)/Delta_ord`: `{', '.join(str(v) for v in predicted_full)}`"
        )
        lines.append(f"- Full family matches exact search: `{full_match}`")
        lines.append(
            f"- Predicted minimal subfamily `k=m/(M Delta_ord)`: `{', '.join(str(v) for v in predicted_minimal)}`"
        )
        lines.append(f"- Minimal subfamily contained in exact search: `{minimal_contained}`")
        lines.append(
            f"- Full family strictly larger than minimal subfamily: `{strict_full_family}`"
        )
        lines.append("")

    spacing_group_checks: list[dict[str, object]] = []
    spacing_invariance_match_count = 0
    for (delta_ord, mode_count), entries in sorted(family_by_spacing_key.items()):
        if len(entries) < 2:
            continue

        reference_value = entries[0]["exact_best_s_min"]
        reference_family = entries[0]["exact_best_ks"]
        invariant = all(
            entry["exact_best_s_min"] == reference_value and entry["exact_best_ks"] == reference_family
            for entry in entries[1:]
        )
        if invariant:
            spacing_invariance_match_count += 1

        spacing_group_checks.append(
            {
                "Delta_ord": delta_ord,
                "M": mode_count,
                "N_start_values": ",".join(str(entry["N_start"]) for entry in entries),
                "exact_best_s_min": str(reference_value),
                "exact_best_branch_family": fraction_list_to_string(list(reference_family)),
                "N_start_invariance_match": invariant,
            }
        )

    lines.insert(7, "## Global Summary")
    lines.insert(8, "")
    lines.insert(9, f"- Total test cases: `{len(test_cases)}`")
    lines.insert(10, f"- Cases with exact best value `1/M`: `{best_value_match_count}/{len(test_cases)}`")
    lines.insert(11, f"- Cases where the full optimal family matches exact search: `{full_family_match_count}/{len(test_cases)}`")
    lines.insert(12, f"- Cases where the minimal subfamily is contained in exact search: `{minimal_contained_count}/{len(test_cases)}`")
    if spacing_group_checks:
        lines.insert(
            13,
            f"- Repeated `(Delta_ord, M)` groups passing `N_start`-invariance: `{spacing_invariance_match_count}/{len(spacing_group_checks)}`",
        )
        insert_idx = 14
    else:
        insert_idx = 13
    if strict_full_family_cases:
        lines.insert(
            insert_idx,
            "- Cases where the full optimal family is strictly larger than the minimal subfamily: "
            + f"`{'; '.join(strict_full_family_cases)}`",
        )
        lines.insert(insert_idx + 1, "")
    else:
        lines.insert(insert_idx, "- No case produced a full family larger than the minimal subfamily.")
        lines.insert(insert_idx + 1, "")

    if spacing_group_checks:
        lines.append("## N_start Invariance Check")
        lines.append("")
        lines.append(
            "The theory predicts that `N_start` only translates the orbit on the circle and should not change either"
        )
        lines.append("the optimal value or the optimal branch family. The repeated `(Delta_ord, M)` pairs below verify this directly.")
        lines.append("")
        for row in spacing_group_checks:
            lines.append(
                f"- Delta_ord={row['Delta_ord']}, M={row['M']}, N_start in {{{row['N_start_values']}}}: "
                f"`{row['N_start_invariance_match']}`; "
                f"best `s_min={row['exact_best_s_min']}`; "
                f"branch family `{row['exact_best_branch_family']}`"
            )
        lines.append("")

    write_csv(
        out_dir / "verification_table.csv",
        rows,
        [
            "N_start",
            "Delta_ord",
            "M",
            "mode_set",
            "exact_best_s_min",
            "predicted_best_s_min",
            "matches_best_value",
            "exact_best_branch_count",
            "exact_best_branch_family",
            "predicted_full_branch_count",
            "predicted_full_branch_family",
            "predicted_full_family_matches_exact_search",
            "predicted_minimal_subfamily_count",
            "predicted_minimal_subfamily",
            "minimal_subfamily_contained_in_exact_search",
            "full_family_strictly_larger_than_minimal_subfamily",
        ],
    )
    write_csv(
        out_dir / "n_start_invariance_check.csv",
        spacing_group_checks,
        [
            "Delta_ord",
            "M",
            "N_start_values",
            "exact_best_s_min",
            "exact_best_branch_family",
            "N_start_invariance_match",
        ],
    )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert best_value_match_count == len(test_cases), "Some cases did not recover the predicted best value 1/M."
    assert full_family_match_count == len(test_cases), "Some cases did not recover the full predicted optimal family."
    assert minimal_contained_count == len(test_cases), "Some minimal subfamily branches were missing from exact search."
    assert spacing_invariance_match_count == len(spacing_group_checks), "Some repeated (Delta_ord, M) groups broke N_start invariance."

    print("Completed arithmetic-progression closed-form verification.")
    print(f"Output directory: {out_dir}")


if __name__ == "__main__":
    main()
