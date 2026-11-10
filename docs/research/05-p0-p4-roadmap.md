---
tags: [PokeLua, roadmap, optimization, acceptance]
status: PLAN_APPROVED_SCOPE
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
---
# P0 → P4 实施路线图

[[../README]] · [[04-benchmark-protocol]] · [[07-branch-sync-governance]]

## 原则
本阶段在 `develop` 已完成 FRLG P1 首轮调度器代码改造，并提供 Mock 回归测试；实际 mGBA 性能与 ROM 兼容性仍未观察。先保持原版函数语义，优化证明通过后再逐平台迁移。详见 [[09-frlg-p1-implementation]]。按 **P0→P1→P2→P3→P4** 走，每阶段通过 Gate 才进入下一阶段。

| 阶段 | 实施事项 | 交付物 | Gate |
|---|---|---|---|
| **P0** Baseline | 固定上游 SHA、26 脚本清单、功能路径、环境矩阵、黄金输入/结果、性能基线 | manifest、trace、benchmark JSON | 至少 FRLG/E/RS 和典型 Gen1/4/5 脚本可重复运行 |
| **P1** Scheduling | mGBA 精确帧与 UI 拆分、合并 Seed/ID 采样、热键边沿处理 | FRLG P1 实现 + 对账 | Watchpoint/按键帧序列 0 差异；UI ≤12Hz 目标 |
| **P2** Hotspots | 预测前状态快照、迭代预算、dirty 缓存、PK3 offset 表预分配、字符串输出去重 | FRLG P2 + E/RS 可移植补丁 | 原版逐样本预测/PK3 结果一致；独立统计性能变化 |
| **P3** Bot correctness | TID 和 Initial Seed 独立状态机、重试日志、互斥、存档代际复位、可取消与超时 | Bot trace/失败重现用例 | 正式 TID/SID 验证；成功和失败路径 0 事件遗漏 |
| **P4** Regression | 1×–16× 真机／模拟器验证，跨平台差异、CI 纯算法测试和回归报告 | JSON/Markdown 性能报告、测试矩阵 | 符合 [[04-benchmark-protocol]]，不满足则记录未通过 |

## 优先次序
**Tier A**：Gen3 mGBA FRLG（逐帧 UI + 预测循环 + 双 Bot，受益面最大）、E、RS 以及三款 Held Item、Checksums。
**Tier B**：Gen4 BizHawk DP/Pt/HGSS，Gen4 DeSmuMe；Gen5 BW/B2W2 两组平台。侧重分离时间状态、预测计算与画面绘制，跨版本验证。
**Tier C**：Gen1 双平台 Bot 的上限/取消与可终止性；Gen3 Dolphin 六脚本和 Ranch 的文本缓存、PK 解密与存档状态。

## 每阶段避免的回归
- P1：不能让“UI 刷新 N 帧一次”把 Bot 回调也降频。
- P2：多帧任务续算时 Snapshot 若变化应取消旧任务，不能混用两个 Seed 状态。
- P3：载入存档后的 `currentFrame`、缓存和 RNG 世代要一起切换，禁止只复原窗口显示。
- P4：实测需在同一环境，且正确标注卡顿是 Lua 还是模拟器本身。

## 推荐代码组织（待 P1 开始才落地）
```text
tests/
  fixtures/                  # 人工造的测试向量，禁止提交商业 ROM
  unit/                      # 纯 Lua RNG/PK/排序测试
  traces/                    # 匿名化事件序列
  performance/               # 可重复运行基准
src/                          # 等价性验证通过后再考虑提取共享模块
docs/                         # 本 Obsidian Vault
```
不同模拟器执行 Lua 的版本/加载能力不一致，不能假定文件内 `require` 可用；第一阶段优先通过生成后的单文件脚本交付，每个平台建立 adapter 层接口草案。

## 迭代日志与责任
建议每个 PR 同时更新测试结果及对应研究文档，模板见 [[../templates/research-record]]；每个 PR 要明确 source SHA、ROM 范围、功能差异和实机结果。发布不与上游同步快照混淆。
