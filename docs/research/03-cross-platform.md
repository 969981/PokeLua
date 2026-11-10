---
tags: [PokeLua, BizHawk, DeSmuMe, Dolphin, VBA, cross-platform]
status: STATIC_VERIFIED+INFERRED
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
---
# 跨平台审计：Gen 1 / Gen 4 / Gen 5 / Dolphin

[[../README]] · [[01-performance-architecture]] · [[04-benchmark-protocol]]

不能套用同一套计时器、API 或刷新机制到所有模拟器。各平台脚本采用不同帧循环模型，必须分别做入口与 Savestate 生命周期审计。

## Gen 1 — BizHawk 与 VBA
- `Gen 1/BizHawk/RBGY_Bot_BizHawk.lua` 约 430 行；`Gen 1/VBA/RBGY_Bot_VBA.lua` 约 423 行。
- BizHawk 版 `while not shinyFound[1] do` 里 `savestate.save(0)`、按键、`emu.frameadvance()`，失败时又 `savestate.load(0)`，是真正的自动化热循环。
- 内层部分等待有 `i < frameLimit` 上限，而外层 `while not shinyFound[1]` 未见统一尝试上限；**无限循环风险为静态推断**，取决于游戏可达性与 Bot 退出条件。
- 优先给每个 Bot 增加可选的 `maxAttempts`／`maxFramesPerAttempt`／失败原因统计／取消操作，不改变闪光判定或输入时序。
- 优化目标优先保证 **可终止性和恢复一致性**，不是强行降频自动化循环。

证据：[BizHawk Gen1 Bot](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%201/BizHawk/RBGY_Bot_BizHawk.lua#L197-L240)。

## Gen 4 — BizHawk
- `DP_RNG_BizHawk.lua` / `Pt_RNG_BizHawk.lua` / `HGSS_RNG_BizHawk.lua` 各约 1400 行。
- 主体使用 `while not wrongGameVersion do` + `emu.frameadvance()`：每步执行多个状态读取和窗口绘制。
- 遇敌预测 `while not battleStartJumpFlag do` 是候选计算热点，不能未经计时就认为它必然比 GUI 更慢。
- 推荐拆为精确帧状态、可缓存的日期/时间与宝可梦解码、按需的预测和可裁剪的 GUI；重点验证游戏时间、Delay 和 RNG Advances 各自的来源及边界。

证据：[DP BizHawk 预测](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/BizHawk/DP_RNG_BizHawk.lua#L1140-L1165)、[主循环](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/BizHawk/DP_RNG_BizHawk.lua#L1370-L1401)。

## Gen 4 — DeSmuMe
- `DP/Pt/HGSS_RNG_DeSmuMe.lua` 使用 `gui.register(main)`；各约 1490 行。
- 以 `memory.read* ` API 别名读状态；GUI 绘制的 `gui.text/box` 与模式切换应作 dirty-state / redraw 优化。
- 不允许假设 `gui.register` 相当于 mGBA 的同名 `callbacks:add("frame")`；需要按照具体 DeSmuMe 版本验证调用顺序和暂停语义。
- 推荐按场景保存输入轨迹，比较 Clock/Delay/Seed/捕获/育种/游走各模块的相同帧结果。

证据：[DP DeSmuMe](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/DeSmuMe/DP_RNG_DeSmuMe.lua)。

## Gen 5 — BizHawk 与 DeSmuMe
- BW 与 B2W2 各有两版；BizHawk 使用主 `while` / `emu.frameadvance()`，DeSmuMe 使用 `gui.register(main)`。
- 检查两个平台读取同一 DS 内存对象时的字节序与 64 位 RNG 分解策略；对随机数使用多段变量存储时要防止精度损失。
- 对比 BW/B2W2 捕获、孵蛋、C-Gear、场景模式以及存档恢复数据，不能用 BW 的偏移直接替代 B2W2。
- 优先复用**算法测试向量和事件模型**，而非直接复制 mGBA UI 代码。

证据：[B2W2 BizHawk 主循环](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%205/BizHawk/B2W2_RNG_BizHawk.lua#L1010-L1036)、[BW DeSmuMe](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%205/DeSmuMe/BW_RNG_DeSmuMe.lua)。

## Dolphin — Gen 3 与 Ranch
- `Colosseum_RNG_Dolphin.lua` 将 `ReadValue32/16/8` 赋给 `read32Bit/read16Bit/read8Bit`，在 `onScriptUpdate()` 构建文本并 `SetScreenText()`。
- Gen4 `Ranch_RNG_Dolphin.lua` 通过读字节拼成 PK4 小端字段，区别于 Wii 主机大端读取；不能在“减少 read8 调用”时改变字节序。
- Dolphin 的 `onStateLoaded/onStateSaved` 回调存在但部分实现为空：这表示**需要**设计状态恢复测试，不能直接认定运行中一定错。
- 对 Dolphin 建议先对长文本构造、PK3/PK4 解密重复工作做差异缓存，并验证不同版本 Lua Core 的 `onScriptUpdate` 实际节奏。

证据：[Colosseum Dolphin](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/Dolphin/Colosseum_RNG_Dolphin.lua)、[Ranch Dolphin](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/Dolphin/Ranch_RNG_Dolphin.lua)。

## 横向重用边界
可重用：RNG 测试向量、帧事件规范、快照字段、错误码、benchmark 统计格式、文档模板。
不直接重用：模拟器读写函数、存档接口、绘制接口、输入状态、实时计时 API、线程/协程假设。
