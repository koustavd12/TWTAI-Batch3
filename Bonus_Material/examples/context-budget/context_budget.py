#!/usr/bin/env python3
"""Estimate what your setup puts into Claude's context at the START of every session.

Rough rule: 1 token is about 4 characters of English. Treat results as estimates,
and use /context inside Claude Code for the real numbers.

Counts, for a project folder (and optionally ~/.claude):
  - CLAUDE.md                  -> fully loaded every session
  - skills (description only)  -> only the name + description is always loaded;
                                  the body loads when the skill is invoked
  - agents (description only)  -> same idea
  - output styles, commands    -> listed for awareness

Usage: python3 context_budget.py [folder] [--home]
"""
import pathlib, re, sys

def toks(text): return max(1, round(len(text) / 4))

def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    if not m: return {}, text
    meta = dict(re.findall(r"^([\w-]+):\s*(.+)$", m.group(1), re.M))
    return meta, m.group(2)

def scan(root: pathlib.Path, label: str):
    rows = []
    for p in list(root.glob("CLAUDE.md")) + list(root.glob(".claude/CLAUDE.md")):
        rows.append((f"{label}CLAUDE.md", "always-on", toks(p.read_text())))
    for kind in ("skills", "agents"):
        pattern = "**/SKILL.md" if kind == "skills" else "**/*.md"
        for base in [root / ".claude" / kind, root / kind]:
            for p in base.glob(pattern) if base.exists() else []:
                text = p.read_text()
                meta, body = frontmatter(text)
                head = f"{meta.get('name','')} {meta.get('description','')}"
                rows.append((f"{label}{kind[:-1]}: {meta.get('name', p.stem)}", "always-on (description)", toks(head)))
                rows.append((f"{label}{kind[:-1]}: {meta.get('name', p.stem)}", "on-invoke (body)", toks(body)))
    return rows

target = pathlib.Path(next((a for a in sys.argv[1:] if not a.startswith("--")), ".")).resolve()
rows = scan(target, "")
if "--home" in sys.argv:
    rows += scan(pathlib.Path.home() / ".claude", "~/ ")

always = sum(t for _, kind, t in rows if kind.startswith("always"))
print(f"{'Item':44} {'When loaded':26} {'~tokens':>8}")
print("-" * 80)
for name, kind, t in sorted(rows, key=lambda r: (r[1], -r[2])):
    print(f"{name[:44]:44} {kind:26} {t:>8}")
print("-" * 80)
print(f"{'Always-on total (estimate)':71} {always:>8}")
print(f"{'Share of a 200,000-token window':71} {always/200000:>8.2%}")
