#!/usr/bin/env bash
# Lint one Markdown doc with Claude and return machine-readable findings.
# Exit 1 if any finding has severity "high", so CI can fail the build.
#
# Usage: ./doc_lint_ci.sh docs/auth.md
# Add --bare to the claude call in CI (needs ANTHROPIC_API_KEY; skips local hooks/plugins/CLAUDE.md).
set -euo pipefail
FILE="${1:?usage: doc_lint_ci.sh <file.md>}"

SCHEMA='{
  "type": "object",
  "properties": {
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "line":     { "type": "integer" },
          "severity": { "type": "string", "enum": ["high", "medium", "low"] },
          "rule":     { "type": "string" },
          "fix":      { "type": "string" }
        },
        "required": ["line", "severity", "rule", "fix"]
      }
    }
  },
  "required": ["findings"]
}'

OUT=$(claude -p \
  "Review the Markdown document on stdin against our style guide: active voice, present tense, second person, sentence-case headings, images need alt text, never show a real-looking password or secret (that is severity high). Report every violation with its line number." \
  --output-format json \
  --json-schema "$SCHEMA" < "$FILE")

echo "$OUT" | jq '.structured_output.findings'
echo "cost: \$$(echo "$OUT" | jq -r '.total_cost_usd')" >&2

HIGH=$(echo "$OUT" | jq '[.structured_output.findings[] | select(.severity == "high")] | length')
if [ "$HIGH" -gt 0 ]; then
  echo "FAIL: $HIGH high-severity finding(s)" >&2
  exit 1
fi
echo "PASS" >&2
