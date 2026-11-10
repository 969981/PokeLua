#!/usr/bin/env python3
"""Offline Ranch probe generator + no-offer Dolphin mock parity tests."""
import csv
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SCRIPT=ROOT/'Gen 4/Dolphin/Ranch_RNG_Dolphin.lua'
spec=importlib.util.spec_from_file_location('ranch_probe', HERE/'build_readonly_probe.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RanchProbe(unittest.TestCase):
    def test_generated_is_read_only_instrumentation(self):
        original=SCRIPT.read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as tmp:
            generated=module.build(original, Path(tmp)/'ranch_scan.tsv', interval=5)
        for name in ('ranchProbe.frames = ranchProbe.frames + 1',
                     'ranchProbe.threads = ranchProbe.threads + 1',
                     'ranchProbe.read32 = ranchProbe.read32 + 1',
                     'ranchProbeInScan = false',
                     'local result = object + build.pk4Offset'):
            self.assertIn(name,generated)
        self.assertIn('SetScreenText(',generated)
        self.assertEqual(original.count('WriteValue32('),generated.count('WriteValue32('))

    def test_synthetic_dolphin_no_offer_same_screen(self):
        lua=shutil.which('lua') or shutil.which('lua5.4') or shutil.which('texlua')
        if not lua: self.skipTest('Lua interpreter unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            original=SCRIPT.read_text(encoding='utf-8')
            optimized=module.build(original,tmp/'scan.tsv',5)
            originalPath=tmp/'original.lua'
            generatedPath=tmp/'probe.lua'
            originalPath.write_text(original,encoding='utf-8')
            generatedPath.write_text(optimized,encoding='utf-8')
            def execute(source):
                return subprocess.run([lua,str(HERE/'ranch_mock.lua'),str(source),'10'],
                    capture_output=True,text=True,check=True).stdout
            self.assertEqual(execute(originalPath),execute(generatedPath))
            with (tmp/'scan.tsv').open(encoding='utf-8',newline='') as f:
                rows=list(csv.DictReader(f,delimiter='\t'))
            self.assertEqual(len(rows),2)
            self.assertEqual(int(rows[-1]['updates']),10)
            self.assertEqual(int(rows[-1]['scans']),10)
            self.assertEqual(int(rows[-1]['found']),0)
            self.assertEqual(int(rows[-1]['threads']),0)
            self.assertEqual(int(rows[-1]['stack_frames']),0)
            self.assertEqual(int(rows[-1]['read32_calls']),10)
if __name__=='__main__':
    unittest.main()
