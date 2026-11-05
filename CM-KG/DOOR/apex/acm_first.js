// acm_first.js — TEXTS-01 (2026-10-31), ACM-68000 v1.1 ruling: the expansion is Agent Clearance Manifest, written out once on first use on every surface
// that spells it. acmFirst(text, kind) writes it after the first "ACM-68000" a reader sees — in HTML the first one in the body text (not in a tag, a URL
// or <title>); in plain text and Markdown the first one in the file. "ACM-68000 (…" becomes "ACM-68000 (Agent Clearance Manifest — …" so a following
// parenthesis is not doubled. One copy per Worker folder (the same bytes everywhere: SITE\TEXTS-01\acm_first.js).
// READ-01 (2026-10-31): written once per page — a page that already carries the expansion anywhere in its body is left as it is. Never written inside
// the mono arrow (class="arrow"; in text, a line with →), inside a table whose Expansion column carries it, or in the h1 title line (in text, the "# "
// line); where an earlier pass wrote it there, it is taken out. First-use prose keeps it.
export const ACM_EXPANSION = 'Agent Clearance Manifest';
const EXP = ACM_EXPANSION;
function insertAt(t, i) {
  const after = t.slice(i + 9);
  if (/^\s*\(/.test(after)) { const m = /^\s*\(/.exec(after); return t.slice(0, i + 9) + m[0] + EXP + ' — ' + after.slice(m[0].length); }
  return t.slice(0, i + 9) + ' (' + EXP + ')' + after;
}
const unwrite = z => z.replace(/ACM-68000(\s*)\(Agent Clearance Manifest — /g, 'ACM-68000$1(').replace(/ACM-68000 \(Agent Clearance Manifest\)/g, 'ACM-68000');
const ARROW = '<(p|div|pre|span|code)\\b[^>]*\\bclass="[^"]*\\barrow\\b[^"]*"[^>]*>[\\s\\S]*?<\\/\\2>';
const ZONES = new RegExp('<(script|style|title)\\b[\\s\\S]*?<\\/\\1>|<p class="mission"[\\s\\S]*?<\\/p>|' + ARROW + '|<table\\b[\\s\\S]*?<\\/table>|<h1\\b[\\s\\S]*?<\\/h1>', 'gi');
const expTable = z => /^<table/i.test(z) && /<th\b[^>]*>\s*Expansion\s*<\/th>/i.test(z);
const isZone = z => /^<table/i.test(z) ? expTable(z) : /^<h1\b/i.test(z) || new RegExp('^' + ARROW.replace('\\2', '\\1'), 'i').test(z);
function html(t) {
  const b = Math.max(0, t.search(/<body[\s>]/i)); const head = t.slice(0, b);
  const body = t.slice(b).replace(ZONES, z => isZone(z) ? unwrite(z) : z);
  if (body.replace(/<(script|style)\b[\s\S]*?<\/\1>/gi, '').includes(EXP)) return head + body;   // once per page
  const re = new RegExp(ZONES.source + '|<[^>]*>|ACM-68000', 'gi'); let m;   // a mission paragraph is verbatim canonical text: never touched
  while ((m = re.exec(body))) {
    if (/^<table/i.test(m[0]) && !expTable(m[0])) { re.lastIndex = m.index + 6; continue; }   // an ordinary table: walk its cells
    if (m[0] === 'ACM-68000') return head + insertAt(body, m.index);
  }
  return head + body;
}
function text(t) {
  const L = t.split('\n'); const zone = L.map(l => l.includes('→') || /^#\s/.test(l));
  for (let i = 0; i < L.length; i++) if (/^\s*\|/.test(L[i]) && (i === 0 || !/^\s*\|/.test(L[i - 1])) && /\bExpansion\b/.test(L[i])) for (let k = i; k < L.length && /^\s*\|/.test(L[k]); k++) zone[k] = true;
  for (let i = 0; i < L.length; i++) if (zone[i]) L[i] = unwrite(L[i]);
  const s = L.join('\n'); if (s.includes(EXP)) return s;   // once per file
  let off = 0;
  for (let i = 0; i < L.length; i++) { const k = zone[i] ? -1 : L[i].indexOf('ACM-68000'); if (k >= 0) return insertAt(s, off + k); off += L[i].length + 1; }
  return s;
}
export function acmFirst(t, kind) {
  if (typeof t !== 'string' || !t.includes('ACM-68000')) return t;
  return kind === 'html' ? html(t) : text(t);
}
export async function acmFirstResponse(resp) {
  const ct = (resp.headers.get('content-type') || '').toLowerCase();
  const kind = ct.includes('text/html') ? 'html' : (ct.includes('text/plain') || ct.includes('markdown')) ? 'text' : null;
  if (!kind || !resp.ok) return resp;
  const t = await resp.text(); const o = acmFirst(t, kind);
  const h = new Headers(resp.headers); h.delete('content-length'); if (o !== t) h.set('X-ACM-First-Use', 'written');
  return new Response(o, { status: resp.status, statusText: resp.statusText, headers: h });
}
