#!/usr/bin/env python3
"""ROM-free source invariants for cross-emulator PokeLua optimizations.

Run from root: python tests/optimization/verify.py
Requires git, python3, Lua 5.4 + luac for complete validation.
"""
import argparse
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE="3739f7b5801cee38ccd2d6ed764fe87df6e2fd58"

OFFSET_PATHS=[
"Gen 3/mGBA/E_RNG_mGBA.lua",
"Gen 3/mGBA/RS_RNG_mGBA.lua",
"Gen 3/mGBA/Side/E_Held_Item_RNG_mGBA.lua",
"Gen 3/mGBA/Side/FRLG_Held_Item_RNG_mGBA.lua",
"Gen 3/mGBA/Side/RS_Held_Item_RNG_mGBA.lua",
"Gen 4/BizHawk/DP_RNG_BizHawk.lua",
"Gen 4/BizHawk/HGSS_RNG_BizHawk.lua",
"Gen 4/BizHawk/Pt_RNG_BizHawk.lua",
"Gen 4/DeSmuMe/DP_RNG_DeSmuMe.lua",
"Gen 4/DeSmuMe/HGSS_RNG_DeSmuMe.lua",
"Gen 4/DeSmuMe/Pt_RNG_DeSmuMe.lua",
"Gen 5/BizHawk/B2W2_RNG_BizHawk.lua",
"Gen 5/BizHawk/BW_RNG_BizHawk.lua",
"Gen 5/DeSmuMe/B2W2_RNG_DeSmuMe.lua",
"Gen 5/DeSmuMe/BW_RNG_DeSmuMe.lua",
]
DOLPHIN_PURE={
"Gen 3/Dolphin/Ageto_Celebi_RNG_Dolphin.lua",
"Gen 3/Dolphin/Channel_RNG_Dolphin.lua",
"Gen 3/Dolphin/Colo_Pikachu_RNG_Dolphin.lua",
}
OFF_RX=re.compile(r'function getOffset\(offsetType, orderIndex\)\n local offsets = (\{[\s\S]*?\})\n\n return offsets\[offsetType\]\[orderIndex\]( \* 12)?\nend')
NEW_RX=re.compile(r'local PK_BLOCK_OFFSETS = (\{[\s\S]*?\})\n\nfunction getOffset\(offsetType, orderIndex\)\n return PK_BLOCK_OFFSETS\[offsetType\]\[orderIndex\]( \* 12)?\nend')
PAIR_RX=re.compile(r'\["(\w+)"\]\s*=\s*\{([0-9,\s]+)\}')

def old(path):
    return subprocess.check_output(["git","show",BASE+":"+path],cwd=ROOT).decode("utf-8-sig").replace("\r\n","\n")
def new(path):
    return (ROOT/path).read_text(encoding="utf-8-sig").replace("\r\n","\n")
def parse_map(text):
    groups={}
    for k,values in PAIR_RX.findall(text):
        groups[k]=tuple(int(z) for z in values.split(",") if z.strip())
    return groups

class SourceTests(unittest.TestCase):
    def test_mappings_same_24_values_all_15_files(self):
        self.assertEqual(len(OFFSET_PATHS),15)
        for p in OFFSET_PATHS:
            with self.subTest(p=p):
                a=old(p); b=new(p)
                om=OFF_RX.search(a); nm=NEW_RX.search(b)
                self.assertIsNotNone(om)
                self.assertIsNotNone(nm)
                aa=parse_map(om.group(1))
                bb=parse_map(nm.group(1))
                self.assertEqual(aa,bb)
                self.assertEqual(om.group(2),nm.group(2))
                self.assertTrue(all(len(row)==24 for row in aa.values()))
                self.assertEqual(set(aa),set(bb))
                for group in aa:
                    for index in range(1,25):
                        self.assertEqual(aa[group][index-1],bb[group][index-1])

    def test_no_unintended_changes_in_table_only_scripts(self):
        for p in OFFSET_PATHS:
            if p in (
                "Gen 3/mGBA/E_RNG_mGBA.lua",
                "Gen 3/mGBA/RS_RNG_mGBA.lua",
                "Gen 3/mGBA/Side/E_Held_Item_RNG_mGBA.lua",
                "Gen 3/mGBA/Side/FRLG_Held_Item_RNG_mGBA.lua",
                "Gen 3/mGBA/Side/RS_Held_Item_RNG_mGBA.lua"
            ):
                continue
            with self.subTest(p=p):
                a=old(p); b=new(p); m=OFF_RX.search(a)
                self.assertIsNotNone(m)
                wanted=("-- The block order map never changes; avoid allocating it on every lookup.\n"
                        "local PK_BLOCK_OFFSETS = "+m.group(1)+"\n\n"
                        "function getOffset(offsetType, orderIndex)\n"
                        " return PK_BLOCK_OFFSETS[offsetType][orderIndex]"+(m.group(2) or "")+"\nend")
                self.assertEqual(a.replace(m.group(0),wanted,1),b)

    def test_emulator_exact_lane_unchanged_helpers(self):
        for p in ("Gen 3/mGBA/E_RNG_mGBA.lua","Gen 3/mGBA/RS_RNG_mGBA.lua"):
            with self.subTest(p=p):
                a=old(p);b=new(p)
                for function in ("getRngInfo","getSaveStateInput"):
                    pattern=re.compile(r'function '+function+r'\([^\n]*\)\n([\s\S]*?)\nend')
                    self.assertEqual(pattern.search(a).group(0),pattern.search(b).group(0))
                self.assertIn('callbacks:add("frame", updateBuffers)',b)
                self.assertIn('pollInfoModeInput()',b)
                self.assertIn('function shouldRenderP1()',b)
                self.assertIn('getSaveStateInput()\nend\n\nemu:reset()',b)
        a=old("Gen 3/mGBA/E_RNG_mGBA.lua")
        b=new("Gen 3/mGBA/E_RNG_mGBA.lua")
        for fn in ("TIDBotLoop","TIDFoundCheck","initialSeedWritten"):
            pat=re.compile(r'function '+fn+r'\([^\n]*\)\n([\s\S]*?)\nend')
            if fn!="TIDBotLoop":
                self.assertEqual(pat.search(a).group(0),pat.search(b).group(0))
        self.assertIn('updateTIDBotLogic()',b)
        self.assertIn('p1LastTIDResult = tempTID',b)

    def test_side_held_item_exact_lane_helpers(self):
        for p in (
            "Gen 3/mGBA/Side/E_Held_Item_RNG_mGBA.lua",
            "Gen 3/mGBA/Side/FRLG_Held_Item_RNG_mGBA.lua",
            "Gen 3/mGBA/Side/RS_Held_Item_RNG_mGBA.lua"
        ):
            with self.subTest(p=p):
                a=old(p);b=new(p)
                for fn in ("getRngInfo","getSaveStateInput"):
                    pat=re.compile(r'function '+fn+r'\([^\n]*\)\n([\s\S]*?)\nend')
                    self.assertEqual(pat.search(a).group(0),pat.search(b).group(0))
                self.assertIn('p1First, p1Second, p1Third = getRngInfo()',b)
                self.assertIn('if shouldRenderP1() then updateCaptureBuffer() end',b)

    def test_dolphin_preview_only_seed_functions(self):
        for p in DOLPHIN_PURE:
            with self.subTest(p=p):
                before=old(p); after=new(p)
                self.assertIn("previewCachedSeed ~= currentSeed",after)
                self.assertIn("previewCachedSeed, previewCachedText = nil, nil",after)
                for fn in ("LCRNG","LCRNGDistance"):
                    rx=re.compile(r'function '+fn+r'\([^\n]*\)\n([\s\S]*?)\nend')
                    self.assertEqual(rx.search(before).group(0),rx.search(after).group(0))

    def test_luac_syntax_all_game_scripts(self):
        binary=shutil.which("luac5.4") or shutil.which("luac")
        if not binary:self.skipTest("luac unavailable")
        game_files=sorted(p for p in ROOT.glob("Gen */**/*.lua"))
        self.assertEqual(len(game_files),26)
        for path in game_files:
            with self.subTest(p=str(path.relative_to(ROOT))):
                p=subprocess.run([binary,"-p",str(path)],capture_output=True,text=True)
                self.assertEqual(p.returncode,0,p.stderr)

    def test_dolphin_pure_output_matches_real_source_on_mock_memory(self):
        binary=shutil.which("lua5.4") or shutil.which("lua") or shutil.which("texlua")
        if not binary:self.skipTest("Lua runtime unavailable")
        harness=ROOT/"tests/optimization/dolphin_pure_mock.lua"
        for path in sorted(DOLPHIN_PURE):
            with self.subTest(path=path):
                with tempfile.TemporaryDirectory() as folder:
                    orig=pathlib.Path(folder)/"original.lua"
                    orig.write_text(old(path),encoding="utf-8")
                    def execute(source):
                        p=subprocess.run([binary,str(harness),str(source)],
                                         text=True,capture_output=True)
                        self.assertEqual(p.returncode,0,p.stderr)
                        return p.stdout
                    self.assertEqual(execute(orig),execute(ROOT/path))


    def test_mgba_side_exact_lane_matches_baseline_on_mock(self):
        binary=shutil.which("lua5.4") or shutil.which("lua") or shutil.which("texlua")
        if not binary:self.skipTest("Lua runtime unavailable")
        harness=ROOT/"tests/optimization/side_exact_mock.lua"
        for path in (
            "Gen 3/mGBA/Side/E_Held_Item_RNG_mGBA.lua",
            "Gen 3/mGBA/Side/FRLG_Held_Item_RNG_mGBA.lua",
            "Gen 3/mGBA/Side/RS_Held_Item_RNG_mGBA.lua"
        ):
            with self.subTest(path=path):
                with tempfile.TemporaryDirectory() as folder:
                    orig=pathlib.Path(folder)/"original.lua"
                    orig.write_text(old(path),encoding="utf-8")
                    def execute(source):
                        p=subprocess.run([binary,str(harness),str(source)],
                                         text=True,capture_output=True)
                        self.assertEqual(p.returncode,0,p.stderr)
                        trace=p.stdout.split("\nPRINTS ",1)[0]
                        n=int(p.stdout.rsplit("\nPRINTS ",1)[1].strip())
                        return trace,n
                    a=execute(orig)
                    b=execute(ROOT/path)
                    self.assertEqual(a[0],b[0])
                    self.assertLess(b[1],a[1])

    def test_mgba_e_and_rs_rng_input_bot_parity_on_mock(self):
        binary=shutil.which("lua5.4") or shutil.which("lua") or shutil.which("texlua")
        if not binary:self.skipTest("Lua runtime unavailable")
        harness=ROOT/"tests/optimization/mgba_exact_mock.lua"
        for game,path in (
            ("E","Gen 3/mGBA/E_RNG_mGBA.lua"),
            ("RS","Gen 3/mGBA/RS_RNG_mGBA.lua")
        ):
            with self.subTest(game=game):
                with tempfile.TemporaryDirectory() as folder:
                    orig=pathlib.Path(folder)/"original.lua"
                    orig.write_text(old(path),encoding="utf-8")
                    def trace(source):
                        p=subprocess.run([binary,str(harness),game,str(source)],
                            text=True,capture_output=True)
                        self.assertEqual(p.returncode,0,p.stderr)
                        actions=p.stdout.split("\nADVANCES\n",1)[0]
                        advances=p.stdout.split("\nADVANCES\n",1)[1].split("\nPRINTS ",1)[0]
                        count=int(p.stdout.rsplit("\nPRINTS ",1)[1].strip())
                        return actions,advances,count
                    a=trace(orig)
                    b=trace(ROOT/path)
                    self.assertEqual(a[0],b[0], "Bot events / input actions changed")
                    self.assertEqual(a[1],b[1], "RNG/frame/mode changes")
                    self.assertLess(b[2],a[2], "P1 display count should decline")

if __name__=="__main__":
    unittest.main(verbosity=2)
