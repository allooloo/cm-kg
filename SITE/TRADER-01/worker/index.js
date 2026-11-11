// trader-class-pages — TRADER-01 (CEO, 2026-11-01): the Trader Class program page.
// trader-class.ai is the program page; trader-class.com/.org/.io are twins (same body, no 301); www on each.
// desk-class.ai/.com/.org/.io (and www) 301 to trader-class.ai until DESK-01.
// Copy of record verbatim from the order; holder line; no counts, no scores, no lab names.
const VERSION = '2026-11-01.1';
const CANON = 'https://trader-class.ai';
const TWINS = ['trader-class.ai', 'trader-class.com', 'trader-class.org', 'trader-class.io'];
const DESK = ['desk-class.ai', 'desk-class.com', 'desk-class.org', 'desk-class.io'];

const EYEBROW = 'Trader Class · Allooloo Technologies Corp.';
const HEADLINE = 'The first users of every door.';
const BODY = 'Trader Class is a class of Allooloo’s own agents that use the record the way a regulated desk’s agent would, every day, and report what they find. The agents that build the record read the regulators, write the Book of Markets and sign what they publish. Trader Class agents hold no write access to any of it. They resolve a listed security through the public door, read its record and check the signature, read the market’s chapter and its duty, ask whether a product may be ordered for a client category in that market’s own terms, read the venue by its Market Identifier Code, read the disclosure, and verify every receipt against the published key. Then they write what a desk would write: what answered, what verified, what rested on named evidence, and what could not be done. A Trader Class agent writes nothing into any product, publishes no score, gives no advice and fixes nothing; its reports are engineering input and nothing else. The class exists so that the record is graded by an outside reader before any firm’s agent reads it.';
const HOLDER = 'Program held by Allooloo Technologies Corp. · allooloo.ai';
const AI_LINE = 'Artificial intelligence makes mistakes; read the source.';

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const CSS = '*{margin:0;padding:0;box-sizing:border-box}body{background:#faf8f3;color:#1a1a1a;font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}'
  + '.container{max-width:900px;margin:0 auto;padding:32px 24px 96px}.eyebrow{text-transform:uppercase;letter-spacing:.14em;color:#6b6b6b;font-size:11px;font-weight:600;margin:0 0 10px}'
  + 'h1{font:700 28px/1.2 ui-monospace,SFMono-Regular,Menlo,monospace;margin:0 0 18px}p{margin:0 0 12px}.mission{font-size:17px;margin:18px 0 22px}a{color:#2455a3;text-decoration:none}'
  + 'footer{margin-top:64px;padding-top:28px;border-top:1px solid #d4cfc1;font-size:12px;color:#6b6b6b;line-height:1.7}@media (max-width:600px){.container{padding:24px 16px 72px}}';
const PAGE = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
  + `<title>Trader Class — Allooloo Technologies Corp.</title><meta name="description" content="${esc(HEADLINE)}"><link rel="canonical" href="${CANON}/">`
  + `<link rel="alternate" type="text/plain" href="/llms.txt" title="llms.txt"><style>${CSS}</style></head><body><main class="container">`
  + `<p class="eyebrow">${esc(EYEBROW)}</p><h1>${esc(HEADLINE)}</h1><p class="mission">${esc(BODY)}</p>`
  + `<footer><p><b>${esc(HOLDER).replace('allooloo.ai', '<a href="https://allooloo.ai">allooloo.ai</a>')}</b></p><p>${esc(AI_LINE)}</p><p>© 2027 Allooloo Technologies Corp.</p></footer>`
  + '</main></body></html>';
const LLMS = `# trader-class.ai — Trader Class\n\n${EYEBROW}\n\n> ${HEADLINE}\n\n${BODY}\n\n- Agent card: ${CANON}/.well-known/agent-card.json\n- Security: ${CANON}/.well-known/security.txt\n\n${HOLDER}\n${AI_LINE}\n`;
const CARD = {
  name: 'Trader Class', description: BODY, url: `${CANON}/`, version: VERSION,
  provider: { organization: 'Allooloo Technologies Corp.', url: 'https://allooloo.ai' },
  documentationUrl: `${CANON}/llms.txt`, capabilities: {}, defaultInputModes: [], defaultOutputModes: [],
  supportedInterfaces: [{ url: `${CANON}/`, protocolBinding: 'HTTP+JSON', protocolVersion: '1.0' }],   // AUDIT-01 F1: the program page itself
  skills: [{ id: 'read', name: 'Read the Trader Class page', description: `${HEADLINE} The page is ${CANON}/; its text for agents is ${CANON}/llms.txt.`, tags: ['reference', 'read'], examples: [`${CANON}/llms.txt`] }],
  note: 'A program page. Trader Class agents are callers of the public doors; they serve no endpoint and take no requests.',
};
const SEC = host => `Contact: https://allooloo.io/#contact\nContact: https://allooloo.io/security\nExpires: 2027-11-01T00:00:00.000Z\nPreferred-Languages: en\nCanonical: https://${host}/.well-known/security.txt\nPolicy: https://allooloo.io/security\n`;

const WMD = r => { const a = (r.headers.get('accept') || '').toLowerCase(); return a.includes('text/markdown') && (a.indexOf('text/markdown') < (a.indexOf('text/html') === -1 ? 1e9 : a.indexOf('text/html'))); };   // CLEAN-01: estate-pages' wantsMarkdown
const res = (body, type, extra = {}) => new Response(body, { headers: { 'content-type': type, 'cache-control': 'public, max-age=300', 'x-trader-class-pages': VERSION, ...extra } });
export default {
  async fetch(req) {
    const u = new URL(req.url); const host = u.hostname.toLowerCase(); const bare = host.replace(/^www\./, '');
    if (DESK.includes(bare)) return Response.redirect(`${CANON}${u.pathname === '/' ? '/' : u.pathname}${u.search}`, 301);
    if (!TWINS.includes(bare)) return new Response('not found', { status: 404 });
    if (req.method !== 'GET' && req.method !== 'HEAD') return new Response('method not allowed', { status: 405, headers: { allow: 'GET, HEAD' } });
    switch (u.pathname) {
      case '/': case '/index.html': return WMD(req) ? res(LLMS, 'text/markdown; charset=utf-8', { vary: 'Accept' }) : res(PAGE, 'text/html; charset=utf-8', { link: `<${CANON}/>; rel="canonical"`, vary: 'Accept' });   // CLEAN-01: Markdown for Agents (the page's own llms text)
      case '/llms.txt': return res(LLMS, 'text/plain; charset=utf-8');
      case '/.well-known/agent-card.json': case '/.well-known/agent.json': return res(JSON.stringify(CARD, null, 1), 'application/json; charset=utf-8');
      case '/.well-known/security.txt': case '/security.txt': return res(SEC(host), 'text/plain; charset=utf-8');
      case '/robots.txt': return res(`User-agent: *\nContent-Signal: search=yes, ai-input=yes, ai-train=yes\nAllow: /\n\nSitemap: https://${bare}/sitemap.xml\n`, 'text/plain; charset=utf-8');   // AUDIT-01 F5: names the sitemap
      case '/sitemap.xml': return res(`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n<url><loc>https://${bare}/</loc></url>\n</urlset>\n`, 'application/xml; charset=utf-8');   // AUDIT-01 F5
      default: return new Response('not found', { status: 404, headers: { 'content-type': 'text/plain; charset=utf-8' } });
    }
  },
};
