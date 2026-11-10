---
tags: [PokeLua, index, Obsidian]
status: verified-repository
source_branch: main
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
review_date: 2026-11-10
---
# PokeLua 技术研究 Vault

> 本目录即 Obsidian Vault 根目录（在 Obsidian 中选择“打开文件夹作为仓库”，选择 docs/）。所有结论均区分：**STATIC_VERIFIED**（源码可见）、**INFERRED**（静态推断）、**BENCHMARK_PENDING**（待性能测量）、**RUNTIME_NOT_OBSERVED**（尚无模拟器实测）。

## 导航
- [[research/00-repository-inventory|00 仓库全量脚本清单]]
- [[research/01-performance-architecture|01 全平台性能架构与热点]]
- [[research/02-gen3-mgba-frlg|02 Gen3 mGBA 与 FRLG 函数级分析]]
- [[research/03-cross-platform|03 Gen1／Gen4／Gen5／Dolphin 对比]]
- [[research/04-benchmark-protocol|04 性能与准确性测试方案]]
- [[research/05-p0-p4-roadmap|05 P0→P4 优化路线图]]
- [[research/06-original-vs-optimized|06 原版／优化版比较]]
- [[research/07-branch-sync-governance|07 main/develop 同步与开源维护]]
- [[research/08-script-triage|08 26 份脚本逐文件性能分诊]]
- [[research/09-frlg-p1-implementation|09 FRLG P1 调度器实施与 Mock 对账]]
- [[research/10-frlg-real-mgba-gate|10 FRLG P1 真实 mGBA 1×–16× 验收工具与门槛]]
- [[research/11-gen3-mgba-other-hotspots|11 其他 Gen3 mGBA 逐帧和文件 I/O 热点]]
- [[research/12-gen4-ds-hotspots|12 Gen4 DP/Pt/HGSS 遇敌循环与绘制]]
- [[research/13-gen5-ds-hotspots|13 Gen5 BW/B2W2 RNG 与持久化成本]]
- [[research/14-gen1-dolphin-hotspots|14 Gen1 Bot 与 Dolphin/Ranch 栈扫描]]
- [[research/15-other-scripts-roadmap|15 其余 25 脚本优化优先级与验收]]
- [[templates/research-record|研究记录模板]]
- [[auto-sync|现有上游同步机制（保留）]]

## 研究准则
1. 默认分支 main 用于同步上游 Real96/PokeLua，不直接修改自动同步脚本；优化、文档、测试放在 develop。
2. 不把 UI 绘制频率等同于 RNG 计算频率；任何改变 frame、Watchpoint、Savestate、Bot 输入时序的改动，均要逐事件对照。
3. 性能目标：1×／2×／4×／8×／16×，UI 目标 8–12Hz（真实时间），以“同环境不加载脚本”为 FPS 基线；额外开销 ≤10% 仅为目标。
4. 文档标注代码位置或 GitHub 固定提交证据；优化效果数字只能来自可复现基准，不引用未经独立复测的百分比。
5. 每次变更注明 SHA、模拟器构建号、ROM 区域与修订版本、游戏场景、输入序列、前后结果和验收状态。

## 当前快照
- 实际检索：26 个 .lua，Gen1 2／Gen3 13／Gen4 7／Gen5 4。
- 测试证据：已做全量静态代码扫描；尚无统一的 mGBA/Dolphin/BizHawk/DeSmuMe/VBA 跨平台实机 FPS 证据。
- 本阶段提交文档与规划，不自动把未知兼容性的优化代码覆盖上游脚本。

源：[`969981/PokeLua@main`](https://github.com/969981/PokeLua/tree/86918734caa9c05e995d23f315e1caafa6cfd7a2)、[`Real96/PokeLua`](https://github.com/Real96/PokeLua)。
