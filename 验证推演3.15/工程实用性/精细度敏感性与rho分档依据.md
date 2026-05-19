# 精细度敏感性与 `rho` 分档依据

## 1. 这份报告解决什么问题

这份补充报告的目标很明确：

- 不把 `rho≈1.05 / 1.10 / 1.15-1.20` 写成没有来由的经验断言；
- 也不把正文改成器件制造手册；
- 而是给 `rho` 分档补上一套适合量子光学硕士论文和后续 OE 风格写作的**定量依据**。

这里采用的核心思路是：

1. `rho = F/(N\tau_0)` 仍然只是辅助总结量；
2. 分档依据不来自“行业规定”，而来自 achieved finesse 的短缺预算；
3. 镀膜反射率偏差只作为 achieved finesse 偏差的上游来源之一。

---

## 2. 核心公式

对连续满载设计，

\[
\rho = \frac{\mathcal F}{N\tau_0}.
\]

若实际 achieved finesse 与名义设计值之间存在相对缩放，

\[
\mathcal F_{\mathrm{actual}} = (1-\epsilon)\mathcal F_{\mathrm{nominal}},
\]

则有

\[
\rho_{\mathrm{actual}} = (1-\epsilon)\rho_{\mathrm{nominal}}.
\]

因此，若希望实际工作时仍满足

\[
\rho_{\mathrm{actual}}\ge \rho_{\mathrm{floor}},
\]

则名义值至少应满足

\[
\rho_{\mathrm{nominal}}\ge \frac{\rho_{\mathrm{floor}}}{1-\epsilon}.
\]

这就是本轮把经验分档改写成预算分档的基础。

---

## 3. 当前实验提供的内部锚点

本目录当前实验本身已经给出一条非常重要的内部锚点：

- 名义 finesse：`29.8`
- 实测 finesse：`31.35`

对 `N=9, tau0=3` 有

\[
\rho_{\mathrm{nominal}} = \frac{29.8}{27} \approx 1.1037,
\qquad
\rho_{\mathrm{measured}} = \frac{31.35}{27} \approx 1.1611.
\]

因此，“把 achieved finesse 敏感性并入 `rho` 讨论”并不是生造的新议题，而是对当前实验事实的直接整理。

---

## 4. 本轮扫描回答了什么

新增脚本 `08_finesse_robustness_scan.py` 与 `09_finesse_robustness_maps.py` 主要回答三类问题：

### 4.1 achieved finesse 负偏差会把名义 `rho` 拉低到哪里

代表性结果：

- 若名义 `rho=1.10`，遇到 `-5%` achieved finesse 短缺，则
  \[
  \rho_{\mathrm{actual}} \approx 1.045.
  \]
- 若名义 `rho=1.15`，遇到 `-10%` achieved finesse 短缺，则
  \[
  \rho_{\mathrm{actual}} \approx 1.035.
  \]
- 若想在 `-10%` 的 shortfall 下仍保持 `\rho_{\mathrm{actual}}\ge 1.05`，名义值需达到
  \[
  \rho_{\mathrm{nominal}} \ge 1.167.
  \]

### 4.2 当前 `rho` 档位可以怎样被更稳地解释

- `rho≈1.05`
  只能覆盖“别跌回边界太多”的近边界状态，因此更接近探索性验证；
- `rho≈1.10`
  能在约 `5%` 的 finesse shortfall 下保持 `\rho_{\mathrm{actual}}\approx 1.05`，且与当前 9 模名义设计一致，因此适合作为基准工程档；
- `rho≈1.15-1.20`
  对应更高的 finesse 短缺容忍度，因此更适合作为稳健建议区。

### 4.3 为什么高目标 finesse 的实现会更敏感

本轮还用理想对称腔近似

\[
\mathcal F \approx \frac{\pi\sqrt{R}}{1-R}
\]

扫描了 `R \rightarrow \mathcal F` 的放大关系。结果显示：

- 对 `F≈29.8` 的目标，`ΔR = -0.005` 会带来约 `-5%` 的 finesse 变化；
- 对 `F≈95` 的目标，同样 `ΔR = -0.005` 会带来更大的相对 finesse 变化；
- 对 `F≈160` 或更高目标，敏感性继续显著增强。

这说明高维连续满载设计的困难，不只是边界 `F_{\min}=N\tau_0` 提高了，而且系统本身对反射率和附加损耗误差也更敏感。

---

## 5. 这些结论能支撑到什么程度

### 5.1 能支撑的说法

- `rho=1` 是严格解析边界；
- `rho≈1.10` 与当前 9 模样机的名义设计一致；
- `rho≈1.10`、`1.15-1.20` 这些档位可以被解释成对 achieved finesse shortfall 的不同覆盖能力；
- 高目标 finesse 设计对反射率和损耗误差更敏感，这一点可以由 `R \rightarrow \mathcal F` 的扫描直观看出。

### 5.2 不能写得太满的说法

- 不能写成“行业或文献规定 `rho=1.10` 最合理”；
- 不能写成“所有工厂都会保证某个固定的反射率公差，因此 `rho≈1.10` 是通用标准”；
- 不能把 `R \rightarrow \mathcal F` 的理想对称腔近似写成实际器件的完整误差模型；
- 不能把 achieved finesse 的偏差简单归因于镀膜工艺单一来源。

---

## 6. 外部参考能提供什么层级的支持

这部分外部参考的作用是“支撑数量级与物理合理性”，不是替你直接给出 `rho` 常数。

### 6.1 镀膜和反射率公差确实是现实工程量

Thorlabs 的 optical coatings 页面明确说明，镀膜的实际性能会随 coating run 变化，而且规格通常以一定波段上的平均反射率或透过率来表述，而不是单一理想点值。[Thorlabs Optical Coatings](https://www.thorlabs.com/OpticalCoatings)

这支持的结论是：

- 反射率并不是一个完全无误差、无波动的理想固定量；
- 用 `R \rightarrow \mathcal F` 的敏感性来说明 achieved finesse 的上游风险，是合理的。

### 6.2 真实腔体的敏感性不只来自 spacer 长度

NIST 关于低膨胀 Fabry-Perot 腔温度分析的工作明确指出，实际腔体的热响应不仅取决于 spacer 的热膨胀，还取决于镜面与 spacer 的失配形变和具体几何。[NIST](https://www.nist.gov/publications/temperature-analysis-low-expansion-fabry-perot-cavities)

这支持的结论是：

- 真实器件的 achieved finesse 与稳定性，不能被单一“长度公差”完全概括；
- 把讨论重心放在 achieved finesse 这个直接进入判据的系统量上，更适合本文当前的物理论证主线。

---

## 7. 对硕士论文和 OE 风格写作的适配

### 7.1 更适合硕士论文的版本

正文或补充报告里保留下面三点就足够：

1. `rho` 是辅助总结量，不替代 `tau/delta`；
2. `rho` 分档来自 achieved finesse shortfall 预算，而不是凭感觉分段；
3. 当前 9 模器件的 `29.8 -> 31.35` 已经给出直接实验证据。

这样做的优点是：

- 主线仍是物理规律；
- 讨论深度足够 defend；
- 不会把篇幅拖入器件手册式细节。

### 7.2 更适合 OE 风格的版本

若后续要压缩成投稿语言，更该强调的是：

- `tau/delta/rho` 如何形成可迁移的设计准则；
- 连续满载边界 `F_{\min}=N\tau_0`；
- nominal `rho` 需要覆盖 achieved finesse shortfall 的预算思想；
- 当前实验如何为这套规则提供锚点。

而不必在正文里展开过多具体制造工艺细节。

---

## 8. 推荐话术

下面这段话是本轮最推荐保留的版本：

> 在本文当前模型、筛选阈值和 finesse 误差预算下，`rho≈1.05` 更接近探索性边界区；`rho≈1.10` 与当前 9 模器件的名义设计一致，并可覆盖约 `5%` 级别的 achieved finesse 短缺而保持 `rho_actual≈1.05`，因此可作为基准工程档；`rho≈1.15-1.20` 对应更强的 finesse 短缺容忍度，因而更适合作为较稳健的经验建议区。上述分档不是行业标准常数，而是本文模型、当前筛选阈值和给定 finesse 误差预算下的经验分档。

---

## 9. 本报告对应的脚本与输出

- `08_finesse_robustness_scan.py`
- `09_finesse_robustness_maps.py`
- `outputs/08_finesse_robustness_scan/finesse_relative_error_scan.csv`
- `outputs/08_finesse_robustness_scan/reflectivity_to_finesse_scan.csv`
- `outputs/08_finesse_robustness_scan/current_design_finesse_anchor.csv`
- `outputs/08_finesse_robustness_scan/rho_required_under_finesse_shortfall.csv`
- `outputs/09_finesse_robustness_maps/rho_required_vs_finesse_shortfall.png`
- `outputs/09_finesse_robustness_maps/reflectivity_error_to_finesse_gain.png`
- `outputs/09_finesse_robustness_maps/rho_nominal_to_rho_actual_bands.png`
- `outputs/09_finesse_robustness_maps/current_design_29p8_vs_31p35_anchor.png`
- `outputs/09_finesse_robustness_maps/rho_band_justification_table.csv`
