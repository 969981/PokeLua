---
tags: [PokeLua, FRLG, mGBA, P1, benchmark, validation]
status: INSTRUMENTATION_PREPARED+RUNTIME_NOT_OBSERVED
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
date: 2026-11-10
---
# FRLG P1：真实 mGBA 1×–16× 验收关口

[[../README]] · [[09-frlg-p1-implementation]] · [[04-benchmark-protocol]] · [[05-p0-p4-roadmap]]

## 当前结果
本轮确认仓库 P1 仍在 develop，且已经开发生成真实 mGBA 测量 Lua 的工具。
当前执行环境 **未安装 mGBA，也没有 FRLG ROM 或存档**，因此没有真实 1×/4×/8×/16× FPS 数据及正式 TID/SID 结果。禁止将 Mock 判为实机 PASS。

## 工具
- [操作和采样说明](../../tests/real_mgba/README.md)
- [Lua 探针生成器](../../tests/real_mgba/build_probe.py)
- [TSV 结果汇总](../../tests/real_mgba/analyze_probe.py)

两种互斥测量模式：
- 性能模式：在原版与 P1 **独立生成** Lua，按真实秒聚合 frame callbacks、UI redraw 数量及回调 CPU 时间；都引入相同探针开销。自身日志是“模拟帧回调吞吐”，不是 GPU 绘制 FPS。
- Trace 模式：额外记录 Watchpoint、Initial Seed/TID Bot 的 save/retry/found 事件；磁盘 I/O 会影响速度，所以不得混入性能分数。

## 验收矩阵
| 条件 | 门槛 | 状态 |
|---|---|---|
| 1×/4×/8×/16× | 相同游戏场景分别测原版与 P1 | RUNTIME_NOT_OBSERVED |
| UI | 实际约 8–12 Hz，无长时卡死 | RUNTIME_NOT_OBSERVED |
| 16× | 尽可能达到目标倍率，脚本相对无脚本额外损失目标 ≤10% | RUNTIME_NOT_OBSERVED |
| RNG | 相同 Seed、Advances、帧输入及即时存档轨迹 | MOCK 部分对账 |
| Initial Seed Bot | 第 1/35/40 帧、写监视点、重试及命中 | MOCK 事件对账 |
| TID Bot | 写监视点、重试、临时 TID 以及最终正式 TID/SID | MOCK 事件对账，正式 ID 未验证 |
| 遇敌预测 | 相同结果且不卡模拟帧 | P2 待实施 |

## 操作次序
1. 固定模拟器构建、ROM 修订及 SHA-256，准备相同起点存档。先记录 **无脚本** 基线。
2. 原版和 P1 分别在 1×、4×、8×、16×、室外/草丛/战斗/PC 等场景采集，每组至少 120s 采样。
3. 单独在 Trace 模式跑两个 Bot 的失败/命中/存档恢复；比较事件、Seed、callback tick、emulator frame。
4. 将临时 ID 与正式 SaveBlock2 TID/SID、实际 RNG Advances 对账；仅有日志不能证明最终生成正确。
5. 如 16× 仍低速，先分离当前原版遇敌预测的无上限 while 热点，再推进 [[05-p0-p4-roadmap|P2]]。

## 未闭合
实机性能结果、原版/优化版最终训练家 ID 一致性、ROM 游戏状态对账均为 RUNTIME_NOT_OBSERVED；本报告不附虚构 FPS 或“16× 已通过”结论。
