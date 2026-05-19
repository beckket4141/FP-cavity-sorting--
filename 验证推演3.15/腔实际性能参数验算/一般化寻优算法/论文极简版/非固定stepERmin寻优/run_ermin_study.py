from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def find_workspace_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        probe = candidate / "oe_paper" / "simulation" / "scripts" / "fp_design" / "core.py"
        if probe.exists():
            return candidate
    raise FileNotFoundError("Could not locate thesis workspace root from current script path.")


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = find_workspace_root(SCRIPT_DIR)
SIM_SCRIPTS_DIR = WORKSPACE_ROOT / "oe_paper" / "simulation" / "scripts"
if str(SIM_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_SCRIPTS_DIR))

from fp_design.core import enumerate_exact_candidates, evaluate_response_metrics, parse_fraction  # noqa: E402


OUTPUT_TABLES_DIR = SCRIPT_DIR / "tables"
OUTPUT_REPORTS_DIR = SCRIPT_DIR / "reports"

CSV_ENCODING = "utf-8-sig"
FLOAT_TOL = 1e-12


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    config_path = SCRIPT_DIR / "case_config.json"
    return json.loads(config_path.read_text(encoding="utf-8"))


def candidate_sort_by_smin(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        by=["s_min", "geometry_gap_to_0p5", "q", "m"],
        ascending=[False, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)


def candidate_sort_by_ermin(df: pd.DataFrame, label: str) -> pd.DataFrame:
    return df.sort_values(
        by=[f"ER_min_dB_{label}", f"ER_mean_dB_{label}", "geometry_gap_to_0p5", "q", "m"],
        ascending=[False, False, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)


def compute_candidate_rows(config: dict) -> tuple[pd.DataFrame, int]:
    modes = [int(value) for value in config["target_modes"]]
    k_min = parse_fraction(config["search_window"]["k_min"])
    k_max = parse_fraction(config["search_window"]["k_max"])
    tau0 = float(config["tau0"])
    geometry_target = float(config["geometry_target_L_over_R"])
    fixed_finesse_values = {str(key): float(value) for key, value in config["fixed_finesse_values"].items()}

    candidates, q_limit = enumerate_exact_candidates(modes, k_min, k_max, geometry_target=geometry_target)
    rows: list[dict[str, float | int | str | bool]] = []

    for candidate in candidates:
        row: dict[str, float | int | str | bool] = {
            "k_fraction": str(candidate.k_fraction),
            "k": candidate.k,
            "q": candidate.q,
            "m": candidate.m,
            "s_min_fraction": str(candidate.s_min_fraction),
            "s_min": candidate.s_min,
            "F_min_tau0": math.inf if candidate.s_min <= FLOAT_TOL else tau0 / candidate.s_min,
            "L_over_R": candidate.l_over_r,
            "geometry_gap_to_0p5": candidate.geometry_gap,
            "has_positive_s_min": bool(candidate.s_min > FLOAT_TOL),
        }
        for label, finesse in fixed_finesse_values.items():
            metrics = evaluate_response_metrics(modes, candidate.k, finesse)
            worst_idx = int(np.argmin(metrics.er_sum_db))
            row[f"ER_min_dB_{label}"] = float(metrics.min_er_sum_db)
            row[f"ER_mean_dB_{label}"] = float(metrics.mean_er_sum_db)
            row[f"ER_worst_mode_{label}"] = int(modes[worst_idx])
            row[f"efficiency_min_{label}"] = float(metrics.min_efficiency)
            row[f"efficiency_mean_{label}"] = float(metrics.mean_efficiency)
        rows.append(row)

    all_df = pd.DataFrame(rows)
    return all_df, q_limit


def add_ranks(all_df: pd.DataFrame, fixed_finesse_labels: list[str]) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    ranked_views: dict[str, pd.DataFrame] = {}

    ranking_by_smin = candidate_sort_by_smin(all_df).copy()
    ranking_by_smin.insert(0, "rank_by_smin", range(1, len(ranking_by_smin) + 1))
    ranked_views["smin"] = ranking_by_smin

    merged = all_df.copy()
    merged = merged.merge(
        ranking_by_smin[["k_fraction", "rank_by_smin"]],
        on="k_fraction",
        how="left",
        validate="one_to_one",
    )

    for label in fixed_finesse_labels:
        ranking = candidate_sort_by_ermin(all_df, label).copy()
        rank_col = f"rank_by_ERmin_{label}"
        ranking.insert(0, rank_col, range(1, len(ranking) + 1))
        ranked_views[label] = ranking
        merged = merged.merge(
            ranking[["k_fraction", rank_col]],
            on="k_fraction",
            how="left",
            validate="one_to_one",
        )

    merged = merged.sort_values("rank_by_smin", kind="mergesort").reset_index(drop=True)
    return merged, ranked_views


def pareto_frontier(df: pd.DataFrame, er_col: str) -> pd.DataFrame:
    finite_df = df[np.isfinite(df["F_min_tau0"])].copy()
    finite_df = finite_df.sort_values(
        by=["F_min_tau0", er_col, "geometry_gap_to_0p5", "q", "m"],
        ascending=[True, False, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)

    frontier_indices: list[int] = []
    best_er_so_far = -math.inf
    for idx, row in finite_df.iterrows():
        er_value = float(row[er_col])
        if er_value > best_er_so_far + FLOAT_TOL:
            frontier_indices.append(idx)
            best_er_so_far = er_value

    frontier_df = finite_df.loc[frontier_indices].copy().reset_index(drop=True)
    frontier_df.insert(0, "pareto_rank", range(1, len(frontier_df) + 1))
    frontier_df.insert(1, "pareto_metric", er_col)
    return frontier_df


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [header, separator]
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(rows)


def format_db_delta(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}"


def build_report(
    config: dict,
    all_df: pd.DataFrame,
    ranked_views: dict[str, pd.DataFrame],
    frontier_df: pd.DataFrame,
    q_limit: int,
) -> str:
    fixed_finesse_values = {str(key): float(value) for key, value in config["fixed_finesse_values"].items()}
    baseline_candidate = str(config["baseline_checks"]["candidate"])
    pareto_label = str(config["pareto_reference_finesse"])
    expected_family = list(config["expected_smin_optimal_family"])

    ranking_by_smin = ranked_views["smin"]
    baseline_row = all_df.loc[all_df["k_fraction"] == baseline_candidate].iloc[0]
    family_df = ranking_by_smin.loc[ranking_by_smin["k_fraction"].isin(expected_family)].copy()
    family_df = family_df.sort_values("geometry_gap_to_0p5", kind="mergesort").reset_index(drop=True)

    family_df["ERmin_rank_within_family_F32p21"] = (
        family_df["ER_min_dB_F32p21"].rank(method="dense", ascending=False).astype(int)
    )
    family_df["ERmin_rank_within_family_F87"] = (
        family_df["ER_min_dB_F87"].rank(method="dense", ascending=False).astype(int)
    )

    best_ermin_rows = {label: ranked_views[label].iloc[0] for label in fixed_finesse_values}
    constrained_f87 = all_df.loc[all_df["F_min_tau0"] <= fixed_finesse_values[pareto_label] + FLOAT_TOL].copy()
    constrained_f87 = candidate_sort_by_ermin(constrained_f87, pareto_label)
    constrained_best = constrained_f87.iloc[0]

    top_family_md = markdown_table(
        family_df[
            [
                "k_fraction",
                "L_over_R",
                "geometry_gap_to_0p5",
                "ER_min_dB_F32p21",
                "ER_min_dB_F87",
                "ERmin_rank_within_family_F32p21",
                "ERmin_rank_within_family_F87",
            ]
        ].round(
            {
                "L_over_R": 6,
                "geometry_gap_to_0p5": 6,
                "ER_min_dB_F32p21": 3,
                "ER_min_dB_F87": 3,
            }
        ),
        [
            "k_fraction",
            "L_over_R",
            "geometry_gap_to_0p5",
            "ER_min_dB_F32p21",
            "ER_min_dB_F87",
            "ERmin_rank_within_family_F32p21",
            "ERmin_rank_within_family_F87",
        ],
    )

    frontier_preview = frontier_df.head(6).copy()
    frontier_preview = frontier_preview[
        [
            "pareto_rank",
            "k_fraction",
            "F_min_tau0",
            f"ER_min_dB_{pareto_label}",
            f"ER_mean_dB_{pareto_label}",
            "geometry_gap_to_0p5",
        ]
    ].round(
        {
            "F_min_tau0": 3,
            f"ER_min_dB_{pareto_label}": 3,
            f"ER_mean_dB_{pareto_label}": 3,
            "geometry_gap_to_0p5": 6,
        }
    )
    frontier_md = markdown_table(
        frontier_preview,
        [
            "pareto_rank",
            "k_fraction",
            "F_min_tau0",
            f"ER_min_dB_{pareto_label}",
            f"ER_mean_dB_{pareto_label}",
            "geometry_gap_to_0p5",
        ],
    )

    best_f32 = best_ermin_rows["F32p21"]
    best_f87 = best_ermin_rows["F87"]
    delta_f87 = float(best_f87[f"ER_min_dB_F87"]) - float(baseline_row["ER_min_dB_F87"])
    delta_f32 = float(best_f32[f"ER_min_dB_F32p21"]) - float(baseline_row["ER_min_dB_F32p21"])
    delta_family_f87 = float(constrained_best[f"ER_min_dB_F87"]) - float(baseline_row["ER_min_dB_F87"])

    lines = [
        "# ERmin vs smin Nonuniform Study",
        "",
        "## Scope",
        "- Target directory only: the current ERmin study folder.",
        "- Reused the same `oe_paper/simulation/scripts/fp_design/core.py` Airy-response and `ER_sum` definition.",
        "- Candidate set is exactly the finite rational search used by the existing `smin` study; no continuous black-box scan was introduced.",
        "",
        "## Objective Definition",
        "",
        "For fixed finesse `F`, this study treats",
        "",
        "`ERmin(F) = max_k min_i ER_sum_i(F; k)`",
        "",
        "as a different optimization target from",
        "",
        "`smin(k) = max_k s_min(k)`",
        "",
        "and from the derived requirement `F_min = tau0 / s_min` with `tau0=3`.",
        "",
        "## Baseline Reproduction",
        f"- Exact denominator bound reproduced: `q_limit={q_limit}`.",
        f"- `smin` optimal family reproduced: `{', '.join(expected_family)}`.",
        f"- Geometry-favored `smin` choice reproduced: `{config['expected_geometry_favored_candidate']}`.",
        (
            f"- Baseline `{baseline_candidate}` check passed at `F=32.21`: "
            f"`ER_min={baseline_row['ER_min_dB_F32p21']:.6f} dB`, "
            f"`ER_mean={baseline_row['ER_mean_dB_F32p21']:.6f} dB`."
        ),
        (
            f"- Baseline `{baseline_candidate}` check passed at `F=87`: "
            f"`ER_min={baseline_row['ER_min_dB_F87']:.6f} dB`, "
            f"`ER_mean={baseline_row['ER_mean_dB_F87']:.6f} dB`."
        ),
        "",
        "## Main Results",
        (
            f"- Fixed `F=32.21` worst-channel optimum moves to `{best_f32['k_fraction']}`: "
            f"`ER_min={best_f32['ER_min_dB_F32p21']:.3f} dB`, "
            f"`ER_mean={best_f32['ER_mean_dB_F32p21']:.3f} dB`, "
            f"`s_min={best_f32['s_min_fraction']}`, "
            f"`F_min={best_f32['F_min_tau0']:.1f}`. "
            f"Relative to `{baseline_candidate}`, worst-channel ER changes by `{format_db_delta(delta_f32)} dB`."
        ),
        (
            f"- Fixed `F=87` worst-channel optimum also moves to `{best_f87['k_fraction']}`: "
            f"`ER_min={best_f87['ER_min_dB_F87']:.3f} dB`, "
            f"`ER_mean={best_f87['ER_mean_dB_F87']:.3f} dB`, "
            f"`s_min={best_f87['s_min_fraction']}`, "
            f"`F_min={best_f87['F_min_tau0']:.1f}`. "
            f"Relative to `{baseline_candidate}`, worst-channel ER changes by `{format_db_delta(delta_f87)} dB`."
        ),
        (
            f"- The `F=87` optimum `{best_f87['k_fraction']}` is **not** a cheaper design: "
            f"its own `F_min={best_f87['F_min_tau0']:.1f}` is higher than `87`, "
            "so it represents a different trade-off rather than a contradiction of the current `smin` choice."
        ),
        (
            f"- If we keep the current `tau0=3` requirement ceiling `F_min<=87`, "
            f"the best `ERmin(F=87)` candidate becomes `{constrained_best['k_fraction']}`, "
            f"not `{baseline_candidate}`. "
            f"It improves worst-channel ER by `{format_db_delta(delta_family_f87)} dB` at the same `F_min={constrained_best['F_min_tau0']:.1f}`."
        ),
        "",
        "## smin-Optimal Family Comparison",
        top_family_md,
        "",
        (
            f"Inside the current `smin`-optimal family, `{constrained_best['k_fraction']}` is the best `ERmin` point at both fixed finesse values, "
            f"while `{baseline_candidate}` remains the geometry-favored point because its `L/R` stays closest to `0.5`."
        ),
        "",
        "## Pareto View",
        (
            f"The Pareto table `pareto_frontier_Fmin_vs_ERmin.csv` uses `ER_min(F={fixed_finesse_values[pareto_label]:.2f})` "
            f"as the vertical metric and `F_min=tau0/s_min` as the horizontal cost."
        ),
        frontier_md,
        "",
        "## Interpretation",
        "- The reviewer-style question is valid: replacing `smin` by fixed-finesse `ERmin` does change the optimizer.",
        "- That change does not invalidate the current `smin` derivation, because the two objectives answer different design questions.",
        "- The current `7/29` point is consistent with the existing policy `maximize smin first, then prefer moderate geometry`.",
        (
            f"- If the policy were changed to `maximize ERmin at fixed F=87 while staying within the current threshold`, "
            f"`6/29` would be the more natural pick than `7/29`."
        ),
        "",
        "## Appendix Recommendation",
        (
            "Recommendation: keep the current `smin`-based appendix figure and add one clarifying sentence, "
            "rather than inserting a new default appendix figure. "
            "The extra Pareto/frontier plot generated here is better kept as reviewer-response backup material."
        ),
        (
            "Suggested sentence: \"The nonuniform example in Fig. S3 is selected under the `s_min` / `F_min` design objective; "
            "if one instead optimizes the fixed-finesse worst-channel `ER_sum`, the preferred rational candidate shifts, "
            "but only by trading against a higher required finesse or a less central cavity geometry.\""
        ),
    ]

    return "\n".join(lines) + "\n"


def run_baseline_checks(config: dict, all_df: pd.DataFrame, q_limit: int) -> None:
    expected_q_limit = int(config["baseline_checks"]["expected_q_limit"])
    if q_limit != expected_q_limit:
        raise AssertionError(f"Expected q_limit={expected_q_limit}, got {q_limit}.")

    expected_family = sorted(str(value) for value in config["expected_smin_optimal_family"])
    ranking_by_smin = candidate_sort_by_smin(all_df)
    max_smin = float(ranking_by_smin.iloc[0]["s_min"])
    actual_family = sorted(
        str(value)
        for value in ranking_by_smin.loc[np.isclose(ranking_by_smin["s_min"], max_smin, atol=FLOAT_TOL), "k_fraction"].tolist()
    )
    if actual_family != expected_family:
        raise AssertionError(f"Expected smin family {expected_family}, got {actual_family}.")

    geometry_favored = str(ranking_by_smin.iloc[0]["k_fraction"])
    expected_geometry_favored = str(config["expected_geometry_favored_candidate"])
    if geometry_favored != expected_geometry_favored:
        raise AssertionError(
            f"Expected geometry-favored candidate {expected_geometry_favored}, got {geometry_favored}."
        )

    baseline_candidate = str(config["baseline_checks"]["candidate"])
    baseline_row = all_df.loc[all_df["k_fraction"] == baseline_candidate]
    if baseline_row.empty:
        raise AssertionError(f"Could not find baseline candidate {baseline_candidate}.")
    baseline_row = baseline_row.iloc[0]

    for label, expected_metrics in config["baseline_checks"]["metrics"].items():
        expected_er_min = float(expected_metrics["ER_min_dB"])
        expected_er_mean = float(expected_metrics["ER_mean_dB"])
        actual_er_min = float(baseline_row[f"ER_min_dB_{label}"])
        actual_er_mean = float(baseline_row[f"ER_mean_dB_{label}"])
        if not math.isclose(actual_er_min, expected_er_min, rel_tol=0.0, abs_tol=1e-9):
            raise AssertionError(
                f"Baseline ER_min mismatch for {label}: expected {expected_er_min}, got {actual_er_min}."
            )
        if not math.isclose(actual_er_mean, expected_er_mean, rel_tol=0.0, abs_tol=1e-9):
            raise AssertionError(
                f"Baseline ER_mean mismatch for {label}: expected {expected_er_mean}, got {actual_er_mean}."
            )


def main() -> None:
    ensure_dir(OUTPUT_TABLES_DIR)
    ensure_dir(OUTPUT_REPORTS_DIR)

    config = load_config()
    fixed_finesse_labels = list(config["fixed_finesse_values"].keys())

    all_df, q_limit = compute_candidate_rows(config)
    run_baseline_checks(config, all_df, q_limit)

    all_df_with_ranks, ranked_views = add_ranks(all_df, fixed_finesse_labels)
    pareto_label = str(config["pareto_reference_finesse"])
    frontier_df = pareto_frontier(all_df_with_ranks, f"ER_min_dB_{pareto_label}")

    family_df = all_df_with_ranks.loc[
        all_df_with_ranks["k_fraction"].isin(config["expected_smin_optimal_family"])
    ].copy()
    family_df = family_df.sort_values(
        by=["geometry_gap_to_0p5", "k"],
        ascending=[True, True],
        kind="mergesort",
    ).reset_index(drop=True)

    all_df_with_ranks.to_csv(OUTPUT_TABLES_DIR / "all_candidate_metrics.csv", index=False, encoding=CSV_ENCODING)
    ranked_views["smin"].to_csv(OUTPUT_TABLES_DIR / "ranking_by_smin.csv", index=False, encoding=CSV_ENCODING)
    ranked_views["F32p21"].to_csv(
        OUTPUT_TABLES_DIR / "ranking_by_ERmin_F32p21.csv", index=False, encoding=CSV_ENCODING
    )
    ranked_views["F87"].to_csv(OUTPUT_TABLES_DIR / "ranking_by_ERmin_F87.csv", index=False, encoding=CSV_ENCODING)
    family_df.to_csv(
        OUTPUT_TABLES_DIR / "smin_optimal_family_comparison.csv", index=False, encoding=CSV_ENCODING
    )
    frontier_df.to_csv(
        OUTPUT_TABLES_DIR / "pareto_frontier_Fmin_vs_ERmin.csv", index=False, encoding=CSV_ENCODING
    )

    report_text = build_report(config, all_df_with_ranks, ranked_views, frontier_df, q_limit)
    (OUTPUT_REPORTS_DIR / "ERmin_vs_smin_report.md").write_text(report_text, encoding="utf-8")

    print(f"Outputs written to: {SCRIPT_DIR}")
    print(f"q_limit={q_limit}")
    print(f"Best by smin: {ranked_views['smin'].iloc[0]['k_fraction']}")
    print(f"Best by ERmin@F32.21: {ranked_views['F32p21'].iloc[0]['k_fraction']}")
    print(f"Best by ERmin@F87: {ranked_views['F87'].iloc[0]['k_fraction']}")


if __name__ == "__main__":
    main()
