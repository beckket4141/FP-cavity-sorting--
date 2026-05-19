# 主图、正文引用与图题脚手架

当前主图以 `simulation/outputs/figures/` 中的新版 5 幅图为准。旧版 `figures/exports/` 和 `build_jns_figures.py` 只作历史参考。

## 图 1 统一折叠谱与几何回代

- 文件：
  - `simulation/outputs/figures/fig01_general_cavity_framework.png`
  - `simulation/outputs/figures/fig01_general_cavity_framework.pdf`
- 数据源：
  - `simulation/outputs/data/general_cavity_mapping.csv`
  - `simulation/outputs/data/general_cavity_backsubstitution_checks.csv`
- 正文引用位置：
  - 第 2 节“稳定双镜 FP 腔的 Gouy 相位折叠谱框架”
- 功能：
  - 建立 `k_eff` 控制的折叠谱排布。
  - 展示 `k_eff` 到 `L/R` 的几何回代。
  - 平凹和对称双凹作为主要可讨论构型；一般非对称两镜腔只作为框架可扩展对象。
- 图前检查：
  - 若实际图中只清楚展示平凹和对称双凹，正文只需一句说明一般非对称腔可按同一 `g1 g2` 公式处理。
  - 若实际图中有明显的一般非对称腔曲线或 panel，第 2 节必须补一小段说明非对称腔在相同 `k_eff` 下对应一族几何实现。
- 中文图题：
  - 稳定双镜 FP 腔中 LG 模式分束的统一折叠谱框架。
- 英文图题：
  - Unified folded-spectrum framework for LG mode sorting in stable two-mirror FP cavities.

## 图 2 最小间距景观与解析最优分支

- 文件：
  - `simulation/outputs/figures/fig02_continuous_N_landscape.png`
  - `simulation/outputs/figures/fig02_continuous_N_landscape.pdf`
- 数据源：
  - `simulation/outputs/data/continuous_N_smin_landscape.csv`
  - `simulation/outputs/data/continuous_N_optimal_branches.csv`
- 正文引用位置：
  - 第 3 节“连续模式组的最小间距景观与最优排布”
- 功能：
  - 展示 `s_min(k)` 下包络结构。
  - 标出解析最优分支 `k=m/M`。
  - 用 Farey/层级细化解释景观结构，不写成严格分形。
- 中文图题：
  - 连续模式组的最小间距景观与解析最优分支。
- 英文图题：
  - Minimum-spacing landscape and analytic optimal branches for consecutive mode groups.

## 图 3 Airy 串扰热图与容量边界

- 文件：
  - `simulation/outputs/figures/fig03_airy_response_matrix.png`
  - `simulation/outputs/figures/fig03_airy_response_matrix.pdf`
- 数据源：
  - `simulation/outputs/data/continuous_M9_raw_airy_response_matrix.csv`
  - `simulation/outputs/data/continuous_M9_condition_probability_matrix.csv`
  - `simulation/outputs/data/continuous_M9_response_summary.json`
  - `simulation/outputs/data/continuous_capacity_boundary.csv`
- 正文引用位置：
  - 第 4 节“Airy 透射下的有限维串扰、性能指标与容量边界”
- 功能：
  - 用热图展示 `M=9` 的有限维 Airy 串扰结构和条件概率结构。
  - 支撑理论数值 `eta_sort=94.1166%`、`ER_sum=12.0404 dB`。
  - 正文中将容量边界作为 Airy 串扰阈值的自然后续，而不是另起一条线。
- 中文图题：
  - \(M=9\) 连续模式组的 Airy 串扰热图与条件概率分布。
- 英文图题：
  - Airy crosstalk maps and conditional probabilities for a consecutive mode group with \(M=9\).

## 图 4 几何实现与鲁棒性排序

- 文件：
  - `simulation/outputs/figures/fig04_capacity_performance.png`
  - `simulation/outputs/figures/fig04_capacity_performance.pdf`
- 数据源：
  - `simulation/outputs/data/m9_general_cavity_branch_sensitivity.csv`
  - `simulation/outputs/reports/table_m9_cavity_branch_sensitivity.csv`
  - `simulation/outputs/reports/table_continuous_design_blueprint_tau0_3.csv`
- 正文引用位置：
  - 第 4 节末尾，作为从 Airy 性能闭环回到几何实现层的过渡。
- 功能：
  - 比较平凹与对称双凹的几何实现。
  - 展示 `M=9` 时平凹偏向 `m=2`、对称双凹偏向 `m=4` 的鲁棒性排序。
  - 强调同一 `k_eff` 下串扰性能相同，差异来自几何回代和灵敏度。
- 正文篇幅：
  - 图 4 服务于第 4 节末尾的实现层过渡，正文控制在 1 到 2 段。
  - 具体数值和排序尽量由图 4 或可选表 2 承担，正文只提炼结论。
- 中文图题：
  - 平凹腔与对称双凹腔的几何实现及 \(M=9\) 鲁棒分支比较。
- 英文图题：
  - Geometry realization and robust-branch comparison between plane-concave and symmetric double-concave cavities for \(M=9\).

## 图 5 径向寄生与卫星峰来源

- 文件：
  - `simulation/outputs/figures/fig05_oam_special_case_errors.png`
  - `simulation/outputs/figures/fig05_oam_special_case_errors.pdf`
- 数据源：
  - `simulation/outputs/data/radial_waist_mismatch_scan.csv`
  - `simulation/outputs/data/satellite_peak_degeneracy_examples.csv`
  - `simulation/outputs/data/oam_error_boundary_summary.json`
- 正文引用位置：
  - 第 5 节“OAM 序列、径向寄生与卫星峰来源”
- 功能：
  - 展示轴对称束腰失配下的径向泄漏分布。
  - 用相同 `N` 简并解释卫星峰来源。
  - OAM 序列特例和 `+l/-l` 简并由正文文字交代，不作为本图的主要可视化任务。
- 中文图题：
  - 径向寄生分量与卫星峰来源。
- 英文图题：
  - Radial parasitic components and the origin of satellite peaks.

## 图表检查项

- 每幅图的正文引用必须先讲物理问题，再指向图。
- 图 2 避免使用“严格分形”表述。
- 图 3 中 Airy 热图只是有限维串扰的可视化，不把“矩阵”写成新物理概念。
- 图 4 明确腔型不改变同一 `k_eff` 下的串扰性能，只改变几何回代和鲁棒性。
- 图 5 只承担径向泄漏和卫星峰示意，不承担 OAM 特例或 `+l/-l` 简并的概念图任务。
- 正文表格方案放在 `manuscript/section_scaffold.md` 第 4 节中维护；本文件只维护主图。
