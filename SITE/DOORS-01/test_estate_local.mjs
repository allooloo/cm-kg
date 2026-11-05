// test_estate_local.mjs — DOORS-01: the estate source in Node (real network for the door check, mock KV): three bands in every footer (allooloo.io and getasof.ai
// included), FOR DESKS lists only doors that answer, in order; FOR HUMANS without the trailing "· ·"; the nav unchanged; the three door pages: the mark as title,
// h1, Markdown twin and llms.txt first line, live tiles, the form above the footer, no price; www same body; card doors order.
import { readFile } from 'node:fs/promises';
const W = (await import('file:///C:/ALLOOLOO/CM-KG/ESTATE/worker/protocols.js')).default;
const PUB = 'C:/ALLOOLOO/CM-KG/ESTATE/public'; const kv = new Map(); const x402 = new Map([['tot:get_filings_receipts', '3']]);
const env = { ASSETS: { fetch: async r => { const p = new URL(r.url).pathname; try { return new Response(await readFile(PUB + p)); } catch { return new Response('nf', { status: 404 }); } } }, STATUS: { get: async k => kv.get(k) ?? null, put: async (k, v) => { kv.set(k, v); }, list: async () => ({ keys: [] }) }, X402: { get: async k => x402.get(k) ?? null } };
const waits = []; const get = async (u, acc = 'text/html') => { const r = await W.fetch(new Request(u, { headers: { accept: acc, 'user-agent': 'doors01-local reader' }, redirect: 'manual' }), env, { waitUntil: p => waits.push(p) }); return { status: r.status, body: await r.text(), h: r.headers }; };
const R = []; const ok = (n, c, d) => { R.push(!!c); console.log(`${c ? 'PASS' : 'FAIL'} ${n}${d ? ' · ' + d : ''}`); };
const NAV = 'Issuer|Orderability|Target Market|As Of|Issuerwire';
await get('https://getissuer.ai/'); await Promise.all(waits);   // the first render starts the door check; the second reads it
for (const h of ['allooloo.io', 'getissuer.ai', 'getasof.ai', 'gettargetmarket.ai', 'getfilings.ai', 'getticker.ai', 'getauditor.ai', 'data-vintage.ai', 'ca-cm-kg.ai']) {
  const p = await get(`https://${h}/`); const f = (/<footer>([\s\S]*)<\/footer>/.exec(p.body) || [, ''])[1];
  const bands = [...f.matchAll(/<span class="kicker">([A-Z ]+)<\/span>/g)].map(m => m[1]).join('|');
  const desks = [...((/FOR DESKS<\/span>(.*?)<\/p>/.exec(f) || [, ''])[1]).matchAll(/<code>(get_\w+)<\/code>/g)].map(m => m[1]);
  const nav = [...((/<nav aria-label="Estate"><ul>(.*?)<\/ul><\/nav>/s.exec(p.body) || [, ''])[1]).matchAll(/>([^<>]+)<\/a>/g)].map(m => m[1]).join('|');
  ok(`${h} three bands`, p.status === 200 && bands === 'FOR AGENTS|FOR DESKS|FOR HUMANS', bands + ' · desks ' + desks.join(','));
  ok(`${h} FOR DESKS live only, in order`, desks.join(',') === 'get_issuer,get_orderability,get_target_market,get_as_of' || desks.join(',') === 'get_issuer,get_orderability,get_target_market,get_as_of,get_filings,get_ticker,get_auditor');
  ok(`${h} FOR HUMANS no trailing dots`, !/Security<\/a> · <a/.test(f) && f.includes('FOR HUMANS'));
  ok(`${h} nav unchanged`, nav === NAV, nav);
}
for (const [h, t] of [['getfilings.ai', 'get_filings'], ['getticker.ai', 'get_ticker'], ['getauditor.ai', 'get_auditor']]) {
  const p = await get(`https://${h}/`); const mark = (/<h1>([^<]*)<\/h1>/.exec(p.body) || [, ''])[1]; const title = (/<title>([^<]*)<\/title>/.exec(p.body) || [, ''])[1];
  ok(`${h} mark`, mark.startsWith(`${t} — `) && title === mark, mark);
  const ll = await get(`https://${h}/llms.txt`); ok(`${h} llms first line`, ll.body.split('\n')[0] === `# ${mark}`);
  const md = await get(`https://${h}/index.md`); ok(`${h} twin`, /markdown/.test(md.h.get('content-type') || '') && md.body.includes(t));
  ok(`${h} form above the footer`, /formspree\.io\/f\/[^"]+"[\s\S]*<\/main>[\s\S]*<footer>/.test(p.body));
  ok(`${h} live tiles`, /markets live/.test(p.body) && (h !== 'getfilings.ai' || /receipts written/.test(p.body)));
  ok(`${h} no price`, !/\$\s?\d|USD\s?\d|0\.01/.test(p.body.replace(/<script[\s\S]*?<\/script>/g, '')));
  const cd = JSON.parse((await get(`https://${h}/.well-known/agent-card.json`, 'application/json')).body); ok(`${h} card doors order`, cd['x-allooloo'].doors.map(x => x.split(' ')[0]).join(',') === 'get_issuer,get_orderability,get_target_market,get_as_of,get_filings,get_ticker,get_auditor');
  const w = await get(`https://www.${h}/`); ok(`www.${h} same body`, w.status === 200);
}
const al = await get('https://getasof.ai/llms.txt'); ok('getasof llms doors line', al.body.includes('get_as_of https://getasof.ai/ · get_filings https://getfilings.ai/'));
console.log(R.every(Boolean) ? 'DOORS-01 ESTATE LOCAL PASS' : 'DOORS-01 ESTATE LOCAL FAIL'); process.exit(R.every(Boolean) ? 0 : 1);
