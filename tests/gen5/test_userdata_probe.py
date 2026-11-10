#!/usr/bin/env python3
"""Verify Gen5 observe-only userdata.set probe preserves original writes."""
import csv
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('gen5_probe',HERE/'build_userdata_probe.py')
probe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

GAME_FILES=(
"Gen 5/BizHawk/BW_RNG_BizHawk.lua",
"Gen 5/BizHawk/B2W2_RNG_BizHawk.lua"
)

SOURCE=r'''
while not wrongGameVersion do
 userdata.set("tempCurrentSeed", frame % 2)
 userdata.set("advances", frame)
 userdata.set("mtCounter", 0)
 emu.frameadvance()
end
'''

HARNESS=r'''
local path=assert(arg[1])
local trace={}
frame=1
wrongGameVersion=false
userdata={}
function userdata.set(key,value)
 trace[#trace+1]=key..":"..tostring(value).."@"..frame
end
emu={}
function emu.frameadvance()
 frame=frame+1
 if frame>12 then wrongGameVersion=true end
end
dofile(path)
print(table.concat(trace,"|"))
'''

class Gen5UserdataProfiler(unittest.TestCase):
    def test_two_real_game_sources_instrument_without_removing_writes(self):
        lua=shutil.which('luac5.4') or shutil.which('luac')
        for path in GAME_FILES:
            with self.subTest(path=path):
                text=(ROOT/path).read_text(encoding='utf-8-sig')
                with tempfile.TemporaryDirectory() as d:
                    script,n=probe.instrument(text,Path(d)/'values.tsv',300)
                    self.assertEqual(n,text.count('userdata.set('))
                    self.assertGreaterEqual(n,3)
                    self.assertEqual(script.count('p2TrackedUserdataSet('),n+1)
                    self.assertIn('p2OriginalUserdataSet(key,value)',script)
                    self.assertIn('p2FlushUserdataProfile()\n emu.frameadvance()',script.replace('\r\n','\n'))
                    if lua:
                        file=Path(d)/'instrumented.lua'
                        file.write_text(script,encoding='utf-8')
                        p=subprocess.run([lua,'-p',str(file)],capture_output=True,text=True)
                        self.assertEqual(p.returncode,0,p.stderr)

    def test_synthetic_original_api_call_trace_equal(self):
        lua=shutil.which('lua5.4') or shutil.which('lua') or shutil.which('texlua')
        if not lua:self.skipTest('Lua runtime missing')
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            original=d/'original.lua'
            instrumented=d/'instrumented.lua'
            harness=d/'harness.lua'
            log=d/'writes.tsv'
            original.write_text(SOURCE,encoding='utf-8')
            optimized,n=probe.instrument(SOURCE,log,4)
            instrumented.write_text(optimized,encoding='utf-8')
            harness.write_text(HARNESS,encoding='utf-8')
            log.write_text('frames\twrites\tunchanged\tdistinct_keys\tuserdata_cpu_s\tkey_counts\n',encoding='utf-8')

            def run(path):
                p=subprocess.run([lua,str(harness),str(path)],capture_output=True,text=True)
                self.assertEqual(p.returncode,0,p.stderr)
                return p.stdout
            self.assertEqual(run(original),run(instrumented))
            with log.open(encoding='utf-8',newline='') as handle:
                rows=list(csv.DictReader(handle,delimiter='\t'))
            self.assertEqual(len(rows),3)
            last=rows[-1]
            self.assertEqual(int(last['frames']),12)
            self.assertEqual(int(last['writes']),36)
            self.assertEqual(int(last['unchanged']),11)
            self.assertEqual(int(last['distinct_keys']),3)
            self.assertIn('mtCounter=12/11',last['key_counts'])

if __name__=="__main__":
    unittest.main(verbosity=2)
