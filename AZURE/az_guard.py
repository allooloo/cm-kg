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

def require_github(account='allooloo'):
    """Before any registry publish or push: the active gh account must be the estate's own; switch if another is active; stop if it is not in the keyring."""
    st = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True, shell=True); out = (st.stdout or '') + (st.stderr or '')
    if f'account {account}' not in out: sys.exit(f'gh_guard: GitHub account {account} is not in the gh keyring — STOP (gh auth login as {account})')
    active = None
    for block in out.split('Logged in to github.com account')[1:]:
        name = block.split()[0]
        if 'Active account: true' in block: active = name
    if active != account:
        sw = subprocess.run(['gh', 'auth', 'switch', '--user', account], capture_output=True, text=True, shell=True)
        if sw.returncode != 0: sys.exit(f'gh_guard: could not switch gh to {account} — STOP: {(sw.stderr or sw.stdout)[:120]}')
        print(f'gh account: was {active}, switched to {account}')
    else: print(f'gh account: {account} — active, confirmed')
    return account

if __name__ == '__main__': require_allooloo(); require_github('allooloo')
