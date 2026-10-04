---
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Here is a draft API page. What is missing from it?

# Create an order
POST /orders creates an order. Send a JSON body with `item` and `quantity`.
Example: curl -X POST https://api.example.com/orders -d '{"item":"A1","quantity":2}'
