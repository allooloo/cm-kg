var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// worker/signals-canon.json
var signals_canon_default = {
  source: "C:\\ALLOOLOO\\START_ME_UP\\ACM-68000_Canonical-Text_v1.1_2026-10-31.docx",
  head: [
    "ACM-68000",
    "Clearance rules and the immutable rule register \xB7 Canonical text",
    "Version 1.1 \xB7 31 October 2026 \xB7 Standard held by Allooloo Technologies Corp. \xB7 Open standard, MIT licence"
  ],
  mission: "ACM-68000 defines the clearance rule reference and signal vocabulary for listed issuers' records. Its rule register binds every rule_version used in a receipt to an immutable revision of a duty, its jurisdiction, legal reference, sources and effective dates. Each family publishes how its evidence-backed outcomes map to the clearance signals for a specified read or action. The producing node signs rule and outcome records under the ECO-10060 contract; the RCO door separately signs the receipt of the cleared read. ACM makes the governing revision and the meaning of clearance recoverable, and keeps three distinctions: lookup is not permission, missing evidence is not a negative finding, and system failure is not a resolved restriction.",
  section: "6. The clearance vocabulary",
  paragraphs: [
    "ACM-200 means cleared. It never means a listing state. A listing attribute \u2014 trading, suspended, delisted \u2014 belongs in its own field on the record. A sourced halt may be an input to a family's restriction rule; the raw listing attribute and the resolved signal remain distinct, including when both appear in one response.",
    "ACM-404 names the register and the lookup target: an absent rule revision and an absent subject registration are different failures and never share an unexplained message. ACM-451 names the required filing or evidence when known, and never disguises a service outage as a request to read."
  ],
  binding_heading: "6.1 Family binding table",
  binding_paragraphs: [
    "The bindings below are the common interpretation. Each immutable family revision supplies its own source-backed prerequisites, applicability and reason codes before a binding is applied. A listed duty name is a register seed, not a completed rule.",
    "An ESG ACM-200 clears the named check; it is not a sustainability claim. An AMP ACM-200 requires route-gate evidence; it is never produced because an endpoint is discoverable. An unresolved prerequisite stays visible: no evaluation issues ACM-200 while hiding an unmet condition. Evidence gaps, operational errors and unresolved conflicts have explicit representations, and a family uses ACM-451 only where its published binding calls for the named source to be read."
  ],
  table_head: [
    "Signal",
    "Reading",
    "Boundary"
  ],
  binding_head: [
    "Family",
    "ACM-200",
    "ACM-403",
    "ACM-404",
    "ACM-451"
  ],
  signals: {
    "ACM-200": {
      code: "ACM-200",
      reading: "Cleared",
      boundary: "The specified read or action has cleared the applicable registered checks in the stated context.",
      bindings: [
        {
          family: "Duty clearance (national and shared families)",
          outcome: "Declared action clears the duty checks"
        },
        {
          family: "AIO orderability",
          outcome: "Product, market and client-class action clears the orderability checks"
        },
        {
          family: "AMP route clearance",
          outcome: "Actor, instrument, action and endpoint clear the route gates"
        },
        {
          family: "ESG duty family",
          outcome: "The named disclosure check clears its defined criteria"
        }
      ]
    },
    "ACM-403": {
      code: "ACM-403",
      reading: "Restricted or halted",
      boundary: "Evidence establishes a restriction or an applicable halt under the selected revision.",
      bindings: [
        {
          family: "Duty clearance (national and shared families)",
          outcome: "An applicable duty condition restricts the action"
        },
        {
          family: "AIO orderability",
          outcome: "Evidence establishes a distribution or target-market restriction"
        },
        {
          family: "AMP route clearance",
          outcome: "An applicable venue restriction, entitlement failure or halt is established"
        },
        {
          family: "ESG duty family",
          outcome: "Evidence establishes a restriction under the applicable disclosure rule"
        }
      ]
    },
    "ACM-404": {
      code: "ACM-404",
      reading: "Not on the register",
      boundary: "The named lookup target is absent from the identified register. This establishes neither global absence nor prohibition.",
      bindings: [
        {
          family: "Duty clearance (national and shared families)",
          outcome: "Requested duty revision absent from the register"
        },
        {
          family: "AIO orderability",
          outcome: "Requested product or rule registration absent from its register"
        },
        {
          family: "AMP route clearance",
          outcome: "Requested venue, route or rule registration absent from its register"
        },
        {
          family: "ESG duty family",
          outcome: "Requested disclosure or rule registration absent from its register"
        }
      ]
    },
    "ACM-451": {
      code: "ACM-451",
      reading: "Read the filing",
      boundary: "The binding requires the identified filing or source to be read before a conclusion or a progression.",
      bindings: [
        {
          family: "Duty clearance (national and shared families)",
          outcome: "A specified filing must be read to complete the check"
        },
        {
          family: "AIO orderability",
          outcome: "Required product or target-market material must be read"
        },
        {
          family: "AMP route clearance",
          outcome: "Required venue notice or filing must be read"
        },
        {
          family: "ESG duty family",
          outcome: "Required disclosure material must be read"
        }
      ]
    }
  },
  reserved: [
    {
      code: "ACM-000",
      state: "reserved",
      served: false,
      reuse: "never",
      forwards_to: "https://acm-68000.org/"
    },
    {
      code: "ACM-300",
      state: "reserved",
      served: false,
      reuse: "never",
      forwards_to: "https://acm-68000.org/"
    },
    {
      code: "ACM-500",
      state: "reserved",
      served: false,
      reuse: "never",
      forwards_to: "https://acm-68000.org/"
    }
  ],
  shell: {
    style: '*{margin:0;padding:0;box-sizing:border-box}body{background:#faf8f3;color:#1a1a1a;font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}\n.container{max-width:900px;margin:0 auto;padding:32px 24px 96px}.topbar{font-size:12px;color:#6b6b6b;letter-spacing:.04em;margin-bottom:14px}\n.eyebrow{text-transform:uppercase;letter-spacing:.14em;color:#6b6b6b;font-size:11px;font-weight:600;margin:0 0 10px}h1{font:700 28px/1.2 ui-monospace,SFMono-Regular,Menlo,monospace;margin:0 0 4px}\nh1 .host{display:block;font-size:14px;color:#c84a1e;font-weight:600;margin-top:6px}h2{font-size:18px;font-weight:700;margin:34px 0 12px;padding-bottom:8px;border-bottom:2px solid #c84a1e}\nh3{font-size:15px;margin:22px 0 8px}p{margin:0 0 12px}.mission{font-size:17px;margin:18px 0 22px}.arrow{font-family:ui-monospace,monospace;font-size:13px;background:#f3eee0;padding:12px 14px;border-radius:4px}\n.meta{font-size:13px;color:#6b6b6b}table{width:100%;border-collapse:collapse;font-size:13px;margin:12px 0 24px}th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #d4cfc1;vertical-align:top;overflow-wrap:anywhere}\nth{background:#f3eee0;font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:.04em}a{color:#2455a3;text-decoration:none}code,.mono{font-family:ui-monospace,monospace;font-size:13px}\n.surfaces{font-family:ui-monospace,monospace;font-size:12px;background:#1a1a1a;color:#f3eee0;padding:16px 20px;border-radius:4px;margin:12px 0 24px;white-space:pre-wrap;overflow-x:auto;line-height:1.7}\n.ok{color:#2e7d32;font-weight:700}.bad{color:#c62828;font-weight:700}footer{margin-top:64px;padding-top:28px;border-top:1px solid #d4cfc1;font-size:12px;color:#6b6b6b;line-height:1.7}\nform{display:grid;gap:6px;max-width:520px}form input,form textarea{font:inherit;padding:8px;border:1px solid #d4cfc1;border-radius:3px;background:#fff}form button{justify-self:start;padding:9px 16px;border:0;border-radius:3px;background:#c84a1e;color:#f3eee0}.hp{display:none}\n@media (max-width:600px){.container{padding:24px 16px 72px}th,td{padding:7px}}',
    topbar: "Standard held by Allooloo Technologies Corp. \xB7 Open standard, MIT licence.",
    footer: '<footer><p><b>Standard held by Allooloo Technologies Corp. \xB7 Open standard, MIT licence.</b></p><p class="stack"><a href="https://eco-10060.org/">ECO-10060</a> \xB7 <a href="https://sm-eco-10060.org/">SM-ECO-10060</a> \xB7 <a href="https://acm-68000.org/">ACM-68000</a> \xB7 <a href="https://aio-10060.org/">AIO-10060</a> \xB7 <a href="https://amp-10060.org/">AMP-10060</a> \xB7 <a href="https://rco-10060.org/">RCO-10060</a> \xB7 <a href="https://cpg-68000.ai/">CPG-68000</a> \xB7 <a href="https://cpg-68000.org/stack/1.json">stack version</a></p><p>RCO is the Record of Cleared Orders. Artificial intelligence makes mistakes; read the source.</p><p>\xA9 2026 Allooloo Technologies Corp.</p></footer>'
  }
};

// worker/acm_first.js
var ACM_EXPANSION = "Agent Clearance Manifest";
var WROTE = /ACM-68000\s*(?:\(\s*|·\s*|<\/[a-z]+>\s*·\s*)Agent Clearance Manifest/;
function insertAt(t, i) {
  const after = t.slice(i + 9);
  if (/^\s*\(/.test(after)) {
    const m = /^\s*\(/.exec(after);
    return t.slice(0, i + 9) + m[0] + ACM_EXPANSION + " \u2014 " + after.slice(m[0].length);
  }
  return t.slice(0, i + 9) + " (" + ACM_EXPANSION + ")" + after;
}
__name(insertAt, "insertAt");
function acmFirst(t, kind) {
  if (typeof t !== "string" || !t.includes("ACM-68000")) return t;
  if (kind !== "html") {
    if (WROTE.test(t.slice(0, t.indexOf("ACM-68000") + 60))) return t;
    return insertAt(t, t.indexOf("ACM-68000"));
  }
  const b = t.search(/<body[\s>]/i);
  let i = b < 0 ? 0 : b;
  const re = /<(script|style|title)\b[\s\S]*?<\/\1>|<p class="mission"[\s\S]*?<\/p>|<[^>]*>|ACM-68000/gi;
  re.lastIndex = i;
  let m;
  while (m = re.exec(t)) {
    if (m[0] === "ACM-68000") {
      if (WROTE.test(t.slice(m.index, m.index + 60))) return t;
      return insertAt(t, m.index);
    }
  }
  return t;
}
__name(acmFirst, "acmFirst");

// worker/index.js
var VERSION = "2026-10-31.1";
var STANDARD = "https://acm-68000.org/";
var REGISTER = "https://acm-68000.org/register.json";
var RESOLVER = "https://mcp.getissuer.ai/mcp";
var LIVE = Object.keys(signals_canon_default.signals).map((c) => c.slice(4));
var RESERVED = signals_canon_default.reserved.map((r) => r.code.slice(4));
var esc = /* @__PURE__ */ __name((s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]), "esc");
var SEC = { "x-content-type-options": "nosniff", "x-frame-options": "DENY", "strict-transport-security": "max-age=31536000; includeSubDomains", "X-ACM-Version": VERSION };
var J = /* @__PURE__ */ __name((o, status = 200) => new Response(JSON.stringify(o, null, 1) + "\n", { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=300", "access-control-allow-origin": "*", ...SEC } }), "J");
var T = /* @__PURE__ */ __name((t, ct = "text/plain; charset=utf-8") => new Response(acmFirst(t, "text"), { headers: { "content-type": ct, "cache-control": "public, max-age=300", ...SEC } }), "T");
var R301 = /* @__PURE__ */ __name((to) => new Response(null, { status: 301, headers: { location: to, "cache-control": "public, max-age=3600", ...SEC } }), "R301");
var table = /* @__PURE__ */ __name((head, rows) => `<table><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`, "table");
var VER = (/Version (\d+\.\d+)/.exec(signals_canon_default.head[2]) || [])[1];
function sig(code) {
  const s = signals_canon_default.signals["ACM-" + code];
  return { standard: "ACM-68000", expansion: "Agent Clearance Manifest", standard_version: VER, signal: s.code, reading: s.reading, boundary: s.boundary, bindings: s.bindings, standard_page: STANDARD, register: REGISTER, resolver: RESOLVER, reserved: signals_canon_default.reserved };
}
__name(sig, "sig");
function page(code, host) {
  const s = signals_canon_default.signals["ACM-" + code];
  const body = `<p class="eyebrow">ACM-68000 \xB7 ${esc(signals_canon_default.section)}</p><h1>${esc(s.code)} \xB7 ${esc(s.reading)}<span class="host">${esc(host)}</span></h1><p class="mission"><b>${esc(signals_canon_default.mission)}</b></p><h2>${esc(signals_canon_default.section)}</h2>` + table(signals_canon_default.table_head, [[s.code, s.reading, s.boundary]]) + signals_canon_default.paragraphs.map((t) => `<p>${esc(t)}</p>`).join("") + `<h2>${esc(signals_canon_default.binding_heading)}</h2>` + table(["Family", s.code], s.bindings.map((b) => [b.family, b.outcome])) + signals_canon_default.binding_paragraphs.map((t) => `<p>${esc(t)}</p>`).join("") + `<h2>Machine surfaces</h2><p class="meta"><a href="/signal.json">/signal.json</a> \xB7 <a href="/signals.json">/signals.json</a> \xB7 <a href="/llms.txt">/llms.txt</a> \xB7 <a href="/.well-known/agent-card.json">/.well-known/agent-card.json</a> \xB7 <a href="${STANDARD}">acm-68000.org</a> \xB7 <a href="${REGISTER}">register.json</a> \xB7 get_signal at <a href="${RESOLVER}">${RESOLVER.replace("https://", "")}</a></p>`;
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(s.code)} \xB7 ${esc(s.reading)} \u2014 ACM-68000</title><meta name="description" content="${esc(s.code)} \xB7 ${esc(s.reading)}: ${esc(s.boundary)}"><link rel="canonical" href="https://${esc(host)}/"><style>${signals_canon_default.shell.style}</style></head><body><div class="container"><div class="topbar">${signals_canon_default.shell.topbar}</div>${body}${signals_canon_default.shell.footer}</div></body></html>`;
  return acmFirst(html, "html");
}
__name(page, "page");
function llms(code, host) {
  const s = signals_canon_default.signals["ACM-" + code];
  return `# ${host} \u2014 ${s.code} \xB7 ${s.reading}

${signals_canon_default.mission}

${signals_canon_default.section}
${s.code} \xB7 ${s.reading} \u2014 ${s.boundary}

${signals_canon_default.paragraphs.join("\n\n")}

${signals_canon_default.binding_heading}
${s.bindings.map((b) => `- ${b.family}: ${b.outcome}`).join("\n")}

${signals_canon_default.binding_paragraphs.join("\n\n")}

Standard: ${STANDARD} \xB7 register: ${REGISTER} \xB7 get_signal: ${RESOLVER}

${signals_canon_default.shell.topbar.replace(/<[^>]+>/g, "")}
`;
}
__name(llms, "llms");
var index_default = {
  async fetch(request) {
    const url = new URL(request.url);
    let host = url.hostname.toLowerCase();
    if (host.startsWith("www.")) host = host.slice(4);
    const m = host.match(/^acm-(\d{3})\.(ai|org|com|io)$/);
    if (!m) return J({ error: "not_found" }, 404);
    const [, code, tld] = m;
    if (RESERVED.includes(code)) return R301(STANDARD);
    if (!LIVE.includes(code)) return J({ error: "not_found", host }, 404);
    if (tld !== "ai") return R301(`https://acm-${code}.ai${url.pathname}${url.search}`);
    const p = url.pathname;
    const me = `https://${host}/`;
    if (p === "/" || p === "/index.html") return new Response(page(code, host), { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=300", ...SEC } });
    if (p === "/signal.json") return J(sig(code));
    if (p === "/signals.json") return J({ standard: "ACM-68000", expansion: "Agent Clearance Manifest", standard_version: VER, source: `ACM-68000 canonical text v${VER} \xA76`, signals: Object.values(signals_canon_default.signals).map((s) => ({ code: s.code, reading: s.reading, boundary: s.boundary, page: `https://acm-${s.code.slice(4)}.ai/` })), reserved: signals_canon_default.reserved, standard_page: STANDARD });
    if (p === "/llms.txt" || p === "/index.md") return T(llms(code, host), p === "/index.md" ? "text/markdown; charset=utf-8" : "text/plain; charset=utf-8");
    if (p === "/.well-known/agent-card.json") {
      const s = signals_canon_default.signals["ACM-" + code];
      return J({ protocolVersion: "0.3.0", name: `${s.code} \xB7 ${s.reading}`, description: `${s.code} \xB7 ${s.reading}: ${s.boundary}`, url: me, provider: { organization: "Allooloo Technologies Corp.", url: "https://allooloo.io" }, holder: "Allooloo Technologies Corp.", licence: "MIT", standard: "ACM-68000", expansion: "Agent Clearance Manifest", documentationUrl: me + "llms.txt", kind: "reference surface (serves no tools)", capabilities: { streaming: false, pushNotifications: false }, defaultInputModes: ["application/json"], defaultOutputModes: ["application/json", "text/plain"], skills: [] });
    }
    if (p === "/health.json") return J({ status: "ok", host, version: VERSION, signal: "ACM-" + code });
    if (p === "/robots.txt") return T(`User-agent: *
Allow: /
Sitemap: ${me}sitemap.xml
`);
    if (p === "/sitemap.xml") return T(`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${["", "signal.json", "signals.json", "llms.txt"].map((x) => `<url><loc>${me}${x}</loc></url>`).join("")}</urlset>
`, "application/xml");
    if (p === "/.well-known/security.txt") return T(`Contact: https://allooloo.io/#contact
Contact: https://allooloo.io/security
Expires: 2027-10-31T00:00:00Z
Preferred-Languages: en
Canonical: ${me}.well-known/security.txt
`);
    return J({ error: "not_found", host, paths: ["/", "/signal.json", "/signals.json", "/llms.txt", "/index.md", "/health.json", "/.well-known/agent-card.json", "/.well-known/security.txt", "/robots.txt", "/sitemap.xml"] }, 404);
  }
};
export {
  index_default as default
};

