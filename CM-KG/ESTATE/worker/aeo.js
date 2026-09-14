// Agent readiness kit (CEO, Sept 12 2026) for every surface the estate Worker serves — built to the isitagentready.com check list read from its
// POST /api/scan on the day (the START_ME_UP_5_AGENT_READINESS_AEO.md spec was not on disk): Link headers, markdown negotiation, Content-Signal in
// robots.txt, RFC 9264 api-catalog, RFC 9728 protected-resource metadata (open resource, truthfully), auth.md, MCP server card, A2A Agent Card to the
// current spec (skills + supportedInterfaces), Agent Skills index + SKILL.md files, ARD ai-catalog, real 404s. Everything points at the node's own
// mcp. door (nodes), the apex router (allooloo.io, product roots, estate roots) or the beacon variant (Hong Kong). CMR headers v1 stay on every response.
import { OPERATOR, CORPORATE, CONTACT, CONTACT2, APEX, APEX_AGENT, SURFACES_VERSION, REGION_FULL, esc, today } from './chrome.js';

export const TOOLS = [
  ['resolve_issuer', 'Resolve an issuer', 'Find a listed company by ticker (with exchange prefix or suffix), ISIN, LEI, legal name or sourced alias; returns the record summary, node and version.', 'identifier (string)'],
  ['get_record', 'Read the record', 'Return the full Capital Markets Record for an issuer: every identity field with value, source URL, reader and state; aliases; gaps; the events URL.', 'identifier (string), version (optional)'],
  ['list_aliases', 'List the names', 'Every name the issuer has traded or filed under, each with its source.', 'identifier (string)'],
  ['list_events_since', 'Disclosure events since a date', 'Dated, typed disclosure events for an issuer over the trailing twelve months, newest first, paged.', 'identifier (string), since (YYYY-MM-DD), cursor, limit'],
  ['list_nodes', 'The twelve nodes', 'Which node holds which market, live or not, record and event counts, drop date, door and Agent Card URLs.', '(none)']
];
export const CONTENT_SIGNAL = 'Content-Signal: search=yes, ai-input=yes, ai-train=yes';
export const KEYRING = 'https://agentic-x402.ai/x402/jwks.json';   // the estate keyring of record (x402 receipts key, kid allooloo-x402-receipts-2026-09); the CMR keyring joins when signing ships

// Where this host's agent answers: the node door, the apex, or the beacon.
export function target(c, cc) {
  if (c.kind === 'node' && cc === 'hk') return { kind: 'beacon', mcp: null, agent: null, openapi: null, mcpjson: null, name: 'Hong Kong node — beacon (Width 0, local partner wanted)', note: 'no door and no agent; the apex answers not found for Hong Kong identifiers' };
  if (c.kind === 'node') return { kind: 'node', mcp: `https://mcp.${cc}-cm-kg.ai/mcp`, agent: `https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json`, openapi: `https://mcp.${cc}-cm-kg.ai/openapi.json`, mcpjson: `https://mcp.${cc}-cm-kg.ai/mcp.json`, name: `${cc}-cm-kg door` };
  if (c.kind === 'product' && c.product === 'x402') return { kind: 'apex', mcp: `${APEX}/mcp`, agent: `${APEX_AGENT}/.well-known/agent-card.json`, openapi: 'https://agentic-x402.ai/openapi.json', mcpjson: `${APEX}/mcp.json`, name: 'Agentic x402 — a paid call with a signed receipt (apex door for MCP)' };
  return { kind: 'apex', mcp: `${APEX}/mcp`, agent: `${APEX_AGENT}/.well-known/agent-card.json`, openapi: `${APEX}/openapi.json`, mcpjson: `${APEX}/mcp.json`, name: 'Capital Markets Knowledge Graph — apex router' };
}
export function linkHeader(host, t) {
  const parts = [`<https://${host}/llms.txt>; rel="llms-txt"; type="text/plain"`, `<https://${host}/>; rel="alternate"; type="text/markdown"`, `<https://${host}/.well-known/agent-card.json>; rel="agent-card"; type="application/json"`, `<https://${host}/.well-known/api-catalog>; rel="api-catalog"; type="application/linkset+json"`, `<https://${host}/.well-known/mcp/server-card.json>; rel="mcp-server-card"; type="application/json"`, `<https://${host}/.well-known/mcp.json>; rel="mcp-server-card"; type="application/json"`, `<https://${host}/.well-known/ai-catalog.json>; rel="ai-catalog"; type="application/json"`, `<https://${host}/.well-known/ard.json>; rel="ard"; type="application/ard+json"`, `<${KEYRING}>; rel="keyring"; type="application/json"`];
  if (t.openapi) parts.push(`<${t.openapi}>; rel="service-desc"; type="application/json"`);
  return parts.join(', ');
}
export function apiCatalog(host, t, extra) {
  const item = { anchor: `https://${host}/`, 'service-doc': [{ href: `https://${host}/llms.txt`, type: 'text/plain' }, { href: `https://${host}/auth.md`, type: 'text/markdown' }], 'service-meta': [{ href: `https://${host}/.well-known/mcp/server-card.json`, type: 'application/json' }, { href: `https://${host}/.well-known/agent-card.json`, type: 'application/json' }] };
  if (t.openapi) item['service-desc'] = [{ href: t.openapi, type: 'application/json' }];
  const set = [item];
  if (t.mcp) set.push({ anchor: t.mcp, 'service-desc': [{ href: t.openapi, type: 'application/json' }], 'service-meta': [{ href: t.mcpjson, type: 'application/json' }, { href: t.agent, type: 'application/json' }], 'service-doc': [{ href: t.mcp.replace('/mcp', '/llms.txt'), type: 'text/plain' }] });
  for (const e of (extra || [])) set.push(e);
  return { linkset: set };
}
export function protectedResource(host, t) {
  return { resource: `https://${host}`, authorization_servers: ['https://agentic-registries.ai'], bearer_methods_supported: ['header'], scopes_supported: ['records:read', 'events:read', 'licensed:read'], resource_name: `${host} — ${OPERATOR}`, resource_documentation: `https://${host}/auth.md`, resource_policy_uri: 'https://allooloo.io/terms', note: 'public routes (every MCP door, record and event path, every surface) require no authentication; licensed routes take a bearer token from the Registries authorization server (client_credentials)' };
}
export function authMd(host, t) {
  const AS = 'https://agentic-registries.ai'; const door = t.mcp ? t.mcp : APEX + '/mcp';
  return `# auth.md

This service supports agentic registration. Resource server: \`https://${host}\` (this surface; its MCP door is \`${door}\`). Authorization server: \`${AS}\` (the Registries gate, in service Sept 13 2026). Public routes — every surface, every MCP door, every record and event path — answer without a token, read-only, public-record only. Licensed routes take a bearer token.

## Discover

1. Read \`WWW-Authenticate: Bearer resource_metadata="https://${host}/.well-known/oauth-protected-resource"\` on a 401, or fetch \`/.well-known/oauth-protected-resource\` directly: \`resource\`, \`resource_name\`, \`authorization_servers\` (\`${AS}\`), \`scopes_supported\` (\`records:read\`, \`events:read\`, \`licensed:read\`), \`bearer_methods_supported\` (\`header\`).
2. Fetch \`${AS}/.well-known/oauth-authorization-server\` (also served on every surface): \`issuer\`, \`token_endpoint\`, \`registration_endpoint\`, \`revocation_endpoint\`, \`jwks_uri\`, \`grant_types_supported\` and the \`agent_auth\` block (\`identity_endpoint\`, \`claim_endpoint\`, \`events_endpoint\`, \`identity_types_supported\`).

## Pick a method

- Session with an ID-JAG → not offered here (\`identity_assertion\` is not in \`identity_types_supported\`).
- Email only → not offered here (\`service_auth\` is not in \`identity_types_supported\`).
- Neither → \`anonymous\`: register below. Registrations are active on issue; no claim ceremony is required.
- A plain OAuth client → \`POST ${AS}/oauth/register\` (RFC 7591) then \`client_credentials\`.

## Register

### anonymous

\`\`\`http
POST /agent/identity HTTP/1.1
Host: agentic-registries.ai
Content-Type: application/json

{
  "type": "anonymous",
  "client_name": "my agent",
  "agent_card": "https://my-agent.example/.well-known/agent-card.json",
  "scope": "records:read events:read licensed:read"
}
\`\`\`

Response (201):

\`\`\`json
{
  "identity_type": "anonymous",
  "identity_assertion": "<JWT, typ identity_assertion, 30 days>",
  "assertion_expires": "<ISO 8601>",
  "claim_token": "<opaque>",
  "client_id": "cmkg_…",
  "client_secret": "<shown once>",
  "scopes": ["records:read", "events:read", "licensed:read"]
}
\`\`\`

### client_credentials (RFC 7591 registration)

\`\`\`http
POST /oauth/register HTTP/1.1
Host: agentic-registries.ai
Content-Type: application/json

{ "client_name": "my agent", "agent_card": "https://…/.well-known/agent-card.json", "scope": "records:read events:read licensed:read", "contacts": ["…"] }
\`\`\`

Response (201): \`client_id\`, \`client_secret\` (shown once), \`scope\`, \`registration_client_uri\`.

## Claim ceremony

Optional. Registrations are active on issue. To attach a contact to an anonymous registration:

\`\`\`http
POST /agent/identity/claim HTTP/1.1
Host: agentic-registries.ai
Content-Type: application/json

{ "claim_token": "<from registration>", "email": "agent-owner@example" }
\`\`\`

Response: \`{ "claim_attempt": { "status": "complete", "client_id": "cmkg_…" } }\` — no user code, no verification URI, no polling.

## Exchange the assertion

\`\`\`http
POST /oauth/token HTTP/1.1
Host: agentic-registries.ai
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=<identity_assertion>&scope=licensed:read
\`\`\`

or, with client credentials:

\`\`\`http
POST /oauth/token HTTP/1.1
Host: agentic-registries.ai
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=cmkg_…&client_secret=…&scope=licensed:read
\`\`\`

Response: \`{ "access_token": "<ES256 JWT>", "token_type": "Bearer", "expires_in": 3600, "scope": "licensed:read" }\`. Audience \`${APEX}\`; keys at \`${AS}/oauth/jwks.json\` (kid allooloo-registry-2026-09-13); \`POST ${AS}/oauth/introspect\` with \`token=\` answers \`active\`.

## Use the access_token

\`Authorization: Bearer <access_token>\` on the licensed routes: \`https://agentic-trades.ai/licensed/record/{node}/{exchange}/{code}\` (the same record as the free route, receipted per client) and \`${AS}/registry/whoami\`. Tokens last 3600 s; get a new one with the same grant — there is no refresh token. The paid x402 route on agentic-trades.ai takes payment instead of a token. Public routes never need the header.

## Errors

| Code | Endpoint | Action |
|------|----------|--------|
| \`invalid_client\` | \`/oauth/token\` | client_id, client_secret or licence wrong or expired: register again or write to the operator |
| \`invalid_grant\` | \`/oauth/token\`, \`/agent/identity/claim\` | assertion or claim_token invalid, expired or revoked: register again |
| \`unsupported_grant_type\` | \`/oauth/token\` | use \`client_credentials\` or \`urn:ietf:params:oauth:grant-type:jwt-bearer\` |
| \`unsupported_identity_type\` | \`/agent/identity\` | use \`anonymous\` |
| \`missing_token\`, \`expired\`, \`revoked\`, \`bad_signature\` | licensed routes (401 + \`WWW-Authenticate\`) | get a new access token |

## Revocation

Credential layer: \`POST ${AS}/oauth/revoke\` with \`token=<access_token or identity_assertion>\` (RFC 7009; always 200). Registration layer: a registration is set inactive by the operator on the firm's instruction, on licence expiry (\`valid_until\`) or on misuse; its tokens stop at their next request. Revocation events for registered agents are accepted at \`${AS}/agent/event/notify\` (RFC 8935, \`application/secevent+jwt\`). Nothing is deleted; registrations and receipts stay on the registry.

Operator: ${OPERATOR}. The agents that built this read their own mail: ${CONTACT2}. Questions: the contact form at ${CONTACT}. Surface version ${SURFACES_VERSION}; as of ${today()}.
`;
}
export function mcpServerCard(host, t, live, label) {
  const base = { name: t.name, scope: t.kind === 'node' ? `${t.name.replace(' door', '')} only` : t.kind === 'beacon' ? 'nothing answered on this node' : `every live node through the apex router; this surface: ${label || host}`, serverInfo: { name: t.kind === 'node' ? t.name.replace(' door', '') : 'cm-kg', version: '0.12.1' }, description: t.kind === 'beacon' ? t.note : 'Capital Markets Knowledge Graph: one record per listed company, source and read date on every field, served in the issuer\'s jurisdiction. Read-only, public-record only, no auth.', transport: t.mcp ? 'streamable-http' : null, url: t.mcp, endpoints: t.mcp ? [{ type: 'streamable-http', url: t.mcp }] : [], authentication: { type: 'none' }, tools: TOOLS.map(([n, tt, d]) => ({ name: n, title: tt, description: d })), agentCard: t.agent, openapi: t.openapi, descriptor: t.mcpjson, registry: 'io.github.allooloo/cm-kg', documentation: `https://${host}/llms.txt`, provider: { organization: OPERATOR, url: CORPORATE }, surface: `https://${host}/`, as_of: today() };
  if (t.kind === 'beacon') base.beacon = true;
  return base;
}
export function agentCard(host, t, label, description, live, cc) {
  const skills = t.kind === 'beacon'
    ? [{ id: 'beacon', name: 'Beacon — Hong Kong at Width 0', description: 'The roster (HKEX Main Board, GEM, REITs) is held, not served; no filings read; no door until a local partner reads them. Hong Kong identifiers answer not found at the apex.', tags: ['capital-markets', 'hong-kong', 'beacon'], examples: [] }]
    : TOOLS.map(([n, tt, d, p]) => ({ id: n, name: tt, description: d, tags: ['capital-markets', 'public-record', 'mcp', cc || 'estate'], inputModes: ['application/json'], outputModes: ['application/json'], examples: [n === 'list_nodes' ? '{"tool":"list_nodes","arguments":{}}' : `{"tool":"${n}","arguments":{"identifier":"…"}}`], parameters: p }));
  const url = t.mcp || `${APEX}/mcp`;
  return { name: label, description, url, preferredTransport: 'JSONRPC', supportedInterfaces: [{ url, transport: 'JSONRPC' }], additionalInterfaces: [{ url, transport: 'JSONRPC' }], version: '0.12.1', protocolVersion: '0.3.0', provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, iconUrl: `https://${host}/icon-512.png`,
    capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false, extensions: [] }, defaultInputModes: ['application/json', 'text/plain'], defaultOutputModes: ['application/json'], securitySchemes: {}, security: [], skills, agentCardOfRecord: t.agent, 'x-cmkg': { registry: 'io.github.allooloo/cm-kg', surface_version: SURFACES_VERSION, beacon: t.kind === 'beacon' || undefined, x402: { endpoint: 'https://agentic-x402.ai/api', surface_endpoint: `https://${host}/api`, surface: 'https://agentic-x402.ai/', price_usdc: '0.01', receipts: 'https://agentic-x402.ai/x402/receipt/{nonce}', jwks: 'https://agentic-x402.ai/x402/jwks.json' } } };
}
export function skillsIndex(host, t) {
  const list = t.kind === 'beacon' ? [['beacon', 'Beacon — Hong Kong at Width 0', 'What is held and what is wanted on the Hong Kong node; where the other eleven answer.']] : TOOLS.map(([n, tt, d]) => [n.replace(/_/g, '-'), tt, d]);
  return { name: `${host} agent skills`, description: 'Skills for calling the Capital Markets Knowledge Graph doors over MCP (Streamable HTTP, JSON-RPC 2.0, no auth).', skills: list.map(([id, name, description]) => ({ name: id, id, description, url: `https://${host}/.well-known/agent-skills/${id}/SKILL.md`, path: `${id}/SKILL.md` })), as_of: today() };
}
export function skillMd(host, t, id) {
  if (t.kind === 'beacon' && id === 'beacon') return `---\nname: beacon\ndescription: Hong Kong node of the Capital Markets Knowledge Graph at Width 0 — roster held, no door; where the other eleven markets answer.\n---\n# Beacon — Hong Kong at Width 0\n\n1. The Hong Kong roster (HKEX Main Board, GEM, REITs; stock code, ISIN, English name, LEI where GLEIF maps it) is held in the build pond and not served.\n2. No filings are read; no MCP door, no Agent Card; a local partner is wanted.\n3. The other eleven markets answer through the apex router: POST JSON-RPC to ${APEX}/mcp with tool \`list_nodes\` to see which node holds which market.\n4. Operator: ${OPERATOR}. Surface: https://${host}/\n`;
  if (t.kind === 'beacon') return null;
  const tool = TOOLS.find(x => x[0].replace(/_/g, '-') === id); if (!tool) return null;
  const [n, tt, d, p] = tool; const url = t.mcp || `${APEX}/mcp`;
  return `---\nname: ${id}\ndescription: ${d}\n---\n# ${tt} (\`${n}\`)\n\n1. Door: \`${url}\` — MCP Streamable HTTP, JSON-RPC 2.0, stateless, no auth, read-only, public-record only.\n2. Call:\n\n\`\`\`json\n{ "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": { "name": "${n}", "arguments": { ${n === 'list_nodes' ? '' : '"identifier": "TSX:SHOP"'}${n === 'list_events_since' ? ', "since": "2026-01-01"' : ''} } } }\n\`\`\`\n\n3. Arguments: ${p}.\n4. Answer: \`result.structuredContent\` — ${d}\n5. Every field carries \`source_url\`, \`read_by\` and \`state\`; blank stays blank; no prices, quotes or licensed market data.\n6. Identifier forms: exchange prefix (\`TSX:SHOP\`, \`LSE:SHEL\`, \`XETRA:SAP\`), suffix (\`SHOP.TO\`, \`7203.T\`), ISIN, LEI, legal name, sourced alias. The apex routes to the node that holds the name; a node door answers its own market only.\n7. Descriptors: ${t.openapi || APEX + '/openapi.json'} · ${t.mcpjson || APEX + '/mcp.json'} · Agent Card ${t.agent || APEX_AGENT + '/.well-known/agent-card.json'}.\n8. Operator: ${OPERATOR}. Surface: https://${host}/ (version ${SURFACES_VERSION}).\n`;
}
export function aiCatalog(host, t, label, description) {
  // ARD manifest (agenticresourcediscovery.org): domain-anchored urn:air identifiers, IANA media types, one url each, representativeQueries in a banker's words. One catalog per zone, own voice; served at /.well-known/ai-catalog.json and /.well-known/ard.json.
  const urn = (ns, name) => `urn:air:${host}:${ns}:${name}`;
  const door = t.mcp ? t.name : 'the apex router';
  const entries = [];
  if (t.mcp) {
    entries.push({ identifier: urn('server', t.kind === 'node' ? t.name.replace(' door', '') : 'cm-kg'), displayName: t.name, type: 'application/mcp-server-card+json', url: `https://${host}/.well-known/mcp/server-card.json`, description: `MCP door of the Capital Markets Knowledge Graph reached from ${host}: five read-only tools, public-record only, no auth, served in the issuer's own jurisdiction.`, capabilities: TOOLS.map(x => x[0]), representativeQueries: ['resolve TSX:SHOP and tell me which node holds the record', 'give me the Capital Markets Record for LSE:BARC with the source of every field', 'list the disclosure events for XETRA:SAP since 2026-01-01', 'which of the twelve market nodes are live and how many issuer records does each hold'] });
    entries.push({ identifier: urn('agent', t.kind === 'node' ? t.name.replace(' door', '') : 'cm-kg'), displayName: label, type: 'application/a2a-agent-card+json', url: t.agent, description: `A2A Agent Card of the agent that answers for ${host}; skills mirror the five MCP tools.`, capabilities: ['a2a', 'jsonrpc'], representativeQueries: ['what can the Capital Markets Knowledge Graph agent do for a dealer', 'which skills does the cm-kg agent expose over A2A'] });
    entries.push({ identifier: urn('api', 'read-paths'), displayName: 'HTTP read paths', type: 'application/vnd.oai.openapi+json', url: t.openapi, description: 'OpenAPI 3.1 description of the door\'s HTTP read paths (record, events, aliases, nodes).', capabilities: ['openapi', 'read-only'], representativeQueries: ['fetch the record for uk-cm-kg/LSE/BARC over plain HTTPS', 'what HTTP paths does the door expose without MCP'] });
    entries.push({ identifier: urn('skills', 'catalog'), displayName: `${host} agent skills`, type: 'application/json', url: `https://${host}/.well-known/agent-skills/index.json`, description: 'Agent Skills index: one SKILL.md per tool with the door, the call shape and the answer shape.', capabilities: TOOLS.map(x => x[0].replace(/_/g, '-')), representativeQueries: ['show me the skill file for reading a Capital Markets Record', 'how do I call list_events_since from an agent'] });
  } else {
    entries.push({ identifier: urn('beacon', 'hk-cm-kg'), displayName: t.name, type: 'text/plain', url: `https://${host}/llms.txt`, description: t.note, capabilities: ['beacon'], representativeQueries: ['is the Hong Kong node of the Capital Markets Knowledge Graph live', 'where do Hong Kong listed companies answer'] });
  }
  entries.push({ identifier: urn('document', 'llms-txt'), displayName: `${host} llms.txt`, type: 'text/plain', url: `https://${host}/llms.txt`, description: `What ${host} is, its counts live from list_nodes, its kit paths and its doors, in twelve numbered lines.`, capabilities: ['llms-txt'], representativeQueries: [`what is ${host} and who operates it`, 'where are the machine paths for this surface'] });
  entries.push({ identifier: urn('catalog', 'api-linkset'), displayName: 'API catalog (RFC 9264 linkset)', type: 'application/linkset+json', url: `https://${host}/.well-known/api-catalog`, description: 'Linkset of the surface\'s service documents, descriptions and metadata.', capabilities: ['linkset'], representativeQueries: ['list the API descriptions this host links to', 'where is the service description for the door'] });
  entries.push({ identifier: urn('api', 'paid-call'), displayName: `Paid call — ${host}/api`, type: 'application/json', url: `https://${host}/api`, description: 'HTTP 402 door (x402 v2, scheme exact, $0.01 USDC on Base): pays for this surface\'s statement of record and answers with an EdDSA-signed receipt that resolves forever at /x402/receipt/{nonce}. Doctrine: https://agentic-x402.ai/.', capabilities: ['x402', 'receipt'], representativeQueries: ['what does one paid call on this surface cost and what does it return', 'how do I pay for a receipted call with USDC on Base'] });
  return { specVersion: '1.0', name: label, description, host: { displayName: label, identifier: `did:web:${host}`, url: `https://${host}/` }, publisher: { name: OPERATOR, url: CORPORATE, identifier: 'did:web:allooloo.io' }, url: `https://${host}/`, updated: today(), entries, capabilities: t.mcp ? [{ type: 'mcp', name: t.name, url: t.mcp, transport: 'streamable-http', auth: 'none', tools: TOOLS.map(x => x[0]) }, { type: 'a2a', name: label, agentCard: t.agent }, { type: 'openapi', url: t.openapi }, { type: 'x402', url: `https://${host}/api`, price_usdc: '0.01' }] : [{ type: 'beacon', name: t.name, note: t.note }, { type: 'x402', url: `https://${host}/api`, price_usdc: '0.01' }], documentation: [`https://${host}/llms.txt`, `https://${host}/auth.md`, 'https://agentic-radar.ai/radar.json', 'https://agentic-x402.ai/'], contact: CONTACT, door };
}
// HTML → Markdown for the markdown-negotiated twin of every page (same content, no chrome duplication beyond the title).
export function toMarkdown(html, host) {
  let s = html.replace(/<head>[\s\S]*?<\/head>/, '').replace(/<header>[\s\S]*?<\/header>/, '').replace(/<footer>[\s\S]*?<\/footer>/, '').replace(/<form[\s\S]*?<\/form>/g, '(contact form: https://allooloo.io/#contact)');
  s = s.replace(/<div class="tile"><div class="v">([\s\S]*?)<\/div><div class="k">([\s\S]*?)<\/div>(?:<div class="s">([\s\S]*?)<\/div>)?<\/div>/g, (m, v, k, src) => `\n- ${v.replace(/<[^>]+>/g, '')} ${k.replace(/<[^>]+>/g, '')}${src ? ' (' + src.replace(/<[^>]+>/g, '') + ')' : ''}`).replace(/<\/div>/g, '\n');
  s = s.replace(/<pre>([\s\S]*?)<\/pre>/g, (m, a) => '\n```\n' + a + '\n```\n');
  s = s.replace(/<table[^>]*>([\s\S]*?)<\/table>/g, (m, a) => { const rows = [...a.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map(r => [...r[1].matchAll(/<t[hd][^>]*>([\s\S]*?)<\/t[hd]>/g)].map(c => c[1].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim())); if (!rows.length) return ''; return '\n| ' + rows[0].join(' | ') + ' |\n|' + rows[0].map(() => ' --- ').join('|') + '|\n' + rows.slice(1).map(r => '| ' + r.join(' | ') + ' |').join('\n') + '\n'; });
  s = s.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/g, '\n# $1\n').replace(/<h2[^>]*>([\s\S]*?)<\/h2>/g, '\n## $1\n').replace(/<dt>([\s\S]*?)<\/dt>\s*<dd>([\s\S]*?)<\/dd>/g, '\n- **$1** $2').replace(/<p[^>]*>([\s\S]*?)<\/p>/g, '\n$1\n').replace(/<a [^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g, '[$2]($1)').replace(/<code>([\s\S]*?)<\/code>/g, '`$1`').replace(/<br\s*\/?>/g, '\n');
  s = s.replace(/<[^>]+>/g, '').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/\n{3,}/g, '\n\n').trim();
  return s + `\n\n---\n${OPERATOR} · https://${host}/ · public-record only · version ${SURFACES_VERSION}\n`;
}
export const wantsMarkdown = req => { const a = (req.headers.get('accept') || '').toLowerCase(); return a.includes('text/markdown') && (a.indexOf('text/markdown') < (a.indexOf('text/html') === -1 ? 1e9 : a.indexOf('text/html'))); };
