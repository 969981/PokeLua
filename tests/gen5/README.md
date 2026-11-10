# BW/B2W2 BizHawk userdata.set 观测工具

生成器仅制作新的 Lua 测量副本，不修改仓库中的 Gen5 游戏脚本；每一个原 userdata.set 调用保持原顺序执行。

命令（仓库根目录）：
  python tests/gen5/build_userdata_probe.py --source "Gen 5/BizHawk/BW_RNG_BizHawk.lua" --label bw_userdata
  python tests/gen5/build_userdata_probe.py --source "Gen 5/BizHawk/B2W2_RNG_BizHawk.lua" --label b2w2_userdata

加载到 BizHawk Lua Console 后采集 tests/gen5/output/<label>_userdata.tsv。

合成测试：python tests/gen5/test_userdata_probe.py
分析报告：python tests/gen5/analyze_userdata.py tests/gen5/output/bw_userdata_userdata.tsv

注意：重复值比例不是可跳过写入的证明；必须对真实 Savestate onload 恢复数据逐帧验证。无商业 ROM、无游戏实测 FPS 的证据状态为 RUNTIME_NOT_OBSERVED。
