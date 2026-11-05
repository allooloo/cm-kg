// stampclass.js — BOOK-05 part 1 (CEO, 2026-10-31): instrument_class on the record (ECO-10060 v1.2 §7.1, record schema v0.2), stamped here before the record
// is signed. BOOK-06 (CEO 2026-11-01), in this order:
//   1. register — where the instrument reference register (ESMA FIRDS) holds the record's ISIN: the ISO 10962 category name its CFI states, sourced to the
//      register entry with its publication date (EU records; uk instruments reported to ESMA FIRDS — the FCA's own FIRDS API needs a registered key);
//   2. the record's own CFI (identity.cfi, read from FIRDS by the node) where the register lookup holds no entry: the ISO 10962 name, the record field's source;
//   3. rulebook — the listing regime's class for the record's listing group (classes.py): exchange | CFI category or listing group, else *;
//   4. not_found, with the pages checked.
// Schema v0.2 unchanged. One copy per Worker folder (gate, apex).
import { CLASSES, CFI, ISO10962 } from './classes.js';
export const RECORD_SCHEMA = 'ECO-10060 v1.2 §7.1 · record schema v0.2 (unratified)';
const val = (i, k) => (i && i[k] && typeof i[k] === 'object') ? i[k].value : null;
const iso = c => c ? (ISO10962[String(c).slice(0, 2).toUpperCase()] || ISO10962[String(c).slice(0, 1).toUpperCase()] || null) : null;
export function groupKey(rec) {
  const i = rec.identity || {}; const ex = String(val(i, 'exchange') || '').toLowerCase().trim();
  const cfi = val(i, 'cfi'); const g = cfi ? 'CFI:' + String(cfi).slice(0, 2).toUpperCase() : (val(i, 'sub_category') || val(i, 'security_type') || '*');
  return `${ex}|${g}`;
}
export function stampClass(rec) {
  if (!rec || typeof rec !== 'object' || Array.isArray(rec) || !rec.cmr) return rec;
  const i = rec.identity || {}; const isin = String(val(i, 'isin') || '').toUpperCase(); const node = rec.node || String(rec.cmr).split('/')[0];
  const reg = isin && CFI[isin]; const own = val(i, 'cfi'); let ic;
  if (reg && reg.iso) ic = { value: reg.iso, from: `ISO 10962 CFI ${reg.cfi} — ${reg.register} entry for ${isin}${reg.mic ? ' (MIC ' + reg.mic + ')' : ''}`, cfi: reg.cfi, source_url: reg.url, source_date: reg.date, state: 'sourced', basis: 'register' };
  else if (own && iso(own)) ic = { value: iso(own), from: `ISO 10962 CFI ${own} — the record's own CFI (identity.cfi)`, cfi: own, source_url: (i.cfi && i.cfi.source_url) || null, source_date: null, state: 'sourced', basis: 'record_cfi' };
  else {
    const k = groupKey(rec); const t = CLASSES[node]; const g = t && t[k];
    ic = g && g.class ? { value: g.class, from: g.from || null, source_url: g.source_url, source_date: g.source_date, read_at: g.read_at, state: 'sourced', basis: 'rulebook', group: k }
      : { value: null, state: 'not_found', group: k, pages_checked: (g && g.pages_checked) || [], reason: g ? 'no register CFI for this instrument, and no page of the listing regime stated the class of its listing group' : 'no register CFI for this instrument, and its listing group was not read' };
  }
  return { ...rec, schema: RECORD_SCHEMA, instrument_class: ic };
}
