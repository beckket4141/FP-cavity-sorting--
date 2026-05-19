# 四套数据的解析 2/9 分支主峰位置偏差汇总

## 理论口径

- `k_th = 2/9 = 0.222222222`
- `L/R_th = sin^2(pi * 2/9) = 0.413175911`
- 全部偏差都按各自目录采用的 `FSR_final` 归一化，只看主峰相对位置，不看精细度。

## merged 主结果

- `0p88mm / FSR补全后数据`: RMS=0.002136 FSR, max=0.003322 FSR, worst l=5, `l=9` closure=0.002296 FSR
- `0p88mm / 原始数据`: RMS=0.002894 FSR, max=0.003720 FSR, worst l=2, `l=9` closure=0.002313 FSR
- `0p98mm / FSR补全后数据`: RMS=0.002215 FSR, max=0.004407 FSR, worst l=8, `l=9` closure=0.002597 FSR
- `0p98mm / 原始数据`: RMS=0.002040 FSR, max=0.003566 FSR, worst l=8, `l=9` closure=0.002598 FSR

## 输出

- 每个分析子目录新增 `theory_position_validation.csv`、`theory_position_validation_summary.csv`、`theory_position_validation.png`、`theory_position_validation.md`。
- 总汇总新增 `outputs/final_theory_position_validation_comparison.csv`、`outputs/final_theory_position_validation_report.md` 和 `outputs/final_theory_position_validation_overview.png`。
