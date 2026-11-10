---
tags: [PokeLua, Gen4, BizHawk, DeSmuMe, RNG, encounter]
status: STATIC_VERIFIED+BENCHMARK_PENDING
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
review_date: 2026-11-10
---
# Gen 4 DP／Pt／HGSS：六份 DS 脚本性能与算法风险

[[../README]] · [[11-gen3-mgba-other-hotspots]] · [[13-gen5-ds-hotspots]]

## 共用热点：野生遇敌预测
证据：[DP BizHawk L1139–1185](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/BizHawk/DP_RNG_BizHawk.lua#L1139-L1185)、[DP DeSmuMe L1135–1184](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/DeSmuMe/DP_RNG_DeSmuMe.lua#L1135-L1184)、[HGSS BizHawk L1142–1175](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/BizHawk/HGSS_RNG_BizHawk.lua#L1142-L1175)。

- 六份脚本的 `getEncounterMissingSteps(movement, encounter)` 均包含 `while not battleStartJumpFlag do`；循环推进预测 RNG，直到命中概率判断，但未设置固定迭代上限或取消机制。
- `battleStartJumpFlag` 在 `getRngInfo()` 的外部阶段更新，不在该预测循环中变化。因此它仅决定是否进入循环，**不构成“执行 N 次后就停止”的保护**。
- 只有进入特定 Encounter Area 才调用预测，不能笼统说“每帧必然跑满”。风险随当前 tile/lead ability/held item/rate/seed 变化。
- 若运动率或遭遇率意外为零、无效或预测始终不命中，循环可能极长甚至不终止；这是基于控制流的条件风险，不是实机已发生的崩溃。

### 可证等价的优化
1. 在预言调用前缓存 `movement`、`encounter`、`coolDown`、`currentSeed`、`mapAttribute`、能力/道具效果及游戏配置；这些作为预测任务版本 Key。
2. 把每次迭代改成 `state={seed,missingSteps,coolDownSteps,...}` 的可恢复任务，每个模拟帧按预算执行若干步。遇到输入变化立即丢弃旧任务，绝不把旧结果作为当前预测。
3. 先使用无预算纯函数与原版比对 **生成结果和 RNG 状态**，再加入预算/续算；不改变调用次数、分支判断和 LCG 常数。
4. 启用“计算中/超限”状态；禁止返回假的 0 步或错误预测结果冒充真实数字。
5. 样本涵盖 0、极小、通常、最大值的 encounter rate，冷却、骑车/行走、笛子、特性和持有物，以及遇敌区边界。

## 两个平台的不同循环契约
- **BizHawk**：DP/Pt/HGSS 以 `while not wrongGameVersion do ... emu.frameadvance() end` 主循环推进；包含 `userdata.set` 的状态持久化和 `event.onloadstate` 恢复。
- **DeSmuMe**：DP/Pt/HGSS 以 `gui.register(main)` 显示回调；`getSaveStateInput` 与载入记录文件也是不同实现。
- **重要**：BizHawk 和 DeSmuMe 的 overlay 绘制命令可能需每帧调用才能持续显示。不能直接把 `gui.drawBox/text` 整体降到 10Hz；应先**每帧少量绘制预先缓存的内容**，减少复杂解密与预测。是否允许低频重绘，必须实机测试图层持久性。

## 另一组重复计算：宝可梦与遇敌修正
- `getOffset(offsetType,orderIndex)` 每次调用都会构造不同区块排列 table；在每份脚本里多次调用。先提升为常量 `GROWTH/ATTACK/MISC`，与所有 24 种顺序逐项对账。
- HGSS [`getLeadHeldItem` L1094–1119](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/BizHawk/HGSS_RNG_BizHawk.lua#L1094-L1119) 在设置遇敌率时依据 PID、checksum 与解密流得到持有道具。若出现多次同帧调用，可按对象内容/切换队伍状态缓存，失效必须跟随 PID、校验和、当前领队与内存地址变更。
- `setDateTime`、日期/种子格式化与静态 GUI 标签可以缓存字符串或中间结果；游戏时间、RTC/Delay 不能直接用低频值驱动 RNG。

## 性能验证
对比四种档位：原版；只加纯预测 memo；纯预测迭代预算；加入界面状态缓存。分别测 1×/4×/8×/16×，捕获模式/站立、步行、非遇敌区、回退、战斗。记录 CPU 回调长尾、每帧计算次数、预测结果新鲜度与 RNG 输入输出一致性。

## 6 个适配文件
- `Gen 4/BizHawk/{DP,Pt,HGSS}_RNG_BizHawk.lua`
- `Gen 4/DeSmuMe/{DP,Pt,HGSS}_RNG_DeSmuMe.lua`

建议以 **DP BizHawk** 的纯预测提取作为第一个微基准，验证后使用共享金向量对 DeSmuMe/Pt/HGSS 分别适配；不要直接合并源文件，各 ROM 版本/区域偏移与分支逻辑不同。
