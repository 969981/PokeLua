---
tags: [PokeLua, Gen5, BW, B2W2, BizHawk, userdata, profiling]
status: PROFILER_READY+RUNTIME_NOT_OBSERVED
baseline_commit: 53fbfc57e543efaa7bee9053ce79ce3b515f3d93
date: 2026-11-10
---
# Gen5 BizHawk userdata.set 高频写入：只观察、不改变保存语义

[[../README]] · [[13-gen5-ds-hotspots]] · [[20-gen4-encounter-p2]] · [[17-ranch-readonly-profile]]

## 已有源码证据
BW BizHawk 的 getRngInfo 每模拟帧写入 tempCurrentSeedLow、advances、mtCounter、cgearSeed、hitDelay、hitDate（加上条件初始化）；B2W2 BizHawk 每帧主要写入 tempCurrentSeedLow、advances、mtCounter。两者均使用 event.onloadstate 从 userdata 恢复状态。

不能直接把这些持久化写入改为低频刷新，因为 Savestate 任意模拟帧都可发生，没证据证明跳过原写入后 onloadstate 仍恢复正确。

## 本轮实现
仅在 tests/gen5/ 下新增生成器 build_userdata_probe.py。它读取现有游戏 Lua，生成一个独立的带观测工具版本，将每个 userdata.set 调用包装为 p2TrackedUserdataSet；包装器最终按原来的参数调用 **完整的原 userdata.set**，保持顺序与返回值。默认游戏 Lua 完全不变。

测量：累计运行帧数、userdata.set 次数、同一 Lua 观察期重复值次数、不同键数、每键写入/重复统计、os.clock 近似 CPU 时间。每 300 次主循环写入一次主机 TSV（可设置间隔），避免逐帧文件 I/O。

重复值仅说明调用参数相同，绝不意味着跳过 userdata.set 对 Savestate 安全；Lua 侧 last-value 历史未跟随 Savestate 回退，因此这部分仅用于粗略成本定位。

## 本地使用
仓库根目录，Windows PowerShell 示例：

    python tests/gen5/build_userdata_probe.py --source "Gen 5/BizHawk/BW_RNG_BizHawk.lua" --label bw_userdata
    python tests/gen5/build_userdata_probe.py --source "Gen 5/BizHawk/B2W2_RNG_BizHawk.lua" --label b2w2_userdata

在对应合法 ROM 和 BizHawk Lua Console 加载生成的 output/*_instrumented.lua；每游戏至少 1×/4×/8×/16×、普通地图/进入战斗/载入即时存档等场景。不要同时运行原版和探针版。分别收集 TSV，并附模拟器/ROM/存档 SHA、实际模拟帧率、原版无探针 FPS 作为外部基线。

生成 JSON 报告：

    python tests/gen5/analyze_userdata.py tests/gen5/output/bw_userdata_userdata.tsv --output tests/gen5/output/bw_userdata_report.json

若无 os.clock，CPU 时间不可用；若无 io.open，TSV 无结果应标 BLOCKED。探针自身造成开销，CPU 时间不可直接当游戏 FPS。

## 离线门槛
测试：python tests/gen5/test_userdata_probe.py（Python + Lua 5.4），对真实 BW/B2W2 源码做静态插装及语法检查，合成 12 帧 Mock 对比原版与探针版本完全相同的 userdata.set 键、值、帧顺序，并验证重复写入统计。

本轮不修改 RNG/MT/Delay/C-Gear 计算、不触碰本体事件函数、不修改 userdata 保留时机；**实机测试尚未完成**。只有拿到真实 onloadstate 回归与性能数据后，才能考虑有条件的写入消除或脏标记，而不应直接定时持久化。
