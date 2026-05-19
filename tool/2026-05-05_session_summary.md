# 2026-05-05 会话记录 — 论文理解与工具脚本

## 1. 完成的工作

在 `tool/` 目录下创建了三个 Python 脚本：

### 1.1 `read_latex.py`
- 解析 `main.tex` 和 `supplement.tex`
- 提取：摘要、章节、公式（含标签）、图、表、关键参数

### 1.2 `read_pdf.py`
- 读取 `main.pdf`（13页）和 `supplement 1.pdf`（6页）
- 支持 PyMuPDF / PyPDF2 双后端
- 关键词搜索（Gouy, FSR, finesse, capacity, extinction, efficiency 等）

### 1.3 `simulation_params.py`（核心脚本）
- 论文所有关键参数集中在一个字典 `THESIS_PARAMS` 中
- 已实现的可直接调用的仿真函数：
  - `gouy_step_from_LR(L_over_R)` — Eq. (2)
  - `LR_from_gouy_step(k)` — 反解
  - `folded_position(N, k)` — Eq. (4-5)
  - `circular_spacing(pos_i, pos_j)` — Eq. (6)
  - `min_spacing(N_orders, k)` — Eq. (7)，返回 $s_{\min}$、最差模式对、各模式折叠位置
  - `airy_transmittance(delta_nu_over_FSR, finesse)` — Eq. (11)
  - `crosstalk_sum_M(M, finesse)` — 直接求和
  - `crosstalk_sum_closed(M, finesse)` — 闭式（Supp A.1）
  - `crosstalk_limit(tau_0)` — 大 $M$ 极限 (Eq. 8)
  - `er_from_crosstalk(P_noise)` / `eta_from_crosstalk(P_noise)` — Eq. (9)
  - `design_blueprint(M, tau_0=3)` — 生成 Table 2 设计蓝图
- **验证结果**：6 项参数一致性检查全部通过，设计蓝图与论文 Table 2 一致

---

## 2. 论文内容理解

### 2.1 核心物理模型

FP 腔中 LG 模的共振频率为

$$\nu_{q,N} = \text{FSR}\left(q + N\frac{\phi}{\pi}\right)$$

其中 $N = 2p + |l| + 1$ 为横模阶数，$\phi = \arccos(\sqrt{1-L/R})$ 为单程 Gouy 相位。

**归一化 Gouy 步长**（核心设计参数）：

$$k \equiv \frac{\phi}{\pi} = \frac{1}{\pi}\arccos\sqrt{1-\frac{L}{R}}$$

仅由几何比 $L/R$ 决定。

### 2.2 Spectral Folding 方法

- 折叠位置：$\text{pos}(N) = ((N-1)k) \bmod 1$
- 映射到单位圆上，圆弧间距：$s_{ij} = \min(|\text{pos}_i - \text{pos}_j|,\ 1 - |\text{pos}_i - \text{pos}_j|)$
- 最小间距：$s_{\min} = \min_{i \neq j} s_{ij}$
- 几何上限：$s_{\min} \le 1/M$（均匀分布时取等号）

### 2.3 设计准则与容量边界

**分辨力判据**：

$$\tau_{\min} = \mathcal{F} \cdot s_{\min} \ge \tau_0$$

**容量边界**（适用于任意目标集）：

$$M \le \left\lfloor \frac{\mathcal{F}}{\tau_0} \right\rfloor$$

即：finesse 为 $\mathcal{F}$ 的单腔最多能 sorting $\lfloor\mathcal{F}/\tau_0\rfloor$ 个模式。

### 2.4 均匀步长目标集的闭式解

$$\Delta_{\text{ord}} \cdot k \equiv \frac{m}{M} \pmod{1},\quad \gcd(m,M)=1$$

$$(L/R)^* = \sin^2(\pi k^*)$$

不同 $m$ 分支的灵敏度由 $dk/d(L/R) = [2\pi\sqrt{(L/R)(1-L/R)}]^{-1}$ 决定，最小灵敏度在 $L/R = 0.5$ 处。

### 2.5 非均匀目标集

最优 $k$ 归约为有限有理穷举搜索，分母上界：

$$q \le \max\left(\text{den}(a),\ \text{den}(b),\ 2D_{\max}\right)$$

### 2.6 性能评估

**Airy 透射函数**（串扰来源）：

$$T(\nu) = \frac{1}{1 + \left(\frac{2\mathcal{F}}{\pi}\right)^2 \sin^2\left(\frac{\pi\nu}{\text{FSR}}\right)}$$

**有限 $M$ 总串扰**（闭式，Supp A.1）：

$$P_{\text{noise}}^{(M)} = \frac{M}{\sqrt{1+a}} \frac{1+q^M}{1-q^M} - 1,\quad a = (2\mathcal{F}/\pi)^2,\quad q = \frac{\sqrt{1+a}-1}{\sqrt{1+a}+1}$$

**大 $M$ 极限**（保守上界）：

$$P_{\text{noise}}^{(\infty)}(\tau_0) = \frac{\pi}{2\tau_0}\coth\frac{\pi}{2\tau_0} - 1$$

$$\text{ER}_{\text{sum}}^{(\infty)} = 10\lg\frac{1}{P_{\text{noise}}^{(\infty)}},\quad \eta_{\text{sort}}^{(\infty)} = \frac{1}{1 + P_{\text{noise}}^{(\infty)}}$$

### 2.7 实验参数（$M=9$ 连续模，$p=0$）

| 参数 | 值 |
|---|---|
| 波长 | 795 nm |
| FSR | $9.915 \pm 0.004$ GHz |
| Finesse $\mathcal{F}$ | $32.21 \pm 0.19$ |
| $\mathcal{F}_{\min}$ (阈值) | 27 |
| $k^*$ | $2/9 \approx 0.2222$ |
| $k_{\text{meas}}$ | $0.2228 \pm 0.0003$ |
| $(L/R)^*$ | $\sin^2(2\pi/9) \approx 0.4132$ |
| 选用的 coprime 分支 | $m = 2$（灵敏度最低） |
| $\tau_0$ | 3 |
| FWHM | $\approx 307.9$ MHz |
| $l=9$ 回返偏移 | 23 MHz（0.23% FSR） |
| $\eta_{\text{sort}}$ 实测均值 | 93.19% |
| ER 实测均值 | 11.41 dB |
| 峰值透射率均值 | $\bar{T} \approx 0.88$ |

### 2.8 附录要点

- **A.1**: Airy 圆求和的闭式推导 + 大 $M$ 极限
- **A.2**: 一般目标集最优 $k$ 的有理性证明（全局最大在 V 型下包络的折点或端点）
- **B.1**: 投影臂 $\mathbf{S}$ 矩阵标定 + 非负最小二乘反演 $\hat{\mathbf{x}} = \arg\min_{\mathbf{x}\ge 0}\|\mathbf{S}\mathbf{x} - \mathbf{y}\|_2$
- **B.2**: $M=9$ 设计点公差窗口 $\Delta k \in [-3.6, +4.5]\times 10^{-3}$（在实测 $\mathcal{F}=32.21$ 下 $\tau_{\min}\ge\tau_0$）
- **C**: 推广到一般稳定两镜腔 — $k_{\text{eff}} = \pi^{-1}\arccos(\sqrt{g_1 g_2})$，平面-凹面/对称双凹面/非对称腔均为特例

---

## 3. 后续可进行的仿真方向（待讨论）

- 计算给定目标集的最优 $k$ 和对应的 $s_{\min}$
- Airy 模式串扰矩阵计算
- 不同 $M$、$\tau_0$ 下的性能边界扫描
- 非均匀目标集的有理穷举搜索
- 腔几何公差敏感性分析
- $k$ 偏差对 ER/$\eta$ 的影响
- 推广到双凹面腔 / 一般两镜腔的设计

---

## 4. 文件清单（本次新增）

```
tool/
  read_latex.py           # LaTeX 解析
  read_pdf.py             # PDF 读取 + 关键词搜索
  simulation_params.py    # 参数字典 + 仿真函数
  2026-05-05_session_summary.md   # 本文件
```
