---
tags: [PokeLua, performance, architecture]
status: STATIC_VERIFIED+BENCHMARK_PENDING
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
---
# 全平台性能热点：架构审计

[[../README]] · [[02-gen3-mgba-frlg]] · [[03-cross-platform]] · [[04-benchmark-protocol]]

## 结论矩阵
| 平台／世代 | 源码已经确认 | 运行时风险推断 | 优先级 |
|---|---|---|---|
| mGBA Gen3 | 多个 `update*Buffer` 挂在逐帧回调；大量 `buffer:clear/print` | 高倍速 UI 重排、重复读写及解密 | P1 |
| FRLG mGBA | `getEncounterMissingSteps` 内 `while not isEncounterStep`，循环里调用笛子／道具／特性修正 | 不定长度预测阻塞帧 | P1 |
| BizHawk Gen4/5 | Lua 主 `while` 加 `emu.frameadvance()` | 每帧重算与绘制；分支模式非按需 | P2 |
| DeSmuMe Gen4/5 | `gui.register(main)` + 多项 `gui.text` | GUI 和内存读取重复 | P2 |
| BizHawk/VBA Gen1 | 多个等待目标的 Bot `while` | 停滞、无限重试及输入事件时序 | P2 |
| Dolphin Gen3/4 | `onScriptUpdate` + `ReadValue*` + `SetScreenText` | 文本构建、PK 解码；屏幕更新频率待测 | P3 |

## mGBA：热路径依据
- `Gen 3/mGBA/FRLG_RNG_mGBA.lua` L1195–1210：`updateBuffers` 每模拟帧依次更新七类展示／存档输入。
- FRLG L534 开始：`while not isEncounterStep`；内部 LCRNG 与多个访问内存的 modifier 函数。
- `LCRNGDistance` 的跳跃表主要为 O(32)；如果未通过 Profile 发现是热点，不应先改底层 RNG 算术。
- `showInfo` 每次执行 `getOffset`；`getOffset` 内构建 offsets 表。缓存 24 种排列索引可避免重复分配，需保证子结构偏移完全相同。
- `getRngInfo` 同帧多个窗口重复调用；可以共用 RNG snapshot，但必须区分“采样 RNG 状态”和“展示格式”。

## 因果链（推断，待 Profile）
`帧回调` → 多个页面执行 → 相同 SaveBlock/Seed 再读取 → 多次 PK 解密／大量字符串拼接 → `console Buffer clear/print` → 16× 时每真实秒执行次数上升。

预测开销还受遇敌率、道具和状态影响；高倍速卡顿很可能是多热点叠加，不能仅凭静态代码断言哪一段耗时最高。

## 目标架构
1. **Exact Lane**：帧、Watchpoint、Bot 输入边沿、存档事件、RNG 跟踪必须按原语义运行，遗漏数目标为 0。
2. **Snapshot Lane**：一帧一次读取共享的 RNG、SaveBlock 指针与 TrainerID；依据状态失效条件复用。
3. **Predict Lane**：把遇敌规则的环境信息一次读取后纯计算，单次计算设置迭代额度；跨帧续算只针对不影响 exact lane 的任务。
4. **Render Lane**：按真实时间 8–12Hz 目标刷新；数据无变化不重新打印；落后时丢弃过时 UI，不丢失 RNG／Bot 事件。
5. **Instrumentation**：按函数记录 Lua 自身耗时、内存读次数、绘制次数、长尾（p95/p99）和错误，诊断模式可禁用。

## 不能做的“伪优化”
- 把整个 `updateBuffers` 简单改成每 N 帧运行：可能跳过 Bot 的严格帧输入。
- 只用两次 Seed 判断回退：LCG 模 2^32 的轨迹存在前进/回退歧义，应使用显式即时存档事件和代际状态。
- 在高倍速单帧计算更长的无限预测：阻塞更严重。
- 把一种模拟器的 `emu:read32` 接口直接复制到其他模拟器。
- 将 10Hz 界面刷新写成 10 模拟帧刷新：16× 下仍然会高频刷新。

## 性能验证
先做不带脚本基线、原版、只做 UI 降频版、缓存版、完整优化版五组对照；对比实际速度、纯 Lua 耗时、RNG/TID/PID/IV 等语义差异。详见 [[04-benchmark-protocol]]。

定位引用（固定 SHA）：[FRLG 主循环](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/FRLG_RNG_mGBA.lua#L1195-L1210)、[遇敌循环](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/FRLG_RNG_mGBA.lua#L526-L551)。
