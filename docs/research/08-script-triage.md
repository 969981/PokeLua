---
tags: [PokeLua, static-metrics, script-triage, priority]
status: STATIC_VERIFIED+BENCHMARK_PENDING
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
---
# 26 份脚本逐文件性能分诊矩阵

[[../README]] · [[00-repository-inventory]] · [[01-performance-architecture]] · [[05-p0-p4-roadmap]]

## 方法与局限
通过 GitHub `main` 固定提交 `86918734` 读取了全部 26 份 Lua，做文本级静态扫描。下表的 `fn` 是函数定义文本匹配数量（`function name(...)`），`while` 是源文本词项匹配次数；这些**不等于运行中的调用次数、循环次数或 CPU 消耗**。风险评级为静态审计推断，尚未实机 profiling。目录条目及行数见 [[00-repository-inventory]]。

## Gen 1 — Bot 等待与回退
| 脚本 | fn | while | 静态证据／性能与可靠性风险 | 优先安排 |
|---|---:|---:|---|---|
| RBGY_Bot_BizHawk.lua | 18 | 8 | 多处 `while`；`savestate.save/load` 和 `emu.frameadvance` 出现在刷闪路径 | P2：重试计数、取消、错误码、事件轨迹 |
| RBGY_Bot_VBA.lua | 18 | 8 | 同类 Bot，多循环，模拟器 API 不同 | P2：同一生成样本跨 BizHawk/VBA 对账 |

## Gen 3 — mGBA 显示与预测
| 脚本 | fn | while | 主要静态风险 | 优先安排 |
|---|---:|---:|---|---|
| E_RNG_mGBA.lua | 45 | 0 | `frame → updateBuffers`，多页面反复展示、读取 | P1：统一 snapshot + UI 降频 |
| FRLG_RNG_mGBA.lua | 58 | 1 | 同上 + `while not isEncounterStep` + 双 Bot Watchpoint | **P1/P2/P3 首个样板** |
| RS_RNG_mGBA.lua | 40 | 0 | 同一框架，区域/版本地址不同 | P1：复用调度思路，不复用地址 |
| RS_RNG_Checksums_mGBA.lua | 25 | 0 | checksum 监视与窗口显示 | P2：仅 dirty 数据时重算校验 |
| Side/E_Held_Item_RNG_mGBA.lua | 29 | 0 | 道具预测、显示刷新、固有 RNG 参数 | P2：缓存预测输入，金样本 |
| Side/FRLG_Held_Item_RNG_mGBA.lua | 29 | 0 | 道具预测/版本偏移 | P2：和 FRLG 主脚本分开测 |
| Side/RS_Held_Item_RNG_mGBA.lua | 29 | 0 | 道具预测/版本偏移 | P2：确认 RS 地址、PID/道具输出 |

`fn`/ `while` 仅作为扫描线索。FRLG 原版有静态 `emu:read8/16/32` 调用表达式约 54 处，不能据此当成“每帧 54 次读取”——函数多次执行、条件分支和遇敌循环会显著改变实际次数。

## Gen 3 — Dolphin Lua Core
| 脚本 | fn | while | 主要静态风险 | 优先安排 |
|---|---:|---:|---|---|
| Ageto_Celebi_RNG_Dolphin.lua | 13 | 0 | `ReadValue*`、`onScriptUpdate` | P3：输出变化检测 |
| Channel_RNG_Dolphin.lua | 11 | 0 | 同平台 RNG/显示回调 | P3：测文本更新耗时 |
| Colo_Pikachu_RNG_Dolphin.lua | 13 | 0 | 同平台种子与对象显示 | P3：先验收 RNG/目标数据 |
| Colosseum_Light_RNG_Dolphin.lua | 14 | 0 | 游戏状态及文本构造 | P3：按需刷新 |
| Colosseum_RNG_Dolphin.lua | 14 | 0 | `onScriptUpdate` 拼接多种 Pokémon 信息 | P3：PID/PK 解码 dirty 缓存 |
| XD_RNG_Dolphin.lua | 15 | 0 | 游戏状态/数据读取与 SetScreenText | P3：多场景对照 |

## Gen 4 — 预测长循环与 GUI
| 脚本 | fn | while | 静态证据／风险 | 优先安排 |
|---|---:|---:|---|---|
| DP_RNG_BizHawk.lua | 54 | 2 | `while not battleStartJumpFlag` 预测 + 每帧 `emu.frameadvance` | P2：预测预算/逐帧准确 |
| Pt_RNG_BizHawk.lua | 53 | 2 | 同结构，游戏地址不同 | P2：按游戏隔离配置 |
| HGSS_RNG_BizHawk.lua | 56 | 2 | 同结构，额外游戏分支 | P2：场景态缓存 |
| DP_RNG_DeSmuMe.lua | 59 | 1 | `gui.register(main)`、大量 GUI 文本构造 | P2：分离 GUI 与计算 |
| Pt_RNG_DeSmuMe.lua | 58 | 1 | GUI 回调、游戏偏移 | P2：显示差分 |
| HGSS_RNG_DeSmuMe.lua | 61 | 1 | GUI 回调、多种模式 | P2：模式依赖采样 |
| Ranch_RNG_Dolphin.lua | 17 | 3 | `onScriptUpdate`、PK4 大小端解码及提供对象扫描 | P3：缓存 + 大小端回归 |

## Gen 5 — 双平台 BW/B2W2
| 脚本 | fn | while | 主要静态风险 | 优先安排 |
|---|---:|---:|---|---|
| BW_RNG_BizHawk.lua | 43 | 1 | 主循环 `emu.frameadvance`，64 位 RNG/跨状态显示 | P2：64 位精度+存档回退 |
| B2W2_RNG_BizHawk.lua | 32 | 1 | 同样主循环，版本独有状态 | P2：B2W2 独立金样本 |
| BW_RNG_DeSmuMe.lua | 48 | 0 | `gui.register(main)`，多页面内存与 GUI | P2：按需解码/渲染 |
| B2W2_RNG_DeSmuMe.lua | 37 | 0 | GUI 回调、版本独有地址 | P2：跨模拟器数据对账 |

## 统一优先级（非性能结论）
- **最高：FRLG mGBA**：热循环和 Watchpoint/Bot 并存，既有性能又有正确性敏感区域；先隔离 exact lane，再动预测。
- **高：其他 Gen 3 mGBA**：与 FRLG 相同帧更新机制，最容易复用设计，但需要分别测试版本和存档结构。
- **中：Gen 4/5 BizHawk 和 DeSmuMe**：策略复用而不是 API 复制；将长循环、解密与 GUI 计时后决定具体收益。
- **中：Gen 1 Bot**：首先保证可取消与可恢复，避免误把无限搜索解释成纯性能瓶颈。
- **后续：Dolphin**：优先做 `onScriptUpdate` 计时、差分显示以及 Wii/PK4 字节序的测试。

## 需要采集的真正证据
对每份脚本至少提供：运行中的 callbacks/s、模拟 FPS、每次 update 耗时分布、API 读调用次数、实际 render 次数、模拟器版本、ROM 版本和 RNG/PK 输出对账。没有这些数据，本文只给**静态排查顺序**，不能给真实性能提升百分比。

固定参考：[镜像源码](https://github.com/969981/PokeLua/tree/86918734caa9c05e995d23f315e1caafa6cfd7a2)。
