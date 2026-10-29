r"""row_register.py — NODE-ROW-01…09 (DAY ORDER 5, 2026-10-24): the nine markets join every map the NODE-EU chain reads, so a ROW node closes on the same
rails (eu_node.py · load_nodes.py · provision_region.py · provision_jobs.py · job_node.py · apex_join.py). Idempotent; .pre-row-20261024 beside each file.
Store region = the Azure region in the country, else the nearest (flagged); door + job in the nearest existing environment (subscription at its 16-environment
maximum, ENV_HOST); nightly 02:00 local standard time as a fixed UTC cron; ark region in or nearest the country; lab keys by reference from the nearest vault.
Sources: RAILS\row-sources\<cc>\ (eu_node.py falls back there). Usage: python -X utf8 -I row_register.py"""
import io, os, re, shutil
R = r'C:\ALLOOLOO'
ROW = {  # cc: (country, store region, door env region, std offset hours, ark region, vault)
    'ky': ('Cayman Islands', 'eastus', 'eastus', -5, 'us-east-1', 'allooloo-cmkg-kv-us'),
    'bm': ('Bermuda', 'eastus', 'eastus', -4, 'us-east-1', 'allooloo-cmkg-kv-us'),
    'je': ('Jersey', 'uksouth', 'uksouth', 0, 'eu-west-2', 'allooloo-cmkg-kv-uk'),
    'in': ('India', 'centralindia', 'southeastasia', 5.5, 'ap-south-1', 'allooloo-cmkg-kv-sg'),
    'tw': ('Taiwan', 'eastasia', 'eastasia', 8, 'ap-east-2', 'allooloo-cmkg-kv-sg'),
    'sa': ('Saudi Arabia', 'qatarcentral', 'italynorth', 3, 'me-central-1', 'allooloo-cmkg-kv-fr'),
    'ae': ('United Arab Emirates', 'uaenorth', 'italynorth', 4, 'me-central-1', 'allooloo-cmkg-kv-fr'),
    'br': ('Brazil', 'brazilsouth', 'eastus', -3, 'sa-east-1', 'allooloo-cmkg-kv-us'),
    'mx': ('Mexico', 'mexicocentral', 'eastus', -6, 'mx-central-1', 'allooloo-cmkg-kv-us'),
}
def edit(path, fn):
    t = io.open(path, encoding='utf-8', newline='').read(); n = fn(t)
    if n != t:
        if not os.path.exists(path + '.pre-row-20261024'): shutil.copy2(path, path + '.pre-row-20261024')
        io.open(path, 'w', encoding='utf-8', newline='').write(n); print('edited', path)
    else: print('unchanged', path)
TAG = '   # NODE-ROW (DAY ORDER 5, 2026-10-24)'
names = ', '.join(f"'{c}': '{v[0]}'" for c, v in ROW.items())
# load_nodes.py: names
edit(os.path.join(R, r'CM-KG\RAILS\door\load_nodes.py'), lambda t: t if "'ky': 'Cayman Islands'" in t else t.replace("'cz': 'Czech Republic'}", "'cz': 'Czech Republic', " + names + "}" + TAG, 1))
# apex_join.py: names; HOME skipped for ky bm je (an incorporation prefix, not a listing home); EU_DOOR only for the European nodes (a ROW node has its own zone)
def aj(t):
    if "'ky': 'Cayman Islands'" in t: return t
    t = t.replace("'cz': 'Czech Republic'}", "'cz': 'Czech Republic', " + names + "}", 1)
    t = t.replace("if 'const EU_DOOR = ' not in t:", "ROW = " + repr(list(ROW)) + TAG + ": own zone (mcp.<cc>-cm-kg.ai) — never in EU_DOOR; ky bm je never in HOME (KY/BM/JE ISINs are incorporation prefixes, the listings sit on HKEX, LSE and others)\nif cc not in ROW and 'const EU_DOOR = ' not in t:", 1)
    t = t.replace("if f\"'{node}': 'https://{fqdn}'\" not in t.split('const PUBLIC')[0].split('const EU_DOOR')[1] if 'const EU_DOOR' in t else True:", "if cc not in ROW and (f\"'{node}': 'https://{fqdn}'\" not in t.split('const PUBLIC')[0].split('const EU_DOOR')[1] if 'const EU_DOOR' in t else True):", 1)
    t = t.replace("if f\"{cc.upper()}: '{node}'\" not in t:", "if cc not in ('ky', 'bm', 'je') and f\"{cc.upper()}: '{node}'\" not in t:", 1)
    t = t.replace("nodes.append({'node': node, 'country': NAMES[cc], 'registry': None, 'door': f'https://{fqdn}',", "nodes.append({'node': node, 'country': NAMES[cc], 'registry': None, 'door': f'https://mcp.{node}.ai' if cc in ROW else f'https://{cc}.eu-cm-kg.ai' if cc != 'lu' else 'https://mcp.lu-cm-kg.ai',", 1)
    return t
edit(os.path.join(R, r'CM-KG\RAILS\eu-node\apex_join.py'), aj)
# eu_node.py: sources from row-sources when the market has no eu-sources folder
edit(os.path.join(R, r'CM-KG\RAILS\eu-node\eu_node.py'), lambda t: t if 'row-sources' in t else t.replace("    p = os.path.join(RAILS, 'eu-sources', CC, name + '.py')", "    p = os.path.join(RAILS, 'eu-sources', CC, name + '.py')\n    if not os.path.exists(p): p = os.path.join(RAILS, 'row-sources', CC, name + '.py')" + TAG, 1))
# job_node.py: standard offsets (India +5:30)
edit(os.path.join(R, r'CM-KG\RAILS\job\job_node.py'), lambda t: t if "'ky': -5" in t else t.replace("'cz': 1})   # NODE-EU (2026-10-24)", "'cz': 1})   # NODE-EU (2026-10-24)\nSTD_OFFSET.update({" + ', '.join(f"'{c}': {v[3]}" for c, v in ROW.items()) + "})" + TAG, 1))
# provision_jobs.py: region, ark, offset, vault, environment host; the cron in minutes (India's half hour)
def pj(t):
    if "ROW_NODES" in t: return t
    add = ("ROW_NODES = {" + ', '.join(f"'{c}': '{v[1]}'" for c, v in ROW.items()) + "}" + TAG + "\n"
           "ROW_ARK = {" + ', '.join(f"'{c}': '{v[4]}'" for c, v in ROW.items()) + "}\n"
           "ROW_STD = {" + ', '.join(f"'{c}': {v[3]}" for c, v in ROW.items()) + "}\n"
           "ROW_KV = {" + ', '.join(f"'{c}': '{v[5]}'" for c, v in ROW.items()) + "}\n"
           "for _cc, _r in ROW_NODES.items():\n    _m = int(round((2 - ROW_STD[_cc]) * 60)) % 1440; NODES[_cc] = _r; ARK[_cc] = ROW_ARK[_cc]; NIGHTLY[_cc] = f\"{_m % 60} {_m // 60} * * *\"; KV[_cc] = ROW_KV[_cc]\n")
    t = t.replace("ENV_HOST = {'be': 'westeurope',", add + "ENV_HOST = {'be': 'westeurope',", 1)
    t = re.sub(r"(ENV_HOST = \{[^\n]*?'cz': 'germanywestcentral')\}", lambda m: m.group(1) + ", " + ', '.join(f"'{c}': '{v[2]}'" for c, v in ROW.items()) + "}", t, count=1)
    return t
edit(os.path.join(R, r'CM-KG\RAILS\job\provision_jobs.py'), pj)
edit(os.path.join(R, r'AZURE\provision_region.py'), lambda t: t if "'ky': 'eastus'" in t else re.sub(r"(ENV_HOST = \{[^\n]*?'cz': 'germanywestcentral')\}", lambda m: m.group(1) + ", " + ', '.join(f"'{c}': '{v[2]}'" for c, v in ROW.items()) + "}", t, count=1))
import json
json.dump({c: {'country': v[0], 'store_region': v[1], 'door_region': v[2], 'std': v[3], 'ark': v[4], 'vault': v[5]} for c, v in ROW.items()}, open(os.path.join(R, r'CM-KG\RAILS\zones-do5\row-nodes-plan.json'), 'w'), indent=1)
