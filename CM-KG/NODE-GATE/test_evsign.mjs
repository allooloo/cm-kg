// SHELF-01 fix (2026-10-27) — local test of signEvents: signs a sample events response with the CMR key (read in-process from AGENT KEYS, never printed)
// and verifies every line against the public key of record (NODE-SIGN\cmr-signing.pub.jwk.json). Usage: node test_evsign.mjs
import { readFileSync } from 'node:fs';
import { signEvents } from './worker/cmrsign.js';
const env = { CMR_SIGNING_JWK: readFileSync('C:/ALLOOLOO/AGENT KEYS/cmr-signing-jwk.txt', 'utf8') };
const pub = JSON.parse(readFileSync('C:/ALLOOLOO/CM-KG/NODE-SIGN/cmr-signing.pub.jwk.json', 'utf8'));
const sample = { cmr: 'ca-cm-kg/TSX/SHOP', total: 2, events: [{ date: '2026-10-22', event_type: 'newswire_release', title: 'A', url: 'https://example.org/a' }, { date: '2026-10-01', event_type: 'financial_statement', title: 'B', url: 'https://example.org/b' }] };
const out = await signEvents(env, sample);
const sortDeep = v => Array.isArray(v) ? v.map(sortDeep) : (v && typeof v === 'object') ? Object.fromEntries(Object.keys(v).sort().map(k => [k, sortDeep(v[k])])) : v;
const b64u = buf => Buffer.from(buf).toString('base64url');
const k = await crypto.subtle.importKey('jwk', { kty: 'OKP', crv: 'Ed25519', x: (pub.keys ? pub.keys[0] : pub).x }, { name: 'Ed25519' }, false, ['verify']);
let ok = 0;
for (const e of out.events) {
  const s = e.signature; const body = { ...e }; delete body.signature;
  const v = await crypto.subtle.verify('Ed25519', k, Buffer.from(s.signature, 'base64url'), new TextEncoder().encode(s.protected + '.' + b64u(new TextEncoder().encode(JSON.stringify(sortDeep(body))))));
  ok += v ? 1 : 0; console.log(e.cmr, e.date, s.kid, v ? 'VERIFIED' : 'FAILED');
}
console.log(`${ok}/${out.events.length} lines verify · events_signed ${out.events_signed}`);
