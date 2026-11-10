# Gen4 六份 DS 遇敌预测 P2：离线对照

仓库根目录执行：python tests/gen4/test_encounter_p2.py

依赖 Python 3、Lua 5.4、完整 Git 历史。测试从固定旧提交提取原版预测函数，在合成内存上对比原版同步预测与新版协程最后的步数及冷却值，并验证分片预算、完成缓存、失效、战斗和零概率情形。

本测试不会运行任何 ROM 或真实模拟器，不能视为实测 FPS 或游戏 RNG 完整等价。细节见 docs/research/20-gen4-encounter-p2.md。
