---
tags: [PokeLua, Gen3, RS, checksum, cache, performance]
status: CODE_IMPLEMENTED+RUNTIME_NOT_OBSERVED
source_commit: 6b0beff573a8017ca67b613e22158c8e26c0e29b
date: 2026-11-10
---
# RS_RNG_Checksums：每帧存档 I/O 改为真实秒级缓存

[[../README]] · [[11-gen3-mgba-other-hotspots]] · [[15-other-scripts-roadmap]] · [[17-ranch-readonly-profile]]

## 问题与源码证据
当前原版 `Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua` 的 `updateBuffers()` 每个模拟帧调用 `updateTENANNIVBuffer`。它调用 `getChecksumsList`，原先每次执行 `io.open(savePath, "rb")`、`read(0x20000)` 和读取 28 个段（`0xFF7 + i * 0x1000`）的两字节 checksum。**每秒 960 次帧回调时理论 120 MiB/s 主机读取请求量**，不是实测磁盘吞吐或性能开销。

原版证据：[L142–169](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/RS_RNG_Checksums_mGBA.lua#L142-L169)、[L265–309](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%203/mGBA/RS_RNG_Checksums_mGBA.lua#L265-L309)。

## 已实施改造（develop）
1. 新增 `checksumFileCache`，`getChecksumsList()` 按 `os.time()` 的真实秒时钟每秒最多访问一次 `.sav` 文件；同一秒其余模拟帧复用 28 段原样字符串列表。时钟倒退主动刷新。
2. 保留原版 `string.format("%02X%02X\n", bytes:byte(segmentAddr + 1), bytes:byte(segmentAddr))`、`getCurrentXORChecksumSeed()` 和 `xor ^ targetSeed` 的计算步骤，不改 RNG 算法、ROM/区域判断或游戏内 RAM 读取。
3. 文件不存在／无法读取或不足 `0x1BFF8` 字节：缓存当前错误状态，输出 `Save-file checksum unavailable`，避免原版每帧 `assert(io.open)` 直接退出。
4. 保存文件正常恢复后会在下一个真实秒重新读取。保留 `invalidateChecksumsCache()` 作为显式清除本次缓存的入口（实际刷新仍由下一次调用执行）。
5. 原 `updateChecksumsBuffer` 虽暂时未启用，但已加 nil 防护；输出明确注释“文件快照可能滞后未保存的游戏 RAM”。

## 与原版比较
| 项目 | 原版 | develop 缓存版 |
|---|---|---|
| 28 个 checksum 的提取与字节序 | 每帧重读 128KiB | **不变**，每秒最多一次文件轮询 |
| XOR seed | `getCurrentXORChecksumSeed` | 原函数不动 |
| 动态 RTC、Seed、Trainer、Option 显示 | 每帧 | 保持原方式 |
| 文件丢失 | `assert(io.open)` 可直接终止 | 透明报错、按间隔恢复 |
| 过期风险 | 磁盘读取实时（仍受游戏 save flush 影响） | **额外最多约 1 秒缓存延迟，可能跨秒边界**；游戏不写回磁盘时仍可能更久 |
| 实机 FPS 提升 | 未测 | 未测（不虚构百分比） |

## 如何验收
离线合成存档脚本：[`tests/rs_checksums/cache_mock.lua`](../../tests/rs_checksums/cache_mock.lua)，运行命令：
```bash
lua tests/rs_checksums/cache_mock.lua "Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua"
```
要求：28 条一致、XOR 一致、同秒 960 次调用只打开一次文件、下一秒刷新、文件缺失/不完整及恢复、时钟倒退／显式失效。属于 **合成数据 Mock 测试**，不是实际游戏测量。

实机需要 Ruby/Sapphire USA/EUR、同一区域与修订的 battery .sav，记录 mGBA 写盘事件：保存之前／保存之后超过一秒，观察 XOR 结果及错误提示；同场景 1×/4×/8×/16× 分别测读取次数和真实帧吞吐。

## 未解决边界
- 该方案没有减轻其他窗口每模拟帧 `clear/print` 的 CPU/Console 开销，后续才能实施纯 UI 分层。
- `os.time()` 只有秒级精度，应用不能保证保存动作之后瞬间更新；若目标任务要求毫秒级精度，应建立由用户或模拟器保存事件触发的缓存失效机制。
- `savePath` 是原脚本中的本地绝对文件路径，用户必须按自己的环境修改；本提交不上传或变更任何真实游戏存档。
