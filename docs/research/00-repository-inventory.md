---
tags: [PokeLua, inventory, source-audit]
status: STATIC_VERIFIED
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
---
# 全量仓库脚本清单与能力地图

[[../README|返回导航]] · [[01-performance-architecture]] · [[05-p0-p4-roadmap]]

依据 GitHub `main` 递归 tree 与逐个 `fetch_file`：**26 个 Lua**；统计为源代码行数（包含空行），并非运行时性能测量。

## Gen 1 — 2
| 环境 | 脚本 | 行数 |
|---|---|---:|
| BizHawk | `Gen 1/BizHawk/RBGY_Bot_BizHawk.lua` | 430 |
| VBA | `Gen 1/VBA/RBGY_Bot_VBA.lua` | 423 |

功能（根据上游 README）：赠送、定点、钓鱼、交换、TID Bot、队伍数据。两个平台都包含 8 个文本级 `while` 关键字；不能仅依数量推断风险高低。

## Gen 3 — 13
| 环境 | 脚本 | 行数 |
|---|---|---:|
| mGBA | `Gen 3/mGBA/E_RNG_mGBA.lua` | 1028 |
| mGBA | `Gen 3/mGBA/FRLG_RNG_mGBA.lua` | 1210 |
| mGBA | `Gen 3/mGBA/RS_RNG_mGBA.lua` | 919 |
| mGBA | `Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua` | 310 |
| mGBA Side | `Gen 3/mGBA/Side/E_Held_Item_RNG_mGBA.lua` | 699 |
| mGBA Side | `Gen 3/mGBA/Side/FRLG_Held_Item_RNG_mGBA.lua` | 680 |
| mGBA Side | `Gen 3/mGBA/Side/RS_Held_Item_RNG_mGBA.lua` | 682 |
| Dolphin | `Gen 3/Dolphin/Ageto_Celebi_RNG_Dolphin.lua` | 163 |
| Dolphin | `Gen 3/Dolphin/Channel_RNG_Dolphin.lua` | 154 |
| Dolphin | `Gen 3/Dolphin/Colo_Pikachu_RNG_Dolphin.lua` | 163 |
| Dolphin | `Gen 3/Dolphin/Colosseum_Light_RNG_Dolphin.lua` | 332 |
| Dolphin | `Gen 3/Dolphin/Colosseum_RNG_Dolphin.lua` | 329 |
| Dolphin | `Gen 3/Dolphin/XD_RNG_Dolphin.lua` | 352 |

FRLG/E/RS/mGBA Side 采用 `callbacks:add("frame", updateBuffers)`；FRLG 还包含 `while not isEncounterStep` 的预测路径。Dolphin 侧采用 `ReadValue32`／`onScriptUpdate`／`SetScreenText` 模式，不宜套用 mGBA 的刷新 API。

## Gen 4 — 7
| 环境 | 脚本 | 行数 |
|---|---|---:|
| BizHawk | `Gen 4/BizHawk/DP_RNG_BizHawk.lua` | 1401 |
| BizHawk | `Gen 4/BizHawk/Pt_RNG_BizHawk.lua` | 1406 |
| BizHawk | `Gen 4/BizHawk/HGSS_RNG_BizHawk.lua` | 1400 |
| DeSmuMe | `Gen 4/DeSmuMe/DP_RNG_DeSmuMe.lua` | 1491 |
| DeSmuMe | `Gen 4/DeSmuMe/Pt_RNG_DeSmuMe.lua` | 1496 |
| DeSmuMe | `Gen 4/DeSmuMe/HGSS_RNG_DeSmuMe.lua` | 1490 |
| Dolphin | `Gen 4/Dolphin/Ranch_RNG_Dolphin.lua` | 561 |

BizHawk 三脚本都有 `while not battleStartJumpFlag` 与主循环 `emu.frameadvance()`；DeSmuMe 三脚本通过 `gui.register(main)` 注册显示回调；Ranch 使用 Dolphin Lua Core 并含 Wii 大端与 PK4 小端转换。

## Gen 5 — 4
| 环境 | 脚本 | 行数 |
|---|---|---:|
| BizHawk | `Gen 5/BizHawk/BW_RNG_BizHawk.lua` | 1299 |
| BizHawk | `Gen 5/BizHawk/B2W2_RNG_BizHawk.lua` | 1036 |
| DeSmuMe | `Gen 5/DeSmuMe/BW_RNG_DeSmuMe.lua` | 1395 |
| DeSmuMe | `Gen 5/DeSmuMe/B2W2_RNG_DeSmuMe.lua` | 1130 |

BW/B2W2 有 RNG／捕获／孵蛋／C-Gear／宝可梦信息展示路径（能力以原 README 和具体分支为准）；需要单独审计 64 位 RNG 的正确性、存档恢复和模式切换缓存。

## 仓库维护项
- `.github/workflows/sync-upstream.yml`：每 4 小时同步上游至 `main`，发布脚本快照预发布版本。
- `docs/auto-sync.md`：已存在的同步说明，必须保留。
- `LICENSE`、`README.md`、`.gitignore`。
- 本次分支 `develop` 专门承接文档、测试和经验证的优化。

**证据边界**：本清单验证“存在何代码／有何调用路径”，不代表执行了全 ROM、多区域、多版本的兼容性测试。

源码固定快照：[浏览脚本](https://github.com/969981/PokeLua/tree/86918734caa9c05e995d23f315e1caafa6cfd7a2)。
