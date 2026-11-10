# RS save checksum cache: offline regression

针对 develop 中的 `Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua`。

在仓库根目录运行：

```bash
lua tests/rs_checksums/cache_mock.lua "Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua"
```

需要 Lua 5.3+。合成 128 KiB 存档，无 ROM。脚本覆盖 28 段原版字节顺序及 XOR、960 次同秒调用只打开一次文件、下一秒刷新、文件消失/长度不足、失败后恢复、时钟回拨、手动缓存失效。

**此测试不证明模拟器内真实 .sav 的写入频率或 1×–16× 性能。** 实机需要记录真实保存后 1s 轮询结果，确认显示状态和文件同步。

## 真实 mGBA 三组性能对照

与仅检查缓存逻辑的 Mock 不同，这套实验在你自己的 Ruby/Sapphire ROM 会话内采集真实 frame callback 吞吐。

- [构建 mGBA 三组探针](build_real_benchmark.py)：minmal（最小探针）、原版、develop 缓存版
- [分析每秒采样](analyze_real_benchmark.py)：FPS、文件读取次数/字节、CPU 采样、末次 XOR
- [离线测试](test_real_suites.py)：验证探针生成和报告门槛，不表示真实游戏通过
- [完整 PowerShell 操作说明](../../docs/research/18-rs-ranch-real-acceptance.md)

**重要：** 三组均使用自带 Lua 探针，minimal 不是绝对无脚本基线；用户需另行记录无脚本 mGBA GUI 性能。没有合法 ROM/.sav 就无法获得真实性能数据。
