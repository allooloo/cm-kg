// CM-KG apex router (ORDER-018 re-cut): mcp.capitalmarketsknowledgegraph.ai. Control plane global, data plane regional. This Worker holds only the
// index (ticker / ISIN / LEI / name / alias / CMR key -> node) as a static asset and the node list; list_nodes answers here; every record and
// event call is forwarded to the owning node's regional door (Azure Container App in the node's region). No record body is stored or cached
// at the apex. No fallback: if a node's regional door does not answer, the apex returns unavailable for that node — never a record from
// another store. The old shared Worker + D1 door (cm-kg-door) stays deployed beside this one and is listed for CEO deletion at end of scope.
// Agent Card at agent.capitalmarketsknowledgegraph.ai describes the router and lists the node agents.
import { decisionId, sha256, receiptLinks, writeReceipt } from './rco.js';
import { signRecord, sigRef } from './cmrsign.js';   // NODE-SIGN-01
let ENV = null;
import { decide, settle, paymentDoor, PRICING, relay } from './x402gate.js';
const INTERNAL = /^Allooloo (eco-pages|acm-signals|digest|rco-writer)/;   // Allooloo's own renderers: no receipt, no meter
const PAID_TOOLS = ['resolve_issuer', 'get_signal', 'get_record', 'list_events_since', 'list_aliases', 'get_eco'];
const ROUTING = [{ resolves: 'gtin', what: 'GTINs', door: 'https://gtinfetch.ai/mcp' }, { resolves: 'issuer', what: 'Listed issuers (ticker, ISIN, LEI)', door: 'https://mcp.getissuer.ai/mcp' }, { resolves: 'receipt', what: 'Receipts — the Record of Cleared Orders', door: 'https://mcp.rco-a2a.ai/mcp' }];
const RCO_JWKS = { keys: [{"kty": "OKP", "crv": "Ed25519", "x": "cqa-iPbl2AD_Yw3bIxQCPAmzSiBemxU6ajL2nI1w9QA", "kid": "allooloo-cmr-2026-10", "alg": "EdDSA", "use": "sig"}, {"kty": "OKP", "crv": "Ed25519", "x": "N-knqz1-H9xwNGvOS0Eu7CDrmdPgzFjCgvExLJt2lQw", "kid": "allooloo-rco-2026-10", "alg": "EdDSA", "use": "sig"}] };   // RCO-A-01: the receipt-signing key of record (public half)
const OPERATOR = 'Allooloo Technologies Corp.'; const SERVER_VERSION = '0.18.0';   // 0.18.0 = NODE-HALT-01 (2026-10-24): get_signal answers ACM-403 from the record's halt flag.   // 0.17.0 = NODE-SIGN-01 (2026-10-24): records and resolve summaries forwarded here are signed (kid allooloo-cmr-2026-10).   // 0.16.0 = PROTOCOLS-A-01 (2026-10-24): /eco/mcp and /signals/mcp.   // 0.15.0 = X402-A-01 (2026-10-24): x402 v2, free tier per agent per day, paid reads carry their receipt. 0.14.0 = RCO-A-01 (2026-10-24): receipts on resolve_issuer and get_signal. 0.13.0 = ACM-SIGNALS-01 (2026-10-24): get_signal, the ACM-68000 issuer state. ORDER-021 (Sept 16 2026): the human root renders each live node's link from nodes.json `door` (the field of record), not from a rebuilt hostname
const PROTOCOL = '2025-06-18';
const REGIONAL = {  // node -> regional door origin (Container Apps FQDN; direct to the origin, not through the node's Cloudflare hostname)
  'ca-cm-kg': 'https://cmkg-door-ca.nicemushroom-8b4ba259.canadacentral.azurecontainerapps.io', 'uk-cm-kg': 'https://cmkg-door-uk.livelybay-3553b0b4.uksouth.azurecontainerapps.io', 'au-cm-kg': 'https://cmkg-door-au.politeplant-e73e0a46.australiaeast.azurecontainerapps.io',
  'sg-cm-kg': 'https://cmkg-door-sg.ambitioussand-03ccaab5.southeastasia.azurecontainerapps.io', 'ch-cm-kg': 'https://cmkg-door-ch.gentledune-3c70acd2.switzerlandnorth.azurecontainerapps.io', 'de-cm-kg': 'https://cmkg-door-de.greensand-6ae55941.germanywestcentral.azurecontainerapps.io',
  'fr-cm-kg': 'https://cmkg-door-fr.agreeablehill-d2a7639b.francecentral.azurecontainerapps.io', 'nl-cm-kg': 'https://cmkg-door-nl.purpleisland-61490c7a.westeurope.azurecontainerapps.io', 'jp-cm-kg': 'https://cmkg-door-jp.calmpebble-18a3633a.japaneast.azurecontainerapps.io',
  'kr-cm-kg': 'https://cmkg-door-kr.calmpond-68249885.koreacentral.azurecontainerapps.io', 'us-cm-kg': 'https://cmkg-door-us.purpleglacier-e6bfd21c.eastus.azurecontainerapps.io',
  'it-cm-kg': 'https://cmkg-door-it.kindcliff-313fa995.italynorth.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'es-cm-kg': 'https://cmkg-door-es.victoriouswave-87fb8870.spaincentral.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'se-cm-kg': 'https://cmkg-door-se.bluegrass-1bcc155a.swedencentral.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'dk-cm-kg': 'https://cmkg-door-dk.bluegrass-1bcc155a.swedencentral.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'no-cm-kg': 'https://cmkg-door-no.orangewave-55876fe2.norwayeast.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'fi-cm-kg': 'https://cmkg-door-fi.bluegrass-1bcc155a.swedencentral.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'be-cm-kg': 'https://cmkg-door-be.purpleisland-61490c7a.westeurope.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'ie-cm-kg': 'https://cmkg-door-ie.purpleisland-61490c7a.westeurope.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'at-cm-kg': 'https://cmkg-door-at.greensand-6ae55941.germanywestcentral.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'pl-cm-kg': 'https://cmkg-door-pl.greensand-6ae55941.germanywestcentral.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'pt-cm-kg': 'https://cmkg-door-pt.victoriouswave-87fb8870.spaincentral.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'lu-cm-kg': 'https://cmkg-door-lu.purpleisland-61490c7a.westeurope.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'gr-cm-kg': 'https://cmkg-door-gr.kindcliff-313fa995.italynorth.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'cz-cm-kg': 'https://cmkg-door-cz.greensand-6ae55941.germanywestcentral.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'ky-cm-kg': 'https://cmkg-door-ky.purpleglacier-e6bfd21c.eastus.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'bm-cm-kg': 'https://cmkg-door-bm.purpleglacier-e6bfd21c.eastus.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'je-cm-kg': 'https://cmkg-door-je.livelybay-3553b0b4.uksouth.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'tw-cm-kg': 'https://cmkg-door-tw.kindtree-f0e64750.eastasia.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'ae-cm-kg': 'https://cmkg-door-ae.kindcliff-313fa995.italynorth.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'br-cm-kg': 'https://cmkg-door-br.purpleglacier-e6bfd21c.eastus.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'mx-cm-kg': 'https://cmkg-door-mx.purpleglacier-e6bfd21c.eastus.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'in-cm-kg': 'https://cmkg-door-in.ambitioussand-03ccaab5.southeastasia.azurecontainerapps.io',   // NODE-EU (2026-10-24)
  'hk-cm-kg': 'https://cmkg-door-hk.kindtree-f0e64750.eastasia.azurecontainerapps.io' };   // hk: ORDER-035 (2026-10-22), East Asia
const EU_DOOR = { 'it-cm-kg': 'https://it.eu-cm-kg.ai', 'es-cm-kg': 'https://es.eu-cm-kg.ai', 'se-cm-kg': 'https://se.eu-cm-kg.ai', 'dk-cm-kg': 'https://dk.eu-cm-kg.ai', 'no-cm-kg': 'https://no.eu-cm-kg.ai', 'fi-cm-kg': 'https://fi.eu-cm-kg.ai', 'be-cm-kg': 'https://be.eu-cm-kg.ai', 'ie-cm-kg': 'https://ie.eu-cm-kg.ai', 'at-cm-kg': 'https://at.eu-cm-kg.ai', 'pl-cm-kg': 'https://pl.eu-cm-kg.ai', 'pt-cm-kg': 'https://pt.eu-cm-kg.ai', 'gr-cm-kg': 'https://gr.eu-cm-kg.ai', 'cz-cm-kg': 'https://cz.eu-cm-kg.ai' };   // DAY ORDER 5 ZONES-01 (2026-10-24): the European doors answer under the EU regime zone, <cc>.eu-cm-kg.ai (path card); Luxembourg has its own zone (mcp.lu-cm-kg.ai) and takes the default
const PUBLIC = {}; for (const n of Object.keys(REGIONAL)) PUBLIC[n] = EU_DOOR[n] ? { door: EU_DOOR[n] + '/mcp', agent_card: EU_DOOR[n] + '/.well-known/agent-card.json' } : { door: `https://mcp.${n}.ai/mcp`, agent_card: `https://agent.${n}.ai/.well-known/agent-card.json` };
const ANN = { readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true };
const TOOLS = [
  { name: 'resolve_issuer', title: 'Resolve issuer', annotations: { title: 'Resolve issuer', ...ANN }, description: 'Find a listed company by ticker, ISIN or LEI: the apex names the owning node and forwards to that node\'s regional door for the record summary.', inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'Ticker with or without exchange (SHOP, TSX:SHOP, SHEL.L, BHP.AX, D05.SI, NESN.SW, SAP.DE, 7203.T, 005930.KS), ISIN, LEI, an exact legal name or a sourced alias.' } }, required: ['identifier'] } },
  { name: 'get_record', title: 'Get Capital Markets Record', annotations: { title: 'Get Capital Markets Record', ...ANN }, description: 'Return the full Capital Markets Record, served by the owning node\'s regional door (never stored at the apex).', inputSchema: { type: 'object', properties: { identifier: { type: 'string' }, version: { type: 'integer' } }, required: ['identifier'] } },
  { name: 'list_events_since', title: 'List disclosure events since a date', annotations: { title: 'List disclosure events since a date', ...ANN }, description: 'Dated, URL\'d disclosure events for an issuer since a date, served by the owning node\'s regional door.', inputSchema: { type: 'object', properties: { identifier: { type: 'string' }, since: { type: 'string' }, cursor: { type: 'integer' }, limit: { type: 'integer' } }, required: ['identifier'] } },
  { name: 'list_aliases', title: 'List sourced aliases', annotations: { title: 'List sourced aliases', ...ANN }, description: 'Sourced trade and former names, served by the owning node\'s regional door.', inputSchema: { type: 'object', properties: { identifier: { type: 'string' } }, required: ['identifier'] } },
  { name: 'list_nodes', title: 'List market nodes', annotations: { title: 'List market nodes', ...ANN }, description: 'Every market node on the roster (nodes.json, region on each), which are live, their regional doors and Agent Cards.', inputSchema: { type: 'object', properties: {} } },
  { name: 'get_signal', title: 'Get ACM-68000 signal', annotations: { title: 'Get ACM-68000 signal', ...ANN }, description: 'The ACM-68000 signal for a listed security in its home market: ACM-200 TRADING (on the register), ACM-404 NOT ON THE REGISTER, ACM-451 READ THE FILING (a regulatory filing in the last three days, named), ACM-300 CONDITIONAL (a bare ticker names more than one issuer: add the exchange), ACM-000 NOT APPLICABLE (a GTIN: ask gtinfetch.ai), ACM-500 SYSTEM ERROR (the home node did not answer). ACM-403 HALTED is advisory: the nodes carry no halt flag yet, so the answer links the market\'s halts page. Each signal has its page at https://acm-<code>.ai/.', inputSchema: { type: 'object', properties: { identifier: { type: 'string', description: 'ISIN (best), ticker with exchange (TSX:SHOP, SHEL.L), LEI or CMR key.' } }, required: ['identifier'] } },
];
const ECO_MARKETS = ['ae','ar','at','au','be','br','ca','ch','cl','co','cr','cz','de','dk','do','ec','es','fi','fr','gr','gt','hk','id','ie','il','in','it','jp','kr','ma','mx','my','nl','no','pa','pe','ph','pl','pt','sa','se','sg','th','tr','uk','us','uy','vn','za'];
const EXTRA_TOOLS = [
  { name: 'get_eco', title: 'Get Electronic Compliance Object', annotations: { title: 'Get Electronic Compliance Object', readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true }, description: 'The Electronic Compliance Object of one market (49): regulator, exchanges and listings page, regulated-information store, disclosure deadlines, ad hoc regime, filing format, ISIN prefix, LEI, calendar, languages, halts page — each field with its source page, signed (kid allooloo-eco-2026-10) — and the node status.', inputSchema: { type: 'object', properties: { market: { type: 'string', description: 'two-letter market code (fr, uk, us, de, jp, …)' } }, required: ['market'] } },
  { name: 'list_signals', title: 'List ACM-68000 signals', annotations: { title: 'List ACM-68000 signals', readOnlyHint: true, destructiveHint: false, openWorldHint: false, idempotentHint: true }, description: 'The seven ACM-68000 signals, what each means for a listed issuer, and the page of each (acm-<code>.ai).', inputSchema: { type: 'object', properties: {} } }];
const PROFILES = { '/eco/mcp': { name: 'allooloo-eco', tools: ['get_eco', 'get_signal', 'resolve_issuer', 'list_nodes'], instructions: 'Electronic Compliance Objects (Allooloo): get_eco(market) for the disclosure regime of a market (index: allooloo.ai/markets), each field sourced and signed; get_signal for the ACM-68000 state of a listed security; receipts on mcp.rco-a2a.ai.' },
  '/signals/mcp': { name: 'acm-signals', tools: ['get_signal', 'list_signals'], instructions: 'ACM-68000 signals for listed issuers (Allooloo): get_signal(identifier) answers ACM-200 TRADING, ACM-404 NOT ON THE REGISTER, ACM-451 READ THE FILING (named), ACM-300, ACM-000, ACM-500; ACM-403 HALTED is advisory. list_signals names the seven and their pages.' } };
let INDEX = null, NODES = null;
async function boot(env, origin) {
  if (INDEX) return;
  const [i, n] = await Promise.all([env.ASSETS.fetch(new Request(origin + '/index.json')), env.ASSETS.fetch(new Request(origin + '/nodes.json'))]);
  INDEX = i.ok ? await i.json() : { ticker: {}, isin: {}, lei: {}, alias: {}, name: {}, cmr: {} }; NODES = n.ok ? await n.json() : [];
  // ENUM-01 (DAY ORDER 6, 2026-10-25): a node's public door and card are its roster entry's `door` (the field of record); EU_DOOR above stays as the record
  for (const x of NODES) if (x.door) { const d = String(x.door).replace(/\/mcp$/, '').replace(/\/$/, ''); PUBLIC[x.node] = { door: d + '/mcp', agent_card: d.includes('.eu-cm-kg.ai') ? d + '/.well-known/agent-card.json' : d.replace('://mcp.', '://agent.') + '/.well-known/agent-card.json' }; }
}
const SUFFIX = { TO: 'ca-cm-kg', V: 'ca-cm-kg', CN: 'ca-cm-kg', NE: 'ca-cm-kg', L: 'uk-cm-kg', LN: 'uk-cm-kg', AQ: 'uk-cm-kg', AX: 'au-cm-kg', AU: 'au-cm-kg', NS: 'au-cm-kg', SI: 'sg-cm-kg', SG: 'sg-cm-kg', SW: 'ch-cm-kg', VX: 'ch-cm-kg', BX: 'ch-cm-kg', DE: 'de-cm-kg', F: 'de-cm-kg', XE: 'de-cm-kg', PA: 'fr-cm-kg', AS: 'nl-cm-kg', NA: 'nl-cm-kg', T: 'jp-cm-kg', JP: 'jp-cm-kg', KS: 'kr-cm-kg', KQ: 'kr-cm-kg', KN: 'kr-cm-kg', N: 'us-cm-kg', O: 'us-cm-kg', OQ: 'us-cm-kg', US: 'us-cm-kg', HK: 'hk-cm-kg' };
const PREFIX = { TXSE: 'us-cm-kg', 'TXSE-LISTED': 'us-cm-kg', TSX: 'ca-cm-kg', TSXV: 'ca-cm-kg', 'TSX-V': 'ca-cm-kg', CVE: 'ca-cm-kg', CSE: 'ca-cm-kg', CNSX: 'ca-cm-kg', NEO: 'ca-cm-kg', CBOE: 'ca-cm-kg', 'CBOE-CANADA': 'ca-cm-kg', LSE: 'uk-cm-kg', LON: 'uk-cm-kg', AIM: 'uk-cm-kg', AQSE: 'uk-cm-kg', ASX: 'au-cm-kg', NSX: 'au-cm-kg', SGX: 'sg-cm-kg', CATALIST: 'sg-cm-kg', 'SGX-CATALIST': 'sg-cm-kg', SIX: 'ch-cm-kg', SWX: 'ch-cm-kg', BX: 'ch-cm-kg', XETRA: 'de-cm-kg', ETR: 'de-cm-kg', FRA: 'de-cm-kg', DE: 'de-cm-kg', EUREX: 'de-cm-kg', XPAR: 'fr-cm-kg', EPA: 'fr-cm-kg', ALXP: 'fr-cm-kg', XMLI: 'fr-cm-kg', EURONEXT: 'fr-cm-kg', XAMS: 'nl-cm-kg', AMS: 'nl-cm-kg', AEX: 'nl-cm-kg', ALXA: 'nl-cm-kg', TSE: 'jp-cm-kg', TYO: 'jp-cm-kg', JPX: 'jp-cm-kg', 'TSE-PRIME': 'jp-cm-kg', 'TSE-STANDARD': 'jp-cm-kg', 'TSE-GROWTH': 'jp-cm-kg', 'TSE-PRO': 'jp-cm-kg', 'TSE-REIT': 'jp-cm-kg', KRX: 'kr-cm-kg', KOSPI: 'kr-cm-kg', KOSDAQ: 'kr-cm-kg', KONEX: 'kr-cm-kg', NYSE: 'us-cm-kg', NASDAQ: 'us-cm-kg', XNYS: 'us-cm-kg', XNAS: 'us-cm-kg', HKEX: 'hk-cm-kg', SEHK: 'hk-cm-kg', XHKG: 'hk-cm-kg', HKG: 'hk-cm-kg', 'HKEX-GEM': 'hk-cm-kg', GEM: 'hk-cm-kg', 'HKEX-REIT': 'hk-cm-kg' };
function nodesFor(kind, value) { const v = INDEX[kind] && INDEX[kind][value]; return v ? [].concat(v) : []; }
function whichNode(idRaw) {
  const id = (idRaw || '').trim(); if (!id) return { nodes: [], kind: 'empty' };
  const up = id.toUpperCase(); let m;
  if ((m = up.match(/^([A-Z]{2}-CM-KG)\//))) return { nodes: [m[1].toLowerCase()], kind: 'cmr' };
  if (/^[A-Z]{2}[A-Z0-9]{9}\d$/.test(up)) return { nodes: nodesFor('isin', up), kind: 'isin' };
  if (/^[A-Z0-9]{18}[0-9]{2}$/.test(up)) return { nodes: nodesFor('lei', up), kind: 'lei' };
  const pm = up.match(/^([A-Z\-]+):(.+)$/); if (pm && PREFIX[pm[1]]) return { nodes: [PREFIX[pm[1]]], kind: 'ticker' };
  const sm = up.match(/^(.+)\.([A-Z]{1,2})$/); if (sm && SUFFIX[sm[2]] && !nodesFor('ticker', up).length) return { nodes: [SUFFIX[sm[2]]], kind: 'ticker' };
  let n = nodesFor('ticker', up); if (n.length) return { nodes: n, kind: 'ticker' };
  const nk = id.toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim();
  n = nodesFor('alias', nk); if (n.length) return { nodes: n, kind: 'alias' };
  n = nodesFor('name', nk); if (n.length) return { nodes: n, kind: 'name' };
  return { nodes: [], kind: 'ticker' };
}
async function forward(node, name, args) {
  const origin = REGIONAL[node]; if (!origin) return { error: 'unavailable', node, note: 'no regional door configured for this node' };
  try {
    const r = await fetch(origin + '/mcp', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }), signal: AbortSignal.timeout(20000) });
    if (!r.ok) return { error: 'unavailable', node, note: `regional door answered ${r.status}`, regional_door: PUBLIC[node].door };
    const j = await r.json(); const out = (j.result && j.result.structuredContent) || { error: 'unavailable', node, note: 'regional door returned no structured content' };
    if (out && typeof out === 'object' && !Array.isArray(out)) out.served_by = { node, regional_door: PUBLIC[node].door, agent_card: PUBLIC[node].agent_card };
    if (ENV && out && !out.error) { if (name === 'get_record') return await signRecord(ENV, out); if (name === 'resolve_issuer' && Array.isArray(out.matches)) out.matches = await Promise.all(out.matches.map(x => signRecord(ENV, x))); }
    return out;
  } catch (e) { return { error: 'unavailable', node, note: `regional door did not answer (${e.name || 'error'}); no fallback — the record lives only in its own region`, regional_door: PUBLIC[node].door }; }
}
// ---- ACM-SIGNALS-01 (2026-10-24): get_signal — the ACM-68000 issuer state, read live from the home node (and Issuerwire for filings), never typed
const SIGNALS = { 'ACM-000': 'NOT APPLICABLE', 'ACM-200': 'TRADING', 'ACM-300': 'CONDITIONAL', 'ACM-403': 'HALTED', 'ACM-404': 'NOT ON THE REGISTER', 'ACM-451': 'READ THE FILING', 'ACM-500': 'SYSTEM ERROR' };
const MEANING = { 'ACM-000': 'The issuer layer does not apply to this identifier.', 'ACM-200': 'On the home market\'s register: proceed.', 'ACM-300': 'More than one issuer matches: name the exchange or give the ISIN, then ask again.', 'ACM-403': 'Trading is halted or suspended: do not act until it resumes.', 'ACM-404': 'Not on the register of any market on the roster: do not act on it as listed.', 'ACM-451': 'A regulatory filing is dated in the last three days: a person reads it before the agent acts.', 'ACM-500': 'The home market\'s node did not answer: retry; no record is served from another store.' };
const IW = 'https://mcp.issuerwire.ai/mcp';
const HOME = { IN: 'in-cm-kg', MX: 'mx-cm-kg', BR: 'br-cm-kg', AE: 'ae-cm-kg', TW: 'tw-cm-kg', CZ: 'cz-cm-kg', GR: 'gr-cm-kg', LU: 'lu-cm-kg', PT: 'pt-cm-kg', PL: 'pl-cm-kg', AT: 'at-cm-kg', IE: 'ie-cm-kg', BE: 'be-cm-kg', FI: 'fi-cm-kg', NO: 'no-cm-kg', DK: 'dk-cm-kg', SE: 'se-cm-kg', ES: 'es-cm-kg', IT: 'it-cm-kg', CA: 'ca-cm-kg', GB: 'uk-cm-kg', US: 'us-cm-kg', DE: 'de-cm-kg', FR: 'fr-cm-kg', NL: 'nl-cm-kg', CH: 'ch-cm-kg', AU: 'au-cm-kg', SG: 'sg-cm-kg', JP: 'jp-cm-kg', KR: 'kr-cm-kg', HK: 'hk-cm-kg', KY: 'hk-cm-kg', BM: 'hk-cm-kg' };
async function iw(name, args) {
  try { const r = await fetch(IW, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', 'user-agent': 'getissuer get_signal (ACM-SIGNALS-01)' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: args } }), signal: AbortSignal.timeout(8000) });
    const raw = await r.text(); const line = raw.split('\n').find(l => l.trim().startsWith('{') || l.startsWith('data: {')); const j = JSON.parse(line.replace(/^data: /, ''));
    return JSON.parse(j.result.content[0].text); } catch (e) { return null; }
}
const sigOut = (code, extra) => { const o = { signal: code, state: SIGNALS[code], meaning: MEANING[code], signal_page: `https://acm-${code.slice(4)}.ai/`, standard: 'https://acm-68000.org/', read_at: new Date().toISOString(), ...extra };
  // NODE-HALT-01 (2026-10-24): ACM-403 comes from the record's halt flag; the advisory line stays only where the node's flag was not read for this record
  if (!o.halt || o.halt.value == null) o.advisory_403 = 'ACM-403 HALTED: this node\'s halt flag was not read for this record; read the market\'s halts page (named on its ECO page) before acting.';
  return o; };
async function getSignal(idRaw) {
  const id = String(idRaw || '').trim(); const up = id.toUpperCase();
  if (/^\d{8}$|^\d{12,14}$/.test(id)) return sigOut('ACM-000', { identifier: id, note: 'a GTIN, not a listed-security identifier', route: { gtins: 'https://gtinfetch.ai/mcp', path: `https://gtinfetch.ai/01/${id.padStart(14, '0')}` } });
  const w = whichNode(id);
  if (!w.nodes.length) return sigOut('ACM-404', { identifier: id, matched_by: w.kind, note: 'no node on the roster holds this identifier', nodes: NODES.filter(n => n.live).map(n => n.node) });
  const outs = await Promise.all(w.nodes.map(n => forward(n, 'resolve_issuer', { identifier: id })));
  const matches = [].concat(...outs.map(o => o.matches || []));
  if (!matches.length) { const un = outs.filter(o => o.error === 'unavailable'); return un.length ? sigOut('ACM-500', { identifier: id, unavailable: un.map(o => o.node) }) : sigOut('ACM-404', { identifier: id, matched_by: w.kind }); }
  const isIsin = w.kind === 'isin';
  if (!isIsin && w.kind !== 'cmr' && new Set(matches.map(m => m.cmr)).size > 1) return sigOut('ACM-300', { identifier: id, matched_by: w.kind, candidates: matches.map(m => ({ cmr: m.cmr, name: m.name, exchange: m.exchange, isin: m.isin || null })) });
  const homeNode = isIsin ? HOME[up.slice(0, 2)] : null;
  const ranked = matches.slice().sort((a, b) => ((b.node === homeNode) - (a.node === homeNode)) || ((b.security_type || '').startsWith('Corporate') - (a.security_type || '').startsWith('Corporate')) || (String(b.as_of).localeCompare(String(a.as_of))));
  const h = ranked[0]; const cc = h.node.split('-')[0]; const cut = new Date(Date.now() - 3 * 86400000).toISOString().slice(0, 10);
  const base = { record_signature: sigRef(h), identifier: id, issuer: h.name, node: h.node, cmr: h.cmr, exchange: h.exchange, isin: h.isin || null, lei: h.lei || null, as_of: h.as_of, record: h.record_url, events: h.events_url, eco: `https://${cc}-eco.ai/`, door: PUBLIC[h.node] ? PUBLIC[h.node].door : null,
    elsewhere: ranked.slice(1).map(m => ({ node: m.node, name: m.name, exchange: m.exchange, record: m.record_url })) };
  const recd = await forward(h.node, 'get_record', { identifier: h.cmr }); const halt = recd && !recd.error ? (recd.halt || null) : null; if (halt) base.halt = halt;
  if (recd && recd.signature) base.record_signature = sigRef(recd);
  if (halt && halt.value === true) return sigOut('ACM-403', { ...base, halted: { since: halt.since || null, reason: halt.reason || null, page: halt.page || halt.source_url, read_at: halt.read_at, read_by: halt.read_by } });
  let filing = null;
  const ev = await forward(h.node, 'list_events_since', { identifier: h.cmr, limit: 25 });
  const e = (ev.events || []).find(x => x.event_type !== 'newswire_release' && String(x.date) >= cut);
  if (e) filing = { date: e.date, title: e.title, url: e.url || null, source: e.source || e.wire || null, from: 'node events' };
  if (!filing) {
    const mk = cc === 'uk' ? 'UK' : cc.toUpperCase();
    const ri = await iw('resolve_issuer', { query: h.isin || h.cmr.split('/').pop(), market: mk, limit: 3 });
    const key = ri && (ri.issuers || ri.matches || ri.results || [])[0] && ((ri.issuers || ri.matches || ri.results)[0].issuer_key);
    if (key) { const lf = await iw('list_filings', { issuer: key, since: cut, type: 'filing', limit: 3 }); const row = lf && (lf.rows || [])[0]; if (row && String(row.date) >= cut) filing = { date: row.date, title: row.title, issuerwire_row: row.id, issuer_key: key, read: 'get_row on https://mcp.issuerwire.ai/mcp', from: 'Issuerwire' }; }
  }
  if (filing) return sigOut('ACM-451', { ...base, filing });
  return sigOut('ACM-200', base);
}
async function callTool(name, args) {
  args = args || {};
  if (name === 'list_signals') return { protocol: 'ACM-68000', standard: 'https://acm-68000.org/', signals: [['000', 'NOT_APPLICABLE', 'NOT APPLICABLE'], ['200', 'ALLOW', 'TRADING'], ['300', 'CONDITIONAL', 'CONDITIONAL'], ['403', 'RESTRICT', 'HALTED (advisory)'], ['404', 'NOT_FOUND', 'NOT ON THE REGISTER'], ['451', 'ESCALATE', 'READ THE FILING'], ['500', 'SYSTEM_ERROR', 'SYSTEM ERROR']].map(([c, s, i]) => ({ code: 'ACM-' + c, state: s, listed_issuers: i, page: `https://acm-${c}.ai/` })), tool: 'get_signal' };
  if (name === 'get_eco') { const cc = String(args.market || '').toLowerCase().trim(); if (!/^[a-z]{2}$/.test(cc)) return { error: 'not_found', market: args.market, markets: 'https://allooloo.ai/markets' };   // ENUM-01: the ECO page itself says whether a market has an object (ECO_MARKETS above, 49, is the record of ECO-01 only)
    try { const r = await fetch(`https://${cc}-eco.ai/eco.json`, { headers: { 'user-agent': 'Allooloo getissuer (get_eco)', accept: 'application/json' }, signal: AbortSignal.timeout(12000) }); if (r.status === 404) return { error: 'not_found', market: cc, markets: 'https://allooloo.ai/markets' }; const j = await r.json(); return { market: cc, page: `https://${cc}-eco.ai/`, ...j }; } catch (e) { return { error: 'unavailable', market: cc, page: `https://${cc}-eco.ai/` }; } }
  if (name === 'get_signal') return getSignal(args.identifier);
  if (name === 'list_nodes') return { door: 'apex router: index only; records and events are served by each node\'s regional door', live_nodes: NODES.filter(n => n.live).map(n => n.node), nodes: NODES.map(n => ({ ...n, regional_door: PUBLIC[n.node] ? PUBLIC[n.node].door : null, agent_card: PUBLIC[n.node] ? PUBLIC[n.node].agent_card : null })) };
  const w = whichNode(args.identifier);
  if (!w.nodes.length) return { error: 'not_found', identifier: args.identifier, kind: w.kind, note: 'no node in the index holds this identifier' };
  if (name === 'resolve_issuer') {
    const outs = await Promise.all(w.nodes.map(n => forward(n, name, args)));
    const matches = [].concat(...outs.map(o => o.matches || [])); const unavailable = outs.filter(o => o.error === 'unavailable');
    return { matches, matched_by: w.kind, ambiguous: matches.length > 1, nodes_asked: w.nodes, unavailable: unavailable.length ? unavailable : undefined, note: unavailable.length ? 'one or more regional doors did not answer; no fallback store' : undefined };
  }
  if (w.nodes.length > 1) return { error: 'ambiguous', nodes: w.nodes, note: 'the identifier lives on more than one node; add an exchange prefix or use the CMR key' };
  return forward(w.nodes[0], name, args);
}
// ---- RCO-A-01 (2026-10-24): the receipt of a decision the resolver cleared (plan v1.1 §2.6)
async function receiptFor(d, host) {
  const { id, name, args, out } = d; const ident = String(args.identifier || '').trim(); const w = whichNode(ident);
  const type = /^\d{8}$|^\d{12,14}$/.test(ident) ? 'gtin' : ({ isin: 'isin', lei: 'lei', cmr: 'cmr', ticker: 'ticker' }[w.kind] || 'identifier');
  let signal, rule; const records = [];
  if (name === 'get_signal') {
    signal = out.signal; rule = { id: 'ACM-68000 issuer states — getissuer get_signal', version: SERVER_VERSION };
    if (out.record) records.push({ url: out.record, as_of: out.as_of || null, sha256: await sha256({ cmr: out.cmr, node: out.node, as_of: out.as_of, isin: out.isin, issuer: out.issuer }), signature: out.record_signature || null });
    if (out.filing) records.push({ url: out.filing.url || ('https://mcp.issuerwire.ai/mcp#get_row:' + out.filing.issuerwire_row), as_of: out.filing.date || null, sha256: await sha256(out.filing),
      signature: out.filing.from === 'Issuerwire' ? { alg: 'EdDSA', kid: 'amn-2026-10', keyring: 'https://issuerwire.ai/.well-known/jwks.json', note: 'the row is signed by Issuerwire; the full signed row is served on x402' } : null });
  } else {
    const m = out.matches || []; signal = m.length ? 'ACM-200' : (out.unavailable && out.unavailable.length ? 'ACM-500' : 'ACM-404');
    rule = { id: 'getissuer resolve_issuer — the registers of every node on the roster (index only)', version: SERVER_VERSION + ' · index as_of ' + indexAsOf() };
    for (const x of m.slice(0, 6)) records.push({ url: x.record_url, as_of: x.as_of || null, sha256: await sha256(x), signature: sigRef(x) });
  }
  if (!records.length) records.push({ url: `https://${host}/nodes.json`, as_of: indexAsOf() || null, sha256: null, signature: null });
  const body = { decision_id: id, object: { type, id: ident.slice(0, 80) }, actor_class: d.actor || 'ai-agent (MCP client)', rule, records_read: records.filter(r => r.url), signal, decided_at: d.at, issuing_door: `https://${host}/mcp` };
  if (d.settlement) body.settlement = d.settlement;   // X402-A-01: a paid read's receipt names its settlement (network and transaction, never an amount)
  return body;
}
function rpcResult(id, result) { return { jsonrpc: '2.0', id, result }; }
function rpcError(id, code, message) { return { jsonrpc: '2.0', id: id === undefined ? null : id, error: { code, message } }; }
async function handleRpc(msg, cx) {
  const prof = cx && cx.profile ? PROFILES[cx.profile] : null; const ALL = TOOLS.concat(EXTRA_TOOLS); const LIST = prof ? ALL.filter(x => prof.tools.includes(x.name)) : TOOLS;
  const { id, method, params } = msg || {};
  if (!method) return rpcError(id, -32600, 'Invalid Request');
  if (method === 'initialize') return rpcResult(id, { protocolVersion: (params && params.protocolVersion) || PROTOCOL, capabilities: { tools: { listChanged: false } }, serverInfo: { name: prof ? prof.name : 'capitalmarketsknowledgegraph', version: SERVER_VERSION }, instructions: prof ? prof.instructions : 'Capital Markets Knowledge Graph apex: an index-only router. Identify an issuer by ticker, ISIN or LEI; the record is served by the owning node\'s regional door in its own jurisdiction. Read-only, public-record only, no auth, no prices.' });
  if (method.startsWith('notifications/')) return null;
  if (method === 'ping') return rpcResult(id, {});
  if (method === 'tools/list') return rpcResult(id, { tools: LIST });
  if (method === 'tools/call') { const name = params && params.name; if (!LIST.find(t => t.name === name)) return rpcError(id, -32602, `Unknown tool: ${name}`); const args = (params && params.arguments) || {}; const out = await callTool(name, args);
    if (cx && !cx.internal && (name === 'resolve_issuer' || name === 'get_signal') && out && typeof out === 'object') { const did = decisionId(); out.receipt = receiptLinks(did); cx.decisions.push({ id: did, name, args, out, at: new Date().toISOString() }); } return rpcResult(id, { content: [{ type: 'text', text: JSON.stringify(out) }], structuredContent: out, isError: !!(out && out.error && out.error !== 'ambiguous') }); }
  if (method === 'resources/list') return rpcResult(id, { resources: [] });
  if (method === 'prompts/list') return rpcResult(id, { prompts: [] });
  return rpcError(id, -32601, `Method not found: ${method}`);
}
// ORDER-027 C2 (2026-10-17): agent.getissuer.ai / mcp.getissuer.ai are aliases of this router — same tools, same index, same card; the card's name reads 'getissuer' there.
function agentCard(host) {
  return { name: /(^|\.)getissuer\.ai$/.test(host || '') ? 'getissuer' : 'Capital Markets Knowledge Graph — apex router', description: 'Index-only router over the Capital Markets Knowledge Graph: names the node that holds an issuer (ticker, ISIN, LEI, legal name or sourced alias) and forwards record and event calls to that node\'s regional door. No record body is stored or served from the apex; each node\'s data lives and is served in its own jurisdiction. Read-only, public-record only, no auth, no prices.',
    url: 'https://mcp.capitalmarketsknowledgegraph.ai/mcp', preferredTransport: 'JSONRPC', supportedInterfaces: [{ url: 'https://mcp.capitalmarketsknowledgegraph.ai/mcp', transport: 'JSONRPC' }], additionalInterfaces: [{ url: 'https://mcp.capitalmarketsknowledgegraph.ai/mcp', transport: 'JSONRPC' }], securitySchemes: {}, security: [], defaultInputModes: ['application/json', 'text/plain'], defaultOutputModes: ['application/json'], iconUrl: 'https://mcp.capitalmarketsknowledgegraph.ai/icon-512.png', provider: { organization: OPERATOR, url: 'https://allooloo.io' }, version: SERVER_VERSION, documentationUrl: 'https://mcp.capitalmarketsknowledgegraph.ai/llms.txt', protocolVersion: '0.3.0', capabilities: { streaming: false, pushNotifications: false, stateTransitionHistory: false }, defaultInputModes: ['application/json', 'text/plain'], defaultOutputModes: ['application/json'],
    skills: TOOLS.map(t => ({ id: t.name, name: t.title, description: t.description, tags: ['capital-markets', 'public-record', 'router', 'mcp'] })),
    'x-cmkg': { role: 'apex router', transport: 'MCP Streamable HTTP (JSON-RPC 2.0, stateless, no auth)', registry: 'io.github.allooloo/cm-kg', contact: 'allooloo@users.noreply.github.com', roster: { nodes: (NODES || []).length, live: (NODES || []).filter(n => n.live).length, source: 'https://mcp.getissuer.ai/nodes.json (the roster of record; list_nodes)' },   // LIST-02 (2026-10-26): read from the roster, never typed
    node_agents: (NODES || []).map(n => ({ node: n.node, country: n.country, live: !!n.live, regional_door: PUBLIC[n.node] ? PUBLIC[n.node].door : null, agent_card: PUBLIC[n.node] ? PUBLIC[n.node].agent_card : null, example: n.example || null })), old_shared_door: 'the Cloudflare Worker + D1 door (cm-kg-door) stays deployed beside this router and is listed for CEO deletion at end of scope' } };
}
function indexAsOf() { let m = ''; for (const n of (NODES || [])) { if (n && n.as_of && String(n.as_of) > m) m = String(n.as_of); } return m; }
function asOfOf(obj) {  // the as-of of the record served: a result that carries as_of, or the newest among resolve_issuer matches
  if (!obj || typeof obj !== 'object') return '';
  if (obj.as_of) return String(obj.as_of);
  if (obj.record && obj.record.as_of) return String(obj.record.as_of);
  if (Array.isArray(obj.matches) && obj.matches.length) { let m = ''; for (const x of obj.matches) if (x && x.as_of && String(x.as_of) > m) m = String(x.as_of); return m; }
  return '';
}
function headers(extra = {}) { const asOf = (extra && extra['X-CMR-As-Of']) || indexAsOf(); return { 'Content-Security-Policy': CSP, 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'X-CMR-Node': 'apex', 'X-CMR-As-Of': asOf, 'X-CMR-Contact': 'CEO mk@allooloo.ai', 'X-CMR-Source': 'public-record', 'X-CMR-Operator': OPERATOR, 'X-CMR-Registry': 'io.github.allooloo/cm-kg', 'X-CMR-Version': SERVER_VERSION, 'Strict-Transport-Security': 'max-age=31536000', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version, Authorization', 'Access-Control-Expose-Headers': 'X-CMR-Node, X-CMR-As-Of, X-CMR-Source, X-CMR-Operator, X-CMR-Version, Mcp-Session-Id', ...extra }; }
function json(obj, status = 200, cache = 'no-store', asOf = '') { return new Response(JSON.stringify(obj), { status, headers: headers({ 'content-type': 'application/json; charset=utf-8', 'cache-control': cache, ...(asOf ? { 'X-CMR-As-Of': asOf } : {}) }) }); }
function human() {
  const live = NODES.filter(n => n.live);
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Capital Markets Knowledge Graph — apex router</title><link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><meta name="theme-color" content="#14213D"><style>body{font-family:system-ui,sans-serif;max-width:72ch;margin:2rem auto;padding:0 1rem;color:#14213D;line-height:1.5}code{background:#f3f4f6;padding:.1em .3em}h1{font-size:1.4rem}</style></head><body><h1>Capital Markets Knowledge Graph — apex router</h1>
<p>Index-only. This door names the node that holds an issuer and forwards record and event calls to that node's regional door; no record body lives here. Each node's data is served in its own jurisdiction. Read-only, public-record only, no authentication, no prices.</p>
<p>MCP endpoint (Streamable HTTP): <code>https://mcp.capitalmarketsknowledgegraph.ai/mcp</code> · Agent Card: <a href="https://agent.capitalmarketsknowledgegraph.ai/.well-known/agent-card.json">agent.capitalmarketsknowledgegraph.ai</a> · <a href="/nodes.json">/nodes.json</a> · <a href="/llms.txt">/llms.txt</a></p>
<p>Live nodes (${live.length}): ${live.map(n => `<a href="${n.door || '#'}">${n.country}</a>`).join(' · ')}</p>
<p>Operator: Allooloo Technologies Corp., Richmond, BC, Canada.</p></body></html>`;
}
function llms() { return `# Capital Markets Knowledge Graph — apex router\nOperator: Allooloo Technologies Corp. Read-only MCP server at https://mcp.capitalmarketsknowledgegraph.ai/mcp (Streamable HTTP, JSON-RPC 2.0, no auth). Index only: ticker / ISIN / LEI / legal name / sourced alias -> node. Records and events are served by each node's regional door in its own jurisdiction and forwarded through here; nothing is stored at the apex; no fallback store.\nTools: resolve_issuer, get_record, list_events_since, list_aliases (forwarded), list_nodes (answered here).\nNodes: ${(NODES || []).map(n => `${n.node} (${n.country}, ${n.live ? 'live' : 'not live'}) door ${PUBLIC[n.node] ? PUBLIC[n.node].door : '-'} card ${PUBLIC[n.node] ? PUBLIC[n.node].agent_card : '-'}`).join('; ')}\nGET paths: /, /nodes.json, /llms.txt, /.well-known/agent-card.json, /record/<node>/<EXCHANGE>/<CODE> and /events/<node>/<EXCHANGE>/<CODE> (forwarded to the node).\n`; }
const CSP = "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; base-uri 'none'; form-action https://formspree.io; frame-ancestors 'none'; upgrade-insecure-requests";
const ROBOTS = host => `User-agent: *\nAllow: /\nContent-Signal: search=yes, ai-input=yes, ai-train=yes\n\nUser-agent: GPTBot\nAllow: /\n\nUser-agent: ClaudeBot\nAllow: /\n\nUser-agent: Claude-User\nAllow: /\n\nUser-agent: Claude-SearchBot\nAllow: /\n\nUser-agent: Google-Extended\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: Perplexity-User\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: ChatGPT-User\nAllow: /\n\nUser-agent: Bingbot\nAllow: /\n\nUser-agent: Applebot\nAllow: /\n\nUser-agent: Applebot-Extended\nAllow: /\n\nUser-agent: Amazonbot\nAllow: /\n\nUser-agent: CCBot\nAllow: /\n\nUser-agent: DuckAssistBot\nAllow: /\n\nUser-agent: meta-externalagent\nAllow: /\n\nUser-agent: Bytespider\nAllow: /\n\nUser-agent: cohere-ai\nAllow: /\n\nUser-agent: Diffbot\nAllow: /\n\nUser-agent: YouBot\nAllow: /\n\nUser-agent: MistralAI-User\nAllow: /\n\nUser-agent: xAI-Grok\nAllow: /\n\nSitemap: https://${host}/sitemap.xml\n`;
const SECURITY = host => `Contact: mailto:developers@allooloo.ai\nContact: https://allooloo.io\nExpires: 2027-09-12T00:00:00.000Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\nPolicy: https://allooloo.io\n`;
const KIT_PATHS = ['/', '/llms.txt', '/facts.json', '/nodes.json', '/robots.txt', '/sitemap.xml', '/mcp.json', '/openapi.json', '/.well-known/agent-card.json', '/.well-known/security.txt'];
function sitemap(host) { return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${KIT_PATHS.filter(x => x !== '/robots.txt').map(x => `<url><loc>https://${host}${x === '/' ? '/' : x}</loc></url>`).join('')}</urlset>\n`; }
function mcpJson(host) { const live = NODES.filter(n => n.live); return { name: 'cm-kg apex', description: 'Capital Markets Knowledge Graph — apex router: index only, forwards every call to the node that holds the identifier; no record body leaves its jurisdiction', version: SERVER_VERSION, transport: 'streamable-http', url: `https://${host}/mcp`, authentication: 'none', tools: TOOLS.map(t => ({ name: t.name, description: t.description })), agent_card: 'https://agent.capitalmarketsknowledgegraph.ai/.well-known/agent-card.json', openapi: `https://${host}/openapi.json`, llms: `https://${host}/llms.txt`, facts: `https://${host}/facts.json`, operator: OPERATOR, contact: 'developers@allooloo.ai', registry: 'io.github.allooloo/cm-kg', live_nodes: live.map(n => n.node), records: live.reduce((a, n) => a + (n.records || 0), 0), events: live.reduce((a, n) => a + (n.events || 0), 0), regional_doors: Object.fromEntries(live.map(n => [n.node, PUBLIC[n.node] ? PUBLIC[n.node].door : null])) }; }
function openapi(host) {
  const params = [{ name: 'node', in: 'path', required: true, schema: { type: 'string' } }, { name: 'exchange', in: 'path', required: true, schema: { type: 'string' } }, { name: 'code', in: 'path', required: true, schema: { type: 'string' } }];
  return { openapi: '3.1.0', info: { title: 'cm-kg apex router', version: SERVER_VERSION, description: 'Apex router of the Capital Markets Knowledge Graph: MCP over Streamable HTTP at /mcp; identifier index only; forwards to the regional door that holds the record. Public-record only.', contact: { name: OPERATOR, email: 'developers@allooloo.ai', url: 'https://allooloo.io' } }, servers: [{ url: `https://${host}` }],
    paths: { '/mcp': { post: { summary: 'MCP JSON-RPC (tools/list, tools/call)', requestBody: { required: true, content: { 'application/json': { schema: { type: 'object' } } } }, responses: { 200: { description: 'JSON-RPC response' } } } },
      '/record/{node}/{exchange}/{code}': { get: { summary: 'Capital Markets Record, forwarded to the owning node', parameters: params, responses: { 200: { description: 'record' }, 404: { description: 'not found' }, 503: { description: 'node unavailable, no fallback' } } } },
      '/events/{node}/{exchange}/{code}': { get: { summary: 'Dated disclosure events, forwarded to the owning node', parameters: params, responses: { 200: { description: 'events page' } } } },
      '/nodes.json': { get: { summary: 'The roster of record: every node with live counts', responses: { 200: { description: 'nodes' } } } }, '/facts.json': { get: { summary: 'Apex facts', responses: { 200: { description: 'facts' } } } }, '/llms.txt': { get: { summary: 'Machine instructions', responses: { 200: { description: 'text' } } } }, '/.well-known/agent-card.json': { get: { summary: 'A2A Agent Card', responses: { 200: { description: 'card' } } } } } };
}
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url); const host = url.hostname; const origin = url.origin; await boot(env, origin); ENV = env;
    const p = url.pathname.replace(/\/+$/, '') || '/';
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: headers() });
    if (p === '/mcp' || PROFILES[p]) {
      if (request.method !== 'POST') return new Response('POST JSON-RPC to /mcp', { status: 405, headers: headers({ 'content-type': 'text/plain', Allow: 'POST, OPTIONS' }) });
      let body; try { body = await request.json(); } catch (e) { return json(rpcError(null, -32700, 'Parse error'), 400); }
      const cx = { internal: INTERNAL.test(request.headers.get('user-agent') || ''), decisions: [], profile: PROFILES[p] ? p : null };
      const units = cx.internal ? 0 : (Array.isArray(body) ? body : [body]).filter(m => m && m.method === 'tools/call' && m.params && PAID_TOOLS.includes(m.params.name)).length;
      const g = units ? await decide(request, env, { door: 'getissuer', resource: `https://${host}/mcp`, description: 'One record read on getissuer, the listed-issuer resolver (Allooloo Technologies Corp.)', units }) : { pass: true, free: true };
      if (g.response) return g.response;
      const batch = Array.isArray(body); const outs = []; for (const m of (batch ? body : [body])) { const r = await handleRpc(m, cx); if (r) outs.push(r); }
      let pay = null; if (g.paid) { pay = await settle(env, g.paid, 'getissuer'); if (!pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed: ' + (pay.pr.errorReason || 'unknown') }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header, 'cache-control': 'no-store' } }); for (const d of cx.decisions) d.settlement = { network: pay.pr.network, transaction: pay.tx }; }
      if (cx.decisions.length && ctx) ctx.waitUntil(Promise.all(cx.decisions.map(async d => writeReceipt(env, await receiptFor(d, host)))));
      if (!outs.length) return new Response(null, { status: 202, headers: headers() });
      let servedAsOf = ''; for (const o of outs) { const sc = o && o.result && o.result.structuredContent; const a = asOfOf(sc); if (a > servedAsOf) servedAsOf = a; }
      const resp = json(batch ? outs : outs[0], 200, 'no-store', servedAsOf); if (pay) { resp.headers.set('PAYMENT-RESPONSE', pay.header); resp.headers.set('X-PAYMENT-RESPONSE', pay.header); } if (cx.decisions.length) { resp.headers.set('X-RCO-Decision-Id', cx.decisions.map(d => d.id).join(', ')); resp.headers.set('Access-Control-Expose-Headers', 'X-CMR-Node, X-CMR-As-Of, X-CMR-Source, X-CMR-Operator, X-CMR-Version, Mcp-Session-Id, X-RCO-Decision-Id, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE, PAYMENT-REQUIRED'); }
      return resp;
    }
    if (request.method === 'POST' && (p === '/x402/facilitator/verify' || p === '/x402/facilitator/settle')) return relay(request, env, p.slice(17));   // X402-A-01 rider: the RCO door's facilitator relay
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method Not Allowed', { status: 405, headers: headers() });
    if (p === '/.well-known/jwks.json') return json(RCO_JWKS, 200, 'public, max-age=3600');
    if (p === '/.well-known/agent-card.json' || p === '/.well-known/agent.json' || (host.startsWith('agent.') && p === '/')) return json(agentCard(host), 200, 'public, max-age=300');
    if (p === '/') return new Response(human(), { status: 200, headers: headers({ 'content-type': 'text/html; charset=utf-8', 'cache-control': 'public, max-age=300' }) });
    if (p === '/llms.txt') return new Response(llms(), { status: 200, headers: headers({ 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=3600' }) });
    if (p === '/nodes.json') return json(NODES.map(n => ({ ...n, regional_door: PUBLIC[n.node] ? PUBLIC[n.node].door : null, agent_card: PUBLIC[n.node] ? PUBLIC[n.node].agent_card : null })), 200, 'public, max-age=3600');
    if (p === '/facts.json') return json({ door: host, role: 'apex router (index only)', live_nodes: NODES.filter(n => n.live).map(n => n.node), nodes: Object.fromEntries(NODES.map(n => [n.node, { live: !!n.live, records: n.records, regional_door: PUBLIC[n.node] ? PUBLIC[n.node].door : null, ...(n.backfill ? { backfill: n.backfill } : {}) }])), backfill: { dataset: 'Allooloo Datasets — backfill (BACKFILL-01): history per market, epoch 2021-01-01; never a market count', markets_with_history: NODES.filter(n => n.backfill && n.backfill.rows).length, rows: NODES.reduce((a, n) => a + ((n.backfill && n.backfill.rows) || 0), 0), documents: NODES.reduce((a, n) => a + ((n.backfill && n.backfill.documents) || 0), 0), source: 'each store backfill/facts.json, carried onto the roster by build_index.py' }, operator: OPERATOR, source: 'public-record', mcp_url: 'https://mcp.capitalmarketsknowledgegraph.ai/mcp' }, 200, 'public, max-age=300');   // BACKFILL-01 B-7 (DAY ORDER 7): apex facts gain the backfill counts
    if (p === '/robots.txt') return new Response(ROBOTS(host), { headers: headers({ 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=86400' }) });
    if (p === '/.well-known/security.txt') return new Response(SECURITY(host), { headers: headers({ 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=86400' }) });
    if (p === '/sitemap.xml') return new Response(sitemap(host), { headers: headers({ 'content-type': 'application/xml; charset=utf-8', 'cache-control': 'public, max-age=3600' }) });
    if (p === '/mcp.json' || p === '/.well-known/mcp.json') return json({ ...mcpJson(host), payment: paymentDoor(env), routing: ROUTING, receipts: { door: 'https://mcp.rco-a2a.ai/mcp', keyring: 'https://mcp.getissuer.ai/.well-known/jwks.json', note: 'every resolve_issuer and get_signal leaves an RCO receipt; the answer carries its decision_id' } }, 200, 'public, max-age=300');
    if (p === '/x402/pricing.json') return json({ ...PRICING, door: `https://${host}/mcp`, payment: paymentDoor(env) }, 200, 'public, max-age=300');
    if (p === '/openapi.json') return json(openapi(host), 200, 'public, max-age=3600');
    if (['/favicon.ico', '/favicon.svg', '/apple-touch-icon.png', '/icon-48.png', '/icon-96.png', '/icon-144.png', '/icon-192.png', '/icon-512.png', '/site.webmanifest'].includes(p)) { const a = await env.ASSETS.fetch(new Request(origin + p)); return a.ok ? new Response(a.body, { status: 200, headers: headers({ 'content-type': a.headers.get('content-type') || 'application/octet-stream', 'cache-control': 'public, max-age=86400' }) }) : json({ error: 'not_found' }, 404); }
    const sg = p.match(/^\/signal\/([^/]+)$/);
    if (sg || /^\/(record|events)\//.test(p)) {
      const internal = INTERNAL.test(request.headers.get('user-agent') || '');
      const g = internal ? { pass: true, free: true } : await decide(request, env, { door: 'getissuer', resource: `https://${host}${p}`, description: 'One record read on getissuer, the listed-issuer resolver (Allooloo Technologies Corp.)' });
      if (g.response) return g.response;
      if (sg) {
        const ident = decodeURIComponent(sg[1]); const out = await getSignal(ident); let pay = null;
        if (g.paid) { pay = await settle(env, g.paid, 'getissuer'); if (!pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed: ' + (pay.pr.errorReason || 'unknown') }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header, 'cache-control': 'no-store' } }); }
        let did = null; if (!internal) { did = decisionId(); out.receipt = receiptLinks(did); const d = { id: did, name: 'get_signal', args: { identifier: ident }, out, at: new Date().toISOString(), actor: 'api-client (HTTP GET)', settlement: pay ? { network: pay.pr.network, transaction: pay.tx } : undefined }; if (ctx) ctx.waitUntil((async () => writeReceipt(env, await receiptFor(d, host)))()); }
        if (pay) out.settlement = { network: pay.pr.network, transaction: pay.tx, payer: pay.payer };
        const resp = json(out, 200, 'no-store', out.as_of || ''); if (did) resp.headers.set('X-RCO-Decision-Id', did); if (pay) { resp.headers.set('PAYMENT-RESPONSE', pay.header); resp.headers.set('X-PAYMENT-RESPONSE', pay.header); }
        resp.headers.set('Access-Control-Expose-Headers', 'X-RCO-Decision-Id, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE, PAYMENT-REQUIRED'); return resp;
      }
      if (g.paid) { const pay = await settle(env, g.paid, 'getissuer'); if (!pay.settled) return new Response(JSON.stringify({ x402Version: 2, error: 'settlement failed' }), { status: 402, headers: { 'content-type': 'application/json', 'PAYMENT-RESPONSE': pay.header } }); request.__pay = pay; }
    }
    let m = p.match(/^\/(record|events)\/([a-z]{2}-cm-kg)\/([A-Z\-]+)\/(.+)$/i);
    if (m) { const node = m[2].toLowerCase(); const key = `${node}/${m[3].toUpperCase()}/${decodeURIComponent(m[4])}`; const out = m[1].toLowerCase() === 'record' ? await forward(node, 'get_record', { identifier: key }) : await forward(node, 'list_events_since', { identifier: key, since: url.searchParams.get('since') || undefined, cursor: url.searchParams.get('cursor') || 0, limit: url.searchParams.get('limit') || 50 }); return json(out, out.error ? (out.error === 'unavailable' ? 503 : 404) : 200, 'no-store', asOfOf(out)); }
    return json({ error: 'not_found', doors: ['/', '/mcp', '/nodes.json', '/facts.json', '/llms.txt', '/.well-known/agent-card.json', '/record/<node>/<EXCHANGE>/<CODE>', '/events/<node>/<EXCHANGE>/<CODE>'] }, 404);
  }
};
