#!/usr/bin/env python3
"""Analyze cumulative Ranch Lua Core scan counters exported by the read-only probe."""
import argparse
import csv
import json
from pathlib import Path

METRICS=('updates','scans','found','threads','stack_frames','read32_calls','scan_cpu_s','max_scan_cpu_s')

def load_rows(path):
    with Path(path).open(encoding='utf-8',newline='') as handle:
        rows=[{name:float(row[name]) if name.endswith('_cpu_s') else int(row[name]) for name in METRICS}
              for row in csv.DictReader(handle,delimiter='\t')]
    if not rows:
        raise ValueError('No Ranch probe samples. Run the generated Lua in Dolphin first.')
    return rows

def analyze(rows):
    last=rows[-1]
    # Values are cumulative since script start. No fabricated FPS data.
    updates=last['updates']
    if updates<=0: raise ValueError('No updates observed')
    windows=[]
    previous={field:0 for field in METRICS}
    for row in rows:
        elapsed=row['updates']-previous['updates']
        scans=row['scans']-previous['scans']
        if elapsed>0:
            windows.append({
                'updates':elapsed,
                'scans_per_update':scans/elapsed,
                'frames_per_scan':(row['stack_frames']-previous['stack_frames'])/scans if scans else 0,
                'read32_per_scan':(row['read32_calls']-previous['read32_calls'])/scans if scans else 0,
                'scan_cpu_ms_per_scan':1000*(row['scan_cpu_s']-previous['scan_cpu_s'])/scans if scans else 0
            })
        previous=row
    return {
        'evidence':'RANCH_DOLPHIN_PROBE_LOG_NOT_UNINSTRUMENTED_FPS',
        'updates':updates,
        'scans':last['scans'],
        'found':last['found'],
        'threads_per_scan':last['threads']/last['scans'] if last['scans'] else None,
        'stack_frames_per_scan':last['stack_frames']/last['scans'] if last['scans'] else None,
        'read32_calls_per_scan':last['read32_calls']/last['scans'] if last['scans'] else None,
        'mean_scan_cpu_ms':1000*last['scan_cpu_s']/last['scans'] if last['scans'] else None,
        'max_scan_cpu_ms':1000*last['max_scan_cpu_s'],
        'windows':windows,
        'warnings':[
            'Probe overhead is included; CPU time does not equal FPS loss.',
            'Clock unavailable may yield zero CPU times. Count metrics still useful.',
            'No offer / Hayley offer / main-menu scenes must be labeled separately.'
        ]
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('tsv',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    report=json.dumps(analyze(load_rows(a.tsv)),indent=2,ensure_ascii=False)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(report+'\n',encoding='utf-8')
        print('Wrote',a.output)
    else: print(report)
if __name__=='__main__':main()
