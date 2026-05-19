# FP 腔一般化理论推导（双凹 / 一般两镜腔）目录说明

这个目录用于把你当前正文中的平凹 FP 腔理论，整理成一个更一般的两镜稳定 FP 腔框架，重点回答下面几个问题：

- 哪些结论只在平凹腔里成立；
- 哪些结论可以直接推广到双凹乃至一般两镜腔；
- 为什么“双凹 Gouy 相位积累翻倍”这个想法有直观参考价值，但不能直接当作严格公式；
- 对称双凹腔和一般双凹腔的几何回代关系到底该怎么写；
- 推广以后，容量界是否保持不变，工程优选分支是否改变。

## 推荐阅读顺序

1. [一般化理论详细推导.md](D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\FP腔一般化理论推导_双凹\一般化理论详细推导.md)
   这是主文档。适合完整理解整套逻辑。

2. [appendix_general_fp_cavity.tex](D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\FP腔一般化理论推导_双凹\appendix_general_fp_cavity.tex)
   这是偏“论文附录口吻”的压缩版 LaTeX 草稿。适合以后往论文里搬。

3. [outputs\general_fp_summary.txt](D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\FP腔一般化理论推导_双凹\outputs\general_fp_summary.txt)
   这是数值和结论的速览版，几分钟就能看完。

## 文件说明

- [一般化理论详细推导.md](D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\FP腔一般化理论推导_双凹\一般化理论详细推导.md)
  中文长文档。包含完整的逻辑拆解、逐步推导、对称双凹特例、为什么不是简单乘 2、小参数极限、一般双凹回代公式，以及对你现有正文理论的影响分析。

- [appendix_general_fp_cavity.tex](D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\FP腔一般化理论推导_双凹\appendix_general_fp_cavity.tex)
  偏简洁的附录版 LaTeX 草稿。优点是更接近最终论文风格；缺点是推导细节比 Markdown 长文档少。

- [verify_general_fp_cavity.py](D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\FP腔一般化理论推导_双凹\verify_general_fp_cavity.py)
  验证脚本。负责生成这个目录下的数值核对文件。

## outputs 目录说明

- [outputs\general_fp_summary.txt](D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\FP腔一般化理论推导_双凹\outputs\general_fp_summary.txt)
  最关键的数值摘要。里面已经明确写出：
  - 平凹框架能否推广；
  - 对称双凹是否等于“平凹翻倍”；
  - 小 `L/R` 极限下的比例关系；
  - `M=9` 时鲁棒性优选分支如何变化。

- [outputs\geometry_mapping_comparison.csv](D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\FP腔一般化理论推导_双凹\outputs\geometry_mapping_comparison.csv)
  对比相同 `L/R` 下：
  - 平凹腔步长；
  - “错误的直接翻倍假设”；
  - 对称双凹腔真实步长。

- [outputs\m9_branch_sensitivity.csv](D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\FP腔一般化理论推导_双凹\outputs\m9_branch_sensitivity.csv)
  比较 `M=9` 时：
  - 平凹腔三条代表支 `m=1,2,4`；
  - 对称双凹近平面支和近同心支的对应分支；
  - 各分支的几何灵敏度。

## 这套资料的核心结论

最短版本只有三句：

1. 你正文里真正普适的是“以 `k` 为核心的圆周折叠设计框架”，不是平凹腔那条特定的 `L/R` 公式。
2. 对一般两镜稳定 FP 腔，应把步长统一写成
   `k_eff = arccos(sqrt(g1 g2)) / pi`。
3. 对称双凹腔不是简单把平凹腔做 `L -> 2L`；理论容量界可以继承，但几何回代和鲁棒性最优分支会改变。

## 如果以后你只想回答一个问题

如果以后有人问：

> “你的理论是不是只能用于平凹腔？”

这个目录给出的最稳回答是：

> 不是。实验实现是平凹腔，但正文后半段的折叠谱、最小间距、Airy 串扰和容量界本质上只依赖有效步长 `k`。平凹腔只是 `k` 的一种几何实现；对称双凹和一般双凹腔只需要改写 `k` 与几何参数的映射。

## 如果以后你只想回答另一个问题

如果有人问：

> “双凹腔是不是就是平凹腔 Gouy 相位翻倍？”

这个目录给出的最稳回答是：

> 这个直觉有物理图像上的参考价值，但不能直接当公式。因为双凹腔的一程传播虽然包含两段 Gouy 相位积累，但本征模束腰位置和瑞利长度也同步改变，所以最终结果不是简单乘 2。小 `L/R` 极限下，真实增强因子趋近于 `sqrt(2)`，不是 `2`。

## 备注

这次只是在 `验证推演3.15/FP腔一般化理论推导_双凹/` 目录下整理资料，没有改正文、附录主文件或章节结构。
