// test_apex_local.mjs — USR-03: the apex router in Node. get_research on the router's own tool list and card; a call by ISIN resolved on the live node door
// (read only) and answered from a mock page store loaded from CM-KG\RESEARCH\pages; typed errors; the doors line carries the eighth door; the door hosts unchanged.
// No signing key and no receipt token here: the signature and the receipt are proved on the wire.
import { readFile } from 'node:fs/promises'; import fs from 'node:fs';
const A = (await import('file:///C:/ALLOOLOO/CM-KG/DOOR/apex/index.js')).default;
const ST = 'C:/ALLOOLOO/CM-KG/DOOR/apex/static'; const kv = new Map(); const pages = new Map();
for (const l of fs.readFileSync('C:/ALLOOLOO/CM-KG/RESEARCH/pages/nl.jsonl', 'utf8').split('\n')) if (l) { const p = JSON.parse(l); pages.set('p:' + p.cmr, p); }
const env = { ASSETS: { fetch: async r => { const p = new URL(r.url).pathname; try { return new Response(await readFile(ST + p)); } catch { return new Response('nf', { status: 404 }); } } }, X402: { get: async k => kv.get(k) ?? null, put: async (k, v) => kv.set(k, v), list: async () => ({ keys: [] }) },
  RESEARCH: { get: async (k, t) => pages.get(k) ?? null } };
const rpc = async (host, m) => (await A.fetch(new Request(`https://${host}/mcp`, { method: 'POST', headers: { 'content-type': 'application/json', 'user-agent': 'Allooloo digest (usr01-local)' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, ...m }) }), env, { waitUntil() {} })).json();
const get = async (host, p) => (await A.fetch(new Request(`https://${host}${p}`, { headers: { 'user-agent': 'usr01-local' } }), env, { waitUntil() {} })).text();
const R = []; const ok = (n, c, d) => { R.push(!!c); console.log(`${c ? 'PASS' : 'FAIL'} ${n}${d ? ' · ' + d : ''}`); };
const tl = await rpc('mcp.getissuer.ai', { method: 'tools/list' }); ok('getissuer tools carry get_research', tl.result.tools.some(x => x.name === 'get_research'), tl.result.tools.map(x => x.name).join(','));
const some = [...pages.values()].find(p => p.numbers.identity.isin.value && p.numbers.disclosure.filings > 0);
const c = (await rpc('mcp.getissuer.ai', { method: 'tools/call', params: { name: 'get_research', arguments: { isin: some.numbers.identity.isin.value } } })).result.structuredContent;
ok('get_research by ISIN', c.cmr === some.cmr && c.markdown.startsWith("The page is the record's research on the issuer") && c.as_of === some.as_of && c.sections.length === 10 && c.licensed.rows.length === 0, `${c.cmr || c.error} ${c.as_of || c.note}`);
ok('receipt block present (not written without the token)', c.receipt && (c.receipt.id || c.receipt.status === 'not written'), JSON.stringify(c.receipt).slice(0, 80));
const e1 = (await rpc('mcp.getissuer.ai', { method: 'tools/call', params: { name: 'get_research', arguments: { ticker: 'ZZZZNOPE9' } } })).result; ok('unknown_issuer', e1.structuredContent.error === 'unknown_issuer' && e1.isError === true);
const e2 = (await rpc('mcp.getissuer.ai', { method: 'tools/call', params: { name: 'get_research', arguments: {} } })).result; ok('invalid_request', e2.structuredContent.error === 'invalid_request');
const e3 = (await rpc('mcp.getissuer.ai', { method: 'tools/call', params: { name: 'get_research', arguments: { ticker: 'AAPL', exchange: 'NASDAQ' } } })).result; ok('no_page for an issuer whose page is not in the store', e3.structuredContent.error === 'no_page', e3.structuredContent.cmr);
const card = JSON.parse(await get('agent.getissuer.ai', '/.well-known/agent-card.json')); ok('card carries the eighth door', card.skills.some(s => s.id === 'get_research'));
const ll = await get('mcp.getissuer.ai', '/llms.txt'); ok('llms carries get_research and the doors line', ll.includes('get_research (Data Research') && ll.includes('get_auditor https://getauditor.ai/ · get_research https://getresearch.ai/'));
const mj = JSON.parse(await get('mcp.getissuer.ai', '/mcp.json')); ok('mcp.json lists get_research', JSON.stringify(mj.tools || mj).includes('get_research'));
const d = await rpc('mcp.getfilings.ai', { method: 'tools/list' }); ok('door hosts unchanged', d.result.tools.map(x => x.name).join(',') === 'get_filings,resolve_issuer,list_nodes');
const dc = JSON.parse(await get('agent.getfilings.ai', '/.well-known/agent-card.json')); ok('door card doors order ends with get_research', dc['x-allooloo'].doors.map(x => x.split(' ')[0]).join(',') === 'get_issuer,get_orderability,get_target_market,get_as_of,get_filings,get_ticker,get_auditor,get_research');
console.log(R.every(Boolean) ? 'USR-03 APEX LOCAL PASS' : 'USR-03 APEX LOCAL FAIL'); process.exit(R.every(Boolean) ? 0 : 1);
