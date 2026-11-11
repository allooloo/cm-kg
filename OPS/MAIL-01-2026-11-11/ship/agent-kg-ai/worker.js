var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// worker/x402.js
var X402 = {
  origin: "https://agent-kg.ai",
  operator: "Agentic KG Holdings",
  office: "Agentic Private Office \u2014 Matthew Keddy",
  network: "eip155:8453",
  // Base mainnet
  asset: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  // USDC on Base
  assetName: "USD Coin",
  // EIP-712 domain name of the USDC contract on Base mainnet
  eip712Version: "2",
  amount: "10000",
  // $0.01 in USDC (6 decimals)
  amountUsdc: "0.01",
  facilitator: "https://api.cdp.coinbase.com/platform/v2/x402",
  explorer: "https://basescan.org/tx/",
  kid: "mk-office-x402-2026-09",
  maxTimeoutSeconds: 60
};
var DESCRIPTION = "A signed statement of the office's current holdings summary for $0.01 USDC \u2014 Agentic Private Office \u2014 Matthew Keddy: shareholdings, hyperscaler tenancies, keys and as-of, drawn from /facts.json and signed EdDSA (kid mk-office-x402-2026-09), with a receipt that resolves forever at /x402/receipt/{nonce}.";
var b64 = /* @__PURE__ */ __name((o) => btoa(unescape(encodeURIComponent(JSON.stringify(o)))), "b64");
var unb64 = /* @__PURE__ */ __name((s) => JSON.parse(decodeURIComponent(escape(atob(s)))), "unb64");
var b64uBuf = /* @__PURE__ */ __name((buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""), "b64uBuf");
var b64uStr = /* @__PURE__ */ __name((s) => b64uBuf(new TextEncoder().encode(s)), "b64uStr");
var unb64u = /* @__PURE__ */ __name((s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4)), (c) => c.charCodeAt(0)), "unb64u");
var hex = /* @__PURE__ */ __name((n) => Array.from(crypto.getRandomValues(new Uint8Array(n)), (b) => b.toString(16).padStart(2, "0")).join(""), "hex");
var X402_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS",
  "access-control-allow-headers": "PAYMENT-SIGNATURE, X-PAYMENT, Content-Type",
  "access-control-expose-headers": "PAYMENT-REQUIRED, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE, X-X402-Receipt"
};
function requirements(env) {
  return {
    scheme: "exact",
    network: X402.network,
    amount: X402.amount,
    maxAmountRequired: X402.amount,
    asset: X402.asset,
    payTo: env.X402_PAYTO,
    maxTimeoutSeconds: X402.maxTimeoutSeconds,
    resource: `${X402.origin}/api`,
    description: DESCRIPTION,
    mimeType: "application/json",
    extra: { name: X402.assetName, version: X402.eip712Version }
  };
}
__name(requirements, "requirements");
function bazaar() {
  return {
    bazaar: {
      info: {
        input: { type: "http", method: "GET" },
        output: {
          type: "json",
          example: {
            receipt: { receipt_url: `${X402.origin}/x402/receipt/{nonce}`, settled: true, amount_usdc: "0.01", network: X402.network },
            statement: "<EdDSA JWT over data, kid mk-office-x402-2026-09>",
            data: { office: "Agentic Private Office \u2014 Matthew Keddy", holdings: [{ name: "wefetch", url: "https://wefetch.ai/" }] }
          }
        }
      },
      schema: {
        $schema: "https://json-schema.org/draft/2020-12/schema",
        type: "object",
        properties: {
          input: { type: "object", properties: { type: { type: "string", const: "http" }, method: { type: "string", enum: ["GET", "HEAD"] } }, required: ["type", "method"] },
          output: { type: "object", properties: { type: { type: "string" }, example: { type: "object" } } }
        },
        required: ["input"]
      }
    }
  };
}
__name(bazaar, "bazaar");
var OUSD = { asset: "0xB2000000000000000000002fEb517dFeC7415344", name: "OpenUSD", version: "1" };
var EIP2612_GAS_SPONSORING = { eip2612GasSponsoring: { info: { description: "The facilitator accepts EIP-2612 gasless Permit to Permit2 canonical contract.", version: "1" }, schema: { type: "object" } } };
function accepts(env) {
  const usdc = requirements(env);
  return [usdc, { ...usdc, asset: OUSD.asset, payTo: env.X402_PAYTO_OUSD || env.X402_PAYTO, extra: { assetTransferMethod: "permit2", name: OUSD.name, version: OUSD.version } }];
}
__name(accepts, "accepts");
async function handleSettled(env) {
  const out = { zone: new URL(X402.origin).hostname, settled: 0, last_tx: null, last_receipt: null, last_at: null, as_of: (/* @__PURE__ */ new Date()).toISOString(), network: X402.network, asset: "USDC, OUSD", door: `${X402.origin}/x402` };
  try {
    out.settled = parseInt(await env.OFFICE_X402.get("x402:count") || "0", 10);
    const l = await env.OFFICE_X402.get("x402:last", "json");
    if (l) {
      out.last_tx = l.transaction || null;
      out.last_receipt = l.receipt || null;
      out.last_at = l.at || null;
    }
  } catch {
    return new Response(JSON.stringify({ error: "register unavailable" }), { status: 503, headers: X402_HEADERS });
  }
  return new Response(JSON.stringify(out, null, 1), { status: 200, headers: X402_HEADERS });
}
__name(handleSettled, "handleSettled");
function paymentRequired(env, error) {
  const req = requirements(env);
  const body = {
    x402Version: 2,
    error: error || `Payment required: $0.01 USDC on ${req.network}`,
    accepts: accepts(env),
    resource: { url: req.resource, description: req.description, mimeType: req.mimeType },
    extensions: { ...bazaar(), ...EIP2612_GAS_SPONSORING },
    free_route: `${X402.origin}/facts.json`,
    receipts: { jwks: `${X402.origin}/x402/jwks.json`, kid: X402.kid, resolve: `${X402.origin}/x402/receipt/{nonce}` },
    operator: X402.operator
  };
  return new Response(JSON.stringify(body, null, 1), { status: 402, headers: { ...X402_HEADERS, "PAYMENT-REQUIRED": b64(body) } });
}
__name(paymentRequired, "paymentRequired");
async function cdpJwt(env, method, host, path) {
  const id = env.CDP_API_KEY_ID, secret = env.CDP_API_KEY_SECRET;
  if (!id || !secret) return null;
  const now = Math.floor(Date.now() / 1e3);
  const claims = { sub: id, iss: "cdp", aud: ["cdp_service"], nbf: now, exp: now + 120, uris: [`${method} ${host}${path}`] };
  let alg, key, sigAlg;
  if (secret.includes("BEGIN")) {
    const der = Uint8Array.from(atob(secret.replace(/-----[^-]+-----/g, "").replace(/\s+/g, "")), (c) => c.charCodeAt(0));
    alg = "ES256";
    key = await crypto.subtle.importKey("pkcs8", der, { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
    sigAlg = { name: "ECDSA", hash: "SHA-256" };
  } else {
    const raw = Uint8Array.from(atob(secret), (c) => c.charCodeAt(0));
    alg = "EdDSA";
    key = await importEd25519Seed(raw.slice(0, 32));
    sigAlg = { name: "Ed25519" };
  }
  const h = b64uStr(JSON.stringify({ alg, kid: id, typ: "JWT", nonce: hex(16) }));
  const p = b64uStr(JSON.stringify(claims));
  const sig = await crypto.subtle.sign(sigAlg, key, new TextEncoder().encode(`${h}.${p}`));
  return `${h}.${p}.${b64uBuf(sig)}`;
}
__name(cdpJwt, "cdpJwt");
function importEd25519Seed(seed) {
  const pkcs8 = new Uint8Array([48, 46, 2, 1, 0, 48, 5, 6, 3, 43, 101, 112, 4, 34, 4, 32, ...seed]);
  return crypto.subtle.importKey("pkcs8", pkcs8, { name: "Ed25519" }, false, ["sign"]);
}
__name(importEd25519Seed, "importEd25519Seed");
async function facilitator(env, path, body) {
  const base = env.X402_FACILITATOR || X402.facilitator;
  const u = new URL(base + path);
  const h = { "content-type": "application/json", accept: "application/json" };
  if (u.hostname.endsWith("coinbase.com")) {
    const jwt = await cdpJwt(env, "POST", u.hostname, u.pathname);
    if (jwt) h["Authorization"] = "Bearer " + jwt;
  }
  try {
    const r = await fetch(u.toString(), { method: "POST", headers: h, body: JSON.stringify(body), signal: AbortSignal.timeout(3e4) });
    let j = null;
    try {
      j = await r.json();
    } catch {
      j = { error: "facilitator answered " + r.status };
    }
    return { status: r.status, body: j };
  } catch (e) {
    return { status: 0, body: { error: "facilitator unreachable" } };
  }
}
__name(facilitator, "facilitator");
async function signReceipt(env, claims) {
  const key = await importEd25519Seed(unb64u(env.X402_RECEIPT_SEED));
  const h = b64uStr(JSON.stringify({ alg: "EdDSA", typ: "JWT", kid: X402.kid }));
  const p = b64uStr(JSON.stringify(claims));
  const sig = await crypto.subtle.sign({ name: "Ed25519" }, key, new TextEncoder().encode(`${h}.${p}`));
  return `${h}.${p}.${b64uBuf(sig)}`;
}
__name(signReceipt, "signReceipt");
async function signStatement(env, claims) {
  return signReceipt(env, claims);
}
__name(signStatement, "signStatement");
function holdingsSummary(facts) {
  return {
    office: facts.office,
    principal: facts.principal,
    canonical: facts.canonical,
    holdings: facts.holdings,
    tenancies: facts.tenancies,
    tenancies_line: facts.tenancies_line,
    keys: facts.keys,
    entity: facts.entity,
    as_of: facts.as_of,
    surface_version: facts.surface_version
  };
}
__name(holdingsSummary, "holdingsSummary");
function preflight() {
  return new Response(null, { status: 204, headers: X402_HEADERS });
}
__name(preflight, "preflight");
async function handleApi(request, env, loadFacts) {
  if (!env.X402_PAYTO) {
    return new Response(
      JSON.stringify({ error: "receiver_not_configured", note: "the pay-to address (Worker secret X402_PAYTO) is not set; the CEO places it at AGENT KEYS\\x402-payto.txt", free_route: `${X402.origin}/facts.json` }, null, 1),
      { status: 503, headers: X402_HEADERS }
    );
  }
  const sig = request.headers.get("PAYMENT-SIGNATURE") || request.headers.get("X-PAYMENT");
  if (!sig) return paymentRequired(env);
  let payload;
  try {
    payload = unb64(sig);
  } catch {
    return paymentRequired(env, "PAYMENT-SIGNATURE is not base64 JSON");
  }
  const chosen = String(payload.accepted && payload.accepted.asset || "").toLowerCase();
  const offered = accepts(env);
  const req = offered.find((a) => a.asset.toLowerCase() === chosen) || offered[0];
  const v = await facilitator(env, "/verify", { x402Version: payload.x402Version || 2, paymentPayload: payload, paymentRequirements: req });
  if (!(v.body && v.body.isValid)) {
    return paymentRequired(env, "payment not valid: " + (v.body && (v.body.invalidReason || v.body.error) || v.status));
  }
  const facts = await loadFacts();
  const data = holdingsSummary(facts);
  const s = await facilitator(env, "/settle", { x402Version: payload.x402Version || 2, paymentPayload: payload, paymentRequirements: req });
  const settled = !!(s.body && (s.body.success || s.body.transaction || s.body.txHash));
  const tx = s.body && (s.body.transaction || s.body.txHash) || null;
  const now = Math.floor(Date.now() / 1e3);
  const nonce = hex(16);
  const payer = s.body && s.body.payer || payload.payload && payload.payload.authorization && payload.payload.authorization.from || payload.payload && payload.payload.permit2Authorization && payload.payload.permit2Authorization.from || "payer";
  const claims = {
    iss: X402.origin,
    sub: payer,
    jti: nonce,
    iat: now,
    resource: req.resource,
    scheme: "exact",
    standard: req.asset === OUSD.asset ? "Permit2 permitWitnessTransferFrom" : "EIP-3009 transferWithAuthorization",
    network: req.network,
    asset: req.asset,
    amount: req.amount,
    amount_usdc: X402.amountUsdc,
    payTo: req.payTo,
    transaction: tx,
    explorer: tx ? X402.explorer + tx : null,
    settled,
    facilitator: env.X402_FACILITATOR || X402.facilitator,
    receipt_url: `${X402.origin}/x402/receipt/${nonce}`,
    operator: X402.operator
  };
  let jwt = null, statement = null;
  try {
    jwt = await signReceipt(env, claims);
  } catch {
    jwt = null;
  }
  try {
    statement = await signReceipt(env, { iss: X402.origin, iat: now, jti: nonce, typ: "holdings-summary", statement: data });
  } catch {
    statement = null;
  }
  const receipt = { ...claims, jwt, kid: X402.kid, jwks: `${X402.origin}/x402/jwks.json` };
  try {
    await env.OFFICE_X402.put(`x402:receipt:${nonce}`, JSON.stringify(receipt));
  } catch {
  }
  try {
    if (settled) {
      const c = parseInt(await env.OFFICE_X402.get("x402:count") || "0", 10) + 1;
      await env.OFFICE_X402.put("x402:count", String(c));
      await env.OFFICE_X402.put("x402:last", JSON.stringify({ x402Version: 2, success: true, transaction: tx, network: req.network, amount: req.amount, asset: req.asset, payer, explorer: claims.explorer, at: (/* @__PURE__ */ new Date()).toISOString(), resource: req.resource, receipt: claims.receipt_url }));
    }
  } catch {
  }
  const pr = { x402Version: 2, success: settled, transaction: tx, network: req.network, amount: req.amount, asset: req.asset, payer, receipt: claims.receipt_url, errorReason: settled ? null : s.body && (s.body.errorReason || s.body.error) || null };
  const enc = b64(pr);
  return new Response(JSON.stringify({ receipt, statement, data }, null, 1), {
    status: settled ? 200 : 402,
    headers: { ...X402_HEADERS, "PAYMENT-RESPONSE": enc, "X-PAYMENT-RESPONSE": enc, "X-X402-Receipt": claims.receipt_url }
  });
}
__name(handleApi, "handleApi");
async function handleReceipt(env, nonce) {
  if (!/^[a-f0-9]{32}$/.test(nonce)) return new Response(JSON.stringify({ error: "bad nonce" }), { status: 400, headers: X402_HEADERS });
  let r = null;
  try {
    r = await env.OFFICE_X402.get(`x402:receipt:${nonce}`, "json");
  } catch {
  }
  if (!r) return new Response(JSON.stringify({ error: "unknown receipt", nonce }), { status: 404, headers: X402_HEADERS });
  return new Response(JSON.stringify(r, null, 1), { status: 200, headers: { ...X402_HEADERS, "cache-control": "public, max-age=31536000, immutable" } });
}
__name(handleReceipt, "handleReceipt");
async function paidStats(env) {
  let count = 0, last = null, source = "facilitator settlement receipts counted in KV";
  try {
    count = parseInt(await env.OFFICE_X402.get("x402:count") || "0", 10);
    last = await env.OFFICE_X402.get("x402:last", "json");
  } catch {
    source = "KV unavailable";
  }
  return {
    paid_calls: count,
    last,
    price_usdc: X402.amountUsdc,
    network: X402.network,
    asset: X402.asset,
    route: `${X402.origin}/api`,
    facilitator: env.X402_FACILITATOR || X402.facilitator,
    receipts: `${X402.origin}/x402/receipt/{nonce}`,
    jwks: `${X402.origin}/x402/jwks.json`,
    kid: X402.kid,
    receiver_configured: !!env.X402_PAYTO,
    source
  };
}
__name(paidStats, "paidStats");

// worker/oauth.js
var ISS = "https://agent-kg.ai";
var KID = "mk-office-2026-09";
var TTL = 3600;
var SCOPES = ["office:read", "office:attest"];
var JSONH = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "access-control-allow-origin": "*" };
var b64uBuf2 = /* @__PURE__ */ __name((buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""), "b64uBuf");
var b64uStr2 = /* @__PURE__ */ __name((s) => b64uBuf2(new TextEncoder().encode(s)), "b64uStr");
var unb64u2 = /* @__PURE__ */ __name((s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4)), (c) => c.charCodeAt(0)), "unb64u");
var hex2 = /* @__PURE__ */ __name((n) => Array.from(crypto.getRandomValues(new Uint8Array(n)), (b) => b.toString(16).padStart(2, "0")).join(""), "hex");
var sha256 = /* @__PURE__ */ __name(async (s) => b64uBuf2(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s))), "sha256");
var json = /* @__PURE__ */ __name((o, status = 200, extra = {}) => new Response(JSON.stringify(o, null, 1), { status, headers: { ...JSONH, ...extra } }), "json");
var oauthError = /* @__PURE__ */ __name((error, description, status = 400) => json({ error, error_description: description }, status), "oauthError");
function metadata() {
  return {
    issuer: ISS,
    authorization_endpoint: `${ISS}/oauth/authorize`,
    token_endpoint: `${ISS}/oauth/token`,
    registration_endpoint: `${ISS}/oauth/register`,
    introspection_endpoint: `${ISS}/oauth/introspect`,
    revocation_endpoint: `${ISS}/oauth/revoke`,
    jwks_uri: `${ISS}/.well-known/jwks.json`,
    scopes_supported: SCOPES,
    response_types_supported: ["none"],
    grant_types_supported: ["client_credentials"],
    token_endpoint_auth_methods_supported: ["client_secret_post", "client_secret_basic"],
    introspection_endpoint_auth_methods_supported: ["client_secret_post", "client_secret_basic", "none"],
    revocation_endpoint_auth_methods_supported: ["client_secret_post", "client_secret_basic"],
    id_token_signing_alg_values_supported: ["EdDSA"],
    token_signing_alg_values_supported: ["EdDSA"],
    subject_types_supported: ["public"],
    code_challenge_methods_supported: [],
    service_documentation: `${ISS}/auth.md`,
    op_policy_uri: `${ISS}/auth.md`,
    claims_supported: ["iss", "sub", "aud", "exp", "iat", "jti", "scope", "client_name", "kid"],
    agent_auth: {
      skill: `${ISS}/auth.md`,
      register_uri: `${ISS}/oauth/register`,
      identity_types_supported: ["anonymous"],
      identity_assertion: { assertion_types_supported: [], credential_types_supported: ["oauth2_client_credentials"] },
      claim_uri: `${ISS}/#contact`,
      revocation_uri: `${ISS}/oauth/revoke`,
      note: "Anonymous registration only: the office binds no user accounts to agents. A registered agent receives client credentials; its tokens are signed against the office keyring."
    }
  };
}
__name(metadata, "metadata");
function protectedResource() {
  return {
    resource: ISS,
    authorization_servers: [ISS],
    scopes_supported: SCOPES,
    bearer_methods_supported: ["header"],
    resource_documentation: `${ISS}/auth.md`,
    resource_name: "Agentic Private Office \u2014 Matthew Keddy",
    licensed_routes: [`${ISS}/licensed/statement`]
  };
}
__name(protectedResource, "protectedResource");
async function importSeed(seed) {
  const pkcs8 = new Uint8Array([48, 46, 2, 1, 0, 48, 5, 6, 3, 43, 101, 112, 4, 34, 4, 32, ...seed]);
  return crypto.subtle.importKey("pkcs8", pkcs8, { name: "Ed25519" }, false, ["sign"]);
}
__name(importSeed, "importSeed");
async function signOffice(env, claims) {
  const key = await importSeed(unb64u2(env.OFFICE_KEY_SEED));
  const h = b64uStr2(JSON.stringify({ alg: "EdDSA", typ: "JWT", kid: KID }));
  const p = b64uStr2(JSON.stringify(claims));
  const sig = await crypto.subtle.sign({ name: "Ed25519" }, key, new TextEncoder().encode(`${h}.${p}`));
  return `${h}.${p}.${b64uBuf2(sig)}`;
}
__name(signOffice, "signOffice");
async function verifyOffice(env, token, jwksLoader) {
  try {
    const [h, p, s] = token.split(".");
    const header = JSON.parse(new TextDecoder().decode(unb64u2(h)));
    const claims = JSON.parse(new TextDecoder().decode(unb64u2(p)));
    const keys = (await jwksLoader()).keys || [];
    const jwk = keys.find((k) => k.kid === header.kid);
    if (!jwk || header.alg !== "EdDSA") return { active: false, reason: "kid" };
    const key = await crypto.subtle.importKey("jwk", { kty: "OKP", crv: "Ed25519", x: jwk.x }, { name: "Ed25519" }, false, ["verify"]);
    const ok = await crypto.subtle.verify({ name: "Ed25519" }, key, unb64u2(s), new TextEncoder().encode(`${h}.${p}`));
    if (!ok) return { active: false, reason: "signature" };
    const now = Math.floor(Date.now() / 1e3);
    if (claims.exp && claims.exp < now) return { active: false, reason: "expired", claims };
    if (claims.iss !== ISS) return { active: false, reason: "issuer" };
    let revoked = null;
    try {
      revoked = await env.OFFICE_X402.get(`oauth:revoked:${claims.jti}`);
    } catch {
    }
    if (revoked) return { active: false, reason: "revoked", claims };
    return { active: true, claims };
  } catch {
    return { active: false, reason: "malformed" };
  }
}
__name(verifyOffice, "verifyOffice");
async function readForm(request) {
  const ct = request.headers.get("content-type") || "";
  if (ct.includes("application/json")) return await request.json().catch(() => ({}));
  const t = await request.text();
  return Object.fromEntries(new URLSearchParams(t));
}
__name(readForm, "readForm");
function clientAuth(request, body) {
  const auth = request.headers.get("authorization") || "";
  if (auth.toLowerCase().startsWith("basic ")) {
    try {
      const [id, secret] = atob(auth.slice(6)).split(":");
      return { id, secret };
    } catch {
    }
  }
  return { id: body.client_id, secret: body.client_secret };
}
__name(clientAuth, "clientAuth");
async function handleOAuth(request, env, url, jwksLoader) {
  const path = url.pathname;
  if (path === "/oauth/authorize") {
    return oauthError("unsupported_response_type", "This authorization server issues client_credentials tokens to registered agents only; there is no end-user authorization flow. Register at /oauth/register, then POST /oauth/token.", 400);
  }
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: { ...JSONH, "access-control-allow-methods": "POST, OPTIONS", "access-control-allow-headers": "Authorization, Content-Type" } });
  if (request.method !== "POST") return oauthError("invalid_request", "POST required", 405);
  const body = await readForm(request);
  if (path === "/oauth/register") {
    const name = String(body.client_name || "").trim().slice(0, 120);
    if (!name) return oauthError("invalid_client_metadata", "client_name is required");
    const client_id = "akg-" + hex2(8);
    const client_secret = hex2(24);
    const rec = {
      client_id,
      client_name: name,
      secret_hash: await sha256(client_secret),
      scope: SCOPES.join(" "),
      grant_types: ["client_credentials"],
      token_endpoint_auth_method: "client_secret_post",
      client_uri: body.client_uri || null,
      contacts: Array.isArray(body.contacts) ? body.contacts.slice(0, 3) : [],
      registered_at: (/* @__PURE__ */ new Date()).toISOString(),
      identity: "anonymous"
    };
    try {
      await env.OFFICE_X402.put(`oauth:client:${client_id}`, JSON.stringify(rec));
    } catch {
      return oauthError("server_error", "registry unavailable", 503);
    }
    try {
      const c = parseInt(await env.OFFICE_X402.get("oauth:clients") || "0", 10) + 1;
      await env.OFFICE_X402.put("oauth:clients", String(c));
    } catch {
    }
    return json({
      client_id,
      client_secret,
      client_name: name,
      client_id_issued_at: Math.floor(Date.now() / 1e3),
      client_secret_expires_at: 0,
      grant_types: ["client_credentials"],
      token_endpoint_auth_method: "client_secret_post",
      scope: rec.scope,
      token_endpoint: `${ISS}/oauth/token`,
      note: "Store the secret; it is not shown again. Tokens are EdDSA JWTs signed against the office keyring (kid mk-office-2026-09)."
    }, 201);
  }
  if (path === "/oauth/token") {
    if (body.grant_type !== "client_credentials") return oauthError("unsupported_grant_type", "client_credentials only");
    const { id, secret } = clientAuth(request, body);
    if (!id || !secret) return oauthError("invalid_client", "client_id and client_secret required", 401);
    let rec = null;
    try {
      rec = await env.OFFICE_X402.get(`oauth:client:${id}`, "json");
    } catch {
    }
    if (!rec || rec.secret_hash !== await sha256(secret)) return oauthError("invalid_client", "unknown client or bad secret", 401);
    const asked = String(body.scope || rec.scope).split(/\s+/).filter(Boolean);
    if (asked.some((s) => !SCOPES.includes(s))) return oauthError("invalid_scope", `scopes supported: ${SCOPES.join(" ")}`);
    const now = Math.floor(Date.now() / 1e3);
    const claims = { iss: ISS, sub: id, aud: ISS, client_name: rec.client_name, scope: asked.join(" "), iat: now, exp: now + TTL, jti: hex2(16) };
    const token = await signOffice(env, claims);
    return json({ access_token: token, token_type: "Bearer", expires_in: TTL, scope: claims.scope, kid: KID, jwks_uri: `${ISS}/.well-known/jwks.json` });
  }
  if (path === "/oauth/introspect") {
    const token = body.token;
    if (!token) return oauthError("invalid_request", "token required");
    const v = await verifyOffice(env, token, jwksLoader);
    if (!v.active) return json({ active: false, reason: v.reason });
    const c = v.claims;
    return json({ active: true, iss: c.iss, sub: c.sub, aud: c.aud, client_id: c.sub, client_name: c.client_name, scope: c.scope, iat: c.iat, exp: c.exp, jti: c.jti, token_type: "Bearer", kid: KID });
  }
  if (path === "/oauth/revoke") {
    const token = body.token;
    if (!token) return oauthError("invalid_request", "token required");
    const { id, secret } = clientAuth(request, body);
    const v = await verifyOffice(env, token, jwksLoader);
    if (v.active || v.reason === "expired") {
      let rec = null;
      try {
        rec = await env.OFFICE_X402.get(`oauth:client:${id}`, "json");
      } catch {
      }
      if (!rec || rec.secret_hash !== await sha256(secret || "") || rec.client_id !== v.claims.sub) return oauthError("invalid_client", "revocation requires the token's own client credentials", 401);
      try {
        await env.OFFICE_X402.put(`oauth:revoked:${v.claims.jti}`, "1", { expirationTtl: Math.max(60, (v.claims.exp || 0) - Math.floor(Date.now() / 1e3) + 60) });
      } catch {
      }
    }
    return new Response(null, { status: 200, headers: JSONH });
  }
  return oauthError("invalid_request", "unknown endpoint", 404);
}
__name(handleOAuth, "handleOAuth");
async function handleLicensed(request, env, url, jwksLoader, loadFacts, holdingsSummary2, signStatement2) {
  const auth = request.headers.get("authorization") || "";
  const challenge = /* @__PURE__ */ __name((err, desc, status) => new Response(JSON.stringify({ error: err, error_description: desc, resource_metadata: `${ISS}/.well-known/oauth-protected-resource` }, null, 1), {
    status,
    headers: { ...JSONH, "www-authenticate": `Bearer realm="agent-kg.ai", resource_metadata="${ISS}/.well-known/oauth-protected-resource"${err ? `, error="${err}", error_description="${desc}"` : ""}` }
  }), "challenge");
  if (!auth.toLowerCase().startsWith("bearer ")) return challenge("", "a Bearer token from /oauth/token is required", 401);
  const v = await verifyOffice(env, auth.slice(7).trim(), jwksLoader);
  if (!v.active) return challenge("invalid_token", v.reason, 401);
  if (!String(v.claims.scope || "").split(" ").includes("office:attest")) return challenge("insufficient_scope", "office:attest required", 403);
  const facts = await loadFacts();
  const data = holdingsSummary2(facts);
  const now = Math.floor(Date.now() / 1e3);
  const statement = await signStatement2(env, { iss: ISS, iat: now, jti: hex2(16), typ: "holdings-summary", aud: v.claims.sub, licensed_to: v.claims.client_name, statement: data });
  return json({ licensed_to: { client_id: v.claims.sub, client_name: v.claims.client_name }, statement, data, kid: "mk-office-x402-2026-09", jwks: `${ISS}/x402/jwks.json` });
}
__name(handleLicensed, "handleLicensed");
async function oauthStats(env) {
  try {
    return { registered_agents: parseInt(await env.OFFICE_X402.get("oauth:clients") || "0", 10), issuer: ISS, kid: KID };
  } catch {
    return { registered_agents: 0, issuer: ISS, kid: KID };
  }
}
__name(oauthStats, "oauthStats");

// worker/mcp.js
var SERVER = { name: "Agentic Private Office \u2014 Matthew Keddy", protocolVersion: "2025-06-18" };
var OPERATOR = "Agentic KG Holdings";
var JSONH2 = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", "access-control-allow-origin": "*", "access-control-allow-methods": "POST, GET, OPTIONS", "access-control-allow-headers": "Content-Type, Accept, Mcp-Session-Id, Mcp-Protocol-Version" };
var TOOLS = [
  {
    name: "office_statement",
    description: "The office's current holdings summary, signed: shareholdings, hyperscaler tenancies, keys and as-of, drawn from facts.json and signed EdDSA (kid mk-office-x402-2026-09, key at /x402/jwks.json). The same statement the paid call and the licensed route return.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    outputSchema: { type: "object", properties: { statement: { type: "string", description: "EdDSA JWT over data" }, data: { type: "object" }, kid: { type: "string" }, jwks: { type: "string" } }, required: ["statement", "data", "kid", "jwks"] }
  }
];
var rpc = /* @__PURE__ */ __name((id, result) => ({ jsonrpc: "2.0", id, result }), "rpc");
var rpcErr = /* @__PURE__ */ __name((id, code, message) => ({ jsonrpc: "2.0", id, error: { code, message } }), "rpcErr");
var text = /* @__PURE__ */ __name((o) => ({ content: [{ type: "text", text: JSON.stringify(o, null, 1) }], structuredContent: o }), "text");
async function officeStatement(env, ctx) {
  const facts = await ctx.loadFacts();
  const data = ctx.holdingsSummary(facts);
  const now = Math.floor(Date.now() / 1e3);
  const jti = Array.from(crypto.getRandomValues(new Uint8Array(8)), (b) => b.toString(16).padStart(2, "0")).join("");
  let statement = null;
  try {
    statement = await ctx.signStatement(env, { iss: "https://agent-kg.ai", iat: now, jti, typ: "holdings-summary", statement: data });
  } catch {
    statement = null;
  }
  return { statement, data, kid: "mk-office-x402-2026-09", jwks: "https://agent-kg.ai/x402/jwks.json" };
}
__name(officeStatement, "officeStatement");
async function handleMcp(request, env, url, ctx) {
  const { version } = ctx;
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: JSONH2 });
  if (request.method === "GET") {
    return new Response(JSON.stringify({ server: { ...SERVER, version }, operator: OPERATOR, transport: "streamable-http", endpoint: `${url.origin}/mcp`, usage: "POST JSON-RPC 2.0: initialize, tools/list, tools/call", tools: TOOLS.map((t) => t.name), card: `${url.origin}/.well-known/mcp.json` }, null, 1), { status: 200, headers: JSONH2 });
  }
  if (request.method !== "POST") return new Response(JSON.stringify(rpcErr(null, -32600, "POST required")), { status: 405, headers: JSONH2 });
  let msgs;
  try {
    msgs = await request.json();
  } catch {
    return new Response(JSON.stringify(rpcErr(null, -32700, "parse error")), { status: 400, headers: JSONH2 });
  }
  const batch = Array.isArray(msgs);
  const out = [];
  for (const m of batch ? msgs : [msgs]) {
    const id = m && m.id !== void 0 ? m.id : null;
    if (!m || m.jsonrpc !== "2.0" || typeof m.method !== "string") {
      out.push(rpcErr(id, -32600, "invalid request"));
      continue;
    }
    if (m.method.startsWith("notifications/")) continue;
    try {
      if (m.method === "initialize") {
        out.push(rpc(id, { protocolVersion: m.params && m.params.protocolVersion || SERVER.protocolVersion, capabilities: { tools: { listChanged: false } }, serverInfo: { name: SERVER.name, version }, instructions: "Read-only door over the office record. One tool: office_statement, the signed holdings summary. The paid call is GET /api (x402); the licensed statement is /licensed/statement (OAuth). Nothing is answered from memory." }));
      } else if (m.method === "ping") {
        out.push(rpc(id, {}));
      } else if (m.method === "tools/list") {
        out.push(rpc(id, { tools: TOOLS }));
      } else if (m.method === "tools/call") {
        const name = m.params && m.params.name;
        if (name === "office_statement") out.push(rpc(id, text(await officeStatement(env, ctx))));
        else out.push(rpcErr(id, -32602, `unknown tool: ${name}`));
      } else out.push(rpcErr(id, -32601, `method not found: ${m.method}`));
    } catch (e) {
      out.push(rpcErr(id, -32603, "internal error"));
    }
  }
  if (!out.length) return new Response(null, { status: 202, headers: JSONH2 });
  return new Response(JSON.stringify(batch ? out : out[0], null, 1), { status: 200, headers: JSONH2 });
}
__name(handleMcp, "handleMcp");
function serverCard(version) {
  return {
    serverInfo: { name: SERVER.name, version },
    transport: { type: "streamable-http", endpoint: "https://agent-kg.ai/mcp" },
    capabilities: { tools: {} },
    tools: TOOLS.map((t) => ({ name: t.name, description: t.description })),
    authentication: { reads: "none", licensed: "https://agent-kg.ai/.well-known/oauth-protected-resource" },
    operator: OPERATOR,
    principal: "Matthew Keddy",
    surface: "https://agent-kg.ai",
    agent_card: "https://agent-kg.ai/.well-known/agent-card.json",
    keyring: "https://agent-kg.ai/.well-known/jwks.json",
    doors: [
      { name: "Family Office Knowledge Graph", surface: "https://familyofficeknowledgegraph.ai", endpoint: "https://mcp.fo-kg.ai/mcp", card: "https://familyofficeknowledgegraph.ai/.well-known/mcp.json", agent_card: "https://agent.fo-kg.ai/.well-known/agent-card.json", tools: ["resolve_family_office", "get_record", "list_events_since", "list_aliases", "list_nodes"], nodes: ["ca-fo-kg"] }
    ]
  };
}
__name(serverCard, "serverCard");

// worker/index.js
var CANON = "agent-kg.ai";
var ORIGIN = `https://${CANON}`;
var VERSION = "0.12.4";
var SURFACE = VERSION;
var OPERATOR2 = "Agentic KG Holdings";
var CONTACT = "mailto:mk@agent-kg.ai";
var LOCAL = /* @__PURE__ */ __name((h) => h === "localhost" || h.startsWith("127.") || h === "[::1]", "LOCAL");
var HEADERS = {
  "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
  "referrer-policy": "strict-origin-when-cross-origin",
  "permissions-policy": "camera=(), microphone=(), geolocation=()",
  "content-security-policy": "default-src 'none'; img-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; script-src 'self'; connect-src 'self' https://formspree.io; form-action https://formspree.io; base-uri 'none'; frame-ancestors 'none'",
  "content-signal": "search=yes, ai-input=yes, ai-train=yes",
  "x-office": "Agentic Private Office - Matthew Keddy",
  "x-office-operator": OPERATOR2,
  "x-office-version": VERSION,
  "x-office-contact": CONTACT,
  "x-office-keyring": `${ORIGIN}/.well-known/jwks.json`,
  "x-office-jwks": `${ORIGIN}/.well-known/jwks.json`,
  "x-office-kid": "mk-office-2026-09",
  "x-office-x402": "ready",
  "x-office-mcp": `${ORIGIN}/mcp`,
  "x-office-card": `${ORIGIN}/.well-known/agent-card.json`,
  "link": [
    `<${ORIGIN}/llms.txt>; rel="describedby"; type="text/plain"`,
    `<${ORIGIN}/.well-known/agent-card.json>; rel="agent-card"; type="application/json"`,
    `<${ORIGIN}/.well-known/ai-catalog.json>; rel="ai-catalog"; type="application/json"`,
    `<${ORIGIN}/.well-known/jwks.json>; rel="jwks"; type="application/json"`,
    `<${ORIGIN}/.well-known/mcp.json>; rel="mcp-server"; type="application/json"`,
    `<${ORIGIN}/.well-known/api-catalog>; rel="api-catalog"; type="application/linkset+json"`,
    `<${ORIGIN}/openapi.json>; rel="service-desc"; type="application/openapi+json"`,
    `<${ORIGIN}/auth.md>; rel="service-doc"; type="text/markdown"`,
    `<${ORIGIN}/mcp>; rel="service"`
  ].join(", ")
};
var CACHE = { page: "public, max-age=300", kit: "public, max-age=3600", icon: "public, max-age=604800", asset: "public, max-age=86400" };
var TYPES = {
  "/llms.txt": "text/plain; charset=utf-8",
  "/robots.txt": "text/plain; charset=utf-8",
  "/.well-known/security.txt": "text/plain; charset=utf-8",
  "/auth.md": "text/markdown; charset=utf-8",
  "/site.webmanifest": "application/manifest+json",
  "/sitemap.xml": "application/xml; charset=utf-8",
  "/.well-known/api-catalog": "application/linkset+json",
  "/.well-known/http-message-signatures-directory": "application/http-message-signatures-directory+json",
  "/openapi.json": "application/openapi+json; charset=utf-8",
  "/webmcp.js": "text/javascript; charset=utf-8"
};
var KIT = /* @__PURE__ */ new Set([
  "/llms.txt",
  "/facts.json",
  "/ai-catalog.json",
  "/robots.txt",
  "/sitemap.xml",
  "/site.webmanifest",
  "/auth.md",
  "/openapi.json",
  "/health.json",
  "/.well-known/security.txt",
  "/.well-known/agent-card.json",
  "/.well-known/ai-catalog.json",
  "/.well-known/ard.json",
  "/.well-known/jwks.json",
  "/x402/jwks.json",
  "/.well-known/api-catalog",
  "/.well-known/oauth-authorization-server",
  "/.well-known/openid-configuration",
  "/.well-known/oauth-protected-resource",
  "/.well-known/mcp/server-card.json",
  "/.well-known/mcp.json",
  "/.well-known/skills.json",
  "/.well-known/agent-skills/index.json",
  "/.well-known/http-message-signatures-directory"
]);
var ICON = /\.(ico|png|svg|jpg)$/;
var RECORD_PAGES = { "/status": "/status.html", "/terms": "/terms.html", "/privacy": "/privacy.html", "/security": "/security.html", "/no-cookies": "/no-cookies.html" };
var STATUS_KIT = ["/llms.txt", "/facts.json", "/ai-catalog.json", "/.well-known/agent-card.json", "/.well-known/jwks.json", "/.well-known/mcp.json", "/.well-known/skills.json", "/.well-known/security.txt", "/robots.txt", "/sitemap.xml"];
var esc = /* @__PURE__ */ __name((s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]), "esc");
var tokens = /* @__PURE__ */ __name((s) => String(Math.ceil(s.length / 4)), "tokens");
function wantsMarkdown(request) {
  const a = (request.headers.get("accept") || "").toLowerCase();
  if (!a.includes("text/markdown")) return false;
  const md = a.indexOf("text/markdown"), html = a.indexOf("text/html");
  return html === -1 || md < html;
}
__name(wantsMarkdown, "wantsMarkdown");
function htmlToMarkdown(html) {
  const unesc = /* @__PURE__ */ __name((s) => s.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&nbsp;/g, " "), "unesc");
  let body = html.replace(/[\s\S]*?<body[^>]*>/, "").replace(/<\/body>[\s\S]*$/, "");
  body = body.replace(/<script[\s\S]*?<\/script>/g, "").replace(/<nav[\s\S]*?<\/nav>/g, "").replace(/<!--[\s\S]*?-->/g, "");
  body = body.replace(/<a\s[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g, (_, h, t) => `[${t.replace(/<[^>]+>/g, "").trim()}](${h.startsWith("/") ? ORIGIN + h : h})`);
  body = body.replace(/<img[^>]*>/g, "");
  body = body.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/g, (_, t) => `
# ${t.replace(/<[^>]+>/g, "").trim()}
`);
  body = body.replace(/<h2[^>]*>([\s\S]*?)<\/h2>/g, (_, t) => `
## ${t.replace(/<[^>]+>/g, "").trim()}
`);
  body = body.replace(/<h3[^>]*>([\s\S]*?)<\/h3>/g, (_, t) => `
### ${t.replace(/<[^>]+>/g, "").trim()}
`);
  body = body.replace(/<div class="sec-eyebrow">([\s\S]*?)<\/div>/g, (_, t) => `
*${t.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim()}*
`);
  body = body.replace(/<dt[^>]*>([\s\S]*?)<\/dt>\s*<dd[^>]*>([\s\S]*?)<\/dd>/g, (_, a, b) => `- ${a.replace(/<[^>]+>/g, "").trim()}: ${b.replace(/<[^>]+>/g, "").trim()}
`);
  body = body.replace(/<div class="(?:proof-num|hero-stat-num)[^"]*">([\s\S]*?)<\/div>\s*<div class="(?:proof-label|hero-stat-label)">([\s\S]*?)<\/div>/g, (_, n, l) => `- ${l.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim()}: ${n.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim()}
`);
  body = body.replace(/<li[^>]*>([\s\S]*?)<\/li>/g, (_, t) => `- ${t.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim()}
`);
  body = body.replace(/<label[^>]*>([\s\S]*?)<\/label>/g, (_, t) => `- ${t.replace(/<[^>]+>/g, "").trim()}: (field)
`);
  body = body.replace(/<button[^>]*>([\s\S]*?)<\/button>/g, (_, t) => `- ${t.replace(/<[^>]+>/g, "").trim()} (button)
`);
  body = body.replace(/<p[^>]*>([\s\S]*?)<\/p>/g, (_, t) => `
${t.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim()}
`);
  body = body.replace(/<span class="footer-sep">·<\/span>/g, " \xB7 ");
  body = body.replace(/<[^>]+>/g, "");
  body = unesc(body).split("\n").map((l) => l.replace(/[ \t]+/g, " ").trimEnd()).join("\n").replace(/\n{3,}/g, "\n\n").trim();
  return body + "\n";
}
__name(htmlToMarkdown, "htmlToMarkdown");
function volumeFigures(facts) {
  const v = ((facts || {}).radar || {}).volume || {};
  return { "volume.ytd": String(v.ytd_phrase || "").replace(/\s*year to date$/, "") || null, "volume.annualised": String(v.annualised_phrase || "").replace(/\s*annualised$/, "") || null };
}
__name(volumeFigures, "volumeFigures");
function withHeaders(res, path) {
  for (const [k, v] of Object.entries(HEADERS)) res.headers.set(k, v);
  if (path === "/" || path === "/x402" || path === "/status") {
    if (!res.headers.get("cache-control")) res.headers.set("cache-control", CACHE.page);
  } else if (KIT.has(path)) res.headers.set("cache-control", CACHE.kit);
  else if (ICON.test(path)) res.headers.set("cache-control", CACHE.icon);
  else if (path === "/styles.css" || path === "/webmcp.js") res.headers.set("cache-control", CACHE.asset);
  if (TYPES[path]) res.headers.set("content-type", TYPES[path]);
  else if (path.endsWith(".json")) res.headers.set("content-type", "application/json; charset=utf-8");
  else if (path.endsWith("/SKILL.md")) res.headers.set("content-type", "text/markdown; charset=utf-8");
  return res;
}
__name(withHeaders, "withHeaders");
var jsonRes = /* @__PURE__ */ __name((o, status = 200, extra = {}) => new Response(JSON.stringify(o, null, 1), { status, headers: { "content-type": "application/json; charset=utf-8", ...extra } }), "jsonRes");
var handler = {
  async fetch(request, env) {
    const url = new URL(request.url);
    const host = url.hostname.toLowerCase();
    if (host !== CANON && !LOCAL(host)) {
      return new Response(null, { status: 301, headers: { location: `${ORIGIN}/`, "x-office-version": VERSION, "x-office-operator": OPERATOR2 } });
    }
    const path = url.pathname;
    const asset = /* @__PURE__ */ __name((p) => env.ASSETS.fetch(new Request(new URL(p, url), { method: "GET" })), "asset");
    const loadJson = /* @__PURE__ */ __name(async (p) => {
      const r = await asset(p);
      return r.ok ? await r.json() : {};
    }, "loadJson");
    const loadFacts = /* @__PURE__ */ __name(async () => {
      const f = await loadJson("/facts.json");
      f.radar = f.radar || {};
      f.radar.paid_calls = "held in KV for the office's own read; never rendered publicly (CEO ruling 2026-09-14: usage counts are competitive data)";
      f.radar.registered_agents = (await oauthStats(env)).registered_agents;
      return f;
    }, "loadFacts");
    const officeJwks = /* @__PURE__ */ __name(() => loadJson("/.well-known/jwks.json"), "officeJwks");
    const x402Jwks = /* @__PURE__ */ __name(() => loadJson("/x402/jwks.json"), "x402Jwks");
    if (path === "/mcp") return withHeaders(await handleMcp(request, env, url, { version: VERSION, loadFacts, holdingsSummary, signStatement, x402JwksLoader: x402Jwks }), path);
    if (path.startsWith("/oauth/")) return withHeaders(await handleOAuth(request, env, url, officeJwks), path);
    if (path === "/api" && request.method === "OPTIONS") return preflight();
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", { status: 405, headers: { allow: "GET, HEAD", "content-type": "text/plain; charset=utf-8" } });
    }
    if (path === "/api") return withHeaders(await handleApi(request, env, loadFacts), path);
    if (path === "/x402/settled.json") return withHeaders(await handleSettled(env), path);
    const rm = path.match(/^\/x402\/receipt\/([^/]+)$/);
    if (rm) return withHeaders(await handleReceipt(env, rm[1]), path);
    if (path === "/.well-known/oauth-authorization-server" || path === "/.well-known/openid-configuration") return withHeaders(jsonRes(metadata()), path);
    if (path === "/.well-known/oauth-protected-resource") return withHeaders(jsonRes(protectedResource()), path);
    if (path === "/licensed/statement") return withHeaders(await handleLicensed(request, env, url, officeJwks, loadFacts, holdingsSummary, signStatement), path);
    const am = path.match(/^\/attest\/([a-z0-9.-]+)$/i);
    if (am) {
      const facts = await loadFacts();
      const hostAsked = am[1].toLowerCase();
      const h = (facts.holdings || []).find((x) => new URL(x.url).hostname === hostAsked);
      if (!h) return withHeaders(jsonRes({ error: "not_a_holding", host: hostAsked, holdings: (facts.holdings || []).map((x) => new URL(x.url).hostname) }, 404, { "cache-control": "no-store" }), path);
      const now = Math.floor(Date.now() / 1e3);
      const claims = { iss: ORIGIN, sub: hostAsked, iat: now, jti: Array.from(crypto.getRandomValues(new Uint8Array(8)), (b) => b.toString(16).padStart(2, "0")).join(""), typ: "holding-attestation", holding: h.name, url: h.url, held: h.line, through: "Agentic Private Office \u2014 Matthew Keddy", operator: OPERATOR2, as_of: facts.as_of };
      let attestation = null;
      try {
        attestation = await signOffice(env, claims);
      } catch {
        attestation = null;
      }
      return withHeaders(jsonRes({ attestation, kid: "mk-office-2026-09", jwks: `${ORIGIN}/.well-known/jwks.json`, claims, verify: "the estate signs a line back on its own host; both ends prove the holding" }, 200, { "cache-control": "no-store" }), path);
    }
    if (path === "/.well-known/mcp/server-card.json" || path === "/.well-known/mcp.json") return withHeaders(jsonRes(serverCard(VERSION)), path);
    if (path === "/facts.json") {
      const f = await loadFacts();
      return withHeaders(new Response(request.method === "HEAD" ? null : JSON.stringify(f, null, 2), { status: 200, headers: { "content-type": "application/json; charset=utf-8" } }), path);
    }
    if (path === "/health.json") {
      let kv = "ok";
      try {
        await env.OFFICE_X402.get("x402:count");
      } catch {
        kv = "unavailable";
      }
      const f = await loadFacts();
      return withHeaders(jsonRes({ status: "ok", surface: CANON, operator: OPERATOR2, version: VERSION, as_of: f.as_of, time: (/* @__PURE__ */ new Date()).toISOString(), kv, registered_agents: f.radar.registered_agents, doors: { page: "/", x402: "/api", mcp: "/mcp", oauth: "/oauth/token", licensed: "/licensed/statement", attest: "/attest/{holding-host}" } }, 200, { "cache-control": "no-store" }), path);
    }
    const page = /* @__PURE__ */ __name(async (tplPath, map, cache, raw = []) => {
      const html = (await (await asset(tplPath)).text()).replace(/\{\{([a-z_.0-9]+)\}\}/g, (_, k) => map[k] === null || map[k] === void 0 ? "\u2014" : k.startsWith("x402.last_") || raw.includes(k) ? map[k] : esc(map[k]));
      if (wantsMarkdown(request)) {
        const md = htmlToMarkdown(html);
        return new Response(request.method === "HEAD" ? null : md, { status: 200, headers: { "content-type": "text/markdown; charset=utf-8", vary: "Accept", "cache-control": cache, "x-markdown-tokens": tokens(md) } });
      }
      return new Response(request.method === "HEAD" ? null : html, { status: 200, headers: { "content-type": "text/html; charset=utf-8", vary: "Accept", "cache-control": cache } });
    }, "page");
    if (path === "/" || path === "/index.html") {
      const facts = await loadFacts();
      const r = facts.radar || {}, an = r.annual || {};
      const held = [], skipped = [], jur = /* @__PURE__ */ new Set();
      let sum = { records: 0, fields: 0, nodes: 0 };
      for (const h of facts.holdings || []) {
        if (!h.facts) {
          skipped.push(`${h.name} \u2014 no facts.json on the record`);
          continue;
        }
        try {
          const hf = await (await fetch(h.facts, { headers: { accept: "application/json" }, signal: AbortSignal.timeout(4e3), cf: { cacheTtl: 300 } })).json();
          const c = hf.radar && hf.radar.counts || {};
          if (typeof c.records !== "number") {
            skipped.push(`${h.name} \u2014 ${h.facts} answered without counts`);
            continue;
          }
          sum.records += c.records || 0;
          sum.fields += c.fields || 0;
          sum.nodes += c.nodes || 0;
          if (Array.isArray(c.jurisdiction_list)) for (const j of c.jurisdiction_list) jur.add(j);
          else if (typeof c.jurisdictions === "number") jur.add(`${h.name}:${c.jurisdictions}`);
          held.push(`${h.name} \u2014 ${h.facts} (records ${c.records}, fields ${c.fields}, nodes ${c.nodes}, jurisdictions ${Array.isArray(c.jurisdiction_list) ? c.jurisdiction_list.length : c.jurisdictions})`);
        } catch (e) {
          skipped.push(`${h.name} \u2014 ${h.facts} did not answer`);
        }
      }
      const fmtN = /* @__PURE__ */ __name((n) => typeof n === "number" ? n.toLocaleString("en-US") : "pending", "fmtN");
      const tenancies = (facts.tenancies || []).reduce((a2, t) => a2 + (t.count || 0), 0);
      const labs = ((facts.laboratories || {}).list || []).length;
      const ring = ((facts.keys || {}).ring || []).length;
      const sources = `holdings read live from each graph's facts.json \xB7 tenancies, labs and keys from the office's books \xB7 as of ${an.as_of || String(facts.as_of || "").slice(0, 7)}.`;
      const map = {
        "annual.datapoints": an.datapoints,
        "annual.markets": an.markets,
        "annual.as_of": an.as_of,
        // ORDER AK-x402-03 (2026-10-03): the hero's two volume figures are the measured line, read from facts.json radar.volume and rounded as it rounds them
        ...volumeFigures(facts),
        "radar.graphs_held": fmtN(held.length),
        "radar.records": fmtN(sum.records),
        "radar.fields": fmtN(sum.fields),
        "radar.jurisdictions": fmtN(jur.size),
        "radar.nodes": fmtN(sum.nodes),
        "radar.tenancies_held": fmtN(tenancies),
        "radar.labs": fmtN(labs),
        "radar.keys_on_ring": fmtN(ring),
        "sources.line": sources,
        surface_version: SURFACE,
        as_of: facts.as_of
      };
      return withHeaders(await page("/index.html", map, CACHE.page), "/");
    }
    if (path === "/x402" || path === "/x402/" || path === "/x402.html") {
      const [facts, ps] = await Promise.all([loadFacts(), paidStats(env)]);
      const last = ps.last || {};
      const map = {
        "x402.state": ps.receiver_configured ? "LIVE \xB7 BASE MAINNET" : "RECEIVER NOT CONFIGURED",
        "x402.kid": ps.kid,
        "x402.receiver": ps.receiver_configured ? "configured (Worker secret; the address is on the 402 offer)" : "not configured \u2014 the CEO places the pay-to address; /api answers 503 until then",
        "x402.last_tx": last.explorer ? `<a href="${esc(last.explorer)}" rel="noopener" target="_blank">${esc(last.transaction)}</a>` : null,
        "x402.last_receipt": last.receipt ? `<a href="${esc(last.receipt)}">${esc(last.receipt)}</a>` : null,
        "x402.last_at": last.at ? esc(last.at) : null,
        surface_version: SURFACE,
        as_of: facts.as_of
      };
      return withHeaders(await page("/x402.html", map, "no-store"), "/x402");
    }
    if (RECORD_PAGES[path]) {
      const facts = await loadFacts();
      const map = { surface_version: SURFACE, as_of: facts.as_of };
      if (path === "/status") {
        const row = /* @__PURE__ */ __name((label, ok, right, cls) => `<li class="${cls || (ok ? "ok" : "bad")}"><span>${esc(label)}</span><span class="${cls || (ok ? "ok" : "bad")}">${esc(right)}</span></li>`, "row");
        const probe = /* @__PURE__ */ __name(async (p, expect) => {
          try {
            const r = await handler.fetch(new Request(ORIGIN + p, { method: "GET", headers: { accept: "application/json, text/plain, */*" } }), env);
            const ct = (r.headers.get("content-type") || "").split(";")[0];
            return row(p, r.status === expect, `${r.status} \xB7 ${ct}`);
          } catch (e) {
            return row(p, false, "no answer");
          }
        }, "probe");
        const rows = [];
        for (const p of STATUS_KIT) rows.push(await probe(p, 200));
        rows.push(await probe("/api", 402));
        const last = (await paidStats(env)).last;
        if (last && last.receipt) rows.push(await probe(new URL(last.receipt).pathname, 200));
        else rows.push(row("/x402/receipt/{nonce}", true, "endpoint up \xB7 no receipt yet"));
        try {
          const ds = await (await fetch("https://cloudflare-dns.com/dns-query?name=agent-kg.ai&type=DS&do=1", { headers: { accept: "application/dns-json" }, signal: AbortSignal.timeout(4e3), cf: { cacheTtl: 300 } })).json();
          const n = (ds.Answer || []).length;
          rows.push(row("DNSSEC \xB7 agent-kg.ai", n > 0 && ds.AD, n > 0 ? ds.AD ? "DS at parent \xB7 validating (AD)" : "DS at parent \xB7 not yet validating" : "enabled at Cloudflare \xB7 DS not at parent yet (registrar pushes it)", n > 0 && ds.AD ? "ok" : "warn"));
        } catch (e) {
          rows.push(row("DNSSEC \xB7 agent-kg.ai", false, "resolver did not answer", "warn"));
        }
        const rd = facts.radar.readiness;
        rows.push(rd ? row(`Readiness scan \xB7 ${rd.date}`, true, `Level ${rd.level} ${rd.level_name || ""} \xB7 ${rd.pass} pass / ${rd.fail} fail`, rd.fail ? "warn" : "ok") : row("Readiness scan", false, "no scan recorded", "warn"));
        map["status.rows"] = rows.join("\n");
      }
      const res = await page(RECORD_PAGES[path], map, path === "/status" ? "no-store" : CACHE.page, path === "/status" ? ["status.rows"] : []);
      return withHeaders(res, path === "/status" ? "/status" : "/");
    }
    if (path === "/llms.txt" || path === "/.well-known/agent-card.json") {
      const src = await asset(path);
      if (src.status === 200) {
        const vf = volumeFigures(await loadFacts());
        const text2 = (await src.text()).replace(/\{\{(volume\.(?:ytd|annualised))\}\}/g, (_, k) => vf[k] || "\u2014");
        return withHeaders(new Response(request.method === "HEAD" ? null : text2, { status: 200, headers: { "content-type": src.headers.get("content-type") || "text/plain; charset=utf-8" } }), path);
      }
    }
    const a = await env.ASSETS.fetch(request);
    if (a.status === 404 || (a.headers.get("content-type") || "").includes("text/html")) {
      return withHeaders(jsonRes({ error: "not_found", surface: CANON, path }, 404, { "cache-control": "no-store" }), "/404");
    }
    return withHeaders(new Response(a.body, a), path);
  }
};
var index_default = handler;
export {
  index_default as default
};

