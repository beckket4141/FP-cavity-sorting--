from __future__ import annotations

import csv
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path

from run_minimal_fullset_search import load_config


def difference_set(modes: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted({b - a for idx, a in enumerate(modes) for b in modes[idx + 1 :]}))


def modular_distance(residue: int, q: int) -> int:
    residue %= q
    return min(residue, q - residue)


def totient(n: int) -> int:
    result = n
    x = n
    p = 2
    while p * p <= x:
        if x % p == 0:
            while x % p == 0:
                x //= p
            result -= result // p
        p += 1
    if x > 1:
        result -= result // x
    return result


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    p = 3
    while p * p <= n:
        if n % p == 0:
            return False
        p += 2
    return True


def residue_profile_by_gcd(diffs: tuple[int, ...], q: int) -> tuple[Counter[int], bool]:
    residues = {d % q for d in diffs}
    has_zero = 0 in residues
    residues.discard(0)
    profile: Counter[int] = Counter()
    for residue in residues:
        profile[math.gcd(residue, q)] += 1
    return profile, has_zero


def nonzero_residue_count(diffs: tuple[int, ...], q: int) -> tuple[int, bool]:
    profile, has_zero = residue_profile_by_gcd(diffs, q)
    return sum(profile.values()), has_zero


def allowed_branch_count(q: int, a: Fraction, b: Fraction) -> int:
    count = 0
    for m in range(1, q):
        if math.gcd(m, q) != 1:
            continue
        k = Fraction(m, q)
        if a <= k <= b:
            count += 1
    return count


def exact_best_rho(diffs: tuple[int, ...], q: int, a: Fraction, b: Fraction) -> tuple[int | None, list[int]]:
    best: int | None = None
    best_ms: list[int] = []
    for m in range(1, q):
        if math.gcd(m, q) != 1:
            continue
        k = Fraction(m, q)
        if not (a <= k <= b):
            continue
        rho = q
        for d in diffs:
            rho = min(rho, modular_distance(d * m, q))
        if best is None or rho > best:
            best = rho
            best_ms = [m]
        elif rho == best:
            best_ms.append(m)
    return best, best_ms


def layer_low_shell_size(q: int, g: int, r: int) -> int:
    count = 0
    for residue in range(1, q):
        if math.gcd(residue, q) != g:
            continue
        if modular_distance(residue, q) < r:
            count += 1
    return count


def coprime_prefix_count(n: int, t: int) -> int:
    if t <= 0:
        return 0
    return sum(1 for value in range(1, t + 1) if math.gcd(value, n) == 1)


def layer_low_shell_size_closed_form(q: int, g: int, r: int) -> int:
    n = q // g
    t = (r - 1) // g
    return 2 * coprime_prefix_count(n, t)


def fiber_multiplicity(q: int, g: int) -> int:
    return totient(q) // totient(q // g)


def coarse_upper_bound_rho(diffs: tuple[int, ...], q: int) -> int:
    nu_q, has_zero = nonzero_residue_count(diffs, q)
    if has_zero:
        return 0
    return (q - nu_q + 1) // 2


def layered_upper_bound_rho(diffs: tuple[int, ...], q: int) -> int:
    profile, has_zero = residue_profile_by_gcd(diffs, q)
    if has_zero:
        return 0
    best = 0
    for r in range(1, (q // 2) + 1):
        ok = True
        for g, count in profile.items():
            layer_size = totient(q // g)
            low_shell = layer_low_shell_size_closed_form(q, g, r)
            if count > layer_size - low_shell:
                ok = False
                break
        if ok:
            best = r
        else:
            break
    return best


def prime_lower_bound_rho(diffs: tuple[int, ...], q: int, a: Fraction, b: Fraction) -> int | None:
    nu_q, has_zero = nonzero_residue_count(diffs, q)
    mu_q = allowed_branch_count(q, a, b)
    if has_zero or not is_prime(q) or mu_q <= 0 or nu_q <= 0:
        return None
    return 1 + ((mu_q - 1) // (2 * nu_q))


def composite_lower_bound_rho(diffs: tuple[int, ...], q: int, a: Fraction, b: Fraction) -> int:
    profile, has_zero = residue_profile_by_gcd(diffs, q)
    mu_q = allowed_branch_count(q, a, b)
    if has_zero or mu_q <= 0:
        return 0

    best = 0
    for r in range(1, (q // 2) + 1):
        covered_upper = 0
        for g, count in profile.items():
            bad_per_residue = fiber_multiplicity(q, g) * layer_low_shell_size_closed_form(q, g, r)
            covered_upper += count * min(mu_q, bad_per_residue)
        if mu_q > covered_upper:
            best = r
        else:
            break
    return best


def profile_to_string(profile: Counter[int]) -> str:
    if not profile:
        return ""
    return ";".join(f"{g}:{profile[g]}" for g in sorted(profile))


def display_value(value: object) -> str:
    if value == "":
        return "N/A"
    return str(value)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parent
    config = load_config(root / "minimal_example_config.json")
    out_dir = root / "results" / "q_counting_bounds"
    out_dir.mkdir(parents=True, exist_ok=True)

    diffs = difference_set(config.candidate_modes)
    a = Fraction(str(config.search.k_min))
    b = Fraction(str(config.search.k_max))
    q_bound = max(a.denominator, b.denominator, 2 * max(diffs))

    rows: list[dict[str, object]] = []
    for q in range(2, q_bound + 1):
        profile, has_zero = residue_profile_by_gcd(diffs, q)
        nu_q = sum(profile.values())
        mu_q = allowed_branch_count(q, a, b)
        coarse_upper = 0 if has_zero else (q - nu_q + 1) // 2
        layered_upper = layered_upper_bound_rho(diffs, q)
        prime_lower = prime_lower_bound_rho(diffs, q, a, b)
        composite_lower = composite_lower_bound_rho(diffs, q, a, b)
        exact_rho, best_ms = exact_best_rho(diffs, q, a, b)

        rows.append(
            {
                "q": q,
                "profile_by_gcd": profile_to_string(profile),
                "nu_q_nonzero": nu_q,
                "has_zero_residue": has_zero,
                "mu_q_window_branch_count": mu_q,
                "coarse_upper_bound_rho": coarse_upper,
                "layered_upper_bound_rho": layered_upper,
                "prime_lower_bound_rho": prime_lower if prime_lower is not None else "",
                "composite_lower_bound_rho": composite_lower,
                "exact_best_rho": exact_rho if exact_rho is not None else "",
                "exact_best_s_min": exact_rho / q if exact_rho is not None else "",
                "best_m_list": ",".join(str(v) for v in best_ms),
                "coarse_upper_tight": (exact_rho is not None and exact_rho == coarse_upper),
                "layered_upper_tight": (exact_rho is not None and exact_rho == layered_upper),
                "prime_lower_tight": (prime_lower is not None and exact_rho is not None and exact_rho == prime_lower),
                "composite_lower_tight": (exact_rho is not None and exact_rho == composite_lower),
            }
        )

    fieldnames = [
        "q",
        "profile_by_gcd",
        "nu_q_nonzero",
        "has_zero_residue",
        "mu_q_window_branch_count",
        "coarse_upper_bound_rho",
        "layered_upper_bound_rho",
        "prime_lower_bound_rho",
        "composite_lower_bound_rho",
        "exact_best_rho",
        "exact_best_s_min",
        "best_m_list",
        "coarse_upper_tight",
        "layered_upper_tight",
        "prime_lower_tight",
        "composite_lower_tight",
    ]
    write_csv(out_dir / "q_bounds_table.csv", rows, fieldnames)

    tight_rows = [
        row for row in rows
        if row["coarse_upper_tight"]
        or row["layered_upper_tight"]
        or row["prime_lower_tight"]
        or row["composite_lower_tight"]
    ]
    write_csv(out_dir / "tight_bound_cases.csv", tight_rows, fieldnames)

    row29 = next(row for row in rows if row["q"] == 29)
    composite_examples = [
        row for row in rows
        if row["q"] in {32, 35, 36, 40, 42}
    ]

    lines: list[str] = []
    lines.append("# q Counting Bounds Summary")
    lines.append("")
    lines.append(f"- Window: `[a,b]=[{a},{b}]`")
    lines.append(f"- Denominator search bound: `{q_bound}`")
    lines.append(f"- Difference set max: `{max(diffs)}`")
    lines.append("")
    lines.append("## Current Example Highlight")
    lines.append("")
    lines.append(
        f"- `q=29`: `profile={row29['profile_by_gcd']}`, `mu_q={row29['mu_q_window_branch_count']}`, "
        f"`layered upper={row29['layered_upper_bound_rho']}`, "
        f"`composite lower={row29['composite_lower_bound_rho']}`, "
        f"exact `rho_q^*={display_value(row29['exact_best_rho'])}`."
    )
    lines.append(f"- Best branches at `q=29`: `{row29['best_m_list']}`.")
    lines.append("")
    lines.append("## Composite-Denominator Snapshots")
    lines.append("")
    for row in composite_examples:
        lines.append(
            f"- `q={row['q']}`: `profile={row['profile_by_gcd']}`, "
            f"`layered upper={row['layered_upper_bound_rho']}`, "
            f"`composite lower={row['composite_lower_bound_rho']}`, "
            f"exact `rho_q^*={display_value(row['exact_best_rho'])}`."
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- `profile_by_gcd` records how the nonzero difference residues are distributed across gcd layers.")
    lines.append("- `layered_upper_bound_rho` is a stronger necessary-condition upper bound than the old coarse count bound.")
    lines.append("- `composite_lower_bound_rho` extends the prime-denominator lower bound to general composite denominators.")
    lines.append("- When layered upper and composite lower meet, `rho_q^*` is determined exactly by counting alone.")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Completed refined q-counting-bounds analysis.")
    print(f"Output directory: {out_dir}")
    print("q=29 row:", row29)


if __name__ == "__main__":
    main()
