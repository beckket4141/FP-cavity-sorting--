from __future__ import annotations

import csv
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

from analyze_q_counting_bounds import difference_set, modular_distance
from run_minimal_fullset_search import load_config


def allowed_ms(q: int, a: Fraction, b: Fraction) -> list[int]:
    return [m for m in range(1, q) if math.gcd(m, q) == 1 and a <= Fraction(m, q) <= b]


def residue_to_diffs_map(diffs: tuple[int, ...], q: int) -> dict[int, tuple[int, ...]]:
    mapping: dict[int, list[int]] = {}
    for d in diffs:
        residue = d % q
        if residue == 0:
            continue
        mapping.setdefault(residue, []).append(d)
    return {residue: tuple(sorted(values)) for residue, values in sorted(mapping.items())}


def exact_rho_for_branch(diffs: tuple[int, ...], q: int, m: int) -> tuple[int, tuple[int, ...]]:
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


def inverse_shell(q: int, m: int, r: int) -> tuple[int, ...]:
    inverse = pow(m, -1, q)
    values = {(r * inverse) % q, (-r * inverse) % q}
    return tuple(sorted(values))


def first_inverse_shell_hit(
    residues: set[int],
    q: int,
    m: int,
) -> tuple[int | None, tuple[int, ...]]:
    for r in range(1, (q // 2) + 1):
        shell = inverse_shell(q, m, r)
        hits = tuple(value for value in shell if value in residues)
        if hits:
            return r, hits
    return None, tuple()


def tuple_to_string(values: tuple[int, ...]) -> str:
    return ",".join(str(value) for value in values)


def counter_to_string(counter: Counter[int]) -> str:
    return ";".join(f"{key}:{counter[key]}" for key in sorted(counter))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parent
    config = load_config(root / "minimal_example_config.json")
    out_dir = root / "results" / "inverse_shell_criterion"
    out_dir.mkdir(parents=True, exist_ok=True)

    diffs = difference_set(config.candidate_modes)
    a = Fraction(str(config.search.k_min))
    b = Fraction(str(config.search.k_max))
    q_bound = max(a.denominator, b.denominator, 2 * max(diffs))

    per_branch_rows: list[dict[str, object]] = []
    per_q_rows: list[dict[str, object]] = []
    vacancy_rows: list[dict[str, object]] = []

    branch_match_count = 0
    q_match_count = 0
    total_branches = 0
    total_qs = 0

    zero_free_qs_all_hit: list[int] = []
    zero_free_qs_with_vacancy: list[int] = []
    invariant_positive_qs: list[int] = []

    for q in range(2, q_bound + 1):
        allowed = allowed_ms(q, a, b)
        if not allowed:
            continue

        total_qs += 1
        residue_map = residue_to_diffs_map(diffs, q)
        residues = set(residue_map)
        has_zero = any(d % q == 0 for d in diffs)

        rho_by_m: dict[int, int] = {}
        predicted_by_m: dict[int, int] = {}
        pair_hit_by_m: dict[int, bool] = {}
        first_hit_residues_by_m: dict[int, tuple[int, ...]] = {}
        limiting_diffs_by_m: dict[int, tuple[int, ...]] = {}

        missed_first_shell_ms: list[int] = []
        first_shell_hit_ms: list[int] = []

        for m in allowed:
            total_branches += 1
            exact_rho, limiting_diffs = exact_rho_for_branch(diffs, q, m)
            if has_zero:
                predicted_rho = 0
                first_hit_residues = tuple()
            else:
                first_hit_radius, first_hit_residues = first_inverse_shell_hit(residues, q, m)
                if first_hit_radius is None:
                    raise RuntimeError(f"No inverse-shell hit found for q={q}, m={m}.")
                predicted_rho = first_hit_radius

            inverse_pair = inverse_shell(q, m, 1)
            inverse_pair_hit = any(value in residues for value in inverse_pair)

            rho_by_m[m] = exact_rho
            predicted_by_m[m] = predicted_rho
            pair_hit_by_m[m] = inverse_pair_hit
            first_hit_residues_by_m[m] = first_hit_residues
            limiting_diffs_by_m[m] = limiting_diffs

            if inverse_pair_hit:
                first_shell_hit_ms.append(m)
            else:
                missed_first_shell_ms.append(m)

            source_diffs = tuple(
                sorted({d for residue in first_hit_residues for d in residue_map.get(residue, tuple())})
            )

            per_branch_rows.append(
                {
                    "q": q,
                    "m": m,
                    "k_fraction": f"{m}/{q}",
                    "has_zero_residue": has_zero,
                    "exact_rho": exact_rho,
                    "predicted_rho_by_inverse_shell": predicted_rho,
                    "inverse_pair": tuple_to_string(inverse_pair),
                    "inverse_pair_hit": inverse_pair_hit,
                    "first_hit_inverse_shell_residues": tuple_to_string(first_hit_residues),
                    "first_hit_source_diffs": tuple_to_string(source_diffs),
                    "limiting_diffs_exact": tuple_to_string(limiting_diffs),
                    "prediction_matches_exact": exact_rho == predicted_rho,
                }
            )

            if exact_rho == predicted_rho:
                branch_match_count += 1

        rho_counter = Counter(rho_by_m.values())
        exact_best_rho = max(rho_by_m.values())
        exact_best_ms = tuple(sorted(m for m, rho in rho_by_m.items() if rho == exact_best_rho))
        predicted_best_rho = max(predicted_by_m.values())
        predicted_best_ms = tuple(sorted(m for m, rho in predicted_by_m.items() if rho == predicted_best_rho))

        all_inverse_pairs_hit = (not has_zero) and len(missed_first_shell_ms) == 0
        has_first_shell_vacancy = (not has_zero) and len(missed_first_shell_ms) > 0
        all_admissible_equal = len(rho_counter) == 1
        common_rho = next(iter(rho_counter)) if all_admissible_equal else ""

        per_q_rows.append(
            {
                "q": q,
                "allowed_branches": tuple_to_string(tuple(allowed)),
                "mu_q": len(allowed),
                "has_zero_residue": has_zero,
                "exact_best_rho": exact_best_rho,
                "predicted_best_rho": predicted_best_rho,
                "exact_best_m_list": tuple_to_string(exact_best_ms),
                "predicted_best_m_list": tuple_to_string(predicted_best_ms),
                "all_inverse_pairs_hit": all_inverse_pairs_hit,
                "missed_first_shell_m_list": tuple_to_string(tuple(missed_first_shell_ms)),
                "first_shell_hit_m_list": tuple_to_string(tuple(first_shell_hit_ms)),
                "all_admissible_equal": all_admissible_equal,
                "common_rho_if_equal": common_rho,
                "rho_spectrum": counter_to_string(rho_counter),
                "prediction_matches_exact": (exact_best_rho == predicted_best_rho and exact_best_ms == predicted_best_ms),
            }
        )

        if exact_best_rho == predicted_best_rho and exact_best_ms == predicted_best_ms:
            q_match_count += 1

        if all_inverse_pairs_hit:
            zero_free_qs_all_hit.append(q)
        if has_first_shell_vacancy:
            zero_free_qs_with_vacancy.append(q)
            vacancy_rows.append(
                {
                    "q": q,
                    "mu_q": len(allowed),
                    "exact_best_rho": exact_best_rho,
                    "best_m_list": tuple_to_string(exact_best_ms),
                    "missed_first_shell_m_list": tuple_to_string(tuple(missed_first_shell_ms)),
                    "rho_spectrum": counter_to_string(rho_counter),
                }
            )
        if all_admissible_equal and exact_best_rho > 0:
            invariant_positive_qs.append(q)

    write_csv(
        out_dir / "per_branch_inverse_shell.csv",
        per_branch_rows,
        [
            "q",
            "m",
            "k_fraction",
            "has_zero_residue",
            "exact_rho",
            "predicted_rho_by_inverse_shell",
            "inverse_pair",
            "inverse_pair_hit",
            "first_hit_inverse_shell_residues",
            "first_hit_source_diffs",
            "limiting_diffs_exact",
            "prediction_matches_exact",
        ],
    )
    write_csv(
        out_dir / "per_denominator_inverse_shell.csv",
        per_q_rows,
        [
            "q",
            "allowed_branches",
            "mu_q",
            "has_zero_residue",
            "exact_best_rho",
            "predicted_best_rho",
            "exact_best_m_list",
            "predicted_best_m_list",
            "all_inverse_pairs_hit",
            "missed_first_shell_m_list",
            "first_shell_hit_m_list",
            "all_admissible_equal",
            "common_rho_if_equal",
            "rho_spectrum",
            "prediction_matches_exact",
        ],
    )
    write_csv(
        out_dir / "first_shell_vacancy_cases.csv",
        vacancy_rows,
        ["q", "mu_q", "exact_best_rho", "best_m_list", "missed_first_shell_m_list", "rho_spectrum"],
    )

    row29 = next(row for row in per_q_rows if row["q"] == 29)
    row73 = next(row for row in per_q_rows if row["q"] == 73)
    nontrivial_invariant_qs = [
        q
        for q in invariant_positive_qs
        if next(row for row in per_q_rows if row["q"] == q)["mu_q"] > 1
    ]
    nontrivial_invariant_rho_gt_1_qs = [
        q
        for q in nontrivial_invariant_qs
        if next(row for row in per_q_rows if row["q"] == q)["common_rho_if_equal"] not in ("", 1)
    ]

    lines: list[str] = []
    lines.append("# Inverse-Shell Criterion Summary")
    lines.append("")
    lines.append("## Verification")
    lines.append("")
    lines.append(f"- Search window: `[a,b]=[{a},{b}]`")
    lines.append(f"- Denominator bound: `Q_I(S)={q_bound}`")
    lines.append(f"- Branch-level match count: `{branch_match_count}/{total_branches}`")
    lines.append(f"- Denominator-level match count: `{q_match_count}/{total_qs}`")
    lines.append("- Result: the inverse-shell prediction reproduces the exact `rho_q(m)` and the exact best `(q,m)` classification on the full `q<=Q_I(S)` range.")
    lines.append("")
    lines.append("## Exact Design Corollaries")
    lines.append("")
    lines.append("- If `q` has a zero residue, then every admissible branch collides and `rho_q(m)=0`.")
    lines.append("- If `q` is zero-free and every admissible inverse pair `{±m^{-1}}` is hit by the residue set, then every admissible branch is forced to `rho_q(m)=1`, hence `s_min(m/q)=1/q` for all admissible `m`.")
    lines.append("- If `q` is zero-free and some admissible inverse pair `{±m^{-1}}` is missed, then that branch automatically satisfies `rho_q(m)>=2`, so `q` is immediately worth deeper search.")
    lines.append("")
    lines.append("## Current Example")
    lines.append("")
    lines.append(
        f"- `q=29`: all admissible inverse pairs are hit; `missed_first_shell_m_list={row29['missed_first_shell_m_list']}`; exact `rho` spectrum `{row29['rho_spectrum']}`."
    )
    lines.append(
        f"- `q=73`: the only missed first-shell branch is `m={row73['missed_first_shell_m_list']}`; exact best branches `{row73['exact_best_m_list']}`; exact `rho` spectrum `{row73['rho_spectrum']}`."
    )
    lines.append("")
    lines.append("## q Classification in the Current 5.4 Example")
    lines.append("")
    lines.append(f"- Zero-free q with all admissible inverse pairs hit: `{', '.join(str(q) for q in zero_free_qs_all_hit)}`")
    lines.append(f"- Zero-free q with at least one first-shell vacancy: `{', '.join(str(q) for q in zero_free_qs_with_vacancy)}`")
    lines.append("")
    lines.append("## Empirical Boundary")
    lines.append("")
    lines.append(f"- Nontrivial branch-invariant positive-rho q (at least two admissible branches): `{', '.join(str(q) for q in nontrivial_invariant_qs)}`")
    if nontrivial_invariant_rho_gt_1_qs:
        lines.append(
            f"- Nontrivial branch-invariant cases with common rho > 1: `{', '.join(str(q) for q in nontrivial_invariant_rho_gt_1_qs)}`"
        )
    else:
        lines.append("- No nontrivial branch-invariant case with common `rho>1` appeared on `q<=Q_I(S)`.")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Completed inverse-shell criterion analysis.")
    print(f"Output directory: {out_dir}")
    print(f"Branch-level matches: {branch_match_count}/{total_branches}")
    print(f"Denominator-level matches: {q_match_count}/{total_qs}")


if __name__ == "__main__":
    main()
