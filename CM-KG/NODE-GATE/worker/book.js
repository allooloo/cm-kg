// book.js — BOOK-04 (2026-10-31): the market's chapter of the Book of Markets on its own node door, under /book/.
//   /book/ and /book/manifest.json   chapter version, supersedes, the five sections (version, supersedes, file, sha256 of the Book version)
//   /book/eco.json /book/acm.json /book/aio.json /book/amp.json /book/esg.json   one section each
// Served from the Book mirror (allooloocmkgapex/book, read-only SAS under the container policy book-wire-read, Worker secret BOOK_SAS) at request time,
// edge-cached BOOK_TTL seconds — a version the Monday agent writes reaches the door without a roll. Nothing is baked.
// inferred rows are left out of every file (the Book keeps them; BOOK-02: excluded from every node read); conflict rows are served as the Book holds them.
// Each file is signed by the node under kid allooloo-eco-2026-10 (Worker secret ECO_SIGNING_JWK): a detached JWS over base64url(protected) + '.' +
// base64url(canonical JSON of the file without `signature`: keys sorted at every level, compact); the node id is in the signed payload.
// Keyring: the door's own /.well-known/jwks.json (also https://<market>-eco.ai/.well-known/jwks.json).
export const ECO_KID = 'allooloo-eco-2026-10';
export const ECO_JWK_PUBLIC = { kty: 'OKP', crv: 'Ed25519', x: 'xck201IeRYKukZCIgxaSJIjGXpCspCMYa_E7AtvOO1s', kid: ECO_KID, alg: 'EdDSA', use: 'sig' };
const BLOB = 'https://allooloocmkgapex.blob.core.windows.net/book/';
const FAMS = ['ECO', 'ACM', 'AIO', 'AMP', 'ESG'];
const enc = new TextEncoder();
const b64u = buf => { let s = ''; for (const c of new Uint8Array(buf)) s += String.fromCharCode(c); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); };
const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
let KEY = null;
async function key(env) {
  if (KEY) return KEY;
  const j = JSON.parse(String(env.ECO_SIGNING_JWK).replace(/^﻿/, '').trim());
  KEY = await crypto.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: j.x, d: j.d }, { name: 'Ed25519' }, false, ['sign']);
  return KEY;
}
async function sign(env, obj, door) {
  const o = { ...obj }; delete o.signature;
  const ph = b64u(enc.encode(JSON.stringify({ alg: 'EdDSA', kid: ECO_KID })));
  const sig = await crypto.subtle.sign('Ed25519', await key(env), enc.encode(ph + '.' + b64u(enc.encode(JSON.stringify(sortDeep(o))))));
  return { ...o, signature: { alg: 'EdDSA', kid: ECO_KID, protected: ph, signature: b64u(sig), jwks: `${door}/.well-known/jwks.json`, over: "base64url(protected) + '.' + base64url(canonical JSON of the file without signature: keys sorted, compact)" } };
}
async function blob(env, ctx, name, list) {
  const u = BLOB + (list ? `?restype=container&comp=list&prefix=${encodeURIComponent(name)}` : name.split('/').map(encodeURIComponent).join('/'));
  const r = await fetch(u + (list ? '&' : '?') + String(env.BOOK_SAS).trim().replace(/^\?/, ''), { cf: { cacheTtl: Number(env.BOOK_TTL || 300), cacheEverything: true } });
  if (!r.ok) throw new Error(`book mirror ${r.status} on ${name}`);
  return list ? r.text() : r.json();
}
export async function chapter(env, ctx, cc) {   // AIO-01: also read by aio.js
  const xml = await blob(env, ctx, `${cc}/chapters/`, true);
  const vs = [...xml.matchAll(/<Name>([^<]+)<\/Name>/g)].map(m => m[1]).map(n => [Number((/\.chapter\.v(\d+)\.json$/.exec(n) || [])[1] || 0), n]).filter(x => x[0]).sort((a, b) => b[0] - a[0]);
  if (!vs.length) return null;
  const man = await blob(env, ctx, vs[0][1]); const secs = {};
  await Promise.all(man.sections.map(async ref => { secs[ref.family] = await blob(env, ctx, ref.path); }));
  return { man, path: vs[0][1], secs };
}
const noInferred = s => ({ ...s, fields: (s.fields || []).filter(f => !(f && f.inferred)) });
const J = (o, status = 200) => new Response(JSON.stringify(o, null, 1), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=300', 'access-control-allow-origin': '*', 'X-Book': 'mirror' } });
export function bookPath(p) { return p === '/book' || p.startsWith('/book/'); }
export async function serveBook(request, env, ctx, node, door) {
  const url = new URL(request.url); const p = url.pathname.replace(/\/+$/, '') || '/';
  if (request.method !== 'GET' && request.method !== 'HEAD') return J({ error: 'read-only: GET /book/manifest.json' }, 405);
  if (!env.BOOK_SAS || !env.ECO_SIGNING_JWK) return J({ error: 'book not wired on this door' }, 503);
  const cc = node.split('-')[0]; const file = p === '/book' ? 'manifest.json' : p.slice(6);
  const fam = (/^(eco|acm|aio|amp|esg)\.json$/.exec(file) || [])[1];
  if (file !== 'manifest.json' && !fam) return J({ error: 'not found', files: ['manifest.json', ...FAMS.map(f => f.toLowerCase() + '.json')].map(f => `${door}/book/${f}`) }, 404);
  let ch; try { ch = await chapter(env, ctx, cc); } catch (e) { return J({ error: String(e.message || e) }, 502); }
  if (!ch) return J({ error: `no chapter for ${cc} in the Book` }, 404);
  const m = ch.man;
  const base = { node, door, market: cc, jurisdiction_namespace: m.jurisdiction_namespace, chapter: m.version, source: 'Book of Markets mirror (allooloocmkgapex/book), read at request time' };
  if (!fam) {
    const out = { ...base, kind: 'book-manifest', schema_version: m.schema_version, chapter_id: m.chapter_id, version: m.version, supersedes: m.supersedes || null, as_of: m.as_of, produced_at: m.produced_at,
      book_path: ch.path, sections: m.sections.map(r => ({ family: r.family, section_id: r.section_id, version: r.version, supersedes: (ch.secs[r.family] || {}).supersedes || null,
        file: `${door}/book/${r.family.toLowerCase()}.json`, book_path: r.path, book_sha256: r.sha256 })),
      note: 'Each section file is the Book version named here, its inferred rows left out; conflict rows are served as the Book holds them.' };
    return J(await sign(env, out, door));
  }
  const F = fam.toUpperCase(); const ref = m.sections.find(r => r.family === F); const s = ch.secs[F];
  if (!ref || !s) return J({ error: `no ${F} section in ${m.version}` }, 404);
  const out = { ...base, kind: 'book-section', family: F, version: s.version, supersedes: s.supersedes || null, book_path: ref.path, book_sha256: ref.sha256, section: noInferred(s) };
  return J(await sign(env, out, door));
}
// the agent card gains one link: book → <door>/book/
export async function cardWithBook(resp, door) {
  if (!resp.ok || !(resp.headers.get('content-type') || '').includes('json')) return resp;
  let c; try { c = await resp.clone().json(); } catch (e) { return resp; }
  if (!c || typeof c !== 'object' || Array.isArray(c)) return resp;
  const h = new Headers(resp.headers); h.delete('content-length'); h.set('X-Book', 'card-link');
  return new Response(JSON.stringify({ ...c, book: `${door}/book/` }), { status: resp.status, headers: h });
}
