# Review instructions (docs repository)

## What Important means here

Reserve Important for anything that would make a reader fail or get hurt:
a wrong command, parameter, endpoint, or default; a step missing from a
procedure; a real-looking password, token, or key; a broken link in a
procedure; a screenshot that contradicts the step beside it.
Style, tone, and wording preferences are Nit at most.

## Cap the nits

Report at most five Nits per review. If you found more, write
"plus N similar items" in the summary instead of posting them inline.
If everything you found is a Nit, start the summary with "No blocking issues."

## Do not report

- Anything CI already enforces: link check, spellcheck, Markdown lint
- Generated files under `shots/` and any `*.lock` file
- Release-notes entries written by the release bot

## Always check

- Every code sample matches the parameters documented in the same page
- Every procedure has prerequisites before step 1 and an expected result after the last step
- Headings are sentence case; images have alt text
- Text near a changed screenshot still matches what the screenshot shows

## Verification bar

A claim about product behavior needs a `file:line` citation in the source
or the OpenAPI spec, not an inference from a name.

## Summary shape

Open with a one-line tally such as "2 factual, 4 style".
