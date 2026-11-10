---
tags: [PokeLua, Gen5, BW, B2W2, BizHawk, DeSmuMe, RNG]
status: STATIC_VERIFIED+BENCHMARK_PENDING
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
review_date: 2026-11-10
---
# Gen 5 BW/B2W2：精确 RNG 与显示热路径审计

[[../README]] · [[12-gen4-ds-hotspots]] · [[04-benchmark-protocol]]

## 主入口与性能模型
| 脚本 | 源码入口 | 热点类别 |
|---|---|---|
| BW BizHawk | [L1271–1299](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%205/BizHawk/BW_RNG_BizHawk.lua#L1271-L1299) | `while ... emu.frameadvance`、GUI、userdata 持久化 |
| B2W2 BizHawk | [L1010–1036](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%205/BizHawk/B2W2_RNG_BizHawk.lua#L1010-L1036) | 同上 |
| BW DeSmuMe | [L1364–1395](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%205/DeSmuMe/BW_RNG_DeSmuMe.lua#L1364-L1395) | `gui.register(main)`、图形输出 |
| B2W2 DeSmuMe | [L1101–1130](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%205/DeSmuMe/B2W2_RNG_DeSmuMe.lua#L1101-L1130) | 同上 |

## 每帧持久化与 RNG
- **STATIC_VERIFIED**：BW BizHawk `getRngInfo` [L800–823](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%205/BizHawk/BW_RNG_BizHawk.lua#L800-L823) 每次执行 `userdata.set` 更新 `tempCurrentSeedLow`、`advances`、`mtCounter`、`cgearSeed`、`hitDelay`、`hitDate` 六项（首次生成种子处还有两项）。B2W2 BizHawk [L633–656](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%205/BizHawk/B2W2_RNG_BizHawk.lua#L633-L656) 更新三项。
- **INFERRED**：userdata 接口可能有每回调序列化/调用开销；需 profile 测量。不能直接把全部持久化降到 10Hz：BizHawk `event.onloadstate` 从 userdata 恢复，低频数据可能造成回退后计数错误。
- **建议**：隔离“每模拟帧 RNG 与 MT 状态计算”、按需 GUI 文本计算、存档同步/读回。先用封装计时 userdata 操作，再决定是否只在值变化、保存状态时持久化，且任何策略都要保证加载后准确回滚。

## BW 与 B2W2 不能合并的差异
- BW 的 MT advances 计算使用 `(mtIndex - 624) + mtCounter*624`；B2W2 用 `(mtIndex - 2) + mtCounter*624`，不能因为名字相同就统一。
- 两者读取 64-bit LCG 当前 Seed 的高低 32 位，距离跟踪和初始 Seed 需要对齐 RNG 对象与版本。保持 source-to-source 的 Seed/Advances/MT/Delay 输出。
- `LCRNGDistance` 多处使用 `dist>999` 作为大幅距离回退解释，存在正常较大前进距离变成负值的**算法正确性风险**；此处记录为另立修复议题，不混入性能 P1 补丁。

## 其他优化点
1. `getOffset` 在函数体内每次创建 24 组区块映射表，提升为常量，覆盖 24 种排列 + PK5 解码对照。
2. `setDateTime`、`buildSeedFromDelay` 和 C-Gear 预测/格式化仅在相关输入变化时重算。
3. Capture/Breeding/Roamer/C-Gear/Pokemon Info 切换模式：未启用的页面不执行解密；活跃页面可以依据内存对象身份和加密区校验缓存计算内容。
4. 在 BizHawk / DeSmuMe 上每帧仍可能需要绘制 Overlay，但可以缓存高成本数据与已格式化字符串。先实机确认 GUI 图层生命周期，再选用低频重绘。
5. 状态日志应覆盖 `currentSeedHigh:Low`、MT seed/index、Delay、C-Gear、TID/SID、Savestate 后第一帧，确保优化不改变实际 RNG 轨迹。

## 建议顺序与 Gate
BW BizHawk 作为首个对照 → B2W2 BizHawk → BW DeSmuMe → B2W2 DeSmuMe。首先实现纯函数单测、稳定指针/MT/RTC 金样本，再做计算与显示分离。任何引入异步数据解析必须保证 **不是把上一帧 RNG 误报为当前帧**。

无真实模拟器实测：`BENCHMARK_PENDING`。
