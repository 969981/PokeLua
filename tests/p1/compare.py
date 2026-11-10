#!/usr/bin/env python3
"""FRLG P1 regression: compare upstream to develop without downloading/sharing ROMs.

Run from the repository root:
 python tests/p1/compare.py
 python tests/p1/compare.py --lua texlua
"""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
FRLG = "Gen 3/mGBA/FRLG_RNG_mGBA.lua"
HARNESS = ROOT / "tests/p1/frlg_mock.lua"

def with_targets(source):
    # Same test targets for both branches; otherwise upstream has empty targets.
    for name, value in [("botTargetInitialSeeds", "0x2222"), ("botTargetTIDs", "1")]:
        pat = r"(?m)^(local " + name + r"\s*=\s*)\{[^}\n]*\}"
        source, matches = re.subn(pat, lambda m: m.group(1) + "{" + value + "}", source, count=1)
        assert matches == 1, f"missing config for {name}"
    return source

def run(lua, source, scenario, speed, ticks):
    with tempfile.TemporaryDirectory(prefix="frlg-p1-") as temp:
        script = pathlib.Path(temp) / "run.lua"
        script.write_text(with_targets(source), encoding="utf-8")
        cmd = [lua, str(HARNESS), str(script), scenario, str(speed), str(ticks)]
        proc = subprocess.run(cmd, text=True, capture_output=True, check=True)
        output = proc.stdout
    def segment(start, end):
        return output.split(start+"\n",1)[1].split("\n"+end,1)[0]
    metric_match = re.search(r"METRIC reads=(\d+) prints=(\d+) clears=(\d+) callbacks=(\d+)",output)
    assert metric_match, "missing metric"
    return {
        "actions": segment("ACTIONS_BEGIN","ACTIONS_END"),
        "rng": segment("RNG_BEGIN","RNG_END"),
        "metrics": dict(zip(("reads","prints","clears","callbacks"),map(int,metric_match.groups()))),
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--lua",default=shutil.which("lua") or shutil.which("lua5.4") or shutil.which("texlua"))
    parser.add_argument("--original-file",help="optional original Lua path (else git show main:path)")
    parser.add_argument("--optimized-file",default=str(ROOT / FRLG))
    args=parser.parse_args()
    assert args.lua, "Lua 5.3+ runtime required (e.g. lua or texlua)"
    if args.original_file:
        before=pathlib.Path(args.original_file).read_text(encoding="utf-8")
    else:
        before=subprocess.check_output(["git","show","main:"+FRLG],cwd=ROOT,text=True)
    after=pathlib.Path(args.optimized_file).read_text(encoding="utf-8")
    cases=[("idle",1,1200),("idle",16,4800),("tid",16,200),("seed",16,200)]
    results=[]
    for mode,speed,ticks in cases:
        a=run(args.lua,before,mode,speed,ticks)
        b=run(args.lua,after,mode,speed,ticks)
        assert a["actions"]==b["actions"], f"{mode} input/Watchpoint/savestate trace changed"
        assert a["rng"]==b["rng"], f"{mode} RNG Advances trace changed"
        assert b["metrics"]["callbacks"]==ticks
        assert b["metrics"]["prints"]<a["metrics"]["prints"], f"{mode} render load did not decline"
        if mode=="tid":
            assert "write:1@" in b["actions"] and b["actions"].count("loadbuf@")>=2
        if mode=="seed":
            assert "write:8738@" in b["actions"] and b["actions"].count("loadbuf@")>=1
        results.append({
            "scenario":mode,"multiplier_simulated":speed,"callbacks":ticks,
            "exact_actions_equal":True,"rng_advances_equal":True,
            "original":a["metrics"],"optimized":b["metrics"],
            "evidence":"OFFLINE_MOCK_ONLY"
        })
    print(json.dumps({"status":"MOCK_PASS","results":results,
                      "warning":"Not emulator FPS or real ROM compatibility evidence"},indent=2))
if __name__=="__main__":
    main()
