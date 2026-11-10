# Ranch read-only stack-scan profiling

从仓库根目录：

```bash
python tests/ranch/build_readonly_probe.py --source "Gen 4/Dolphin/Ranch_RNG_Dolphin.lua" --label ranch_01
```

生成 `tests/ranch/output/ranch_01_instrumented.lua`（复制脚本）和 `ranch_01_scan.tsv`。在支持对应 Lua Core 的 Dolphin 中加载生成脚本，并运行至少数百次 `onScriptUpdate()`。

每 300 次更新（可用 `--interval` 调整）写一次累计记录：更新次数、调用栈搜索次数、命中数、线程数、栈帧数、`read32Bit` 调用次数和 `os.clock` 扫描耗时。**仅读取 Wii 游戏内存，不修改模拟器 RAM；但探针会在主机文件中写 TSV**。

不要用探针结果直接宣称无探针版本的 FPS/CPU 占用率。采样器有自身读计数、计时和日志开销；`os.clock` 未提供时耗时字段为 0，计数仍可用；`io.open` 未提供时不会生成有效日志，要标记 BLOCKED。

离线检查（有 Python 和 Lua 5.3+ 时）：

```bash
python tests/ranch/test_probe.py
```

使用虚拟全 0 Wii 内存：分别执行原版和探针 10 次更新，检查屏幕输出字节一致、读计数 10、栈帧 0、没有游戏内存写入。另须真实 Dolphin/游戏验证 offer 命中分支、对象临时失效、线程/栈数量上限与表单刷新生命周期。

详细证据：`docs/research/17-ranch-readonly-profile.md`。

分析真实探针 TSV：

```bash
python tests/ranch/analyze_scan.py tests/ranch/output/ranch_01_scan.tsv --output tests/ranch/output/ranch_01_report.json
```

这里的平均扫描开销只对应注入探针的 Lua，不代表无探针 FPS。
