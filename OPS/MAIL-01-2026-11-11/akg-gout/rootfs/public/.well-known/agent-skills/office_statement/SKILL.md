---
name: office_statement
description: The office's current holdings summary, signed EdDSA (kid mk-office-x402-2026-09): via MCP tool office_statement, the paid call GET /api, or the licensed route /licensed/statement.
---

# office_statement

The office's current holdings summary, signed EdDSA (kid mk-office-x402-2026-09): via MCP tool office_statement, the paid call GET /api, or the licensed route /licensed/statement.

## Input

```json
{
  "type": "object",
  "properties": {},
  "additionalProperties": false
}
```

## Output

```json
{
  "type": "object",
  "properties": {
    "statement": {
      "type": "string"
    },
    "data": {
      "type": "object"
    },
    "kid": {
      "type": "string"
    },
    "jwks": {
      "type": "string"
    }
  },
  "required": [
    "statement",
    "data"
  ]
}
```

## Endpoints

- https://agent-kg.ai/mcp
- https://agent-kg.ai/api
- https://agent-kg.ai/licensed/statement

Operator: Agentic KG Holdings · Principal: Matthew Keddy · Surface: https://agent-kg.ai · Keyring: https://agent-kg.ai/.well-known/jwks.json
