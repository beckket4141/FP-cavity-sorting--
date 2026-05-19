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


def residue_set_nonzero(diffs: tuple[int, ...], q: int) -> tuple[int, ...]:
    residues = sorted({d % q for d in diffs if d % q != 0})
    return tuple(residues)


def transformed_residue_set(residues: tuple[int, ...], m: int, q: int) -> tuple[int, ...]:
    return tuple(sorted({(m * residue) % q for residue in residues}))


def shell_signature(transformed: tuple[int, ...], q: int) -> tuple[int, ...]:
    counts = [0] * (q // 2)
    for residue in transformed:
        dist = modular_distance(residue, q)
        if dist == 0:
            continue
        counts[dist - 1] += 1
    return tuple(counts)


def first_hit_residues(transformed: tuple[int, ...], q: int) -> tuple[int, tuple[int, ...]]:
    best = min(modular_distance(residue, q) for residue in transformed)
    residues = tuple(sorted(residue for residue in transformed if modular_distance(residue, q) == best))
    return best, residues


def first_hit_diffs(diffs: tuple[int, ...], m: int, q: int, best_rho: int) -> tuple[int, ...]:
    hits = sorted({d for d in diffs if modular_distance(d * m, q) == best_rho})
    return tuple(hits)


def stabilizer(residues: tuple[int, ...], q: int) -> tuple[int, ...]:
    base = set(residues)
    return tuple(sorted(m for m in units(q) if {(m * residue) % q for residue in residues} == base))


def signature_to_string(signature: tuple[int, ...]) -> str:
    nonzero_parts = [f"{idx + 1}:{count}" for idx, count in enumerate(signature) if count]
    return ";".join(nonzero_parts) if nonzero_parts else "empty"


def tuple_to_string(values: tuple[int, ...]) -> str:
    return ",".join(str(v) for v in values)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    root = Path(__file__).resolve().parent
    config = load_config(root / "minimal_example_config.json")
    out_dir = root / "results" / "m_shell_classes"
    out_dir.mkdir(parents=True, exist_ok=True)

    diffs = difference_set(config.candidate_modes)
    a = Fraction(str(config.search.k_min))
    b = Fraction(str(config.search.k_max))

    per_m_rows: list[dict[str, object]] = []
    class_rows: list[dict[str, object]] = []
    summary_lines: list[str] = []
    summary_lines.append("# m Shell Classification Summary")
    summary_lines.append("")
    summary_lines.append(f"- Window: `[a,b]=[{a},{b}]`")
    summary_lines.append(f"- Target denominators: `{', '.join(str(q) for q in TARGET_QS)}`")
    summary_lines.append("")

    for q in TARGET_QS:
        residues = residue_set_nonzero(diffs, q)
        allowed = allowed_ms(q, a, b)
        stab = stabilizer(residues, q)

        exact_class_map: dict[tuple[int, ...], list[int]] = defaultdict(list)
        shell_class_map: dict[tuple[int, ...], list[int]] = defaultdict(list)
        transformed_by_m: dict[int, tuple[int, ...]] = {}
        signature_by_m: dict[int, tuple[int, ...]] = {}
        rho_by_m: dict[int, int] = {}
        hit_residues_by_m: dict[int, tuple[int, ...]] = {}
        hit_diffs_by_m: dict[int, tuple[int, ...]] = {}

        for m in allowed:
            transformed = transformed_residue_set(residues, m, q)
            signature = shell_signature(transformed, q)
            rho, hit_residues = first_hit_residues(transformed, q)
            hits = first_hit_diffs(diffs, m, q, rho)

            transformed_by_m[m] = transformed
            signature_by_m[m] = signature
            rho_by_m[m] = rho
            hit_residues_by_m[m] = hit_residues
            hit_diffs_by_m[m] = hits

            exact_class_map[transformed].append(m)
            shell_class_map[signature].append(m)

        exact_class_id_by_m: dict[int, int] = {}
        shell_class_id_by_m: dict[int, int] = {}

        for class_id, transformed in enumerate(sorted(exact_class_map, key=lambda item: exact_class_map[item][0]), start=1):
            members = tuple(sorted(exact_class_map[transformed]))
            representative = members[0]
            rho = rho_by_m[representative]
            signature = signature_by_m[representative]
            for m in members:
                exact_class_id_by_m[m] = class_id
            class_rows.append(
                {
                    "q": q,
                    "class_type": "exact",
                    "class_id": class_id,
                    "members": tuple_to_string(members),
                    "size": len(members),
                    "rho": rho,
                    "signature": signature_to_string(signature),
                    "first_hit_residues": tuple_to_string(hit_residues_by_m[representative]),
                    "first_hit_diffs": tuple_to_string(hit_diffs_by_m[representative]),
                }
            )

        for class_id, signature in enumerate(sorted(shell_class_map, key=lambda item: shell_class_map[item][0]), start=1):
            members = tuple(sorted(shell_class_map[signature]))
            representative = members[0]
            rho = rho_by_m[representative]
            for m in members:
                shell_class_id_by_m[m] = class_id
            class_rows.append(
                {
                    "q": q,
                    "class_type": "shell",
                    "class_id": class_id,
                    "members": tuple_to_string(members),
                    "size": len(members),
                    "rho": rho,
                    "signature": signature_to_string(signature),
                    "first_hit_residues": tuple_to_string(hit_residues_by_m[representative]),
                    "first_hit_diffs": tuple_to_string(hit_diffs_by_m[representative]),
                }
            )

        for m in allowed:
            per_m_rows.append(
                {
                    "q": q,
                    "m": m,
                    "k_fraction": f"{m}/{q}",
                    "k_decimal": float(Fraction(m, q)),
                    "rho_q_m": rho_by_m[m],
                    "s_min_q_m": rho_by_m[m] / q,
                    "exact_class_id": exact_class_id_by_m[m],
                    "shell_class_id": shell_class_id_by_m[m],
                    "shell_signature": signature_to_string(signature_by_m[m]),
                    "first_hit_residues": tuple_to_string(hit_residues_by_m[m]),
                    "first_hit_diffs": tuple_to_string(hit_diffs_by_m[m]),
                }
            )

        summary_lines.append(f"## q={q}")
        summary_lines.append("")
        summary_lines.append(f"- Allowed branches: `{tuple_to_string(tuple(allowed))}`")
        summary_lines.append(f"- Stabilizer size in `U_q`: `{len(stab)}`")
        summary_lines.append(f"- Stabilizer members: `{tuple_to_string(stab)}`")
        summary_lines.append(f"- Exact classes inside window: `{len(exact_class_map)}`")
        summary_lines.append(f"- Shell classes inside window: `{len(shell_class_map)}`")
        for m in allowed:
            summary_lines.append(
                f"- `m={m}`: `rho={rho_by_m[m]}`, `exact class={exact_class_id_by_m[m]}`, "
                f"`shell class={shell_class_id_by_m[m]}`, "
                f"`signature={signature_to_string(signature_by_m[m])}`, "
                f"`first-hit residues={tuple_to_string(hit_residues_by_m[m])}`, "
                f"`first-hit diffs={tuple_to_string(hit_diffs_by_m[m])}`."
            )
        summary_lines.append("")

    write_csv(
        out_dir / "per_m_classification.csv",
        per_m_rows,
        [
            "q",
            "m",
            "k_fraction",
            "k_decimal",
            "rho_q_m",
            "s_min_q_m",
            "exact_class_id",
            "shell_class_id",
            "shell_signature",
            "first_hit_residues",
            "first_hit_diffs",
        ],
    )
    write_csv(
        out_dir / "class_summary.csv",
        class_rows,
        [
            "q",
            "class_type",
            "class_id",
            "members",
            "size",
            "rho",
            "signature",
            "first_hit_residues",
            "first_hit_diffs",
        ],
    )
    (out_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    print("Completed m-shell classification analysis.")
    print(f"Output directory: {out_dir}")


if __name__ == "__main__":
    main()
