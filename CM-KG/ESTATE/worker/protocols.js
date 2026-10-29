// protocols.js — PROTOCOLS-A-01 (DAY ORDER 3, CEO 2026-10-24): the entry of estate-pages wraps surfaces.js (unchanged). On every surface it serves, the
// machine files say where an agent goes: the A2A card names the resolver (getissuer, https://mcp.getissuer.ai/mcp) as an interface and a skill; mcp.json
// (/.well-known/mcp.json, /mcp.json, /.well-known/mcp/server-card.json) carries the x402 payment door, the routing block and the receipt door; llms.txt
// carries the routing block as its first lines under the title. Bodies are otherwise untouched; non-JSON or non-200 answers pass as they are.
import inner from './surfaces.js';
import { paymentDoor } from './x402gate.js';
import { classify5, handle5 } from './do5.js';
import { withPrompt } from './prompt.js';   // PROMPT-01 (DAY ORDER 6, 2026-10-25)   // DAY ORDER 5 (2026-10-24): the 28 zones of the day + the European subdomains, before surfaces.js
const RESOLVER = 'https://mcp.getissuer.ai/mcp';
const ROUTING = [{ resolves: 'gtin', what: 'GTINs', door: 'https://gtinfetch.ai/mcp' }, { resolves: 'issuer', what: 'Listed issuers (ticker, ISIN, LEI)', door: RESOLVER }, { resolves: 'receipt', what: 'Receipts — the Record of Cleared Orders', door: 'https://mcp.rco-a2a.ai/mcp' }];
const RECEIPTS = { door: 'https://mcp.rco-a2a.ai/mcp', keyring: 'https://allooloo.ai/.well-known/jwks.json', note: 'every resolve_issuer and get_signal on the Allooloo doors leaves an RCO receipt; the answer carries its decision_id' };
const MCP_PATHS = ['/.well-known/mcp.json', '/mcp.json', '/.well-known/mcp/server-card.json'];
async function rewrite(request, env, r) {
  const p = new URL(request.url).pathname;
  if (r.status !== 200 || !(p === '/llms.txt' || p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json' || MCP_PATHS.includes(p))) return r;
  const ct = r.headers.get('content-type') || ''; const h = new Headers(r.headers); h.delete('content-length'); h.set('X-Allooloo-Protocols', '2026-10-24.1');
  if (p === '/llms.txt') {
    let t = await r.text(); if (t.includes('Doors by what they resolve:')) return new Response(t, { status: 200, headers: h });
    const block = 'Doors by what they resolve:\n' + ROUTING.map(x => `- ${x.what} → ${x.door}`).join('\n') + '\n';
    const i = t.indexOf('\n'); t = t.startsWith('# ') && i > 0 ? t.slice(0, i + 1) + '\n' + block + t.slice(i + 1) : block + '\n' + t;
    return new Response(t, { status: 200, headers: h });
  }
  if (!ct.includes('json')) return r;
  let j; try { j = await r.json(); } catch (e) { return r; }
  if (p.includes('agent')) {
    const ifs = j.supportedInterfaces || [];
    if (!JSON.stringify(ifs).includes('mcp.getissuer.ai')) j.supportedInterfaces = [{ url: RESOLVER, transport: 'JSONRPC', protocolBinding: 'JSONRPC', description: 'getissuer — the listed-issuer resolver (start here)' }, ...ifs];
    const sk = j.skills || []; if (!sk.some(s => s && s.id === 'route-issuer')) j.skills = [{ id: 'route-issuer', name: 'Route: listed issuers → getissuer', description: `Listed issuers (ticker, ISIN, LEI) resolve at ${RESOLVER}: resolve_issuer and get_signal (ACM-68000).`, tags: ['routing', 'resolver', 'mcp'] }, ...sk];
    j.resolver = RESOLVER; j.routing = ROUTING; j.payment = paymentDoor(env);
  } else { j.payment = paymentDoor(env); j.routing = ROUTING; j.receipts = RECEIPTS; j.resolver = RESOLVER; }
  return new Response(JSON.stringify(j, null, 1), { status: 200, headers: h });
}
export default {
  scheduled: inner.scheduled,
  async fetch(request, env, ctx) {
    // HEALTH-01 (DAY ORDER 6, 2026-10-25): a2a-health.ai renders allooloo.io/status — the same handler, the same KV data, no copy. / and /status answer the
    // status page, /status.json its machine twin; each answer names allooloo.io/status as canonical. Every other path 301s to the same path on allooloo.io.
    const u0 = new URL(request.url); const h0 = u0.hostname.replace(/^www\./, '');
    if (h0 === 'a2a-health.ai') {
      const path = u0.pathname === '/' ? '/status' : u0.pathname;
      if (!['/status', '/status.json'].includes(path)) return Response.redirect('https://allooloo.io' + u0.pathname + u0.search, 301);
      const inner_r = await inner.fetch(new Request('https://allooloo.io' + path + u0.search, request), env, ctx);
      const hh = new Headers(inner_r.headers); hh.set('Link', '<https://allooloo.io' + path + '>; rel="canonical"'); hh.set('X-Health-Of', 'https://allooloo.io' + path);
      let body = await inner_r.text(); if (path === '/status') body = body.replace('<head>', '<head><link rel="canonical" href="https://allooloo.io/status">');
      hh.delete('content-length'); return new Response(body, { status: inner_r.status, headers: hh });
    }
    const c5 = classify5(new URL(request.url).hostname); if (c5) return c5.cc === 'sa' ? handle5(request, env, c5) : withPrompt(u0.hostname, u0.pathname, await rewrite(request, env, await handle5(request, env, c5)));   /* SEEKING PARTNER hosts carry that only: no routing or payment overlay (CEO ruling 2026-10-24) */ return withPrompt(u0.hostname, u0.pathname, await rewrite(request, env, await inner.fetch(request, env, ctx))); }   // PROMPT-01: the prompt block on the issuer pages
};
