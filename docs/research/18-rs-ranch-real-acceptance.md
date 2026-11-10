# RS/Ranch 真机对照实验（2026-11-10）

> 目标是采集证据，不是假定已经有 16× 结果。当前自动化环境没有 mGBA、Dolphin Lua Core、ROM 或游戏运行态。所有真实结果必须在本地合法游戏会话里产生。

## 0. 版本固定

- 使用 `969981/PokeLua` 的 `develop`，记录当前 commit SHA。
- mGBA 必须使用桌面版且有 **Tools → Scripting**；支持的 `callbacks:add("frame")` 是模拟帧回调。官方 API：https://mgba.io/docs/scripting.html
- **Ranch 需要 Dolphin Lua Core 自定义构建，不是默认 Dolphin 稳定版就一定支持 Lua。** 该构建的运行入口是 **Tools → Execute Script**，通常把生成 Lua 放进 Dolphin Lua Core 的 `Scripts` 文件夹，按 Start 启动。请记录准确的构建号。旧项目文档：https://github.com/SwareJonge/Dolphin-Lua-Core/blob/master/Readme.md
- 记录 ROM 区域/修订/哈希、模拟器构建和 CPU 型号，必要时隐藏私人存档和账户信息。
- 所有 `tests/**/output/` 已用 .gitignore 忽略。禁止将游戏 ROM 和正式存档上传到公开仓库。

## 1. mGBA RS：三个版本、四档倍率

在仓库根目录执行。先运行 `git switch develop`。建立临时文件夹：

```powershell
New-Item -ItemType Directory -Force "tests/rs_checksums/output"
git show 86918734caa9c05e995d23f315e1caafa6cfd7a2:"Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua" | Set-Content -Encoding utf8 "tests/rs_checksums/output/RS_original.lua"
```

选择**你自己的 Ruby / Sapphire USA/EUR .sav**。示例路径按实际环境更换：

```powershell
$save = "D:\Games\mGBA\battery\Pokemon Ruby.sav"
python tests/rs_checksums/build_real_benchmark.py --variant minimal --label minimal_16x
python tests/rs_checksums/build_real_benchmark.py --variant original --source "tests/rs_checksums/output/RS_original.lua" --save-path "$save" --label original_16x
python tests/rs_checksums/build_real_benchmark.py --variant cached --source "Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua" --save-path "$save" --label cached_16x
```

依次加载 output 里的 `*_probe.lua`（**不要同时启动多份**），再在 mGBA GUI 把倍率设为 16×，从相同状态继续运行。另复制上述命令更换 `1x`、`4x`、`8x` 三档 label，并在模拟器 GUI 手动设置对应倍率。脚本不会控制倍率。每次先预热 30 秒，再记录至少 120 秒；同一场景建议 3 次，分别用唯一 label。建议场景：启动后的室外静止、行走、打开选项、游戏内保存前/保存后。

**三个对照的含义：**
- `minimal`：只有 Lua frame 回调计数的**最小探针基线**，不是严格无 Lua 的 FPS。
- `original`：上游未缓存 .sav 的原版 + 同样的探针。
- `cached`：develop 缓存版 + 同样的探针。

输出每秒记录：模拟帧回调、文件打开与读取次数、128KiB 读取的实际返回字节数、CPU 时间、最后已完成的 checksum XOR。

```powershell
python tests/rs_checksums/analyze_real_benchmark.py --minimal "tests/rs_checksums/output/minimal_16x_frames.tsv" --original "tests/rs_checksums/output/original_16x_frames.tsv" --cached "tests/rs_checksums/output/cached_16x_frames.tsv" --requested-speed 16x --scene outdoor_idle --out "tests/rs_checksums/output/report_16x.json"
```

应分别观察 `callback_fps`、`save_reads`、`save_bytes`、`last_xor` 与 `duration_gate_met`，尤其不要只看 1× 时的 FPS（帧锁定时速度可能不变）。主程序不加载 Lua 的速度应额外从 mGBA GUI 记录，才可估计脚本相对真正无脚本的负担。

**准确性边界：** 文件在测试过程中更新时，缓存版有最多约一秒的附加延迟；对稳定磁盘数据才比较末尾 XOR。一致的 XOR 不足以证明 28 段逐一相同，完整字节准确性由合成测试与另行真实存档快照验证。

## 2. Ranch：无赠送 vs 真实提供梦幻／霏欧纳

先在 Dolphin Lua Core 中确认可以运行 `Gen 4/Dolphin/Ranch_RNG_Dolphin.lua`。在仓库根目录：

```powershell
python tests/ranch/build_readonly_probe.py --source "Gen 4/Dolphin/Ranch_RNG_Dolphin.lua" --label ranch_no_offer --interval 100
python tests/ranch/build_readonly_probe.py --source "Gen 4/Dolphin/Ranch_RNG_Dolphin.lua" --label ranch_offer --interval 100
```

把生成的 `ranch_no_offer_instrumented.lua` / `ranch_offer_instrumented.lua` 各自复制到 Dolphin Lua Core 的 Scripts 文件夹（具体路径由安装版本决定），在 **Tools → Execute Script** 中 **Start**；每次只运行一个脚本。两场景都需要至少 600 次 `onScriptUpdate`：
- 无赠送：在未触发 Hayley 特殊赠送的游戏场景测稳定扫描开销；
- 有赠送：真正触发梦幻／霏欧纳提供事件，确认游戏画面和脚本确实显示目标宝可梦，且 `found > 0`。

```powershell
python tests/ranch/compare_scenes.py --no-offer "tests/ranch/output/ranch_no_offer_scan.tsv" --offer "tests/ranch/output/ranch_offer_scan.tsv" --minimum-updates 600 --out "tests/ranch/output/ranch_comparison.json"
```

`status=REVIEW_READY` 只是证据具备：既有无赠送帧，也观察到了至少一次特殊对象命中，**不是优化成功或 Ranch 全功能通过**。比较 `threads_per_scan`、`stack_frames_per_scan`、`read32_calls_per_scan`、`mean_scan_cpu_ms` 和 `max_scan_cpu_ms` 后，再决定缓存指针/预算遍历是否值得改。

## 3. 离线不带游戏的门槛

```powershell
python -m unittest discover -s tests/rs_checksums -p "test_real_suites.py" -v
lua tests/rs_checksums/cache_mock.lua "Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua"
python tests/ranch/test_probe.py
```

Lua 需支持 5.3+ 位操作。离线测试与生成器检查不能替代 mGBA/Dolphin 实机测量。

## 4. 实验报告判定

- `PASS` 只在实际 ROM 运行态、相同场景与倍率、校验和/PK4 结果对账、采样时间、最终报告都满足时填写。
- `BLOCKED` 表示模拟器不提供 `io.open`、`os.time`、`os.clock` 或 Lua API，不要用造数填补。
- `NOT_OBSERVED` 表示未运行对应场景或 Ranch 提供对象未出现。
- 所有标称 16× 的报告都必须展示“实际模拟回调帧数／真实秒”，而不是仅展示 GUI 设成 16×。

文档索引：[[18-rs-ranch-real-acceptance]]。
