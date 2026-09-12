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

// Where this host's agent answers: the node door, the apex, or the beacon.
export function target(c, cc) {
  if (c.kind === 'node' && cc === 'hk') return { kind: 'beacon', mcp: null, agent: null, openapi: null, mcpjson: null, name: 'Hong Kong node — beacon (Width 0, local partner wanted)', note: 'no door and no agent; the apex answers not found for Hong Kong identifiers' };
  if (c.kind === 'node') return { kind: 'node', mcp: `https://mcp.${cc}-cm-kg.ai/mcp`, agent: `https://agent.${cc}-cm-kg.ai/.well-known/agent-card.json`, openapi: `https://mcp.${cc}-cm-kg.ai/openapi.json`, mcpjson: `https://mcp.${cc}-cm-kg.ai/mcp.json`, name: `${cc}-cm-kg door` };
  return { kind: 'apex', mcp: `${APEX}/mcp`, agent: `${APEX_AGENT}/.well-known/agent-card.json`, openapi: `${APEX}/openapi.json`, mcpjson: `${APEX}/mcp.json`, name: 'Capital Markets Knowledge Graph — apex router' };
}
export function linkHeader(host, t) {
  const parts = [`<https://${host}/llms.txt>; rel="llms-txt"; type="text/plain"`, `<https://${host}/>; rel="alternate"; type="text/markdown"`, `<https://${host}/.well-known/agent-card.json>; rel="agent-card"; type="application/json"`, `<https://${host}/.well-known/api-catalog>; rel="api-catalog"; type="application/linkset+json"`, `<https://${host}/.well-known/mcp/server-card.json>; rel="mcp-server-card"; type="application/json"`];
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
  return { resource: `https://${host}`, authorization_servers: [], bearer_methods_supported: [], scopes_supported: [], resource_name: `${host} — ${OPERATOR}`, resource_documentation: `https://${host}/auth.md`, resource_policy_uri: 'https://allooloo.io/terms', note: 'open resource: the public doors and surfaces require no authentication; the Registries gate (agent identity, licences, receipts) is not yet in service' };
}
export function authMd(host, t) {
  return `# Auth.md — ${host}\n\n1. Authentication on this host: none. The surface and its machine kit are public-record documents.\n2. Authentication on the doors: none. ${t.mcp ? `The MCP door \`${t.mcp}\` answers Streamable HTTP JSON-RPC to any caller, read-only, under the rate the door states.` : 'This node has no door at Width 0 (beacon); the apex router answers not found for its identifiers.'}\n3. OAuth / OIDC: no authorization server is published (\`/.well-known/openid-configuration\` and \`/.well-known/oauth-authorization-server\` answer 404 on purpose). \`/.well-known/oauth-protected-resource\` states the open resource truthfully.\n4. Registries (the gate): agent identity, the Agent Card presented, licence shape, nodes covered, validity, revocation and receipts — built under its own order; not yet in service. Stated on https://agentic-registries.ai/.\n5. Registration on-ramp when the gate lands: the contact form at ${CONTACT} naming the firm, the agent and the nodes wanted.\n6. Operator: ${OPERATOR}. The agents that built this read their own mail: ${CONTACT2}.\n7. Surface version: ${SURFACES_VERSION}; as of ${today()}.\n`;
}
export function mcpServerCard(host, t, live) {
  const base = { name: t.name, serverInfo: { name: t.kind === 'node' ? t.name.replace(' door', '') : 'cm-kg', version: '0.11.0' }, description: t.kind === 'beacon' ? t.note : 'Capital Markets Knowledge Graph: one record per listed company, source and read date on every field, served in the issuer\'s jurisdiction. Read-only, public-record only, no auth.', transport: t.mcp ? 'streamable-http' : null, url: t.mcp, endpoints: t.mcp ? [{ type: 'streamable-http', url: t.mcp }] : [], authentication: { type: 'none' }, tools: TOOLS.map(([n, tt, d]) => ({ name: n, title: tt, description: d })), agentCard: t.agent, openapi: t.openapi, descriptor: t.mcpjson, registry: 'io.github.allooloo/cm-kg', documentation: `https://${host}/llms.txt`, provider: { organization: OPERATOR, url: CORPORATE }, surface: `https://${host}/`, as_of: today() };
  if (t.kind === 'beacon') base.beacon = true;
  return base;
}
export function agentCard(host, t, label, description, live, cc) {
  const skills = t.kind === 'beacon'
    ? [{ id: 'beacon', name: 'Beacon — Hong Kong at Width 0', description: 'The roster (HKEX Main Board, GEM, REITs) is held, not served; no filings read; no door until a local partner reads them. Hong Kong identifiers answer not found at the apex.', tags: ['capital-markets', 'hong-kong', 'beacon'], examples: [] }]
    : TOOLS.map(([n, tt, d, p]) => ({ id: n, name: tt, description: d, tags: ['capital-markets', 'public-record', 'mcp', cc || 'estate'], inputModes: ['application/json'], outputModes: ['application/json'], examples: [n === 'list_nodes' ? '{"tool":"list_nodes","arguments":{}}' : `{"tool":"${n}","arguments":{"identifier":"…"}}`], parameters: p }));
  const url = t.mcp || `${APEX}/mcp`;
  return { name: label, description, url, preferredTransport: 'JSONRPC', supportedInterfaces: [{ url, transport: 'JSONRPC' }], additionalInterfaces: [{ url, transport: 'JSONRPC' }], version: '0.11.0', protocolVersion: '0.3.0', provider: { organization: OPERATOR, url: CORPORATE }, documentationUrl: `https://${host}/`, iconUrl: `https://${host}/icon-512.png`,
    capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false, extensions: [] }, defaultInputModes: ['application/json', 'text/plain'], defaultOutputModes: ['application/json'], securitySchemes: {}, security: [], skills, agentCardOfRecord: t.agent, 'x-cmkg': { registry: 'io.github.allooloo/cm-kg', surface_version: SURFACES_VERSION, beacon: t.kind === 'beacon' || undefined } };
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
  const entries = t.mcp ? [{ identifier: 'mcp', displayName: t.name, id: 'mcp', type: 'mcp', name: t.name, url: t.mcp, transport: 'streamable-http', auth: 'none', description: 'Capital Markets Knowledge Graph door — five read-only tools, public-record only' }, { identifier: 'a2a', displayName: label, id: 'a2a', type: 'a2a', name: label, url: t.agent || `https://${host}/.well-known/agent-card.json`, description: 'A2A Agent Card' }, { identifier: 'openapi', displayName: 'HTTP read paths', id: 'openapi', type: 'openapi', name: 'HTTP read paths', url: t.openapi, description: 'OpenAPI 3.1 description of the door' }] : [{ identifier: 'beacon', displayName: t.name, id: 'beacon', type: 'beacon', name: t.name, url: `https://${host}/`, description: t.note }];
  return { specVersion: '1.0', name: label, description, publisher: { name: OPERATOR, url: CORPORATE }, url: `https://${host}/`, updated: today(), entries, capabilities: t.mcp ? [{ type: 'mcp', name: t.name, url: t.mcp, transport: 'streamable-http', auth: 'none', tools: TOOLS.map(x => x[0]) }, { type: 'a2a', name: label, agentCard: t.agent || `https://${host}/.well-known/agent-card.json` }, { type: 'openapi', url: t.openapi }] : [{ type: 'beacon', name: t.name, note: t.note }], documentation: [`https://${host}/llms.txt`, `https://${host}/auth.md`, 'https://agentic-radar.ai/radar.json'], contact: CONTACT };
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
