# 剩余五份游戏 Lua：ROM-free 回归测试

在项目根目录执行：

```bash
python tests/remaining/test_remaining.py
```

需要 Python 3、Git 完整历史（旧 SHA e62970b333888c8fa51e2e8919523a40193d730d）、Lua 5.4 和 luac。
测试 26 份 Lua 的语法，三份 Colosseum/XD 的画面输出与捕获率缓存，两个 Gen1 Bot 默认模式相同 Savestate/按键轨迹及四类可选上限。
没有 ROM，没有真实模拟器与性能数据。Ranch 继续在 tests/ranch/ 下采集两场景证据。
研究笔记：docs/research/22-remaining-five-optimizations.md。
