r"""nodes_region.py — DAY ORDER 5 (CEO 2026-10-25): the region of every node on the roster of record, CM-KG\DOOR\apex\static\nodes.json (what list_nodes serves).
Read from Azure, never typed: the node store's location (storage account allooloocmkg<cc>pond) and its door's location (Container App cmkg-door-<cc>), named by
Azure's own location list (displayName, and metadata.physicalLocation for the city). Each entry gains region = {azure, city, store, door} (azure/city = the store,
where the record sits; door = where it is served when that differs). Run after every apex join (eu_close.sh, row_close.sh) and by hand. .pre copy per day beside.
Usage: python -X utf8 -I nodes_region.py"""
import os, json, shutil, subprocess, datetime
NJ = r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json'
ENV = dict(os.environ, AZURE_CONFIG_DIR=r'C:\ALLOOLOO\.azure', MSYS_NO_PATHCONV='1'); AZ = [r'C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe', '-IX', 'utf8', '-m', 'azure.cli']
def az(*a): return json.loads(subprocess.run([*AZ, *a, '-o', 'json'], capture_output=True, text=True, env=ENV, encoding='utf-8').stdout or 'null')
locs = {l['name']: (l['displayName'], (l.get('metadata') or {}).get('physicalLocation')) for l in az('account', 'list-locations')}
stores = {s['name']: s['location'] for s in az('storage', 'account', 'list', '--query', "[?starts_with(name,'allooloocmkg') && ends_with(name,'pond')].{name:name,location:location}")}
doors = {a['name']: a['location'].lower().replace(' ', '') for a in az('containerapp', 'list', '--query', "[?starts_with(name,'cmkg-door-')].{name:name,location:location}")}
day = datetime.date.today().strftime('%Y%m%d')
if not os.path.exists(NJ + f'.pre-region-{day}'): shutil.copy2(NJ, NJ + f'.pre-region-{day}')
nodes = json.load(open(NJ, encoding='utf-8')); n = 0
for x in nodes:
    cc = x['node'].split('-')[0]; st = stores.get(f'allooloocmkg{cc}pond'); dr = doors.get(f'cmkg-door-{cc}')
    if not st: continue
    disp, city = locs.get(st, (st, None)); ddisp = locs.get(dr, (dr, None))[0] if dr else None
    x['region'] = {'azure': disp, 'city': city, 'store': st, 'door': dr, 'door_azure': ddisp if dr and dr != st else None, 'read_from': 'Azure Resource Manager (storage account + Container App location), Azure location list'}; n += 1
json.dump(nodes, open(NJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('region on', n, 'of', len(nodes), 'roster entries')

# DAY ORDER 5 (CEO 2026-10-25): the duty line on the roster too, so every surface reads one list. The first twelve keep their published duty (products.js DUTY,
# read by node — not retyped); a European node: MiFID II product governance (the EU regime object, eu-eco.ai/eco.json); any other node: its regulator's
# disclosure rules, the regulator read from its own ECO record (<cc>-eco.ai/eco.json). Each carries duty_source.
import urllib.request
DUTY12 = json.loads(subprocess.run(['node', '-e', "import('./products.js').then(m=>process.stdout.write(JSON.stringify(m.DUTY)))"], cwd=r'C:\ALLOOLOO\CM-KG\ESTATE\worker', capture_output=True, text=True, encoding='utf-8').stdout or '{}')
EU = {'it', 'es', 'se', 'dk', 'no', 'fi', 'be', 'ie', 'at', 'pl', 'pt', 'lu', 'gr', 'cz'}   # EU and EEA (Norway is EEA); Switzerland stays FinSA (in the twelve)
DOMICILE = {'ky', 'bm', 'je'}
def eco(cc):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(f'https://{cc}-eco.ai/eco.json', headers={'User-Agent': 'Allooloo digest (nodes_region)'}), timeout=30).read())
    except Exception: return {}
for x in nodes:
    cc = x['node'].split('-')[0]
    if cc in DUTY12: x['duty'] = DUTY12[cc]; x['duty_source'] = 'ESTATE\\worker\\products.js DUTY (the published duty line)'
    elif cc in EU: x['duty'] = 'MiFID II product governance'; x['duty_source'] = 'https://eu-eco.ai/eco.json (mifid_ii_product_governance)'
    elif cc in DOMICILE: x['duty'] = 'record held by the listing market'; x['duty_source'] = 'CEO ruling 2026-10-25: a domicile carries no duty of its own'
    else:   # CEO ruling 2026-10-25: a duty line is policy keyed by market — taken only from the market's ECO record; none there, nothing printed (a gap in the report)
        dl = (((eco(cc).get('record') or {}).get('fields') or {}).get('duty') or {})
        x['duty'] = dl.get('value') if dl.get('state') == 'sourced' else None; x['duty_source'] = f'https://{cc}-eco.ai/eco.json (duty)' if x['duty'] else None; x['duty_gap'] = None if x['duty'] else 'no duty line in the ECO record'
json.dump(nodes, open(NJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('duty on', sum(1 for x in nodes if x.get('duty')), 'of', len(nodes))

# ENUM-01 (DAY ORDER 6, 2026-10-25): the market's example issuer on the roster entry too (ECO\examples.json, written at every node close — policy keyed by
# market), so the status probe and the PROMPT-01 prompt blocks read one list. A live node with no example line gets example_gap (named, never guessed).
EX = json.load(open(r'C:\ALLOOLOO\CM-KG\ECO\examples.json', encoding='utf-8'))
for x in nodes:
    e = EX.get(x['node'].split('-')[0])
    if e: x['example'] = {k: e.get(k) for k in ('ticker', 'isin', 'name', 'record_url') if e.get(k)}; x.pop('example_gap', None)
    else: x.pop('example', None); x['example_gap'] = 'no example line in ECO/examples.json'
# DOORS-02 (2026-10-26): an example must name one record on its own door. The door never guesses — an ISIN or ticker shared by two listings (a dual counter,
# a Eurex product filed under its underlying's ISIN) answers 'ambiguous' and no signed record, which is how de and hk read unsigned at COMPS-01. Each example is
# read on its door (get_record, ISIN then ticker); an ambiguous one is refused and named as example_gap, never published. A door that does not answer keeps its line.
def ambiguous(door, ident):
    try:
        b = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'get_record', 'arguments': {'identifier': ident}}}).encode()
        sc = json.loads(urllib.request.urlopen(urllib.request.Request(door, data=b, headers={'content-type': 'application/json', 'accept': 'application/json', 'User-Agent': 'Allooloo digest (nodes_region)'}), timeout=30).read())['result']['structuredContent']
        return sc.get('matches') if sc.get('error') == 'ambiguous' else None
    except Exception: return None
for x in nodes:
    e, door = x.get('example'), x.get('door')   # the roster's door (list_nodes prints it as regional_door)
    if not e or not door: continue
    door = door if door.endswith('/mcp') else door.rstrip('/') + '/mcp'
    for k in ('isin', 'ticker'):
        m = e.get(k) and ambiguous(door, e[k])
        if m:
            x.pop('example', None); x['example_gap'] = f"example {k} {e[k]} matches {len(m)} listings on the node ({', '.join(m[:4])}); ECO/examples.json needs an identifier that names one record"
            print('REFUSED', x['node'], x['example_gap']); break
json.dump(nodes, open(NJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('example on', sum(1 for x in nodes if x.get('example')), 'of', len(nodes))
