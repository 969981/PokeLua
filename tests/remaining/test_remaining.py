#!/usr/bin/env python3
"""Remaining 5 game Lua: source invariants, ROM-free output and Bot parity.

Ranch is NOT modified; its profiling awaits actual Dolphin offer/no-offer
observations. Mock tests are not emulator/FPS evidence.
"""
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = "e62970b333888c8fa51e2e8919523a40193d730d"
DOLPHIN = (
    "Gen 3/Dolphin/Colosseum_Light_RNG_Dolphin.lua",
    "Gen 3/Dolphin/Colosseum_RNG_Dolphin.lua",
    "Gen 3/Dolphin/XD_RNG_Dolphin.lua",
)
GEN1 = (
    ("Gen 1/BizHawk/RBGY_Bot_BizHawk.lua", "biz"),
    ("Gen 1/VBA/RBGY_Bot_VBA.lua", "vba"),
)

def baseline(p):
    return subprocess.check_output(["git", "show", BASE + ":" + p], cwd=ROOT).decode("utf-8-sig").replace("\r\n","\n")
def optimized(p):
    return (ROOT / p).read_text(encoding="utf-8-sig").replace("\r\n","\n")
def function_body(text, name):
    m = re.search(r"(?m)^function "+re.escape(name)+r"\([^\n]*\)\n[\s\S]*?^end$",text)
    assert m, f"function {name} not found"
    return m.group(0)

class RemainingOptimizationTests(unittest.TestCase):
    def test_all_26_game_lua_syntax(self):
        luac=shutil.which("luac5.4") or shutil.which("luac")
        if not luac:self.skipTest("Lua compiler not installed")
        game=list(ROOT.glob("Gen [0-9]*/**/*.lua"))
        self.assertEqual(len(game),26)
        for file in game:
            with self.subTest(p=str(file.relative_to(ROOT))):
                proc=subprocess.run([luac,"-p",str(file)],capture_output=True,text=True)
                self.assertEqual(proc.returncode,0,proc.stderr)

    def test_dolphin_runtime_mem_reads_and_rng_functions_are_unchanged(self):
        for path in DOLPHIN:
            with self.subTest(file=path):
                a,b=baseline(path),optimized(path)
                for fn in ("getPokemonInfo","getPokemonInfoText","LCRNGDistance","onScriptUpdate"):
                    self.assertEqual(function_body(a,fn),function_body(b,fn),fn+" changed")
                self.assertEqual(a.count("SetScreenText("),b.count("SetScreenText("))
                self.assertEqual(a.count("ReadValue32"),b.count("ReadValue32"))
                self.assertIn("local CATCH_RATE_MEMO_LIMIT = 256",b)
                self.assertIn("local a = (HP * rate * bonusBall) // (3 * HP)",b)
                if path.endswith("Colosseum_RNG_Dolphin.lua") or path.endswith("XD_RNG_Dolphin.lua"):
                    self.assertIn('string.rep(" ", math.max(0, padding + goodSpacing + 1))',b)

    def test_dolphin_real_functions_screen_trace_and_expensive_sqrt_reduction(self):
        lua=shutil.which("lua5.4") or shutil.which("lua") or shutil.which("texlua")
        if not lua:self.skipTest("Lua runtime unavailable")
        harness=ROOT/"tests/remaining/dolphin_screen_mock.lua"
        for path in DOLPHIN:
            with self.subTest(file=path):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp=pathlib.Path(tmp)
                    original=tmp/"baseline.lua"
                    original.write_text(baseline(path),encoding="utf-8")
                    game="xd" if path.endswith("XD_RNG_Dolphin.lua") else "colo"
                    def run(file):
                        proc=subprocess.run([lua,str(harness),str(file),game],text=True,
                                            capture_output=True,timeout=20)
                        self.assertEqual(proc.returncode,0,proc.stderr)
                        a,b=proc.stdout.rsplit("\nSQRT_COUNT ",1)
                        return a,int(b.strip())
                    o,n=run(original),run(ROOT/path)
                    self.assertEqual(o[0],n[0],"Displayed text or per-frame display count drift")
                    self.assertGreater(o[1],0,"Mock did not exercise expensive calcCatchRate")
                    self.assertLess(n[1],o[1],"Expected fewer repeated sqrt calculations")

    def test_gen1_original_search_replay_unchanged_when_limits_disabled(self):
        lua=shutil.which("lua5.4") or shutil.which("lua") or shutil.which("texlua")
        if not lua:self.skipTest("Lua runtime unavailable")
        harness=ROOT/"tests/remaining/gen1_bot_mock.lua"
        for path,platform in GEN1:
            with self.subTest(platform=platform):
                with tempfile.TemporaryDirectory() as tmp:
                    original=pathlib.Path(tmp)/"original.lua"
                    original.write_text(baseline(path),encoding="utf-8")
                    def run(file,scenario):
                        proc=subprocess.run([lua,str(harness),str(file),platform,scenario],
                                            text=True,capture_output=True,timeout=20)
                        self.assertEqual(proc.returncode,0,proc.stderr)
                        return proc.stdout.split("===TRACE===\n",1)[1]
                    self.assertEqual(run(original,"tid_success"),run(ROOT/path,"tid_success"),
                                     "Default TID save/load/key/frame trace changed")

    def test_gen1_each_opt_in_attempt_limit_stops(self):
        lua=shutil.which("lua5.4") or shutil.which("lua") or shutil.which("texlua")
        if not lua:self.skipTest("Lua runtime unavailable")
        harness=ROOT/"tests/remaining/gen1_bot_mock.lua"
        for path,platform in GEN1:
            for case in ("tid_limit","shiny_limit","bite_limit","species_limit"):
                with self.subTest(platform=platform,case=case):
                    proc=subprocess.run([lua,str(harness),str(ROOT/path),platform,case],
                                        text=True,capture_output=True,timeout=20)
                    self.assertEqual(proc.returncode,0,proc.stderr)
                    self.assertIn("stopped after 2 attempts",proc.stdout)

    def test_gen1_original_shiny_and_tid_checks_unchanged(self):
        for path,_ in GEN1:
            with self.subTest(file=path):
                a,b=baseline(path),optimized(path)
                for fn in ("isShiny","isTIDFound","getDVs","getInput"):
                    self.assertEqual(function_body(a,fn),function_body(b,fn))
                self.assertIn("local BOT_MAX_ATTEMPTS = 0",b)
                for kind in ("shiny","bite","species","tid"):
                    self.assertIn('botCanAttempt("'+kind+'"',b)
                self.assertEqual(a.count("savestate.save("),b.count("savestate.save("))
                self.assertEqual(a.count("savestate.load("),b.count("savestate.load("))
                self.assertEqual(a.count("emu.frameadvance()"),b.count("emu.frameadvance()"))

if __name__=="__main__":
    unittest.main(verbosity=2)
