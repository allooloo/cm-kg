"""Azure CLI one-root guard (STANDING RULE, CEO Sept 13 2026): before any Azure write, confirm tenant, subscription and signed-in user match the Allooloo estate; stop if not.
Use:  from az_guard import require_allooloo; require_allooloo()"""
import json, subprocess, sys
TENANT = '04a24e43-dc13-4578-950a-910db076a799'
SUBSCRIPTION = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'
USER_SUFFIX = 'allooloo296.onmicrosoft.com'
def context():
    r = subprocess.run(['az', 'account', 'show', '-o', 'json'], capture_output=True, text=True, shell=True)
    if r.returncode != 0: return None
    try: return json.loads(r.stdout)
    except Exception: return None
def require_allooloo():
    c = context()
    if not c: sys.exit('az_guard: no az context (az login --tenant ' + TENANT + ') — STOP')
    user = (c.get('user') or {}).get('name', '')
    ok = c.get('tenantId') == TENANT and c.get('id') == SUBSCRIPTION and user.endswith(USER_SUFFIX)
    line = f"az context: tenant {c.get('tenantId')} · subscription {c.get('id')} · user {user}"
    if not ok: sys.exit('az_guard: CLI context is not the Allooloo estate — STOP. ' + line + f'. Expected tenant {TENANT}, subscription {SUBSCRIPTION}, user *@{USER_SUFFIX}. Take the CLI back with: az account set --subscription {SUBSCRIPTION}; az account show')
    print(line + ' — Allooloo, confirmed')
    return c
if __name__ == '__main__': require_allooloo()
