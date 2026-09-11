// AI ASK — the desk at ask.allooloo.io. Holds no data: reads only through the two live MCP doors.
// Order of answering: identifier -> field (deterministic) -> list (deterministic) -> prose (Claude with the door attached) -> facts.
const OPERATOR = 'Allooloo Technologies Corp.';
const STOP = new Set(['WHO', 'WHAT', 'WHICH', 'WHERE', 'WHEN', 'HOW', 'IS', 'ARE', 'THE', 'A', 'AN', 'OF', 'FOR', 'IN', 'ON', 'AT', 'TO', 'AND', 'OR', 'DOES', 'DO', 'DID', 'ITS', 'IT', 'THIS', 'THAT', 'BY', 'WITH', 'FROM', 'AS', 'BE', 'HAS', 'HAVE', 'ANY', 'ALL', 'LAST', 'SINCE', 'ISIN', 'LEI', 'TSX', 'TSXV', 'CSE', 'CBOE', 'NEO', 'AGM', 'CEO', 'CFO', 'IPO', 'ETF', 'MCP', 'AI', 'ASK', 'CMR', 'KYP', 'SEDAR', 'SEDI', 'HQ', 'US', 'UK', 'CA', 'NCIB', 'REIT', 'ME', 'MY', 'SHOW', 'LIST', 'GIVE', 'TELL', 'PLEASE', 'ABOUT', 'DUAL', 'RUNS', 'RUN', 'YES', 'NO', 'NOT', 'NEW', 'OLD', 'ONE', 'TWO', 'ALSO', 'THEIR', 'THEY', 'HE', 'SHE', 'WE', 'YOU', 'I', 'IF', 'SO', 'UP', 'OUT', 'AM', 'PM', 'Q1', 'Q2', 'Q3', 'Q4', 'FY', 'YTD', 'M', 'Y', 'D', 'W']);
const FIELDS = [
  ['transfer_agent', /transfer agent|registrar/i, 'Transfer agent'], ['auditor', /auditor|audit firm|accountant/i, 'Auditor'], ['isin', /\bisin\b/i, 'ISIN'], ['lei', /\blei\b|legal entity identifier/i, 'LEI'],
  ['newswire', /newswire|news wire|wire of habit|press release service|which wire/i, 'Newswire of habit'], ['jurisdiction', /incorporat|jurisdiction|domicil|where is it (based|registered)/i, 'Incorporation jurisdiction'],
  ['sector', /\bsector\b|industry/i, 'Sector'], ['hq_city', /head ?office|headquarter|\bhq\b|based in|where is .* located|city/i, 'Head office'], ['tier', /\btier\b/i, 'Listing tier'],
  ['sedar_profile', /sedar/i, 'SEDAR+ profile'], ['sedi_link', /\bsedi\b|insider (report|filing)/i, 'SEDI'], ['security_type', /security type|what kind of (security|listing)|is it (a|an) (etf|fund|corporate)/i, 'Security type'],
  ['exchange', /which exchange|what exchange|listed on|where (is|does) it trade/i, 'Exchange'], ['name', /legal name|full name|what is the name/i, 'Legal name'], ['ticker', /\bticker\b|symbol/i, 'Ticker'],
];
const LISTS = [
  ['halt_resume', /halt|resum|cease trade/i, 'Halts and resumes'], ['agm_record_date', /record date|agm|annual (general )?meeting|special meeting/i, 'AGM and record dates'],
  ['financial_statement', /financial statement|results|earnings|quarter|year[- ]end|statement date/i, 'Financial statement dates'], ['early_warning', /early warning/i, 'Early-warning releases'],
  ['corporate_action', /corporate action|dividend|consolidat|split|name change|symbol change|rights/i, 'Corporate actions'], ['exchange_bulletin', /bulletin|notice/i, 'Exchange bulletins'],
  ['newswire_release', /release|announce|news|press/i, 'Newswire releases'], ['*', /event|disclosure|filing|what happened|timeline|history|activity/i, 'All events'],
];
const MONTHS = { january: 1, february: 2, march: 3, april: 4, may: 5, june: 6, july: 7, august: 8, september: 9, october: 10, november: 11, december: 12, jan: 1, feb: 2, mar: 3, apr: 4, jun: 6, jul: 7, aug: 8, sep: 9, sept: 9, oct: 10, nov: 11, dec: 12 };
function cmrHeaders(node, asOf, version) {
  return { 'X-CMR-Node': node || 'desk', 'X-CMR-As-Of': asOf || '', 'X-CMR-Version': String(version || ''), 'X-CMR-Source': 'public-record', 'X-CMR-Operator': OPERATOR, 'Strict-Transport-Security': 'max-age=31536000',
    'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin', 'Access-Control-Allow-Origin': '*' };
}
function json(obj, status, meta, cache) { return new Response(JSON.stringify(obj), { status: status || 200, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': cache || 'no-store', ...cmrHeaders(meta && meta.node, meta && meta.as_of, meta && meta.version) } }); }
async function mcp(door, name, args) {
  const r = await fetch(door + '/mcp', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args || {} } }) });
  if (!r.ok) throw new Error(`door ${door} answered ${r.status}`);
  const j = await r.json(); if (j.error) throw new Error(j.error.message); return (j.result && j.result.structuredContent) || {};
}
function tokens(q) { return (q || '').replace(/[?,;!()"']/g, ' ').split(/\s+/).filter(Boolean); }
function findIdentifier(q, explicit) {
  const cands = [];
  if (explicit && explicit.trim()) cands.push(explicit.trim());
  for (const t of tokens(q)) {
    const u = t.toUpperCase();
    if (/^[A-Z]{2}[A-Z0-9]{9}\d$/.test(u) || /^[A-Z0-9]{18}\d{2}$/.test(u)) cands.push(u);
    else if (/^(TSX|TSXV|TSX-V|CSE|CNSX|NEO|CBOE|CVE|CNQ):[A-Z0-9.\-]+$/.test(u)) cands.push(u);
    else if (/^[A-Z]{1,6}(\.[A-Z]{1,2})?(\.[A-Z]{1,2})?$/.test(t) && t === u && !STOP.has(u) && t.length >= 2) cands.push(u);
  }
  return [...new Set(cands)];
}
function sinceFrom(q) {
  const s = q.toLowerCase();
  let m = s.match(/(20\d\d)-(\d\d)-(\d\d)/); if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  m = s.match(/since\s+([a-z]+)(?:\s+(20\d\d))?/); if (m && MONTHS[m[1]]) { const y = m[2] || String(new Date().getUTCFullYear()); const d = `${y}-${String(MONTHS[m[1]]).padStart(2, '0')}-01`; return d > new Date().toISOString().slice(0, 10) ? `${Number(y) - 1}-${String(MONTHS[m[1]]).padStart(2, '0')}-01` : d; }
  m = s.match(/last\s+(\d+)\s*(day|week|month)/); if (m) { const n = Number(m[1]) * (m[2] === 'day' ? 1 : m[2] === 'week' ? 7 : 30); return new Date(Date.now() - n * 86400000).toISOString().slice(0, 10); }
  m = s.match(/(\d+)\s*m\b/); if (m) return new Date(Date.now() - Number(m[1]) * 30 * 86400000).toISOString().slice(0, 10);
  if (/this year|ytd/.test(s)) return `${new Date().getUTCFullYear()}-01-01`;
  return null;
}
function stateSummary(rec) { const c = {}; for (const f of Object.values(rec.identity || {})) if (f && f.state) c[f.state] = (c[f.state] || 0) + 1; return Object.entries(c).map(([k, v]) => `${k} ${v}`).join(' · ') || 'no states'; }
function chips(rec) {
  const t = `${rec.identity.exchange.value}:${rec.identity.ticker.value}`; const out = [];
  for (const [k, , label] of FIELDS) if (rec.identity[k] && rec.identity[k].value !== null && !['ticker', 'name', 'exchange'].includes(k)) out.push({ label: `${rec.identity.ticker.value} · ${label.toLowerCase()}`, q: `${label} for ${t}` });
  out.push({ label: `${rec.identity.ticker.value} · halts 12m`, q: `halts in the last 12 months for ${t}` }, { label: `${rec.identity.ticker.value} · releases 12m`, q: `releases in the last 12 months for ${t}` }, { label: `${rec.identity.ticker.value} · record dates`, q: `record dates for ${t}` }, { label: `${rec.identity.ticker.value} · aliases`, q: `what names does ${t} release under` });
  return out.slice(0, 12);
}
function suggested(rec, door) {
  const s = []; const id = rec.identity;
  if (id.newswire && id.newswire.source_url) s.push({ href: id.newswire.source_url, label: 'newswire release', src: id.newswire.value });
  if (id.name && id.name.source_url) s.push({ href: id.name.source_url, label: 'exchange profile', src: id.exchange.value + ' list' });
  if (id.sedar_profile && id.sedar_profile.value) s.push({ href: id.sedar_profile.value, label: 'SEDAR+ profile', src: 'sedarplus.ca (unverified)' });
  s.push({ href: rec.events_url.replace('/events/', '/record/'), label: 'node record', src: 'mcp.ca-cm-kg.ai' });
  return s;
}
function shareUrl(host, ident, q) { const u = new URL('https://' + host + '/'); if (ident) u.searchParams.set('id', ident); if (q) u.searchParams.set('q', q); return u.toString(); }
async function ask(env, host, body) {
  const q = (body.q || '').trim().slice(0, 500); const explicit = (body.id || '').trim().slice(0, 60);
  const ql = q.toLowerCase();
  const out = { q, identifier: { input: explicit || null, candidates: [], kind: null, matches: [], picked: null }, record: null, answer: null, footer: null, also: [], suggested: [], share_url: shareUrl(host, explicit, q) };
  // 0. facts questions that need no identifier
  const cands = findIdentifier(q, explicit);
  if (!cands.length) {
    if (/what is (a |the )?(capital markets record|cmr)\b|what is this|what is ai ask|what is the desk/i.test(q)) {
      out.answer = { kind: 'facts', title: 'What a Capital Markets Record is', text: 'One record per listed company, keyed on ISIN, ticker and LEI. Versioned, sourced, never deleted. Every field names the registry it came from or the engine that read it and carries a state: sourced, filled, confirmed or conflict. Blank stays blank, with the reason. Public-record only: no prices, no quotes, no licensed market data. Spec: CMR v0 (cm-record.org, draft). Signature: absent until cm-record signing exists.', read_by: 'desk copy from the CMR v0 spec', cites: [] };
    } else if (/who runs|who operates|who is behind|operator|who owns/i.test(q)) {
      const f = await fetch(env.DOOR_CA + '/facts.json').then(r => r.json());
      out.answer = { kind: 'facts', title: 'Operator', text: `${f.operator}. Node ${f.node}, ${f.records} records as of ${f.as_of}, source ${f.source}. Vancouver, Canada.`, read_by: 'mcp.ca-cm-kg.ai /facts.json', cites: ['facts.json'] };
    } else if (/node|market|live|which countries|coverage|what can (you|i) ask/i.test(q)) {
      const n = await mcp(env.DOOR_GLOBAL, 'list_nodes', {});
      out.answer = { kind: 'facts', title: 'Market nodes', rows: n.nodes.map(x => ({ date: x.live ? 'live' : 'not live', title: `${x.node} — ${x.country}${x.live ? ` — ${x.records} records as of ${x.as_of}` : ''}`, url: x.live ? x.door : null })), read_by: 'mcp.capitalmarketsknowledgegraph.ai list_nodes', cites: ['list_nodes'] };
    } else {
      out.answer = { kind: 'clarify', title: 'Which issuer?', text: 'Give a ticker (SHOP, TSX:SHOP, SHOP.TO, AUMB.V, CSE:AWR), an ISIN, an LEI, or a name the issuer releases under. Without an identifier the desk can only say what it is and which nodes are live.', read_by: 'desk', cites: [] };
    }
    out.footer = { node: 'global', as_of: null, version: null, read_by: out.answer.read_by, state: 'no issuer record' }; return out;
  }
  // 1. identifier — resolve every candidate, never guess
  let matches = []; let kind = null;
  for (const c of cands) { const r = await mcp(env.DOOR_CA, 'resolve_issuer', { identifier: c }); if (r.matches && r.matches.length) { matches = r.matches; kind = r.matched_by || 'ticker'; out.identifier.candidates.push(c); out.identifier.input = out.identifier.input || c; break; } out.identifier.candidates.push(c); }
  out.identifier.kind = kind; out.identifier.matches = matches;
  if (!matches.length) { const g = await mcp(env.DOOR_GLOBAL, 'resolve_issuer', { identifier: cands[0] }); out.answer = { kind: 'clarify', title: 'Not on any live node', text: `${cands.join(', ')}: ${g.note || 'no record on the live nodes'}. Live today: ca-cm-kg (TSX, TSXV, CSE, Cboe Canada).`, read_by: 'mcp.capitalmarketsknowledgegraph.ai resolve_issuer', cites: ['resolve_issuer'] }; out.footer = { node: 'global', as_of: null, version: null, read_by: out.answer.read_by, state: 'no issuer record' }; return out; }
  if (matches.length > 1) { out.answer = { kind: 'pick', title: 'More than one listing matches', rows: matches.map(m => ({ date: m.exchange, title: `${m.name} — ${m.exchange}:${m.ticker}`, url: null, pick: `${m.exchange}:${m.ticker}` })), text: 'Pick one; the desk never guesses.', read_by: 'mcp.ca-cm-kg.ai resolve_issuer', cites: ['resolve_issuer'] }; out.footer = { node: 'ca-cm-kg', as_of: matches[0].as_of, version: matches[0].version, read_by: out.answer.read_by, state: 'ambiguous identifier' }; return out; }
  const picked = matches[0]; out.identifier.picked = picked.cmr;
  const rec = await mcp(env.DOOR_CA, 'get_record', { identifier: picked.cmr });
  out.record = rec; out.also = chips(rec); out.suggested = suggested(rec); out.share_url = shareUrl(host, `${picked.exchange}:${picked.ticker}`, q);
  const base = { node: rec.node, as_of: rec.as_of, version: rec.version };
  // 2. field question — deterministic
  const fq = FIELDS.find(([, re]) => re.test(ql));
  const lq = LISTS.find(([, re]) => re.test(ql));
  const aliasQ = /alias|also known|former name|trade name|names does|release under/i.test(ql);
  if (aliasQ) {
    const a = await mcp(env.DOOR_CA, 'list_aliases', { identifier: picked.cmr });
    out.answer = { kind: 'list', title: 'Sourced aliases', rows: (a.aliases || []).map(x => ({ date: '', title: x.value, url: x.source_url, read_by: x.read_by })), text: a.aliases && a.aliases.length ? null : 'No sourced alias on record.', read_by: 'mcp.ca-cm-kg.ai list_aliases', cites: ['list_aliases'] };
    out.footer = { ...base, read_by: 'list_aliases', state: stateSummary(rec) }; return out;
  }
  if (fq && !(lq && lq[0] !== 'newswire_release' && LISTS.indexOf(lq) < 6 && /halt|record date|agm|financial statement|early warning|corporate action|bulletin/i.test(ql))) {
    const [key, , label] = fq; const f = rec.identity[key];
    if (f && f.value !== null) {
      out.answer = { kind: 'field', title: label, value: String(f.value), source_url: f.source_url, read_by: f.read_by, state: f.state, second_source_url: f.second_source_url || null, second_read_by: f.second_read_by || null, note: f.note || null, cites: [key] };
      out.footer = { ...base, read_by: f.read_by || 'record', state: f.state || 'sourced' };
    } else {
      out.answer = { kind: 'field', title: label, value: null, reason: (f && f.reason) || 'no source read', read_by: null, state: null, cites: [key], text: `${label} is blank on the record. ${(f && f.reason) || ''}`.trim() };
      out.footer = { ...base, read_by: 'record (blank field)', state: 'blank' };
    }
    return out;
  }
  // 3. list question — deterministic
  if (lq) {
    const since = sinceFrom(q) || new Date(Date.now() - 365 * 86400000).toISOString().slice(0, 10);
    const ev = await mcp(env.DOOR_CA, 'list_events_since', { identifier: picked.cmr, since, limit: 200 });
    let rows = ev.events || []; if (lq[0] !== '*' && lq[0] !== 'newswire_release') rows = rows.filter(e => e.event_type === lq[0]);
    else if (lq[0] === 'newswire_release') rows = rows.filter(e => !['exchange_bulletin', 'halt_resume', 'corporate_action'].includes(e.event_type) || /release/.test(e.read_by));
    out.answer = { kind: 'list', title: `${lq[2]} since ${since}`, rows: rows.map(e => ({ date: e.date, title: e.title, url: e.url, type: e.event_type, read_by: e.read_by, state: e.state })), total: rows.length, text: rows.length ? null : `No ${lq[2].toLowerCase()} on the record since ${since}.`, read_by: 'mcp.ca-cm-kg.ai list_events_since', cites: ['list_events_since'] };
    out.footer = { ...base, read_by: 'list_events_since', state: rows.length ? `${rows.length} events · ${[...new Set(rows.map(r => r.state))].join('/')}` : 'no events' }; return out;
  }
  // 4. prose — Claude with the door attached; answers only from tool results
  const door = env.DOOR_CA;
  const sys = `You are AI ASK, the desk on the Capital Markets Knowledge Graph. The issuer in question is ${rec.identity.name.value} (${picked.cmr}). Answer ONLY from the results of the cm-kg tools (get_record, list_events_since, list_aliases, resolve_issuer, list_nodes). Cite the field or event you used, by field name or event date and title. Never add a fact the record does not hold; if the record does not hold it, say "not on the record". No prices, quotes or market data. Public-record only. Be brief and plain.`;
  const req = { model: env.CLAUDE_MODEL || 'claude-sonnet-5', max_tokens: 1200, system: sys, mcp_servers: [{ type: 'url', url: door + '/mcp', name: 'cm-kg' }], messages: [{ role: 'user', content: `Question about ${rec.identity.name.value} (${picked.cmr}): ${q}` }] };
  const r = await fetch('https://api.anthropic.com/v1/messages', { method: 'POST', headers: { 'x-api-key': env.CLAUDE_API_KEY, 'anthropic-version': '2023-06-01', 'anthropic-beta': 'mcp-client-2025-04-04', 'content-type': 'application/json' }, body: JSON.stringify(req) });
  if (!r.ok) { const t = await r.text(); out.answer = { kind: 'error', title: 'The reader did not answer', text: `Claude returned ${r.status}. The record is still shown at right.`, read_by: 'read by Claude · from the record', cites: [] }; out.footer = { ...base, read_by: 'read by Claude (failed)', state: stateSummary(rec) }; return out; }
  const j = await r.json(); let text = ''; const cites = [];
  for (const b of j.content || []) { if (b.type === 'text') text += b.text; if (b.type === 'mcp_tool_use') cites.push(`${b.name}(${JSON.stringify(b.input)})`); }
  out.answer = { kind: 'prose', title: 'Read by Claude · from the record', text: text.trim() || 'not on the record', cites, read_by: 'read by Claude · from the record', tool_calls: cites.length, usage: j.usage ? { input: j.usage.input_tokens, output: j.usage.output_tokens } : null };
  out.footer = { ...base, read_by: 'read by Claude · from the record', state: stateSummary(rec) }; return out;
}
function llms(host) {
  return `# AI ASK — the desk on the Capital Markets Knowledge Graph
Operator: Allooloo Technologies Corp. (Vancouver, Canada). Host: https://${host}/
What it is: a human front door onto the Capital Markets Knowledge Graph. A compliance officer or banker asks about a listed company; the desk parses the identifier, opens the node through the MCP door, and answers from the record — field, source, reader, state. It holds no data of its own: every answer is read through mcp.ca-cm-kg.ai (Canada node) and mcp.capitalmarketsknowledgegraph.ai (global door).
How it answers, in order: identifier first (ticker, ISIN, LEI, or a sourced alias); field questions deterministically from get_record; list questions from list_events_since; anything else read by Claude with the door attached, answering only from tool results. Every answer carries node, as_of, version, read-by and state, and a copy link.
Agents: do not use this desk; use the door directly. Canada node MCP: https://mcp.ca-cm-kg.ai/mcp — tools resolve_issuer, get_record, list_events_since, list_aliases, list_nodes. Facts: https://mcp.ca-cm-kg.ai/facts.json. Global door: https://mcp.capitalmarketsknowledgegraph.ai/mcp
Rules: public-record only; no prices, quotes or licensed market data; blank stays blank with its reason; no guessed identifiers or aliases; no signature until cm-record signing exists.
Machine paths on this host: /llms.txt, /facts.json, /robots.txt. Share links: /?id=<identifier>&q=<question> (re-answered on open; nothing is stored).
`;
}
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url); const host = url.hostname; const p = url.pathname.replace(/\/+$/, '') || '/';
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cmrHeaders('desk', '', '') });
    if (env.RL) { try { const { success } = await env.RL.limit({ key: request.headers.get('cf-connecting-ip') || 'anon' }); if (!success) return json({ error: 'rate_limited' }, 429); } catch (e) {} }
    if (p === '/api/ask' && request.method === 'POST') {
      let body; try { body = await request.json(); } catch (e) { return json({ error: 'bad_json' }, 400); }
      try { const out = await ask(env, host, body); return json(out, 200, out.footer ? { node: out.footer.node, as_of: out.footer.as_of, version: out.footer.version } : null); }
      catch (e) { return json({ error: 'door_error', message: String(e.message || e).slice(0, 200) }, 502); }
    }
    if (p === '/llms.txt') return new Response(llms(host), { headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=3600', ...cmrHeaders('desk', '', '') } });
    if (p === '/facts.json') {
      const f = await fetch(env.DOOR_CA + '/facts.json').then(r => r.json()).catch(() => ({}));
      return json({ desk: 'AI ASK', host, operator: OPERATOR, reads_through: [env.DOOR_CA, env.DOOR_GLOBAL], holds_data: false, answer_order: ['identifier', 'field (deterministic)', 'list (deterministic)', 'prose (Claude with the door attached)'], node: f.node, as_of: f.as_of, version: f.version, records: f.records, events: f.events, live_nodes: f.live_nodes || ['ca-cm-kg'] }, 200, { node: f.node, as_of: f.as_of, version: f.version }, 'public, max-age=300');
    }
    if (p === '/robots.txt') return new Response('User-agent: *\nAllow: /\nUser-agent: GPTBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\nSitemap: https://' + host + '/sitemap.xml\n', { headers: { 'content-type': 'text/plain', ...cmrHeaders('desk', '', '') } });
    if (p === '/sitemap.xml') return new Response(`<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://${host}/</loc></url><url><loc>https://${host}/llms.txt</loc></url><url><loc>https://${host}/facts.json</loc></url></urlset>`, { headers: { 'content-type': 'application/xml', ...cmrHeaders('desk', '', '') } });
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method Not Allowed', { status: 405, headers: cmrHeaders('desk', '', '') });
    // static assets (the desk page, styles, script, fonts, favicons) with CMR headers on every response
    const a = await env.ASSETS.fetch(request);
    const h = new Headers(a.headers); for (const [k, v] of Object.entries(cmrHeaders('desk', '', ''))) h.set(k, v);
    return new Response(a.body, { status: a.status, headers: h });
  }
};
