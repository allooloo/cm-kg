"""Roll the eleven CM-KG node doors 0.11.0 -> 0.12.1 one at a time (CEO order 2026-09-17 item 4). FROM-live image cmkg-door:0.12.1
(version line only). Own anchor per door = the revision and image before. Gate per door: initialize version, tools/list 5, CMR headers
(X-CMR-As-Of present), resolve_issuer valid input ok, bad input typed. Stops on the first failing gate."""
import subprocess, json, sys, os, time
sys.path.insert(0, r"C:\PADEL\harness")
from common import Door, headers_allooloo, classify_call, body_head
IMG = "allooloocmkg.azurecr.io/cmkg-door:0.12.1"
NODES = [("ca", "allooloo-cmkg-canadacentral", "TSX:SHOP"), ("us", "allooloo-cmkg-eastus", "AAPL"), ("uk", "allooloo-cmkg-uksouth", "LSE:SHEL"), ("de", "allooloo-cmkg-germanywestcentral", "SAP"),
         ("fr", "allooloo-cmkg-francecentral", "FR0000120271"), ("nl", "allooloo-cmkg-westeurope", "NL0000009165"), ("ch", "allooloo-cmkg-switzerlandnorth", "NESN"), ("au", "allooloo-cmkg-australiaeast", "ASX:BHP"),
         ("sg", "allooloo-cmkg-southeastasia", "D05"), ("jp", "allooloo-cmkg-japaneast", "7203.T"), ("kr", "allooloo-cmkg-koreacentral", "005930.KS")]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "roll.json")
rep = json.load(open(OUT)) if os.path.exists(OUT) else {}


def az(cmd):
    r = subprocess.run("az " + cmd, capture_output=True, text=True, shell=True, timeout=900)
    return (r.stdout or "") + (r.stderr or "")


def gate(cc, ident):
    d = Door(f"https://mcp.{cc}-cm-kg.ai/mcp"); ini = d.initialize(); si = ((ini.get("json") or {}).get("result") or {}).get("serverInfo") or {}
    tl = d.tools_list(); n = len(((tl.get("json") or {}).get("result") or {}).get("tools") or [])
    h = headers_allooloo(ini.get("headers") or {})
    ok = classify_call(d.call("resolve_issuer", {"identifier": ident}, 5)) == "ok"
    bad = classify_call(d.call("resolve_issuer", {"identifier": "ZZZZ-NOT-A-TICKER"}, 6), bad=True)
    g = {"version": si.get("version"), "tools": n, "headers": h, "valid_ok": ok, "bad": bad}
    g["PASS"] = si.get("version") == "0.12.1" and n == 5 and h.get("ok") and ok and bad in ("typed_error", "typed_body")
    return g


for cc, rg, ident in NODES:
    app = f"cmkg-door-{cc}"
    if rep.get(cc, {}).get("gate", {}).get("PASS"):
        print(cc, "already rolled and gated"); continue
    before = json.loads(az(f"containerapp show -n {app} -g {rg} --query \"{{rev:properties.latestRevisionName,image:properties.template.containers[0].image}}\" -o json").split("WARNING")[0] or "{}")
    pre = gate(cc, ident)
    out = az(f"containerapp update -n {app} -g {rg} --image {IMG} --revision-suffix v0121-0917 --query \"{{rev:properties.latestRevisionName,state:properties.provisioningState}}\" -o json")
    try:
        after = json.loads(out[out.index("{"):out.rindex("}") + 1])
    except Exception:
        after = {"error": out[-300:]}
    time.sleep(25)
    g = gate(cc, ident)
    rep[cc] = {"app": app, "rg": rg, "anchor": before, "version_before": pre.get("version"), "rolled": after, "gate": g}
    json.dump(rep, open(OUT, "w"), indent=1)
    print(json.dumps({cc: {"before": pre.get("version"), "after": g.get("version"), "rev": after.get("rev"), "PASS": g["PASS"], "headers_ok": g["headers"].get("ok"), "as_of": g["headers"].get("as_of")}}), flush=True)
    if not g["PASS"]:
        print("GATE FAILED on", cc, "- stopping the roll; anchor", before); sys.exit(1)
print("ALL ELEVEN ROLLED")
