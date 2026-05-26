# NNLS零值与误差条推演报告

本文档基于 `D:\自制软件\1.thesis\Data\full` 中的最终 9 模数据，对 corrected matrix 中的零值、误差条口径、raw/corrected 差异和保守 floor 稳健性做一次可追溯推演。配套脚本与完整表格位于同目录：

- `full9_robustness_audit.py`
- `full9_robustness_audit.xlsx`
- `full9_robustness_audit_summary.md`

参考了大论文附录 `appendices/app_e5_calibration_robustness.tex` 中关于检测端响应矩阵校正、三次独立测量和统计不确定度的说明。

## 1. 主要结论

1. corrected matrix 中的 7 个非对角 0 值可以由逐 run 重跑 NNLS 复现。raw detector-side 读数并不为 0；对应 unconstrained LS 分量为小负值，NNLS 在非负约束下将其压到边界。
2. 三次响应矩阵条件数分别为 5.05、4.99、5.43，平均 5.16，属于适度良态；重新计算的 NNLS 解与源文件 corrected matrix 最大绝对差为 \(4.93\times10^{-10}\,\mathrm{W}\)。
3. 对 0 值施加保守 leakage floor 后，ER 结论稳定。即使把所有非对角 0 替换成 0.1%，mean \(ER_{\mathrm{sum}}\) 只下降约 0.05 dB；替换成 0.2% 时下降约 0.10 dB。
4. 当前脚本中 `1.96*SEM` 不宜严格称为 95% CI。若使用三次独立测量的 95% t 区间，误差条应乘以 \(t_{0.975,2}=4.303\)，约为当前 `1.96*SEM` 的 2.20 倍。
5. 更稳妥的图注/正文口径是：`mean ± SD from three independent measurements`，与大论文附录 E5 已写的“标准差作为统计不确定度”一致。若保留现有误差条，则应明确写成 `mean ± 1.96 SEM`，不要写成严格 95% CI。

## 2. NNLS 零值来源

combined corrected matrix 中的 7 个 0：

| position | raw pct per run | unconstrained LS \(x\) per run | NNLS \(x\) per run |
|---|---:|---:|---:|
| ch3, lock1 | 0.0762%, 0.0635%, 0.0367% | -1.002e-08, -1.355e-08, -1.586e-08 W | 0, 0, 0 |
| ch4, lock2 | 0.0726%, 0.0757%, 0.0622% | -2.324e-08, -2.703e-08, -2.726e-08 W | 0, 0, 0 |
| ch5, lock3 | 0.1002%, 0.0878%, 0.0476% | -3.757e-08, -5.112e-08, -5.039e-08 W | 0, 0, 0 |
| ch6, lock4 | 0.1116%, 0.1962%, 0.1207% | -6.922e-08, -6.721e-08, -7.256e-08 W | 0, 0, 0 |
| ch7, lock5 | 0.3007%, 0.3678%, 0.3420% | -6.764e-08, -6.463e-08, -5.977e-08 W | 0, 0, 0 |
| ch7, lock8 | 0.3275%, 0.9485%, 0.1667% | -1.836e-07, -2.481e-07, -4.305e-08 W | 0, 0, 0 |
| ch8, lock6 | 0.5932%, 0.6106%, 0.5256% | -6.934e-08, -7.657e-08, -7.988e-08 W | 0, 0, 0 |

判断：这些位置不是“测得串扰严格为零”，而是 \(Sx=y\) 反演中的非负边界解。raw \(y_i\) 为非零，说明探测端确实有读数；但在扣除 readout response 的交叉响应后，最小二乘意义下该物理分量落到小负值。NNLS 把小负值投影到 \(x_i=0\)，这是符合非负功率先验的边界估计。

补充材料中建议避免把这些 0 解释为物理上完全无串扰，可写成 “entries estimated at the non-negativity boundary” 或 “below the resolvable level after response de-embedding”。

## 3. Floor sensitivity

基于 combined corrected percentage matrix，对所有非对角 0 值替换为统一 floor 后重算 \(ER_{\mathrm{sum}}\)：

| floor | mean \(ER_{\mathrm{sum}}\) | min \(ER_{\mathrm{sum}}\) | mean drop |
|---:|---:|---:|---:|
| 最小非零 off-diagonal = 0.0297% | 11.3821 dB | 10.6523 dB | -0.0150 dB |
| 0.01% | 11.3921 dB | 10.6523 dB | -0.0051 dB |
| 0.05% | 11.3719 dB | 10.6523 dB | -0.0252 dB |
| 0.10% | 11.3469 dB | 10.6523 dB | -0.0502 dB |
| 0.20% | 11.2975 dB | 10.6417 dB | -0.0997 dB |

判断：即使采取偏保守的 0.1% 或 0.2% leakage floor，ER 变化仍远小于 run-to-run 误差条量级，不改变 9 模满载分选性能结论。注意这里的 mean ER 来自 combined percentage matrix 直接重算，因此与 `ER_summary` 中“先逐 run 算 ER 再取均值”的 11.405 dB 有约 0.01 dB 的微小口径差异。

## 4. Raw / response / corrected 对照

| \(l\) | raw diag | \(S_{ll}\) | corrected diag | corrected \(ER_{\mathrm{sum}}\) |
|---:|---:|---:|---:|---:|
| 0 | 94.1673% | 10.9971% | 94.0681% | 12.0025 dB |
| 1 | 97.1547% | 19.4892% | 94.4110% | 12.2768 dB |
| 2 | 96.3821% | 17.5364% | 94.2853% | 12.1745 dB |
| 3 | 94.8659% | 14.7849% | 93.4893% | 11.5713 dB |
| 4 | 92.2693% | 11.4964% | 92.8815% | 11.1554 dB |
| 5 | 86.9946% | 9.0980% | 92.7177% | 11.0489 dB |
| 6 | 81.8796% | 7.0749% | 92.2427% | 10.7522 dB |
| 7 | 79.5755% | 5.3864% | 92.0764% | 10.6523 dB |
| 8 | 76.8168% | 3.7927% | 92.5470% | 10.9403 dB |

判断：raw diagonal 的高低主要混合了 readout arm 的模式依赖响应，不能直接解释为 FP cavity 输出强弱。特别是 \(l=1\) raw diagonal 最大，与 \(S_{11}\) 最大一致；高 \(l\) raw diagonal 下降也与 \(S_{ll}\) 下降一致。corrected matrix 的作用正是把这部分检测端响应剥离。

## 5. Errorbar 口径

### Fig. 5(c) ER

| \(l\) | mean ER | SD | SEM | 1.96 SEM | t95 SEM |
|---:|---:|---:|---:|---:|---:|
| 0 | 12.0148 | 0.4243 | 0.2450 | 0.4802 | 1.0541 |
| 1 | 12.2787 | 0.1643 | 0.0949 | 0.1860 | 0.4082 |
| 2 | 12.1768 | 0.1839 | 0.1062 | 0.2081 | 0.4568 |
| 3 | 11.5758 | 0.2600 | 0.1501 | 0.2942 | 0.6458 |
| 4 | 11.1600 | 0.2626 | 0.1516 | 0.2971 | 0.6523 |
| 5 | 11.0628 | 0.4566 | 0.2636 | 0.5167 | 1.1343 |
| 6 | 10.7673 | 0.4846 | 0.2798 | 0.5484 | 1.2038 |
| 7 | 10.6629 | 0.4068 | 0.2349 | 0.4603 | 1.0106 |
| 8 | 10.9468 | 0.3153 | 0.1821 | 0.3568 | 0.7833 |

### Fig. 5(d) Transmittance

| \(l\) | mean trans. | SD | SEM | 1.96 SEM | t95 SEM |
|---:|---:|---:|---:|---:|---:|
| 0 | 92.8928% | 0.7105% | 0.4102% | 0.8041% | 1.7651% |
| 1 | 91.6597% | 0.9309% | 0.5375% | 1.0535% | 2.3126% |
| 2 | 90.4994% | 1.0776% | 0.6221% | 1.2194% | 2.6769% |
| 3 | 88.8197% | 1.8507% | 1.0685% | 2.0943% | 4.5974% |
| 4 | 88.5996% | 2.5189% | 1.4543% | 2.8504% | 6.2572% |
| 5 | 86.5429% | 2.2577% | 1.3035% | 2.5549% | 5.6085% |
| 6 | 85.1426% | 3.2250% | 1.8620% | 3.6495% | 8.0114% |
| 7 | 82.6473% | 2.5499% | 1.4722% | 2.8854% | 6.3342% |
| 8 | 82.7064% | 2.4165% | 1.3951% | 2.7345% | 6.0028% |

推荐：正文图注和表格优先统一为 `mean ± SD from three independent measurements`。如果图中已经画的是 `1.96 SEM`，则图注必须明确写 `mean ± 1.96 SEM`，不要写 `95% CI`。如果确实要写 95% CI，应按 t 分布重画，误差条约为当前 `1.96 SEM` 的 2.20 倍。

## 6. High-\(l\) readout SNR 判断

现有数据能支持两点：

1. \(S_{88}=3.79\%\) 确实说明高阶检测端响应较弱，但三次响应矩阵条件数仍约 5，反演不是病态问题。
2. `channel_snr_summary.txt` 中每次 run 的 corrected \(ER_{\mathrm{sum}}\) 最低值仍在 10.3 dB 以上，run-to-run 变化可由独立重复测量量化。

现有数据暂不能严格完成 detector dark noise / background floor 层面的绝对 SNR 证明，因为未看到独立的 power meter 暗噪声、background-only measurement 或 calibration uncertainty budget。若审稿人追问“低 \(S_{88}\) 是否接近仪器噪声底”，需要补实验噪声数据或在回复中限定为“基于重复测量与响应矩阵条件数的数值稳健性检查”。

## 7. 可用于 supplement 的英文说明

The response correction was performed by solving \(Sx=y\), where \(y\) is the detector-side raw projection vector and \(S\) is the independently measured projection-arm response matrix. For each of the three independent runs, we re-solved the system using both unconstrained least squares and non-negative least squares. The off-diagonal zero entries in the corrected matrix are not raw measured zeros. The corresponding raw detector readings are finite, while the unconstrained least-squares estimates are small negative values; NNLS therefore places these components at the non-negativity boundary. These entries should be interpreted as boundary estimates below the resolvable level after response de-embedding, rather than as strictly zero physical crosstalk.

The three response matrices have moderate condition numbers of 5.05, 4.99, and 5.43. As a conservative sensitivity test, we replaced the zero off-diagonal entries by finite leakage floors. A 0.1% floor changes the mean \(ER_{\mathrm{sum}}\) by only about 0.05 dB, and even a 0.2% floor changes it by about 0.10 dB. The full-load sorting conclusion is therefore insensitive to the boundary-zero entries introduced by NNLS.

## 8. 可用于 rebuttal 的英文短段

The raw projection matrix includes the projection-arm response and therefore should not be interpreted as the cavity sorting matrix directly. We independently measured the response matrix \(S\) in each run and used NNLS to solve \(Sx=y\) under the physical non-negativity constraint. The zero entries after correction are NNLS boundary estimates: the raw detector powers at these positions are non-zero, but the unconstrained least-squares solution assigns small negative components, which are projected to zero by NNLS. The response matrices are moderately conditioned, and applying conservative leakage floors to the zero entries changes the mean \(ER_{\mathrm{sum}}\) by less than 0.1 dB for floors up to 0.2%. Thus the reported sorting performance does not rely on treating those entries as physically exact zeros.

