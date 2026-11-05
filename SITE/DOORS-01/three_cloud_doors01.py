r"""three_cloud_doors01.py — DOORS-01 proof: three-cloud read of one door (argv getfilings | getticker | getauditor) at mcp.<door>.ai with STOCK, UNPATCHED clients, no bearer (the
three_cloud_iw.py harness shape): AWS Strands MCPClient · Azure Semantic Kernel MCPStreamableHttpPlugin · google-genai with an MCP ClientSession as a tool.
PADEL harness venv. Per cloud: list tools (expect 3) · the door's tool on NASDAQ:MSFT (signed kid allooloo-cmr-2026-10, a receipt id
that verify_receipt finds valid on mcp.rco-records.ai) · a typed error (an unknown issuer → unknown_issuer). Evidence: three-cloud-<door>.json. No secret printed."""
import sys, json, asyncio, time, urllib.request, pathlib
sys.path.insert(0, r"C:\PADEL\harness"); from common import key
K = sys.argv[1]; T = {"getfilings": "get_filings", "getticker": "get_ticker", "getauditor": "get_auditor"}[K]
DOOR = f"https://mcp.{K}.ai/mcp"; UA = {"User-Agent": "Allooloo doors-01 three-cloud", "content-type": "application/json", "accept": "application/json"}
ARG = {"get_filings": {"issuer": "NASDAQ:MSFT", "from": "2026-01-01", "to": "2026-03-31"}, "get_ticker": {"identifier": "MSFT", "exchange": "NASDAQ"}, "get_auditor": {"issuer": "NASDAQ:MSFT"}}[T]
VER = (T, ARG); REF = (T, {**ARG, **({"identifier": "ZZZZNOPE9"} if T == "get_ticker" else {"issuer": "ZZZZNOPE9"})})
def verify(rid):
    b = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "verify_receipt", "arguments": {"id": rid}}}).encode()
    j = json.load(urllib.request.urlopen(urllib.request.Request("https://mcp.rco-records.ai/mcp", data=b, headers=UA, method="POST"), timeout=60)); r = j["result"]; sc = r.get("structuredContent") or json.loads(r["content"][0]["text"])
    return (sc.get("verification") or {}).get("valid")
ini = json.load(urllib.request.urlopen(urllib.request.Request(DOOR, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}).encode(), headers=UA, method="POST"), timeout=60))
ver = ini["result"]["serverInfo"]["version"]
out = {"door": DOOR, "door_version": ver, "server": ini["result"]["serverInfo"]["name"], "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "bearer": None}
def payload(res):
    if isinstance(res, dict):
        if res.get("structuredContent"): return res["structuredContent"]
        c = res.get("content") or []
    else:
        sc = getattr(res, "structuredContent", None) or getattr(res, "structured_content", None)
        if sc: return sc
        c = getattr(res, "content", None) or []
    for x in c:
        t = getattr(x, "text", None) or (x.get("text") if isinstance(x, dict) else None)
        if t:
            try: return json.loads(t)
            except Exception: return {"raw": t[:160]}
    return {}
def slim_ver(d): rid = (d.get("receipt") or {}).get("id"); return {"cmr": d.get("cmr"), "events": d.get("count") if T == "get_filings" else (d.get("isin") or {}).get("value") if T == "get_ticker" else (d.get("auditor") or {}).get("value"), "kid": (d.get("signature") or {}).get("kid"), "receipt": rid, "receipt_valid": verify(rid) if rid else None, "error": d.get("error")}
def slim_ref(d): return {"code": d.get("code") or d.get("error")}
def grade(rep):
    v = rep.get("verify") or {}
    rep["pass"] = bool(rep.get("listed") == 3 and v.get("cmr") == "us-cm-kg/NASDAQ/MSFT" and v.get("kid") == "allooloo-cmr-2026-10" and v.get("receipt_valid") is True and (rep.get("refusal") or {}).get("code") == "unknown_issuer"); return rep
def aws():
    from strands.tools.mcp import MCPClient
    import strands, mcp.client.streamable_http as sh
    fn = getattr(sh, "streamablehttp_client", None) or getattr(sh, "streamable_http_client"); rep = {"client": f"strands-agents {getattr(strands, '__version__', '?')} MCPClient · mcp streamable-http"}
    c = MCPClient(lambda: fn(DOOR)); n = [0]
    with c:
        rep["listed"] = len(c.list_tools_sync())
        def call(name, args):
            n[0] += 1; return payload(c.call_tool_sync(tool_use_id=f"door-{n[0]}", name=name, arguments=args))
        rep["verify"] = slim_ver(call(*VER)); rep["refusal"] = slim_ref(call(*REF))
    return grade(rep)
try: out["aws_strands"] = aws()
except BaseException as e: out["aws_strands"] = {"pass": False, "error": repr(e)[:220]}
async def azure():
    from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin
    import semantic_kernel
    rep = {"client": f"semantic-kernel {semantic_kernel.__version__} MCPStreamableHttpPlugin"}; p = MCPStreamableHttpPlugin(name="door", url=DOOR); await p.connect()
    try:
        rep["listed"] = len((await p.session.list_tools()).tools)
        async def acall(name, args): return payload(await p.session.call_tool(name, args))
        rep["verify"] = slim_ver(await acall(*VER)); rep["refusal"] = slim_ref(await acall(*REF))
    finally: await p.close()
    return grade(rep)
try: out["azure_semantic_kernel"] = asyncio.run(azure())
except BaseException as e: out["azure_semantic_kernel"] = {"pass": False, "error": repr(e)[:220]}
async def google():
    from google import genai
    import google.genai as gg
    from mcp import ClientSession
    import mcp.client.streamable_http as sh
    fn = getattr(sh, "streamablehttp_client", None) or getattr(sh, "streamable_http_client"); rep = {"client": f"google-genai {gg.__version__} pure stock + mcp ClientSession as a tool"}
    client = genai.Client(api_key=key("gemini"))
    async with fn(DOOR) as st:
        async with ClientSession(st[0], st[1]) as s:
            await s.initialize(); rep["listed"] = len((await s.list_tools()).tools)
            async def acall(name, args): return payload(await s.call_tool(name, args))
            rep["verify"] = slim_ver(await acall(*VER)); rep["refusal"] = slim_ref(await acall(*REF))
            try:
                resp = await client.aio.models.generate_content(model="gemini-3.1-pro-preview", contents=f"Call {T} with the arguments {json.dumps(ARG)} and reply with the cmr field only.", config={"tools": [s], "temperature": 0})
                rep["model_attach"] = True; rep["model_reply"] = (resp.text or "")[:80]
            except BaseException as e: rep["model_attach"] = False; rep["model_error"] = repr(e)[:200]
    grade(rep); rep["pass"] = rep["pass"] and rep.get("model_attach") is True; return rep
try: out["google_genai"] = asyncio.run(google())
except BaseException as e: out["google_genai"] = {"pass": False, "error": repr(e)[:220]}
out["PASS"] = all(out[k].get("pass") for k in ("aws_strands", "azure_semantic_kernel", "google_genai"))
(pathlib.Path(__file__).parent / f"three-cloud-{K}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
for k in ("aws_strands", "azure_semantic_kernel", "google_genai"):
    r = out[k]; print(f"{k:24} {'PASS' if r.get('pass') else 'FAIL'} | listed {r.get('listed')} | verify {r.get('verify')} | refusal {r.get('refusal')} | {r.get('model_reply') or r.get('error') or r.get('model_error') or ''}")
print("PASS" if out["PASS"] else "FAIL", "door", ver)
