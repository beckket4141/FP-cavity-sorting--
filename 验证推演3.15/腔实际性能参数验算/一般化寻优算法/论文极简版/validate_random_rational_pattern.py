from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


@dataclass(frozen=True)
class ValidationConfig:
    random_seed: int = 20260322
    case_count: int = 100
    set_size: int = 12
    mode_min: int = 1
    mode_max: int = 60
    k_min: float = 0.2
    k_max: float = 0.3
    target_L_over_R: float = 0.5
    q_max: int = 200
    coarse_samples: int = 6001
    refine_half_window: float = 0.0015
    refine_samples: int = 6001
    score_tolerance: float = 5e-5


@dataclass(frozen=True)
class Candidate:
    k: float
    s_min: float
    L_over_R: float
    source: str
    q: int | None = None
    m: int | None = None


def difference_set(modes: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted({b - a for idx, a in enumerate(modes) for b in modes[idx + 1 :]}))


def k_to_L_over_R(k: float) -> float:
    return math.sin(math.pi * k) ** 2


def s_min_from_diffs(diffs: tuple[int, ...], k: float) -> float:
    best = 0.5
    for d in diffs:
        x = (d * k) % 1.0
        dist = min(x, 1.0 - x)
        if dist < best:
            best = dist
    return best


def rank_key(candidate: Candidate, target_lr: float) -> tuple[float, float, float]:
    return (round(candidate.s_min, 12), -abs(candidate.L_over_R - target_lr), -abs(candidate.k - 0.25))


def linspace(start: float, stop: float, samples: int) -> list[float]:
    if samples <= 1:
        return [start]
    step = (stop - start) / (samples - 1)
    return [start + idx * step for idx in range(samples)]


def search_continuous(diffs: tuple[int, ...], config: ValidationConfig) -> Candidate:
    best: Candidate | None = None
    for k in linspace(config.k_min, config.k_max, config.coarse_samples):
        candidate = Candidate(k=k, s_min=s_min_from_diffs(diffs, k), L_over_R=k_to_L_over_R(k), source="continuous")
        if best is None or rank_key(candidate, config.target_L_over_R) > rank_key(best, config.target_L_over_R):
            best = candidate
    assert best is not None
    k_lo = max(config.k_min, best.k - config.refine_half_window)
    k_hi = min(config.k_max, best.k + config.refine_half_window)
    refined = best
    for k in linspace(k_lo, k_hi, config.refine_samples):
        candidate = Candidate(k=k, s_min=s_min_from_diffs(diffs, k), L_over_R=k_to_L_over_R(k), source="continuous")
        if rank_key(candidate, config.target_L_over_R) > rank_key(refined, config.target_L_over_R):
            refined = candidate
    return refined


def modular_distance(residue: int, q: int) -> int:
    residue %= q
    return min(residue, q - residue)


def search_rational(diffs: tuple[int, ...], config: ValidationConfig) -> Candidate:
    best: Candidate | None = None
    k_min_fraction = Fraction(str(config.k_min))
    k_max_fraction = Fraction(str(config.k_max))
    for q in range(2, config.q_max + 1):
        start = math.ceil(float(k_min_fraction * q))
        end = math.floor(float(k_max_fraction * q))
        for m in range(start, end + 1):
            if math.gcd(m, q) != 1:
                continue
            k_fraction = Fraction(m, q)
            if not (k_min_fraction <= k_fraction <= k_max_fraction):
                continue
            rho = q
            for d in diffs:
                rho = min(rho, modular_distance(d * m, q))
                if rho == 0:
                    break
            candidate = Candidate(
                k=float(k_fraction),
                s_min=rho / q,
                L_over_R=k_to_L_over_R(float(k_fraction)),
                source="rational",
                q=q,
                m=m,
            )
            if best is None or rank_key(candidate, config.target_L_over_R) > rank_key(best, config.target_L_over_R):
                best = candidate
    assert best is not None
    return best


def fraction_hint(value: float, max_denominator: int) -> str:
    frac = Fraction(value).limit_denominator(max_denominator)
    if abs(float(frac) - value) < 1e-6:
        return f"{frac.numerator}/{frac.denominator}"
    return ""


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    config = ValidationConfig()
    rng = random.Random(config.random_seed)
    root = Path(__file__).resolve().parent
    out_dir = root / "results" / "random_validation"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    denominator_hist: dict[int, int] = {}
    match_count = 0
    rational_beats_grid_count = 0
    unmatched_count = 0

    for case_id in range(1, config.case_count + 1):
        modes = tuple(sorted(rng.sample(range(config.mode_min, config.mode_max + 1), config.set_size)))
        diffs = difference_set(modes)
        continuous_best = search_continuous(diffs, config)
        rational_best = search_rational(diffs, config)
        gap = continuous_best.s_min - rational_best.s_min

        if abs(gap) <= config.score_tolerance:
            status = "match"
            match_count += 1
        elif gap < -config.score_tolerance:
            status = "rational_beats_grid"
            rational_beats_grid_count += 1
        else:
            status = "unmatched"
            unmatched_count += 1

        assert rational_best.q is not None
        denominator_hist[rational_best.q] = denominator_hist.get(rational_best.q, 0) + 1

        rows.append(
            {
                "case_id": case_id,
                "modes": str(list(modes)),
                "difference_count": len(diffs),
                "continuous_best_k": continuous_best.k,
                "continuous_best_k_fraction_hint": fraction_hint(continuous_best.k, config.q_max),
                "continuous_best_s_min": continuous_best.s_min,
                "continuous_best_L_over_R": continuous_best.L_over_R,
                "rational_best_q": rational_best.q,
                "rational_best_m": rational_best.m,
                "rational_best_k": rational_best.k,
                "rational_best_k_fraction": f"{rational_best.m}/{rational_best.q}",
                "rational_best_s_min": rational_best.s_min,
                "rational_best_L_over_R": rational_best.L_over_R,
                "continuous_minus_rational": gap,
                "status": status,
            }
        )

    write_csv(
        out_dir / "validation_cases.csv",
        rows,
        [
            "case_id",
            "modes",
            "difference_count",
            "continuous_best_k",
            "continuous_best_k_fraction_hint",
            "continuous_best_s_min",
            "continuous_best_L_over_R",
            "rational_best_q",
            "rational_best_m",
            "rational_best_k",
            "rational_best_k_fraction",
            "rational_best_s_min",
            "rational_best_L_over_R",
            "continuous_minus_rational",
            "status",
        ],
    )

    hist_rows = [
        {"q": q, "count": count}
        for q, count in sorted(denominator_hist.items(), key=lambda item: (-item[1], item[0]))
    ]
    write_csv(out_dir / "denominator_histogram.csv", hist_rows, ["q", "count"])

    top_examples = sorted(rows, key=lambda item: item["continuous_minus_rational"], reverse=True)[:10]
    worst_rational = sorted(rows, key=lambda item: item["continuous_minus_rational"])[:10]

    lines: list[str] = []
    lines.append("# Random Validation Summary")
    lines.append("")
    lines.append(f"- Random seed: `{config.random_seed}`")
    lines.append(f"- Case count: `{config.case_count}`")
    lines.append(f"- Set size: `{config.set_size}`")
    lines.append(f"- Mode range: `[{config.mode_min}, {config.mode_max}]`")
    lines.append(f"- Search window: `k in [{config.k_min}, {config.k_max}]`")
    lines.append(f"- Rational search denominator cap: `q <= {config.q_max}`")
    lines.append("")
    lines.append("## Outcome Counts")
    lines.append("")
    lines.append(f"- `match`: `{match_count}`")
    lines.append(f"- `rational_beats_grid`: `{rational_beats_grid_count}`")
    lines.append(f"- `unmatched`: `{unmatched_count}`")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- `match` means the best rational candidate up to the scanned denominator cap matches the dense continuous search to within the tolerance.")
    lines.append("- `rational_beats_grid` usually means the dense grid missed a narrow optimum but the rational candidate found it more cleanly.")
    lines.append("- `unmatched` means the dense continuous search still beats the rational search cap by more than the tolerance; this may indicate either a larger-denominator optimum or simple undersampling effects.")
    lines.append("")
    lines.append("## Most Frequent Best Denominators")
    lines.append("")
    for row in hist_rows[:10]:
        lines.append(f"- `q={row['q']}` appears `{row['count']}` times.")
    lines.append("")
    lines.append("## Largest Continuous Advantage Cases")
    lines.append("")
    for item in top_examples:
        lines.append(
            f"- Case {item['case_id']}: gap = `{item['continuous_minus_rational']:.8f}`, "
            f"continuous `k≈{item['continuous_best_k']:.6f}`, rational `{item['rational_best_k_fraction']}`."
        )
    lines.append("")
    lines.append("## Largest Rational Advantage Cases")
    lines.append("")
    for item in worst_rational:
        lines.append(
            f"- Case {item['case_id']}: gap = `{item['continuous_minus_rational']:.8f}`, "
            f"continuous `k≈{item['continuous_best_k']:.6f}`, rational `{item['rational_best_k_fraction']}`."
        )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Completed random rational-pattern validation.")
    print(f"Output directory: {out_dir}")
    print(f"match={match_count}, rational_beats_grid={rational_beats_grid_count}, unmatched={unmatched_count}")


if __name__ == "__main__":
    main()
