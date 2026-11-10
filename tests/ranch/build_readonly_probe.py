#!/usr/bin/env python3
"""Generate a separate read-only My Pokemon Ranch Dolphin Lua scan profiler.

The original Ranch Lua remains untouched. The generated copy instruments only
ReadValue32 accounting, thread/stack visits and onScriptUpdate scan timing.
"""
import argparse
import json
from pathlib import Path
import re

PROBE_PRELUDE = r'''
-- Read-only profiling: counts RAM reads but never writes to game memory.
-- This file is GENERATED; do not use its timings as baseline uninstrumented FPS.
local ranchProbe = {
 updates=0, scans=0, found=0, threads=0, frames=0, read32=0,
 totalCpu=0, maxScanCpu=0
}
local ranchProbeInScan = false
local ranchProbeClock = (os and os.clock) and os.clock or nil
local ranchProbePath = __LOG_PATH__
local ranchProbeInterval = __REPORT_INTERVAL__
'''

PROBE_FLUSH = r'''
-- Profile flush runs AFTER the original onScriptUpdate; game output unchanged.
local __originalRanchUpdate = onScriptUpdate
function onScriptUpdate()
 __originalRanchUpdate()
 ranchProbe.updates = ranchProbe.updates + 1
 if ranchProbe.updates % ranchProbeInterval == 0 then
  if io and io.open then
   local log = io.open(ranchProbePath, "a")
   if log then
    log:write(string.format("%d\t%d\t%d\t%d\t%d\t%d\t%.8f\t%.8f\n",
      ranchProbe.updates, ranchProbe.scans, ranchProbe.found,
      ranchProbe.threads, ranchProbe.frames, ranchProbe.read32,
      ranchProbe.totalCpu, ranchProbe.maxScanCpu))
    log:close()
   end
  end
 end
end

'''

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise ValueError(f'{label}: expected one source location, got {count}')
    return text.replace(old, new, 1)

def build(source, log_path, interval):
    if interval < 1: raise ValueError('interval must be positive')
    if 'local ranchProbe = {' in source: raise ValueError('already instrumented')
    newline='\r\n' if '\r\n' in source else '\n'
    s=source.replace('\r\n','\n')
    prelude=PROBE_PRELUDE.replace('__LOG_PATH__', json.dumps(str(log_path.resolve()), ensure_ascii=False))
    prelude=prelude.replace('__REPORT_INTERVAL__', str(interval))
    s=replace_once(s, 'local read8Bit = ReadValue8\n',prelude+'\nlocal read8Bit = ReadValue8\n','prelude')
    s=replace_once(s, '''local function read32Bit(addr)
 return ReadValue32(addr) & 0xFFFFFFFF
end''', '''local function read32Bit(addr)
 if ranchProbeInScan then ranchProbe.read32 = ranchProbe.read32 + 1 end
 return ReadValue32(addr) & 0xFFFFFFFF
end''', 'read-only read counter')

    start=s.index('local function findOfferedPK4(build)\n')
    stop=s.index('\n-- Position (0-3)',start)
    sub=s[start:stop]
    sub=replace_once(sub,'local function findOfferedPK4(build)\n',
        '''local function findOfferedPK4(build)
 ranchProbe.scans = ranchProbe.scans + 1
 local __startCpu = ranchProbeClock and ranchProbeClock() or nil
 ranchProbeInScan = true
''','scan entry')
    sub=replace_once(sub,'''  if not isPointer(thread) then
   break
  end

  local frame''','''  if not isPointer(thread) then
   break
  end
  ranchProbe.threads = ranchProbe.threads + 1

  local frame''','thread count')
    sub=replace_once(sub,'''   if not isPointer(frame) then
    break
   end

   if read32Bit''','''   if not isPointer(frame) then
    break
   end
   ranchProbe.frames = ranchProbe.frames + 1

   if read32Bit''','frame count')
    sub=replace_once(sub,'''     return object + build.pk4Offset''','''     local result = object + build.pk4Offset
     ranchProbeInScan = false
     ranchProbe.found = ranchProbe.found + 1
     local __elapsed = __startCpu and ranchProbeClock() - __startCpu or 0
     ranchProbe.totalCpu = ranchProbe.totalCpu + __elapsed
     if __elapsed > ranchProbe.maxScanCpu then ranchProbe.maxScanCpu = __elapsed end
     return result''','successful scan')
    sub=replace_once(sub,''' return nil
end''',''' ranchProbeInScan = false
 local __elapsed = __startCpu and ranchProbeClock() - __startCpu or 0
 ranchProbe.totalCpu = ranchProbe.totalCpu + __elapsed
 if __elapsed > ranchProbe.maxScanCpu then ranchProbe.maxScanCpu = __elapsed end
 return nil
end''','scan not found')
    s=s[:start]+sub+s[stop:]
    s=replace_once(s,'function onScriptCancel()\n',PROBE_FLUSH+'\nfunction onScriptCancel()\n','update wrapper')
    return s.replace('\n',newline)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path('Gen 4/Dolphin/Ranch_RNG_Dolphin.lua'))
    p.add_argument('--output-dir',type=Path,default=Path('tests/ranch/output'))
    p.add_argument('--label',default='ranch_scan')
    p.add_argument('--interval',type=int,default=300,help='flush cumulative counters every N updates')
    a=p.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,50}',a.label): p.error('invalid label')
    if a.interval<1:p.error('interval must be positive')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    target=a.output_dir/(a.label+'_instrumented.lua')
    logfile=(a.output_dir/(a.label+'_scan.tsv')).resolve()
    # Generate on the machine where Dolphin runs, to keep log paths valid.
    text=build(a.source.read_text(encoding='utf-8-sig'),logfile,a.interval)
    target.write_text(text,encoding='utf-8')
    logfile.write_text('updates\tscans\tfound\tthreads\tstack_frames\tread32_calls\tscan_cpu_s\tmax_scan_cpu_s\n',encoding='utf-8')
    print('Generated (load in Dolphin Lua Core):',target.resolve())
    print('Read-only profile log:',logfile)
    print('Does not write to game RAM. CPU time and scan counts are instrumentation observations, not uninstrumented FPS.')
if __name__=='__main__':main()
