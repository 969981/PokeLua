#!/usr/bin/env python3
"""Summarize cumulative Gen5 userdata.set observer counters from real BizHawk."""
import argparse
import csv
import json
from pathlib import Path

def analyze(path):
    with Path(path).open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f,delimiter='\t'))
    if not rows:raise ValueError("No completed observations; run instrumented Lua in BizHawk")
    last=rows[-1]
    f=int(last['frames']);n=int(last['writes']);u=int(last['unchanged'])
    keys={}
    for pair in last['key_counts'].split(','):
        if not pair:continue
        key,vals=pair.split('=',1)
        total,repeat=map(int,vals.split('/',1))
        keys[key]={'writes':total,'unchanged':repeat}
    return {
      'evidence':'BIZHAWK_GEN5_INSTRUMENTED_USERDATA_COUNTERS',
      'frames':f,'writes':n,'unchanged_writes':u,
      'write_calls_per_frame':n/f if f else None,
      'unchanged_share':u/n if n else None,
      'distinct_keys':int(last['distinct_keys']),
      'userdata_set_cpu_s_approx':float(last['userdata_cpu_s']),
      'keys':keys,
      'warnings':[
         'The wrapper still invokes every original userdata.set, in order.',
         'Value repeats alone do not prove it is safe to skip writes on Savestate load.',
         'CPU times include profiler overhead and are not emulator FPS.',
         'Lua-side repeat history is not reset on savestate rewind; repeat counts are only diagnostic.'
      ]
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('tsv',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    out=json.dumps(analyze(a.tsv),ensure_ascii=False,indent=2)+'\n'
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(out,encoding='utf-8')
        print('Wrote',a.output)
    else:print(out)
if __name__=='__main__':main()
