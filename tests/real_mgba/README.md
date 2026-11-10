# FRLG P1：真实 mGBA 验收工具

工具：build_probe.py（生成带观测点的独立 Lua），analyze_probe.py（汇总真实采样日志）。
研究笔记：../../docs/research/10-frlg-real-mgba-gate.md

## 环境
需要 Python 3.9+、Git、支持 Lua Scripting 的 mGBA 桌面版及你自己的 FRLG ROM/存档。官方说明：https://mgba.io/docs/scripting.html 。**仓库不分发游戏或存档。**

## 生成原版与 P1 对照文件
在 PokeLua 仓库根目录、develop 分支下操作。原版固定在提交 86918734caa9c05e995d23f315e1caafa6cfd7a2。先创建 tests/real_mgba/output 目录，在 PowerShell 运行：

    git show 86918734caa9c05e995d23f315e1caafa6cfd7a2:"Gen 3/mGBA/FRLG_RNG_mGBA.lua" | Set-Content -Encoding utf8 "tests/real_mgba/output/FRLG_original.lua"

务必在导出前创建该 output 文件夹。使用 UTF-8 写文件，避免 PowerShell 5 默认 UTF-16。

运行：

    python tests/real_mgba/build_probe.py --source "tests/real_mgba/output/FRLG_original.lua" --label original_16x
    python tests/real_mgba/build_probe.py --source "Gen 3/mGBA/FRLG_RNG_mGBA.lua" --label p1_16x

分别生成 output/original_16x_instrumented.lua 与 output/p1_16x_instrumented.lua。
在 mGBA 中启动游戏后 Tools > Scripting 仅载入其中一个脚本。注意：上游原脚本加载时就会调用 emu:reset()，所以先载入脚本再恢复相同起始存档。不要同时运行两份脚本。

对 1×、4×、8×、16× 分别重复上述过程、更换 label，以确保日志不相互覆盖。

## 采样方案
在相同 ROM、模拟器版本、游戏场景、存档、按键序列下采集：
- 无 Lua 脚本：用 mGBA 内部速度读数单独记录，作为绝对性能基线；
- 原版 instrumented 与 develop P1 instrumented：每档至少预热 30s，采样 120s，建议三次；
- 分别在室外静止、草丛步行、战斗、队伍、PC 盒子状态测试。

每秒写入 output/<label>_perf.tsv：真实秒数、模拟 frame 回调次数、显示更新次数、Lua 回调 CPU 近似耗时、最长回调耗时。callback FPS 是模拟回调吞吐，不是显卡显示 FPS。os.clock 的读数不是独立的精确 wall-clock。不要把无 Lua、原版与 P1 不同场景的结果直接相除。

比较：

    python tests/real_mgba/analyze_probe.py --baseline "tests/real_mgba/output/original_16x_perf.tsv" --optimized "tests/real_mgba/output/p1_16x_perf.tsv" --output "tests/real_mgba/output/report_16x.json"

报告中原版/P1 速度比不等同于“相对于无 Lua 的脚本额外开销”。

## TID 与 Initial Seed Bot 精确回归
另行生成 Trace 版本，不能与 FPS 测试混用：

    python tests/real_mgba/build_probe.py --source "tests/real_mgba/output/FRLG_original.lua" --label original_seed_trace --trace
    python tests/real_mgba/build_probe.py --source "Gen 3/mGBA/FRLG_RNG_mGBA.lua" --label p1_seed_trace --trace

在两个生成 Lua 内，把 botTargetInitialSeeds 设置为**相同目标数组**；测试 TID Bot 时同理设置 botTargetTIDs。之后再启动并加载各脚本：
- Initial Seed Bot：Continue 界面 Shift+SELECT，核对第 1/35/40 帧按键、写监视点、失败重试及命中。
- TID Bot：姓名 OK 界面 Shift+START，核对临时 TID、写监视点、回退与最终命中。
- output/<label>_events.tsv 保存 callback tick、模拟器 frame、WATCH / SAVE / RETRY / FOUND、Seed 值。两个日志必须使用相同初始存档和模拟帧输入。
- 初始 TID 命中不等于正式训练家身份已经确定；必须另行记录 SaveBlock2 正式 TID/SID，并核对 RNG Advances。
- 可以向 analyze_probe.py 同时传入 --baseline-events 和 --optimized-events，分别检查精确 tick+frame+event+seed 与仅 event+seed 对账。
- 运行新的试验前请重新生成同一 label，避免事件日志追加混入上一次实验。

## 证据边界
本次提交只提供采集和对账工具及离线 Mock 检查。尚未运行真实 FRLG ROM。现有 P1 没有改掉无上限的遇敌预测 while 循环；若草丛状态仍卡，需进入 P2 定位。 
