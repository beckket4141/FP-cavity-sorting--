# 一般化非连续候选总阶数筛选程序

这个目录只放第五章 §5.4 方法演示需要的程序、配置与输出，不改论文正文，也不覆盖上级目录中已有的实验数据文件。

## 入口

```powershell
python run_generalized_screening.py
```

或指定配置：

```powershell
python run_generalized_screening.py --config .\configs\your_case.json
```

## 默认配置

- 候选总阶数集合：`[1, 4, 6, 10, 15, 18, 22, 27, 31, 37, 40, 46]`
- 物理口径约束：`candidate_modes` 必须是正整数，且每个 `N >= 1`
- `tau_0 = 3`
- `k in [0.01, 0.49]`
- 几何偏好：`L/R` 尽量接近 `0.5`
- 默认硬约束：`|L/R - 0.5| <= 0.12`
- 可行性预算：`feasibility_finesse = 32`
- 物理评估精细度：`F_eval = 32`

## 近优候选层策略

程序保留两层输出：

1. 正文主结果层
- 继续使用“每个 `k` 下的最大可共存子集”
- 再按连续 `k` 区域提取 representative
- 服务于 §5.4 的正文主表和主图

2. 完整/近优候选层
- 在每个 `k` 下额外导出近优可行子集
- 默认阈值：
  `subset_size >= min(max_subset_size, max(near_optimal_min_subset_size, max_subset_size - near_optimal_size_drop))`
- 默认参数：
  `near_optimal_size_drop = 1`
  `near_optimal_min_subset_size = 5`
- 这意味着默认会保留：
  - 所有最大子集
  - 所有只比该 `k` 下最大子集少 1 个模式、且子集规模仍不小于 5 的可行子集

## 主要输出

运行后会在 `.\outputs\<case_name>\` 下生成：

- `main_ranked_solutions.csv`
  正文主结果表
- `all_ranked_solutions.csv`
  与主结果表相同，保留为兼容别名
- `near_optimal_ranked_candidates.csv`
  近优/完整候选结果表
- `screening_summary.xlsx`
  包含主结果、近优结果、landscape、subset regions 四个 sheet
- `search_landscape.csv`
- `subset_regions.csv`
- `best_solution_summary.md`
- `result_readme.md`
- `figures\search_landscape.png`
- `solutions\solution_rankXX_*\`

## 哪些适合正文，哪些适合附录

更适合正文：

- `main_ranked_solutions.csv` 的前几行
- `figures\search_landscape.png`
- 最优解目录中的 `positions_circle.png`
- 最优解目录中的 `condition_probability_heatmap.png`
- 最优解目录中的 `per_mode_metrics.png`

更适合附录/补充材料：

- `near_optimal_ranked_candidates.csv`
- `subset_regions.csv`
- `search_landscape.csv`
- 各代表解目录下的 `pairwise_distances.csv`
- 各代表解目录下的 `raw_response_matrix.csv`
- 各代表解目录下的 `condition_probability_matrix.csv`

## 算法摘要

1. 对每个采样 `k` 计算全部候选模式的归一化位置 `pos(N) = (Nk) mod 1`
2. 计算圆周最短距离 `s_ij`
3. 用 `feasibility_finesse * s_ij < tau_0` 构造冲突图
4. 在共存图上做最大团搜索，得到最大可共存子集
5. 在同一个 `k` 下再导出近优可行子集
6. 对每个子集输出 `s_min`、`F_min`、`ER_sum`、separation efficiency 等指标

## 说明

- `feasibility_finesse` 用于可行性判据
- `F_min = tau_0 / s_min` 永远由几何自动反推
- `F_eval` 只用于物理响应评估
- 当前 `airy_model` 仍默认走 `exact_periodic` 计算口径
