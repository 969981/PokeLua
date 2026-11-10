---
tags: [PokeLua, Gen4, DP, Platinum, HGSS, RNG, performance, coroutine, regression]
status: CODE_READY+RUNTIME_NOT_OBSERVED
baseline_commit: 53fbfc57e543efaa7bee9053ce79ce3b515f3d93
date: 2026-11-10
---
# Gen4 遇敌预测 P2：六版本分片计算与输入缓存

[[../README]] · [[12-gen4-ds-hotspots]] · [[19-all-lua-optimization]]

## 范围与算法边界
改动覆盖 DP／Pt／HGSS × BizHawk／DeSmuMe 六份。保留原版 getEncounterMissingSteps 的 RNG 消耗顺序、LCG 常量、coolDownEndCheck、getEncounterCheckValue 和二元返回值。只新增第三个可选参数 p2YieldStep，在原有 while 的每次迭代开头调用（未传入时等价旧版），允许协程在预算内暂停。

DP／Pt 与 HGSS 不是同一冷却算法：DP／Pt 冷却阶段可能推进 RNG，HGSS 直接累计步数。两条路径保留原控制流，不合并公式。

## 运行时改动
- showEncounterMissingSteps 每次仍读取地图、movementRate、encounterRate，调用 updateEncounterPredictionP2。
- 输入身份包含 pidAddr、PID 对象指针、mapAttribute、movementRate、encounterRate、cooldown 当前计数、当前 Seed、battleStartJumpFlag；任一变化重新建任务，禁止旧结果冒充新状态。
- coroutine.resume 每次 UI 更新只执行一次，每次最多 64 轮原预测循环；协程内部保留 wild RNG seed、missingSteps、coolDownSteps。适配 BizHawk 主循环及 DeSmuMe gui.register。
- 完成后同输入缓存复用。未算完显示 Calculating / Pending；0 movement 或 0 encounter 时显示 N/A，避免无解无限循环；非遇敌区显示原版 0 步；战斗状态维持原版 0/0。
- 当 Seed 每帧都变时，缓存会不断失效，可能持续 Calculating；这是避免显示错误结果的保守行为，而非预测算法不正确。
- 外部 UI 绘制、userdata.set、RNG Advances、Savestate、按键时序均未修改；该补丁不保证模拟器立即跑满 16×。

## 无 ROM 对账
工具：tests/gen4/test_encounter_p2.py（Python 3、Git 历史、Lua 5.4）。

1. 自动从固定 baseline_commit 提取原预测函数，核对其控制流只增加可选 yield 钩子。
2. 从六份游戏脚本抽取原版冷却和 RNG Check 函数，以合成 RAM、32 位 LCG 运行 8 组固定 Seed/移动率/遇敌率/冷却输入；直接预测与分片协程最终输出必须一致。
3. 每次 resume 最多调用 192 次 LCRNG（3 次 × 64 迭代上限）；同输入完成缓存不重算。
4. Seed 改变废弃旧结果，0 概率不阻塞，战斗时返回 0/0。

命令：python tests/gen4/test_encounter_p2.py。通过仅为 OFFLINE_EQUIVALENCE_PASS，不是实机 FPS/RNG 回归。

## 实机验收
每游戏记录模拟器构建、ROM SHA、存档 SHA；1×／4×／8×／16×；草丛/洞穴/骑车/步行/零遇敌/特性与道具/存档回退/地图切换。核对旧版与新版步骤+cooldown、完成时间、pending 状态、长尾 callback、RNG Advances/MT/TID/PID 和生成结果。Overlay 每帧仍绘制。

## 下一阶段
Gen5 BW/B2W2 BizHawk 只先 profile userdata.set 调用次数、重复值写入比例与 CPU 耗时；未经 Savestate 回滚对账不可降频持久化。Ranch 使用已提交探针取得无 offer、有 offer 两个真实场景的搜索成本与命中生命周期后再决定是否缓存对象。

关联：[[13-gen5-ds-hotspots]] · [[17-ranch-readonly-profile]]。
