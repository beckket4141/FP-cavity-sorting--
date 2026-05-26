# 数据溯源速查表

本表用于返修时快速定位关键数值、来源文件、生成脚本和适用 issue。默认数据源为 `D:\自制软件\1.thesis\Data\full`。

## 核心实验数值

| 关键数值 | 值 | 来源文件 | sheet / 行 | 生成脚本 | 用于 issue |
|---|---:|---|---|---|---|
| combined diagonal share mean | 93.190768% | `triplicate_full9_aggregate.xlsx` | `overall_stats` / `combined_diag_share_mean_%` | `aggregate_triplicate_full9.py` | A, C, F |
| combined diagonal share min | 92.075145% | `triplicate_full9_aggregate.xlsx` | `overall_stats` / `combined_diag_share_min_%` | `aggregate_triplicate_full9.py` | E, F |
| combined diagonal share max | 94.410181% | `triplicate_full9_aggregate.xlsx` | `overall_stats` / `combined_diag_share_max_%` | `aggregate_triplicate_full9.py` | C, F |
| mean \(ER_{\mathrm{sum}}\) across all channels/runs | 11.405086 dB | `triplicate_full9_aggregate.xlsx` | `overall_stats` / `ER_sum_all_mean_dB` | `aggregate_triplicate_full9.py` | B, F |
| overall \(ER_{\mathrm{sum}}\) `1.96 SEM` | 0.250695 dB | `triplicate_full9_aggregate.xlsx` | `overall_stats` / `ER_sum_all_errorbar95_dB` | `aggregate_triplicate_full9.py` | B |
| min channel \(ER_{\mathrm{sum}}\) | 10.662879 dB at \(l=7\) | `triplicate_full9_aggregate.xlsx` | `ER_summary` / row `channel=7` | `aggregate_triplicate_full9.py` | E, F |
| \(l=8\) \(ER_{\mathrm{sum}}\) | 10.946809 dB | `triplicate_full9_aggregate.xlsx` | `ER_summary` / row `channel=8` | `aggregate_triplicate_full9.py` | E |
| raw \(l=1\) diagonal | 97.154702% | `triplicate_full9_raw_aggregate.xlsx` | `combined_raw_percentage` / `ch=1, lock=1` | `aggregate_triplicate_full9.py` | C |
| raw \(l=8\) diagonal | 76.8168% | `triplicate_full9_raw_aggregate.xlsx` | `combined_raw_percentage` / `ch=8, lock=8` | `aggregate_triplicate_full9.py` | C, D |
| corrected \(l=8\) diagonal | 92.547061% | `triplicate_full9_aggregate.xlsx` | `combined_percentage` / `ch=8, lock=8` | `aggregate_triplicate_full9.py` | C, D |

## Response matrix 与 NNLS 审计

| 关键数值 | 值 | 来源文件 | sheet / 行 | 生成脚本 | 用于 issue |
|---|---:|---|---|---|---|
| \(S_{00}\) | 10.997074% | `triplicate_full9_calib_matrix_heatmap.xlsx` | `combined_calib_S_percent` / `ch=0, lock=0` | `aggregate_triplicate_full9.py` | C |
| \(S_{11}\) | 19.489237% | `triplicate_full9_calib_matrix_heatmap.xlsx` | `combined_calib_S_percent` / `ch=1, lock=1` | `aggregate_triplicate_full9.py` | C |
| \(S_{88}\) | 3.792727% | `triplicate_full9_calib_matrix_heatmap.xlsx` | `summary` / `combined_diag_min_%`; also `combined_calib_S_percent` | `aggregate_triplicate_full9.py` | D |
| calibration off-diagonal max | 0.167137% | `triplicate_full9_calib_matrix_heatmap.xlsx` | `summary` / `combined_offdiag_max_%` | `aggregate_triplicate_full9.py` | C, D |
| condition numbers run 1/2/3 | 5.05 / 4.99 / 5.43 | `full9_robustness_audit.xlsx` | `condition_numbers` | `full9_robustness_audit.py` | A, C, D |
| mean condition number | 5.16 | `full9_robustness_audit_summary.md` | `Key computed facts` | `full9_robustness_audit.py` | A, C, D |
| NNLS reproduction max abs diff | \(4.93\times10^{-10}\) W | `full9_robustness_audit.xlsx` | `nnls_reproduction` | `full9_robustness_audit.py` | A |
| smallest non-zero corrected off-diagonal | 0.0297% | `full9_robustness_audit_summary.md` | `Key computed facts` | `full9_robustness_audit.py` | A |

## Seven NNLS zero positions

| zero position | raw pct per run | LS values per run | NNLS values | 来源文件 | sheet | 生成脚本 | 用于 issue |
|---|---|---|---|---|---|---|---|
| ch3, lock1 | 0.0762%, 0.0635%, 0.0367% | -1.002e-08, -1.355e-08, -1.586e-08 W | 0,0,0 | `full9_robustness_audit.xlsx` | `nnls_zero_trace` | `full9_robustness_audit.py` | A |
| ch4, lock2 | 0.0726%, 0.0757%, 0.0622% | -2.324e-08, -2.703e-08, -2.726e-08 W | 0,0,0 | `full9_robustness_audit.xlsx` | `nnls_zero_trace` | `full9_robustness_audit.py` | A |
| ch5, lock3 | 0.1002%, 0.0878%, 0.0476% | -3.757e-08, -5.112e-08, -5.039e-08 W | 0,0,0 | `full9_robustness_audit.xlsx` | `nnls_zero_trace` | `full9_robustness_audit.py` | A |
| ch6, lock4 | 0.1116%, 0.1962%, 0.1207% | -6.922e-08, -6.721e-08, -7.256e-08 W | 0,0,0 | `full9_robustness_audit.xlsx` | `nnls_zero_trace` | `full9_robustness_audit.py` | A |
| ch7, lock5 | 0.3007%, 0.3678%, 0.3420% | -6.764e-08, -6.463e-08, -5.977e-08 W | 0,0,0 | `full9_robustness_audit.xlsx` | `nnls_zero_trace` | `full9_robustness_audit.py` | A |
| ch7, lock8 | 0.3275%, 0.9485%, 0.1667% | -1.836e-07, -2.481e-07, -4.305e-08 W | 0,0,0 | `full9_robustness_audit.xlsx` | `nnls_zero_trace` | `full9_robustness_audit.py` | A |
| ch8, lock6 | 0.5932%, 0.6106%, 0.5256% | -6.934e-08, -7.657e-08, -7.988e-08 W | 0,0,0 | `full9_robustness_audit.xlsx` | `nnls_zero_trace` | `full9_robustness_audit.py` | A |

## Floor sensitivity

| floor | mean \(ER_{\mathrm{sum}}\) | min \(ER_{\mathrm{sum}}\) | mean drop | 来源文件 | sheet | 生成脚本 | 用于 issue |
|---:|---:|---:|---:|---|---|---|---|
| 0.0297% | 11.3821 dB | 10.6523 dB | -0.0150 dB | `full9_robustness_audit.xlsx` | `floor_sensitivity` | `full9_robustness_audit.py` | A |
| 0.10% | 11.3469 dB | 10.6523 dB | -0.0502 dB | `full9_robustness_audit.xlsx` | `floor_sensitivity` | `full9_robustness_audit.py` | A |
| 0.20% | 11.2975 dB | 10.6417 dB | -0.0997 dB | `full9_robustness_audit.xlsx` | `floor_sensitivity` | `full9_robustness_audit.py` | A |

## Errorbar 与 transmittance

| 关键数值 | 值 | 来源文件 | sheet / 行 | 生成脚本 | 用于 issue |
|---|---:|---|---|---|---|
| t factor for \(n=3\) 95% CI | \(t_{0.975,2}=4.303\) | `full9_robustness_audit.py` | constant `T95_DF2` | `full9_robustness_audit.py` | B |
| \(l=7\) ER 1.96 SEM | 0.4603 dB | `full9_robustness_audit.xlsx` | `ER_errorbar_compare` | `full9_robustness_audit.py` | B, E |
| \(l=7\) ER t95 SEM | 1.0106 dB | `full9_robustness_audit.xlsx` | `ER_errorbar_compare` | `full9_robustness_audit.py` | B |
| transmittance \(l=0\) | 92.8928% ± 0.7105% SD | `triplicate_transmittance_l0_8_stats.txt` | `l=0` line | `aggregate_transmittance_l0_8.py`; parsed by `full9_robustness_audit.py` | B, D |
| transmittance \(l=7\) | 82.6473% ± 2.5499% SD | `triplicate_transmittance_l0_8_stats.txt` | `l=7` line | `aggregate_transmittance_l0_8.py`; parsed by `full9_robustness_audit.py` | B, D, E |
| transmittance \(l=8\) | 82.7064% ± 2.4165% SD | `triplicate_transmittance_l0_8_stats.txt` | `l=8` line | `aggregate_transmittance_l0_8.py`; parsed by `full9_robustness_audit.py` | B, D, E |

## 理论阈值与参考线

| 关键数值 | 值 | 来源文件 | 位置 | 生成脚本 | 用于 issue |
|---|---:|---|---|---|---|
| \(\tau_0\) | 3 | `main.tex` | design criterion / Table `oe_tau_bounds` | manuscript analytical derivation | F |
| conservative \(\eta_{\mathrm{sort}}^{(\infty)}\) | 91.76% | `main.tex` | Table `oe_tau_bounds`, text near \(\tau_0=3\) | manuscript analytical derivation | F |
| conservative \(ER_{\mathrm{sum}}^{(\infty)}\) lower bound | 10.47 dB | `main.tex` | Table `oe_tau_bounds`, Fig. 5(c) text | manuscript analytical derivation | F |
| exact finite-\(M\) Airy reference | 12.04 dB | `main.tex` | Fig. 5(c) text | manuscript analytical derivation / measured finesse | F, E |
| \(M=9\) threshold finesse at \(\tau_0=3\) | \(\mathcal{F}_{\min}=27\) | `main.tex`, `supplement.tex` | design/tolerance discussion | manuscript analytical derivation | F |

## 前人 FP-OAM sorter 定位依据

| 关键依据 | 内容 | 来源文件 | 位置 | 生成脚本 | 用于 issue |
|---|---|---|---|---|---|
| Wei et al. title | "Active sorting of orbital angular momentum states of light with a cascaded tunable resonator" | `oe_paper/范文/参考文献/_pdf_text_clean/1.FP腔OAM主动分选与级联谐振器.txt` | title lines | PDF text extraction | G |
| modular sorter architecture | Each module accepts multiple OAM states, outputs one state, and diverts others unaltered for subsequent processing | same | Results / modular process | PDF text extraction | G |
| cascaded resonator sorter | Multiport OAM sorter is constructed by cascading tunable resonators | same | Abstract and Fig. 1/Fig. 3 descriptions | PDF text extraction | G |
| predecessor degeneracy statement | Opposite topological charges are degenerate in a single FP cavity because resonance depends on \(|l|\) | same | Modular design of an OAM sorter | PDF text extraction | H |
