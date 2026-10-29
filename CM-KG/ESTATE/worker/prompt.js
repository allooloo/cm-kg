// prompt.js — PROMPT-01 (DAY ORDER 6, 2026-10-25): on every issuer page (<cc>-issuer.ai and <cc>.eu-issuer.ai) one copyable prompt block — the exact text an
// agent user pastes into Claude or ChatGPT to read this market through the apex door — and the Add-to buttons for the doors. Generated from the market's
// roster entry (list_nodes: country, node, door, example issuer, duty); nothing typed per page. No script (the issuer pages carry none): the block is a
// <pre> selected whole on one click (user-select: all). A market not on the roster, or a SEEKING PARTNER page, gets no block.
import { readRoster, ROSTER, ccOf, doorOf } from './roster.js';
const APEX = 'https://mcp.getissuer.ai/mcp';
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
export function marketPrompt(n) {
  const ex = n.example || {}; const id = ex.ticker || ex.isin;
  return [`Use the Capital Markets Knowledge Graph MCP server at ${APEX} (Allooloo; read-only, no sign-in).`,
    `1. Call list_nodes and read the ${n.country} node (${n.node}): is it live, its record and event counts, its as-of date, its regional door${n.duty ? ' and the duty it serves' : ''}.`,
    id ? `2. Call resolve_issuer with "${id}"${ex.name ? ` (${ex.name})` : ''}, then get_record for the match. Give me every field with its source URL and read date; leave blank what the record leaves blank.` : `2. Call resolve_issuer for the ${n.country} issuer I name, then get_record for the match. Give me every field with its source URL and read date.`,
    `3. Call get_signal for the same identifier and tell me the ACM-68000 signal (ACM-200 trading, ACM-403 halted, ACM-404 not on the register) and its receipt id.`,
    `Answer only from the tools; name the door that served each answer (${doorOf(n)}/mcp).`].join('\n');
}
const enc = o => encodeURIComponent(JSON.stringify(o));
const b64 = s => btoa(unescape(encodeURIComponent(s)));
export function addTo(name, url) {
  return [['Claude', 'https://claude.ai/settings/connectors', 'Settings → Connectors → Add custom connector → paste the door URL'],
    ['ChatGPT', 'https://chatgpt.com/#settings/Connectors', 'Settings → Connectors (developer mode) → Create → paste the door URL'],
    ['Cursor', `cursor://anysphere.cursor-deeplink/mcp/install?name=${encodeURIComponent(name)}&config=${encodeURIComponent(b64(JSON.stringify({ url })))}`, 'opens Cursor with the server filled in'],
    ['VS Code', `vscode:mcp/install?${enc({ name, type: 'http', url })}`, 'opens VS Code with the server filled in']];
}
export function promptBlock(title, text, doors) {
  const btns = doors.map(([label, name, url]) => `<p style="margin:.4em 0"><strong>${esc(label)}</strong> <code>${esc(url)}</code><br>${addTo(name, url).map(([who, href, how]) => `<a href="${esc(href)}" rel="noopener" title="${esc(how)}" style="display:inline-block;margin:.2em .4em .2em 0;padding:.2em .7em;border:1px solid currentColor;border-radius:4px;text-decoration:none">Add to ${esc(who)}</a>`).join('')}</p>`).join('');
  return `<section id="ask" aria-labelledby="ask-h"><h2 id="ask-h">${esc(title)}</h2><p>Paste this into Claude or ChatGPT once the door is connected (one click selects it all):</p><pre style="white-space:pre-wrap;user-select:all;-webkit-user-select:all;padding:.8em;border:1px solid #ccc;border-radius:4px;background:rgba(0,0,0,.03)">${esc(text)}</pre>${btns}<p class="src" style="font-size:.85em">Generated from the roster of record (list_nodes at ${esc(APEX)}) at render — PROMPT-01.</p></section>`;
}
// the issuer-page hosts: <cc>-issuer.ai and <cc>.eu-issuer.ai (lu.eu-issuer.ai 301s to lu-issuer.ai and never reaches here)
export function issuerCc(host) { const h = host.replace(/^www\./, ''); const m = h.match(/^([a-z]{2})-issuer\.ai$/) || h.match(/^([a-z]{2})\.eu-issuer\.ai$/); return m ? m[1] : null; }
export async function withPrompt(host, path, r) {
  const cc = issuerCc(host); if (!cc || path !== '/' || r.status !== 200 || !(r.headers.get('content-type') || '').includes('text/html')) return r;
  if (!ROSTER.nodes.length) { try { await readRoster(); } catch (e) { return r; } }
  const n = ROSTER.nodes.find(x => ccOf(x) === cc && x.live); if (!n) return r;   // not on the roster (SEEKING PARTNER, NODE OPENING): no block
  const html = await r.text(); if (!html.includes('</main>')) return new Response(html, r);
  const block = promptBlock(`Ask an agent — ${n.country}`, marketPrompt(n), [['getissuer (apex door, every market)', 'getissuer', APEX], [`${n.country} node door`, n.node, `${doorOf(n)}/mcp`]]);
  const h = new Headers(r.headers); h.delete('content-length'); h.set('X-Allooloo-Prompt', 'PROMPT-01');
  return new Response(html.replace('</main>', block + '</main>'), { status: 200, headers: h });
}
