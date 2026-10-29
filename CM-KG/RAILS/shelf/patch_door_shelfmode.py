r"""SHELF-01 — the two new doors on the shared door image (cmkg-door 0.17.0): DOOR_MODE=bench (data-bench.ai) and DOOR_MODE=review (data-review.ai).
Market doors (DOOR_MODE unset) are unchanged. The shelf doors read the apex store (STORAGE_ACCOUNT=allooloocmkgapex): container 'shelf' (public sets:
bench questions, review JSON) and, for the bench door only, 'shelf-private' (the answers; never served). A market-year appears only when it is published,
which the rails do only when the ledger entry is complete and the manifest verifies.
  bench:  list_benches · get_bench(market, year) -> the questions · score_bench(market, year, answers[]) -> per-question pass/fail, score, signed scorecard
  review: list_reviews · get_review(market, year) -> the signed review JSON (the PDF goes by licence)"""
p = r'C:\ALLOOLOO\CM-KG\DOOR\container\index.js'
s = open(p, encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
rep("const ANN = { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true };",
"""const ANN = { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true };
// SHELF-01 (0.17.0): DOOR_MODE=bench | review runs this image as a shelf door on the apex store; unset = a market door, exactly as before
const DOOR_MODE = (process.env.DOOR_MODE || '').toLowerCase();
const SHELF_TOOLS = {
  bench: [
    { name: 'list_benches', title: 'List published benches', annotations: { title: 'List published benches', ...ANN }, description: 'Return the market-years with a published bench (questions public; answers held at this door).', inputSchema: { type: 'object', properties: {} } },
    { name: 'get_bench', title: 'Get a bench', annotations: { title: 'Get a bench', ...ANN }, description: 'Return the question set of one market-year bench: issuers, dated questions, the sealed manifest it was drawn from.', inputSchema: { type: 'object', properties: { market: { type: 'string' }, year: { type: 'integer' } }, required: ['market', 'year'] } },
    { name: 'score_bench', title: 'Score answers against a bench', annotations: { title: 'Score answers against a bench', readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true }, description: 'Score an agent\\'s answers to one market-year bench: per-question pass or fail, the score, a signed scorecard. The expected answers never leave this door.', inputSchema: { type: 'object', properties: { market: { type: 'string' }, year: { type: 'integer' }, agent: { type: 'string', description: 'Who answered (named on the scorecard).' }, answers: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, answer: {} }, required: ['id', 'answer'] } } }, required: ['market', 'year', 'answers'] } }],
  review: [
    { name: 'list_reviews', title: 'List published reviews', annotations: { title: 'List published reviews', ...ANN }, description: 'Return the market-years with a published review.', inputSchema: { type: 'object', properties: {} } },
    { name: 'get_review', title: 'Get a review', annotations: { title: 'Get a review', ...ANN }, description: 'Return one market-year disclosure review: counts by type, latency distribution, auditor concentration, listings and delistings, silent issuers — signed, from the sealed layer.', inputSchema: { type: 'object', properties: { market: { type: 'string' }, year: { type: 'integer' } }, required: ['market', 'year'] } }] };""")
rep("  if (method === 'tools/list') return rpcResult(id, { tools: TOOLS });",
    "  if (method === 'tools/list') return rpcResult(id, { tools: SHELF_TOOLS[DOOR_MODE] || TOOLS });")
rep("if (!TOOLS.find(t => t.name === name)) return rpcError(id, -32602, `Unknown tool: ${name}`);",
    "if (!(SHELF_TOOLS[DOOR_MODE] || TOOLS).find(t => t.name === name)) return rpcError(id, -32602, `Unknown tool: ${name}`);")
rep("async function callTool(name, args) {\n  args = args || {};",
"""async function shelfList(prefix) { const out = []; for await (const b of container.listBlobsFlat({ prefix })) { const m = b.name.match(/-([a-z]{2})-(\\d{4})\\.json$/); if (m) out.push({ market: m[1], year: Number(m[2]), published: b.properties.lastModified }); } return out; }
const normA = v => String(v).toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').replace(/ llp$| lp$/, '').trim();
async function shelfSign(o) {
  const j = process.env.CMR_SIGNING_JWK ? JSON.parse(process.env.CMR_SIGNING_JWK.replace(/^\\uFEFF/, '').trim()) : null; if (!j) return { ...o, signature: null, note_signature: 'signing key not configured on this door' };
  const { createPrivateKey, sign } = await import('node:crypto');
  const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
  const b64u = b => Buffer.from(b).toString('base64url'); const ph = b64u(JSON.stringify({ alg: 'EdDSA', kid: 'allooloo-cmr-2026-10' }));
  const key = createPrivateKey({ key: { kty: 'OKP', crv: 'Ed25519', x: j.x, d: j.d }, format: 'jwk' });
  const sig = sign(null, Buffer.from(ph + '.' + b64u(JSON.stringify(sortDeep(o)))), key);
  return { ...o, signature: { alg: 'EdDSA', kid: 'allooloo-cmr-2026-10', protected: ph, signature: b64u(sig), jwks: 'https://allooloo.ai/.well-known/jwks.json', over: "base64url(protected) + '.' + base64url(canonical JSON without signature: keys sorted, compact)" } };
}
async function shelfTool(name, args) {
  const mk = String(args.market || '').toLowerCase(), yr = parseInt(args.year, 10);
  if (name === 'list_benches') return { door: 'data-bench.ai', benches: await shelfList('bench/') };
  if (name === 'list_reviews') return { door: 'data-review.ai', reviews: await shelfList('review/') };
  if (name === 'get_bench') { const b = await cached(`bench/bench-${mk}-${yr}.json`); return b || { error: 'not_published', market: mk, year: yr, note: 'a bench is published only when the market\\'s ledger entry is complete and the year\\'s manifest verifies' }; }
  if (name === 'get_review') { const r = await cached(`review/review-${mk}-${yr}.json`); return r || { error: 'not_published', market: mk, year: yr, note: 'a review is published only when the market\\'s ledger entry is complete and the year\\'s manifest verifies' }; }
  if (name === 'score_bench') {
    const priv = new BlobServiceClient(`https://${process.env.STORAGE_ACCOUNT}.blob.core.windows.net`, cred).getContainerClient('shelf-private');
    let key; try { key = JSON.parse((await priv.getBlobClient(`bench/answers-${mk}-${yr}.json`).downloadToBuffer()).toString('utf8')); } catch (e) { return { error: 'not_published', market: mk, year: yr }; }
    const want = new Map(key.answers.map(a => [a.id, a])); const per = [];
    for (const g of (args.answers || [])) {
      const a = want.get(g.id); if (!a) { per.push({ id: g.id, pass: false, why: 'unknown question' }); continue; }
      const exp = a.answer, got = g.answer;
      const ok = typeof exp === 'number' ? String(got).trim() === String(exp) : (/^\\d{4}-\\d{2}-\\d{2}$/.test(String(exp)) ? String(got).trim().slice(0, 10) === exp : normA(got) === normA(exp));
      per.push({ id: a.id, pass: !!ok });
    }
    const passed = per.filter(x => x.pass).length, n = want.size;
    return shelfSign({ scorecard: `bench-${mk}-${yr}`, agent: args.agent || null, manifest_root: key.manifest_root, questions: n, answered: (args.answers || []).length, passed, score: n ? Math.round(1000 * passed / n) / 10 : null, per_question: per, scored_utc: new Date().toISOString(), note: 'expected answers are held at this door and never returned' });
  }
  return { error: 'unknown_tool', name };
}
async function callTool(name, args) {
  args = args || {};
  if (SHELF_TOOLS[DOOR_MODE]) return shelfTool(name, args);""")
open(p, 'w', encoding='utf-8').write(s)
print('shelf modes patched')
