# 三方共识 Memo（更新到软 `w0` 策略）

## 已达成共识

1. 连续满载 `S_N={1,\dots,N}` 仍是主问题，MIS 是一般化扩展工具。
2. 叙事顺序应保持“先几何、后质量”：先给候选分支，再给工程可用分支。
3. 计算口径按晶体腔执行：
   - `lambda0=795 nm`
   - `n=1.453371`（石英，795 nm）
   - `lambda_medium=lambda0/n`
4. `w0` 改为软分档告警，不再作为几何硬淘汰：
   - `comfortable (>=50 um)`
   - `experimental_ok ([47,50) um)`
   - `high_risk (<47 um)`

## 当前平台下应保留的事实

数据源：`outputs/05_dual_scenario_effective_branches/dual_scenario_branch_summary.csv`

1. `N=9` 在 `CURRENT_PLATFORM` 下最终有效分支为 `m=2,4`（均为 `w0_high_risk` 告警）。
2. `N=12` 在 `CURRENT_PLATFORM` 下有几何候选 `m=5`，但质量层失败，最终有效分支数仍为 0。
3. `N=15,30,50` 说明：高 `N` 下几何层不一定空，但在当前 `F=29.8, tau0=3` 下质量层先成为瓶颈。

## 建议避免的过强表述

1. 不把 `L/R -> 1` 写成“近共心”，应写“接近平凹腔 hemispherical 稳定性边界”。
2. 不把 `N=12` 的结论写成平台无关真理。
3. 不把 `N=9` 写成“只有 `m=2` 唯一可行且口径无关”。

## 一句话版本

解析解给出候选，几何筛选给出可做性，`tau/F` 再决定是否够用；三者合起来才是完整的 FP-OAM 设计理论。
