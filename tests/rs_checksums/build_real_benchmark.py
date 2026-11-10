#!/usr/bin/env python3
"""Generate comparable mGBA Lua probes: minimal, original RS, cached RS.

Load exactly one generated file in Tools > Scripting while your own Ruby/Sapphire
ROM and battery save are available. Never executes an emulator or downloads ROMs.
"""
import argparse
import json
from pathlib import Path
import re

PRELUDE = r'''
-- RS real-emulator measurement instrumentation (does not modify game RAM)
local RS_PROBE_LOG = __LOG_PATH__
local rsProbe = {
 tick=0, frames=0, opens=0, reads=0, bytes=0, cpu=0,
 maxCPU=0, checksum=nil, anchor=os.time()
}
local function rsProbeOpen(path, mode)
 rsProbe.opens = rsProbe.opens + 1
 return io.open(path, mode)
end
local function rsProbeRead(file, bytes)
 local result = file:read(bytes)
 rsProbe.reads = rsProbe.reads + 1
 if result then rsProbe.bytes = rsProbe.bytes + #result end
 return result
end
local function rsProbeFrame(process)
 local start = os.clock()
 if process then process() end
 local duration = os.clock() - start
 rsProbe.cpu = rsProbe.cpu + duration
 if duration > rsProbe.maxCPU then rsProbe.maxCPU = duration end
 rsProbe.tick = rsProbe.tick + 1
 rsProbe.frames = rsProbe.frames + 1
 local second = os.time()
 if second > rsProbe.anchor then
  local elapsed = second - rsProbe.anchor
  local handle = io.open(RS_PROBE_LOG, "a")
  if handle then
   handle:write(string.format("%d\t%d\t%d\t%d\t%d\t%d\t%d\t%.8f\t%.8f\t%s\n",
    second,elapsed,rsProbe.frames,rsProbe.opens,rsProbe.reads,rsProbe.bytes,
    rsProbe.tick,rsProbe.cpu,rsProbe.maxCPU,tostring(rsProbe.checksum or "")))
   handle:close()
  end
  rsProbe.frames,rsProbe.opens,rsProbe.reads,rsProbe.bytes = 0,0,0,0
  rsProbe.cpu,rsProbe.maxCPU = 0,0
  rsProbe.anchor = second
 elseif second < rsProbe.anchor then
  rsProbe.anchor = second
 end
end
-- End instrumentation
'''

def replace_one(text, old, new, label):
    n=text.count(old)
    if n != 1: raise ValueError(f'{label}: expected 1 location, found {n}')
    return text.replace(old,new,1)

def build(source, variant, log_path, save_path=None):
    prelude=PRELUDE.replace('__LOG_PATH__',json.dumps(log_path.as_posix(),ensure_ascii=False))
    if variant == 'minimal':
        return prelude+'\ncallbacks:add("frame", function() rsProbeFrame(nil) end)\n'
    if source is None: raise ValueError('non-minimal variant requires --source')
    s=source.replace('\r\n','\n')
    if save_path:
        pathline=re.compile(r'(?m)^local savePath = "[^\r\n]*".*$')
        s, n=pathline.subn(lambda _: 'local savePath = '+json.dumps(str(save_path),ensure_ascii=False)+'  -- benchmark battery save path',s,count=1)
        if n!=1:raise ValueError('Could not identify local savePath assignment')
    s=replace_one(s,'io.open(savePath, "rb")','rsProbeOpen(savePath, "rb")','checksum file open')
    s=replace_one(s,'saveFile:read(0x20000)','rsProbeRead(saveFile, 0x20000)','checksum file read')
    # The original checksum function is called on every screen update; capture its
    # actual return without invoking an extra file read or changing RNG math.
    hook=r'''local __originalChecksumXor = getCurrentXORChecksumSeed
function getCurrentXORChecksumSeed(list)
 local value = __originalChecksumXor(list)
 rsProbe.checksum = value
 return value
end
local __originalRSUpdate = updateBuffers
function updateBuffers()
 rsProbeFrame(__originalRSUpdate)
end
'''
    s=replace_one(s,'initializeBuffers()\nprintGameInfo()\ncallbacks:add("frame", updateBuffers)',
                  hook+'initializeBuffers()\nprintGameInfo()\ncallbacks:add("frame", updateBuffers)',
                  'frame callback wrapper')
    return prelude+'\n'+s

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variant',choices=['minimal','original','cached'],required=True)
    p.add_argument('--source',type=Path)
    p.add_argument('--save-path',type=Path,help='existing Ruby/Sapphire .sav used by both variants')
    p.add_argument('--label',required=True)
    p.add_argument('--output-dir',type=Path,default=Path('tests/rs_checksums/output'))
    a=p.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}',a.label):p.error('label must be ASCII letters/digits/_/-')
    if a.variant!='minimal' and not a.source:p.error('original/cached require --source')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    trace=(a.output_dir/(a.label+'_frames.tsv')).resolve()
    script=a.output_dir/(a.label+'_probe.lua')
    source=a.source.read_text(encoding='utf-8-sig') if a.source else None
    script.write_text(build(source,a.variant,trace,a.save_path),encoding='utf-8')
    trace.write_text('timestamp\tseconds\tframes\tsave_opens\tsave_reads\tsave_bytes\ttotal_ticks\tcpu_s\tmax_cpu_s\tlast_xor\n',encoding='utf-8')
    print('mGBA script:',script.resolve())
    print('Trace path:',trace)
    print('One script per test. Set mGBA fast-forward manually, then restore the same game state.')
if __name__=='__main__':main()
