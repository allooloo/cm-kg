r"""provision_eco.py — ECO-01 RUN: the Container Apps job eco-refresh in allooloo-cmkg-eastus (Allooloo tenant), weekly Sunday 05:00 UTC.
Same shape as provision_jobs.py: created on the default image, system identity, AcrPull, then registry by identity + the real image.
Roles (least privilege): AcrPull on allooloocmkg · Key Vault Secrets User on allooloo-cmkg-kv-apex (cloudflare-d1-token by reference) ·
Storage Blob Data Contributor on allooloocmkgapex/ops only (the pond drops eco/refresh/<date>/ and digest/rows/<date>/eco-refresh.json).
Ark off (ARK_ENABLED=0) until s3://allooloo-ark-eco exists with Object Lock and the ark writer's policy (the CEO's hand); then:
  az containerapp job update -n eco-refresh -g allooloo-cmkg-eastus --set-env-vars ARK_ENABLED=1 AWS_ACCESS_KEY_ID=secretref:ark-aws-key-id AWS_SECRET_ACCESS_KEY=secretref:ark-aws-secret
Usage: python -X utf8 provision_eco.py <tag>"""
import sys, os, json, subprocess, time
TENANT = "04a24e43-dc13-4578-950a-910db076a799"; SUB = "038b49c0-5a0c-46f7-bd34-41ee6d087b41"
RG = "allooloo-cmkg-eastus"; JOB = "eco-refresh"; ACR = "allooloocmkg"; KV = "allooloo-cmkg-kv-apex"; CRON = "0 5 * * 0"; tag = sys.argv[1]
def az(*a, raw=False, check=True):
    p = subprocess.run(["az", *a] + ([] if raw else ["-o", "json"]), capture_output=True, text=True, encoding="utf-8", errors="replace", shell=(os.name == "nt"))
    if p.returncode:
        if check: raise SystemExit("az %s failed: %s" % (" ".join(a[:5]), (p.stderr or p.stdout)[-500:]))
        return None
    return p.stdout.strip() if raw else (json.loads(p.stdout) if p.stdout.strip() else None)
acct = az("account", "show")
if acct["tenantId"] != TENANT or acct["id"] != SUB: raise SystemExit("STOP: not the Allooloo tenant/subscription of record")
server = az("acr", "show", "-n", ACR, "--query", "loginServer", "-o", "tsv", raw=True); image = "%s/eco-refresh:%s" % (server, tag)
env = next(e["name"] for e in az("containerapp", "env", "list", "-g", RG) if e["properties"]["provisioningState"] == "Succeeded")
base = ["OPS_ACCOUNT=allooloocmkgapex", "OPS_CONTAINER=ops", "CLOUDFLARE_ACCOUNT_ID=dd2832b36f171b815f84c8487aada36b", "WRANGLER_SEND_METRICS=false", "CI=1",
        "ARK_ENABLED=0", "ARK_BUCKET=allooloo-ark-eco", "ARK_REGION=us-east-1", "IMAGE_TAG=" + tag]
if not az("containerapp", "job", "show", "-n", JOB, "-g", RG, check=False):
    az("containerapp", "job", "create", "-n", JOB, "-g", RG, "--environment", env, "--trigger-type", "Schedule", "--cron-expression", CRON, "--replica-timeout", "3600",
       "--replica-retry-limit", "0", "--replica-completion-count", "1", "--parallelism", "1", "--cpu", "0.5", "--memory", "1Gi", "--mi-system-assigned",
       "--env-vars", *base, "--tags", "order=ECO-01", "role=eco-refresh", "clock=Sunday_05:00_UTC")
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
az("containerapp", "job", "secret", "set", "-n", JOB, "-g", RG, "--secrets", "cloudflare-d1-token=keyvaultref:https://%s.vault.azure.net/secrets/cloudflare-d1-token,identityref:system" % KV)
az("containerapp", "job", "update", "-n", JOB, "-g", RG, "--image", image, "--container-name", JOB, "--set-env-vars", *base, "CLOUDFLARE_API_TOKEN=secretref:cloudflare-d1-token")
j = az("containerapp", "job", "show", "-n", JOB, "-g", RG)
print(json.dumps({"job": JOB, "image": j["properties"]["template"]["containers"][0]["image"], "cron": j["properties"]["configuration"]["scheduleTriggerConfig"]["cronExpression"], "principal": pid}))
