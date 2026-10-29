r"""roster.py — ENUM-01 (DAY ORDER 6, 2026-10-25): one market roster, read everywhere.
The roster of record is the apex nodes.json (CM-KG\DOOR\apex\static\nodes.json, served by list_nodes on mcp.getissuer.ai); counts are facts.json.
Nothing on the estate holds its own copy of the market list. Every rail reads it through here:
  load()                 the roster entries, live list first from list_nodes, then the file in this tree/image (the same nodes.json)
  codes() / region(cc)   the live market codes (ca, uk ... in), and a node's store region (region.store, read from Azure by nodes_region.py)
  require(name, policy)  policy keyed by market (ISIN tiebreak, halt source, NOT_BEFORE, tabs, backfill sources ...) stays explicit — but a rail refuses to
                         run when a roster entry has no line in it; the gap is printed and the rail exits (never skipped silently)
Dry run (ENUM-01 proof one): ROSTER_FILE=<a copy of nodes.json> points every rail at that copy; ROSTER_OFFLINE=1 skips list_nodes.
One copy per rails folder (the pond rule); the copies are identical."""
import os, json, urllib.request
ROSTER_FILE = os.environ.get('ROSTER_FILE') or r'C:\ALLOOLOO\CM-KG\DOOR\apex\static\nodes.json'
APEX = os.environ.get('ROSTER_APEX', 'https://mcp.getissuer.ai/mcp')
_CACHE = None
def _from_apex():
    req = urllib.request.Request(APEX, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'list_nodes', 'arguments': {}}}).encode(),
                                 headers={'content-type': 'application/json', 'accept': 'application/json', 'User-Agent': 'Allooloo roster (ENUM-01)'})
    with urllib.request.urlopen(req, timeout=30) as r: j = json.load(r)
    return j['result']['structuredContent']['nodes']
def load(live_only=True):
    """the roster entries; list_nodes when it answers (the served roster), else the file. ROSTER_FILE set = that file only (dry run)."""
    global _CACHE
    if _CACHE is None:
        nodes = None
        if not os.environ.get('ROSTER_FILE') and os.environ.get('ROSTER_OFFLINE') != '1':
            try: nodes = _from_apex()
            except Exception: nodes = None
        if nodes is None: nodes = json.load(open(ROSTER_FILE, encoding='utf-8'))
        _CACHE = nodes
    return [n for n in _CACHE if n.get('live') or not live_only]
def cc_of(n): return n['node'].split('-')[0]
def codes(live_only=True): return [cc_of(n) for n in load(live_only)]
def entry(cc): return next((n for n in load(False) if cc_of(n) == cc), None)
def region(cc):
    e = entry(cc) or {}; return (e.get('region') or {}).get('store')
def count(): return len(load())
def gaps(policy, cc_list=None):
    return [cc for cc in (cc_list or codes()) if cc not in policy]
def require(name, policy, cc_list=None, exit=True):
    """ENUM-01 (b): a policy keyed by market must carry a line for every roster entry; a gap stops the rail and is named."""
    g = gaps(policy, cc_list)
    if g and exit: raise SystemExit(f'ROSTER POLICY GAP · {name} · no line for: {", ".join(g)} (roster {ROSTER_FILE if os.environ.get("ROSTER_FILE") else "list_nodes"}) — rail refused')
    return g
