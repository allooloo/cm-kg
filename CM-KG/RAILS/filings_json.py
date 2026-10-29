r"""RADAR-02 (2026-10-23) — CM-KG/ESTATE/public/filings.json rewritten from what answers. Run by the apex job every night before the estate deploy, and by hand.
  MCP registry      registry.modelcontextprotocol.io v0.1 — both cards (io.github.allooloo/cm-kg, io.github.allooloo/issuerwire): latest version and its publish date
  Azure API Center  allooloo-apic (allooloo-cmkg-shared) — the APIs registered, read with az (the job identity, or the laptop login)
  Anthropic         the Claude directory listing — the page sits behind a sign-in (403 to a plain read): state as reported by the CEO, the URL printed
  Google            the Agent Registry entry — no public read endpoint: state as reported by the CEO (registered 2026-09-13)
A line that does not answer says so with the time tried; nothing is typed in place of a read."""
import os, sys, json, subprocess, datetime, urllib.request
ROOT = os.environ.get('CMKG_ROOT', r'C:\ALLOOLOO' if os.name == 'nt' else '/job/ALLOOLOO'); OUT = os.path.join(ROOT, 'CM-KG', 'ESTATE', 'public', 'filings.json')
SUB = '038b49c0-5a0c-46f7-bd34-41ee6d087b41'; APIC = f'/subscriptions/{SUB}/resourceGroups/allooloo-cmkg-shared/providers/Microsoft.ApiCenter/services/allooloo-apic'
NOW = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def get(url, t=20):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Allooloo filings_json (RADAR-02)', 'Accept': 'application/json'}), timeout=t))
def card(name):
    try:
        j = get(f'https://registry.modelcontextprotocol.io/v0.1/servers/io.github.allooloo%2F{name}/versions'); vs = j.get('servers') or []
        lt = [s for s in vs if ((s.get('_meta') or {}).get('io.modelcontextprotocol.registry/official') or {}).get('isLatest')]
        if not lt: return {'registry': 'MCP registry', 'entry': f'io.github.allooloo/{name}', 'state': f'{len(vs)} versions, none marked latest', 'as_of': NOW, 'read': 'answered'}
        m = lt[0]['_meta']['io.modelcontextprotocol.registry/official']
        return {'registry': 'MCP registry', 'entry': f'io.github.allooloo/{name}', 'state': f"live · latest {lt[0]['server']['version']} (published {str(m.get('publishedAt', ''))[:10]}) · {len(vs)} versions", 'as_of': NOW, 'read': 'answered',
                'url': f'https://registry.modelcontextprotocol.io/v0.1/servers/io.github.allooloo%2F{name}/versions'}
    except Exception as e: return {'registry': 'MCP registry', 'entry': f'io.github.allooloo/{name}', 'state': f'did not answer ({type(e).__name__})', 'as_of': NOW, 'read': 'tried'}
def apic():
    try:
        p = subprocess.run(['az', 'rest', '--method', 'get', '--url', f'https://management.azure.com{APIC}/workspaces/default/apis?api-version=2024-03-01', '-o', 'json'], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           shell=(os.name == 'nt'), env=dict(os.environ, MSYS_NO_PATHCONV='1'), timeout=120)
        if p.returncode != 0: raise RuntimeError((p.stderr or '')[-160:])
        apis = [a['name'] for a in json.loads(p.stdout).get('value', [])]
        return {'registry': 'Azure API Center', 'entry': 'allooloo-apic', 'state': f"live · {len(apis)} APIs registered: {', '.join(apis)}", 'as_of': NOW, 'read': 'answered', 'apis': apis}
    except Exception as e: return {'registry': 'Azure API Center', 'entry': 'allooloo-apic', 'state': f'did not answer ({str(e)[:120]})', 'as_of': NOW, 'read': 'tried'}
def anthropic():
    url = 'https://claude.ai/directory/manage/capital-markets-knowledge-graph-allooloo'
    try: code = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).status
    except urllib.error.HTTPError as e: code = e.code
    except Exception: code = None
    return {'registry': 'Anthropic — Claude directory', 'entry': url, 'state': 'live (as reported by the CEO, 2026-10-22)', 'as_of': NOW, 'read': f'as reported — the listing page is behind a sign-in (HTTP {code} to a plain read)'}
def google():
    return {'registry': 'Google — Agent Registry', 'entry': 'Capital Markets Knowledge Graph (Allooloo)', 'state': 'registered 2026-09-13 (as reported by the CEO)', 'as_of': '2026-09-13', 'read': 'as reported — no public read endpoint'}
out = {'as_of': NOW, 'source': 'CM-KG/RAILS/filings_json.py — rewritten from what answers (nightly in the apex job, before the estate deploy)',
       'filings': [card('cm-kg'), card('issuerwire'), anthropic(), google(), apic()]}
json.dump(out, open(OUT, 'w', encoding='utf-8', newline='\n'), indent=1, ensure_ascii=False)
for f in out['filings']: print(f"{f['registry']} · {f['entry']} · {f['state'][:140]} · {f['read']}")
