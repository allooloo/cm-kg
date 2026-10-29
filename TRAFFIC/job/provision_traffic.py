r"""provision_traffic.py — SITE-04: the Container Apps job cmkg-traffic-nightly in allooloo-cmkg-eastus (Allooloo tenant), nightly 02:30 UTC, on traffic-run:<tag>.
Same shape as provision_eco.py: created on the default image, system identity, AcrPull, then registry by identity + the real image.
Roles (least privilege): AcrPull on allooloocmkg · Key Vault Secrets User on allooloo-cmkg-kv-apex (cloudflare-analytics-token by reference) ·
Storage Blob Data Contributor on allooloocmkgapex/ops only (traffic/<date>/ + traffic/latest.json). Usage: python -X utf8 provision_traffic.py <tag>"""
import sys, os, json, subprocess, time
TENANT = "04a24e43-dc13-4578-950a-910db076a799"; SUB = "038b49c0-5a0c-46f7-bd34-41ee6d087b41"
RG = "allooloo-cmkg-eastus"; JOB = "cmkg-traffic-nightly"; ACR = "allooloocmkg"; KV = "allooloo-cmkg-kv-apex"; CRON = "30 2 * * *"; tag = sys.argv[1]
def az(*a, raw=False, check=True):
    p = subprocess.run(["az", *a] + ([] if raw else ["-o", "json"]), capture_output=True, text=True, encoding="utf-8", errors="replace", shell=(os.name == "nt"))
    if p.returncode:
        if check: raise SystemExit("az %s failed: %s" % (" ".join(a[:5]), (p.stderr or p.stdout)[-500:]))
        return None
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
acct = az("account", "show")
if acct["tenantId"] != TENANT or acct["id"] != SUB: raise SystemExit("STOP: not the Allooloo tenant/subscription of record")
server = az("acr", "show", "-n", ACR, "--query", "loginServer", "-o", "tsv", raw=True); image = "%s/traffic-run:%s" % (server, tag)
env = next(e["name"] for e in az("containerapp", "env", "list", "-g", RG) if e["properties"]["provisioningState"] == "Succeeded")
base = ["OPS_ACCOUNT=allooloocmkgapex", "OPS_CONTAINER=ops", "CLOUDFLARE_ACCOUNT_ID=dd2832b36f171b815f84c8487aada36b", "ROSTER_XLSX=/app/roster.xlsx", "OUT_DIR=/tmp/traffic", "IMAGE_TAG=" + tag]
if not az("containerapp", "job", "show", "-n", JOB, "-g", RG, check=False):
    az("containerapp", "job", "create", "-n", JOB, "-g", RG, "--environment", env, "--trigger-type", "Schedule", "--cron-expression", CRON, "--replica-timeout", "3600",
       "--replica-retry-limit", "0", "--replica-completion-count", "1", "--parallelism", "1", "--cpu", "0.5", "--memory", "1Gi", "--mi-system-assigned",
       "--env-vars", *base, "--tags", "order=SITE-04", "role=traffic-nightly", "clock=02:30_UTC")
    print("created", JOB, CRON, "UTC")
pid = az("containerapp", "job", "show", "-n", JOB, "-g", RG, "--query", "identity.principalId", "-o", "tsv", raw=True)
sa = az("storage", "account", "show", "-n", "allooloocmkgapex", "-g", "allooloo-cmkg-shared", "--query", "id", "-o", "tsv", raw=True)
roles = [("AcrPull", az("acr", "show", "-n", ACR, "--query", "id", "-o", "tsv", raw=True)), ("Key Vault Secrets User", az("keyvault", "show", "-n", KV, "--query", "id", "-o", "tsv", raw=True)),
         ("Storage Blob Data Contributor", sa + "/blobServices/default/containers/ops")]
for role, scope in roles:
    ok = False
    for i in range(8):
        if az("role", "assignment", "create", "--role", role, "--assignee-object-id", pid, "--assignee-principal-type", "ServicePrincipal", "--scope", scope, check=False) is not None: ok = True; break
        time.sleep(15)
    print(" ", role, scope.split("/")[-1], "ok" if ok else "FAILED")
az("containerapp", "job", "registry", "set", "-n", JOB, "-g", RG, "--server", server, "--identity", "system")
az("containerapp", "job", "secret", "set", "-n", JOB, "-g", RG, "--secrets", "cloudflare-analytics-token=keyvaultref:https://%s.vault.azure.net/secrets/cloudflare-analytics-token,identityref:system" % KV)
az("containerapp", "job", "update", "-n", JOB, "-g", RG, "--image", image, "--container-name", JOB, "--set-env-vars", *base, "CLOUDFLARE_ANALYTICS_TOKEN=secretref:cloudflare-analytics-token")
j = az("containerapp", "job", "show", "-n", JOB, "-g", RG)
print(json.dumps({"job": JOB, "image": j["properties"]["template"]["containers"][0]["image"], "cron": j["properties"]["configuration"]["scheduleTriggerConfig"]["cronExpression"], "principal": pid}))
