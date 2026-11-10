---
tags: [PokeLua, GitHub, branching, license, upstream]
status: STATIC_VERIFIED
source_commit: 86918734caa9c05e995d23f315e1caafa6cfd7a2
---
# 上游同步与 develop 分支维护

[[../README]] · [[auto-sync]] · [[05-p0-p4-roadmap]]

## 现有工作流（保留）
仓库已有 `.github/workflows/sync-upstream.yml`，工作流名称 `Sync upstream and publish`；cron `13 */4 * * *` UTC；以 `Real96/PokeLua` 的 `main` 为上游，合并新提交到镜像 `main`。同步时保留本地 `.github/workflows`，随后按上游提交创建 `sync-<sha>` prerelease 与 ZIP/校验和。详见已有 [[../auto-sync]]。

## 分支职责
- **main**：上游镜像 + 自动同步/Release 的基准；除必要 CI 维护外避免添加优化 Lua 或研究改动。
- **develop**：技术研究文档、原版对账、性能测试、逐步落地的原版兼容优化。
- **feature/**：建议今后按 `feature/frlg-ui-scheduler`、`feature/gen4-predict-cache` 等小粒度分支开发；通过测试后合并到 develop。
- 发版时区分 `sync-<upstream-sha>`（纯镜像快照）与未来自定义 `opt-...`（优化构建），不混用标签与说明。

## 上游更新路径
1. 监控 main 的新的镜像提交，**不自动强制重置 develop**。
2. 用 PR `main -> develop` 对照同步（GitHub UI 或显式 merge），若上游修改同一功能需检查冲突。
3. 以新上游 SHA 重新生成脚本清单/基准和 Golden Samples，重新跑 exact lane 的全部回归。
4. 再继续优化功能 PR；严禁为了更新主分支而强制覆盖本地研究文档。

## 许可证
项目仓库有 `LICENSE`（GPL-3.0 系列许可文本，请以许可证原文为准）；开发优化版公开分发时保留上游版权、许可、修改说明与相应源代码供获取。若加入第三方依赖，先核对各自许可兼容性。

## 已知约束
- 原工作流在 **main** checkout 并同步，即使 develop 新增代码，也不会作为默认发布目标。
- 将来如要对 develop 运行 Actions 测试，应新增独立验证 workflow，并注意 token 的 workflow 权限和上游同步冲突。
- 当前只创建 develop 和 docs 文档，无自动合并 PR、无更改镜像自动发布行为。
