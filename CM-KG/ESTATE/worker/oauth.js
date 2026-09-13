// REGISTRIES GATE (TO 100, CEO Sept 13 2026) — agentic-registries.ai is the authorization server of the estate.
// RFC 8414 metadata on every surface, RFC 7591 dynamic client registration for agents, client_credentials token issuance (ES256 JWT, kid of record),
// JWKS, and a bearer-token gate for licensed routes. Public routes stay open. Clients and receipts live in KV (STATUS namespace, prefixes oauth:*).
import { OPERATOR, CORPORATE, headers, json } from './chrome.js';

export const ISSUER = 'https://agentic-registries.ai';
export const AUDIENCE = 'https://mcp.capitalmarketsknowledgegraph.ai';
export const SCOPES = ['records:read', 'events:read', 'licensed:read'];
const TTL = 3600;
const b64u = buf => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const b64uJson = o => b64u(new TextEncoder().encode(JSON.stringify(o)));
const unb64u = s => Uint8Array.from(atob(s.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - s.length % 4) % 4)), c => c.charCodeAt(0));
const rand = n => b64u(crypto.getRandomValues(new Uint8Array(n)));
async function sha256(s) { return b64u(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s))); }

export function metadata() {
  return { issuer: ISSUER, token_endpoint: `${ISSUER}/oauth/token`, registration_endpoint: `${ISSUER}/oauth/register`, jwks_uri: `${ISSUER}/oauth/jwks.json`, introspection_endpoint: `${ISSUER}/oauth/introspect`,
    scopes_supported: SCOPES, response_types_supported: ['none'], grant_types_supported: ['client_credentials'], token_endpoint_auth_methods_supported: ['client_secret_post', 'client_secret_basic'],
    token_endpoint_auth_signing_alg_values_supported: ['ES256'], service_documentation: `${ISSUER}/auth.md`, op_policy_uri: 'https://allooloo.io/terms', op_tos_uri: 'https://allooloo.io/terms', ui_locales_supported: ['en'],
    'x-allooloo': { operator: OPERATOR, audience: AUDIENCE, token_lifetime_seconds: TTL, licensed_routes: ['https://agentic-trades.ai/licensed/record/{node}/{exchange}/{code}', `${ISSUER}/registry/whoami`], public_routes: 'every MCP door, record and event path, and every surface stay open without a token' } };
}
export async function jwks(env) { try { const prv = JSON.parse(env.OAUTH_JWK); const { d, ...pub } = prv; pub.use = 'sig'; return { keys: [pub] }; } catch (e) { return { keys: [] }; } }

// ---- client registration (RFC 7591): an agent registers itself; the operator's confirmation is the KV record it leaves
export async function register(request, env) {
  let body; try { body = await request.json(); } catch (e) { return json({ error: 'invalid_client_metadata', error_description: 'JSON body required' }, { node: 'registry' }, 'no-store', 400); }
  const name = String(body.client_name || '').trim(); if (!name) return json({ error: 'invalid_client_metadata', error_description: 'client_name is required' }, { node: 'registry' }, 'no-store', 400);
  const scope = String(body.scope || 'records:read events:read').split(/\s+/).filter(s => SCOPES.includes(s)).join(' ') || 'records:read';
  const client_id = 'cmkg_' + rand(12); const client_secret = rand(32); const now = Math.floor(Date.now() / 1000);
  const rec = { client_id, secret_hash: await sha256(client_secret), client_name: name, agent_card: body.agent_card || body.agent_card_url || null, client_uri: body.client_uri || null, contacts: body.contacts || [], scope, grant_types: ['client_credentials'], token_endpoint_auth_method: 'client_secret_post', client_id_issued_at: now, state: 'active', nodes: body.nodes || 'all', valid_until: body.valid_until || null };
  await env.STATUS.put(`oauth:client:${client_id}`, JSON.stringify(rec));
  const out = { ...rec, client_secret, client_secret_expires_at: 0, registration_client_uri: `${ISSUER}/oauth/register/${client_id}` }; delete out.secret_hash;
  return json(out, { node: 'registry' }, 'no-store', 201);
}
export async function clientInfo(env, id) { const c = await env.STATUS.get(`oauth:client:${id}`, 'json'); if (!c) return null; const { secret_hash, ...pub } = c; return pub; }

// ---- token issuance: client_credentials, ES256 JWT
async function signJwt(env, claims) {
  const prv = JSON.parse(env.OAUTH_JWK); const key = await crypto.subtle.importKey('jwk', prv, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
  const h = b64uJson({ alg: 'ES256', typ: 'JWT', kid: prv.kid }); const p = b64uJson(claims); const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, key, new TextEncoder().encode(`${h}.${p}`));
  return `${h}.${p}.${b64u(sig)}`;
}
export async function token(request, env) {
  const ct = request.headers.get('content-type') || ''; let form = {};
  try { if (ct.includes('application/json')) form = await request.json(); else { const fd = await request.formData(); for (const [k, v] of fd.entries()) form[k] = v; } } catch (e) { return json({ error: 'invalid_request' }, { node: 'registry' }, 'no-store', 400); }
  let id = form.client_id, secret = form.client_secret; const auth = request.headers.get('authorization') || '';
  if (auth.startsWith('Basic ')) { try { const [u, p] = atob(auth.slice(6)).split(':'); id = id || decodeURIComponent(u); secret = secret || decodeURIComponent(p); } catch (e) { /* fall through */ } }
  if ((form.grant_type || '') !== 'client_credentials') return json({ error: 'unsupported_grant_type', error_description: 'client_credentials only' }, { node: 'registry' }, 'no-store', 400);
  const c = id ? await env.STATUS.get(`oauth:client:${id}`, 'json') : null;
  if (!c || c.state !== 'active' || !secret || (await sha256(secret)) !== c.secret_hash) return new Response(JSON.stringify({ error: 'invalid_client' }), { status: 401, headers: headers({ node: 'registry' }, { 'content-type': 'application/json', 'WWW-Authenticate': 'Basic realm="agentic-registries.ai"', 'cache-control': 'no-store' }) });
  if (c.valid_until && c.valid_until < new Date().toISOString().slice(0, 10)) return json({ error: 'invalid_client', error_description: 'licence expired' }, { node: 'registry' }, 'no-store', 401);
  const asked = String(form.scope || c.scope).split(/\s+/).filter(s => c.scope.split(' ').includes(s)).join(' ') || c.scope;
  const now = Math.floor(Date.now() / 1000); const jti = rand(12);
  const jwt = await signJwt(env, { iss: ISSUER, sub: c.client_id, aud: AUDIENCE, scope: asked, client_name: c.client_name, iat: now, exp: now + TTL, jti });
  try { await env.STATUS.put(`oauth:receipt:${jti}`, JSON.stringify({ client_id: c.client_id, scope: asked, iat: now, exp: now + TTL, event: 'token_issued' }), { expirationTtl: 86400 * 30 }); } catch (e) { /* best effort */ }
  return json({ access_token: jwt, token_type: 'Bearer', expires_in: TTL, scope: asked }, { node: 'registry' }, 'no-store');
}
// ---- verification: the gate for licensed routes
export async function verify(request, env) {
  const auth = request.headers.get('authorization') || ''; if (!auth.startsWith('Bearer ')) return { ok: false, error: 'missing_token' };
  const parts = auth.slice(7).trim().split('.'); if (parts.length !== 3) return { ok: false, error: 'malformed_token' };
  try {
    const prv = JSON.parse(env.OAUTH_JWK); const { d, ...pub } = prv; const key = await crypto.subtle.importKey('jwk', pub, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['verify']);
    const ok = await crypto.subtle.verify({ name: 'ECDSA', hash: 'SHA-256' }, key, unb64u(parts[2]), new TextEncoder().encode(`${parts[0]}.${parts[1]}`)); if (!ok) return { ok: false, error: 'bad_signature' };
    const claims = JSON.parse(new TextDecoder().decode(unb64u(parts[1]))); const now = Math.floor(Date.now() / 1000);
    if (claims.iss !== ISSUER || claims.aud !== AUDIENCE) return { ok: false, error: 'wrong_issuer_or_audience' };
    if (!claims.exp || claims.exp < now) return { ok: false, error: 'expired' };
    return { ok: true, claims };
  } catch (e) { return { ok: false, error: 'verify_failed' }; }
}
export function challenge(resourceHost, error) {
  return new Response(JSON.stringify({ error: error || 'unauthorized', authorization_server: ISSUER, register: `${ISSUER}/oauth/register`, token: `${ISSUER}/oauth/token`, documentation: `${ISSUER}/auth.md` }, null, 1), { status: 401, headers: headers({ node: 'registry' }, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', 'WWW-Authenticate': `Bearer realm="${resourceHost}", resource_metadata="https://${resourceHost}/.well-known/oauth-protected-resource"${error ? `, error="${error}"` : ''}` }) });
}
export async function introspect(request, env) {
  let form = {}; try { const fd = await request.formData(); for (const [k, v] of fd.entries()) form[k] = v; } catch (e) { /* empty */ }
  const fake = new Request('https://x/', { headers: { authorization: 'Bearer ' + (form.token || '') } }); const v = await verify(fake, env);
  return json(v.ok ? { active: true, ...v.claims, token_type: 'Bearer' } : { active: false }, { node: 'registry' }, 'no-store');
}
export async function stats(env) { let n = 0; try { const l = await env.STATUS.list({ prefix: 'oauth:client:' }); n = l.keys.length; } catch (e) { /* none */ } return { authorization_server: ISSUER, registered_clients: n, grant: 'client_credentials', token_lifetime_seconds: TTL, licensed_routes: metadata()['x-allooloo'].licensed_routes }; }
