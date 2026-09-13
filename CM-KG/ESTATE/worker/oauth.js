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
    scopes_supported: SCOPES, response_types_supported: ['none'], grant_types_supported: ['client_credentials', 'urn:ietf:params:oauth:grant-type:jwt-bearer'], revocation_endpoint: `${ISSUER}/oauth/revoke`, token_endpoint_auth_methods_supported: ['client_secret_post', 'client_secret_basic'],
    token_endpoint_auth_signing_alg_values_supported: ['ES256'], service_documentation: `${ISSUER}/auth.md`, op_policy_uri: 'https://allooloo.io/terms', op_tos_uri: 'https://allooloo.io/terms', ui_locales_supported: ['en'],
    agent_auth: { skill: `${ISSUER}/auth.md`, identity_endpoint: `${ISSUER}/agent/identity`, claim_endpoint: `${ISSUER}/agent/identity/claim`, events_endpoint: `${ISSUER}/agent/event/notify`, identity_types_supported: ['anonymous'], identity_assertion: { assertion_types_supported: ['urn:ietf:params:oauth:token-type:jwt'] }, events_supported: ['https://schemas.workos.com/events/agent/auth/identity/assertion/revoked'] },
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
  if ((form.grant_type || '') === 'urn:ietf:params:oauth:grant-type:jwt-bearer') {
    const fake = new Request('https://x/', { headers: { authorization: 'Bearer ' + (form.assertion || '') } }); const v = await verify(fake, env, 'identity_assertion');
    if (!v.ok) return json({ error: 'invalid_grant', error_description: v.error }, { node: 'registry' }, 'no-store', 400);
    const c = await env.STATUS.get(`oauth:client:${v.claims.sub}`, 'json'); if (!c || c.state !== 'active') return json({ error: 'invalid_grant', error_description: 'registration not active' }, { node: 'registry' }, 'no-store', 400);
    const asked = String(form.scope || c.scope).split(/\s+/).filter(s => c.scope.split(' ').includes(s)).join(' ') || c.scope; const now = Math.floor(Date.now() / 1000); const jti = rand(12);
    const jwt = await signJwt(env, { iss: ISSUER, sub: c.client_id, aud: AUDIENCE, scope: asked, client_name: c.client_name, iat: now, exp: now + TTL, jti });
    try { await env.STATUS.put(`oauth:receipt:${jti}`, JSON.stringify({ client_id: c.client_id, scope: asked, iat: now, exp: now + TTL, event: 'token_issued', grant: 'jwt-bearer' }), { expirationTtl: 86400 * 30 }); } catch (e) { /* best effort */ }
    return json({ access_token: jwt, token_type: 'Bearer', expires_in: TTL, scope: asked }, { node: 'registry' }, 'no-store');
  }
  if ((form.grant_type || '') !== 'client_credentials') return json({ error: 'unsupported_grant_type', error_description: 'client_credentials or urn:ietf:params:oauth:grant-type:jwt-bearer' }, { node: 'registry' }, 'no-store', 400);
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
export async function verify(request, env, typ) {
  const auth = request.headers.get('authorization') || ''; if (!auth.startsWith('Bearer ')) return { ok: false, error: 'missing_token' };
  const parts = auth.slice(7).trim().split('.'); if (parts.length !== 3) return { ok: false, error: 'malformed_token' };
  try {
    const prv = JSON.parse(env.OAUTH_JWK); const { d, ...pub } = prv; const key = await crypto.subtle.importKey('jwk', pub, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['verify']);
    const ok = await crypto.subtle.verify({ name: 'ECDSA', hash: 'SHA-256' }, key, unb64u(parts[2]), new TextEncoder().encode(`${parts[0]}.${parts[1]}`)); if (!ok) return { ok: false, error: 'bad_signature' };
    const claims = JSON.parse(new TextDecoder().decode(unb64u(parts[1]))); const now = Math.floor(Date.now() / 1000);
    if (claims.iss !== ISSUER || claims.aud !== AUDIENCE) return { ok: false, error: 'wrong_issuer_or_audience' };
    if (!claims.exp || claims.exp < now) return { ok: false, error: 'expired' };
    if ((claims.typ || 'access') !== (typ || 'access')) return { ok: false, error: 'wrong_token_type' };
    if (claims.jti && await env.STATUS.get(`oauth:revoked:${claims.jti}`)) return { ok: false, error: 'revoked' };
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
// ---- auth.md agent registration (anonymous): the agent registers itself and receives an identity_assertion (a signed JWT, typ identity_assertion, 30 days)
// plus client credentials; the assertion exchanges for access tokens at /oauth/token (jwt-bearer). No claim ceremony is required: registrations are active on issue.
export async function identity(request, env) {
  let body; try { body = await request.json(); } catch (e) { return json({ error: 'invalid_request', error_description: 'JSON body required' }, { node: 'registry' }, 'no-store', 400); }
  const type = body.type || 'anonymous';
  if (type !== 'anonymous') return json({ error: 'unsupported_identity_type', error_description: 'anonymous only; identity_assertion (ID-JAG) and service_auth are not offered', identity_types_supported: ['anonymous'] }, { node: 'registry' }, 'no-store', 400);
  const reg = await register(new Request(request.url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ client_name: body.client_name || body.agent_name || 'anonymous agent', agent_card: body.agent_card || null, scope: body.scope || 'records:read events:read licensed:read', contacts: body.contacts || [], identity_type: 'anonymous' }) }), env);
  const rec = await reg.json(); if (!rec.client_id) return json(rec, { node: 'registry' }, 'no-store', 400);
  const now = Math.floor(Date.now() / 1000); const jti = rand(12);
  const assertion = await signJwt(env, { iss: ISSUER, sub: rec.client_id, aud: AUDIENCE, typ: 'identity_assertion', identity_type: 'anonymous', scope: rec.scope, iat: now, exp: now + 86400 * 30, jti });
  const claim_token = rand(24); try { await env.STATUS.put(`oauth:claim:${claim_token}`, JSON.stringify({ client_id: rec.client_id, iat: now }), { expirationTtl: 86400 * 30 }); } catch (e) { /* best effort */ }
  return json({ identity_type: 'anonymous', identity_assertion: assertion, assertion_expires: new Date((now + 86400 * 30) * 1000).toISOString(), claim_token, client_id: rec.client_id, client_secret: rec.client_secret, scopes: rec.scope.split(' '), token_endpoint: `${ISSUER}/oauth/token`, grant_types: ['urn:ietf:params:oauth:grant-type:jwt-bearer', 'client_credentials'], note: 'active on issue; no claim ceremony is required. POST the claim endpoint with claim_token and email to attach a contact to the registration.' }, { node: 'registry' }, 'no-store', 201);
}
export async function claim(request, env) {
  let body; try { body = await request.json(); } catch (e) { return json({ error: 'invalid_request', error_description: 'JSON body required' }, { node: 'registry' }, 'no-store', 400); }
  const c = body.claim_token ? await env.STATUS.get(`oauth:claim:${body.claim_token}`, 'json') : null;
  if (!c) return json({ error: 'invalid_grant', error_description: 'unknown claim_token' }, { node: 'registry' }, 'no-store', 400);
  const rec = await env.STATUS.get(`oauth:client:${c.client_id}`, 'json'); if (rec && body.email) { rec.contacts = Array.from(new Set([...(rec.contacts || []), String(body.email)])); rec.claimed_at = new Date().toISOString(); await env.STATUS.put(`oauth:client:${c.client_id}`, JSON.stringify(rec)); }
  return json({ claim_attempt: { status: 'complete', client_id: c.client_id, note: 'registrations are active on issue; the contact is attached to the registration. No sign-in ceremony is run.' } }, { node: 'registry' }, 'no-store');
}
export async function events(request, env) {
  const ct = request.headers.get('content-type') || ''; let raw = ''; try { raw = await request.text(); } catch (e) { /* empty */ }
  const jti = rand(12); try { await env.STATUS.put(`oauth:event:${jti}`, JSON.stringify({ at: new Date().toISOString(), content_type: ct, bytes: raw.length, head: raw.slice(0, 512) }), { expirationTtl: 86400 * 30 }); } catch (e) { /* best effort */ }
  return new Response(null, { status: 202, headers: headers({ node: 'registry' }, { 'cache-control': 'no-store' }) });
}
export async function revoke(request, env) {
  let form = {}; try { const fd = await request.formData(); for (const [k, v] of fd.entries()) form[k] = v; } catch (e) { /* empty */ }
  const parts = String(form.token || '').split('.'); if (parts.length === 3) { try { const claims = JSON.parse(new TextDecoder().decode(unb64u(parts[1]))); if (claims.jti) await env.STATUS.put(`oauth:revoked:${claims.jti}`, '1', { expirationTtl: Math.max(60, (claims.exp || 0) - Math.floor(Date.now() / 1000) + 60) }); } catch (e) { /* RFC 7009: always 200 */ } }
  return new Response(null, { status: 200, headers: headers({ node: 'registry' }, { 'cache-control': 'no-store' }) });
}
