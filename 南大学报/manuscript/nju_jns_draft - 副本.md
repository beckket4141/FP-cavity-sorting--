# 稳定双镜法布里-珀罗腔中拉盖尔-高斯模式分束的统一设计框架及误差机理

## 摘要

法布里-珀罗腔通过 Gouy 相位依赖共振可实现对拉盖尔-高斯模式的保态频谱分束。已有研究多以平凹腔或特定实验构型为出发点，尚缺少面向一般稳定双镜腔的统一设计表述。本文以单自由光谱范围内的折叠谱表示为基础，将模式分束设计归结为有效归一化 Gouy 步长的圆周排布问题，建立适用于稳定双镜 FP 腔的统一框架，其中腔型差异体现为有效步长 \(k_{\mathrm{eff}}\) 与几何参数之间的映射关系。结果表明，平凹腔满足 \(L/R=\sin^2(\pi k_{\mathrm{eff}})\)，对称双凹腔满足 \(L/R=1\pm\cos(\pi k_{\mathrm{eff}})\)，后者不能由前者简单作 \(L\rightarrow 2L\) 得到；在小几何比极限下，对称双凹腔相对平凹腔的步长增强因子趋近于 \(\sqrt{2}\)。进一步地，连续模式集的最小间距景观具有由 Farey 邻分数控制的层级细化结构，而不同腔型会改变最优分支的几何回代与鲁棒性排序。以 \(M=9\) 连续模式集为例，平凹腔中鲁棒代表支为 \(m=2\)，对称双凹腔中更鲁棒的代表支转移到 \(m=4\)。在误差机理方面，轴对称束腰失配、束腰位置失配和曲率失配主要激发同一角向指数子空间内的径向高阶分量，其中 \(p=1\) 是首要可观测寄生项；横向偏移和倾斜等破坏圆对称的误差才会显著引入角向混模。该结果为实验频谱中的卫星峰来源提供了统一解释，并说明稳定双镜 FP 腔中的 LG 模式分束应同时从有效步长设计和空间模式误差控制两个层面进行优化。

**关键词**：法布里-珀罗腔；拉盖尔-高斯模式；Gouy 相位；模式分束；谱折叠；误差机理

---

## 1 引言

携带轨道角动量的拉盖尔-高斯（Laguerre-Gaussian, LG）模式为高维光通信、空间模式复用与量子信息处理提供了重要自由度[1-6]。在这类应用中，除了区分不同模式之外，往往还要求输出端保持原有横向场结构，以便进行后续干涉、路由或级联处理。已有模式分束技术包括坐标变换、多平面光转换、干涉级联和单平面衍射设计等[7-11]。这些方法在模式判别和容量扩展方面具有重要价值，但部分量子逻辑、相干路由和模块化空间模式处理任务还需要保态分束过程，即分束后仍保留输入横向模式的振幅与相位结构[12]。

FP 腔提供了实现保态模式选择的另一条路线。稳定腔中横模共振频率由 Gouy 相位决定[13-14]，因而不同横向总阶可在频域中被选择性透射，而横向场结构在理想腔响应中保持不变。近年来，基于可调 FP 谐振器和薄膜 FP 滤波器的 OAM 或模式组选择已经得到实验展示[15-17]。这些工作证明了 FP 腔作为空间模式频谱器件的可行性，但多围绕具体器件或少数模式任务展开；对于给定目标模式集，尤其是高维连续 LG 模式集，仍需要一个能够同时连接腔型选择、容量边界和工程鲁棒性的设计语言。

对模式分束真正起决定作用的并不是“平凹”这一几何标签本身，而是单自由光谱范围内不同横模共振位置的相对排布。若把不同稳定双镜腔统一映射到同一个有效 Gouy 步长参数，则平凹腔、对称双凹腔乃至一般稳定两镜腔都可纳入同一折叠谱框架。图 1 给出了这一思想的示意：折叠谱排布由有效步长决定，具体腔型则通过几何回代实现该步长。

另一方面，随着目标模式数增多，折叠后的共振位置会在单自由光谱范围内形成复杂的最小间距景观。该景观不仅决定可实现的分束容量，也影响分支选择与器件鲁棒性。对于连续目标集，这一景观在视觉上呈现出层级细化特征；其结构来源可以由 Farey 邻分数骨架加以组织，而不需要诉诸严格自相似分形的表述。

此外，实验中常见的卫星峰、峰值衰减和高阶模性能退化，也需要一个与统一设计框架兼容的误差机理解释。若误差主要来自束腰大小失配、束腰位置偏差和曲率偏差，则它们通常保持绕腔轴的圆对称性，理论上主要激发同一角向指数子空间内的径向高阶分量；横向偏移、倾斜和非对称截断等误差则会破坏圆对称性，引入不同角向指数之间的混合。区分这两类误差，有助于统一解释频谱中的寄生峰来源，并为实验优化给出更明确的方向。

基于上述考虑，本文围绕稳定双镜 FP 腔中的 LG 模式分束建立统一设计框架。首先，以有效归一化 Gouy 步长 \(k_{\mathrm{eff}}\) 为核心，重写适用于一般稳定双镜腔的折叠谱设计表述，并给出平凹腔与对称双凹腔的几何回代关系。其次，从 Farey 邻分数和层级细化的角度解释连续目标集最小间距景观的来源，说明不同腔型如何改变最优分支的几何实现与鲁棒性排序。最后，结合径向串扰推演结果，建立与实验频谱现象相一致的误差机理图像，说明轴对称失配主要表现为径向寄生项，且 \(p=1\) 是首要可观测项，而显著角向混模则需要对称性破坏误差参与。

---

## 2 稳定双镜 FP 腔中的统一折叠谱框架

### 2.1 以有效步长为核心的统一表述

对于稳定双镜 FP 腔，横模共振频率可写为

$$
\nu_{q,N}=\mathrm{FSR}\left(q+N k_{\mathrm{eff}}\right),
$$

其中 \(q\) 为纵模指标，\(N=2p+|l|+1\) 为横向总阶，\(p\) 与 \(l\) 分别为 LG 模式的径向指标和角向指标，\(k_{\mathrm{eff}}\) 为相对于一个自由光谱范围归一化后的有效 Gouy 步长。对一般稳定两镜腔，有

$$
k_{\mathrm{eff}}=\frac{1}{\pi}\arccos\left(\sqrt{g_1g_2}\right),
$$

其中 \(g_1=1-L/R_1\)，\(g_2=1-L/R_2\)。一旦采用这一写法，模式分束问题就不再直接依赖于具体腔型，而转化为：给定目标模式集 \(S\)，如何在单自由光谱范围内最大化其折叠共振位置的最小圆周间距。

因此，设计框架可分成两层。第一层是与几何无关的折叠谱排布层，它只关心 \(k_{\mathrm{eff}}\) 与目标模式集之间的算术关系；第二层是与几何相关的回代层，它负责把选定的 \(k_{\mathrm{eff}}\) 变成具体腔长与曲率半径。这样的分层能够把统一物理结构和具体器件实现清晰分开，也使得平凹、双凹与更一般稳定双镜腔之间的对应关系更加明确，如图 1 所示。

### 2.2 平凹腔与对称双凹腔的回代关系

平凹腔是 \(R_1=\infty\)、\(R_2=R\) 的特例，此时有

$$
k_{\mathrm{eff}}=\frac{1}{\pi}\arccos\left(\sqrt{1-L/R}\right),
$$

从而得到几何回代关系

$$
\frac{L}{R}=\sin^2(\pi k_{\mathrm{eff}}).
$$

对于对称双凹腔，\(R_1=R_2=R\)，因此

$$
k_{\mathrm{eff}}=\frac{1}{\pi}\arccos\left(|1-L/R|\right),
$$

回代后得到

$$
\frac{L}{R}=1\pm\cos(\pi k_{\mathrm{eff}}).
$$

这里的两支分别对应近平面稳定支和近同心稳定支。由此可见，对称双凹腔并不是把平凹腔结果中 \(L\) 简单替换为 \(2L\) 即可得到。二者虽然都可用同一个 \(k_{\mathrm{eff}}\) 统一描述，但几何实现方式并不等价。

### 2.3 小几何比极限下的差异

若考察小 \(L/R\) 极限，平凹腔有

$$
k_{\mathrm{pc}}\approx \frac{\sqrt{L/R}}{\pi},
$$

而对称双凹腔有

$$
k_{\mathrm{cc}}\approx \frac{\sqrt{2L/R}}{\pi}.
$$

因此

$$
\frac{k_{\mathrm{cc}}}{k_{\mathrm{pc}}}\rightarrow \sqrt{2},
$$

而不是直观猜想中的 2。这说明“双凹腔的一程 Gouy 相移等于平凹腔翻倍”只能作为粗略图像，不能替代严格公式。真正影响结果的是腔本征模参数也随边界条件一同改变，从而改变了步长与几何参数之间的映射。

---

## 3 景观结构与构型实现

### 3.1 连续目标集最小间距景观的层级细化

对连续目标集 \(S_M=\{1,2,\ldots,M\}\)，折叠共振位置的最小圆周间距可写为

$$
s_{\min}(k)=\min_{1\le q\le M-1}\|qk\|.
$$

这一表达式表明，景观本质上是若干锯齿函数的下包络。随着 \(M\) 增大，新加入的差值约束不会抬高原有景观，而只会在其下方继续切出更细的局部结构。为检验该嵌套关系，本文对 \(M=4,9,15\) 的景观进行了高密度网格计算，结果表明细景观始终逐点不高于粗景观；其中 \(M=9\) 与 \(M=4\) 的逐点重合比例约为 46.1%，\(M=15\) 与 \(M=9\) 的逐点重合比例约为 62.8%。因此，更大的目标集并不是推翻原有粗轮廓，而是在其下方进行算术意义上的细化。

进一步的 Farey 骨架分析表明，在固定 \(M\) 下，景观可以按分母不超过 \(M-1\) 的 Farey 邻分数区间来组织。设相邻分数为 \(a/b<c/d\)，则局部峰值的位置由 mediant \((a+c)/(b+d)\) 决定，峰高由相邻分母之和 \(b+d\) 控制。由此得到的局部峰一般是偏斜帐篷形。图 2 展示了这一 Farey 骨架与景观层级细化之间的对应关系。因此，“景观看起来像分形”的更精确表述是“Farey 骨架约束下的层级细化”，而不是严格意义上的自相似分形。

### 3.2 不同腔型下的几何实现与鲁棒性排序

虽然折叠谱设计层只依赖 \(k_{\mathrm{eff}}\)，但一旦回到具体器件实现，腔型差异便会通过几何映射影响可实现设计点和鲁棒性排序。对于 \(M=9\) 的连续模式集，三条代表性的互素分支 \(m=1,2,4\) 都能达到相同的理论最优间距 \(1/9\)，但其对应的几何点并不等效。

在平凹腔中，三条代表支分别对应 \(L/R\approx0.117\)、0.413 和 0.970，其中 \(m=2\) 分支最接近灵敏度最小点 \(L/R=0.5\)，因此最鲁棒。对称双凹腔中，灵敏度最小点转移到共焦点 \(L/R=1\) 附近，代表支的最优排序也随之改变：\(m=4\) 分支更靠近这一低灵敏度区域，从而成为更鲁棒的代表支。也就是说，容量上限与最优步长条件可以在不同腔型间直接继承，但几何回代与工程优选分支必须重新计算，不能只在平凹腔结果外乘一个整体系数。图 3 比较了平凹腔和对称双凹腔的几何映射及 \(M=9\) 鲁棒分支重排。

这一点对于器件设计具有直接意义。若只从折叠谱排布出发，平凹腔与双凹腔在很多情况下都可实现同样的理论容量；但若考虑加工误差、调节裕量和工作点稳定性，不同腔型可能会偏向不同分支。统一框架的价值在于把这两层区分开：理论容量由 \(k_{\mathrm{eff}}\) 决定，而工程最优实现则由具体几何映射和灵敏度分布共同决定。

---

## 4 误差机理与寄生峰来源

### 4.1 轴对称失配主要引发径向展开

若入射场保持绕腔轴的圆对称形式

$$
E_{\mathrm{in}}(r,\phi)=f(r)\exp(il\phi),
$$

则其对腔模基 \(LG_p^{l'}\) 的投影在角向积分后满足 \(l'=l\)。因此，束腰大小失配、束腰位置偏差、波前曲率失配以及以腔轴为中心的圆对称截断，都可以改变径向指标 \(p\) 的展开系数，却不会在理想条件下引入不同角向指数之间的混合。

对于仅含束腰大小失配的典型情形，若入射场为 \(LG_0^l\)，且 \(\eta=w_{\mathrm{in}}/w_0\)，则同一 \(l\) 子空间内的径向展开满足

$$
|c_{p,l}|^2=
\binom{p+|l|}{p}
\left(\frac{2\eta}{1+\eta^2}\right)^{2|l|+2}
\left(\frac{1-\eta^2}{1+\eta^2}\right)^{2p}.
$$

其中每增加一个径向阶都会额外带来失配小参数

$$
s=\frac{1-\eta^2}{1+\eta^2}
$$

的平方因子。因此，在轻微失配下，\(p=1\) 是首要可观测寄生项，\(p=2\) 及更高项则按更高阶幂次迅速衰减。数值扫描给出了相同趋势。例如，对 \(l=8\) 且 \(\eta=0.95\) 的情形，\(p=1\) 的权重约为 2.31%，而 \(p\ge2\) 的总权重仍显著更低。图 4 给出了不同 \(l\) 与不同束腰比下的径向泄漏分布。

### 4.2 对称性破坏误差才会显著引入角向混模

当误差破坏绕腔轴的圆对称性时，情况发生变化。横向偏移、倾斜、像散和偏心截断等误差会把 \(\exp(il\phi)\) 的单一角向因子耦合到多个 \(l+m\) 分量中，因而在腔模基中同时引入不同 \(l\) 与不同 \(p\) 的混合。以 \(x\) 方向相位倾斜为例，因子 \(\exp(ik_xr\cos\phi)\) 可展开为不同 \(m\) 阶 Bessel 分量，从而直接产生角向指数变化。

数值结果表明，相比轴对称的轴向偏移或束腰失配，横向偏移和相位倾斜更容易在较小误差量下迅速抬升 other-\(l\) 分量。图 5(a,b) 对比了轴对称失配和破坏对称误差的典型结果。由此可见，在实验频谱中，若观察到结构规则、位置可预测、但幅值较弱的寄生小峰，更自然的解释通常是同一 \(l\) 子空间内的径向寄生项被腔选出；若出现明显的角向混模或跨通道泄漏，则更需要从横向失调或对称性破坏误差寻找原因。

### 4.3 卫星峰的统一解释

在球对称或近球对称 FP 腔中，横模共振位置主要由总阶

$$
N=2p+|l|+1
$$

决定。因此，即使输入端名义上制备的是 \(LG_0^l\)，只要其相对于腔本征模基存在少量 \(LG_1^l\) 或更高 \(p\) 分量，这些分量在扫频过程中也会在对应的 \(N\) 共振位置透射出来，从而形成卫星峰。以 \(l=4,p=0\) 为例，其总阶为 \(N=5\)；若存在少量 \(l=4,p=1\) 分量，则其总阶变为 \(N=7\)，与 \(l=6,p=0\) 的频率位置简并。因此，频谱中出现在 \(l=6,p=0\) 附近的弱峰，未必意味着光场真的被转换成了 \(l=6,p=0\)，更可能只是腔模基中少量 \(l=4,p=1\) 分量在该频率点被选择性透射。图 5(c) 示意了这一卫星峰来源。

这一解释与统一框架相容。折叠谱设计层决定了不同总阶在单自由光谱范围内的排布，而空间模式误差则决定了各个总阶上到底有多少可被腔选择出来的权重。因而，频谱主峰位置、容量边界与寄生卫星峰可以在同一个物理框架下被同时理解。

---

## 5 讨论与结论

本文从有效归一化 Gouy 步长 \(k_{\mathrm{eff}}\) 出发，建立了适用于稳定双镜 FP 腔的 LG 模式分束统一框架。与具体平凹推导相比，这一写法的关键优势在于把模式排布问题与几何实现问题分开：单自由光谱范围内的折叠谱设计、最小间距与容量条件由 \(k_{\mathrm{eff}}\) 统一控制，而不同腔型只通过几何回代关系影响实际实现方式与鲁棒性排序。

在此基础上，本文进一步说明了连续目标集最小间距景观的算术来源。景观中的层级细化并非模糊的“分形感”，而可更严格地理解为由 Farey 邻分数骨架组织的下包络细化结构。该结论的物理意义在于：目标模式数的增加不会任意改写全局设计图景，而是在既有粗轮廓下方逐步加入更高阶差值约束。这为理解解析最优分支、局部峰值位置和景观嵌套关系提供了统一语言。

最后，本文把模式分束设计与误差机理重新接通。解析和数值结果共同表明，在保持圆对称的误差条件下，首要问题不是角向混模，而是同一 \(l\) 子空间内的径向寄生分量，其中 \(p=1\) 是首要可观测项；只有在横向偏移、倾斜或其他破坏对称性的误差参与时，other-\(l\) 分量才会显著上升。由此得到的卫星峰解释与现有实验频谱现象是一致的，也提示后续实验优化应同时关注两条路线：其一是通过构型选择和分支选择优化 \(k_{\mathrm{eff}}\) 工作点的几何鲁棒性，其二是通过改善空间模式匹配降低轴对称失配引起的径向寄生项。

综上，稳定双镜 FP 腔中的 LG 模式分束可由“统一步长设计 + 几何回代 + 误差分类”三层结构共同描述。该框架不仅适用于平凹腔，也适用于对称双凹腔与一般稳定两镜腔，并为后续高维空间模式器件的结构设计与误差诊断提供了更统一的理论基础。

---

## 图题

**图 1 稳定双镜 FP 腔中 LG 模式分束的统一折叠谱框架。** (a) FP 腔通过 Gouy 相位依赖共振实现横模选择，并在理想情况下保持透射横向场结构。(b) 横模共振位置可折叠到单自由光谱范围内的圆周上；折叠谱排布、最小间距和容量条件由有效归一化 Gouy 步长 \(k_{\mathrm{eff}}\) 决定。平凹腔与对称双凹腔的差异体现为 \(k_{\mathrm{eff}}\) 到 \(L/R\) 的不同几何回代关系。

**Fig. 1 Unified folded-spectrum framework for LG mode sorting in stable two-mirror FP cavities.** (a) Gouy-phase-dependent resonance enables transverse-mode selection while preserving the transmitted field profile. (b) Transverse-mode resonances are folded into one free spectral range on a circle. The folded arrangement, minimum spacing, and capacity condition are governed by the effective normalized Gouy step \(k_{\mathrm{eff}}\), whereas different cavity geometries enter through different back-substitution relations between \(k_{\mathrm{eff}}\) and \(L/R\).

**图 2 连续目标集最小间距景观的 Farey 骨架与层级细化。** (a) \(s_{\min}(k)\) 可视为若干锯齿函数的下包络，其局部峰由 Farey 邻分数区间组织。(b) 随目标模式数 \(M\) 增大，新的差值约束在原有粗轮廓下方继续切出细结构，形成层级细化而非严格自相似分形。

**Fig. 2 Farey skeleton and hierarchical refinement of the minimum-spacing landscape for consecutive target sets.** (a) The landscape \(s_{\min}(k)\) is the lower envelope of sawtooth constraints and is organized by neighboring Farey fractions. (b) Increasing the target-mode number introduces additional difference constraints below the previous envelope, producing hierarchical refinement rather than strict self-similar fractality.

**图 3 平凹腔与对称双凹腔的几何映射及 \(M=9\) 鲁棒分支比较。** (a) 平凹腔和对称双凹腔具有不同的 \(k_{\mathrm{eff}}\)-\(L/R\) 映射，对称双凹腔不能由平凹腔作 \(L\rightarrow2L\) 得到。(b) 对于 \(M=9\) 连续模式集，平凹腔的鲁棒代表支为 \(m=2\)，而对称双凹腔中更鲁棒的代表支转移到 \(m=4\)。

**Fig. 3 Geometry mapping and robustness comparison between plane-concave and symmetric double-concave cavities for \(M=9\).** (a) The two cavity types have different mappings between \(k_{\mathrm{eff}}\) and \(L/R\); the symmetric double-concave result is not obtained by the substitution \(L\rightarrow2L\). (b) For nine consecutive modes, the most robust representative branch is \(m=2\) in a plane-concave cavity and shifts to \(m=4\) in a symmetric double-concave cavity.

**图 4 轴对称束腰失配下的径向寄生项增长。** 对 \(l=0,4,8\) 的输入 \(LG_0^l\) 模式，束腰比 \(\eta=w_{\mathrm{in}}/w_0\) 偏离 1 时，功率主要从 \(p=0\) 泄漏到同一 \(l\) 子空间内的 \(p=1\) 分量，\(p\ge2\) 项在轻微失配下保持较低水平。

**Fig. 4 Growth of parasitic radial components under axisymmetric waist mismatch.** For input \(LG_0^l\) modes with \(l=0,4,8\), a waist-ratio mismatch \(\eta=w_{\mathrm{in}}/w_0\neq1\) mainly transfers power from \(p=0\) to the \(p=1\) component within the same \(l\) subspace, while \(p\ge2\) terms remain much weaker under mild mismatch.

**图 5 误差分类与卫星峰来源。** (a) 轴对称失配主要增加同一 \(l\) 子空间内的 \(p=1\) 径向分量。(b) 横向偏移和相位倾斜等破坏圆对称的误差会显著引入 other-\(l\) 分量。(c) 卫星峰可由腔模基中的 \(p>0\) 径向寄生项解释，例如 \(LG_1^4\) 与 \(LG_0^6\) 具有相同总阶 \(N=7\)。

**Fig. 5 Error classification and origin of satellite peaks.** (a) Axisymmetric mismatch mainly enhances the \(p=1\) radial component within the same \(l\) subspace. (b) Symmetry-breaking errors such as lateral displacement and phase tilt generate appreciable other-\(l\) components. (c) Satellite peaks can arise from parasitic \(p>0\) components in the cavity-mode basis; for example, \(LG_1^4\) and \(LG_0^6\) share the same transverse order \(N=7\).

## 参考文献

[1] Allen L, Beijersbergen M W, Spreeuw R J C, et al. Orbital angular momentum of light and the transformation of Laguerre-Gaussian laser modes[J]. Physical Review A, 1992, 45(11): 8185-8189.

[2] Shen Y, Wang X, Xie Z, et al. Optical vortices 30 years on: OAM manipulation from topological charge to multiple singularities[J]. Light: Science & Applications, 2019, 8: 90.

[3] Gibson G, Courtial J, Padgett M J, et al. Free-space information transfer using light beams carrying orbital angular momentum[J]. Optics Express, 2004, 12(22): 5448-5456.

[4] Wang J, Yang J Y, Fazal I M, et al. Terabit free-space data transmission employing orbital angular momentum multiplexing[J]. Nature Photonics, 2012, 6(7): 488-496.

[5] Bozinovic N, Yue Y, Ren Y, et al. Terabit-scale orbital angular momentum mode division multiplexing in fibers[J]. Science, 2013, 340(6140): 1545-1548.

[6] Erhard M, Krenn M, Zeilinger A. Advances in high-dimensional quantum entanglement[J]. Nature Reviews Physics, 2020, 2(7): 365-381.

[7] Leach J, Padgett M J, Barnett S M, et al. Measuring the orbital angular momentum of a single photon[J]. Physical Review Letters, 2002, 88(25): 257901.

[8] Berkhout G C G, Lavery M P J, Courtial J, et al. Efficient sorting of orbital angular momentum states of light[J]. Physical Review Letters, 2010, 105(15): 153601.

[9] Mirhosseini M, Malik M, Shi Z, et al. Efficient separation of the orbital angular momentum eigenstates of light[J]. Nature Communications, 2013, 4: 2781.

[10] Labroille G, Denolle B, Jian P, et al. Efficient and mode selective spatial mode multiplexer based on multi-plane light conversion[J]. Optics Express, 2014, 22(13): 15599-15607.

[11] Fontaine N K, Ryf R, Chen H, et al. Laguerre-Gaussian mode sorter[J]. Nature Communications, 2019, 10: 1865.

[12] Brandt F, Hiekkamaki M, Bouchard F, et al. High-dimensional quantum gates using full-field spatial modes of photons[J]. Optica, 2020, 7(2): 98-107.

[13] Kogelnik H, Li T. Laser beams and resonators[J]. Applied Optics, 1966, 5(10): 1550-1567.

[14] Siegman A E. Lasers[M]. Sausalito: University Science Books, 1986.

[15] Wei S, Earl S K, Lin J, et al. Active sorting of orbital angular momentum states of light with a cascaded tunable resonator[J]. Light: Science & Applications, 2020, 9: 10.

[16] Vanani F G, Fardoost A, Zhang Y, et al. Low-crosstalk mode-group demultiplexers based on Fabry-Perot thin-film filters[J]. Optics Express, 2022, 30(22): 39258-39268.

[17] Yang Y F, Chen M Y, Li F P, et al. Scalable cyclic transformation of orbital angular momentum modes based on a nonreciprocal Mach-Zehnder interferometer[J]. Photonics Research, 2024, 12(10): 2249-2256.
