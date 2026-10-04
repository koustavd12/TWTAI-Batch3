#!/usr/bin/env python3
"""PostToolUse hook: lint a Markdown file Claude just wrote or edited.

Claude Code sends JSON on stdin: {"tool_name": "...", "tool_input": {"file_path": "..."}, ...}
Exit 0 = fine. Exit 2 = send stderr back to Claude so it can fix the problem.
"""
import json, re, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

path = (data.get("tool_input") or {}).get("file_path", "")
if not path.endswith(".md"):
    sys.exit(0)

try:
    lines = open(path, encoding="utf-8").read().splitlines()
except OSError:
    sys.exit(0)

problems = []
in_code = False
for n, line in enumerate(lines, 1):
    if line.strip().startswith("```"):
        in_code = not in_code
        continue
    if in_code:
        continue
    m = re.match(r"^(#{1,6})\s+(.*)$", line)
    if m:
        words = m.group(2).split()
        caps = [w for w in words[1:] if w[:1].isupper() and not w.isupper()]
        if len(caps) >= 2:
            problems.append(f"{path}:{n}: heading looks Title Case; use sentence case: '{m.group(2)}'")
    if re.search(r"!\[\]\(", line):
        problems.append(f"{path}:{n}: image has no alt text")
    if re.search(r"\b(is|are|was|were|been|being)\s+\w+ed\s+by\b", line, re.I):
        problems.append(f"{path}:{n}: passive voice ('... was done by ...'); prefer active")

if problems:
    print("Doc lint found issues:\n" + "\n".join(problems), file=sys.stderr)
    sys.exit(2)
sys.exit(0)
