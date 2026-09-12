"""NUMBERS LOG (NODE-SURFACES.md §9): one line per sweep per node — node · date · records · events · delta — read from the apex list_nodes after the
store reload, appended to the boot file's fenced block, and mirrored to CM-KG\ESTATE\public\numbers-log.json (the static asset RADAR widgets 03/06 read).
Usage: python numbers_log.py <cc> [cc ...]   (no args: mirror only, no new lines)."""
import json, os, re, sys, datetime, requests
ROOT = r'C:\ALLOOLOO'; BOOT = os.path.join(ROOT, 'START_ME_UP', 'NODE-SURFACES.md'); ASSET = os.path.join(ROOT, 'CM-KG', 'ESTATE', 'public', 'numbers-log.json')
APEX = 'https://mcp.capitalmarketsknowledgegraph.ai/mcp'
def live():
    r = requests.post(APEX, headers={'content-type': 'application/json', 'accept': 'application/json'}, json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'list_nodes', 'arguments': {}}}, timeout=60).json()
    return {n['node']: n for n in r['result']['structuredContent']['nodes']}
s = open(BOOT, encoding='utf-8').read()
m = re.search(r'(## 9 NUMBERS LOG[\s\S]*?```\n)([\s\S]*?)(```)', s); assert m, 'NUMBERS LOG block not found'
lines = [l for l in m.group(2).splitlines() if l.strip()]
def parse(l):
    p = [x.strip() for x in l.split('·')]
    return {'node': p[0], 'date': p[1], 'records': p[2], 'events': p[3], 'note': '·'.join(p[4:]).strip() if len(p) > 4 else ''}
if sys.argv[1:]:
    L = live(); today = datetime.date.today().isoformat()
    for cc in sys.argv[1:]:
        node = f'{cc}-cm-kg'; n = L.get(node, {})
        prev = [parse(l) for l in lines if l.startswith(node + ' ')]; last = prev[-1] if prev else None
        if not n.get('live'):
            lines.append(f'{node} · {today} · not served (Width 0) · none · sweep: no door'); continue
        rec, ev = int(n.get('records') or 0), int(n.get('events') or 0)
        try: dr, de = rec - int(last['records']), ev - int(last['events'])
        except Exception: dr, de = None, None
        delta = f'records {dr:+d} · events {de:+d}' if dr is not None else 'first line'
        lines.append(f"{node} · {n.get('as_of') or today} · {rec} · {ev} · {delta} (sweep {today})")
        print(lines[-1])
    s = s[:m.start(2)] + '\n'.join(lines) + '\n' + s[m.start(3):]
    open(BOOT, 'w', encoding='utf-8').write(s)
rows = [parse(l) for l in lines]
json.dump({'as_of': datetime.date.today().isoformat(), 'source': 'START_ME_UP/NODE-SURFACES.md §9 NUMBERS LOG (one line per sweep per node; counts from list_nodes after the store reload)', 'lines': rows}, open(ASSET, 'w', encoding='utf-8'), indent=1)
print('numbers-log.json', len(rows), 'lines')
