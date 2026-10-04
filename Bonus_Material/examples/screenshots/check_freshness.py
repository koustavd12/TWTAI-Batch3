#!/usr/bin/env python3
"""Flag a draft that may be out of date. Exit 1 if anything is stale.

Checks:
  1. Screenshots older than max_age_days (from shots.json)
  2. Images referenced in the draft but missing on disk
  3. 'verified_against' front matter vs the installed `claude --version`
  4. 'last_verified' older than max_age_days

Usage: python3 check_freshness.py draft.md
"""
import json, re, subprocess, sys, pathlib, datetime

ROOT = pathlib.Path(__file__).parent
draft = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "draft.md"
cfg = json.loads((ROOT / "shots.json").read_text())
max_age = cfg.get("max_age_days", 30)
text = draft.read_text()
problems = []
today = datetime.date.today()

lock_path = ROOT / "shots" / "lock.json"
lock = json.loads(lock_path.read_text()) if lock_path.exists() else {}
for name, info in lock.items():
    age = (today - datetime.date.fromisoformat(info["captured"])).days
    if age > max_age:
        problems.append(f"screenshot '{name}' is {age} days old (limit {max_age})")

for ref in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text):
    if "://" not in ref and not (draft.parent / ref).exists():
        problems.append(f"image missing on disk: {ref}")

fm = re.match(r"---\n(.*?)\n---", text, re.S)
meta = dict(re.findall(r"^(\w+):\s*(.+)$", fm.group(1), re.M)) if fm else {}
if "last_verified" in meta:
    age = (today - datetime.date.fromisoformat(meta["last_verified"])).days
    if age > max_age:
        problems.append(f"last_verified is {age} days ago (limit {max_age})")
if "verified_against" in meta:
    try:
        now = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.split()[0]
        want = meta["verified_against"].replace("claude-code ", "").strip()
        if now != want:
            problems.append(f"draft verified against Claude Code {want}, installed is {now}")
    except Exception:
        pass

if problems:
    print("STALE:\n- " + "\n- ".join(problems))
    sys.exit(1)
print("Draft is fresh.")
