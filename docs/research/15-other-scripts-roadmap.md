---
tags: [PokeLua, roadmap, optimization, other-scripts, decision]
status: STATIC_VERIFIED+BENCHMARK_PENDING
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
review_date: 2026-11-10
---
# FRLG 以外 25 个脚本：优化实施排序与回归门槛

[[../README]] · [[11-gen3-mgba-other-hotspots]] · [[12-gen4-ds-hotspots]] · [[13-gen5-ds-hotspots]] · [[14-gen1-dolphin-hotspots]] · [[04-benchmark-protocol]]

## 选择原则
按 **执行频率 × 单次潜在成本 × 实现风险 × 可复用范围 × 对 RNG 的影响** 决定先后；这只是源码风险排序，不是实际 FPS 或性能提升排行。

| 先后 | 目标 | 预期改变 | 风险、验收条件 |
|---|---|---|---|
| **0** | RS_RNG_Checksums_mGBA.lua | 避免每模拟帧读取 128 KiB 文件、重算 28 段校验值 | 保存发生后必须得到一致的 28 段结果；找不到文件也不让工具循环崩溃 |
| **1** | Ranch_RNG_Dolphin.lua（先 Profile 再改） | 优化频繁遍历 Wii 线程栈（64×256 候选上限）和 PK4 重解密 | 不能漏掉短生命周期的 Hayley 提供对象；指针失效及时更新 |
| **2** | E_RNG_mGBA.lua 与 RS_RNG_mGBA.lua | 移植 FRLG 的逐帧精确逻辑／低频 Console UI | E TID Watchpoint/重试零差异；RS RNG/孵蛋/游走不变 |
| **3** | Gen4 DP BizHawk 预测器试点 | 避免无上限预测阻塞，每帧预算，缓存同输入结果 | 全部金样本预测步数、冷却/RNG 结果一致 |
| **4** | Gen4 Pt/HGSS BizHawk + 三个 DeSmuMe | 复用纯预测算法与偏移表/解密缓存 | 游戏区域与平台专属 API 单独测试；GUI overlay 不消失 |
| **5** | Gen5 BW/B2W2 四脚本 | 重算与 GUI 解耦，评估 `userdata.set` 和 MT state | BW `mtIndex-624` / B2W2 `mtIndex-2` 严格保留；Savestate 事件准确 |
| **6** | Gen1 RBGY BizHawk + VBA | 增加 Bot 重试边界、取消、输入边沿与日志 | 生成结果/时序不变；失败可恢复，已命中不被重复搜索覆盖 |
| **7** | 三个 Held Item + RS Checksum 以外 Side | PK3 排列表缓存 + 动态字段失效缓存 | E 特殊 RNG 初始状态、PID/道具结果不变 |
| **8** | Gen3 Dolphin 六脚本 | 源码证据支持轻量文本去重与 PK 缓存 | `onScriptUpdate` / `SetScreenText` 的实际刷新语义保持一致 |

## 推荐提交与验证粒度
1. 每份脚本独立 PR/commit，始终以 `develop` 为目标；`main` 仍为上游镜像，不打断每四小时的同步与 release。
2. 每次先保留 **仅探针**版本，再做一项有界优化；任何改动未通过回归就保留原版，不在其他文件批量复制未经证明的修复。
3. 数据：模拟器构建号、ROM 版本 SHA、测试存档哈希、原版 SHA、优化版 SHA、游戏场景、倍率、回调时长 p50/p95/p99、每秒回调数、文件 read 次数/总字节、实际异常状态。
4. 算法：逐帧 seed/advance/MT/PID/IV/TID/SID、Savestate 保存与恢复、Bot 按键时间线；涉及 PK4 endian、PK5 RNG 的单独向量。记录不一致而不是用显示同步掩盖错误。
5. 对 GUI：mGBA Console 文本可保持跨帧，BizHawk/DeSmuMe overlay 是否可隔帧绘制需要实机确认。**优先缓存昂贵计算和格式化结果**，不要直接跳过所有 overlay draw API。

## 统一证据状态
- `STATIC_VERIFIED`：源码直接确认路径；本次已经覆盖 25 个剩余游戏脚本。
- `INFERRED`：潜在性能/行为风险；没有实测耗时，不宣称热点成本排名已证实。
- `UNIT_TESTED`：纯算法/Mock 轨迹经独立测试（当前新目标未跑）。
- `RUNTIME_OBSERVED`：真实模拟器命中预期方法、ROM 状态与日志。
- `BENCHMARKED`：完整环境与 1×–16× 运行测试比较通过。

## 对下一轮的具体建议
下一步应先为 **RS_RNG_Checksums_mGBA.lua** 编写“仿真保存数据变动/校验和变动/找不到文件”的测试与最小化缓存补丁；同时给 Ranch 增加不改变行为的迭代计数探针。两项目都不触碰底层 RNG 算法，风险比同时重写所有 Lua 小。

详见各分世代函数级审计，原版固定源码：[969981/PokeLua@86918734](https://github.com/969981/PokeLua/tree/86918734caa9c05e995d23f315e1caafa6cfd7a2)。
