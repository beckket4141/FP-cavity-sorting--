# 晶体 FP 腔扫腔数据复算说明

本目录只在本地新增或修改 `.py`、`.md` 和 `outputs/` 下的结果文件，不修改任何原始 CSV，也不修改仓库其他位置。

## 当前脚本

- `01_recalc_cavity_params.py`
  重新从扫腔曲线提主峰，分别对 `0.88 mm` 和 `0.98 mm` 的原始数据、FSR 补全后数据做四套独立验算。
- `02_validate_peak_positions_vs_theory.py`
  额外验证各主峰在 FSR 归一化空间内与解析 `2/9` 分支理论位置的偏差。
- `cavity_recalc_common.py`
  通用函数，负责数据发现、峰提取、Lorentz 拟合、FSR 和 `k` 拟合、折射率、参数反推、导图导表等。

## 四套独立分析结果

`01_recalc_cavity_params.py` 会生成四个独立分析目录：

- `outputs/0p88mm/原始数据分析结果/`
- `outputs/0p88mm/FSR补全分析结果/`
- `outputs/0p98mm/原始数据分析结果/`
- `outputs/0p98mm/FSR补全分析结果/`

每套都独立完成：

- 主峰提取与局部 Lorentz 拟合
- 主峰位置汇总
- FSR 方法 A 与方法 B
- `k` 拟合
- 熔融石英折射率计算
- `L`、`L/R`、`R` 反推
- 与另一数据源的交叉验证

## 数据口径

两类数据都可以作为“主分析输入”：

- `原始数据/*.csv`
- `FSR补全后数据/*_final.csv`

补全后主峰验证表只作为 sanity check，不直接当真值输入。

文件名自动识别，不写死某一种模式；兼容：

- `DATA70_l0_symmetrized.csv`
- `DATA70_l0_symmetrized_l0_final.csv`
- `l=0_symmetrized.csv`
- `l=0_symmetrized_final.csv`

统一列名要求：

- `Time_ms`
- `Lambda_aligned`
- `Power_uW`
- `Scan_Direction`

## 物理模型

按晶体腔而不是空气腔处理：

- `FSR_nu = c / (2 n L)`
- `phi = arccos(sqrt(1 - L/R))`
- `k = phi / pi`
- `L/R = sin^2(pi k)`
- `R = L / (L/R)`

峰心提取采用局部 Lorentz 拟合，而不是直接用最大功率点充当峰心。

## FSR、k、F 的采用规则

- `FSR`
  - 方法 A：直接由 `l=0` 中两个纵模 TEM00 主峰频差得到
  - 方法 B：由 `nu_l = nu_ref + (m_l + l*k) * FSR` 做全局拟合
  - 若方法 A 的 Rising/Falling 结果在 1% 内一致，则优先采用方法 A
  - 否则切换到方法 B
- `k`
  - 采用 `pos_meas = ((nu_l - nu_0)/FSR) mod 1`
  - 以 `l=0` 为参考，只用 `l=1..8` 锁定工作点 `pos_fit = (l*k) mod 1`
  - `l=9` 不再参与工作点反演，只作为留出的闭合检验
- `F`
  - 逐峰输出 `F = FSR / FWHM`
  - 最终推荐值默认采用 `l=0` 基模主峰
  - 同时给出全部主峰的加权平均作为交叉验证

## 折射率模型

实现了两个折射率函数：

- `malitson_index_20c(lambda_um)`
- `fused_silica_index(lambda_um, temp_c)`

采用说明：

- 室温基线：Malitson, JOSA 55, 1205 (1965)
- 温度相关模型：Leviton & Frey, Proc. SPIE 6273 (2006) / NASA 收录版本

显式输出：

- `n(20.00 °C)`
- `n(20.18 °C)`
- `Δn = n(20.18 °C) - n(20.00 °C)`
- `n_sellmeier(20 °C) - n_Malitson(20 °C)`

## 01 脚本输出

每个分析子目录下包含：

- `peak_fit_summary.csv`
- `fsr_estimates.csv`
- `k_fit_summary.csv`
- `cavity_parameters_summary.csv`
- `selected_peak_summary.csv`
- `main_peak_positions_summary.csv`
- `cross_source_comparison.csv`
- `peak_fits_overview.png`
- `position_fit.png`
- `report.md`

总汇总输出：

- `outputs/final_cavity_parameter_comparison.csv`
- `outputs/final_report.md`

## 新增：解析 2/9 分支主峰位置验证

`02_validate_peak_positions_vs_theory.py` 不再反推 `L`、`R` 或精细度，只验证主峰在归一化 FSR 空间中的相对位置是否贴近九维连续满载的解析 `2/9` 分支。

采用口径：

- 理论步长固定为 `k_th = 2/9`
- 对应几何比 `L/R_th = sin^2(pi * 2/9) ≈ 0.413176`
- 实测位置定义为 `pos_meas = ((nu_l - nu_0)/FSR_final) mod 1`
- 理论位置定义为 `pos_th = (l * 2/9) mod 1`
- 偏差采用圆周上的最短距离：
  `delta_pos = ((pos_meas - pos_th + 0.5) mod 1) - 0.5`

因此这个验证与精细度 `F` 无关，只和主峰相对位置及选用的归一化 FSR 有关。

每个分析子目录新增：

- `theory_position_validation.csv`
- `theory_position_validation_summary.csv`
- `theory_position_validation.png`
- `theory_position_validation.md`

总目录新增：

- `outputs/final_theory_position_validation_comparison.csv`
- `outputs/final_theory_position_validation_report.md`

## 运行方法

在本目录执行：

```powershell
python 01_recalc_cavity_params.py
python 02_validate_peak_positions_vs_theory.py
```

依赖：

- `numpy`
- `pandas`
- `scipy`
- `matplotlib`

## 说明

- 当前 `L`、`R` 的误差传播只显式包含 `FSR` 与 `k` 的不确定度，没有再单独并入折射率模型本身的系统误差。
- `0.98 mm` 数据里，`l=0` 的 Rising/Falling 有时会落在不同纵模折返上，所以合并时允许按整数个 FSR 对齐。
- 图里若出现中文字体警告，不影响数值结果和 CSV 输出。

## 2026-03-25 修正说明

- `k_relative_fit` 现统一改为“以 `l=0` 为参考、由 `l=1..8` 锁定工作点、将 `l=9` 留作闭合检验”的口径。
- `k_fit_summary.csv` 与 `main_peak_positions_summary.csv` 现已显式标出 `reference / anchor / holdout` 角色，避免再把 `l=9` 当作参与工作点反演的样本。
- `k_relative_fit_err` 与 `k_joint_method_B_err` 不再使用旧版“整段搜索窗宽度”伪误差，而改为局部低分带宽与方向散布主导的口径。
- `k_joint_method_B` 仍保留为全模 Method B 审计值，用于和工作点口径交叉核对，但不再作为 `l=9` 独立验证的表述依据。
