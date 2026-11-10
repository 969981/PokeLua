---
tags: [PokeLua, optimization, all-scripts, Gen1, Gen3, Gen4, Gen5, CI]
status: CODE_READY_OFFLINE_GATES_PENDING
baseline_commit: 3739f7b5801cee38ccd2d6ed764fe87df6e2fd58
date: 2026-11-10
---
# 26 份游戏 Lua 全量优化：代码差异与证据状态

[[../README]] · [[15-other-scripts-roadmap]] · [[09-frlg-p1-implementation]] · [[16-rs-checksum-cache]] · [[17-ranch-readonly-profile]]

## 范围
- 仓库包含 **26 份游戏 Lua**；本次对其中 18 份实施保守优化（15 份 `getOffset` 静态表，其中 E/RS 和三份 Held Item Side 另加 P1；3 份 Dolphin 纯 Seed 预测缓存）。
- FRLG P1 和 RS Checksums 缓存为此前已完成事项，本轮不改变。
- 其余 **6 份仍保持源文件不变**：2 份 Gen1 Bot、3 份 Colosseum/ XD 的复杂 Dolphin 数据显示、1 份 Ranch 线程栈扫描。不是“已经优化了全部 26 份”，而是 **26/26 审查、20/26 有既有或本轮安全变更、6/26 保留现状待实机证据**。
- 每项修改以 `3739f7b580...` 为原版对照提交；不向 `main` 或上游同步分支回写。

## 本轮已修改文件
| 组 | 数量 | 操作 | 不变式 |
|---|---:|---|---|
| Gen3 mGBA E、RS、Side/E、Side/FRLG、Side/RS | 5 | `getOffset` 的 24 种 PK3 子结构排列映射提升为文件级静态表 | 取值、乘以 12 和所有调用参数不变 |
| Gen4 BizHawk DP、Pt、HGSS | 3 | 静态化 PK4 排列映射 | 不动 RNG distance、遇敌循环和存档追踪 |
| Gen4 DeSmuMe DP、Pt、HGSS | 3 | 同上 | 不动 `gui.register` 入口和输入时序 |
| Gen5 BizHawk BW、B2W2 | 2 | 静态化 PK5 排列映射 | 不动 64 位 RNG 和 `userdata.set` |
| Gen5 DeSmuMe BW、B2W2 | 2 | 同上 | 不动 MT Index、C-Gear 和 DeSmuMe GUI |
| Gen3 Dolphin Ageto Celebi、Channel Jirachi、Colo Pikachu | 3 | 为纯 `get*Info(seed)` 增加单入口 Seed 结果缓存 | 同 Seed 的 PID/IV/Nature/HP 预览字符串相同，`advances` 每帧更新 |

### E / RS / 三份 Held Item 特别优化：高倍速显示
- **E（Emerald）**：每模拟帧采样 RNG，原始 `TIDBotLoop` 仍逐帧执行；Bot 执行后再采样一次，以覆盖同一回调内即时存档恢复。R+方向键逐帧检测。全部 Console 面板采用目标约 10Hz 的自适应显示回调。没有动 TID 目标查找、写监视点或 A 键时序。
- **RS（Ruby/Sapphire）**：每帧更新 RNG Advances、逐帧读模式按键和数字存档热键，页面显示按约 10Hz 调度。保留原始 Seed、时间和即时存档读写函数。
- **三份 Held Item Side（E／FRLG／RS）**：每模拟帧继续调用各自的 `getRngInfo()`，原 `getSaveStateInput()` 仍逐帧且位于渲染之后；只对单个 Console Capture 视图使用同样约 10Hz 刷新，不改变各游戏不同的初始 Seed、Advances、Held Item Delay 公式。
- **性能时钟说明**：使用 `os.time()` 的秒级回调率估计，实际切换 1×/4×/8×/16× 后需短暂重新校准。不能称为经过真实毫秒计时的严格 10Hz，也不能在无 ROM 时宣称跑满 16×。
- **准确性边界**：保留原版逻辑在 E 中的空目标 TID 列表、RS 的 `dist > 999` 解释等行为；这些可能需要独立正确性补丁，不能偷偷混入性能优化。

## 未自动更改的六份（原因）
| 范围 | 风险 | 为什么保留 |
|---|---|---|
| Gen1 BizHawk/VBA RBGY 双 Bot | 多个外层无限重试、Savestate/按键时序耦合 | 没有合法游戏实机输入轨迹，不能一刀切改循环或超时 |
| Gen3 Dolphin Colosseum Light、Colosseum、XD | 多对象数据及每帧 PK3 实时变化；`SetScreenText` 生命周期不明 | 单独按指针缓存会产生过期宝可梦，先记录对象身份／加密原始区 |
| Gen4 Dolphin Ranch | Wii 线程栈扫描与短命 offer 对象 | 此前已做只读探针；应先拿无 offer 和 offer 两场景真实性能、命中时长再考虑缓存 |

## 离线回归工具
- [`tests/optimization/verify.py`](../../tests/optimization/verify.py)：检查 15 个表 24 档的**所有映射值**；其中 10 个仅表移动的脚本必须保证其它源代码字符（归一化换行后）完全一致；26 游戏 Lua 均经 `luac -p` 语法检查。
- [`tests/optimization/dolphin_pure_mock.lua`](../../tests/optimization/dolphin_pure_mock.lua)：相同 10 个合成 Seed（含重复和回退），把 3 个 Dolphin 纯 Seed 预览脚本与原版逐字节比较全部输出。
- [`tests/optimization/mgba_exact_mock.lua`](../../tests/optimization/mgba_exact_mock.lua)：对 E/RS 的 240 帧模拟回调比较 RNG Advances、模式按键边沿及 Emerald TID Bot Watchpoint、保存、重试/命中操作轨迹，同时比对窗口打印次数。
- [`tests/optimization/side_exact_mock.lua`](../../tests/optimization/side_exact_mock.lua)：三份 Held Item 脚本各 480 帧对比原版 RNG 返回值、逐帧存档输入调用次数和 UI 输出下降，仍属无 ROM Mock。它是 Mock，不能代替真实 mGBA 结果。
- 运行：`python tests/optimization/verify.py`（Python、Git、Lua 5.4/luac，且 checkout 的本地仓库含 baseline git commit）。

## 原版已存在的 Dolphin IV 类型问题（独立正确性议题）

在 Ageto／Channel／Colo Pikachu 三个上游脚本里，`getIVs()` 使用 `string.format("%02d", ...)` 返回补零字符串，随后这些字符串被传给 `getHPTypeAndPower()` 的位运算。Lua 5.4 对部分补零字符串（例如 `"08"`、`"09"`）可能拒绝位运算并报错。该问题在本轮缓存优化前的原版源码中就存在。

离线纯预览 Mock 会对**原版与优化版两边**统一将 Hidden Power 计算参数转成数字；不会改动两个源码，也不会改变展示中的 IV 文本格式。由此通过的输出等价只证明缓存改造未带来额外差异，**不代表这三个原版已修复数值类型问题或 Dolphin 实机完全兼容**。建议单开 correctness PR，通过六项 IV 的 00–31 完整向量后再处理。

## 运行时 Gate
1. **mGBA E/RS**：同一 ROM/存档及输入录像，在 1×/4×/8×/16× 对照 RNG Advances、R+左右、9 个 Slot 的 Savestate、E TID 成功/失败写入事件、实时 Console 稳定性和实际吞吐。
2. **Gen4/5 BizHawk/DeSmuMe**：相同 24 档加密区块解析结果、真实 PK3/4/5、MT/RNG、C-Gear/遇敌预测完全相同；需确认标准模拟器 Lua 环境实际兼容文件级常量。
3. **Dolphin 纯配信**：同 Seed 预览结果一致；首次进入和状态读取、ROM 实机 UI 仍正常。
4. **性能**：读数和 FPS 必须标注模拟器版本、ROM 修订、环境、实测起止、原版与优化版源码 SHA、预热和样本；离线 Mock/CI 没有 FPS 结论。

## 下一项高收益但未贸然动的工作
- Gen4 `getEncounterMissingSteps` 六版：最可能影响捕获场景的无上限预测，适合先 DP BizHawk 原版纯函数金样本，再分批预算计算。
- Gen5 `userdata.set`：必须在 Savestate onload 语义验证后才决定是否缓存；直接降频可能造成 RNG Advances 错误。
- Ranch：需真实 Dolphin 线程数/栈深的无赠送及有赠送两场景数据。
- Gen1：需状态机和可取消重试，但必须先保留原有 TID/闪光回放的成功概率与帧序列。

证据状态：**源代码静态修改已就绪；离线 CI 通过后才能标记 UNIT_TESTED；真实模拟器 RUNTIME_NOT_OBSERVED。**

## 更新（2026-11-10）：剩余六份中的五份已新增保守改造

Gen1 两版增加默认关闭的重试上限与计数；Colosseum Light/Colosseum/XD 通过按实际输入缓存捕获率纯计算，并缩减重复填充字符串的工作。Ranch 保留游戏 Lua 原版，只使用只读探针。仓库当前目标为 25/26 游戏 Lua 有源码优化，剩余 Ranch 需真实 offer/no-offer 探针数据。详见 [[22-remaining-five-optimizations]]。上述仍不代表模拟器 16× 实测达标。
