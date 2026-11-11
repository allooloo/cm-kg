"""MAIL-01 item 5 proof: one test message to ops@agent-bev.ai, sent from ops@allooloo.ai (Allooloo's ops address) through Allooloo's ACS
(allooloo-ops-acs), Entra token of the signed-in Allooloo user. Never from gsc-em.com, never from the HEY box. Allooloo guard runs first."""
import json, subprocess, sys, time, urllib.request, urllib.error
sys.path.insert(0, r"C:\ALLOOLOO\AZURE")
PY = r"C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe"
def az(*a):
    r = subprocess.run([PY, "-IBm", "azure.cli", *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode: raise SystemExit(" ".join(a[:3]) + " failed: " + r.stderr.strip()[-300:])
    return r.stdout.strip()
c = json.loads(az("account", "show", "-o", "json"))
assert c["tenantId"] == "04a24e43-dc13-4578-950a-910db076a799" and c["id"] == "038b49c0-5a0c-46f7-bd34-41ee6d087b41" and c["user"]["name"].endswith("allooloo296.onmicrosoft.com"), "not the Allooloo root"
host = az("resource", "show", "-g", "allooloo-cmkg-shared", "-n", "allooloo-ops-acs", "--resource-type", "Microsoft.Communication/CommunicationServices", "--query", "properties.hostName", "-o", "tsv")
tok = json.loads(az("account", "get-access-token", "--resource", "https://communication.azure.com", "-o", "json"))["accessToken"]
body = {"senderAddress": "ops@allooloo.ai", "recipients": {"to": [{"address": "ops@agent-bev.ai"}]},
        "content": {"subject": "MAIL-01 routing test — ops@agent-bev.ai", "plainText": "MAIL-01 (2026-11-11): one test message to ops@agent-bev.ai, to prove the Cloudflare Email Routing rule delivers. No action needed."}}
req = urllib.request.Request(f"https://{host}/emails:send?api-version=2023-03-31", json.dumps(body).encode(), {"content-type": "application/json", "authorization": f"Bearer {tok}"})
try:
    r = urllib.request.urlopen(req, timeout=60); op = json.loads(r.read() or b"{}"); print("sent:", r.status, "operation", op.get("id"), "at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
except urllib.error.HTTPError as e: print("send refused:", e.code, e.read()[:300])
