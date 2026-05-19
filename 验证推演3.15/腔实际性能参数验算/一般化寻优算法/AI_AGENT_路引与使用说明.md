# AI Agent 路引与使用说明

这份文档面向后续进入本目录工作的 agent，用来快速回答：

- 这套程序现在做什么
- 默认案例是什么
- 哪些输出适合直接服务第五章 §5.4
- 哪些输出更适合做附录或 trade-off 分析

## 1. 工作边界

当前目录职责：

- 实现“非连续候选总阶数集合”的一般化筛选程序
- 输出结构化结果、图、摘要与逐解数据
- 为第五章 §5.4 提供可复核的素材

当前目录不负责：

- 直接修改 thesis 正文
- 覆盖上级目录中的实验原始数据
- 取代前文连续满载解析分支的主叙事

## 2. 先看哪里

推荐顺序：

1. `README.md`
2. `configs/default_irregular_case.json`
3. `run_generalized_screening.py`
4. `generalized_fp/core.py`
5. `outputs/default_irregular_case/best_solution_summary.md`
6. `outputs/default_irregular_case/main_ranked_solutions.csv`
7. `outputs/default_irregular_case/near_optimal_ranked_candidates.csv`

## 3. 默认案例口径

默认候选总阶数集合：

`[1, 4, 6, 10, 15, 18, 22, 27, 31, 37, 40, 46]`

注意：

- `candidate_modes` 必须是正整数
- 每个 `N >= 1`
- 不允许 `0` 或负数

这条口径已经和论文里 `N = 2p + |l| + 1` 保持一致。

## 4. 两层输出怎么理解

### 4.1 正文主结果层

保留“每个 `k` 下的最大可共存子集”主逻辑，并继续按连续 `k` 区域提 representative。

主要文件：

- `outputs/default_irregular_case/main_ranked_solutions.csv`
- `outputs/default_irregular_case/all_ranked_solutions.csv`
  兼容别名，与上面内容相同
- `outputs/default_irregular_case/subset_regions.csv`
- `outputs/default_irregular_case/figures/search_landscape.png`

这一层适合直接服务第五章 §5.4 的正文写作。

### 4.2 近优/完整候选层

程序现在额外导出 near-optimal feasible subsets，用来做 trade-off 分析。

默认策略：

- 保留所有最大子集
- 额外保留满足
  `subset_size >= min(max_subset_size, max(near_optimal_min_subset_size, max_subset_size - near_optimal_size_drop))`
  的可行子集

默认参数：

- `near_optimal_size_drop = 1`
- `near_optimal_min_subset_size = 5`

主要文件：

- `outputs/default_irregular_case/near_optimal_ranked_candidates.csv`
- `outputs/default_irregular_case/screening_summary.xlsx`

该表中会明确区分：

- `k`
- `subset_modes`
- `subset_size`
- `s_min`
- `F_min`
- `avg_ER_sum_dB`
- `avg_separation_efficiency`
- `is_max_subset_for_k`
- `max_subset_size_for_k`
- `subset_size_gap_to_k_max`
- `k_rank`
- `global_rank`

这一层更适合附录、补充材料和后续筛选 trade-off。

## 5. 核心代码位置

- `generalized_fp/config.py`
  配置解析与输入校验
- `generalized_fp/core.py`
  几何位置、圆周距离、冲突图、最大团、近优候选枚举、指标计算
- `generalized_fp/exporting.py`
  主结果层与近优候选层导出
- `generalized_fp/plotting.py`
  绘图
- `run_generalized_screening.py`
  主入口

## 6. 当前默认案例最值得记住的结果

默认案例当前第一名：

- `k ≈ 0.28072`
- `L/R ≈ 0.59591`
- 最大可共存子集大小：`8`
- 最优子集：`[1,10,18,22,27,31,37,46]`
- `s_min ≈ 0.10488`
- `F_min ≈ 28.60`
- 平均 `ER_sum ≈ 12.71 dB`
- 平均 separation efficiency `≈ 94.88%`

这组默认结果不再回到旧的连续 9 模近邻，更适合当“一般化方法演示”的默认示例。

## 7. 如果要重跑

在本目录执行：

```powershell
python run_generalized_screening.py
```

或：

```powershell
python run_generalized_screening.py --config .\configs\your_case.json
```

程序会清空同名 case 输出目录并重新生成结果。

## 8. 一句话 handoff

这套程序现在已经同时支持：

- 正文主结果层：最大可共存子集
- 近优候选层：用于 trade-off 的可行备选解

要快速上手，先看 `README.md`、`default_irregular_case.json`、`best_solution_summary.md`，再按需看 `main_ranked_solutions.csv` 和 `near_optimal_ranked_candidates.csv`。
