#!/usr/bin/env python3
"""Re-capture every screenshot listed in shots.json using headless Chrome.

Reports which images CHANGED since the last run (by SHA-256), so you know which
parts of the draft need a human or Claude to re-read. Standard library only.

Usage: python3 refresh_shots.py [--only NAME]
"""
import hashlib, json, subprocess, sys, time, pathlib

ROOT = pathlib.Path(__file__).parent
cfg = json.loads((ROOT / "shots.json").read_text())
lock_path = ROOT / "shots" / "lock.json"
lock = json.loads(lock_path.read_text()) if lock_path.exists() else {}
only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None

changed = []
for s in cfg["shots"]:
    if only and s["name"] != only:
        continue
    url = s["url"]
    if "://" not in url:
        url = (ROOT / url).resolve().as_uri()
    out = ROOT / "shots" / f"{s['name']}.png"
    cmd = [cfg["chrome"], "--headless=new", "--disable-gpu", "--hide-scrollbars",
           f"--window-size={s['width']},{s['height']}", f"--screenshot={out}", url]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if not out.exists():
        print(f"FAIL {s['name']}: {r.stderr[-200:]}")
        continue
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    status = "NEW" if s["name"] not in lock else ("CHANGED" if lock[s["name"]]["sha256"] != digest else "unchanged")
    lock[s["name"]] = {"sha256": digest, "captured": time.strftime("%Y-%m-%d"), "url": s["url"]}
    print(f"{status:9} {s['name']}  ->  {out.relative_to(ROOT)}  (used in: {', '.join(s.get('used_in', []))})")
    if status == "CHANGED":
        changed.append(s["name"])

lock_path.write_text(json.dumps(lock, indent=2))
if changed:
    print("\nReview the draft text near these screenshots:", ", ".join(changed))
