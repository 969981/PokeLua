#!/usr/bin/env python3
"""Summarize two real-mGBA callback performance logs without inventing FPS data."""
import argparse
import csv
import json
from pathlib import Path
import statistics

def read(path):
    result=[]
    with path.open(encoding='utf-8',newline='') as f:
        for x in csv.DictReader(f,delimiter='\t'):
            elapsed=int(x['elapsed_s']); n=int(x['frame_callbacks']); render=int(x['render_calls'])
            if elapsed>0 and n>0:
                result.append({'elapsed_s':elapsed,'frames':n,'renders':render,
                    'cpu_s':float(x['callback_cpu_s']), 'max_cpu_s':float(x['max_callback_cpu_s']),
                    'callback_fps':n/elapsed, 'render_hz':render/elapsed})
    if not result:raise ValueError(f'no samples in {path}')
    return result

def aggregate(a, discard):
    a=a[discard:]
    if not a: raise ValueError('too many warmup samples discarded')
    secs=sum(x['elapsed_s'] for x in a)
    frames=sum(x['frames'] for x in a)
    return {'samples':len(a),'seconds':secs,'callback_fps':frames/secs,
      'effective_speed_x_at_59_7275fps': frames/secs/59.7275,
      'render_hz':sum(x['renders'] for x in a)/secs,
      'mean_callback_cpu_ms':1000*sum(x['cpu_s'] for x in a)/frames,
      'worst_callback_cpu_ms':1000*max(x['max_cpu_s'] for x in a),
      'sample_fps_min':min(x['callback_fps'] for x in a),
      'sample_fps_median':statistics.median(x['callback_fps'])}

def event_lines(p):
    with p.open(encoding='utf-8',newline='') as f:
        return [(int(x['tick']),int(x['emulator_frame']),x['event'],x['seed_value']) for x in csv.DictReader(f,delimiter='\t')]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,required=True, help='original-script tsv from same scenario')
    p.add_argument('--optimized',type=Path,required=True)
    p.add_argument('--warmup',type=int,default=5,help='discard N initial 1-second samples, default 5')
    p.add_argument('--min-seconds',type=int,default=90)
    p.add_argument('--baseline-events',type=Path)
    p.add_argument('--optimized-events',type=Path)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    b=aggregate(read(args.baseline),args.warmup)
    o=aggregate(read(args.optimized),args.warmup)
    ratio=o['callback_fps']/b['callback_fps']
    trace=None
    if bool(args.baseline_events) != bool(args.optimized_events):p.error('provide both event logs or neither')
    if args.baseline_events:
        x=event_lines(args.baseline_events);y=event_lines(args.optimized_events)
        trace={'exact_tick_frame_event_seed_parity':x==y,
           'same_event_and_seed_sequence':[(z[2],z[3]) for z in x]==[(z[2],z[3]) for z in y],
           'baseline_events':len(x),'optimized_events':len(y),
           'note':'Exact parity requires identical savestates, start frame and manually reproduced controller inputs.'}
    report={'evidence':'REAL_MGBA_USER_LOGS_UNVERIFIED_BY_ASSISTANT',
      'metric':'emu frame callback throughput, not graphics render FPS',
      'baseline':b,'optimized':o,'throughput_ratio':ratio,
      'throughput_retained_90pct_target':ratio>=0.90,
      'duration_gate_met':min(b['seconds'],o['seconds'])>=args.min_seconds,
      'events':trace,'warnings':[
       'No-script baseline required for absolute script overhead; this compares original with optimized.',
       'Both Lua copies are instrumented; os.clock() measures callback CPU approximation and may perturb speed.',
       'Do not claim RNG/Bot parity without synchronized savestates and frame-exact trace validation.']}
    out=json.dumps(report,indent=2,ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(out+'\n',encoding='utf-8')
        print(f'Wrote {args.output}')
    else:print(out)

if __name__=='__main__':main()
