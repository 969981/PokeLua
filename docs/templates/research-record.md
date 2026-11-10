---
tags: [PokeLua, template]
status: TEMPLATE
---
# 研究记录模板

[[../README]]

## 问题
- 日期：
- 脚本：
- Git commit：
- 代码行／函数：
- 平台／模拟器版本／ROM 区域与修订：
- 影响：性能 / 正确性 / 兼容性 / 维护成本

## 证据级别
- [ ] STATIC_VERIFIED（代码证据）
- [ ] INFERRED（推断）
- [ ] UNIT_TESTED（离线计算验证）
- [ ] RUNTIME_OBSERVED（模拟器事件命中）
- [ ] BENCHMARKED（带环境与样本的真实性能测量）

## 原版数据
- 样本 ID：
- 初始 Seed 与 RNG 差值：
- 事件日志／关键帧：
- ROM 哈希（不上传 ROM）：
- Benchmark JSON：

## 优化设计
- 行为不变式：
- 内存缓存失效规则：
- 时间／帧调度：
- 预期收益与风险：
- 回退方式：

## 对账
| 条件 | 原版 | 优化版 | PASS / FAIL / NOT_OBSERVED |
|---|---|---|---|
| 1×  | | | NOT_OBSERVED |
| 4×  | | | NOT_OBSERVED |
| 8×  | | | NOT_OBSERVED |
| 16× | | | NOT_OBSERVED |

## 结论与后续
- 结论：
- 未闭合证据：
- PR／Commit：
