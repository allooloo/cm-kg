
// ---------- ORDER-032 C.4 — agent-swap.ai: which cloud serves each market's record now, its last swap, and when the record last reached the second cloud.
// Live at render: the serving cloud is the X-Allooloo-Origin header each node door returns; swaps and ark writes come from the published logs
// /swap/swaps.json (written by the swap rail) and /swap/ark.json (written at the sweep close). Sourced or blank: a door that does not answer reads "did not answer".
const SWAP_NODES = [['nl', 'Netherlands'], ['ch', 'Switzerland'], ['fr', 'France'], ['de', 'Germany'], ['sg', 'Singapore'], ['au', 'Australia'], ['uk', 'United Kingdom'], ['ca', 'Canada'], ['jp', 'Japan'], ['kr', 'South Korea'], ['us', 'United States']];
const CLOUD = { azure: 'Azure', aws: 'AWS' };
export const SWAP_COPY = {
  title: 'agent-swap — the record keeps answering',
  h1: 'agent-swap — the record keeps answering',
  desc: 'For each of eleven markets: the cloud serving the issuer record now, the last swap, and the last night the record reached its second cloud. Live at render.',
  lead: "Every market's issuer record is served from its own country and reaches a second cloud the same night. When the serving cloud stops answering, the same record answers from the other one: same address, same tools, same record."
};
async function assetJson(env, url, path) { try { const r = await env.ASSETS.fetch(new URL(path, url)); return r.ok ? await r.json() : null; } catch (e) { return null; } }
export async function swapData(env, url) {
  const [swaps, ark] = await Promise.all([assetJson(env, url, '/swap/swaps.json'), assetJson(env, url, '/swap/ark.json')]);
  const log = ((swaps && swaps.swaps) || []).slice().sort((a, b) => (a.at < b.at ? -1 : 1));
  const rows = await Promise.all(SWAP_NODES.map(async ([cc, country]) => {
    const node = `${cc}-cm-kg`; let origin = null, asOf = null;
    try {
      const ac = new AbortController(); const t = setTimeout(() => ac.abort(), 4000);
      const r = await fetch(`https://mcp.${node}.ai/facts.json`, { signal: ac.signal, cf: { cacheTtl: 0 } }); clearTimeout(t);
      if (r.ok) { origin = (r.headers.get('x-allooloo-origin') || '').toLowerCase() || null; asOf = r.headers.get('x-cmr-as-of') || null; }
    } catch (e) { }
    const sw = log.filter(x => x.node === node); const a = ((ark && ark.nodes) || {})[node] || null;
    return { node, country, serving: origin, as_of: asOf, swaps: sw.length, last_swap: sw.length ? sw[sw.length - 1] : null, last_ark_write: a ? a.last_write : null };
  }));
  return { at: new Date().toISOString(), rows, swap_log: log };
}
function swapBody(d, host) {
  const rows = d.rows.map(r => [`<code class="nw">${esc(r.node)}</code>`, esc(r.country), r.serving ? esc(CLOUD[r.serving] || r.serving) : 'did not answer', r.as_of ? esc(r.as_of) : '',
    r.last_swap ? `${esc(r.last_swap.at.slice(0, 10))} (to ${esc(CLOUD[r.last_swap.to] || r.last_swap.to)})` : 'none yet', r.swaps ? int(r.swaps) : 'none yet', r.last_ark_write ? esc(r.last_ark_write) : 'not yet']);
  const log = d.swap_log.length ? table(['When (UTC)', 'Market', 'From', 'To', 'Proof'], d.swap_log.slice().reverse().map(x => [esc(x.at.replace('T', ' ').slice(0, 16)), `<code class="nw">${esc(x.node)}</code>`, esc(CLOUD[x.from] || x.from), esc(CLOUD[x.to] || x.to), esc(x.proof || '')])) : '<p>No swap yet.</p>';
  return `<p class="lead">${esc(SWAP_COPY.lead)}</p>
<h2>1 Serving now</h2>${table(['Market', 'Country', 'Serving cloud', 'Record as of', 'Last swap', 'Swaps', 'Last copy to the second cloud'], rows)}
<p>Read at ${esc(d.at.replace('T', ' ').slice(0, 16))} UTC from each market's door.</p>
<h2>2 Swaps</h2>${log}
<h2>3 Machine kit</h2>${num(3, ['<a href="/llms.txt"><code>/llms.txt</code></a> · <a href="/facts.json"><code>/facts.json</code></a> · <a href="/.well-known/agent-card.json"><code>/.well-known/agent-card.json</code></a>', `Doors: <code>https://mcp.&lt;market&gt;-cm-kg.ai/mcp</code> · apex <code>${esc(APEX)}/mcp</code>`, `Operator: ${esc(OPERATOR)}`])}
${contactSection(host)}`;
}
function swapFacts(d, host) {
  return { domain: host, kind: 'record', product: 'agent-swap', what: SWAP_COPY.lead, operator: OPERATOR, corporate: CORPORATE, contact: CONTACT, as_of: d.at.slice(0, 10), read_at: d.at, surface_version: SURFACES_VERSION,
    nodes: d.rows.map(r => ({ node: r.node, country: r.country, serving: r.serving, record_as_of: r.as_of, swaps: r.swaps, last_swap: r.last_swap, last_ark_write: r.last_ark_write })), swaps: d.swap_log,
    machine_paths: ['/llms.txt', '/facts.json', '/.well-known/agent-card.json', '/.well-known/security.txt', '/sitemap.xml', '/robots.txt'], source: 'X-Allooloo-Origin header of each node door at render; /swap/swaps.json; /swap/ark.json' };
}
function swapLlms(d, host) {
  return [`# ${host} — agent-swap, the record keeps answering`, `1. ${SWAP_COPY.lead}`, `2. Read at ${d.at} from each market's door:`,
    ...d.rows.map(r => `   - ${r.node} (${r.country}): serving ${r.serving ? (CLOUD[r.serving] || r.serving) : 'did not answer'}; record as of ${r.as_of || 'not read'}; swaps ${r.swaps || 'none yet'}${r.last_swap ? `; last ${r.last_swap.at.slice(0, 10)} to ${r.last_swap.to}` : ''}; last copy to the second cloud ${r.last_ark_write || 'not yet'}`),
    `3. Doors: https://mcp.<market>-cm-kg.ai/mcp; apex ${APEX}/mcp. Operator: ${OPERATOR}. Contact: ${CONTACT}. agent-swap.com, .io, .org and .co.uk forward here.`,
    '4. Machine paths: /llms.txt /facts.json /.well-known/agent-card.json /.well-known/security.txt /sitemap.xml /robots.txt'].join('\n') + '\n';
}
// record-grade pages carry no script (Site Book): the shared footer's /webmcp.js and the light/dark toggle (which needs it) are taken out for this family
export function stripScripts(htmlText) { return htmlText.replace('<script src="/webmcp.js"></script>', '').replace(/<button class="tint"[\s\S]*?<\/button>/, ''); }
