#!/usr/bin/env python3
"""A tiny MCP server over stdio. Standard library only: no pip install.

Protocol: newline-delimited JSON-RPC 2.0 on stdin/stdout.
Tools: doc_stats, find_passive, check_headings.
"""
import json, re, sys

PROTOCOL = "2025-06-18"

TOOLS = [
    {
        "name": "doc_stats",
        "description": "Word count, sentence count, average sentence length, and a Flesch reading-ease score for a block of text.",
        "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    },
    {
        "name": "find_passive",
        "description": "List sentences that look like passive voice (form of 'to be' + past participle).",
        "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    },
    {
        "name": "check_headings",
        "description": "Report Markdown headings that are not sentence case.",
        "inputSchema": {"type": "object", "properties": {"markdown": {"type": "string"}}, "required": ["markdown"]},
    },
]

PASSIVE = re.compile(r"\b(?:is|are|was|were|been|being|be)\s+(?:\w+ly\s+)?\w+(?:ed|en)\b", re.I)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def syllables(word):
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups) - (1 if word.endswith("e") and len(groups) > 1 else 0)
    return max(1, n)


def doc_stats(text):
    words = re.findall(r"[A-Za-z']+", text)
    sents = sentences(text)
    if not words or not sents:
        return "No words found."
    asl = len(words) / len(sents)
    asw = sum(syllables(w) for w in words) / len(words)
    flesch = 206.835 - 1.015 * asl - 84.6 * asw
    return (f"words={len(words)} sentences={len(sents)} "
            f"avg_sentence_length={asl:.1f} flesch_reading_ease={flesch:.0f}")


def find_passive(text):
    hits = [s for s in sentences(text) if PASSIVE.search(s)]
    if not hits:
        return "No passive-voice candidates found."
    return "Passive-voice candidates:\n" + "\n".join(f"- {s}" for s in hits)


def check_headings(markdown):
    out, in_code = [], False
    for n, line in enumerate(markdown.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        m = None if in_code else re.match(r"^#{1,6}\s+(.*)$", line)
        if m:
            words = m.group(1).split()
            caps = [w for w in words[1:] if w[:1].isupper() and not w.isupper()]
            if len(caps) >= 2:
                out.append(f"line {n}: '{m.group(1)}'")
    return "Headings not in sentence case:\n" + "\n".join(out) if out else "All headings are sentence case."


IMPL = {
    "doc_stats": lambda a: doc_stats(a["text"]),
    "find_passive": lambda a: find_passive(a["text"]),
    "check_headings": lambda a: check_headings(a["markdown"]),
}


def reply(id_, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    msg.update({"error": error} if error else {"result": result})
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        msg = json.loads(raw)
        method, id_ = msg.get("method"), msg.get("id")
        if id_ is None:          # notification (e.g. notifications/initialized): no reply
            continue
        if method == "initialize":
            reply(id_, {
                "protocolVersion": (msg.get("params") or {}).get("protocolVersion", PROTOCOL),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "doc-tools", "version": "1.0.0"},
            })
        elif method == "ping":
            reply(id_, {})
        elif method == "tools/list":
            reply(id_, {"tools": TOOLS})
        elif method == "tools/call":
            p = msg.get("params") or {}
            fn = IMPL.get(p.get("name"))
            if not fn:
                reply(id_, error={"code": -32602, "message": f"Unknown tool: {p.get('name')}"})
                continue
            try:
                text = fn(p.get("arguments") or {})
                reply(id_, {"content": [{"type": "text", "text": text}], "isError": False})
            except Exception as e:  # tool errors are results, not protocol errors
                reply(id_, {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True})
        else:
            reply(id_, error={"code": -32601, "message": f"Method not found: {method}"})


if __name__ == "__main__":
    main()
