#!/usr/bin/env python3
"""ROM-free tests for the real-emulator benchmark generators and log readers."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

builder=load('rsbuild',ROOT/'tests/rs_checksums/build_real_benchmark.py')
reader=load('rsread',ROOT/'tests/rs_checksums/analyze_real_benchmark.py')

MOCK_RS = '''local savePath = "fake.sav"
function getChecksumsList()
 local saveFile = assert(io.open(savePath, "rb"))
 local bytes = saveFile:read(0x20000)
 saveFile:close()
 return {bytes}
end
function getCurrentXORChecksumSeed(list)
 return 0x1234
end
function updateBuffers()
 getCurrentXORChecksumSeed(getChecksumsList())
end
function initializeBuffers() end
function printGameInfo() end
callbacks = callbacks or {}
initializeBuffers()
printGameInfo()
callbacks:add("frame", updateBuffers)
'''

def make_log(path,frames,reads,checksum):
    path.write_text('timestamp\tseconds\tframes\tsave_opens\tsave_reads\tsave_bytes\ttotal_ticks\tcpu_s\tmax_cpu_s\tlast_xor\n'
                    +f'100\t1\t{frames}\t{reads}\t{reads}\t{reads*131072}\t{frames}\t0.05\t0.002\t{checksum}\n',
                    encoding='utf-8')

class BenchmarkTests(unittest.TestCase):
    def test_codegen_has_one_file_read_hook_and_callback(self):
        with tempfile.TemporaryDirectory() as temp:
            source=builder.build(MOCK_RS,'cached',Path(temp)/'p.tsv')
            self.assertEqual(source.count('rsProbeOpen(savePath, "rb")'),1)
            self.assertEqual(source.count('rsProbeRead(saveFile, 0x20000)'),1)
            self.assertIn('rsProbeFrame(__originalRSUpdate)',source)
            self.assertIn('local __originalChecksumXor = getCurrentXORChecksumSeed',source)
            minimal=builder.build(None,'minimal',Path(temp)/'b.tsv')
            self.assertIn('rsProbeFrame(nil)',minimal)
            self.assertNotIn('getChecksumsList',minimal)
            compiler=shutil.which('texluac') or shutil.which('luac')
            if compiler:
                for n,data in (('probe.lua',source),('minimal.lua',minimal)):
                    file=Path(temp)/n
                    file.write_text(data,encoding='utf-8')
                    subprocess.run([compiler,'-p',str(file)],check=True,capture_output=True)

    def test_windows_path_escaped_correctly(self):
        s=builder.build(MOCK_RS,'original',Path('/tmp/probe.tsv'),Path(r'C:\Save Files\game.sav'))
        self.assertIn('C:\\\\Save Files\\\\game.sav',s)

    def test_real_log_reader_is_not_mock_fps_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            make_log(root/'minimal.tsv',930,0,'')
            make_log(root/'original.tsv',450,450,'41237')
            make_log(root/'cached.tsv',850,1,'41237')
            data={name:reader.summarize(reader.read_log(root/(name+'.tsv'),0))
                  for name in ('minimal','original','cached')}
            out=reader.evaluate(data['minimal'],data['original'],data['cached'],1)
            self.assertEqual(out['status'],'REVIEW_READY')
            self.assertTrue(out['stabilized_checksum_xor_equal'])
            self.assertGreater(out['cached_read_reduction_ratio'],0.99)
            self.assertLess(out['cached_to_minimal_fps_ratio'],1.0)

class RanchSceneTests(unittest.TestCase):
    def test_two_scene_gate_requires_actual_offer_hit(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            cols='updates\tscans\tfound\tthreads\tstack_frames\tread32_calls\tscan_cpu_s\tmax_scan_cpu_s\n'
            (root/'no.tsv').write_text(cols+'600\t600\t0\t600\t1200\t3600\t0.6\t0.002\n',encoding='utf-8')
            (root/'yes.tsv').write_text(cols+'600\t600\t20\t600\t1300\t3700\t0.8\t0.004\n',encoding='utf-8')
            result=subprocess.run([sys.executable,str(ROOT/'tests/ranch/compare_scenes.py'),
              '--no-offer',str(root/'no.tsv'),'--offer',str(root/'yes.tsv'),
              '--minimum-updates','600'],capture_output=True,text=True,check=True)
            self.assertIn('"status": "REVIEW_READY"',result.stdout)
            (root/'yes.tsv').write_text(cols+'600\t600\t0\t600\t1300\t3700\t0.8\t0.004\n',encoding='utf-8')
            result=subprocess.run([sys.executable,str(ROOT/'tests/ranch/compare_scenes.py'),
              '--no-offer',str(root/'no.tsv'),'--offer',str(root/'yes.tsv')],
              capture_output=True,text=True,check=True)
            self.assertIn('"status": "INCOMPLETE"',result.stdout)
if __name__=='__main__':unittest.main()
