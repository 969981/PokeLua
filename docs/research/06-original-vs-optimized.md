---
tags: [PokeLua, comparison, FRLG, decision-record]
status: STATIC_VERIFIED+BENCHMARK_PENDING
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
---
# 原版脚本与拟优化版本的行为比较

[[../README]] · [[02-gen3-mgba-frlg]] · [[04-benchmark-protocol]]

## 比较对象
- 官方上游 `Real96/PokeLua` / 当前镜像 `969981/PokeLua@main`：`Gen 3/mGBA/FRLG_RNG_mGBA.lua`。
- 用户此前上传的 `FRLG_RNG_mGBA_ID.lua`：文件名不同，目标 TID 配置为 `{0,1,2}`；上传稿 1199 行、上游当前文件 1210 行。
- 之前聊天中生成过 V2 性能优化方案/文件，并未直接覆盖上游。当前已在本分支直接基于上游 FRLG 源码提交 P1 调度优化；见 [[09-frlg-p1-implementation]]。该变更进行了本地同类 Mock 轨迹测试，但仍没有真实模拟器性能数据。

## 已观察到的源码差异
| 项目 | 用户上传版 | 当前上游 | 影响 |
|---|---|---|---|
| `botTargetTIDs` | `{0,1,2}` | `{}` | 默认 TID 命中条件不同 |
| `showStepCounter()` | 未出现独立显示函数 | 有，捕获页显示蛋周期步数 | 界面输出不同 |
| `showInfo()` | 精简了部分信息展示 | 含友情度／蛋周期文本 | 不能用用户旧文件替换上游 |
| `LCRNG` / `LCRNGDistance` | 关键公式相同 | 关键公式相同 | 优化仍须保持数学与异常状态语义 |
| `Initial Seed Bot` / `TID Bot` | 核心流程相同 | 核心流程相同 | 回归重点为帧序列／Watchpoint／最终 ID |

## 规划中的比较（尚无真实 FPS）
| 比较项 | 原版 | develop P1/P2 目标 | 证据状态 |
|---|---|---|---|
| UI 刷新 | 跟着逐帧主回调 | 自适应 8–12Hz | 原版 STATIC_VERIFIED，目标 PLAN |
| RNG 状态读取 | 多页面会重复调用 `getRngInfo` | 每帧读一次并共享 | 原版 STATIC_VERIFIED，目标 PLAN |
| 遇敌预测 | 同步 `while not isEncounterStep` | 同输入纯计算缓存＋预算分批 | 原版 STATIC_VERIFIED，目标 PLAN |
| PK3 offsets | 在函数内构建 offsets 表 | 复用预分配映射 | 原版 STATIC_VERIFIED，目标 PLAN |
| Bot 事件 | 逐帧+Watchpoint | 保留逐帧与 Watchpoint | 目标待 trace 验证 |
| 存档读取 | 原版独立 SaveState 值文件 | 增强状态生命周期/去抖 | 目标待验证 |
| 16× 成绩 | 无本次实机数据 | 额外 FPS 损失 ≤10% 目标 | RUNTIME_NOT_OBSERVED |

## 决策
- 以最新镜像 `main` 为基线，防止抹掉 `showStepCounter` 等上游功能。
- 核心算法先不改：优先显示/缓存/计算隔离；已知的距离解释异常单独建“正确性修复”任务。
- 回归比较至少区分 **源码差异**、**离线单测**、**带模拟器的行为回放**、**实际性能测量** 四类证据，缺失不算 PASS。

参见 [[05-p0-p4-roadmap]]。
