# OE 审稿回应预案库总目录

本文档是审稿前预演与证据库的入口。当前阶段只整理潜在审稿质疑、证据链、可用回应和补充材料方案，不直接修改 `main.tex` 或 `supplement.tex`。

## 使用原则

1. 收到真实审稿意见前，不把 rebuttal 防御性话术写进正文。
2. 每条潜在质疑都先归入 issue card，再决定是否需要正文修改、补充材料、图表、数据包或仅在 response letter 中解释。
3. 所有数值引用优先查 `data_provenance_map.md`，再回到原始 Excel、TXT 或脚本。
4. 所有回应都按三类边界管理：`Can claim`、`Can cautiously say`、`Should not claim`。

## Issue 总览

| ID | Priority | Risk | Status | 对应意见 | 主题 | 文件 | 关联 |
|---|---|---|---|---|---|---|---|
| G | P0 | Medium-High | 已用 Wei et al. 前人架构更新，待准备图 | Major 1 | Single FP module vs multiport sorter | `issue_G_sorter_definition_scope.md` | H, F, J |
| H | P0 | High | 已预案 | Major 2 | Transverse-order degeneracy | `issue_H_transverse_order_degeneracy.md` | G, F, I |
| A | P0 | High | 计算完成，卡已整理 | Major 5 | NNLS zero boundary | `issue_A_NNLS_zero_boundary.md` | C, B, D |
| C | P0 | High | 计算完成，卡已整理 | Major 5 / Minor 2 | Raw vs corrected response | `issue_C_raw_vs_corrected_response.md` | A, D, J |
| B | P0 | High | 计算完成，策略待审稿触发 | 数据统计风险 | Errorbar statistics | `issue_B_errorbar_statistics.md` | A, C |
| I | P1 | Medium | 已预案 | Major 4 | State-preservation evidence boundary | `issue_I_state_preservation_boundary.md` | G, H |
| F | P1 | Medium-High | 已预案 | Major 3/6/7 | Capacity bound, \(\tau_0\), theory-experiment gap | `issue_F_capacity_tau0_theory_gap.md` | G, H, E |
| D | P1 | Medium-High | 部分完成，缺噪声底数据 | Major 5 | High-\(l\) readout SNR | `issue_D_high_l_readout_snr.md` | A, C, J |
| J | P1 | Medium | 待打包 | Minor 5 | Data/package readiness | `issue_J_data_package_readiness.md` | all |
| E | P2 | Low-Medium | 已预案 | 数据局部非单调 | \(l=8\) ER slightly higher than \(l=7\) | `issue_E_l8_l7_nonmonotonic.md` | F, D |

## Open Decisions

| Decision | Default | Trigger for alternative | Alternative |
|---|---|---|---|
| Errorbar 策略 | 不重画图；将 `95% CI` 收敛为 `mean ± 1.96 SEM from three independent runs` | 审稿人明确要求严格 95% CI，或编辑要求统计定义一致 | 用 \(t_{0.975,2}=4.303\) 重算并重画 Fig. 5(c,d) |
| High-\(l\) SNR 是否补测 | 暂不补测；用 \(\kappa(S)\approx5\) 和重复测量稳定性作为数值稳健性证据 | 审稿人要求 dark noise / background-only / power meter noise floor | 补测暗噪声、background-only、power meter resolution，并重算高阶读出 SNR |
| Sorter 概念图是否现在画 | 先写 `figure_preparation_notes.md`，不立即出正式图 | 审稿人质疑 single module vs multiport sorter，或返修中决定主动澄清 | 画 single FP module vs cascaded multiport sorter 概念图 |
| 是否改 `main.tex` / `supplement.tex` | 审稿前不改 | 收到审稿意见并完成 issue 映射 | 按需局部修改正文、补充材料或图注 |

## 审稿意见回来后的映射流程

1. 逐条复制审稿意见原文，标注对应 issue ID。
2. 判断每条意见需要的动作类型：`rebuttal only`、`main-text wording`、`supplement clarification`、`figure/table addition`、`new analysis`、`new measurement`、`data package`。
3. 从对应 issue card 抽取 `Current evidence`、`Quantitative result`、`Safe response wording` 和 `If reviewer pushes harder`。
4. 从 `data_provenance_map.md` 查数值来源，必要时重跑对应生成脚本。
5. 组装 response letter，并建立“审稿人意见 -> issue card -> 采取动作 -> 修改位置”的追踪表。
6. 最后才决定是否修改 `main.tex`、`supplement.tex` 或图件。

## 当前证据文件

- `full9_robustness_audit.py`
- `full9_robustness_audit.xlsx`
- `full9_robustness_audit_summary.md`
- `NNLS零值与误差条推演报告.md`
- `data_provenance_map.md`
- `rebuttal_snippets_bank.md`
- `figure_preparation_notes.md`

## 一致性检查清单

- [x] G/H/I/F 中的概念边界一致：single module、distinct transverse orders、profile preservation、capacity upper bound。
- [x] A/C/D 中的数据边界一致：raw detector-side readout、response-corrected estimate、moderately conditioned inversion。
- [x] B 中不再把 \(n=3\) per-channel 的 `1.96 SEM` 称为严格 95% CI。
- [x] 所有 P0/P1 issue cards 都包含 `If reviewer pushes harder`。
- [x] 所有关键数值均能在 `data_provenance_map.md` 中找到来源文件和生成脚本。
