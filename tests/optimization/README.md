# PokeLua 跨平台优化回归

在 `develop` 仓库根目录运行：

```bash
python tests/optimization/verify.py
```

需要 Python 3.9+、Git、Lua 5.4 和 luac。测试会对照固定旧提交 `3739f7b...` 的 **原始源代码**：

- 检查 15 份 Gen3/4/5 脚本的 24 档 `getOffset` 全部映射值与原版一致；对其中只有表变更的 10 份脚本做整体字符对比（忽略换行格式）。
- 对全部 26 份游戏 Lua 执行 `luac -p` 语法检查。
- 对 Dolphin 三份纯 Seed 配信预览以 10 组含重复/回退的 Seed 比较全部输出文本。
- 对 Emerald/RS 各 240 帧模拟，检查 RNG、模式输入和 Emerald TID Bot 的事件轨迹一致，以及 UI 打印次数减少。
- 对三份 Held Item Side 脚本各 480 帧模拟，检查逐帧 RNG 和 Savestate 输入调用数一致、UI 负载下降。

**Mock 不包含任何商业 ROM 或真实模拟器。** 不代表高倍率 FPS 或 TID 成功率的实机测试。真实门槛见 `docs/research/19-all-lua-optimization.md`。
