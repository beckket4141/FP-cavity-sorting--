# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This repository contains the manuscript and supporting code for a research paper on Laguerre-Gaussian (LG) mode sorting in Fabry-Perot (FP) cavities, built on a spectral-folding model. The work presents an analytical design framework, a capacity boundary, and experimental validation with a 9-mode consecutive target set. The two primary publication targets are:

- **OE manuscript** (`Sorting_in_FP_cavities/`) — Optica journal article (English), the primary publication.
- **南大学报 manuscript** (`南大学报/`) — Nanjing University journal article (Chinese), a separate paper with a broader "unified two-mirror framework + error mechanism" scope.

## Build / Compilation

### OE manuscript (LaTeX)

```powershell
cd "Sorting_in_FP_cavities"
pdflatex -interaction=nonstopmode "Sorting in FP cavities.tex"
bibtex "Sorting in FP cavities"
pdflatex -interaction=nonstopmode "Sorting in FP cavities.tex"
pdflatex -interaction=nonstopmode "Sorting in FP cavities.tex"
```

**Important**: The main file is `Sorting_in_FP_cavities/main.tex` (not `main.tex` in root). The `.bbl` is pre-generated and checked in alongside the source. The document uses `optica-article.cls` with `opticajnl.bst`. Figures live in `Sorting_in_FP_cavities/figures/main/`.

### OE supplemental document

```powershell
cd supplementary_matirial
pdflatex -interaction=nonstopmode supplement.tex
bibtex "supplement 1"
pdflatex -interaction=nonstopmode supplement.tex
pdflatex -interaction=nonstopmode supplement.tex
```

### OE single-tex package

`OE_single_tex_package/` contains a flattened version of the OE manuscript with all LaTeX merged into one file. Compile with a single `pdflatex` pass (references resolved in-line).

## Running analysis and verification code

All Python code lives under `验证推演3.15/`. The common shared library is `analysis_common.py` at the root. Key sub-projects:

### Core verification scripts (run standalone)

```powershell
cd 验证推演3.15
python 01_verify_continuous_analytic_optimum.py   # Continuous s_min landscape + analytic peak families
python 02_verify_platform_formula.py               # Platform-width formula verification
python 03_n9_experiment_platform_check.py           # M=9 experimental operating point check
python 04_n9_vs_n10_boundary.py                     # M=9 vs M=10 capacity boundary
python 05_mis_general_case_counterexamples.py       # General-case counterexample search
```

### Engineering screening pipeline

```powershell
cd 验证推演3.15/工程实用性
python 00_run_all.py  # Runs all screening steps sequentially
```

Individual steps: `01_branch_window_screen.py` through `09_finesse_robustness_maps.py`. Shared utilities in `engineering_screening_common.py`.

### Cavity parameter recalculation & experimental data analysis

```powershell
cd 验证推演3.15/腔实际性能参数验算
python 01_recalc_cavity_params.py                  # Recalculate cavity parameters from raw data
python 02_validate_peak_positions_vs_theory.py     # Validate measured peaks against theory
```

Data lives in `光腰为0.88mm测得数据/` and `光腰为0.98mm测得数据/`.

### Generalized FP cavity search algorithm

```powershell
cd 验证推演3.15/腔实际性能参数验算/一般化寻优算法
python run_generalized_screening.py                 # Full generalized screening run
```

Package: `generalized_fp/` with `core.py` (solver), `config.py`, `exporting.py`, `plotting.py`.

### Other sub-projects

- `tau到性能指标的重新推演/` — Tau metric to performance indicator derivation
- `FP腔一般化理论推导_双凹/` — Generalized two-mirror cavity theory
- `分形验证/` — Farey skeleton and fractal refinement verification
- `标定矩阵相关原理验证调研/` — Calibration matrix principles
- `径向模式串扰推演计算/` — Radial mode crosstalk analysis

### Tool scripts

`tool/simulation_params.py` is the canonical parameter source. Use `python tool/simulation_params.py` to print all thesis parameters and verify consistency. Other tools: `tool/read_latex.py`, `tool/read_pdf.py`.

## Architecture

### Theory model layers

The spectral-folding model has three layers, reflected in both the paper structure and code:

1. **Geometric layer** (`k` → folded positions): `k = (1/π) arccos(√(1-L/R))` maps cavity geometry to a single-FSR circle. This is the `k_from_lr` / `lr_from_k` / `folded_position` / `smin_for_lr` family in `analysis_common.py` and `tool/simulation_params.py`.

2. **Resolvability layer** (spacing + finesse → crosstalk): `τ_min = F · s_min` connects geometric spacing to physical linewidth separation. The Airy crosstalk sums and closed forms (`crosstalk_sum_M`, `crosstalk_sum_closed`, `crosstalk_limit`) are in `tool/simulation_params.py`.

3. **Capacity layer** (`M ≤ ⌊F/τ₀⌋`): the universal design inequality. The `design_blueprint()` function generates the design table.

### Key data flow in verification code

```
analysis_common.py  (shared: k↔L/R, s_min, platform formulas, MIS solver)
       ↓
tool/simulation_params.py  (canonical parameters, Airy crosstalk, design blueprint)
       ↓
Individual 0X_*.py scripts  (import analysis_common, produce outputs/)
```

### Manuscript structure (OE)

`Sorting_in_FP_cavities/main.tex` is a single-file LaTeX document (sections were merged from a prior multi-file layout). Section order: Introduction → Spectral-Folding Model and Design Criterion (with subsections on uniform-step sets, general sets, resolvability/capacity) → Nine-Mode Boundary-Probing Validation (setup, calibration, spectral verification, sorting performance) → Discussion → Conclusion.

### Important paths

- OE manuscript root: `Sorting_in_FP_cavities/`
- OE figures: `Sorting_in_FP_cavities/figures/main/`
- OE bibliography: `Sorting_in_FP_cavities/bib/refs_local.bib`
- Supplement: `supplementary_matirial/supplement.tex`
- Journal draft: `南大学报/manuscript/nju_jns_draft.md`
- Journal figures script: `南大学报/simulation/build_jns_figures.py`
- Shared analysis library: `验证推演3.15/analysis_common.py`
- Canonical parameters: `tool/simulation_params.py`
- All verification outputs: `验证推演3.15/outputs/`

## Key numerical reference values

These are the experimentally validated parameters (from `tool/simulation_params.py`):

| Parameter | Value |
|-----------|-------|
| Wavelength | 795 nm |
| FSR | 9.915 GHz |
| Finesse (measured) | 32.21 |
| M (target modes) | 9 |
| k* (design) | 2/9 ≈ 0.2222 |
| k (measured) | 0.2228 |
| (L/R)* (design) | ≈ 0.4132 |
| τ₀ (threshold) | 3 |
| Mean sorting efficiency | 93.19% |
| Mean ER_sum | 11.41 dB |
