# tau 到性能指标的重新推演

这组脚本的目标是把第五章里已经稳定的 `tau -> ER` 判据，进一步扩展成一条可验证的 sorter 指标链：

`tau_{ij} -> Lorentz kernel K_{ij} -> P(\hat i|j) -> eta_sort / e_sort -> I(l;\hat l)`

## 当前定位与正文口径

当前这一版应视为 **第五章新指标接口的基线模型**，而不是最终物理模型。它的任务是验证：

- `tau -> P(\hat i|j)` 这条链在数量级和结构上是走得通的；
- 第五章可以把 `P(\hat l|l)`、`eta_sort`、`e_sort` 作为正文主结果语言；
- `I(l;\hat l)` 可以作为次级加分指标保留；
- `tau_eff` 继续负责容量边界、阈值线和保守判据，`tau_{ij}` 负责逐通道矩阵近似。

这里有一个最重要的约束需要先说清楚：

- **整张条件概率矩阵不能只靠单个 `tau_eff` 生成。**
- `tau_eff` 仍然非常重要，但它只负责给出全局容量边界、平台可行性和保守下界。
- 如果要生成 `P(\hat i|j)` 这类逐通道矩阵，必须回到全体模式对的微观分辨率 `tau_{ij} = F * s_{ij}`。

也就是说，第五章以后如果要改成“双层口径”，最合理的结构是：

- `tau_eff`：负责 `N_max`、阈值线、平台裕度、保守 ER 下界。
- `tau_{ij}`：负责构造近似条件概率矩阵，并进一步导出 `eta_sort`、`e_sort` 和互信息。

## 本版基线假设

本目录当前封版采用以下假设，正文接入时应原样说明：

- 条件概率矩阵采用 **de-embedded-FP 口径**，只描述 FP 腔本体在 `p=0` 投影子空间下的有效分选矩阵。
- 逐模式泄漏采用洛伦兹核近似：`K_ij = 1 / (1 + 4 * tau_ij^2)`。
- 本版 **不引入检测端权重**，也 **不做 Airy 周期修正**。
- 实验矩阵采用逐列归一化后的条件概率口径，即每一列满足 `sum_i P(\hat i|j) = 1`。
- 如果后续引入 Airy 核、检测权重或不确定度传播，应视为“模型增强”，而非本版成立性的前提。

## 数据源

默认实验数据目录：

- [triplicate_full9_aggregate.xlsx](D:/自制软件/thesis/数据内容/对比度数据/最终数据/triplicate_full9_aggregate.xlsx)
- [1/full9_matrix_with_uncertainty.xlsx](D:/自制软件/thesis/数据内容/对比度数据/最终数据/1/full9_matrix_with_uncertainty.xlsx)
- [2/full9_matrix_with_uncertainty.xlsx](D:/自制软件/thesis/数据内容/对比度数据/最终数据/2/full9_matrix_with_uncertainty.xlsx)
- [3/full9_matrix_with_uncertainty.xlsx](D:/自制软件/thesis/数据内容/对比度数据/最终数据/3/full9_matrix_with_uncertainty.xlsx)

默认参数：

- `F_exp = 31.35`
- `L = 10.25 mm`
- `R = 25.0 mm`
- `l = 0..8`

其中 `F_exp = 31.35` 的口径来自 [CLAUDE.md](D:/自制软件/thesis/CLAUDE.md) 中的说明：`F=29.80（名义），F_exp=31.35（实测）`。

## 模型定义

模式集合为 `l = 0..8`，对应总阶数 `N = l + 1`。几何位置和分辨率按第五章当前主线定义：

```text
k = (1/pi) * arccos(sqrt(1 - L/R))
pos(l) = (l * k) mod 1
s_ij = min(|pos(i)-pos(j)|, 1-|pos(i)-pos(j)|)
tau_ij = F * s_ij
```

第一版只使用洛伦兹核，不混入检测端权重，也不做 Airy 修正：

```text
K_jj = 1
K_ij = 1 / (1 + 4 * tau_ij^2),   i != j
P(î=i | j) = K_ij / sum_m K_mj
```

这对应的是 **de-embedded-FP 口径**：只描述 FP 腔本体在 `p=0` 投影子空间下的近似分选矩阵，不混入 SLM/SMF 链路响应不均匀性。

## 脚本说明

### 1. `01_tau_kernel_to_probability_matrix.py`

从 `L`、`R`、`F_exp` 和 `l=0..8` 出发，计算：

- `k`
- `pos(N)`
- `s_ij`
- `tau_ij`
- 洛伦兹核 `K_ij`
- 理论条件概率矩阵 `P_th(\hat i|j)`

输出：

- `tau_pairwise_table.csv`
- `theory_probability_matrix.csv`
- `theory_summary.txt`

### 2. `02_compare_theory_matrix_with_experiment.py`

读取 `01` 的理论矩阵，与最终实验数据做逐元素比较。

主对比对象是 `triplicate_full9_aggregate.xlsx` 的 `combined_percentage` sheet；另外会读取 `1/2/3/full9_matrix_with_uncertainty.xlsx` 的 `mean` sheet 并逐列归一化，作为重复性验证。

输出：

- `aggregate_matrix_comparison.csv`
- `per_run_matrix_comparison.csv`
- `comparison_summary.txt`

关键统计量：

- `matrix_MAE_pp`
- `diag_MAE_pp`
- `offdiag_MAE_pp`
- `top1_match`
- `top2_match`

### 3. `03_tau_to_eta_esort_mutualinfo.py`

从理论矩阵和实验矩阵分别导出：

- `eta_sort`
- `e_sort,j`
- 平均 `e_sort`
- `ER_sum` / `ER_max` 的矩阵反推值
- `I(l;\hat l)`，默认采用等先验输入分布

同时会把矩阵重算得到的 `ER_sum` / `ER_max` 与 `ER_summary` sheet 中的聚合结果做一致性核对。

输出：

- `theory_metrics.csv`
- `experiment_metrics.csv`
- `metrics_comparison.txt`

### 4. `04_export_ch05_figures.py`

将当前基线结果直接导出为第五章可复用图件：

- `tau_metric_chain.pdf`
- `theory_experiment_probability_matrix.pdf`

## 运行顺序

在当前目录执行：

```powershell
python .\01_tau_kernel_to_probability_matrix.py
python .\02_compare_theory_matrix_with_experiment.py
python .\03_tau_to_eta_esort_mutualinfo.py
python .\04_export_ch05_figures.py
```

## 当前基准结果

使用默认参数和最终三次汇总矩阵，当前这组脚本应复现以下量级：

- `tau_eff = 3.322334`
- `matrix_MAE_pp ≈ 0.44`
- `eta_sort_theory ≈ 94.52%`
- `eta_sort_exp ≈ 93.26%`
- `e_sort_theory ≈ 5.48%`
- `e_sort_exp ≈ 6.74%`
- `I_theory ≈ 2.74 bits`
- `I_exp ≈ 2.65 bits`

此外，`ER_sum` 和 `ER_summary` 的一致性应当非常好；`ER_max` 则可能出现更明显差异。这不是算错，而是因为：

- `ER_summary` 里的 `ER_max_mean_dB` 是先对每次独立实验各自求 `ER_max`，再做 run-to-run 平均；
- 从 `combined_percentage` 回算 `ER_max` 则是先平均矩阵，再取该平均矩阵中的最大串扰通道。

由于 `max()` 是非线性运算，这两条路径本来就不完全等价。

这组结果的意义不是“洛伦兹核已经是终极模型”，而是：

- `tau -> P(\hat i|j)` 这条路在数量级和结构上是走得通的；
- 第五章完全可以把 `eta_sort / e_sort / I(l;\hat l)` 作为最终结果语言；
- 同时仍保留 `tau_eff` 负责容量边界和保守判据。

后续若进入模型增强，优先顺序建议固定为：

1. Airy 核替换。
2. 检测端权重并入。
3. 三次独立实验的不确定度传播。

只有当这些增强明显改善拟合或解释力，且不改变基线结论时，才值得进入正文主线；否则更适合留在附录或展望中。
