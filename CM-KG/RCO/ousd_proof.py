r"""ousd_proof.py — X402-A-01 rider (CEO 2026-10-24): one Open USD settlement on the resolver, proved end to end. The CEO runs it; CC sends no funds.
Same stock x402 Python SDK as AL-x402-01 (al_ousd_pay.py): the selector takes the OUSD accept entry only, spend controls cap the payment at one cent (10000),
the payer key is read in-process from AGENT KEYS\x402-payer-key.txt and never printed. After the paid read it checks:
  · PAYMENT-RESPONSE: success, asset OUSD, the transaction hash;
  · on Base: an OUSD Transfer of 10000 from the payer to the OUSD payTo on the offer (the CB Wallet, AGENT KEYS x402-payto-ousd);
  · the RCO receipt named in the answer (get_receipt): it carries the same settlement transaction.
Evidence: ousd-proof.json beside. Usage: python ousd_proof.py [url]   (default https://mcp.getissuer.ai/signal/FR0000120271?x402=1)
Needs: pip install "x402[httpx,evm]" eth-account   (the AL-x402-01 environment)"""
import asyncio, json, base64, sys, time, pathlib, urllib.request
from eth_account import Account
from x402.client import x402Client
from x402.mechanisms.evm.exact.client import ExactEvmScheme
from x402.mechanisms.evm.signers import EthAccountSignerWithRPC
from x402.http.clients.httpx import x402HttpxClient
URL = sys.argv[1] if len(sys.argv) > 1 else "https://mcp.getissuer.ai/signal/FR0000120271?x402=1"
OUT = pathlib.Path(__file__).with_name("ousd-proof.json"); RPCS = ("https://base-rpc.publicnode.com", "https://mainnet.base.org")
OUSD = "0xB2000000000000000000002fEb517dFeC7415344"; TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
PAYTO = open(r"C:\MATTHEWKEDDY\AGENT KEYS\x402-payto-ousd.txt", encoding="utf-8-sig").read().strip()
UA = {"User-Agent": "Allooloo Technologies Corp. house payer X402-A-01 developers@allooloo.ai", "Accept": "application/json"}
_k = open(r"C:\ALLOOLOO\AGENT KEYS\x402-payer-key.txt", encoding="utf-8").read().strip(); acct = Account.from_key(_k if _k.startswith("0x") else "0x" + _k); del _k
def pick_ousd(version, reqs):
    m = [r for r in reqs if str(getattr(r, "asset", "")).lower() == OUSD.lower()]
    if not m: raise RuntimeError("the offer carries no OUSD accept entry")
    return m[0]
def client(): return x402Client(pick_ousd).register("eip155:8453", ExactEvmScheme(EthAccountSignerWithRPC(acct, RPCS[0]))).set_spend_controls({"allowed_assets": [{"network": "eip155:8453", "asset": OUSD, "max_amount_per_payment": "10000"}]})
def post(u, b): return json.load(urllib.request.urlopen(urllib.request.Request(u, data=json.dumps(b).encode(), headers={"Content-Type": "application/json", "User-Agent": "allooloo X402-A-01"}), timeout=60))
def rpc(m, p):
    for u in RPCS + RPCS:
        try: return post(u, {"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).get("result")
        except Exception: time.sleep(2)
async def main():
    ev = {"url": URL, "payer": acct.address, "ousd_payTo": PAYTO, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    async with x402HttpxClient(client(), headers=UA, timeout=120) as c:
        r = await c.get(URL); ev["http"] = r.status_code; body = r.json(); pr = r.headers.get("payment-response")
    ev["payment_response"] = json.loads(base64.b64decode(pr)) if pr else None
    ev["answer"] = {k: body.get(k) for k in ("signal", "state", "issuer", "settlement", "receipt")}
    tx = (ev["payment_response"] or {}).get("transaction") or (body.get("settlement") or {}).get("transaction")
    rec = None
    for _ in range(10):
        rec = rpc("eth_getTransactionReceipt", [tx]) if tx else None
        if rec: break
        time.sleep(3)
    logs = [l for l in (rec or {}).get("logs", []) if l["topics"] and l["topics"][0] == TRANSFER and l["address"].lower() == OUSD.lower()]
    ev["chain"] = {"tx": tx, "status": (rec or {}).get("status"), "block": int(rec["blockNumber"], 16) if rec else None,
                   "ousd_payer_to_payTo_10000": any(l["topics"][1][-40:].lower() == acct.address[2:].lower() and l["topics"][2][-40:].lower() == PAYTO[2:].lower() and int(l["data"], 16) == 10000 for l in logs)}
    did = (body.get("receipt") or {}).get("decision_id"); time.sleep(20)
    if did:
        g = post("https://mcp.rco-a2a.ai/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_receipt", "arguments": {"decision_id": did}}})["result"]
        rcpt = g.get("structuredContent") or json.loads(g["content"][0]["text"])
        ev["receipt"] = {"decision_id": did, "settlement": rcpt.get("settlement"), "signature_check": rcpt.get("signature_check"), "ledger": rcpt.get("ledger"), "carries_the_tx": (rcpt.get("settlement") or {}).get("transaction") == tx}
    ev["ok"] = bool(ev["http"] == 200 and (ev["payment_response"] or {}).get("success") and ev["chain"]["ousd_payer_to_payTo_10000"] and (ev.get("receipt") or {}).get("carries_the_tx"))
    OUT.write_text(json.dumps(ev, indent=1, ensure_ascii=False), encoding="utf-8")
    print("OK" if ev["ok"] else "FAIL", "http", ev["http"], "tx", tx, "block", ev["chain"]["block"], "receipt", did, "carries tx", (ev.get("receipt") or {}).get("carries_the_tx"))
asyncio.run(main())
