---
tags: [PokeLua, Gen3, mGBA, performance, source-audit]
status: STATIC_VERIFIED+BENCHMARK_PENDING
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
review_date: 2026-11-10
---
# Gen3 mGBA：绿宝石、红蓝宝石、校验和及携带道具脚本审计

[[../README]] · [[08-script-triage]] · [[09-frlg-p1-implementation]] · [[12-gen4-ds-hotspots]]

## 优先级一：RS_RNG_Checksums_mGBA.lua 的存档读取
证据 [getChecksumsList() L147–165](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/RS_RNG_Checksums_mGBA.lua#L147-L165)，[updateBuffers() L294–310](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/RS_RNG_Checksums_mGBA.lua#L294-L310)。

- **STATIC_VERIFIED**：每次 `updateBuffers` 调用 `updateTENANNIVBuffer`，后者调用 `getChecksumsList()`；函数通过 `assert(io.open(savePath,"rb"))` 打开存档，`read(0x20000)` 读 131,072 字节，遍历 28 个段并格式化字符串，后续再 XOR。主函数注册到 `callbacks:add("frame", updateBuffers)`。
- 该 128 KiB 请求按 60 FPS 为每秒 7.5 MiB，960 帧回调/秒为每秒 120 MiB；**仅指每次读取的理论请求量**，并非物理磁盘吞吐或实测性能损失。实际 I/O 受 OS cache、模拟器和文件更新影响。
- **高价值优化 P1**：把校验和分成 `saveChecksumSnapshot`（只在明确的手动刷新、实际文件变化、低频检验时更新）与 `renderChecksumSummary`；第一次载入先验证路径及文件长度，出错显示 `UNAVAILABLE` 而非逐帧 assert 退出。实时 `currentSeed`、文字速度和 RTC 仍按自身变化策略更新。
- **正确性要求**：校验数据必须带上从文件获取的版本/时间戳或用户确认状态；不能把未观察到的最新 .sav 伪装成实时 checksum。不同保存机制是否立即刷新文件，需在 mGBA 真实会话验证。自动判定文件变化的方式（mtime）可能在该 Lua 环境不可用，应保留手动刷新兜底。

## 优先级二：E_RNG_mGBA.lua 的逐帧窗口与 TID Bot
证据 [E 主循环 L1012–1028](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/E_RNG_mGBA.lua#L1012-L1028)、[TID Bot L829–890](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/E_RNG_mGBA.lua#L829-L890)。

- **STATIC_VERIFIED**：每帧更新 Capture/Breeding/Roamer/Pandora/TID/Pokemon 六类窗口及即时存档输入；`showRngInfo` 在多个页面重复调用，重复内存读取和清空/打印。
- Emerald 的 TID Bot 是写监视点 + 临时存档/恢复 + A 键按下/释放，**不允许**将 `updateTIDBotBuffer()` 整个移到低频 UI。
- **优化设计**：移植 FRLG P1 的 exact lane / render lane，但保留 Emerald 特有初始 RNG/存档结构；为每一帧采集 Seed，Bot 的监视点与输入逐帧执行，界面按需更新。
- 进入 P2 后才减少 PK3 读取和 `getOffset` 内重复 table 创建，使用实际相同 PK3 样本对比。

## 优先级三：RS_RNG_mGBA.lua
证据 [主循环 L904–919](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/RS_RNG_mGBA.lua#L904-L919)。

- **STATIC_VERIFIED**：每模拟帧更新五类页面、SaveState 热键；多次调用 `showRngInfo`。
- 可复用 FRLG 的低频 Console UI 分层和逐帧输入，但 RS 游戏版本、地址和不同 RNG 初始状态逻辑必须保持独立。
- 不应硬性用每 12 帧刷新一次：16× 下仍可能高频 UI；使用真实回调率自适应，失去精确时钟时需要清楚标注。

## 三款 Held Item 副脚本
- `Side/E_Held_Item_RNG_mGBA.lua` 的 `getRngInfo()` [L385–414](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/Side/E_Held_Item_RNG_mGBA.lua#L385-L414) 涉及 battle video seed、painting timer 和 advances 计数；**切勿套用 FRLG 的初始 Seed 假设**。
- FRLG/RS Held Item 侧共用显示热路径，`showInfo` 的解密与 `getOffset` 映射重复计算；偏移映射表改为文件级常量，PK3 按 pid/OTID/加密字节 + 地址/slot 的变化键缓存。
- 先保障 `heldItemDelay` 与实际 PID、道具判定一致，之后合并同一平台的 Console 显示调度器。保留多游戏独立地址表，不通过跨游戏复制指针来“优化”。

## P0-P2 子项目与 Gate
| 顺序 | 子项目 | 代码改动边界 | 可验证门槛 |
|---|---|---|---|
| A | RS checksum I/O 缓存 | 只改变存档文件读取和静态选项展示，不改种子 | 28 段校验值与原版同步文件完全一致，存档实际写入后不会永久过期 |
| B | Emerald P1 | 逐帧 Watchpoint/热键与低频 UI 拆分 | TID 成功/失败、Savestate、同帧 RNG 轨迹一致 |
| C | RS P1 | 数据采样/展示分离 | RNG/孵蛋/游走/宝可梦数据相同 |
| D | 三款 Held Item | 复用查表和显示，保持各版本 RNG | 三游戏原始事件、道具和 PID/IV 金样本对账 |

状态：静态审计已完成；没有实际 mGBA RPM/FPS 计时，不能声称性能改善数值。
