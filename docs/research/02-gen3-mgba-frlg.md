---
tags: [PokeLua, Gen3, mGBA, FRLG, RNG]
status: STATIC_VERIFIED+BENCHMARK_PENDING
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
---
# Gen 3 mGBA：FRLG 关键函数与优化边界

[[../README]] · [[01-performance-architecture]] · [[06-original-vs-optimized]]

主要证据：[FRLG_RNG_mGBA.lua 固定源码](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/FRLG_RNG_mGBA.lua)。

## 关键位置／风险
| 函数 | 代码区域（近似，锁定上述 SHA） | 已确认源码行为 | 优化方案 |
|---|---|---|---|
| `LCRNG` | L430 起 | 32-bit LCG 乘加 | 不改算法，增加数学向量测试 |
| `LCRNGDistance` | L439 起 | 32 阶 jump 表、`dist > 999` 即输出负距离 | 明确异常状态，不擅自篡改原义 |
| `getRngInfo` | L467 起 | 依初始值和当前值维护 Advances | 每模拟帧更新一次，供多个窗口共用 |
| `getFluteEffectMod` 等 | L494–525 | 访问玩家、存档或精灵状态 | 遇敌计算之前生成环境快照 |
| `getEncounterMissingSteps` | L526–551 | `while not isEncounterStep`、一轮多次 modifier | 纯计算+缓存+有限预算+异步续算 |
| `getOffset` | L600 之后 | 函数内重新构建 24 种 offset 表 | 挪到顶层常量 |
| `showInfo` | L690 附近 | PID、OTID、4×12 PK3 子结构解密和文字呈现 | 数据变化时计算，保留校验与异常态检测 |
| `initialSeedBotLoop` | L920 后 | 1／35／40 帧按键，Watchpoint，存档回退 | 状态机重构但保持实际按键时间 |
| `TIDBotLoop` | L1000 后 | 监视临时 TID，目标比较，失败恢复存档 | 每次独立尝试记录，最终 TID/SID 复核 |
| `updateBuffers` | L1195–1210 | 每帧统一调用所有窗口 | Exact lane + Render lane 分离 |

## RNG 算法
原版 FRLG 主 LCG：`s' = (0x41C64E6D * s + 0x6073) mod 2^32`。某些遇敌预测路径使用 `0x3039` 加数，**不能统一替换为同一加数**。原版 `LCRNGDistance` 的 `dist > 999` 阈值可导致真实前进超过 999 次时返回大负数；先做 0／1／999／1000／10,000 等向量对账，再确定兼容修复策略。

## 显示层
当前控制台多次 `clear` 和 `print`，FRLG 同一帧重复触发 `showRngInfo`。拆分：
- `onFrameExact`: 读取 RNG 一次、推进 Bot 状态、处理按键边沿。
- `captureSnapshot`: 收集Trainer ID／Seed／当前战斗对象／Box索引等；必要时标记 dirty。
- `updateExpensivePrediction`: 用固定迭代预算续算（未算完显示上一完成结果与状态标记，不得把半成品当最终结果）。
- `renderIfDue`: 基于真实时间或实测 FPS 的 8–12Hz 节流；仅变化才打印。

## Bot 必须保留的语义
- watchpoint `emu:setWatchpoint` 对 `0x02020000` 的写入通知不能经 10Hz UI 轮询替代。
- `saveStateBuffer` 和 `loadStateBuffer` 的调用时刻保持相对帧数不变；重构先做 trace-for-trace 比较。
- TID 命中应读正式 SaveBlock2 中的 `TID`／`SID`，区分“临时写入已命中”与“正式训练家 ID 已验证”。
- Bot 同时启动应明确互斥；恢复时撤销未完成预测和窗口缓存，重建同代 RNG 状态。
- 失败后多次获得相同 TID 不代表优化缺陷已经修复：必须检查重复时间线和延迟策略。

## 数据解析与一致性
保留性格、PID、OTID、Block shuffle、加密块、IV、招式、PP、特性、携带道具和蛋数据语义；新增 PK3 校验和、空对象／非法指针防护时先放入可切换诊断模式，避免改变原版显示结果未被发现。

## 同族脚本顺序
1. FRLG → E → RS（参考同一 mGBA API，但地址、算法行为不能混用）。
2. RS Checksums 独立处理（防止错误“共用 PK3”逻辑）。
3. E/FRLG/RS Held Item 分别建立 Golden Samples；修改解析函数前做全字节/ID 对照。

## 验收关口
相同 ROM+存档+输入：1× 到 16× 模拟相同帧序列时，目标 Seed／Advances／生成 Pokémon PID、IV、Nature／TID／SID／Bot事件顺序保持一致；遇敌预测若改算法，逐样本与原版相同。FPS 与渲染开销单独验收。

> 状态：目前为静态审计；没有模拟器实际测量报告，不写“16× 已通过”。
