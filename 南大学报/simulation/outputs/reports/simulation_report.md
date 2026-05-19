# 南大学报一般稳定 FP 腔理论仿真报告

## 定稿口径

- 本文主变量采用横向总阶 `N=2p+|l|+1`，OAM 只是 `N` 序列的物理特例。
- 单个各向同性 FP 腔按总阶 `N` 分选，不能单独区分 `+l` 与 `-l`。
- 响应串扰分析是理论闭环的一部分，不是附加图；主模型采用周期 Airy 核。
- 对称双凹腔不是平凹腔作 `L -> 2L`，小几何比增强因子趋近 `sqrt(2)`。
- 连续集容量界与 Airy 串扰只依赖 `k_eff` 和 finesse，腔型只改变几何回代与鲁棒性排序。

## 关键数值核对

- 一般腔几何回代最大误差：`2.498e-16`。
- M=9、F=32.21、k=2/9 时，有限维 Airy 参考 `ER_sum=12.0404 dB`，`eta=94.1166%`。
- 同一条件下条件概率矩阵列和最大误差：`2.220e-16`。
- tau0=3 的大 M 极限：`ER_sum=10.4693 dB`，`eta=91.7635%`。
- 连续集 M=2..50 的解析最优 `s_min=1/M` 最大误差：`2.907e-15`。
- `k` 与 `1-k` 的距离矩阵最大差异：`1.998e-15`。
- 一般非连续示例最优点：`k=7/29`，`s_min=0.03448276`，`F_min(tau0=3)=87.0000`。
- OAM 边界：An isotropic FP cavity depends on N=2p+|l|+1 and cannot distinguish +l from -l by itself.
- 径向寄生示例：`|l|=8, eta=0.95` 时 `p=1` 权重约 `2.308%`。

## 主图与数据

- 图1 `fig01_general_cavity_framework.png/.pdf`：一般稳定腔统一 k_eff 框架与平凹/双凹/非对称腔回代。数据源：`general_cavity_mapping.csv, general_cavity_backsubstitution_checks.csv`。
- 图2 `fig02_continuous_N_landscape.png/.pdf`：连续 N 集合的 s_min 景观与解析最优分支。数据源：`continuous_N_smin_landscape.csv, continuous_N_optimal_branches.csv`。
- 图3 `fig03_airy_response_matrix.png/.pdf`：周期 Airy 原始响应矩阵与条件概率矩阵。数据源：`continuous_M9_raw_airy_response_matrix.csv, continuous_M9_condition_probability_matrix.csv`。
- 图4 `fig04_capacity_performance.png/.pdf`：容量边界与有限维 Airy 成功率。数据源：`continuous_capacity_boundary.csv`。
- 图5 `fig05_oam_special_case_errors.png/.pdf`：OAM 特例、signed-OAM 退化与径向寄生峰来源。数据源：`oam_as_N_special_case.csv, radial_waist_mismatch_scan.csv`。

## 正文可用结论

1. 稳定两镜 FP 腔的分选设计可分为两层：折叠谱层只依赖 `k_eff`，几何实现层由具体腔型给出回代关系。
2. 对连续总阶集合 `S_M={1,...,M}`，最优条件为 `k*=m/M` 且 `gcd(m,M)=1`，此时 `s_min=1/M`。
3. 周期 Airy 响应矩阵把几何间距直接转化为条件概率矩阵，因此 `eta_sort` 和 `ER_sum` 是设计理论的自然输出。
4. 容量边界 `M <= floor(F/tau0)` 来自 `tau_min=F*s_min` 与 `s_min<=1/M`，不依赖平凹腔这一特定构型。
5. 平凹和对称双凹在相同 `k_eff` 下具有相同谱排布与串扰矩阵，但对应几何点和鲁棒性排序不同；M=9 时平凹偏向 `m=2`，对称双凹偏向 `m=4`。
6. 对一般非连续总阶集合，最优 `k` 可在有限有理候选中精确搜索；这部分适合作为方法扩展或附录，不必抢主线。
7. OAM 连续分选应表述为 `p=0` 单符号 OAM 集合的总阶连续特例；径向寄生峰则用相同 `N` 的模式简并解释。
