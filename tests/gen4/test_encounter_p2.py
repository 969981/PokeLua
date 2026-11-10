#!/usr/bin/env python3
"""Gen4 encounter P2: six game Lua source/algorithm parity tests, no ROM.

The original while-loop remains the mathematical gold reference. Every
optimized coroutine must return the same (missingSteps, cooldownSteps) for
identical synthetic memory and not exceed its per-callback RNG budget.
"""
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
BASELINE="53fbfc57e543efaa7bee9053ce79ce3b515f3d93"
PATHS=(
"Gen 4/BizHawk/DP_RNG_BizHawk.lua",
"Gen 4/BizHawk/Pt_RNG_BizHawk.lua",
"Gen 4/BizHawk/HGSS_RNG_BizHawk.lua",
"Gen 4/DeSmuMe/DP_RNG_DeSmuMe.lua",
"Gen 4/DeSmuMe/Pt_RNG_DeSmuMe.lua",
"Gen 4/DeSmuMe/HGSS_RNG_DeSmuMe.lua",
)

def baseline(path):
    return subprocess.check_output(
        ["git","show",BASELINE+":"+path],cwd=ROOT).decode("utf-8-sig").replace("\r\n","\n")

def optimized(path):
    return (ROOT/path).read_text(encoding="utf-8-sig").replace("\r\n","\n")

def prediction_section(source):
    start=source.index("function coolDownEndCheck(")
    end=source.index("function showEncounterMissingSteps(pidAddr)",start)
    return source[start:end]

def original_loop_section(source):
    sec=prediction_section(source)
    start=sec.index("function getEncounterMissingSteps(")
    end=sec.index("end\n",start)
    # The return near the end is unambiguous and captures all nested blocks.
    match=re.search(r'\n return missingSteps \+ coolDownSteps, coolDownSteps\nend',sec[start:])
    assert match
    return sec[start:start+match.end()]

LUA_HEADER=r'''
local originalSourcesAreLoaded = true
pidPointerAddr = 0x100000
currentSeedAddr = 0x200000
koreanOffset = 0
battleStartJumpFlag = false
local fakeSeed, fakeCoolDown, rngCalls = 0, 0, 0
floor = math.floor
rshift = function(x,n) return x >> n end
lshift = function(x,n) return (x << n) & 0xFFFFFFFF end
band = function(a,b) return a & b end
read32Bit = function(addr)
 if addr == pidPointerAddr then return 0x300000 end
 if addr == currentSeedAddr then return fakeSeed end
 error(string.format("unexpected read32Bit 0x%X",addr))
end
read8Bit = function(addr)
 if addr < 0x300000 then error("bad cooldown address") end
 return fakeCoolDown
end
LCRNG = function(state,mul,add)
 rngCalls = rngCalls + 1
 return (state * mul + add) & 0xFFFFFFFF
end
'''

LUA_CASES=r'''
local hasP2 = type(updateEncounterPredictionP2) == "function"
local vectors = {
 {0,20,15,0}, {1,40,20,1}, {0x12345678,60,15,2},
 {0xCAFEBABE,30,35,3}, {0xDEADBEEF,80,50,0},
 {0x11111111,15,10,1}, {0xA5A5A5A5,95,90,7},
 {0x98765432,8,6,0},
}
for idx, v in ipairs(vectors) do
 fakeSeed, fakeCoolDown, battleStartJumpFlag = v[1], v[4], false
 local a,b = getEncounterMissingSteps(v[2],v[3])
 if hasP2 then
  resetEncounterPredictionP2()
  rngCalls = 0
  local gotA,gotB,status
  local callbacks=0
  repeat
   callbacks = callbacks + 1
   local before = rngCalls
   gotA,gotB,status = updateEncounterPredictionP2(0x300000,7,v[2],v[3])
   assert(rngCalls-before <= 192, "per-update LCG budget exceeded")
   assert(callbacks < 4096, "P2 did not finish")
  until status == "complete"
  assert(a == gotA and b == gotB, string.format("P2 parity mismatch idx=%d",idx))
  local oldCalls = rngCalls
  local cachedA, cachedB, cachedStatus = updateEncounterPredictionP2(0x300000,7,v[2],v[3])
  assert(cachedA == gotA and cachedB == gotB and cachedStatus == "complete")
  assert(rngCalls == oldCalls, "cached result recalculated")
 end
 print(("CASE %d %d %d"):format(idx,a,b))
end
if hasP2 then
 -- A stale in-progress result must never be displayed for a new seed.
 resetEncounterPredictionP2()
 fakeSeed, fakeCoolDown = 0x14234215, 0
 local x,y,state=updateEncounterPredictionP2(0x300000,7,3,2)
 fakeSeed=0x91919191
 local goldA,goldB=getEncounterMissingSteps(3,2)
 local calls=0
 repeat
  calls=calls+1
  x,y,state=updateEncounterPredictionP2(0x300000,7,3,2)
  assert(calls<4096, "changed seed never completes")
 until state=="complete"
 assert(x==goldA and y==goldB, "stale seed result reused")
 resetEncounterPredictionP2()
 local n,m,kind=updateEncounterPredictionP2(0x300000,7,0,20)
 assert(n==nil and m==nil and kind=="unavailable","zero movement should not hang")
 n,m,kind=updateEncounterPredictionP2(0x300000,7,30,0)
 assert(n==nil and m==nil and kind=="unavailable","zero encounter should not hang")
 battleStartJumpFlag=true
 n,m,kind=updateEncounterPredictionP2(0x300000,7,30,20)
 assert(n==0 and m==0 and kind=="complete","battle result changed")
end
'''

class Gen4P2Regression(unittest.TestCase):
    def test_six_original_loops_unchanged_except_optional_yield(self):
        for p in PATHS:
            with self.subTest(file=p):
                old=original_loop_section(baseline(p))
                new=original_loop_section(optimized(p))
                new=new.replace("function getEncounterMissingSteps(movement, encounter, p2YieldStep)",
                                "function getEncounterMissingSteps(movement, encounter)")
                new=new.replace("  if p2YieldStep then p2YieldStep() end\n","")
                self.assertEqual(old,new,"Original RNG/cooldown algorithm changed")
                source=optimized(p)
                self.assertEqual(source.count("updateEncounterPredictionP2(pidAddr, mapAttribute, movementRate, encounterRate)"),1)
                self.assertIn("resetEncounterPredictionP2()",source)
                self.assertIn('predictionState == "unavailable"',source)

    def test_six_games_budgeted_vs_original_real_functions(self):
        lua=shutil.which("lua5.4") or shutil.which("lua") or shutil.which("texlua")
        if not lua:self.skipTest("Lua 5.4 executable unavailable")
        for p in PATHS:
            with self.subTest(file=p):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp=pathlib.Path(tmp)
                    outputs=[]
                    for version,source in (("baseline",baseline(p)),("p2",optimized(p))):
                        fixture=tmp/(version+".lua")
                        fixture.write_text(
                            LUA_HEADER+"\n"+prediction_section(source)+"\n"+LUA_CASES,encoding="utf-8")
                        result=subprocess.run([lua,str(fixture)],text=True,capture_output=True,timeout=15)
                        self.assertEqual(result.returncode,0,result.stderr)
                        outputs.append(result.stdout)
                    self.assertEqual(outputs[0],outputs[1],"Golden prediction steps/cooldown drift")

if __name__=="__main__":
    unittest.main(verbosity=2)
