---
tags: [PokeLua, benchmark, acceptance, reproducibility]
status: PROTOCOL_READY+RUNTIME_NOT_OBSERVED
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
---
# 性能基准与 RNG / Bot 等价验收规范

[[../README]] · [[05-p0-p4-roadmap]] · [[06-original-vs-optimized]]

## 目标，不是已完成的成绩
- 目标倍率：1× / 2× / 4× / 8× / 16×（能否实际达到受 ROM、模拟器和硬件限制）。
- UI 显示目标：真实时间 8–12 Hz，响应操作不出现长时冻结。
- RNG / TID / Seed Bot：**零漏事件、相同输入序列下逐事件对账一致**。
- 完整版相对不加载脚本时的实际模拟 FPS 附加损失：目标 ≤10%，为工程门槛，不是承诺。
- 问题定位必须先区分显示成本、预测成本、内存读取成本和游戏本身模拟耗时。

## 标准环境记录模板
`{timestamp, platform, emulator_version, emulator_build_sha, host_cpu, host_os, ROM_title, ROM_region, ROM_revision, ROM_sha256, save_sha256, lua_source_sha, initial_seed, scenario, target_multiplier, actual_fps, effective_multiplier}`

ROM 哈希只记录用户自己的合法 ROM；不分发游戏资源或原始存档。

## 实验矩阵
| 维度 | 至少包含 |
|---|---|
| 模式 | 关闭 Lua / 原版 / 仅 P1 调度 / P1+P2 缓存 / 全部优化 |
| 倍速 | 1×、2×、4×、8×、16× |
| 场景 | 标题画面、室外静止、行走高遇敌率、战斗、盒子、孵蛋、Bot |
| 工作量 | 每场景至少 30s 预热 + 120s 采样；需要长稳场景额外 30min |
| 样本 | 每组至少三次相同存档与输入记录；顺序交叉进行，避免硬件热态偏差 |
| 性能 | 模拟 FPS、实际倍率、Lua CPU 耗时（若可用）、回调时长 p50/p95/p99、内存读次数、渲染次数、预测迭代数、Bot 尝试／重试数 |

## 定量指标定义
- `effective_multiplier = actual_simulated_frames_per_real_second / nominal_frames_per_second`（固定记录名义值和游戏帧率来源）。
- `script_overhead_ratio = 1 - (fps_with_script / fps_without_script)`，仅在同一性能受限场景比较，16× 不达标和帧锁定不可直接混为一谈。
- 独立记录帧 callback 次数，RNG 观察次数，Watchpoint 命中次数、UI render 次数。
- 总开销必须包含日志/诊断开销；性能评估中需额外单测关闭诊断的成本。

## RNG 精确性测试
1. 保存原版和优化版的 `frame, initialSeed, currentSeed, advances`，先跑正常前进（0、1、999、1000、10000 次或更多 RNG 推进向量）。
2. 模拟器暂停/恢复、存档保存/加载、强制 reset、切换倍速：验证代际恢复和重新同步状态。
3. Gen3 PK3：PID/OTID、四块排列、checksum、species、ability、IV、moves、PP、egg 的全字段一致性；Gen4 PK4/Gen5 PK5 与各自加解密路径分别验收。
4. 预测器：对包含不同 flute/held item/ability 和 encounter rate 的输入录制原版结果，优化版逐条比对；未完成分批计算不允许显示伪最终步数。

## Bot 精确性测试
- FRLG 原版 Initial Seed Bot 第 1/35/40 帧动作；记录开始帧、各按键边沿、Watchpoint 触发帧、Seed 值、失败恢复帧、最终结果。
- TID Bot 同样记录临时 TID 与正式 SaveBlock2 TID/SID，分类 `TEMP_HIT`、`FINAL_MATCH`、`RETRY`、`TIMEOUT`。
- 为两个 Bot 制作成功、连续失败、重复结果、同一时刻启动、意外手动载入存档等 trace。
- 在 1×/16× 下使用相同模拟帧输入，不应因 UI 降频而导致动作丢失；不同真实时间导致的合法结果变化需明确标注，不能假装种子随机性相同。

## 报告格式
```json
{
  "source_sha": "git-commit",
  "environment": {"emulator": "mGBA", "rom_sha256": "..."},
  "scenario": "FRLG outdoor walking",
  "multiplier_requested": 16,
  "baseline_fps": null,
  "original_fps": null,
  "optimized_fps": null,
  "rng_event_diff_count": null,
  "bot_event_diff_count": null,
  "status": "RUNTIME_NOT_OBSERVED"
}
```

本仓库本轮只落地方案与审计文档；尚未在模拟器实机执行此协议。非实机 mock 不得填入 `actual_fps` 或宣称 16× 通过。
