// test_estate_local.mjs — USR-03: the estate source and the getresearch.ai Worker in Node (real network for the door checks, mock KV and page store).
//   getresearch.ai   the index (numbers from the store ledger and list_nodes, no typed count), a market list, an issuer page (the fence is the first line of
//                    the page text and of the Markdown twin; ten sections in order; licensed shows none loaded), .md and .json twins, machine kit, venues.json
//   the estate       the footer keeps three bands; the Research link is in the FOR HUMANS row; the nav is unchanged; a stub node page carries its Coverage line
//                    and its facts.json the venues block. FOR DESKS shows get_research only once the live router carries it (proved on the wire after release).
import { readFile } from 'node:fs/promises'; import fs from 'node:fs';
const RW = (await import('file:///C:/ALLOOLOO/CM-KG/ESTATE/worker/research.js')).default; const W = (await import('file:///C:/ALLOOLOO/CM-KG/ESTATE/worker/protocols.js')).default;
const PUB = 'C:/ALLOOLOO/CM-KG/ESTATE/public'; const kv = new Map(); const store = new Map(); const pages = fs.readFileSync('C:/ALLOOLOO/CM-KG/RESEARCH/pages/nl.jsonl', 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l));
for (const p of pages) store.set('p:' + p.cmr, p);
store.set('i:nl', { as_of: '2026-11-06', issuers: pages.map(p => { const [, ex, code] = p.cmr.split('/'); return [ex, code, p.numbers.identity.name.value, p.numbers.identity.ticker.value, p.numbers.identity.isin.value]; }) });
store.set('meta', { published_utc: '2026-11-11T00:00:00Z', markets: { nl: { pages: pages.length, as_of: '2026-11-06', coverage_found: 0, coverage_none_found: 0, coverage_not_read: pages.length, open_research_rows: 0 } } });
const env = { ASSETS: { fetch: async r => { const p = new URL(r.url).pathname; try { return new Response(await readFile(PUB + p)); } catch { return new Response('nf', { status: 404 }); } } }, STATUS: { get: async k => kv.get(k) ?? null, put: async (k, v) => { kv.set(k, v); }, list: async () => ({ keys: [] }) }, X402: { get: async () => null }, RESEARCH: { get: async k => store.get(k) ?? null } };
const waits = []; const get = async (w, u, acc = 'text/html') => { const r = await w.fetch(new Request(u, { headers: { accept: acc, 'user-agent': 'usr01-local reader' }, redirect: 'manual' }), env, { waitUntil: p => waits.push(p) }); return { status: r.status, body: await r.text(), h: r.headers }; };
const R = []; const ok = (n, c, d) => { R.push(!!c); console.log(`${c ? 'PASS' : 'FAIL'} ${n}${d ? ' · ' + d : ''}`); };
const FENCE = "The page is the record's research on the issuer — no analyst, no rating, no view."; const txt = b => b.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>|<svg[\s\S]*?<\/svg>/g, ' ').replace(/<[^>]+>/g, ' ').replace(/&#?\w+;/g, ' ').replace(/\s+/g, ' ');
const ix = await get(RW, 'https://getresearch.ai/'); ok('index 200', ix.status === 200 && ix.body.includes('get_research — the research page of a listed company'));
ok('index reads its numbers', new RegExp(`<div class="v">${pages.length}</div>`).test(ix.body) || ix.body.includes(`>${pages.length}<`), String(pages.length)); ok('index has the form above the footer', /<form id="contact"[\s\S]*<footer>/.test(ix.body));
const mk = await get(RW, 'https://getresearch.ai/nl'); ok('market list', mk.status === 200 && (mk.body.match(/href="\/nl\/XAMS\//g) || []).length === pages.length);
const p0 = pages.find(p => p.numbers.disclosure.filings > 0); const ip = await get(RW, 'https://getresearch.ai' + p0.path); const body = txt(ip.body.slice(ip.body.indexOf('</nav>')));
ok('issuer page 200', ip.status === 200, p0.path); ok('the fence is the first line of the page', body.replace(/^(\s|Connect an agent)+/, '').startsWith(FENCE), body.slice(0, 120));
const order = ['Identity and listing', 'The disclosure read', 'Auditor', 'Events and halts', 'Orderability', 'Coverage', 'Open research', 'Licensed', 'As-of depth', 'Sources']; const pos = order.map(t => ip.body.indexOf(`>${t}</h2>`));
ok('ten sections in order', pos.every((x, k) => x > 0 && (k === 0 || x > pos[k - 1])), pos.join(',')); ok('licensed shows none loaded', /Licensed research: none loaded\./.test(ip.body) && ip.body.includes('<td>none loaded</td>'));
const md = await get(RW, 'https://getresearch.ai' + p0.path + '.md'); ok('.md twin starts with the fence', md.body.startsWith(FENCE) && (md.h.get('content-type') || '').includes('markdown'));
const js = JSON.parse((await get(RW, 'https://getresearch.ai' + p0.path + '.json')).body); ok('.json twin is the page object', js.cmr === p0.cmr && js.numbers.licensed.rows.length === 0 && js.numbers_hash === p0.numbers_hash);
for (const f of ['/llms.txt', '/facts.json', '/venues.json', '/.well-known/agent-card.json', '/.well-known/mcp.json', '/.well-known/x402.json', '/.well-known/security.txt', '/robots.txt', '/sitemap.xml', '/sitemap-nl.xml', '/index.md']) { const r = await get(RW, 'https://getresearch.ai' + f); ok(`kit ${f}`, r.status === 200 && r.body.length > 60, String(r.body.length)); }
const fj = JSON.parse((await get(RW, 'https://getresearch.ai/facts.json')).body); ok('facts: pages from the ledger, venues, licensed empty', fj.research_pages === pages.length && fj.venues.count > 50 && fj.licensed.rows === 0 && fj.definition.includes(FENCE));
const ll = (await get(RW, 'https://getresearch.ai/llms.txt')).body; ok('llms first line is the mark; the fence in line 1', ll.startsWith('# get_research — ') && ll.split('\n')[1].includes(FENCE));
ok('www 301', (await get(RW, 'https://www.getresearch.ai/nl')).status === 301); ok('unknown page 404', (await get(RW, 'https://getresearch.ai/nl/XAMS/NOPE')).status === 404);
await get(W, 'https://getissuer.ai/'); await Promise.all(waits); const NAV = 'Issuer|Orderability|Target Market|As Of|Issuerwire';
for (const h of ['allooloo.io', 'getissuer.ai', 'getfilings.ai', 'ca-cm-kg.ai', 'tw-cm-kg.ai']) {
  const p = await get(W, `https://${h}/`); const f = (/<footer>([\s\S]*)<\/footer>/.exec(p.body) || [, ''])[1]; const bands = [...f.matchAll(/<span class="kicker">([A-Z ]+)<\/span>/g)].map(m => m[1]).join('|');
  const nav = [...((/<nav aria-label="Estate"><ul>([\s\S]*?)<\/ul>/.exec(p.body) || [, ''])[1]).matchAll(/<a [^>]*>([^<]+)<\/a>/g)].map(m => m[1]).join('|');
  ok(`${h} footer bands, Research link, nav`, p.status === 200 && bands === 'FOR AGENTS|FOR DESKS|FOR HUMANS' && f.includes('<a href="https://getresearch.ai/">Research</a>') && (h === 'allooloo.io' || nav === NAV), `${bands} · ${nav}`);
}
const tw = await get(W, 'https://tw-cm-kg.ai/'); ok('stub node page carries Coverage', /Coverage: Taiwan Stock Exchange/.test(tw.body) && tw.body.includes('<h2>Venues</h2>'));
const twf = JSON.parse((await get(W, 'https://tw-cm-kg.ai/facts.json', 'application/json')).body); ok('stub node facts carry venues', twf.coverage && twf.venues && twf.venues.exchanges_on_record && twf.venues.regulator.value);
const caf = JSON.parse((await get(W, 'https://ca-cm-kg.ai/facts.json', 'application/json')).body); ok('curated node facts carry venues', caf.venues && caf.venues.exchanges_on_record.TSX > 0, JSON.stringify(caf.venues && caf.venues.exchanges_on_record));
console.log(R.every(Boolean) ? 'USR-03 ESTATE LOCAL PASS' : 'USR-03 ESTATE LOCAL FAIL'); process.exit(R.every(Boolean) ? 0 : 1);
