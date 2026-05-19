from __future__ import annotations

import csv
from fractions import Fraction
from pathlib import Path

from analyze_q_counting_bounds import (
    composite_lower_bound_rho,
    difference_set,
    exact_best_rho,
    fiber_multiplicity,
    layer_low_shell_size_closed_form,
    layered_upper_bound_rho,
    profile_to_string,
    residue_profile_by_gcd,
    totient,
    allowed_branch_count,
)
from run_minimal_fullset_search import load_config


def bad_coverage_upper(profile: dict[int, int], q: int, r: int) -> int:
    total = 0
    for g, count in profile.items():
        total += count * fiber_multiplicity(q, g) * layer_low_shell_size_closed_form(q, g, r)
    return total


def critical_layers_next_step(profile: dict[int, int], q: int, r: int) -> list[int]:
    critical: list[int] = []
    target = r + 1
    for g, count in sorted(profile.items()):
        capacity = totient(q // g) - layer_low_shell_size_closed_form(q, g, target)
        if count > capacity:
            critical.append(g)
    return critical


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parent
    config = load_config(root / "minimal_example_config.json")
    out_dir = root / "results" / "bound_meeting"
    out_dir.mkdir(parents=True, exist_ok=True)

    diffs = difference_set(config.candidate_modes)
    a = Fraction(str(config.search.k_min))
    b = Fraction(str(config.search.k_max))
    q_bound = max(a.denominator, b.denominator, 2 * max(diffs))

    rows: list[dict[str, object]] = []
    for q in range(2, q_bound + 1):
        profile, has_zero = residue_profile_by_gcd(diffs, q)
        mu_q = allowed_branch_count(q, a, b)
        upper = layered_upper_bound_rho(diffs, q)
        lower = composite_lower_bound_rho(diffs, q, a, b)
        exact_rho, best_ms = exact_best_rho(diffs, q, a, b)

        coverage_at_upper = bad_coverage_upper(profile, q, upper)
        surplus_at_upper = mu_q - coverage_at_upper
        critical_layers = critical_layers_next_step(profile, q, upper)
        meeting = (
            mu_q > 0
            and exact_rho is not None
            and lower == upper == exact_rho
            and len(critical_layers) > 0
            and surplus_at_upper > 0
        )

        rows.append(
            {
                "q": q,
                "profile_by_gcd": profile_to_string(profile),
                "has_zero_residue": has_zero,
                "mu_q_window_branch_count": mu_q,
                "layered_upper_bound_rho": upper,
                "composite_lower_bound_rho": lower,
                "exact_best_rho": exact_rho if exact_rho is not None else "",
                "exact_best_s_min": exact_rho / q if exact_rho is not None else "",
                "coverage_upper_at_r": coverage_at_upper,
                "branch_surplus_at_r": surplus_at_upper,
                "critical_layers_at_r_plus_1": ",".join(str(g) for g in critical_layers),
                "one_step_meeting_exact": meeting,
                "best_m_list": ",".join(str(v) for v in best_ms),
            }
        )

    fieldnames = [
        "q",
        "profile_by_gcd",
        "has_zero_residue",
        "mu_q_window_branch_count",
        "layered_upper_bound_rho",
        "composite_lower_bound_rho",
        "exact_best_rho",
        "exact_best_s_min",
        "coverage_upper_at_r",
        "branch_surplus_at_r",
        "critical_layers_at_r_plus_1",
        "one_step_meeting_exact",
        "best_m_list",
    ]
    write_csv(out_dir / "bound_meeting_table.csv", rows, fieldnames)

    meeting_rows = [row for row in rows if row["one_step_meeting_exact"]]
    write_csv(out_dir / "one_step_exact_cases.csv", meeting_rows, fieldnames)

    positive_meeting_rows = [
        row for row in meeting_rows
        if row["exact_best_rho"] not in ("", 0)
    ]
    write_csv(out_dir / "positive_one_step_exact_cases.csv", positive_meeting_rows, fieldnames)

    row29 = next(row for row in rows if row["q"] == 29)
    row32 = next(row for row in rows if row["q"] == 32)
    row35 = next(row for row in rows if row["q"] == 35)

    lines: list[str] = []
    lines.append("# Bound Meeting Summary")
    lines.append("")
    lines.append(f"- Window: `[a,b]=[{a},{b}]`")
    lines.append(f"- Denominator search bound: `{q_bound}`")
    lines.append(f"- One-step exact cases: `{len(meeting_rows)}`")
    lines.append(f"- Positive one-step exact cases: `{len(positive_meeting_rows)}`")
    lines.append("")
    lines.append("## Key Examples")
    lines.append("")
    lines.append(
        f"- `q=29`: `upper={row29['layered_upper_bound_rho']}`, "
        f"`lower={row29['composite_lower_bound_rho']}`, "
        f"`surplus={row29['branch_surplus_at_r']}`, "
        f"`critical layers at r+1={row29['critical_layers_at_r_plus_1']}`, "
        f"exact `rho_q^*={row29['exact_best_rho']}`."
    )
    lines.append(
        f"- `q=32`: `upper={row32['layered_upper_bound_rho']}`, "
        f"`lower={row32['composite_lower_bound_rho']}`, "
        f"`surplus={row32['branch_surplus_at_r']}`, "
        f"`critical layers at r+1={row32['critical_layers_at_r_plus_1']}`, "
        f"exact `rho_q^*={row32['exact_best_rho']}`."
    )
    lines.append(
        f"- `q=35`: `upper={row35['layered_upper_bound_rho']}`, "
        f"`lower={row35['composite_lower_bound_rho']}`, "
        f"`surplus={row35['branch_surplus_at_r']}`, "
        f"`critical layers at r+1={row35['critical_layers_at_r_plus_1']}`, "
        f"exact `rho_q^*={row35['exact_best_rho']}`."
    )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- `branch_surplus_at_r > 0` means the lower-bound counting argument still leaves at least one branch uncovered by all low-shell bad sets.")
    lines.append("- `critical_layers_at_r_plus_1` lists the gcd layers that are already overcrowded at the next radius, forcing the upper bound down to `r`.")
    lines.append("- When both appear simultaneously, `rho_q^*` is fixed exactly by pure counting.")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Completed bound-meeting analysis.")
    print(f"Output directory: {out_dir}")
    print("q=29 row:", row29)


if __name__ == "__main__":
    main()
