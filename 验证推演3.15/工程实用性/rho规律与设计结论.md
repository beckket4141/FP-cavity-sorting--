# `rho` 规律与设计结论

## 1. 这份补充报告的定位

这份文档只服务于 `D:\自制软件\thesis\验证推演3.15\工程实用性` 目录下的工程分析，不修改论文正文。

它的目标不是用 `rho` 取代已有的 `tau/delta` 主框架，而是回答两个更具体的问题：

1. 连续满载设计离解析边界到底有多远？
2. 这段“离边界的距离”在 achieved finesse 偏离名义值时还能剩下多少？

因此，这里对 `rho` 的定位始终是：

- `tau/delta`：主理论坐标；
- `rho`：连续满载设计余量的速查量；
- achieved finesse robustness：给 `rho` 分档补上定量预算依据。

---

## 2. 定义与基本关系

对连续满载解析峰中心，有

\[
\tau_{\mathrm{eff}}^{*} = \frac{\mathcal F}{N},
\qquad
\delta = \frac{\tau_0}{\mathcal F}.
\]

于是可定义

\[
\rho \equiv \frac{\tau_{\mathrm{eff}}^{*}}{\tau_0}
= \frac{\mathcal F}{N\tau_0}
= \frac{1}{N\delta}.
\]

这一定义有三个直接结论：

1. `rho = 1` 是连续满载的解析边界；
2. `rho > 1` 才意味着解析峰顶高于阈值线；
3. 对固定 `N` 与 `tau0`，`rho` 与 finesse 成正比。

同时，

\[
\frac{1}{N} - \delta
= \frac{1}{N}\left(1-\frac{1}{\rho}\right),
\]

因此 `rho` 确实把“高出边界多少”压缩成了一个单独量。

---

## 3. 为什么单靠经验说 `rho≈1.05 / 1.10 / 1.15-1.20` 不够

如果把这些数值直接写成“推荐档位”，容易被质疑为主观分段。

真正更稳的说法应该是：

> 名义 `rho` 的选取，必须覆盖实际 achieved finesse 可能低于名义值的短缺预算。

因为对本文当前这类设计判据而言，真正直接进入容量边界与平台宽度的实现层量，不是某个抽象制造故事，而是**实际 achieved finesse**。

一旦实际 finesse 相对名义值缩放，

\[
\rho_{\mathrm{actual}}
= \rho_{\mathrm{nominal}}
\frac{\mathcal F_{\mathrm{actual}}}{\mathcal F_{\mathrm{nominal}}}.
\]

若记

\[
\mathcal F_{\mathrm{actual}}
= (1-\epsilon)\mathcal F_{\mathrm{nominal}},
\]

其中 `\epsilon` 是 worst-case finesse shortfall，则有

\[
\rho_{\mathrm{actual}}
= (1-\epsilon)\rho_{\mathrm{nominal}}.
\]

于是，为保证实际工作时仍有

\[
\rho_{\mathrm{actual}} \ge \rho_{\mathrm{floor}},
\]

名义值至少应满足

\[
\rho_{\mathrm{nominal}}
\ge \frac{\rho_{\mathrm{floor}}}{1-\epsilon}.
\]

这就是本轮补充分析要建立的“预算化分档”依据。

---

## 4. 本轮新增的两条补强链

### 4.1 achieved finesse 短缺预算

新增脚本 `08_finesse_robustness_scan.py` 对以下量做了系统扫描：

- `rho_nominal = 1.05, 1.10, 1.15, 1.20`
- achieved finesse 相对误差：
  `-10%, -5%, -2%, 0, +2%, +5%, +10%`
- `N = 9, 12, 30, 50`
- `tau0 = 3, 4, 5, 6`

这一链直接回答：

- 名义 `rho` 下探多少会掉回边界附近？
- 对代表性 `N` 而言，final engineering branches 和平台宽度会如何变化？

### 4.2 反射率偏差到 finesse 的上游放大

新增脚本同时用理想对称腔近似

\[
\mathcal F \approx \frac{\pi\sqrt{R}}{1-R}
\]

做了 `R \rightarrow \mathcal F` 的敏感性扫描，用于说明：

- 反射率绝对偏差 `\Delta R` 在不同目标 finesse 下会被放大成多大的 `\Delta \mathcal F / \mathcal F`；
- 高目标 finesse 设计对反射率与附加损耗误差会更敏感。

要强调的是：这条链只是上游解释模型，不替代 achieved finesse 本身的实测判据。

---

## 5. 当前实验锚点为什么很重要

当前实验有一个非常有价值的内部锚点：

- 名义设计：`F = 29.8`
- 实测 achieved finesse：`F = 31.35`

对 `N=9, tau0=3` 而言，这意味着

\[
\rho_{\mathrm{nominal}} = \frac{29.8}{9\times 3} \approx 1.1037,
\qquad
\rho_{\mathrm{measured}} = \frac{31.35}{9\times 3} \approx 1.1611.
\]

也就是说，当前 9 模器件本身就说明了两件事：

1. `rho≈1.10` 不是凭空挑出来的，它与当前样机名义设计天然一致；
2. achieved finesse 的实际偏移会直接把 `rho` 推到另一个分档，这件事在当前实验里已经真实发生过。

因此，把 achieved finesse 敏感性并入 `rho` 的讨论，不是额外“做大文章”，而是对现有实验事实的自然整理。

---

## 6. 本轮最关键的定量结果

由

\[
\rho_{\mathrm{nominal}}
\ge \frac{\rho_{\mathrm{floor}}}{1-\epsilon}
\]

可以直接得到若干非常适合后续引用的数值：

### 6.1 如果只要求实际不掉回边界：`\rho_actual >= 1.00`

- 若容忍 `5%` 的 finesse shortfall，则
  \[
  \rho_{\mathrm{nominal}} \ge \frac{1.00}{0.95} \approx 1.053.
  \]
- 若容忍 `10%` 的 finesse shortfall，则
  \[
  \rho_{\mathrm{nominal}} \ge \frac{1.00}{0.90} \approx 1.111.
  \]

### 6.2 如果要求实际仍保持一个小的有效余量：`\rho_actual >= 1.05`

- 若容忍 `5%` 的 finesse shortfall，则
  \[
  \rho_{\mathrm{nominal}} \ge \frac{1.05}{0.95} \approx 1.105.
  \]
- 若容忍 `10%` 的 finesse shortfall，则
  \[
  \rho_{\mathrm{nominal}} \ge \frac{1.05}{0.90} \approx 1.167.
  \]

### 6.3 这些数如何对应到语言分档

这就给原来的经验分档补上了预算含义：

- `rho≈1.05`
  更接近“只要别跌回边界就行”的近边界设计；
- `rho≈1.10`
  可以覆盖约 `5%` 级别的 finesse shortfall，同时仍把实际 `rho` 维持在 `1.05` 左右；
- `rho≈1.15-1.20`
  对应更高的 finesse 短缺容忍度，因此更适合作为稳健建议区。

---

## 7. 如何更稳地写这三档

### 7.1 可以保留的写法

> 在本文当前模型、筛选阈值和 finesse 误差预算下，`rho≈1.05` 更接近探索性边界区；`rho≈1.10` 与当前 9 模器件的名义设计一致，并可覆盖约 `5%` 级别的 achieved finesse 短缺而保持 `rho_actual≈1.05`，因此可作为基准工程档；`rho≈1.15-1.20` 对应更强的 finesse 短缺容忍度，因而更适合作为较稳健的经验建议区。

### 7.2 必须补上的限定

> 上述分档不是行业标准常数，而是本文模型、当前筛选阈值和给定 finesse 误差预算下的经验分档。

### 7.3 必须避免的写法

- 不要写成“文献规定 `rho=1.10` 更合理”；
- 不要写成“工厂都会把 mirror reflectivity 控在某个固定百分数，所以 `rho=1.10` 是通用标准”；
- 不要把 `rho` 写成脱离 `tau/delta` 的新主理论坐标；
- 不要把 achieved finesse 敏感性说成只来自镀膜工艺，忽略散射、吸收和装调等其他上游来源。

---

## 8. 反射率敏感性这条线该怎么说

这一条线的作用不是直接规定 `rho`，而是给 achieved finesse 误差一个可理解的物理来源图景。

更稳的说法是：

1. 反射率偏差是 achieved finesse 偏差的典型上游来源之一；
2. 在目标 finesse 越高时，同样的 `\Delta R` 会放大成更大的 `\Delta \mathcal F / \mathcal F`；
3. 因而高 `N`、高 `tau0` 所要求的高 finesse 设计，不仅边界线更高，对反射率与损耗误差也更敏感；
4. 最终进入工程判据和 `rho` 分档的，仍然是实际 achieved finesse，而不是厂家名义反射率本身。

这组说法更符合量子光学论文的重心：讨论与物理判据直接耦合的系统量，而不是把篇幅转成器件手册式工艺细节。

---

## 9. 对后续写作最值得复用的几句话

### 关于 `rho`

> `rho = F/(N\tau_0)` 不是新的理论主坐标，而是连续满载设计离解析边界有多远的速查量。

### 关于分档依据

> 对本文而言，`rho` 的工程意义不应只用经验口吻来描述，而应结合 achieved finesse 的 worst-case shortfall 预算来理解：名义 `rho` 必须足够高，才能在实际 finesse 下滑后仍保留所需的 `rho_actual`。

### 关于当前 9 模器件

> 当前 9 模样机的名义设计已经对应 `rho≈1.10`，而实测 finesse 的提升又把它推到 `rho≈1.16`；这说明 `rho` 的工程分档并不是脱离实验的抽象修辞，而是可以直接从现有器件中读出的。

### 关于高维扩展

> 高维连续满载设计的困难，不仅在于 `F_{\min}=N\tau_0` 线性升高，也在于高目标 finesse 设计对反射率与附加损耗误差会变得更敏感，因此名义 `rho` 需要覆盖更现实的 finesse 短缺预算。

---

## 10. 与本目录其他输出的对应关系

本轮 `rho` 相关结论主要对应以下新增输出：

- `outputs/08_finesse_robustness_scan/finesse_relative_error_scan.csv`
- `outputs/08_finesse_robustness_scan/reflectivity_to_finesse_scan.csv`
- `outputs/08_finesse_robustness_scan/current_design_finesse_anchor.csv`
- `outputs/08_finesse_robustness_scan/rho_required_under_finesse_shortfall.csv`
- `outputs/09_finesse_robustness_maps/rho_required_vs_finesse_shortfall.png`
- `outputs/09_finesse_robustness_maps/reflectivity_error_to_finesse_gain.png`
- `outputs/09_finesse_robustness_maps/rho_nominal_to_rho_actual_bands.png`
- `outputs/09_finesse_robustness_maps/current_design_29p8_vs_31p35_anchor.png`
- `outputs/09_finesse_robustness_maps/rho_band_justification_table.csv`

若要准备答辩或后续论文压缩，优先看这份文档和 `精细度敏感性与rho分档依据.md` 即可。
