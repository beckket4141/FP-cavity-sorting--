# 面向 AI Agent 的介绍性文档

本文档面向后续进入目录
`D:\自制软件\1.thesis\My_nju_thesis-master\My_nju_thesis-master\验证推演3.15\腔实际性能参数验算`
工作的 AI agent。

目标是让 agent 能快速理解：

- 这个目录里已经完成了哪些推演、验算和验证
- 各脚本的职责和输出文件应该去哪里找
- 哪些结果是权威结果，哪些是历史遗留文件
- 后续如果要写论文、做答辩图、引用最终数值，默认该选哪套数据

## 1. 工作边界

本轮工作严格只在当前目录内新增或修改：

- `.py`
- `.md`
- `outputs/` 下的结果文件

没有修改：

- 原始 CSV 数据
- thesis 正文
- 仓库其他目录

## 2. 已完成的工作总览

截至目前，这个目录内完成了两大类工作。

### 2.1 晶体 FP 腔实际参数重算

已分别对两套数据、两种数据源做了四套独立分析：

1. `0.88 mm / 原始数据`
2. `0.88 mm / FSR补全后数据`
3. `0.98 mm / 原始数据`
4. `0.98 mm / FSR补全后数据`

每套都独立完成了：

- 主峰重新提取
- Rising / Falling 分开处理
- 主峰局部 Lorentz 拟合
- FWHM 与实验精细度计算
- FSR 两种方法估计
- `k` 拟合
- 熔融石英折射率 `n(795 nm, 20.18 °C)` 计算
- 由 `FSR` 反推 `L`
- 由 `k` 反推 `L/R`
- 由 `L` 和 `L/R` 反推 `R`
- 原始数据与 FSR 补全后数据的交叉验证

### 2.2 主峰位置与解析 2/9 分支理论对比

新增了独立验证：

- 不再拿正文名义 `L=10.25 mm`、`R=25 mm` 当先验输入
- 理论只采用九维连续满载解析分支 `k_th = 2/9`
- 只比较一个 FSR 内归一化主峰位置 `pos`
- 不依赖精细度 `F`

对上述四个分析文件夹都单独做了：

- 主峰位置理论对比表
- 可视化图
- 单独“说法”文件

## 3. 核心脚本说明

### 3.1 `[cavity_recalc_common.py](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/cavity_recalc_common.py)`

通用函数库，负责：

- 数据集自动发现
- CSV 读取与列校验
- 波长转频率
- 候选峰搜索
- Lorentz 拟合
- 主分支选择
- 直接 FSR 估计
- 全局 `FSR/k` 拟合
- `k` 相对位置拟合
- 熔融石英折射率
- `L/R/R` 反推
- 图表导出
- 理论 `2/9` 分支几何函数
- 圆周最短距离残差

### 3.2 `[01_recalc_cavity_params.py](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/01_recalc_cavity_params.py)`

主验算脚本。职责是：

- 跑四套独立 cavity 参数分析
- 生成每套数据的主峰表、FSR 表、`k` 表、腔参数表、图、报告

### 3.3 `[02_validate_peak_positions_vs_theory.py](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/02_validate_peak_positions_vs_theory.py)`

主峰理论位置验证脚本。职责是：

- 用解析 `k_th = 2/9`
- 对四个分析文件夹逐一计算主峰归一化位置偏差
- 输出展示图、汇总表、说法文件

## 4. 当前有效输出结构

### 4.1 四个权威分析文件夹

后续 agent 需要优先阅读的是这四个目录：

- [0p88mm 原始数据分析结果](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p88mm/原始数据分析结果)
- [0p88mm FSR补全分析结果](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p88mm/FSR补全分析结果)
- [0p98mm 原始数据分析结果](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p98mm/原始数据分析结果)
- [0p98mm FSR补全分析结果](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p98mm/FSR补全分析结果)

每个目录中最关键的文件如下：

- `cavity_parameters_summary.csv`
  最终参数表。看 `FSR / F / k / n / L / L/R / R` 就读这个。
- `main_peak_positions_summary.csv`
  主峰位置汇总表。看每个 `l` 的主峰波长和频率就读这个。
- `peak_fit_summary.csv`
  所有候选峰与最终选中峰的完整拟合审计表。
- `fsr_estimates.csv`
  方法 A 与方法 B 的 FSR 对比。
- `k_fit_summary.csv`
  `pos_meas / pos_fit / residual / m_l`。
- `cross_source_comparison.csv`
  原始 vs 补全的交叉验证。
- `theory_position_validation.csv`
  实测主峰位置与解析 `2/9` 理论位置的逐点偏差。
- `theory_position_validation_summary.csv`
  位置验证的 RMS / 最大偏差汇总。
- `theory_position_validation.png`
  当前最适合答辩展示的理论对比图。
- `针对这个文件夹的数据的说法.md`
  已经写好的、可直接用于汇报或改写成正文的话术。

### 4.2 最外层总汇总文件

最外层目前最值得读的文件是：

- [final_theory_position_validation_comparison.csv](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/final_theory_position_validation_comparison.csv)
- [final_theory_position_validation_overview.png](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/final_theory_position_validation_overview.png)
- [final_theory_position_validation_report.md](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/final_theory_position_validation_report.md)
- [汇总这四个文件夹的全部数据的说法.md](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/汇总这四个文件夹的全部数据的说法.md)

如果后续任务是“解释理论是否成立”“做答辩图”“写一段结论”，默认先读这四个文件。

## 5. 历史遗留与注意事项

### 5.1 `outputs/0p88mm/` 和 `outputs/0p98mm/` 根下的旧文件

这两个目录根下还残留了一些早期输出文件，它们来自四文件夹结构建立之前的中间阶段。

后续 agent 的规则应当是：

- 不要把 `outputs/0p88mm/` 根下的旧表当最终结果
- 不要把 `outputs/0p98mm/` 根下的旧表当最终结果
- 权威结果以四个“原始数据分析结果 / FSR补全分析结果”子目录为准

### 5.2 `outputs/final_cavity_parameter_comparison.csv`

这个文件理论上是由 `01_recalc_cavity_params.py` 生成的总汇总，但当前目录经历过多轮重构与补跑。

因此当前建议是：

- 如果它与四个子目录里的 `cavity_parameters_summary.csv` 一致，可以使用
- 如果出现冲突，以四个子目录中的 `cavity_parameters_summary.csv` 为权威

换句话说，后续 agent 不应把这个根汇总 CSV 当作唯一真值来源。

## 6. 物理口径与公式口径

### 6.1 晶体腔口径

本轮重算是按晶体腔，而不是空气腔处理的：

- `FSR_nu = c / (2 n L)`
- `phi = arccos(sqrt(1 - L/R))`
- `k = phi / pi`
- `L/R = sin^2(pi k)`
- `R = L / (L/R)`

折射率不是 `1`，而是熔融石英在约 `795 nm`、`20.18 °C` 的折射率。

### 6.2 理论主峰位置验证口径

主峰理论位置验证不再使用正文名义 `L=10.25 mm`、`R=25 mm` 作为输入，而是固定采用：

- 九维连续满载解析分支 `k_th = 2/9`
- 对应 `L/R_th = sin^2(pi * 2/9) = 0.413175911...`

比较量定义为：

- `pos_meas = ((nu_l - nu_0)/FSR_final) mod 1`
- `pos_th = (l * 2/9) mod 1`
- `delta_pos = ((pos_meas - pos_th + 0.5) mod 1) - 0.5`

因此这里只比较 FSR 内的相对位置，与精细度 `F` 无关。

## 7. 四套 cavity 参数结果

以下数值应以四个子目录各自的 `cavity_parameters_summary.csv` 为准。

### 7.1 `0.88 mm / 原始数据`

- `FSR = 9.915475 GHz`
- `F = 32.085683`
- `k = 0.222682`
- `L = 10.398543 mm`
- `L/R = 0.414598`
- `R = 25.081023 mm`

### 7.2 `0.88 mm / FSR补全后数据`

- `FSR = 9.938668 GHz`
- `F = 31.971669`
- `k = 0.222502`
- `L = 10.374279 mm`
- `L/R = 0.414043`
- `R = 25.056058 mm`

### 7.3 `0.98 mm / 原始数据`

- `FSR = 9.919383 GHz`
- `F = 32.311528`
- `k = 0.221895`
- `L = 10.394446 mm`
- `L/R = 0.412164`
- `R = 25.219193 mm`

### 7.4 `0.98 mm / FSR补全后数据`

- `FSR = 9.919386 GHz`
- `F = 32.317937`
- `k = 0.221863`
- `L = 10.394442 mm`
- `L/R = 0.412065`
- `R = 25.225244 mm`

### 7.5 参数层面的总体判断

从四套结果看：

- 两套光腰数据反推出的 `L` 都稳定在 `10.37–10.40 mm`
- 反推出的 `R` 都稳定在 `25.06–25.23 mm`
- `k` 都稳定在 `0.22186–0.22268`
- 整体上仍然支持“`L` 接近 `10.25 mm` 量级、`R` 接近 `25 mm` 量级”这一判断
- 但新重算值整体比正文名义值略高，尤其 `L` 更接近 `10.39 mm`

## 8. 理论位置验证结果

### 8.1 四套 merged 主结果

以 `theory_position_validation_summary.csv` 中 `measurement_type = merged` 为准：

- `0.88 / 原始数据`：
  RMS = `0.289% FSR`，最大偏差 = `0.372% FSR`
- `0.88 / FSR补全后数据`：
  RMS = `0.214% FSR`，最大偏差 = `0.332% FSR`
- `0.98 / 原始数据`：
  RMS = `0.204% FSR`，最大偏差 = `0.357% FSR`
- `0.98 / FSR补全后数据`：
  RMS = `0.221% FSR`，最大偏差 = `0.441% FSR`

### 8.2 理论验证的物理含义

九维理论相邻峰间距是：

- `1/9 FSR ≈ 11.111% FSR`

而当前实验主结果偏差只有：

- RMS 约 `0.20%–0.29% FSR`
- 最大偏差约 `0.33%–0.44% FSR`

因此这些偏差只占理论峰间距的大约：

- `2%–4%`

这说明：

- 实验主峰排布与解析 `k=2/9` 分支高度一致
- 可以说“理论预测得到了强有力支持”
- 但最好不要说成“理论被绝对严格证明毫无误差”

## 9. 关于“最终选哪套数据”的客观说明

本目录已经把四套结果全部并列展开，目的不是替后续使用者提前裁决“只能用哪一套”，而是把数据的真实原貌完整保留下来。

需要特别记录的是：

- 用户当前的实际采用口径是 `0.88` 的扫腔数据
- 但这并不意味着其他三个文件夹可以忽略
- 后续 agent 在写正文、做答辩或继续复核时，仍应把四套结果一起对照

因此，这里的推荐规则不是“替用户选最终答案”，而是：

- 如果任务是复述当前实际采用的扫腔数据来源，应先看 `0.88 mm` 两个文件夹
- 如果任务是比较原始与补全、或比较 `0.88` 与 `0.98` 的一致性，则必须四套都看
- 如果任务是做客观结论，先并列报告四套结果，再由用户或正文口径决定最终采用哪套

### 9.1 `0.88 mm` 两个文件夹的定位

用户当前实际采用的是 `0.88` 的扫腔数据，因此后续 agent 如果要对齐当前用户口径，应优先阅读：

- [0p88mm 原始数据分析结果](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p88mm/原始数据分析结果)
- [0p88mm FSR补全分析结果](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p88mm/FSR补全分析结果)

其中：

- `0.88 / 原始数据` 更接近“原貌”
- `0.88 / FSR补全后数据` 在理论位置验证里给出了更小的最大偏差

但这里不做单方面裁决，两者都应保留在最终叙述中。

### 9.2 `0.98 mm` 两个文件夹的定位

`0.98 mm` 两个文件夹不应被忽略，它们的价值主要在于：

- 作为独立第二套扫腔数据的横向验证
- 检验结论是否对光腰设定变化敏感
- 检验原始数据与 FSR 补全后数据之间的一致性

其结果表明：

- `0.98 / 原始数据` 与 `0.98 / FSR补全后数据` 非常接近
- 说明理论位置结论对该套数据中的补全策略不敏感

### 9.3 如果只是挑一张展示图

这里也不预设唯一答案。更合理的规则是：

- 如果要对齐“当前实际采用的是 0.88 数据”这一口径，就优先从 `0.88` 两个文件夹选图
- 如果要强调“第二套数据也支持同样结论”，就配合 `0.98` 文件夹的图一起展示
- 如果要做总览比较，则直接使用
  [final_theory_position_validation_overview.png](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/final_theory_position_validation_overview.png)

## 10. 后续 agent 的最短阅读路径

如果后续任务是“先快速上手，再理解四套结果的关系”，建议按下面顺序读：

1. 读本文件
2. 读 [汇总这四个文件夹的全部数据的说法.md](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/汇总这四个文件夹的全部数据的说法.md)
3. 读 [final_theory_position_validation_comparison.csv](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/final_theory_position_validation_comparison.csv)
4. 读四个子目录中的 `cavity_parameters_summary.csv`
5. 读四个子目录中的 `theory_position_validation_summary.csv`
6. 看四个子目录中的 `theory_position_validation.png`

如果后续任务是“对齐当前用户实际采用的是 0.88 数据”这一口径，则优先读：

7. [0p88mm 原始数据分析结果 cavity_parameters_summary.csv](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p88mm/原始数据分析结果/cavity_parameters_summary.csv)
8. [0p88mm FSR补全分析结果 cavity_parameters_summary.csv](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p88mm/FSR补全分析结果/cavity_parameters_summary.csv)
9. [0p88mm 原始数据分析结果 theory_position_validation_summary.csv](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p88mm/原始数据分析结果/theory_position_validation_summary.csv)
10. [0p88mm FSR补全分析结果 theory_position_validation_summary.csv](/D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/outputs/0p88mm/FSR补全分析结果/theory_position_validation_summary.csv)

如果后续任务是“核主峰提取是否可信”，则在对应文件夹继续读：

11. `main_peak_positions_summary.csv`
12. `peak_fit_summary.csv`
13. `cross_source_comparison.csv`

## 11. 一句结论版

如果后续 agent 只需要一句 handoff 结论，可采用：

“当前目录内已经完成了四套独立扫腔重算与四套解析 `k=2/9` 分支位置验证；用户当前实际采用的是 `0.88` 扫腔数据，但其他三个文件夹同样保留为独立交叉验证结果，后续应客观并列呈现四套数据，再由用户或正文口径决定最终引用哪一套。”

## 12. 2026-03-25 口径修正

- 当前 `k_relative_fit` 的定义已经更新：以 `l=0` 为参考，只用 `l=1..8` 锁定工作点，`l=9` 专门作为留出闭合检验。
- 后续如果看到 `k_fit_summary.csv` 或 `main_peak_positions_summary.csv`，应按 `reference / anchor / holdout` 三类角色理解，而不是默认 `l=0..9` 全部参与了 `k` 反演。
- `cavity_parameters_summary.csv` 中新增了 `k_relative_fit_fit_l_values`、`k_relative_fit_holdout_l_values`、`k_relative_fit_holdout_abs_delta_*` 等字段，用来直接追踪这套口径。
- `k_joint_method_B` 依然保留，但它现在是“全模审计值”，不应再被写成 `l=9` 的独立边界验证依据。
