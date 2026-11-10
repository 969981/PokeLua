---
tags: [PokeLua, Gen1, Dolphin, Colosseum, XD, performance]
status: CODE_READY+RUNTIME_NOT_OBSERVED
baseline_commit: e62970b333888c8fa51e2e8919523a40193d730d
date: 2026-11-10
---
# 剩余六份游戏 Lua：五份优化，Ranch 仍按真实数据决策

[[../README]] · [[14-gen1-dolphin-hotspots]] · [[19-all-lua-optimization]] · [[17-ranch-readonly-profile]]

## 本轮真正修改的源码
| 文件 | 修改 | 行为不变式 |
|---|---|---|
| Gen1 BizHawk RBGY | 默认关闭的 Bot 尝试上限、进度计数与选按键边沿保护 | 默认无限搜索、原按键及 Savestate 帧时序不变 |
| Gen1 VBA RBGY | 与 BizHawk 等价的防护，保留 VBA 专属接口 | 字节序、手柄小写 select 和 botState 不变 |
| Colosseum Light | 以 HP、bonusBall、rate 三元组缓存纯捕获率计算 | 原结构体内存读次数和顺序、RNG 和 SetScreenText 不变 |
| Colosseum | 同上，且将循环拼接空格替换为 string.rep | 相同数据完全相同屏幕文本 |
| XD | 同上 | 独立队伍/盒子偏移与显示不变 |
| Ranch | **原游戏 Lua 不修改** | 需先取得 Dolphin 有/无赠送对象的真实探针数据 |

当前 26/26 游戏 Lua 已审计，25/26 相比最初基线已修改源码，Ranch 是唯一仍然原样的游戏 Lua。该覆盖数字不是实测性能达标数字。

## GameCube/XD 优化边界
- 已检查到的是原生结构体字段读取和捕获率公式，不能无证据称其每帧做 PK3 解密。
- calcCatchRate 仍严格使用原式 `(HP * rate * bonusBall) // (3 * HP)` 以及双层 math.sqrt；仅对相同三元组复用结果。缓存上限 256 条，届满整体清空，HP=0 仍直接返回 0。
- 在 Colosseum 与 XD，setPadding 改成 `string.rep(' ', math.max(0, padding+goodSpacing+1))`，等价于原版从 0 开始的包含末端循环。原 onScriptUpdate 和 SetScreenText 每帧继续执行，避免屏幕 overlay 生命周期问题。
- 不缓存未完整核验的对象指针；不会错用上帧 Pokémon 数据。收益仅是减少昂贵数学计算和字符串分配，须真实 Dolphin 实测量化。

## Gen1 可选保护（默认原版行为）
- `BOT_MAX_ATTEMPTS = 0`：默认无限搜索，原版游戏操作不变；用户设为正数才为 shiny/bite/species/tid 四类外层循环建立各自上限。
- `BOT_REPORT_EVERY = 0`：默认不输出周期日志；改为正数则按对应尝试次数报告。
- `getBotAttemptStats()`：返回四类累计尝试次数，不写游戏内存。
- 上限到达后不再开始新一轮 Savestate/joypad 序列，返回 false；Fishing Bot 的咬钩阶段退出向外传播。
- 启用限制才使用 Select 按下边沿闩锁：必须松开再按才重新启动，避免上限触发后保持按键又无限重启。默认不改变 Select 判定。

## 证据与验收
离线：`python tests/remaining/test_remaining.py`。26 个游戏 Lua 语法检查；Gen1 成功 TID 的逐帧 Savestate/输入事件原版对账；两平台各四种上限退出；三份 Dolphin 8 帧屏幕逐字节对账及重复 math.sqrt 次数对比。
这些属于合成 Mock，不是已验证的 GameCube/Wii、BizHawk/VBA 游戏实机表现。Ranch 原版不改，继续执行 [[17-ranch-readonly-profile]] 的无 offer/有 offer 两场景采样。
