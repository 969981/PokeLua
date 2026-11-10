#!/usr/bin/env python3
"""Generate a profiling-only copy of BW/B2W2 BizHawk Lua, no behavioral writes removed.

Counts userdata.set calls, repeated scalar values and approximate CPU time.
Generated Lua invokes the original userdata.set with identical arguments.
"""
import argparse
import json
from pathlib import Path
import re

PRELUDE=r'''
-- BEGIN Gen5 userdata.set observe-only probe.
-- Original userdata.set is still called in full, in the same order.
local p2OriginalUserdataSet = userdata.set
local p2UDLastValues = {}
local p2UDCounts = {}
local p2UDProfile = {frames=0,writes=0,unchanged=0,distinct=0,cpu=0}
local p2UDLogPath = __LOG_PATH__
local p2UDLogInterval = __LOG_INTERVAL__
local p2UDClock = os and os.clock and os.clock or nil

local function p2TrackedUserdataSet(key,value)
 local info = p2UDCounts[key]
 if not info then
  info = {writes=0,unchanged=0}
  p2UDCounts[key] = info
  p2UDProfile.distinct = p2UDProfile.distinct + 1
 end
 local repeated = (p2UDLastValues[key] ~= nil and p2UDLastValues[key] == value)
 if repeated then
  info.unchanged = info.unchanged + 1
  p2UDProfile.unchanged = p2UDProfile.unchanged + 1
 end
 info.writes = info.writes + 1
 p2UDProfile.writes = p2UDProfile.writes + 1
 p2UDLastValues[key] = value

 local before = p2UDClock and p2UDClock() or nil
 local result = p2OriginalUserdataSet(key,value)
 if before then p2UDProfile.cpu = p2UDProfile.cpu + (p2UDClock() - before) end
 return result
end

local function p2FlushUserdataProfile()
 p2UDProfile.frames = p2UDProfile.frames + 1
 if p2UDProfile.frames % p2UDLogInterval ~= 0 then return end
 if not (io and io.open) then return end
 local pairsList = {}
 for key, info in pairs(p2UDCounts) do
  pairsList[#pairsList+1] = tostring(key).."="..info.writes.."/"..info.unchanged
 end
 table.sort(pairsList)
 local file = io.open(p2UDLogPath,"a")
 if file then
  file:write(string.format("%d\t%d\t%d\t%d\t%.8f\t%s\n",
     p2UDProfile.frames,p2UDProfile.writes,p2UDProfile.unchanged,
     p2UDProfile.distinct,p2UDProfile.cpu,table.concat(pairsList,",")))
  file:close()
 end
end
-- END Gen5 userdata.set observe-only probe.
'''

def instrument(text, log_path, interval=300):
    if interval<1: raise ValueError('interval must be >= 1')
    if 'BEGIN Gen5 userdata.set observe-only probe' in text:
        raise ValueError('Already instrumented')
    newline='\r\n' if '\r\n' in text else '\n'
    s=text.replace('\r\n','\n')
    source_calls=s.count('userdata.set(')
    if source_calls<3:raise ValueError('No Gen5 per-frame userdata.set calls found')
    s=s.replace('userdata.set(', 'p2TrackedUserdataSet(')
    loop='\nwhile not wrongGameVersion do\n'
    if s.count(loop)!=1:raise ValueError('Expected one game main loop')
    frame='\n emu.frameadvance()\nend'
    if s.count(frame)!=1:raise ValueError('Expected exactly one main emu.frameadvance')
    s=s.replace(frame,'\n p2FlushUserdataProfile()\n emu.frameadvance()\nend',1)
    prelude=PRELUDE.replace('__LOG_PATH__',json.dumps(log_path.as_posix(),ensure_ascii=False))
    prelude=prelude.replace('__LOG_INTERVAL__',str(interval))
    return (prelude+'\n'+s).replace('\n',newline),source_calls

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--label',required=True)
    p.add_argument('--interval',type=int,default=300)
    p.add_argument('--output-dir',type=Path,default=Path('tests/gen5/output'))
    a=p.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}',a.label):p.error('Invalid --label')
    if a.interval<1:p.error('Interval must be positive')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    logfile=(a.output_dir/(a.label+'_userdata.tsv')).resolve()
    content,calls=instrument(a.source.read_text(encoding='utf-8-sig'),logfile,a.interval)
    script=a.output_dir/(a.label+'_instrumented.lua')
    script.write_text(content,encoding='utf-8')
    logfile.write_text('frames\twrites\tunchanged\tdistinct_keys\tuserdata_cpu_s\tkey_counts\n',encoding='utf-8')
    print('Generated:',script.resolve())
    print('Original userdata.set call sites:',calls)
    print('Log:',logfile)
    print('This profiler preserves original userdata.set calls; requires real BizHawk for performance data.')
if __name__=='__main__':main()
