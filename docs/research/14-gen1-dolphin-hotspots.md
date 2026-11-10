---
tags: [PokeLua, Gen1, Dolphin, Ranch, bots, performance]
status: STATIC_VERIFIED+BENCHMARK_PENDING
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
review_date: 2026-11-10
---
# Gen 1 Bot 与 Dolphin：大循环、线程栈扫描及文本开销

[[../README]] · [[11-gen3-mgba-other-hotspots]] · [[12-gen4-ds-hotspots]]

## My Pokémon Ranch（Gen4 Dolphin）：高优先级
证据：[findOfferedPK4() L391–419](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/Dolphin/Ranch_RNG_Dolphin.lua#L391-L419)、[onScriptUpdate() L540–550](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/Dolphin/Ranch_RNG_Dolphin.lua#L540-L550)。

- **STATIC_VERIFIED**：每次 `onScriptUpdate` 调用 `findOfferedPK4`，从 Wii OS 线程列表开始最多遍历 64 个 thread，每个 thread 最多遍历 256 个 stack frame；最坏可能检查 16,384 个候选（但通常可被非法指针/目标帧早退）。
- 遍历包括数次 `ReadValue32`，候选命中还需验证 vtable 和对象自指关系。受实际栈长度影响，不可把最大次数当作每个更新的实际次数。
- 找到目标后，`readPokemon` 会解密 64 个 PK4 16-bit 字；`readLE16Bit` 从 2 个 byte 解码，意味着一次解密至少需要 128 次 byte 读取（加上其它字段读取）。必须保留 Wii 大端/PK4 小端修正。
- **优化方向**：先记录线程/栈遍历真实次数与回调耗时；若命中对象，缓存指针并每次用 vtable/返回地址/PK4 identity 验证；未命中时考虑增量扫描预算，但短生命周期赠送事件可能漏掉，必须先观察事件持续帧数。更稳妥的长期方案是可靠的原生 hook/触发事件（若模拟器提供且已验证）。
- 减少 PK4 全字节解密：在 `pid+checksum+encryptedBytes+pointer` 未变时复用解密后数据；避免只以指针作为 Key（对象复用后会显示旧梦幻/霏欧纳）。

## Gen3 Dolphin：六份脚本
- `Ageto_Celebi_RNG_Dolphin.lua`、`Channel_RNG_Dolphin.lua`、`Colo_Pikachu_RNG_Dolphin.lua`：约 150–160 行，`onScriptUpdate` 中每次格式化 RNG/目标信息并调用 `SetScreenText`。初步应测量耗时，短脚本不必优先复杂重构。
- `Colosseum_Light_RNG_Dolphin.lua`、`Colosseum_RNG_Dolphin.lua`、`XD_RNG_Dolphin.lua`：每次 `onScriptUpdate` 构造 opponent/party/box 数据文本，并调用 `SetScreenText`；推荐分离每次更新必需的 Seed Advances 与只在对象数据变化时重新解析的 PK3 信息。
- Gen3 Dolphin 脚本中的 `onStateLoaded()` 和 `onStateSaved()` 回调多为空体；**这是需要运行时确认的状态同步风险**，不是已证实的 RNG 错误。RNG 距离倒退解释也应结合 GameCube Seed 来源进行复核。
- 不应套用 mGBA 的 `emu:read32`、Console Buffer 或 `os.time` 降频假设；先确认 Dolphin Lua Core 的回调频率和 SetScreenText 图层保留机制。

## Gen1 RBGY BizHawk + VBA：Bot 的终止性和事件
证据：[BizHawk L197–358](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%201/BizHawk/RBGY_Bot_BizHawk.lua#L197-L358)、[VBA L192–352](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%201/VBA/RBGY_Bot_VBA.lua#L192-L352)。

- **STATIC_VERIFIED**：`shinyBotLoop` 外层 `while not shinyFound[1]`，钓鱼有 `while not biteFlag` 和 `while not targetFishedSpeciesCheck`，TID 有 `while not TIDFound`；内层等待可限 35/110 等帧，但外层没有总尝试或时间上限。
- 真实风险：失败时循环保存/恢复状态并再次触发相同按键；若目标列表为空、游戏状态无变化或 RNG 时间线确定性重放，可能无限尝试。实际发生需真实 ROM 验证。
- 输入 `if key.Select then shinyBotLoop(...)` 是持续按住检测而非明显的上升沿判断；建议加入 Edge trigger，避免按住导致重复进入。但要验证已暂停/Found 状态的逻辑，不能直接改瞬间的 A/Select 时序。
- **优化与可靠性同时改进**：每次尝试记录（generation / slot / source frame / delay / result DVs or TID / reason）；可取消、最大尝试数、超时、恢复失败提醒、重复结果检测。保留核心 shiny/TID 判定与游戏时间线。

## 优先顺序
Ranch 线程扫描 Profile → Gen1 BizHawk Bot 可终止性 → Gen1 VBA 移植 → Colosseum/XD 文本与 PK 数据缓存 → 其余小型 Dolphin 轻量优化。

## 统一验证
实际游戏与模拟器内固定 seed/savestate/输入、RNG Advances 轨迹、目标宝可梦 PID/IV/TID/必要文本结果；对于 Ranch 额外验证目标 offer 的短生命周期与 PK4 全字段，不能只凭找到一次指针认为缓存逻辑安全。
