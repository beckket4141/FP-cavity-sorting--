# 第五章表 1-5 推演结果说明

## 工作边界
- 仅写入当前目录：`D:\自制软件\1.thesis\My_nju_thesis-master\My_nju_thesis-master\验证推演3.15\腔实际性能参数验算\设计表推演`
- 未修改任何 `.tex`、图文件、control/canon、原始实验数据或既有结果文件
- 主线口径固定为 `0.88 / 原始数据分析结果`
- `0.98` 仅作为并行交叉校核

## 已生成文件
- `derive_ch05_tables.py`
- `table1_tau_lower_bound.csv`
- `table2_tau0_3_blueprint.csv`
- `table3_device_parameters.csv`
- `table4_peak_positions.csv`
- `table5_full_load_summary.csv`
- `table3_source_trace.csv`
- `table4_source_trace.csv`
- `table5_source_trace.csv`

## 表 1
- 用途：`tau=1..6` 的维度无关保守底线表，仅含 `ER_sum^(∞)` 与 `eta_sort^(∞)`
- 主来源：`ch05_fp_design_and_validation.tex`
- 收敛记录：
  - tau=1: closed_form=0.712688574960, partial_200000=0.712686074966, abs_diff=2.500e-06
  - tau=2: closed_form=0.197629012645, partial_200000=0.197628387647, abs_diff=6.250e-07
  - tau=3: closed_form=0.089757421029, partial_200000=0.089757143252, abs_diff=2.778e-07
  - tau=4: closed_form=0.050883355300, partial_200000=0.050883199050, abs_diff=1.562e-07
  - tau=5: closed_form=0.032684231493, partial_200000=0.032684131493, abs_diff=1.000e-07
  - tau=6: closed_form=0.022742592514, partial_200000=0.022742523070, abs_diff=6.944e-08

## 表 2
- 用途：固定 `tau0=3` 的连续满载设计蓝图
- 行范围：`N = 4, 9, 15, 30, 50, 100`
- `preferred_m` 规则：在互质解析分支中优先选 `(L/R)^*` 最接近 `0.5` 的分支；若并列取较小 `m`
- `ER_sum_pred`、`eta_sort_pred`、`I_pred` 均按固定维度、等先验、有限维均匀环模型计算

## 表 3
- 主来源：`outputs/0p88mm/原始数据分析结果/cavity_parameters_summary.csv`
- 校核来源：`fsr_estimates.csv`、`k_fit_summary.csv`、`0p98` 对应 summary
- `k`、`FSR`、`F` 为 headline；`L_eff`、`R_eff`、`(L/R)_eff` 仅作后置等效反演几何量

## 表 4
- 主来源：`outputs/0p88mm/原始数据分析结果/main_peak_positions_summary.csv`
- 校核来源：`outputs/final_theory_position_validation_comparison.csv`
- 复核结果：
  - `mean_abs_delta_pos (l=1..8) = 0.002882709885`
  - `rms_delta_pos (l=1..8) = 0.002958362296`
  - `max_abs_delta_pos (l=1..8) = 0.003719649518`
  - `worst_l = 2`
  - `closure_l9_abs_delta_pos = 0.002312743929`
- 待人工拍板：正文最终是否保留 `l=9` 作为主表行

## 表 5
- 主来源：`triplicate_full9_aggregate.xlsx` 与 `triplicate_transmittance_l0_8_stats.txt`
- 校核来源：`triplicate_full9_stats.txt`、`最终数据/1,2,3/full9_matrix_with_uncertainty.xlsx`、`最终数据/1,2,3/透射率.xlsx`、`测量方法.md`
- `±` 统一采用三次独立实验的 `SD`
- worst-case 指标按“通道三次 run 平均后再取最差通道”
- 摘要：
  - `\bar T = 88.564956 ± 0.458109 %`
  - `T_min = 83.959200 %`
  - `\bar\eta_sort = 93.257401 ± 0.474590 %`
  - `\eta_sort,min = 91.574759 %`
  - `\overline{ER_sum} = 11.486175 ± 0.346123 dB`
  - `ER_sum,min = 10.375229 dB`
  - `I(l;\hat l) = 2.656178 ± 0.036194 bits`
  - `I(l;\hat l)` combined-matrix cross-check = `2.651161` bits

## 旧文件边界
- 根目录旧汇总文件只能辅助参考，不能当唯一真值
- 未读取任何 `control/canon`
