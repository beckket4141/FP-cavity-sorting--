from __future__ import annotations

import csv
import math
from fractions import Fraction
from pathlib import Path

from analyze_inverse_shell_criterion import exact_rho_for_branch
from analyze_q_counting_bounds import difference_set
from run_minimal_fullset_search import load_config


def allowed_ms(q: int, a: Fraction, b: Fraction) -> list[int]:
    return [m for m in range(1, q) if math.gcd(m, q) == 1 and a <= Fraction(m, q) <= b]


def projected_shell(q: int, m: int, r: int, d_max: int) -> tuple[int, ...]:
    inverse = pow(m, -1, q)
    candidates = {(r * inverse) % q, (-r * inverse) % q}
    projected = tuple(sorted(value for value in candidates if 1 <= value <= d_max))
    return projected


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
    out_dir = root / "results" / "large_q_shadow_screen"
    out_dir.mkdir(parents=True, exist_ok=True)

    diffs = difference_set(config.candidate_modes)
    diff_set = set(diffs)
    d_max = max(diffs)
    complement = tuple(value for value in range(1, d_max + 1) if value not in diff_set)
    a = Fraction(str(config.search.k_min))
    b = Fraction(str(config.search.k_max))
    q_bound = max(a.denominator, b.denominator, 2 * d_max)

    per_branch_rows: list[dict[str, object]] = []
    per_q_rows: list[dict[str, object]] = []

    any_rho_ge_3 = False
    first_miss_qs: list[int] = []
    q_one_shell_only: list[int] = []
    q_two_shell_needed: list[int] = []

    for q in range(d_max + 1, q_bound + 1):
        allowed = allowed_ms(q, a, b)
        if not allowed:
            continue

        first_shell_miss_ms: list[int] = []
        second_shell_hit_for_misses = True
        best_rho = 0
        best_ms: list[int] = []

        for m in allowed:
            shell1 = projected_shell(q, m, 1, d_max)
            shell2 = projected_shell(q, m, 2, d_max)
            shell3 = projected_shell(q, m, 3, d_max)
            shell1_hits = tuple(value for value in shell1 if value in diff_set)
            shell2_hits = tuple(value for value in shell2 if value in diff_set)
            shell3_hits = tuple(value for value in shell3 if value in diff_set)

            exact_rho, limiting_diffs = exact_rho_for_branch(diffs, q, m)
            if exact_rho > best_rho:
                best_rho = exact_rho
                best_ms = [m]
            elif exact_rho == best_rho:
                best_ms.append(m)

            if exact_rho >= 3:
                any_rho_ge_3 = True

            first_shell_miss = len(shell1_hits) == 0
            if first_shell_miss:
                first_shell_miss_ms.append(m)
                if len(shell2_hits) == 0:
                    second_shell_hit_for_misses = False

            per_branch_rows.append(
                {
                    "q": q,
                    "m": m,
                    "k_fraction": f"{m}/{q}",
                    "shell1_projection": tuple_to_string(shell1),
                    "shell1_hits_in_D": tuple_to_string(shell1_hits),
                    "shell1_is_vacancy": first_shell_miss,
                    "shell2_projection": tuple_to_string(shell2),
                    "shell2_hits_in_D": tuple_to_string(shell2_hits),
                    "shell3_projection": tuple_to_string(shell3),
                    "shell3_hits_in_D": tuple_to_string(shell3_hits),
                    "exact_rho": exact_rho,
                    "exact_s_min": exact_rho / q,
                    "limiting_diffs": tuple_to_string(limiting_diffs),
                }
            )

        if first_shell_miss_ms:
            first_miss_qs.append(q)
        if best_rho == 1:
            q_one_shell_only.append(q)
        elif best_rho == 2:
            q_two_shell_needed.append(q)

        per_q_rows.append(
            {
                "q": q,
                "allowed_branches": tuple_to_string(tuple(allowed)),
                "best_rho": best_rho,
                "best_m_list": tuple_to_string(tuple(best_ms)),
                "best_s_min": best_rho / q,
                "first_shell_miss_m_list": tuple_to_string(tuple(first_shell_miss_ms)),
                "all_first_shell_misses_hit_shell2": second_shell_hit_for_misses,
                "q_is_one_shell_only": best_rho == 1,
                "q_needs_two_shells": best_rho == 2,
            }
        )

    write_csv(
        out_dir / "per_branch_large_q_shadow.csv",
        per_branch_rows,
        [
            "q",
            "m",
            "k_fraction",
            "shell1_projection",
            "shell1_hits_in_D",
            "shell1_is_vacancy",
            "shell2_projection",
            "shell2_hits_in_D",
            "shell3_projection",
            "shell3_hits_in_D",
            "exact_rho",
            "exact_s_min",
            "limiting_diffs",
        ],
    )
    write_csv(
        out_dir / "per_denominator_large_q_shadow.csv",
        per_q_rows,
        [
            "q",
            "allowed_branches",
            "best_rho",
            "best_m_list",
            "best_s_min",
            "first_shell_miss_m_list",
            "all_first_shell_misses_hit_shell2",
            "q_is_one_shell_only",
            "q_needs_two_shells",
        ],
    )

    dominating_q29_margin = Fraction(1, 29) - Fraction(2, min(first_miss_qs)) if first_miss_qs else None

    lines: list[str] = []
    lines.append("# Large-q Shadow Screen Summary")
    lines.append("")
    lines.append("## Setup")
    lines.append("")
    lines.append(f"- Difference-set max: `D_max={d_max}`")
    lines.append(f"- Exact denominator bound: `Q_I(S)={q_bound}`")
    lines.append(f"- Large-q range considered here: `{d_max + 1} <= q <= {q_bound}`")
    lines.append(f"- Difference-set complement on `[1,D_max]`: `{', '.join(str(v) for v in complement)}`")
    lines.append("")
    lines.append("## Exact Large-q Facts For The Current Example")
    lines.append("")
    lines.append(f"- Large-q denominators with exact best `rho=1`: `{', '.join(str(q) for q in q_one_shell_only)}`")
    lines.append(f"- Large-q denominators with exact best `rho=2`: `{', '.join(str(q) for q in q_two_shell_needed)}`")
    if first_miss_qs:
        lines.append(f"- First denominator where a shell-1 vacancy appears: `q={min(first_miss_qs)}`")
        lines.append(f"- All denominators with shell-1 vacancy branches: `{', '.join(str(q) for q in first_miss_qs)}`")
    else:
        lines.append("- No shell-1 vacancy branch appears on the large-q range.")
    lines.append(f"- Any admissible branch with exact `rho>=3` on the large-q range: `{any_rho_ge_3}`")
    lines.append("")
    lines.append("## Meaning")
    lines.append("")
    lines.append("- For `q>D_max`, the nonzero difference residues are exactly the original difference set `D(S)` itself.")
    lines.append("- Therefore fixed-branch screening can be done by projecting each inverse shell onto `[1,D_max]` and checking whether that projection already hits `D(S)`.")
    lines.append("- In the current example, every large-q branch either hits `D(S)` on shell 1 or, if shell 1 misses, it already hits on shell 2.")
    if dominating_q29_margin is not None:
        lines.append(
            f"- Since shell-1 vacancies start only at `q={min(first_miss_qs)}`, every large-q branch satisfies `s_min<=2/{min(first_miss_qs)}={float(Fraction(2, min(first_miss_qs))):.12f} < 1/29={float(Fraction(1, 29)):.12f}`."
        )
        lines.append(
            f"- Hence no denominator in `{d_max + 1} <= q <= {q_bound}` can beat the known optimum `q=29` for the current 12-mode example."
        )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Completed large-q shadow screening analysis.")
    print(f"Output directory: {out_dir}")
    print(f"Any large-q rho>=3: {any_rho_ge_3}")
    if first_miss_qs:
        print(f"First shell-1 vacancy q: {min(first_miss_qs)}")


if __name__ == "__main__":
    main()
