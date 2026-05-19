# simulation 目录说明

本目录集中放置南大学报中文稿的仿真、重绘和补图脚本。当前保留旧版 `build_jns_figures.py`，同时新增一套以横向总阶 `N=2p+|l|+1` 为主变量的一般稳定 FP 腔理论工作流。

## 新版理论工作流

一键生成数据、主图、正文表格和报告：

```powershell
python .\export_jns_tables_and_report.py
```

输出位置：

- `outputs/data/`：所有 CSV/JSON 数据源与矩阵
- `outputs/figures/`：新版 5 张主图的 `.png` 和 `.pdf`
- `outputs/reports/`：正文表格与 `simulation_report.md`

## 新增脚本

- `fp_theory_core.py`
  - 通用公式库：`k_eff`、几何回代、圆周距离、周期 Airy 响应矩阵、条件概率矩阵、性能指标。
- `derive_general_cavity_cases.py`
  - 生成平凹、对称双凹、一般非对称双镜腔的回代核对和鲁棒性表。
- `simulate_continuous_N_sorting.py`
  - 生成连续总阶集合 `S_M={1,...,M}` 的解析最优、容量边界和 M=9 响应矩阵。
- `simulate_general_set_search.py`
  - 对一般有限 `N` 集合做有限有理候选搜索，并输出 Airy 响应矩阵。
- `simulate_oam_special_case_and_errors.py`
  - 生成 `p=0` OAM 特例、`+l/-l` 退化、径向寄生和卫星峰示例。
- `build_jns_theory_figures.py`
  - 根据新版数据生成 5 张理论主图。
- `export_jns_tables_and_report.py`
  - 汇总表格、主图和 `simulation_report.md`。

## 理论口径

- 主变量是横向总阶 `N`，OAM 连续分选只是 `p=0`、单符号 `l` 序列的特例。
- 单个各向同性 FP 腔按 `N=2p+|l|+1` 选择模式，不能单独区分 `+l` 与 `-l`。
- 主响应模型采用周期 Airy 核，不再以 Lorentz 近似作为正文主模型。
- 平凹、对称双凹和一般非对称两镜腔共享同一折叠谱设计层，只在几何回代和鲁棒性排序上不同。
