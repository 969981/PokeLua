# RS save checksum cache: offline regression

针对 develop 中的 `Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua`。

在仓库根目录运行：

```bash
lua tests/rs_checksums/cache_mock.lua "Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua"
```

需要 Lua 5.3+。合成 128 KiB 存档，无 ROM。脚本覆盖 28 段原版字节顺序及 XOR、960 次同秒调用只打开一次文件、下一秒刷新、文件消失/长度不足、失败后恢复、时钟回拨、手动缓存失效。

**此测试不证明模拟器内真实 .sav 的写入频率或 1×–16× 性能。** 实机需要记录真实保存后 1s 轮询结果，确认显示状态和文件同步。
