"""CM-KG APEX HEADER (CEO order 2026-09-17, item 3): X-CMR-As-Of on every apex response — the as-of date of the record served
(a tools/call result that carries as_of, or the newest as_of among resolve_issuer matches) or of the index served (the newest node as_of).
CMR headers v1 otherwise unchanged. Anchor: apex/index.js copied beside this patch as index.js.pre-asof-20260917."""
import io, os, shutil
D = r"C:\ALLOOLOO\CM-KG\DOOR\apex"; p = os.path.join(D, "index.js")
anchor = os.path.join(D, "index.js.pre-asof-20260917")
if not os.path.exists(anchor):
    shutil.copyfile(p, anchor)
s = io.open(p, encoding="utf-8").read()
if "X-CMR-As-Of" in s:
    print("already patched"); raise SystemExit
# 1 headers(): default As-Of = the index served (newest node as_of), overridable per response
old = "function headers(extra = {}) { return { 'Content-Security-Policy': CSP,"
new = ("function indexAsOf() { let m = ''; for (const n of (NODES || [])) { if (n && n.as_of && String(n.as_of) > m) m = String(n.as_of); } return m; }\n"
       "function asOfOf(obj) {  // the as-of of the record served: a result that carries as_of, or the newest among resolve_issuer matches\n"
       "  if (!obj || typeof obj !== 'object') return '';\n"
       "  if (obj.as_of) return String(obj.as_of);\n"
       "  if (obj.record && obj.record.as_of) return String(obj.record.as_of);\n"
       "  if (Array.isArray(obj.matches) && obj.matches.length) { let m = ''; for (const x of obj.matches) if (x && x.as_of && String(x.as_of) > m) m = String(x.as_of); return m; }\n"
       "  return '';\n"
       "}\n"
       "function headers(extra = {}) { const asOf = (extra && extra['X-CMR-As-Of']) || indexAsOf(); return { 'Content-Security-Policy': CSP,")
assert old in s; s = s.replace(old, new, 1)
old2 = "'X-CMR-Node': 'apex', 'X-CMR-Contact': 'CEO mk@allooloo.ai',"
new2 = "'X-CMR-Node': 'apex', 'X-CMR-As-Of': asOf, 'X-CMR-Contact': 'CEO mk@allooloo.ai',"
assert old2 in s; s = s.replace(old2, new2, 1)
s = s.replace("'Access-Control-Expose-Headers': 'X-CMR-Node, X-CMR-Source, X-CMR-Operator, X-CMR-Version, Mcp-Session-Id'",
              "'Access-Control-Expose-Headers': 'X-CMR-Node, X-CMR-As-Of, X-CMR-Source, X-CMR-Operator, X-CMR-Version, Mcp-Session-Id'", 1)
# 2 json(): accept per-response As-Of
old3 = "function json(obj, status = 200, cache = 'no-store') { return new Response(JSON.stringify(obj), { status, headers: headers({ 'content-type': 'application/json; charset=utf-8', 'cache-control': cache }) }); }"
new3 = "function json(obj, status = 200, cache = 'no-store', asOf = '') { return new Response(JSON.stringify(obj), { status, headers: headers({ 'content-type': 'application/json; charset=utf-8', 'cache-control': cache, ...(asOf ? { 'X-CMR-As-Of': asOf } : {}) }) }); }"
assert old3 in s; s = s.replace(old3, new3, 1)
# 3 /mcp: the as-of of the record served on tools/call (forwarded get_record, resolve_issuer matches); index as-of otherwise
old4 = "      return json(batch ? outs : outs[0]);"
new4 = ("      let servedAsOf = ''; for (const o of outs) { const sc = o && o.result && o.result.structuredContent; const a = asOfOf(sc); if (a > servedAsOf) servedAsOf = a; }\n"
        "      return json(batch ? outs : outs[0], 200, 'no-store', servedAsOf);")
assert old4 in s; s = s.replace(old4, new4, 1)
# 4 /record and /events forwards: the record's as-of
old5 = "const out = m[1].toLowerCase() === 'record' ? await forward(node, 'get_record', { identifier: key }) : await forward(node, 'list_events_since', { identifier: key, since: url.searchP"
i = s.index(old5); j = s.index("\n", i); line = s[i:j]
assert "return json(out" in line, line[-200:]
line2 = line.replace("return json(out", "return json(out, out && out.error ? (out.error === 'not_found' ? 404 : 503) : 200, 'no-store', asOfOf(out)", 1) if "return json(out)" in line else line
if line2 == line:
    # generic: add asOf as the 4th argument to whatever json(...) call ends the line
    k = line.rfind("return json("); close = line.rfind(")")
    line2 = line[:close] + ", " + ("asOfOf(out)" if line[k:close].count(",") >= 2 else ("200, 'no-store', asOfOf(out)" if line[k:close].count(",") == 0 else "'no-store', asOfOf(out)")) + line[close:]
s = s[:i] + line2 + s[j:]
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched; forward line now:", line2[-160:])
