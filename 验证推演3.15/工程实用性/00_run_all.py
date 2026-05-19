from __future__ import annotations

import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SCRIPTS = [
    "01_branch_window_screen.py",
    "02_fixed_m_scaling.py",
    "03_relative_margin_filter.py",
    "04_geometry_engineering_screen.py",
    "05_dual_scenario_effective_branches.py",
    "06_rho_margin_scan.py",
    "07_rho_design_maps.py",
    "08_finesse_robustness_scan.py",
    "09_finesse_robustness_maps.py",
]


def main() -> None:
    for script_name in SCRIPTS:
        script_path = BASE_DIR / script_name
        print(f"Running {script_path.name} ...")
        subprocess.run([sys.executable, str(script_path)], check=True)


if __name__ == "__main__":
    main()
