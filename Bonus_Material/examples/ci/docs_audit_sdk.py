#!/usr/bin/env python3
"""Audit a docs folder with the Claude Agent SDK and return structured findings.

pip install claude-agent-sdk
export ANTHROPIC_API_KEY=...        # the SDK uses API-key auth

NOT RUN in the STC article (no API key was available). Syntax-checked only.
Signatures follow the official Python reference: query(), ClaudeAgentOptions,
ResultMessage.structured_output / total_cost_usd.
"""
import asyncio, json, sys
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

SCHEMA = {
    "type": "object",
    "properties": {
        "pages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "missing_sections": {"type": "array", "items": {"type": "string"}},
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                },
                "required": ["file", "missing_sections", "score"],
            },
        }
    },
    "required": ["pages"],
}


async def main(folder: str) -> int:
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep"],        # read-only: cannot edit anything
        permission_mode="dontAsk",                      # deny anything that would prompt
        max_turns=30,
        system_prompt="You audit API documentation for completeness. Never invent content.",
        output_format={"type": "json_schema", "schema": SCHEMA},
    )
    prompt = (f"Audit every Markdown file under {folder}. For each, list missing sections "
              "(description, authentication, parameters, response example, error codes, example) "
              "and give a completeness score.")
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            print(json.dumps(message.structured_output, indent=2))
            print(f"cost: ${message.total_cost_usd}", file=sys.stderr)
            weakest = min((p["score"] for p in message.structured_output["pages"]), default=100)
            return 1 if weakest < 60 else 0           # fail CI when any page scores below 60
    return 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "docs")))
