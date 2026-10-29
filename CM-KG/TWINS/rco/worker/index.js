// twins — TWINS-01 (DAY ORDER 5, 2026-10-24). One Worker per family (eco-twins · acm-twins · rco-twins; this file is copied into each family's folder,
// the family is the FAMILY var). A twin zone renders its family's page — no 301 — fetched from the canonical host at request time, and says which host is canonical:
//  · HTML: <link rel="canonical"> names the canonical URL (rewritten if the page names another), plus a Link: rel="canonical" header;
//  · JSON machine files: a top-level "canonical" field (objects only; arrays pass as they are) and the Link header;
//  · llms.txt and other text: a "Canonical: <url>" line after the title;
//  · every answer: X-Twin-Of: <canonical host>, X-Twin-Family. Machine doors are never here (pages and machine files of the page only).
const MAP = {
  eco: h => { const m = h.match(/^([a-z]{2})-eco\.(io|org|com|net)$/); if (!m) return null; return ['sm', 'xx'].includes(m[1]) ? { host: 'allooloo.ai', base: '/markets' } : { host: `${m[1]}-eco.ai`, base: '' }; },
  acm: h => { const m = h.match(/^acm-(\d{3})\.(org|com|io)$/); return m ? { host: `acm-${m[1]}.ai`, base: '' } : null; },
  rco: h => /^rco-10060\.(ai|com)$/.test(h) ? { host: 'rco-10060.org', base: '' } : null   // the family's page of record is the standard on rco-10060.org
};
const VERSION = '2026-10-24.2';   // .2: caller's user-agent, agent id and payment headers forwarded
export default {
  async fetch(request, env) {
    const url = new URL(request.url); const h = url.hostname.toLowerCase().replace(/^www\./, '');
    const fam = env.FAMILY; const c = (MAP[fam] || (() => null))(h);
    if (!c) return new Response('not a twin of this family', { status: 404 });
    if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method Not Allowed', { status: 405, headers: { allow: 'GET, HEAD' } });
    const path = (c.base && (url.pathname === '/' || url.pathname === '')) ? c.base : (c.base && !['/llms.txt', '/robots.txt', '/sitemap.xml'].includes(url.pathname) && !url.pathname.startsWith('/.well-known/') ? c.base + url.pathname : url.pathname);
    const canonical = `https://${c.host}${path}${url.search}`;
    const fh = { accept: request.headers.get('accept') || '*/*', 'user-agent': `${request.headers.get('user-agent') || 'unknown'} (via Allooloo twins)` };   // the caller stays the caller: free tier and x402 per agent
    for (const k of ['x-agent-id', 'payment-signature', 'x-payment', 'x402-pay']) { const v = request.headers.get(k); if (v) fh[k] = v; }
    const r = await fetch(canonical, { headers: fh, redirect: 'follow' });
    const hd = new Headers(r.headers); hd.delete('content-length'); hd.delete('content-encoding');
    hd.set('Link', `<${canonical}>; rel="canonical"` + (hd.get('Link') ? ', ' + hd.get('Link') : '')); hd.set('X-Twin-Of', c.host); hd.set('X-Twin-Family', fam); hd.set('X-Twins-Version', VERSION);
    const ct = hd.get('content-type') || '';
    if (request.method === 'HEAD' || r.status >= 300) return new Response(request.method === 'HEAD' ? null : r.body, { status: r.status, headers: hd });
    if (ct.includes('text/html')) {
      let t = await r.text(); const tag = `<link rel="canonical" href="${canonical}">`;
      t = /<link rel="canonical"[^>]*>/i.test(t) ? t.replace(/<link rel="canonical"[^>]*>/i, tag) : t.replace(/<\/head>/i, tag + '</head>');
      return new Response(t, { status: r.status, headers: hd });
    }
    if (ct.includes('json')) {
      const t = await r.text(); let j; try { j = JSON.parse(t); } catch (e) { return new Response(t, { status: r.status, headers: hd }); }
      if (j && typeof j === 'object' && !Array.isArray(j)) j = { canonical, twin: `https://${h}${url.pathname}`, ...j };
      return new Response(JSON.stringify(j, null, 1), { status: r.status, headers: hd });
    }
    if (ct.startsWith('text/plain') || ct.includes('markdown')) {
      let t = await r.text(); const i = t.indexOf('\n'); const line = `Canonical: ${canonical}\n`;
      t = t.startsWith('# ') && i > 0 ? t.slice(0, i + 1) + line + t.slice(i + 1) : line + t;
      return new Response(t, { status: r.status, headers: hd });
    }
    return new Response(r.body, { status: r.status, headers: hd });
  }
};
