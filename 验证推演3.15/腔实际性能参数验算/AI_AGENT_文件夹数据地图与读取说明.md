# AI Agent 文件夹数据地图与读取说明

本文档只做一件事：

**客观说明当前文件夹里有什么数据、这些数据分别是什么、如果想具体看某类数据应该去哪里找。**

本文档不负责：

* 预设任何外部使用场景的结构；
* 假设读者已经知道别处的口径约束；
* 把“当前默认工作口径”误写成“唯一最终真值”；
* 用外部任务覆盖文件夹本身的客观组织方式。

---

## 1. 这个文件夹里总体有什么

当前目录  
`D:\自制软件\1.thesis\My_nju_thesis-master\My_nju_thesis-master\验证推演3.15\腔实际性能参数验算`
下，数据大体分成两大块：

1. **晶体 FP 腔实际参数重算与主峰位置验证**
2. **满载叠加态输入实验的数据、去嵌入结果和绘图输出**

如果只想快速建立全局认识，可以把它理解成两条并列的数据链：

* 第一条链回答：FP 腔的实际 `FSR / F / k / L / L/R / R` 大致是多少，主峰位置是否贴近解析 `2/9` 分支。
* 第二条链回答：在 `l=0~8` 的 9 模满载输入下，去嵌入后的矩阵、`ER_sum`、`ER_pairmax`、对角占比和误差条分别是什么。

---

## 2. 顶层目录结构

当前根目录下最重要的项目有：

* [README.md](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/README.md)
  晶体腔参数重算链的说明。
* [面向aiagent的介绍性文档.md](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/面向aiagent的介绍性文档.md)
  说明四套重算结果、权威层级和历史遗留文件。
* [01_recalc_cavity_params.py](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/01_recalc_cavity_params.py)
  腔参数重算脚本。
* [02_validate_peak_positions_vs_theory.py](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/02_validate_peak_positions_vs_theory.py)
  主峰位置理论验证脚本。
* [outputs](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs)
  第一条数据链的全部输出。
* [光腰为0.88mm测得数据](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/光腰为0.88mm测得数据)
  `0.88 mm` 原始测量输入。
* [光腰为0.98mm测得数据](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/光腰为0.98mm测得数据)
  `0.98 mm` 原始测量输入。
* [满载叠加态输入数据](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据)
  第二条数据链的全部数据和图。

---

## 3. 第一条数据链：晶体 FP 腔实际参数重算

### 3.1 这条链的目标

这条链的目标是：

* 从扫腔数据中重提主峰；
* 在晶体腔口径下重算 `FSR`、`F`、`k`、`L`、`L/R`、`R`；
* 再单独验证主峰在一个 FSR 内的相对位置是否贴近解析 `2/9` 分支。

### 3.2 这条链的核心输入

原始输入来自两个目录：

* [光腰为0.88mm测得数据](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/光腰为0.88mm测得数据)
* [光腰为0.98mm测得数据](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/光腰为0.98mm测得数据)

脚本会同时处理：

* 原始数据
* FSR 补全后数据

所以最终得到四套独立结果。

### 3.3 这条链最重要的四个结果目录

后续如果想读“重算后的结果”，优先看下面四个目录：

* [outputs/0p88mm/原始数据分析结果](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p88mm/原始数据分析结果)
* [outputs/0p88mm/FSR补全分析结果](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p88mm/FSR补全分析结果)
* [outputs/0p98mm/原始数据分析结果](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p98mm/原始数据分析结果)
* [outputs/0p98mm/FSR补全分析结果](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p98mm/FSR补全分析结果)

### 3.4 每个结果目录里都有什么

每个结果目录里最常用的文件如下：

* `cavity_parameters_summary.csv`
  最终参数汇总。想看 `FSR / F / k / n / L / L/R / R` 就先读这个。
* `main_peak_positions_summary.csv`
  各主峰位置的汇总表。想看每个 `l` 的主峰波长、频率和被选中的主峰，就读这个。
* `peak_fit_summary.csv`
  所有候选峰和最终入选主峰的拟合审计表。想追溯“为什么选这个峰”时读这个。
* `fsr_estimates.csv`
  `FSR` 的方法 A、方法 B 和最终采用值的比较。
* `k_fit_summary.csv`
  `pos_meas / pos_fit / residual / m_l` 的拟合结果。
* `cross_source_comparison.csv`
  原始数据与补全数据之间的交叉比较。
* `theory_position_validation.csv`
  主峰位置相对解析 `2/9` 分支理论位置的逐点偏差。
* `theory_position_validation_summary.csv`
  上述位置偏差的 RMS、最大偏差等摘要。
* `theory_position_validation.png`
  主峰位置验证图。
* `report.md`
  当前文件夹内这一套结果的简要报告。
* `针对这个文件夹的数据的说法.md`
  用自然语言汇总这一套数据的结果说明。

### 3.5 如果你想看某一类问题，应该去哪

如果问题是“FP 腔的实际参数是多少”，去看：

* `cavity_parameters_summary.csv`

如果问题是“某个 `l` 的主峰是怎么选出来的”，去看：

* `peak_fit_summary.csv`
* `main_peak_positions_summary.csv`

如果问题是“理论 `2/9` 分支和实验位置差多少”，去看：

* `theory_position_validation.csv`
* `theory_position_validation_summary.csv`
* `theory_position_validation.png`

如果问题是“原始数据和补全后数据差多少”，去看：

* `cross_source_comparison.csv`

### 3.6 根目录下与这条链相关的总汇总文件

这条链在根目录 `outputs` 下还给出了一些跨四套结果的总汇总：

* [final_theory_position_validation_comparison.csv](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/final_theory_position_validation_comparison.csv)
  四套数据的主峰位置偏差总汇总表。
* [final_theory_position_validation_report.md](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/final_theory_position_validation_report.md)
  上述总汇总的文字版报告。
* [汇总这四个文件夹的全部数据的说法.md](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/汇总这四个文件夹的全部数据的说法.md)
  把四套结果统一放进同一套说法中的汇总说明。

### 3.7 这条链里哪些文件要小心

根目录里还有一些总汇总文件可能来自多轮重构后的历史产物：

* `final_report.md`
* `final_cavity_parameter_comparison.csv`

它们可以作为辅助参考，但**不能跳过四个权威子目录，直接把这两个文件当唯一真值来源。**

---

## 4. 第二条数据链：满载叠加态输入实验

### 4.1 这条链的目标

这条链的目标是：

* 对 `l=0~8` 的 9 模满载叠加态输入做实验测量；
* 构建检测端归一化标定矩阵；
* 用 NNLS 做去嵌入；
* 输出去嵌入后的满载矩阵、`ER_sum`、`ER_pairmax`、对角占比和误差条；
* 导出可直接使用的 PDF 图。

### 4.2 这条链的根目录

主目录是：

* [满载叠加态输入数据/最终数据](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/最终数据)

这个目录下面最重要的内容有：

* `1/`
* `2/`
* `3/`
  三次独立实验 run。
* `测量方法.md`
  整条链最重要的口径说明文件。
* `triplicate_full9_stats.txt`
  三次 run 合并后的摘要。
* `aggregate_triplicate_full9_matrix.csv`
  合并矩阵数据。
* `aggregate_transmittance_summary.csv`
  透射率汇总。
* `triplicate_transmittance_summary.csv`
  透射率摘要。
* `AI_Agent_RAG_System_Prompt.md`
  已有的 AI 检索路由说明。
* `绘图程序`
  绘图脚本及输出。

### 4.3 `测量方法.md` 里定义了什么

如果后续 agent 只读一个文件来理解这条链，优先读：

* [测量方法.md](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/最终数据/测量方法.md)

这个文件说明了：

* 实验目标和适用范围
* 符号定义
* `raw-SMF` 和 `de-embedded-FP` 两种口径
* 标定矩阵 `S_ij` 的定义
* 满载观测向量 `y^(j)` 的定义
* NNLS 去嵌入模型
* `ER_sum` 和 `ER_pairmax` 的定义
* Monte Carlo 不确定度传播方法
* 单次 run 和输出文件之间的对应关系

### 4.4 `1/2/3` 三个 run 目录里都有什么

每个 run 目录里常见文件如下：

* `final_matrix_summary.xlsx`
  原始统计矩阵汇总。
* `calib_matrix_with_uncertainty.xlsx`
  标定矩阵及其不确定度。
* `full9_matrix_with_uncertainty.xlsx`
  9 模去嵌入矩阵及其不确定度。
* `full4_matrix_with_uncertainty.xlsx`
  4 模去嵌入矩阵及其不确定度。不是每个 run 都一定有。
* `channel_snr_analysis.xlsx`
  各通道的 `ER_sum / ER_pairmax` 等指标分析表。
* `channel_snr_summary.txt`
  该 run 的文字摘要。
* `透射率.xlsx`
  透射率数据表。

### 4.5 如果你想看某一类问题，应该去哪

如果问题是“单次 run 的 `ER_sum` 和 `ER_pairmax` 是多少”，去看：

* `channel_snr_summary.txt`
* `channel_snr_analysis.xlsx`

如果问题是“9 模去嵌入矩阵长什么样”，去看：

* `full9_matrix_with_uncertainty.xlsx`

如果问题是“标定矩阵 `S_ij` 长什么样”，去看：

* `calib_matrix_with_uncertainty.xlsx`

如果问题是“透射率数据在哪里”，去看：

* `透射率.xlsx`
* `aggregate_transmittance_summary.csv`
* `triplicate_transmittance_summary.csv`

### 4.6 三次 run 合并后的核心摘要文件

如果问题不是看单次 run，而是想看合并结果，优先读：

* [triplicate_full9_stats.txt](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/最终数据/triplicate_full9_stats.txt)

这个文件给出：

* 每次 run 的快速摘要
* 三次合并后的逐通道 `ER_sum / ER_max / SignalShare`
* 三次合并后的总体均值和误差条

### 4.7 绘图程序和输出图

绘图脚本在：

* [绘图程序](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/最终数据/绘图程序)

主要脚本有：

* `满载百分比热图_含误差条.py`
* `ER理论实验对比图_含误差条.py`

输出图在：

* [绘图程序/输出图](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/最终数据/绘图程序/输出图)

其中包含多种误差条版本，例如：

* `9维满载百分比热图_含误差条_SD.pdf`
* `9维满载百分比热图_含误差条_SEM.pdf`
* `9维满载百分比热图_含误差条_CI95_t.pdf`
* `ER_sum理论实验对比_含误差条_SD.pdf`
* `ER_sum理论实验对比_含误差条_SEM.pdf`
* `ER_pairmax理论实验对比_含误差条_SD.pdf`

如果问题是“图是怎么来的”，先去看绘图脚本；
如果问题是“当前有哪些现成 PDF 图可以直接查看”，就去看 `输出图` 目录。

---

## 5. 当前最有用的总汇总

如果后续 agent 不想一下子读很多文件，当前最有用的总汇总可以按下面的方式理解。

### 5.1 腔参数四套结果总览

以下数值来自四个权威子目录中的 `cavity_parameters_summary.csv`。

| 数据集 | `FSR` / GHz | `F` | `k` | `L` / mm | `L/R` | `R` / mm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `0.88 / 原始` | 9.915475 | 32.085683 | 0.222682 | 10.398543 | 0.414598 | 25.081023 |
| `0.88 / FSR补全` | 9.938668 | 31.971669 | 0.222502 | 10.374279 | 0.414043 | 25.056058 |
| `0.98 / 原始` | 9.919383 | 32.311528 | 0.221895 | 10.394446 | 0.412164 | 25.219193 |
| `0.98 / FSR补全` | 9.919386 | 32.317937 | 0.221863 | 10.394442 | 0.412065 | 25.225244 |

这张表适合快速回答：

* 四套 cavity 参数重算结果大致在什么范围；
* `0.88` 和 `0.98` 两套数据彼此差多少；
* 原始数据和补全后数据差多少。

### 5.2 主峰位置验证总览

以下数值来自 [final_theory_position_validation_comparison.csv](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/final_theory_position_validation_comparison.csv) 中 `measurement_type=merged` 的四行。

| 数据集 | RMS 偏差 / %FSR | 最大偏差 / %FSR | 最坏通道 |
| --- | ---: | ---: | ---: |
| `0.88 / FSR补全` | 0.2136 | 0.3322 | `l=5` |
| `0.88 / 原始` | 0.2894 | 0.3720 | `l=2` |
| `0.98 / FSR补全` | 0.2215 | 0.4407 | `l=8` |
| `0.98 / 原始` | 0.2040 | 0.3566 | `l=8` |

这张表适合快速回答：

* 四套结果和解析 `2/9` 分支的位置偏差分别有多大；
* 哪一套数据的 RMS 更小；
* 最大偏差落在哪个 `l`。

### 5.3 三次满载实验合并结果总览

以下结果来自 [triplicate_full9_stats.txt](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/最终数据/triplicate_full9_stats.txt)。

单次 run 快速摘要：

* Run 1：`cond(S)=5.0532`，`ER_sum mean=11.625 dB`，`ER_max mean=16.307 dB`，对角占比均值 `93.51%`
* Run 2：`cond(S)=4.9916`，`ER_sum mean=11.741 dB`，`ER_max mean=16.665 dB`，对角占比均值 `93.56%`
* Run 3：`cond(S)=5.4326`，`ER_sum mean=11.092 dB`，`ER_max mean=16.317 dB`，对角占比均值 `92.71%`

三次合并后的总体结果：

* `ER_sum mean ± errorbar95 = 11.486 ± 0.344 dB`
* `ER_max mean ± errorbar95 = 16.429 ± 0.354 dB`
* 对角占比均值 `93.26%`，范围 `[91.57%, 94.88%]`

这部分适合快速回答：

* 三次实验是否稳定；
* 合并后的总体 `ER_sum` 和 `ER_max` 在什么量级；
* 去嵌入矩阵的对角占比在什么范围。

---

## 6. 最简读取路线

如果后续 agent 时间很少，只想最快知道“这里的数据长什么样”，建议按下面顺序读。

### 6.1 想先理解整个文件夹

按顺序读：

1. 本文件
2. [面向aiagent的介绍性文档.md](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/面向aiagent的介绍性文档.md)
3. [测量方法.md](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/最终数据/测量方法.md)

### 6.2 想先看 cavity 参数

按顺序读：

1. 四个子目录中的 `cavity_parameters_summary.csv`
2. `final_theory_position_validation_comparison.csv`
3. `汇总这四个文件夹的全部数据的说法.md`

### 6.3 想先看满载矩阵和 ER

按顺序读：

1. `测量方法.md`
2. `triplicate_full9_stats.txt`
3. 单次 run 的 `channel_snr_summary.txt`
4. `绘图程序/输出图`

---

## 7. 这份文档的使用边界

本文档只负责回答：

* 这个文件夹里有哪些数据；
* 哪些文件适合看哪类问题；
* 当前有哪些全局汇总可以快速建立认识。

如果后续需要：

* 逐单元矩阵值；
* 某个 `l` 的具体主峰拟合过程；
* 某次 run 的逐通道误差条；
* 某张图的绘制细节；

则必须继续下钻到相应的 CSV、XLSX、TXT 或脚本文件，而不能只停留在本总览。

---

## 6. 2026-03-25 修正补充

本目录下与腔参数重算有关的 `k` 口径已更新：

* `k_relative_fit`：以 `l=0` 为参考，只用 `l=1..8` 锁定工作点；
* `l=9`：不再参与工作点反演，只作为留出的闭合检验；
* `k_joint_method_B`：保留为全模审计值，用于交叉核对，不再作为“`l=9` 独立验证”口径；
* `k_fit_summary.csv` 与 `main_peak_positions_summary.csv`：现已显式写出 `reference / anchor / holdout` 角色。

如果后续 agent 需要判断“某个 `k` 数值到底是怎么来的”，优先读：

* `cavity_parameters_summary.csv`
* `k_fit_summary.csv`
* `main_peak_positions_summary.csv`
