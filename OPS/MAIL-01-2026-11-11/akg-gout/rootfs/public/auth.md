# auth.md — agent-kg.ai (Agentic KG Holdings)

## Posture

Pages, kit files, llms.txt, Markdown twins and every /.well-known/ document on this surface are **open** — no authentication to read. The paid door (GET /api, x402) is priced, not gated. One route is licensed: **/licensed/statement**, the signed holdings summary issued to a registered agent by name.

## Authorization server

- Issuer: https://agent-kg.ai
- Metadata: [/.well-known/oauth-authorization-server](https://agent-kg.ai/.well-known/oauth-authorization-server) (also /.well-known/openid-configuration)
- Protected-resource metadata: [/.well-known/oauth-protected-resource](https://agent-kg.ai/.well-known/oauth-protected-resource)
- Keyring: [/.well-known/jwks.json](https://agent-kg.ai/.well-known/jwks.json) — tokens are EdDSA JWTs signed with the office key, kid mk-office-2026-09
- Grant: client_credentials only. Scopes: office:read, office:attest.

## Agent registration (self-contained, anonymous)

1. `POST https://agent-kg.ai/oauth/register` with JSON `{"client_name": "<your agent>", "client_uri": "<optional>"}` → `client_id`, `client_secret` (shown once). The office binds no user accounts to agents: registration is anonymous by design, and every registration is a line in the office register.
2. `POST https://agent-kg.ai/oauth/token` with `grant_type=client_credentials&client_id=…&client_secret=…&scope=office:attest` → `access_token` (Bearer, 3600 s).
3. `GET https://agent-kg.ai/licensed/statement` with `Authorization: Bearer <token>` → `{ licensed_to, statement, data }` — the holdings summary signed to your client by name.
4. Introspect at `/oauth/introspect` (`token=`); revoke at `/oauth/revoke` with your own client credentials.

Humans reach the office through the form at https://agent-kg.ai/#contact — the only door on the page.

```json
{
  "agent_auth": {
    "skill": "https://agent-kg.ai/auth.md",
    "register_uri": "https://agent-kg.ai/oauth/register",
    "identity_types_supported": [
      "anonymous"
    ],
    "identity_assertion": {
      "assertion_types_supported": [],
      "credential_types_supported": [
        "oauth2_client_credentials"
      ]
    },
    "claim_uri": "https://agent-kg.ai/#contact",
    "revocation_uri": "https://agent-kg.ai/oauth/revoke"
  }
}
```

Operator: Agentic KG Holdings · Principal: Matthew Keddy · Machine contact: mk@agent-kg.ai
