// paygo.js — TMKT-02 (PAYGO-01 + LICENCE-01, CEO 2026-11-01): the two ways Allooloo is paid — data-paygo.ai (agents pay per read) and data-licence.ai (firms license
// the record). Text only on the standard page frame; the eyebrow of the copy; reached from the footer row of every Allooloo surface (Pay as you go · Licence), never
// from the top-level nav, no Data-tab entry, no product-bar entry. Page text is the copy of record, verbatim: START_ME_UP\Allooloo_data-paygo_data-licence_Page-
// Copy-of-Record_v1.1_2026-11-01.docx §A and §B, generated into paygo-copy.js (CM-KG\DOOR\gettargetmarket\gen_paygo_copy.py). No price, no tier, no count.
// Zones: data-paygo.ai the page; data-paygo.org/.io/.com twins (the same body, served as data-paygo.ai); datapaygo.ai/.org/.io/.com 301 to data-paygo.ai, path kept;
// data-licence.ai the page; data-licence.org/.io/.com twins. www answers on each. The one form: data-licence.ai's Contact (Formspree, the allooloo.io endpoint).
import { OPERATOR, CORPORATE, CONTACT, SURFACES_VERSION, FORM, esc, num, table } from './chrome.js';
import C from './paygo-copy.js';
export const PAYGO = 'https://data-paygo.ai', LICENCE = 'https://data-licence.ai';
const TWINS = { paygo: ['data-paygo.org', 'data-paygo.io', 'data-paygo.com'], licence: ['data-licence.org', 'data-licence.io', 'data-licence.com'] };
const FORWARDS = { paygo: ['datapaygo.ai', 'datapaygo.org', 'datapaygo.io', 'datapaygo.com'], licence: [] };
const KIT = ['/llms.txt', '/facts.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt', '/mcp.json'];
export const TITLES = { paygo: 'Pay as you go — how AI agents pay Allooloo, per read, in the call that reads', licence: 'Licence — the Allooloo record under licence, for the firm' };
export function classifyP(h) {
  if (/^data-paygo\.(ai|org|io|com)$/.test(h)) return { kind: 'paygo' };
  if (/^data-licence\.(ai|org|io|com)$/.test(h)) return { kind: 'licence' };
  if (/^datapaygo\.(ai|org|io|com)$/.test(h)) return { kind: 'redirect', canonical: PAYGO, status: 301 };
  return null;
}
// every twin and every www answers with the page's own body: the request is served as the .ai host (no 301)
export const serveAs = h => /^(www\.)?data-paygo\.(ai|org|io|com)$/.test(h || '') ? 'data-paygo.ai' : /^(www\.)?data-licence\.(ai|org|io|com)$/.test(h || '') ? 'data-licence.ai' : null;
// links: only the addresses the copy names, and (§B.2, the CC note) each named thing to its zone; the shelf names to the shelf zones
const ZONES = { 'Data Now': 'https://data-now.ai/', 'Data Vintage': 'https://data-vintage.ai/', 'Data Ark': 'https://data-ark.ai/', Replay: 'https://data-replay.ai/', Bench: 'https://data-bench.ai/', Cleanroom: 'https://data-cleanroom.ai/', Review: 'https://data-review.ai/', Score: 'https://data-score.ai/', Timeline: 'https://data-timeline.ai/' };
const DOORS = { 'getissuer.ai': 'https://getissuer.ai/', 'getorderability.ai': 'https://getorderability.ai/', 'gettargetmarket.ai': 'https://gettargetmarket.ai/', 'issuerwire.ai': 'https://issuerwire.ai/', 'rco-records.ai': 'https://rco-records.ai/', 'rco-a2a.ai': 'https://rco-a2a.ai/', 'data-licence.ai': 'https://data-licence.ai/', 'agentic-x402.ai': 'https://agentic-x402.ai/', 'allooloo.io/setup': 'https://allooloo.io/setup' };
const linkify = s => {
  let t = esc(s);
  for (const [n, u] of Object.entries(DOORS)) t = t.replace(new RegExp('(^|[\\s(])' + n.replace(/[.\/]/g, m => '\\' + m) + '(?=[\\s.,;—)]|$)', 'g'), `$1<a href="${u}">${n}</a>`);
  return t.replace(/mcp\.&lt;market&gt;-cm-kg\.ai\/mcp/g, '<code>mcp.&lt;market&gt;-cm-kg.ai/mcp</code>').replace(/x402-pay: 1/g, '<code>x402-pay: 1</code>');
};
const named = s => esc(s).replace(/^(Replay · Bench · Cleanroom · Review · Score · Timeline)/, m => m.split(' · ').map(n => `<a href="${ZONES[n]}">${n}</a>`).join(' · '));
const cell = s => ZONES[s] ? `<a href="${ZONES[s]}">${esc(s)}</a>` : esc(s);
const h2 = (id, t) => `<h2 id="${id}">${esc(t)}</h2>`;
// the one form on data-licence.ai (§B.5, copy of record v1.2): name, firm, role, email, message — the Formspree endpoint of record (allooloo.io); nothing else on the page is a form
const licenceForm = host => `<form id="contact" action="${FORM}" method="POST" accept-charset="UTF-8" toolname="contact_licence" tooldescription="Send a message to Allooloo Technologies Corp. about a licence, through the contact form of record on ${esc(host)}"><input type="hidden" name="site" value="${esc(host)}"><input type="hidden" name="_subject" value="${esc(host)} licence contact"><input type="hidden" name="_next" value="${LICENCE}/"><input type="text" name="_gotcha" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
<label for="f-name">name</label><input id="f-name" type="text" name="name" required autocomplete="name"><label for="f-firm">firm</label><input id="f-firm" type="text" name="firm" required autocomplete="organization"><label for="f-role">role</label><input id="f-role" type="text" name="role" required autocomplete="organization-title"><label for="f-email">email</label><input id="f-email" type="email" name="email" required autocomplete="email"><label for="f-message">message</label><textarea id="f-message" name="message" rows="5" required></textarea><button type="submit">send</button></form>`;
function sections(k, host) {
  return C[k].sections.map(s => {
    const id = s.head.split(' ').slice(1).join('-').toLowerCase().replace(/[^a-z0-9-]/g, '');
    const lis = s.blocks.filter(b => b[0] === 'li').map(b => linkify(b[1]));
    const rest = s.blocks.map(b => b[0] === 'table' ? `<div class="wrap">${table(b[1].head.map(esc), b[1].rows.map(r => r.map((c, i) => i === 0 ? cell(c) : esc(c))))}</div>` : b[0] === 'p' ? `<p>${k === 'licence' && s.n === 2 ? named(b[1]) : linkify(b[1])}</p>` : '').join('');
    return h2(id, s.head) + (lis.length ? num(s.n, lis) : '') + rest + (k === 'licence' && s.n === 5 ? licenceForm(host) : '');
  }).join('\n');
}
export function body(k, host) {
  return `<p class="lead">${linkify(C[k].lead)}</p>\n${sections(k, host)}
${h2('kit', 'Machine kit')}<p>${KIT.map(x => `<a href="${x}"><code>${x}</code></a>`).join(' · ')}</p><p class="muted">Twins (same body, no 301): ${esc(TWINS[k].join(', '))}.${FORWARDS[k].length ? ` Forwards here (301, path kept): ${esc(FORWARDS[k].join(', '))}.` : ''}</p>`;
}
export const eyebrow = k => C[k].eyebrow;
export const h1 = k => C[k].h1;
export const desc = k => C[k].lead;
const canon = k => k === 'paygo' ? PAYGO : LICENCE;
export function facts(k, host) {
  return { domain: host, kind: k === 'paygo' ? 'the pay-as-you-go page' : 'the licence page', head: C[k].h1.replace(/\.$/, ''), operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, surface_version: SURFACES_VERSION, source: 'the copy of record (' + C.source + ')',
    canonical: canon(k) + '/', twins: TWINS[k], forwards_here: FORWARDS[k], reached_from: 'the footer row of every Allooloo surface (Pay as you go · Licence); not in the top-level nav, the Data tab or the product bar',
    ...(k === 'paygo' ? { mechanism: { offer: 'HTTP 402 with a signed offer when the agent asks (header x402-pay: 1)', rails: ['x402 USDC', 'x402 USD'], receipt: 'https://mcp.rco-records.ai/mcp — the settlement reference beside answer_hash', standard: 'https://agentic-x402.ai/' }, prices: 'none on this page: the price is in the offer the door signs for the agent that asked' }
      : { licences: ['Data Now', 'Data Vintage', 'Data Ark'].map(n => ({ name: n, page: ZONES[n] })), named_things: ['Replay', 'Bench', 'Cleanroom', 'Review', 'Score', 'Timeline'].map(n => ({ name: n, page: ZONES[n] })), contact: 'the form on this page (Formspree, name · firm · role · email · message)', terms: 'none on this page: the licence terms live in the agreement' }),
    machine_paths: KIT };
}
export function llms(k, host) {
  const L = [`# ${host} — ${C[k].h1.replace(/\.$/, '')}`, `1. ${C[k].lead}`];
  C[k].sections.forEach(s => L.push(`${s.n + 1}. ${s.head.replace(/^\d+ /, '')}: ` + s.blocks.map(b => b[0] === 'table' ? b[1].rows.map(r => r.join(' — ')).join('; ') : b[1]).join(' ')));
  L.push(`${L.length}. Twins (same body): ${TWINS[k].join(', ')}.${FORWARDS[k].length ? ' Forwards here (301): ' + FORWARDS[k].join(', ') + '.' : ''} Operator: ${OPERATOR}. Surface version: ${SURFACES_VERSION}.`);
  return L.join('\n') + '\n';
}
// the descriptor: no door here — the page names where each door is and how a read is paid
export function descriptor(k) {
  return { name: k === 'paygo' ? 'data-paygo' : 'data-licence', kind: 'page (no MCP door on this host)', page: canon(k) + '/', payment: { page: 'https://data-paygo.ai/' },
    ...(k === 'paygo' ? { doors: ['https://mcp.getissuer.ai/mcp', 'https://mcp.getorderability.ai/mcp', 'https://mcp.gettargetmarket.ai/mcp', 'https://mcp.getasof.ai/mcp', 'https://mcp.getfilings.ai/mcp', 'https://mcp.getticker.ai/mcp', 'https://mcp.getauditor.ai/mcp', 'https://mcp.issuerwire.ai/mcp', 'https://mcp.rco-records.ai/mcp', 'https://mcp.<market>-cm-kg.ai/mcp'], ask_for_the_offer: 'header x402-pay: 1' } : { licence: 'https://data-licence.ai/', contact: 'https://data-licence.ai/#contact' }), operator: OPERATOR };
}
export const paths = () => ['/'].concat(KIT);
