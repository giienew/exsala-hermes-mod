#!/usr/bin/env python3
"""Aggregate THC farm output/run_*.json -> totals + error_kind breakdown.

Usage:
    python3 scripts/analyze_output.py [OUTPUT_DIR]

OUTPUT_DIR default: ~/app/cache/scratch/thc/output
Classifies failures by error_kind and by elapsed_ms bucket (fast-close
<10s = dead proxy/network, slow ~30s = OOM chromium), so the next action
(swap proxy vs cleanup orphan chromium) is unambiguous.
"""
import json
import sys
from collections import Counter
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "~/app/cache/scratch/thc/output"
)

files = sorted(OUT.glob("run_*.json"))
records = []
for f in files:
    try:
        records.extend(json.loads(f.read_text()))
    except Exception:
        pass  # truncated/partial file from a killed run

ok = [r for r in records if r.get("ok") and r.get("api_key")]
failed = [r for r in records if not (r.get("ok") and r.get("api_key"))]

kinds = Counter(r.get("error_kind") or r.get("error", "")[:30] or "" for r in failed)
fast = sum(1 for r in failed if r.get("elapsed_ms", 99999) < 10000)
slow = len(failed) - fast

print(f"run files : {len(files)}")
print(f"records   : {len(records)}")
print(f"ok+key    : {len(ok)}")
print(f"failed    : {len(failed)}")
print(f"fast-close (<10s, dead proxy): {fast}")
print(f"slow-close (>=10s, OOM/checkpoint): {slow}")
print("by error_kind:")
for k, n in kinds.most_common():
    print(f"  {n:4d}  {k}")
