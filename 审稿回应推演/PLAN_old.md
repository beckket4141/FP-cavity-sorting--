# OE 稿件数据稳健性收尾计划

## Summary

已完成：NNLS 零值来源审计、raw/response/corrected 对照、floor sensitivity、ER/transmittance 误差条口径对比，并生成 `full9_robustness_audit.*` 与中文推演报告。

下一步目标：把这些推演结果转成 OE 稿件层面的低风险表述，明确哪些已解决、哪些仍需补强，并保证 `main.tex` / `supplement.tex` / rebuttal 口径一致。

默认决策：采用“**不重画图，改统计表述**”路线。现有误差条按 `mean ± 1.96 SEM from three independent runs` 表述，不再称为 `95% confidence interval`。

## Key Changes

- `main.tex`
  - 修改 Fig. 5 段落中的 `93.19%±0.37% (95% confidence interval...)`，改为 `mean ± 1.96 SEM from three independent runs` 或等价简洁表述。
  - 给 `11.41±0.25 dB` 同步补明误差条口径，避免一个指标有口径、另一个没有口径。
  - 保持正文克制：不主动展开 NNLS 零值辩解，只保留 response correction 的必要说明，并指向 Appendix B.1。

- `supplement.tex`
  - 在 Appendix B.1 的 NNLS 公式后增加一段“边界零值与稳健性检查”说明。
  - 明确：raw detector powers 非零；unconstrained LS 给出小负分量；NNLS 将其投影到非负边界；这些 0 是 boundary estimates，不是物理串扰严格为零。
  - 增加 floor sensitivity 的简短结论：0.1% floor 使 mean \(ER_{\mathrm{sum}}\) 下降约 0.05 dB，0.2% floor 下降约 0.10 dB，结论不变。
  - 保留 high-\(l\) SNR 的谨慎边界：当前可证明矩阵条件数约 5、重复测量稳定；不声称已有 dark-noise/background floor 级别的绝对噪声预算。

- Rebuttal / 内部材料
  - 整理一版英文 rebuttal 段落，围绕三点：response matrix 独立标定、NNLS 零值是边界解、floor robustness 不改变 ER 结论。
  - 保留中文推演报告作为内部证据链，不直接把所有细节塞进正文。

## Quality Gates

- 修改 `.tex` 正文前先读取并遵守 `skills/tex-body-tone-guard/SKILL.md`。
- 全文检索并清除误导性统计表述：
  - 不再出现 `95% confidence interval from three independent runs`，除非真的改用 t-based CI。
  - 图注/正文/补充材料中 errorbar 口径一致。
- 全文检索 response correction 相关词，确认 `raw`、`corrected`、`NNLS`、`response matrix` 的说法不互相冲突。
- 检查补充材料语气：只做事实说明，不写成防御性 rebuttal 腔。
- 若 TeX 工具链可用，编译复制版 OE 稿件；否则至少做 `rg` 检索和 LaTeX 语法局部检查。

## Test Plan

- 数据一致性：
  - 用现有 `full9_robustness_audit.xlsx` 核对条件数 `5.05, 4.99, 5.43`、NNLS 复现最大差 `4.93e-10 W`、floor sensitivity 数值。
  - 确认正文中的 `93.19%`、`11.41 dB`、`10.66 dB` 不被改动，只改统计口径和解释文字。

- 文本一致性：
  - `rg "95\\% confidence|confidence interval|CI|1.96|SEM|standard deviation"` 检查所有统计口径。
  - `rg "zero|boundary|NNLS|non-negative|response-corrected|raw projection"` 检查补充材料新增说明是否可追溯。

- 审稿风险检查：
  - 确认不会让读者以为 raw matrix 自身就是 sorting matrix。
  - 确认不会让读者以为 corrected 0 值是实验测得的绝对零串扰。
  - 确认不会声称已有 dark-noise/background 测量，除非后续找到相应数据。

## Assumptions

- 采用当前推荐路线：不重画 Fig. 5，只修正误差条表述为 `mean ± 1.96 SEM from three independent runs`。
- 当前 `答辩ppt/审稿回应推演/main.tex` 和 `supplement.tex` 是 OE 投稿稿件的工作副本，后续修改先作用于这两个副本。
- 暂不补做新的实验噪声测量；high-\(l\) readout SNR 只写成基于条件数和重复测量的数值稳健性判断。
