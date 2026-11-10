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

## Ranch 两场景对照

在有真实赠送事件的自定义 Dolphin Lua Core 环境中分别生成 `ranch_no_offer` 和 `ranch_offer` 日志，至少各 600 次更新。使用 [compare_scenes.py](compare_scenes.py) 校验两个场景分别具有无命中及真实对象命中证据：

```bash
python tests/ranch/compare_scenes.py --no-offer tests/ranch/output/ranch_no_offer_scan.tsv --offer tests/ranch/output/ranch_offer_scan.tsv --out tests/ranch/output/comparison.json
```

参见 [RS/Ranch 实机验收完整说明](../../docs/research/18-rs-ranch-real-acceptance.md)。此步骤必须使用支持 Tools > Execute Script 的 **Dolphin Lua Core** 特定构建，普通 Dolphin 不保证提供 Lua 接口。
