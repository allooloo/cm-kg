---
name: holding_attestation
description: A line signed with the office key (kid mk-office-2026-09) that a company estate is the office's: GET /attest/{holding-host} for wefetch.ai or allooloo.io.
---

# holding_attestation

A line signed with the office key (kid mk-office-2026-09) that a company estate is the office's: GET /attest/{holding-host} for wefetch.ai or allooloo.io.

## Input

```json
{
  "type": "object",
  "properties": {
    "host": {
      "type": "string",
      "enum": [
        "wefetch.ai",
        "allooloo.io",
        "familyofficeknowledgegraph.ai",
        "rco-a2a.ai"
      ]
    }
  },
  "required": [
    "host"
  ]
}
```

## Output

```json
{
  "type": "object",
  "properties": {
    "attestation": {
      "type": "string"
    },
    "claims": {
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
    "attestation",
    "claims"
  ]
}
```

## Endpoints

- https://agent-kg.ai/attest/{host}

Operator: Agentic KG Holdings · Principal: Matthew Keddy · Surface: https://agent-kg.ai · Keyring: https://agent-kg.ai/.well-known/jwks.json
