---
tags: [PokeLua, Dolphin, Ranch, performance, profiling]
status: PROBE_GENERATOR_READY+RUNTIME_NOT_OBSERVED
source_commit: 6b0beff573a8017ca67b613e22158c8e26c0e29b
date: 2026-11-10
---
# My Pokémon Ranch：只读栈扫描探针及优化前验证

[[../README]] · [[14-gen1-dolphin-hotspots]] · [[15-other-scripts-roadmap]] · [[16-rs-checksum-cache]]

## 已知高成本循环
原版 [`Ranch_RNG_Dolphin.lua` L391–428](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/Dolphin/Ranch_RNG_Dolphin.lua#L391-L428)：`findOfferedPK4(build)` 由 Wii 线程链表入口 `0x800000DC` 开始，最多 64 线程 × 每线程 256 栈帧，检查返回地址、对象指针、vtable，命中才返回 PK4 内存地址。每次 [`onScriptUpdate()`](https://github.com/969981/PokeLua/blob/86918734caa9c05e995d23f315e1caafa6cfd7a2/Gen%204/Dolphin/Ranch_RNG_Dolphin.lua#L540-L550) 都调用一次，未命中时通常较早退出，但真实分布未知。

**仅从上限推导的 16,384 候选并非每次回调实际扫描数，必须先测。**

## 工具交付
- [`tests/ranch/build_readonly_probe.py`](../../tests/ranch/build_readonly_probe.py)：从**仓库原版不修改文件**生成 `*_instrumented.lua`，插入增量计数。
- [`tests/ranch/ranch_mock.lua`](../../tests/ranch/ranch_mock.lua) 及 [`test_probe.py`](../../tests/ranch/test_probe.py)：在合成无对象环境下对比原版与探针的界面文本、寻找次数和无游戏内存写入。
- [`tests/ranch/README.md`](../../tests/ranch/README.md)：运行说明。

```bash
python tests/ranch/build_readonly_probe.py --source "Gen 4/Dolphin/Ranch_RNG_Dolphin.lua" --label ranch_01
python tests/ranch/test_probe.py
```

探针只增强原 `read32Bit` **读操作计数**、`findOfferedPK4` 前后 CPU 计时及内层线程／栈帧访问次数统计。Game RAM 仍只读；日志通过主机 `io.open` 写到 `tests/ranch/output/ranch_01_scan.tsv`。

## 每次汇总字段
| 字段 | 说明 |
|---|---|
| updates | `onScriptUpdate` 运行次数 |
| scans | `findOfferedPK4` 调用次数 |
| found | 目标提供对象命中次数 |
| threads | 通过指针校验的线程累计数 |
| stack_frames | 通过指针校验的栈帧累计数 |
| read32_calls | 搜索期间 `read32Bit` 累计调用数 |
| scan_cpu_s | `os.clock` 观测的累积扫描 CPU 时间 |
| max_scan_cpu_s | 观测的最大单次扫描 CPU 时间 |

采集日志按 300 次更新写一次，不逐帧刷文件；探针会增加测量开销，因此此报告只能用于找到“搜索开销是否值得优化”，不是无探针真实 FPS。若 Lua Core 无 `os.clock`，耗时字段为 0；若无法写文件，则需要记录 BLOCKED。其他对象解析造成的成本不在本探针 CPU 计时范围内。

## Gate
1. 固定 Dolphin Lua Core 版本与 Wii 游戏版本；在三种场景测：主菜单／未出现 Hayley 提供对象／真实提供 Mew/Phione 过程。
2. 记录至少 600 次 `onScriptUpdate`，统计扫描次数/帧、read32/帧、最大和平均耗时，并标注命中对象存在的持续时间。
3. **优化前不得直接缓存某个线程栈帧地址**：返回地址与 vtable 身份可能在相邻帧发生变化；必须证明缓存失效策略及时。
4. 首轮若无 offer，先测是否真正发生深层扫描；若线程栈帧通常为空，优先级可降至后续。
5. 真实提供对象时对账 PK4 PID、species、TID/SID、IVs、checksum 和文本，确定探针不会改变给出对象的时序。

**当前仅有静态源代码和可运行的采集工具；没有实际 Dolphin 提供对象的结果。**
