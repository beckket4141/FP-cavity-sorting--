# 第五章 5.4 论文极简版

这个目录只服务于第五章 `5.4` 的一个小例子：

- 给定随机模式总阶数集合 `[1, 4, 6, 10, 15, 18, 22, 27, 31, 37, 40, 46]`
- 在不再做“选子集”的前提下，要求这 12 个模式整体同时可分辨
- 通过扫描 `k` 与等价的几何比 `L/R = sin^2(pi k)`，寻找使
  `s_min = min_{i!=j} s_ij`
  最大的工作点
- 对给定判据 `tau_0`，输出最小所需精细度
  `F_min = tau_0 / s_min`

这里不再保留：

- 最大团 / 最大独立集选子集
- near-optimal 候选层
- region representative
- 大量 Excel / 图形导出
- 多指标 trade-off 排序

保留的只是第五章 `5.4` 正文真正需要的最小闭环。

## 默认约束

这一版默认直接遵守第五章正文已经写明的“主分支适中取值”口径：

- 默认搜索区间：`k in [0.2, 0.3]`
- 目的：避免 `m=1` 一类使 `k -> 0` 的极端小步长解，也避免靠近 `k -> 0.5` 的近共焦退化区

如果后续你想测试别的“适中几何窗口”，只需改配置文件即可。

## 文件说明

- `minimal_example_config.json`
  场景配置。包含模式集合、`tau` 门槛、搜索参数和可选几何窗口。
- `run_minimal_fullset_search.py`
  极简求解脚本。
- `plot_randomset_smin_landscape.py`
  针对当前随机集合绘制 `s_min` 对 `L/R` 的景观图，并标出最佳工作点。
- `analyze_rational_structure.py`
  扫描有理候选 `m/q`，分析当前随机集合的分母-分支结构。
- `validate_random_rational_pattern.py`
  对随机模式集合批量比较“密集连续搜索”和“有理候选搜索”。
- `exact_qm_search.py`
  利用显式分母上界，在有限 `(q,m)` 集合上做精确搜索。
- `analyze_q_counting_bounds.py`
  计算 `nu_q(S)`、`mu_q(I)` 及其对应的计数型上界/下界。
- `analyze_inverse_shell_criterion.py`
  用“逆元壳层”语言精确重建固定 `q` 下每条 admissible 分支的 `rho_q(m)`，并筛出哪些 `q` 只能给 `1/q`、哪些 `q` 已经存在 `>=2/q` 的候选好分支。
- `analyze_large_q_shadow_screen.py`
  专门研究 `q>D_max` 的大分母区间，把固定分支筛分降到 `[1,D_max]` 上的投影壳层，并检查这些大分母是否还有可能打过当前最优 `q=29`。
- `analyze_large_q_complement_layers.py`
  把 `q>D_max` 的大分母筛分进一步压成“差分补集上的层判据”，精确验证何时 `rho>=2`、何时 `rho>=3`。
- `verify_arithmetic_progression_closed_form.py`
  验证等差模式集 `S_{N_start,\Delta_{ord},M}` 是否继承连续满载的闭式结构，并同时核对完整最优族 `k^*=(n+m/M)/\Delta_{ord}`、最简单代表子族 `k=m/(M\Delta_{ord})` 与 `N_start` 不变性。
- `results/summary.md`
  适合正文或写作笔记直接引用的文字总结。
- `results/tau_results.csv`
  `tau=3` 与 `tau=5` 的最终结果表。
- `results/top_local_optima.csv`
  若干局部优点，便于备查。
- `results/full_scan.csv`
  全扫描结果，便于之后自行画图。
- `results/inverse_shell_criterion/summary.md`
  新增的“逆元壳层判据”摘要，说明它如何精确解释 `q=29` 与 `q=73`。
- `results/rational_structure/inverse_shell_note.md`
  可直接供写作或后续 agent 参考的命题/推论版笔记。
- `results/large_q_shadow_screen/summary.md`
  大分母 `q>D_max` 区间的精确筛分结果，给出“为什么大分母打不过 `q=29`”。
- `results/rational_structure/large_q_shadow_note.md`
  对 `q>D_max` 的投影壳层约化命题与当前例子的剪枝结论整理。
- `results/large_q_complement_layers/summary.md`
  大分母补集层判据的验证摘要，说明为什么当前例子里所有大分母分支最多只到第二层。
- `results/rational_structure/large_q_complement_layer_note.md`
  可直接给后续 agent 或写作使用的“补集层判据”版本说明。
- `results/rational_structure/oe_discrete_branch_closure_note.md`
  面向 OE 主文收口的最终口径，包含主文一句话版、正文短段版、附录命题链和明确不能写过头的话。
- `results/rational_structure/arithmetic_progression_step_z_note.md`
  等差模式集 `S_{N_start,\Delta_{ord},M}` 的闭式推广推导，说明何时仍有解析解、何时会被几何窗口打断，以及为什么完整最优族一般大于最简单代表子族。
- `results/arithmetic_progression_closed_form/summary.md`
  对若干 `N_start,\Delta_{ord},M` 例子的数值核对结果，包含完整最优族匹配、最小子族包含关系与 `N_start` 不变性检查。

## 运行方法

在本目录执行：

```powershell
python run_minimal_fullset_search.py
```

画图：

```powershell
python plot_randomset_smin_landscape.py --csv
```

分析分母-分支结构：

```powershell
python analyze_rational_structure.py
```

批量随机验证：

```powershell
python validate_random_rational_pattern.py
```

执行有限 `(q,m)` 精确搜索：

```powershell
python exact_qm_search.py
```

分析 `q` 的计数型上界/下界：

```powershell
python analyze_q_counting_bounds.py
```

分析固定 `q` 下的逆元壳层判据：

```powershell
python analyze_inverse_shell_criterion.py
```

分析 `q>D_max` 的大分母投影壳层筛分：

```powershell
python analyze_large_q_shadow_screen.py
```

分析 `q>D_max` 的补集层判据：

```powershell
python analyze_large_q_complement_layers.py
```

验证等差模式集的闭式推广：

```powershell
python verify_arithmetic_progression_closed_form.py
```

## 口径说明

- 本例的求解对象是无量纲圆周模型，因此核心输出是 `k`、`L/R`、`s_min` 与 `F_min`。
- 配置里保留了 `wavelength_nm = 795` 与 `refractive_index_note`，仅作为第五章场景元信息；本脚本本身不使用它们参与计算。
- 当前默认结果已经施加了“适中主分支”约束，因此主结果不会再落到极端小 `L/R` 位置。
- 若未来需要讨论别的“实用几何窗口”，只需在配置中修改 `k_min` / `k_max` 或加入 `L_over_R_min` / `L_over_R_max` 约束即可，无需恢复旧仓库的复杂结构。
- 对固定 `q`，当前目录现在还额外提供了一条比完整 `(q,m)` 搜索更短的精确筛分规则：若某条 admissible 分支的逆元对 `{±m^{-1}}` 缺位，则立刻知道该分支满足 `s_min>=2/q`；反之若所有 admissible 逆元对都被命中，则该 `q` 在当前窗口里只能给出 `s_min=1/q`。
- 对当前这组 12 模例子，还额外验证了一个更具体的剪枝事实：在全部大分母范围 `46<=q<=90` 内，所有 admissible 分支都只会在第一层或第二层命中差分集，因此这些大分母候选不可能超过已知最优 `q=29`。
- 进一步地，对同一大分母区间，现在还可直接用差分补集做层筛分：`rho>=2` 等价于第一层投影完全落在补集里，`rho>=3` 等价于前两层投影都完全落在补集里；当前例子中第二层补集空缺从未出现。
- 若目标模式集合本身是等差序列 `S_{N_start,\Delta_{ord},M}=\{N_start,N_start+\Delta_{ord},\dots,N_start+(M-1)\Delta_{ord}\}`，则无约束情形下它与连续满载集在圆周模型中完全同构，最优值仍为 `s_min^*=1/M`，完整解析最优族为 `k^*=(n+m/M)/\Delta_{ord}`；其中 `k=m/(M\Delta_{ord})` 只是最简单代表子族。
