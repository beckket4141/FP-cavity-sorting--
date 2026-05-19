# Q1 定义澄清：Claude 对接文档

## 1. 任务背景

当前任务只针对审稿质疑 Q1：

- 附录把满载实验写成 `\mathbf y = \mathbf S \mathbf x`
- 审稿人因此追问 `x` 的物理定义、对应哪一次锁频、以及 `x` 到底是 `9x1` 还是 `9x9`

用户的硬约束是：

- 我们的补充论证必须让审稿人**更相信**现有工作
- 不能为了补一个点而主动引出更大的质疑
- 本轮不允许修改论文原文
- 本轮不允许修改原始数据

## 2. 当前判断

Q1 的主问题已经基本定位为：

- **不是数据对象本身不成立**
- 而是**附录对真实数据对象做了过度压缩表达**

更准确的模型应为：

- 单次锁定态：`\mathbf y^{(j)} = \mathbf S \mathbf x^{(j)}`
- 全部锁定态合并：`\mathbf Y = \mathbf S \mathbf X`

其中：

- `\mathbf y^{(j)}` 是 FP 锁定在第 `j` 个目标模式共振点时的原始检测列向量
- `\mathbf x^{(j)}` 是同一锁定态下的去嵌入模态功率列向量
- 单列维度是 `9x1`
- 全部 9 个锁定态并起来是 `9x9`

## 3. 已核实证据

### 3.1 文本层证据

存在问题的原文位置：

- [app_e5_calibration_robustness.tex:19](D:/自制软件/1.thesis/My_nju_thesis-master/thesis/appendices/app_e5_calibration_robustness.tex#L19)
  这里把满载模型写成了无上标的 `\mathbf y=\mathbf S\mathbf x`
- [app_e5_calibration_robustness.tex:17](D:/自制软件/1.thesis/My_nju_thesis-master/thesis/appendices/app_e5_calibration_robustness.tex#L17)
  这里说“可视为纯目标模式”，这句话容易引发 Q2
- [ch05_fp_design_and_validation.tex:353](D:/自制软件/1.thesis/My_nju_thesis-master/thesis/chapters/ch05_fp_design_and_validation.tex#L353)
  正文说明了“独立标定 + 响应校正”，但未把列向量结构明写出来

### 3.2 数据 schema 证据

文件：

- `最终数据/测量方法.md`

其中已定义：

- `\mathbf y^{(j)}`
- `\mathbf x^{(j)}`
- `j` 为锁定态/目标模式索引

这是 Q1 最关键的结构性证据。

### 3.3 工作簿结构证据

已核实以下文件表头均为 `lock=0...8`：

- `最终数据/1/calib_matrix_with_uncertainty.xlsx`
- `最终数据/1/full9_matrix_with_uncertainty.xlsx`
- `最终数据/2/...`
- `最终数据/3/...`

这说明数据天然按锁定态列组织，而不是按“单一全局向量”组织。

### 3.4 数值验算证据

新增只读脚本：

- [q1_verify_per_lock_model.py](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/标定方法解释--查漏补缺/q1_verify_per_lock_model.py)

结果文件：

- [q1_per_lock_model_results.md](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/标定方法解释--查漏补缺/q1_per_lock_model_results.md)
- [q1_per_lock_model_results.json](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/标定方法解释--查漏补缺/q1_per_lock_model_results.json)

关键结果：

- 三次实验全局相对残差约为 `0.54% / 0.80% / 0.28%`
- 运行热图与 `X` 列归一化的最大差仅为 `0.002379 / 0.000784 / 0.003580` 个百分点
- 合并热图最大差仅 `0.001282` 个百分点
- 合并 ER 与对角占比统计与从 `X` 直接重算的结果完全一致，仅剩浮点误差

结论：

- Q1 所需的“列向量模型”与实际数据处理是吻合的

## 4. 已确认的风险边界

### 4.1 允许使用的主张

可以安全使用：

1. Q1 主要是数学对象未展开写清。
2. 正确对象是 `\mathbf y^{(j)}`、`\mathbf x^{(j)}` 与 `\mathbf Y=\mathbf S\mathbf X`。
3. 单锁定态是 `9x1`，全体锁定态合并是 `9x9`。
4. 热图和最终指标口径与列向量族 `X` 完全一致。

### 4.2 只能内部掌握、不建议外显的点

内部知道即可：

1. 最差列均出现在 `lock=8`
2. Run 1/2 的 `lock=8` 相对残差约 `3.94% / 4.20%`
3. 该偏差主要来自很小的 `ch=7` 非对角分量，不是主对角信号崩坏

这些点不适合做对外 headline，因为很容易把讨论带进 Q3。

### 4.3 明确禁止越界的主张

不要说：

1. “`S` 是纯检测系统矩阵”
2. “标定时场是纯目标模式，所以离共振泄漏场当然也适用同一矩阵”
3. “Q1 澄清后 Q2 自动被解决”
4. “逐列数值重构成立就等于物理迁移假设成立”

## 5. 建议 Claude 后续优先做什么

如果 Claude 接手继续推进，推荐优先级如下：

1. 先阅读本目录下的详细报告，完全继承 Q1 的安全边界。
2. 如果转向 Q2，重点不是重复 Q1，而是检查：
   - 标定态与满载使用态之间的“模式形状迁移假设”能否被更弱、更稳的表述替代
   - 是否存在能证明 `S` 主要承担读出不均匀性校正、而非强依赖离共振场形的现有数据
3. 如果转向 Q3，重点检查：
   - `l=8` 的单独重复偏差
   - 高倍校正通道的不确定度传播
   - 哪些结果能内部解释，哪些结果适合公开使用

## 6. Claude 后续工作时必须遵守的原则

1. 先加固整体解释链，再补单点漏洞。
2. 若一个补充论证会顺手放大 Q2/Q3，就不要把它写成正式答复口径。
3. 优先使用“更弱但更稳”的说法，而不是“更强但更容易被追问”的说法。
4. 所有新主张必须能回指到现有文件或计算结果。

## 7. 关键文件路径

### 7.1 论文文本

- [ch05_fp_design_and_validation.tex](D:/自制软件/1.thesis/My_nju_thesis-master/thesis/chapters/ch05_fp_design_and_validation.tex)
- [app_e5_calibration_robustness.tex](D:/自制软件/1.thesis/My_nju_thesis-master/thesis/appendices/app_e5_calibration_robustness.tex)

### 7.2 数据与 schema

- `最终数据/测量方法.md`
- `最终数据/1/calib_matrix_with_uncertainty.xlsx`
- `最终数据/1/full9_matrix_with_uncertainty.xlsx`
- `最终数据/2/...`
- `最终数据/3/...`
- `最终数据/triplicate_full9_aggregate.xlsx`

### 7.3 本轮新增材料

- [Q1定义澄清_详细报告.md](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/标定方法解释--查漏补缺/Q1定义澄清_详细报告.md)
- [q1_verify_per_lock_model.py](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/标定方法解释--查漏补缺/q1_verify_per_lock_model.py)
- [q1_per_lock_model_results.md](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/标定方法解释--查漏补缺/q1_per_lock_model_results.md)
- [q1_per_lock_model_results.json](D:/自制软件/1.thesis/My_nju_thesis-master/My_nju_thesis-master/验证推演3.15/腔实际性能参数验算/满载叠加态输入数据/标定方法解释--查漏补缺/q1_per_lock_model_results.json)

## 8. 建议给 Claude 的提示词模板

可以直接用下面这个方向去接力：

> 请先阅读 `Q1定义澄清_详细报告.md`、`q1_per_lock_model_results.md` 和 `测量方法.md`。当前 Q1 已基本判定为“逐锁频列向量模型在数据层成立，但附录定义写得过度压缩”。请在不破坏这一安全边界的前提下，继续评估 Q2 是否能用更弱、更稳的物理论证收口。禁止把 `S` 直接说成纯检测矩阵，禁止把 Q1 的列模型成立外推出离共振模式形状完全不变。优先寻找不会放大 Q3 的论证路径。

## 9. 一句话交接

Q1 已基本站稳：**问题在于定义没有把列向量上标写出来，而不在于数据处理对象本身不成立；后续若继续推进，必须把 Q1 与 Q2/Q3 严格分层。**
