# Engineering Practicality Analysis

This folder extends the 2026-03-15 analytic verification scripts by adding an
engineering screening layer on top of the exact continuous-full-load branches
`k*=m/N`.

The current write-up keeps `tau/delta` as the main theoretical coordinates and
uses

`rho = F / (N * tau0) = 1 / (N * delta)`

as a derived engineering margin factor for continuous full-load design. The new
finesse-sensitivity pass adds a second derived layer:

- `rho` tells us how far a nominal design sits above the analytic existence
  boundary.
- achieved finesse robustness tells us how much that nominal `rho` can shrink
  when the realized cavity finesse deviates from the design value.
- the `R -> F` mapping is only used as an upstream sensitivity model for
  reflectivity and loss errors; the actual screening still uses the achieved or
  measured finesse directly.

Files:

- `00_run_all.py`: run every script below in order.
- `01_branch_window_screen.py`: screen the exact branches with a practical
  `L/R` window and show how the mathematical branch family shrinks.
- `02_fixed_m_scaling.py`: verify the asymptotic collapse of small-`m` and
  edge branches as `N` grows.
- `03_relative_margin_filter.py`: add a relative threshold margin
  `eta = N * delta` and a minimum platform-width filter in `L`.
- `engineering_screening_common.py`: shared formulas, scenarios, screening
  logic, `rho` helpers, and finesse-sensitivity utilities.
- `04_geometry_engineering_screen.py`: compute `L`, `w0`, curved-mirror spot
  size, and boundary distance for every analytic branch.
- `05_dual_scenario_effective_branches.py`: apply geometry screening and
  `tau/F` platform screening under two parameterized scenarios.
- `06_rho_margin_scan.py`: scan `rho`, `tau0`, and `N` to map required finesse,
  analytic headroom, final branch counts, and platform-width trends.
- `07_rho_design_maps.py`: turn the `06` CSV outputs into design charts and a
  representative required-finesse table.
- `08_finesse_robustness_scan.py`: scan achieved finesse shortfall, nominal
  `rho`, and reflectivity error to quantify how finesse uncertainty maps to
  `rho_actual`, final branch survival, and platform width.
- `09_finesse_robustness_maps.py`: turn the `08` CSV outputs into finesse-budget
  charts and the table that justifies the `rho` bands.
- `详细报告_工程筛选与理论价值重估.md`: main write-up for the engineering
  screening story and the theory-value reassessment.
- `rho规律与设计结论.md`: dedicated memo on how `rho` should be explained and
  how it should be constrained by finesse-budget arguments.
- `精细度敏感性与rho分档依据.md`: focused memo on achieved-finesse robustness,
  reflectivity-to-finesse sensitivity, and defensible `rho` band wording.

Key outputs added by the `rho` pass:

- `outputs/06_rho_margin_scan/rho_margin_scan_details.csv`
- `outputs/06_rho_margin_scan/rho_margin_scan_summary.csv`
- `outputs/06_rho_margin_scan/rho_representative_cases.csv`
- `outputs/07_rho_design_maps/required_finesse_lines.png`
- `outputs/07_rho_design_maps/rho_headroom_curve.png`
- `outputs/07_rho_design_maps/rho_branch_counts.png`
- `outputs/07_rho_design_maps/rho_platform_width_representatives.png`
- `outputs/07_rho_design_maps/rho_design_table.csv`

Key outputs added by the finesse-robustness pass:

- `outputs/08_finesse_robustness_scan/finesse_relative_error_scan.csv`
- `outputs/08_finesse_robustness_scan/reflectivity_to_finesse_scan.csv`
- `outputs/08_finesse_robustness_scan/current_design_finesse_anchor.csv`
- `outputs/08_finesse_robustness_scan/rho_required_under_finesse_shortfall.csv`
- `outputs/09_finesse_robustness_maps/rho_required_vs_finesse_shortfall.png`
- `outputs/09_finesse_robustness_maps/reflectivity_error_to_finesse_gain.png`
- `outputs/09_finesse_robustness_maps/rho_nominal_to_rho_actual_bands.png`
- `outputs/09_finesse_robustness_maps/current_design_29p8_vs_31p35_anchor.png`
- `outputs/09_finesse_robustness_maps/rho_band_justification_table.csv`

Default assumptions used here:

- `R = 25 mm`
- monolithic crystal cavity model:
  `lambda0 = 795 nm` (vacuum wavelength), `n = 1.453371` (quartz at 795 nm),
  and `lambda_medium = lambda0 / n`
- current-platform thresholds:
  `L >= 3.0 mm`, `w_curved <= 180 um`, `Delta L >= 0.10 mm`,
  and soft `w0` bands:
  `comfortable (w0 >= 50 um)`, `experimental_ok (47 um <= w0 < 50 um)`,
  `high_risk (w0 < 47 um)`
- relaxed comparison thresholds:
  `L >= 2.5 mm`, `w_curved <= 220 um`, `Delta L >= 0.05 mm`,
  with the same soft `w0` bands:
  `comfortable/experimental_ok/high_risk` = `>=50 / [47,50) / <47 um`
- `tau0` scan values:
  `3, 4, 5, 6`
- `rho` scan values:
  `1.00, 1.02, 1.05, 1.10, 1.15, 1.20, 1.30`
- nominal `rho` values in the finesse-budget scan:
  `1.05, 1.10, 1.15, 1.20`
- achieved finesse relative errors:
  `-10%, -5%, -2%, 0, +2%, +5%, +10%`
- target finesse values in the reflectivity scan:
  `29.8, 40, 95, 160, 180`
- reflectivity absolute errors in the upstream sensitivity scan:
  `-0.010, -0.005, -0.002, -0.001, 0, +0.001, +0.002, +0.005, +0.010`

These values are only a baseline for discussion and can be edited directly at
the top of each script.
