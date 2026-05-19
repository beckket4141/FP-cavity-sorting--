# OE 主文离散分支最终收口口径

这份文档的任务只有一个：

> 把当前这条“离散模式集合 + 有限 `(q,m)` 精确搜索”的研究线，收束成适合 OE 主文与附录使用的最终口径。

这里不再继续往更深的一般数学结构硬推，也不再把已经得到的精确结果写弱成“电脑会搜”。

当前最稳、最适合 OE 的收口原则是：

- 主文停在 **exact finite rational search over `(q,m)`**
- 固定 `q` 的逆元壳层判据可作为**附录补强**
- `q>D_max` 的补集层剪枝可作为**附录里的当前例子强化说明**
- 不把这些结果写成“已经得到普适闭式最优分母理论”

---

## 1. 当前最稳的贡献层级

### 第一层：主文核心贡献

这层是最适合放在主文正面叙事里的：

1. 用 `spectral folding + circular model` 把问题转成圆周上模式位置分离问题；
2. 用 `s_{ij}, s_min, tau_{ij}, tau_min` 建立几何量与性能指标之间的联系；
3. 对连续满载模式集给出闭式最优解；
4. 对一般离散模式集，把原本的连续扫描问题严格降为**有限有理候选 `(q,m)` 的精确搜索问题**。

这已经足够完整，也最符合 optics 设计论文的主叙事。

### 第二层：附录增强贡献

这层可以放进附录，但不建议挤进主文中心位置：

1. 固定 `q` 时，`rho_q(m)` 可精确改写为差分残基集合第一次命中分支 `m` 的逆元壳层的层号；
2. 因而可快速判定某个分母在当前窗口里是“只能到 `1/q`”还是“已经存在 `>=2/q` 的更优分支”；
3. 对当前 12 模例子，`q>D_max` 时还可进一步用补集层判据说明：所有大分母 admissible 分支都只会在第一层或第二层命中差分集，因此不可能打过 `q=29`。

这层是很好的附录亮点，但已经开始带出数论/组合结构味道，不宜反客为主。

### 第三层：不建议再继续作为当前 OE 主线推进

下面这些方向可以保留为 thesis 深化或后续独立研究，但不应继续拖当前主文：

1. 普适闭式 `q=f(S)`；
2. 普适高阶 branch-invariant 条件；
3. 更细的 residue/shell taxonomy；
4. 对所有有限集合统一成立的更深层 closed-form 结构。

---

## 2. 主文一句话版

如果主文里只保留一句最核心、最稳的表述，建议写成：

> For a general discrete mode set, the minimum-separation optimization is no longer a one-step closed-form problem as in the continuously filled case, but it can still be reduced exactly to a finite comparison over rational candidates `k=m/q` within the prescribed geometry window. For the present 12-mode example, this exact finite search yields the optimum `k^*=7/29`.

如果要写中文工作口径，可对应为：

> 对一般离散模式集合，最小间距优化虽不再具有连续满载情形中的一步闭式解，但仍可在给定几何窗口内严格降为有限有理候选 `k=m/q` 的精确比较问题；对当前 12 模例子，该精确搜索给出的最优工作点为 `k^*=7/29`。

这句话的优点是：

- 强于“数值扫描”；
- 但不越界到“已经有一般解析闭式”；
- 还能自然和连续满载分支形成对照。

---

## 3. 正文短段版

如果主文正文需要一小段把离散分支讲完整，建议用下面这版逻辑。

### 推荐正文段落版

> For the continuously filled mode family considered above, the optimal geometry can be obtained in closed form. For a general discrete mode set, such a one-step expression is no longer guaranteed. However, the problem does not fall back to a black-box real-variable sweep: the minimum circular separation can be written in terms of the mode-difference set, and within a rational geometry window the global optimum is attained by a rational point `k=m/q` whose denominator is bounded explicitly. Therefore the continuous design problem can be reduced exactly to a finite search over admissible rational candidates `(q,m)`. For the present 12-mode set `[1,4,6,10,15,18,22,27,31,37,40,46]` in the moderate branch window `k in [0.2,0.3]`, this exact search gives `q^*=29`, with the representative optimum chosen as `k^*=7/29`, corresponding to `(L/R)^*≈0.4729` and `s_min^*=1/29`.

### 中文工作版

> 对前文连续满载模式集，最优几何可由闭式公式直接给出。对于一般离散模式集合，这种一步闭式表达不再自动成立。然而，该问题也并未退化为黑箱连续扫参：最小圆周间距可完全由差分集合决定，而在有理几何窗口内，全局最优点必可在某个有理点 `k=m/q` 处取得，且其分母存在显式上界。因此，原本的连续设计问题可以严格降为对 admissible 有理候选 `(q,m)` 的有限精确搜索。对当前 12 模集合 `[1,4,6,10,15,18,22,27,31,37,40,46]`，在适中主分支窗口 `k in [0.2,0.3]` 内，该精确搜索给出 `q^*=29`；结合工程上优先中等几何比的选择，代表性最优工作点取为 `k^*=7/29`，对应 `(L/R)^*≈0.4729`，并有 `s_min^*=1/29`。

### 这段正文里最重要的三个点

1. 先承认：离散情形不再有连续满载式的一步闭式；
2. 再强调：但它也不是黑箱扫参，而是 exact finite rational search；
3. 最后落到当前例子的具体结果。

---

## 4. 附录补强版

附录里最值得保留的不是把全部结构分析都塞进去，而是保留一条“够短、够硬、够能支撑主文”的命题链。

### 附录命题链建议

1. **命题 A：差分集合约化**
   `s_min(k;S)=min_{d in D(S)} ||dk||`

2. **定理 B：有理窗口内最优点必可有理化，且分母有显式上界**
   从而连续问题严格降为有限 `(q,m)` 精确搜索

3. **命题 C：固定 `q` 的逆元壳层判据**
   `rho_q(m)` 等于差分残基集合第一次命中逆元壳层的层号

4. **推论 D：当前例子中的大分母补集层剪枝**
   对 `q>D_max`，若第一层投影已在差分补集之外，则该分支停在 `1/q`；
   若第一层落在补集内，则至多提升到第二层；
   当前例子里第二层补集空缺从未出现，因此大分母尾部不可能超过 `q=29`

### 附录最建议保留的两句总结

> The exact finite `(q,m)` search is the main discrete-design conclusion. The inverse-shell and complement-layer observations are included only as structural refinements that explain why certain denominators are immediately limited to `1/q`, whereas others admit a `2/q` branch but still cannot overtake the optimum at `q=29` in the present example.

中文工作版：

> 本附录的主结论仍是有限 `(q,m)` 精确搜索；逆元壳层与补集层结果仅作为结构性补强，用于解释为何某些分母在当前窗口中立即被限制在 `1/q`，而另一些分母虽允许 `2/q` 分支，却仍无法在当前例子中超过 `q=29` 的最优值。

---

## 5. `q=29` 与 `q=73` 在主文和附录里的不同写法

### `q=29` 应该怎么写

`q=29` 是当前例子的漂亮结构，可以写成当前例子的亮点，但不要把它上纲成一般定理。

推荐口径：

> In the present example, the exact search identifies `q=29` as the optimal denominator. Within the admissible moderate-branch window, three branches, `6/29`, `7/29`, and `8/29`, attain the same minimum spacing `1/29`; `7/29` is selected as the representative operating point because it is closest to the preferred geometry ratio `(L/R)≈0.5`.

### `q=73` 应该怎么写

`q=73` 的价值是**约束口径**，不是占主文篇幅。

推荐只在附录或内部说明里写成：

> The `q=73` case shows that branch invariance is not generic: although most admissible branches remain limited to `1/q`, a single branch survives the first inverse shell and reaches `2/q`. This example is useful as a counterexample to over-strong claims, but it is not needed in the main narrative.

也就是说：

- `q=29` 可以作为当前例子的正面亮点；
- `q=73` 更适合作为“不要写过头”的内部边界控制器。

---

## 6. 主文明确不要写过头的话

下面这些句子现在都不建议写：

1. “我们已经得到一般离散模式集合的统一闭式最优分母公式 `q=f(S)`”
2. “固定 `q` 后，`m` 一般不再重要”
3. “一般离散模式集合已经像连续满载情形一样有一步解析解”
4. “本文已经建立了对任意有限集合都成立的更深一般数学结构”
5. “当前方法本质上只是数值扫参”

这五类说法要么太强，要么太弱，都不适合现在的真实进度。

---

## 7. 当前最推荐的强度边界

如果要用一句话概括现在最合适的强度边界，我建议写成：

> The discrete branch is stronger than a heuristic scan, because it is an exact finite rational search with an explicit denominator bound; but it is weaker than a general closed-form theory, because the branch dependence on `m` remains essential in general.

中文工作版：

> 离散分支的理论强度高于启发式扫描，因为它已经是一个带显式分母上界的有限有理精确搜索问题；但它又弱于一般闭式理论，因为在一般情况下，分支参数 `m` 仍然具有本质作用。

这句话基本就是当前最好、最稳的总口径。

---

## 8. 建议放置方式

### 主文

主文建议只保留：

1. 一句连续满载有闭式解；
2. 一句一般离散集可降为 exact finite rational search；
3. 当前 12 模例子的结果 `q^*=29, k^*=7/29, s_min^*=1/29`；
4. `tau_0=3` 与 `tau_0=5` 的工程结果。

### 附录

附录建议保留：

1. 差分集合约化；
2. 分母上界与有限 `(q,m)` 精确搜索；
3. 逆元壳层判据；
4. 大分母补集层剪枝；
5. `q=73` 作为不要过度声称 branch-invariant 的反例。

### thesis / 内部笔记

剩余更细的 shell/residue 分类研究都可以保留到 thesis 或内部材料，不必强行进入当前 OE 主文。

---

## 9. 最终推荐口径

如果现在就要确定 OE 版本的最终收口，我建议用下面这句作为总纲：

> 对一般离散模式集合，最小间距优化问题不再具有连续满载情形中的一步闭式解，但它仍可在给定几何窗口内严格降为带显式分母上界的有限有理候选 `(q,m)` 精确搜索；对当前 12 模例子，该精确搜索给出最优分母 `q^*=29`，并在适中主分支内选取代表性工作点 `k^*=7/29`。固定分母下的逆元壳层与大分母补集层结果可作为附录补强，用于解释为何某些分母只能达到 `1/q`，而大分母尾部即便出现 `2/q` 分支，也仍无法超过当前最优值。`

我认为这就是现在最适合作为 OE 主文收口的版本。
