# AI Agent 指引

这份文件不是让 AI 自由发挥的。

它的作用只有一个：在这个目录里回答问题时，先找对证据，再说话。

---

## 1. 当前工作区边界

本指引只对应下面这套当前工作区：

- `DATA_ROOT = D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\腔实际性能参数验算\满载叠加态输入数据\最终数据`
- `REVIEW_ROOT = D:\自制软件\1.thesis\My_nju_thesis-master\thesis\验证推演3.15\腔实际性能参数验算\满载叠加态输入数据\标定方法解释--查漏补缺`
- `THESIS_ROOT = D:\自制软件\1.thesis\My_nju_thesis-master\thesis`

如果看到工作簿 `meta`、脚本注释或旧说明里出现别的历史路径，只能把它当背景痕迹，不能自动当作当前权威来源。

---

## 2. 必须先记住的事实

### 2.1 标定矩阵 `S` 的真实测量方式

第 `k` 列 `S` 的测量方式是：

1. 产生端产生纯 `l=k`
2. `FP` 腔锁定态也是 `l=k`
3. 检测端遍历 `l=0~8` 全部通道

所以 `S` 的作用是标定检测链路本身，不是去猜输入端本来“应该有什么”。

### 2.2 最终性能结论只能用 `de-embedded-FP`

`raw-SMF` 只是检测端原始读数，混有检测链路的模式依赖损耗。

论文和审稿回复里，如果谈器件本体分选性能，必须优先引用 `de-embedded-FP` 口径。

### 2.3 一个旧说法已经作废

“平均 `0.97%`、最大 `2.58% (l=5)` 的独立单模交叉验证”这句话，当前保留数据中没有可直接回溯的独立数据源。

所以：

- 不要再把它当作当前有效事实
- 如果有人问标定重复性，要改用当前三份 `calib_matrix_with_uncertainty.xlsx` 之间的实际离散

### 2.4 审稿质疑 Q1~Q4 不要从头乱猜

如果问题已经进入审稿质疑层面，不要重新从零假设。

优先读取：

- `REVIEW_ROOT\Q1-Q4_总对接文档_含Memory.md`
- `REVIEW_ROOT\Q2迁移合理性_详细报告.md`
- `REVIEW_ROOT\Q3_l8敏感度_详细报告.md`
- `REVIEW_ROOT\Q4_详细报告.md`

---

## 3. 去哪里找什么

### 3.1 方法、口径、文件含义

优先看：

- `DATA_ROOT\测量方法.md`

用途：

- 当前数据怎么定义
- 标定矩阵怎么测
- `raw-SMF` 和 `de-embedded-FP` 的区别
- 哪些旧说法已经废弃

### 3.2 单次 run 的矩阵和指标

优先看：

- `DATA_ROOT\1\calib_matrix_with_uncertainty.xlsx`
- `DATA_ROOT\1\full9_matrix_with_uncertainty.xlsx`
- `DATA_ROOT\1\channel_snr_analysis.xlsx`
- `DATA_ROOT\2\...`
- `DATA_ROOT\3\...`

用途：

- 某一次实验里具体数值是多少
- 三次 run 之间的离散有多大
- 某个通道在某次实验里表现如何

### 3.3 三次合并后的最终结果

优先看：

- `DATA_ROOT\triplicate_full9_aggregate.xlsx`
- `DATA_ROOT\triplicate_full9_stats.txt`

用途：

- 论文里最后那组 9 模平均结果
- 三次合并后的对角占比、`ER_sum`、`ER_max`

### 3.4 脚本定义和计算逻辑

优先看：

- `DATA_ROOT\aggregate_triplicate_full9.py`
- `DATA_ROOT\compare_diag_only_vs_full_matrix.py`

用途：

- 汇总结果怎么来的
- 百分比矩阵怎么定义
- 对角校正和完整矩阵校正差在哪里

### 3.5 论文对齐

只在需要对齐正文时再看：

- `THESIS_ROOT\chapters\ch05_fp_design_and_validation.tex`
- `THESIS_ROOT\appendices\app_e5_calibration_robustness.tex`

---

## 4. 证据优先级

当多个来源冲突时，按下面顺序裁决：

1. 当前工作簿和汇总结果文件
2. 当前目录下正在使用的脚本
3. `REVIEW_ROOT` 下的分析文档
4. `DATA_ROOT\测量方法.md`
5. 论文章节 `.tex`
6. 历史草稿、旧笔记、工作簿 `meta` 中的历史路径

低优先级文字不能推翻高优先级数据。

---

## 5. 回答时的硬规则

### 5.1 先分清三类话

- `Fact`：文件里直接能看到
- `Inference`：根据多个事实推出
- `Unknown`：当前证据不够

### 5.2 数字必须能回溯

只要是关键数字，就必须能指出来源文件。

如果找不到来源，就直接说“当前目录下未找到可回溯证据”，不要补脑。

### 5.3 不要用旧口径顶当前数据

尤其不要再自动引用：

- `0.97%`
- `2.58%`
- 旧路径下的脚本产物
- 已经被用户明确判定为旧版的说明文字

### 5.4 审稿问题回答要讲人话

优先用直白说明：

- 这是什么
- 为什么会这样
- 当前数据支持到什么程度

不要把简单问题说得很绕。

---

## 6. 典型问题怎么路由

### 6.1 “这个数字到底是多少”

先去：

- 单次问题看 `1/2/3` 工作簿
- 合并问题看 `triplicate_full9_aggregate.xlsx`

### 6.2 “这套测量到底怎么做的”

先去：

- `测量方法.md`

### 6.3 “审稿人这条质疑怎么回”

先去：

- `REVIEW_ROOT` 下对应的 `Q1/Q2/Q3/Q4` 文档

### 6.4 “论文正文现在该怎么写”

先去：

- `ch05_fp_design_and_validation.tex`
- `app_e5_calibration_robustness.tex`

---

## 7. 最后的执行要求

回答任何问题前，默认按这个顺序做：

1. 先判断问题属于“方法、单次 run、三次合并、脚本逻辑、审稿回复、论文对齐”哪一类
2. 按上面的路由去找最小够用证据
3. 只基于证据回答
4. 明说哪些是事实，哪些是推断，哪些还不能确定

如果证据不够，就停在“不够”，不要硬编完整答案。
