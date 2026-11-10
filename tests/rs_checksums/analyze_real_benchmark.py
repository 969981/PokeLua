#!/usr/bin/env python3
"""Compare actual mGBA callback throughput for minimal/original/cached RS Lua.

Results are per scenario, per emulator speed. No fabricated measurements.
"""
import argparse
import csv
import json
from pathlib import Path
import statistics

def read_log(path, warmup):
    with path.open(encoding='utf-8',newline='') as handle:
        rows=list(csv.DictReader(handle,delimiter='\t'))
    parsed=[]
    for r in rows:
        try:
            d={k:int(r[k]) for k in ('timestamp','seconds','frames','save_opens','save_reads','save_bytes','total_ticks')}
            d.update({k:float(r[k]) for k in ('cpu_s','max_cpu_s')})
            d['last_xor']=r['last_xor'].strip()
            if d['seconds']>0 and d['frames']>0: parsed.append(d)
        except (ValueError,KeyError) as exc:
            raise ValueError(f'{path}: invalid row {r}: {exc}')
    if len(parsed)<=warmup: raise ValueError(f'{path}: no samples after warmup={warmup}')
    return parsed[warmup:]

def summarize(rows):
    seconds=sum(r['seconds'] for r in rows)
    frames=sum(r['frames'] for r in rows)
    return {
        'duration_s':seconds,
        'sample_windows':len(rows),
        'callback_fps':frames/seconds,
        'effective_speed_x_at_59_7275fps':frames/seconds/59.7275,
        'save_opens':sum(r['save_opens'] for r in rows),
        'save_reads':sum(r['save_reads'] for r in rows),
        'save_bytes':sum(r['save_bytes'] for r in rows),
        'read_ops_per_1000_frames':1000*sum(r['save_reads'] for r in rows)/frames,
        'mean_cpu_ms_per_callback':1000*sum(r['cpu_s'] for r in rows)/frames,
        'worst_callback_cpu_ms':1000*max(r['max_cpu_s'] for r in rows),
        'sample_fps_p50':statistics.median(r['frames']/r['seconds'] for r in rows),
        'last_xor':next((r['last_xor'] for r in reversed(rows) if r['last_xor']),None)
    }

def evaluate(minimal,original,cached,minimum):
    all_long=all(x['duration_s']>=minimum for x in (minimal,original,cached))
    ratio=cached['callback_fps']/original['callback_fps']
    cache_vs_minimal=cached['callback_fps']/minimal['callback_fps']
    xor_equal=(original['last_xor']==cached['last_xor'] and original['last_xor'] is not None)
    return {
        'evidence':'REAL_MGBA_PROBE_LOGS_NOT_INDEPENDENTLY_VERIFIED',
        'minimal':minimal,'original':original,'cached':cached,
        'cached_to_original_fps_ratio':ratio,
        'cached_to_minimal_fps_ratio':cache_vs_minimal,
        'cached_read_reduction_ratio':(
            1-cached['save_reads']/original['save_reads']
            if original['save_reads'] else None),
        'stabilized_checksum_xor_equal':xor_equal,
        'duration_gate_met':all_long,
        'checksum_gate_met':xor_equal,
        'status':'REVIEW_READY' if all_long else 'INSUFFICIENT_DURATION',
        'warnings':[
            'Source variant, .sav path, emulator build, ROM/save hashes, same in-game scene and speed must match.',
            'Sample FPS is Lua frame callback throughput, not UI/GPU FPS.',
            'Minimal probe is NOT no-script baseline; probe and logging add overhead.',
            'At 1x cap throughput may be identical despite reduced CPU usage.',
            'Matching last XOR is NOT full 28-segment identity or proof of save-disk flush timing.'
        ]
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for field in ('minimal','original','cached'):
        p.add_argument('--'+field,required=True,type=Path)
    p.add_argument('--warmup-windows',default=5,type=int)
    p.add_argument('--minimum-seconds',default=90,type=int)
    p.add_argument('--out',type=Path)
    p.add_argument('--scene',default='unlabeled')
    p.add_argument('--requested-speed',default='unknown')
    a=p.parse_args()
    if a.warmup_windows<0 or a.minimum_seconds<0:p.error('warmup and minimum must be nonnegative')
    v={k:summarize(read_log(getattr(a,k),a.warmup_windows)) for k in ('minimal','original','cached')}
    report=evaluate(v['minimal'],v['original'],v['cached'],a.minimum_seconds)
    report['scene']=a.scene
    report['requested_speed']=a.requested_speed
    text=json.dumps(report,indent=2,ensure_ascii=False)+'\n'
    if a.out:
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(text,encoding='utf-8')
        print('Wrote',a.out)
    else:print(text)
if __name__=='__main__':main()
