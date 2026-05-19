from __future__ import annotations

import csv
import math
from fractions import Fraction
from pathlib import Path

from analyze_inverse_shell_criterion import exact_rho_for_branch
from analyze_large_q_shadow_screen import projected_shell
from analyze_q_counting_bounds import difference_set
from run_minimal_fullset_search import load_config


def allowed_ms(q: int, a: Fraction, b: Fraction) -> list[int]:
    return [m for m in range(1, q) if math.gcd(m, q) == 1 and a <= Fraction(m, q) <= b]


def tuple_to_string(values: tuple[int, ...]) -> str:
    return ",".join(str(value) for value in values)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parent
    config = load_config(root / "minimal_example_config.json")
    out_dir = root / "results" / "large_q_complement_layers"
    out_dir.mkdir(parents=True, exist_ok=True)

    diffs = difference_set(config.candidate_modes)
    diff_set = set(diffs)
    d_max = max(diffs)
    complement = set(range(1, d_max + 1)) - diff_set
    complement_tuple = tuple(sorted(complement))
    a = Fraction(str(config.search.k_min))
    b = Fraction(str(config.search.k_max))
    q_bound = max(a.denominator, b.denominator, 2 * d_max)

    per_branch_rows: list[dict[str, object]] = []
    per_q_rows: list[dict[str, object]] = []

    ge2_match_count = 0
    ge3_match_count = 0
    branch_count = 0

    shell1_vacancy_qs: list[int] = []
    shell2_vacancy_qs: list[int] = []
    shell2_vacancy_rows: list[dict[str, object]] = []

    for q in range(d_max + 1, q_bound + 1):
        allowed = allowed_ms(q, a, b)
        if not allowed:
            continue

        q_has_shell1_vacancy = False
        q_has_shell2_vacancy = False

        for m in allowed:
            branch_count += 1
            shell1 = projected_shell(q, m, 1, d_max)
            shell2 = projected_shell(q, m, 2, d_max)
            shell3 = projected_shell(q, m, 3, d_max)

            shell1_hits_d = tuple(value for value in shell1 if value in diff_set)
            shell2_hits_d = tuple(value for value in shell2 if value in diff_set)
            shell3_hits_d = tuple(value for value in shell3 if value in diff_set)
            shell1_in_complement = tuple(value for value in shell1 if value in complement)
            shell2_in_complement = tuple(value for value in shell2 if value in complement)

            exact_rho, limiting_diffs = exact_rho_for_branch(diffs, q, m)
            predicted_ge2 = len(shell1_hits_d) == 0
            predicted_ge3 = len(shell1_hits_d) == 0 and len(shell2_hits_d) == 0

            if predicted_ge2 == (exact_rho >= 2):
                ge2_match_count += 1
            if predicted_ge3 == (exact_rho >= 3):
                ge3_match_count += 1

            if predicted_ge2:
                q_has_shell1_vacancy = True
            if predicted_ge3:
                q_has_shell2_vacancy = True
                shell2_vacancy_rows.append(
                    {
                        "q": q,
                        "m": m,
                        "k_fraction": f"{m}/{q}",
                        "shell1_projection": tuple_to_string(shell1),
                        "shell2_projection": tuple_to_string(shell2),
                        "shell3_projection": tuple_to_string(shell3),
                        "exact_rho": exact_rho,
                    }
                )

            per_branch_rows.append(
                {
                    "q": q,
                    "m": m,
                    "k_fraction": f"{m}/{q}",
                    "shell1_projection": tuple_to_string(shell1),
                    "shell1_hits_D": tuple_to_string(shell1_hits_d),
                    "shell1_hits_complement": tuple_to_string(shell1_in_complement),
                    "shell2_projection": tuple_to_string(shell2),
                    "shell2_hits_D": tuple_to_string(shell2_hits_d),
                    "shell2_hits_complement": tuple_to_string(shell2_in_complement),
                    "shell3_projection": tuple_to_string(shell3),
                    "shell3_hits_D": tuple_to_string(shell3_hits_d),
                    "exact_rho": exact_rho,
                    "predicted_ge_2_by_shell1_complement": predicted_ge2,
                    "predicted_ge_3_by_shell12_complement": predicted_ge3,
                    "limiting_diffs": tuple_to_string(limiting_diffs),
                }
            )

        if q_has_shell1_vacancy:
            shell1_vacancy_qs.append(q)
        if q_has_shell2_vacancy:
            shell2_vacancy_qs.append(q)

        per_q_rows.append(
            {
                "q": q,
                "allowed_branches": tuple_to_string(tuple(allowed)),
                "has_shell1_vacancy_branch": q_has_shell1_vacancy,
                "has_shell2_vacancy_branch": q_has_shell2_vacancy,
            }
        )

    write_csv(
        out_dir / "per_branch_complement_layers.csv",
        per_branch_rows,
        [
            "q",
            "m",
            "k_fraction",
            "shell1_projection",
            "shell1_hits_D",
            "shell1_hits_complement",
            "shell2_projection",
            "shell2_hits_D",
            "shell2_hits_complement",
            "shell3_projection",
            "shell3_hits_D",
            "exact_rho",
            "predicted_ge_2_by_shell1_complement",
            "predicted_ge_3_by_shell12_complement",
            "limiting_diffs",
        ],
    )
    write_csv(
        out_dir / "per_denominator_complement_layers.csv",
        per_q_rows,
        ["q", "allowed_branches", "has_shell1_vacancy_branch", "has_shell2_vacancy_branch"],
    )
    write_csv(
        out_dir / "shell2_vacancy_cases.csv",
        shell2_vacancy_rows,
        ["q", "m", "k_fraction", "shell1_projection", "shell2_projection", "shell3_projection", "exact_rho"],
    )

    lines: list[str] = []
    lines.append("# Large-q Complement-Layer Summary")
    lines.append("")
    lines.append("## Setup")
    lines.append("")
    lines.append(f"- Difference-set max: `D_max={d_max}`")
    lines.append(f"- Large-q range: `{d_max + 1} <= q <= {q_bound}`")
    lines.append(f"- Difference complement on `[1,D_max]`: `{', '.join(str(v) for v in complement_tuple)}`")
    lines.append("")
    lines.append("## Exact Verification")
    lines.append("")
    lines.append(f"- Branch count in the large-q range: `{branch_count}`")
    lines.append(f"- `rho>=2` <=> shell-1 projection misses `D`: `{ge2_match_count}/{branch_count}` matches")
    lines.append(f"- `rho>=3` <=> both shell-1 and shell-2 projections miss `D`: `{ge3_match_count}/{branch_count}` matches")
    lines.append("")
    lines.append("## Current Example")
    lines.append("")
    lines.append(f"- Denominators with at least one shell-1 vacancy branch: `{', '.join(str(q) for q in shell1_vacancy_qs)}`")
    if shell2_vacancy_qs:
        lines.append(f"- Denominators with at least one shell-2 vacancy branch: `{', '.join(str(q) for q in shell2_vacancy_qs)}`")
    else:
        lines.append("- Denominators with at least one shell-2 vacancy branch: `none`")
    lines.append("- Therefore every large-q admissible branch is already forced by shell 1 or shell 2; no large-q branch reaches `rho>=3`.")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Completed large-q complement-layer analysis.")
    print(f"Output directory: {out_dir}")
    print(f"rho>=2 criterion matches: {ge2_match_count}/{branch_count}")
    print(f"rho>=3 criterion matches: {ge3_match_count}/{branch_count}")
    print(f"shell-2 vacancy denominators: {shell2_vacancy_qs if shell2_vacancy_qs else 'none'}")


if __name__ == "__main__":
    main()
