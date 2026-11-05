// test_estate_local.mjs — ASOF-01: the estate source (protocols.js) in Node with mock bindings, no deploy. The nav of record on the shared template (As Of
// to the right of Target Market, before Issuerwire, on every surface in scope); getasof.ai: page, tiles read from the ledger, the definition line, no price,
// no typed count in the copy, the Markdown twin, llms.txt product order, card, descriptor, x402 file; www as the same body. Usage: node test_estate_local.mjs
import { readFile } from 'node:fs/promises';
const W = (await import('file:///C:/ALLOOLOO/CM-KG/ESTATE/worker/protocols.js')).default;
const PUB = 'C:/ALLOOLOO/CM-KG/ESTATE/public'; const kv = new Map(); const x402 = new Map([['tot:asof_receipts', '7']]);
const env = { ASSETS: { fetch: async r => { const p = new URL(r.url).pathname; try { return new Response(await readFile(PUB + p)); } catch { return new Response('nf', { status: 404 }); } } },
  STATUS: { get: async k => kv.get(k) ?? null, put: async (k, v) => { kv.set(k, v); }, list: async () => ({ keys: [] }) }, X402: { get: async k => x402.get(k) ?? null } };
const get = async (u, acc = 'text/html') => { const r = await W.fetch(new Request(u, { headers: { accept: acc, 'user-agent': 'asof01-local' }, redirect: 'manual' }), env, { waitUntil() {} }); return { status: r.status, body: await r.text(), h: r.headers }; };
const lab = f => [...f.matchAll(/<a href="([^"]+)"[^>]*>(.*?)<\/a>/g)].map(m => [m[2].replace(/<[^>]+>/g, ''), m[1]]);
const NAV = ['Issuer', 'Orderability', 'Target Market', 'As Of', 'Issuerwire'];
const R = []; const ok = (n, c, d) => { R.push(!!c); console.log(`${c ? 'PASS' : 'FAIL'} ${n}${d ? ' · ' + d : ''}`); };
for (const h of ['getissuer.ai', 'getorderability.ai', 'gettargetmarket.ai', 'getasof.ai', 'data-paygo.ai', 'data-vintage.ai', 'agentic-radar.ai', 'ca-cm-kg.ai', 'eu-issuer.ai', 'allooloo.io', 'about.allooloo.ai']) {
  const p = await get(`https://${h}/`); const nav = lab((/<nav aria-label="Estate"><ul>(.*?)<\/ul><\/nav>/s.exec(p.body) || [, ''])[1]);
  const asof = nav.find(x => x[0] === 'As Of'); const act = [...p.body.matchAll(/aria-current="page">([^<]+)</g)].map(m => m[1]);
  ok(`${h} nav`, p.status === 200 && nav.map(x => x[0]).join('|') === NAV.join('|') && asof && asof[1] === 'https://getasof.ai/', nav.map(x => x[0]).join(' · ') + ' · active ' + (act.join(',') || '-'));
}
const g = await get('https://getasof.ai/');
ok('getasof.ai active As Of', /aria-current="page">As Of</.test(g.body));
ok('getasof.ai hero line', g.body.includes('<h1>get_as_of — the issuer record, as of any date, with the receipt.</h1>') && g.body.includes('<title>get_as_of — the issuer record, as of any date, with the receipt.</title>'));
ok('getasof.ai definition line (THE LIBRARY)', g.body.includes('get_as_of is the issuer record as it stood on a date'));
ok('getasof.ai what-it-is-not block', g.body.includes('Not a price. Not a terminal. Not a news feed. Not a restated dataset.'));
ok('getasof.ai live tiles (ledger + counter)', /sealed years/.test(g.body) && /markets sealed/.test(g.body) && /receipts written/.test(g.body) && g.body.includes('>7<'), 'receipts tile reads the counter');
ok('getasof.ai no price on the page', !/\$\s?\d|USD\s?\d|0\.01/.test(g.body.replace(/<script[\s\S]*?<\/script>/g, '')));
ok('getasof.ai no typed "Five"', !/Five sealed years/.test(g.body));
ok('getasof.ai typed errors on the tool card', ['unknown_issuer', 'before_record', 'not_sealed', 'not_found'].every(e => g.body.includes(e)));
ok('getasof.ai closing card', g.body.includes('Point-in-time proof.'));
const md = await get('https://getasof.ai/index.md'); ok('Markdown twin /index.md', md.status === 200 && /markdown/.test(md.h.get('content-type') || '') && md.body.includes('as of any date'));
const neg = await get('https://getasof.ai/', 'text/markdown'); ok('Markdown twin by Accept', /markdown/.test(neg.h.get('content-type') || ''));
const ll = await get('https://getasof.ai/llms.txt'); ok('llms.txt product order', /Issuer https:\/\/getissuer\.ai\/ · Orderability [^·]+ · Target Market [^·]+ · As Of https:\/\/getasof\.ai\/ · Issuerwire/.test(ll.body)); ok('llms.txt price to be set', /price to be set/.test(ll.body));
const cd = JSON.parse((await get('https://getasof.ai/.well-known/agent-card.json', 'application/json')).body); ok('agent card', cd.name === 'getasof' && cd.url === 'https://mcp.getasof.ai/mcp' && cd['x-allooloo'].products[3].startsWith('As Of'));
const mj = JSON.parse((await get('https://getasof.ai/.well-known/mcp.json', 'application/json')).body); ok('descriptor', mj.url === 'https://mcp.getasof.ai/mcp' && mj.tools.includes('get_as_of'));
const xj = JSON.parse((await get('https://getasof.ai/.well-known/x402.json', 'application/json')).body); ok('x402 file', /price to be set/.test(JSON.stringify(xj)));
const fj = JSON.parse((await get('https://getasof.ai/facts.json', 'application/json')).body); ok('facts: ledger read', Array.isArray(fj.markets_sealed) && fj.receipts_written === 7, `markets ${fj.markets_sealed} · years ${fj.sealed_years}`);
const w = await get('https://www.getasof.ai/'); ok('www same body', w.status === 200 && w.body.replace(/www\./g, '') === g.body.replace(/www\./g, ''));
const pg = JSON.parse((await get('https://data-paygo.ai/mcp.json', 'application/json')).body); ok('paygo door list order', JSON.stringify(pg.doors || []).includes('"https://mcp.gettargetmarket.ai/mcp","https://mcp.getasof.ai/mcp","https://mcp.issuerwire.ai/mcp"'));
console.log(R.every(Boolean) ? 'ASOF-01 ESTATE LOCAL PASS' : 'ASOF-01 ESTATE LOCAL FAIL'); process.exit(R.every(Boolean) ? 0 : 1);
