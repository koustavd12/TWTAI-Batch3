#!/usr/bin/env python3
"""PreToolUse hook: block hand-edits to generated files (screenshots, lockfiles).

Allow = print nothing, exit 0 (normal permission flow applies).
Deny  = print the JSON decision below; Claude sees the reason and adjusts.
"""
import json, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

path = (data.get("tool_input") or {}).get("file_path", "")
GENERATED = ("/shots/", "shots/lock.json")

if any(marker in path for marker in GENERATED):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "This file is generated. Do not edit it by hand. "
                "Run `python3 refresh_shots.py` to regenerate screenshots."
            ),
        }
    }))
sys.exit(0)
