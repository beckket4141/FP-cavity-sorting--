# OE 审稿预案库最终执行计划

## Summary

当前阶段继续定位为“审稿前预演与证据库建设”，不修改 OE 正文或补充材料。目标是把潜在审稿质疑整理成可检索、可复现、可快速抽取的 issue cards，并配套数据溯源表和回应句库。

执行顺序固定为：先建总目录 → 建数据溯源表 → 写 P0/P1/P2 issue cards → 汇总 rebuttal snippets。

## Deliverables

- `review_response_readiness_index.md`
  - 总目录、优先级、状态、对应 Major/Minor Comment、关联 issue。
  - 增加 `Open decisions` 区域：
    - errorbar 默认改表述不重画；若审稿人坚持 95% CI，则 t-based 重算重画。
    - high-\(l\) SNR 是否补 dark noise / background 测量。
    - sorter 概念图是否现在画，或等审稿意见回来再画。
  - 增加审稿意见回来后的映射流程。

- `data_provenance_map.md`
  - 集中数据速查表。
  - 每行包含：关键数值、数值、来源文件、sheet/行或段落、生成脚本、用于哪个 issue。
  - 必含：
    - 93.19% combined diagonal share。
    - 10.66 dB min ER at \(l=7\)。
    - condition numbers 5.05/4.99/5.43。
    - seven NNLS zero positions。
    - 0.1%/0.2% floor sensitivity。
    - transmittance \(l=0\ldots8\) trend。
    - \(\tau_0=3\)、10.47 dB、12.04 dB 的理论来源。

- `issue_*.md`
  - P0/P1 完整卡使用统一模板。
  - P2 轻量卡可缩写，至少保留 `Risk level`、`Evidence`、`Safe wording`、`If reviewer pushes harder`。
  - 每张卡都标 `Can claim / Can cautiously say / Should not claim`。

- `rebuttal_snippets_bank.md`
  - 从各 issue card 汇总英文短段。
  - 每段标注适用 issue、风险等级、是否可直接用于 response letter、是否需要配表/图。

- `figure_preparation_notes.md`
  - 只列图件方案，不立即改稿。
  - 包含 sorter 概念图、raw/S/corrected 三联图、floor sensitivity 图/表、\(\tau_0\) 设计阈值表。

## Priority And Cards

### P0

- **G. Single FP module vs multiport sorter**
  - 对应 Major Comment 1。
  - 准备 single-module 与 cascaded multiport 的边界说明。
  - 标注建议配图：single FP module vs cascaded sorter。

- **H. Transverse-order degeneracy**
  - 对应 Major Comment 2。
  - 说明 FP 腔按 \(N=2p+|l|+1\) 区分 transverse order。
  - 明确 \(\pm l\) 和同 \(N\) 模式简并；实验 \(p=0,l=0\ldots8\) 中 \(N\) 一一对应。

- **A. NNLS zero boundary**
  - 已有计算基础。
  - 重点：raw 非零、LS 小负值、NNLS 边界解、floor sensitivity 不改变 ER。

- **C. Raw vs corrected response**
  - 与 A 互引但不合并。
  - 重点：raw matrix 是 detector-side readout，corrected matrix 是 de-embedded cavity-output estimate。

- **B. Errorbar statistics**
  - 默认策略：预案阶段不重画图，准备将 `95% CI` 改成 `mean ± 1.96 SEM` 的表述方案。
  - 退路：审稿人坚持则 t-based 95% CI 重算并重画。

### P1

- **I. State-preservation evidence boundary**
  - 对应 Major Comment 4。
  - 区分 CCD intensity profile、线性 FP 机制支持、完整复振幅未直接测量。

- **F. Capacity bound, \(\tau_0\), and theory-experiment gap**
  - 卡内拆三节：
    - F1 arbitrary finite target sets：upper bound vs attainable optimum。
    - F2 \(\tau_0=3\)：设计阈值与容量 scaling。
    - F3 finite-\(M\) Airy reference：12.04 dB 是模型内 reference，不包含全部实验非理想。
  - 对应 Major Comments 3、6、7。

- **D. High-\(l\) readout SNR**
  - 当前证据：\(S_{88}=3.79\%\)、\(\kappa(S)\approx5\)、重复测量稳定。
  - 缺口：dark noise、background-only、power meter noise floor。
  - 在 `Open decisions` 中保留是否补测的决策项。

- **J. Data/package readiness**
  - 从 P2 提到 P1。
  - 准备最小数据包清单：关键 Excel、脚本、图件生成说明、README。
  - 不一定现在打包上传，但要能快速打包。

### P2

- **E. \(l=8\) ER slightly higher than \(l=7\)**
  - 轻量卡。
  - 说明局部非单调、差异小、run-to-run variation 内，不影响所有通道高于 bound。

## Execution Order

1. 创建 `review_response_readiness_index.md` 骨架。
2. 创建 `data_provenance_map.md`，先填已知核心数值和生成脚本。
3. 写 P0 cards：G、H、A、C、B。
4. 写 P1 cards：I、F、D、J。
5. 写 P2 card：E。
6. 汇总 `rebuttal_snippets_bank.md`。
7. 写 `figure_preparation_notes.md`。
8. 做一次一致性检查：
   - issue 间 claim 不冲突。
   - 所有数值能追溯到数据地图。
   - 所有缺数据点都进入 `Should not claim` 或 `Open decisions`。

## Quality Gates

- 不改 `main.tex` / `supplement.tex`。
- 不把 rebuttal 腔写进正文。
- 所有 P0/P1 cards 必须包含退路方案。
- 数据地图必须同时包含来源文件和生成脚本。
- Open decisions 必须明确默认方案和触发替代方案的条件。
- A/C/G/H/I/F 的边界口径必须统一：single module、distinct transverse orders、profile preservation、capacity upper bound、response-corrected estimate。
