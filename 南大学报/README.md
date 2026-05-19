# 南京大学学报稿件工作区

本目录用于独立搭建“**稳定双镜 FP 腔中 LG 模式分束的统一框架与误差机理**”中文学报稿。

当前路线为：

> **LG 分束入口 + Gouy 折叠谱 + Airy 串扰 + 径向寄生机理**。

也就是说，稿件对外以 LG 模式分束、稳定双镜 FP 腔和误差机理作为读者入口；正文内部用横模阶数 `N=2p+|l|+1` 解释各向同性稳定腔的频谱分组，并用 Airy 透射函数完成有限线宽串扰和容量边界分析。

## 当前目录结构

- `journal_template/`
  - 官方下载模板与征稿 PDF。
- `manuscript/`
  - 中文稿、结构脚手架、图表计划、工作模板副本。
- `simulation/`
  - 新版理论脚本、数据导出脚本和主图生成脚本。
- `simulation/outputs/`
  - CSV/JSON 数据、5 幅主图、正文表格和仿真报告。
- `notes/`
  - 投稿要求、标题摘要备选、审稿风险和修稿检查表。
- `figures/`
  - 旧版主图导出空间；新版主图目前以 `simulation/outputs/figures/` 为准。
- `sources/`
  - 源材料映射与复用说明。

## 当前关键文件

修改正文前优先阅读这三份：

- `PLAN.md`
  - 当前总规划和 6 节结构。
- `manuscript/section_scaffold.md`
  - 各节落稿功能、边界和第 4 节 Airy 串扰闭环。
- `manuscript/figure_plan.md`
  - 新版 5 幅主图的功能、引用位置和图题。

辅助文件：

- `manuscript/nju_jns_draft.md`
  - 当前中文稿正文草稿。
- `notes/title_abstract_options.md`
  - 标题、摘要和关键词备选。
- `notes/revision_checklist.md`
  - 修改前后的科学准确性和投稿适配检查清单。
- `simulation/README.md`
  - 新版理论脚本说明。
- `simulation/outputs/reports/simulation_report.md`
  - 当前数值结论、主图和数据源总表。

## 当前已落实内容

1. 已下载官方写作模板 `journal_template/nju_jns_template.docx`。
2. 已下载征稿启事 `journal_template/nju_jns_call_for_papers.pdf`。
3. 已复制工作模板到 `manuscript/nju_jns_template_working_copy.docx`。
4. 已起草中文稿 `manuscript/nju_jns_draft.md`。
5. 已建立新版仿真工作流。
6. 已生成新版 5 幅主图和配套数据。

## 重建新版数据、图和报告

在本目录执行：

```powershell
python .\simulation\export_jns_tables_and_report.py
```

输出位置：

- `simulation/outputs/data/`
- `simulation/outputs/figures/`
- `simulation/outputs/reports/`

旧版图脚本 `simulation/build_jns_figures.py` 仅作为历史参考，不再作为当前主图来源。

## 写作原则

- 标题和引言以 LG 模式分束作为入口。
- `N=2p+|l|+1` 是正文内部的横模阶数变量，不作为标题概念。
- OAM 序列是物理特例，不是单个各向同性 FP 腔的完整模式区分能力声明。
- Airy 透射函数是串扰和容量边界的定量工具。
- `s_min` 景观用于解释连续模式组的算术结构，不抢走性能主线。
- 腔型差异写成几何回代和鲁棒性排序差异。
- 误差机理服务于径向寄生和卫星峰解释。

## 下一轮工作建议

1. 按 `manuscript/section_scaffold.md` 精修 `nju_jns_draft.md`。
2. 特别补强第 4 节 Airy 透射串扰、有限维求和、容量边界和理论/实验数值区分。
3. 补足国内文献和本人前期工作引用。
4. 生成英文摘要初稿。
5. 将 Markdown 稿迁移到官方 Word 模板。
6. 用 `notes/revision_checklist.md` 做投稿前自检。

