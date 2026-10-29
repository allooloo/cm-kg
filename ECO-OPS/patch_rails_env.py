r"""patch_rails_env.py — ECO-OPS-01: the SITE-03A rails take their paths and tokens from the environment when set (the nightly image), the laptop defaults
unchanged. site03a.py also writes registry.json (the GH-01 shape) into the lane on every apply. .pre copies beside."""
import shutil, re
def patch(p, pairs, tag="pre-ecoops01-20261028"):
    shutil.copy2(p, re.sub(r"(\.py)$", f".{tag}\\1", p)); s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert old in s, (p, old[:60]); s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(s); print("patched", p)
patch(r"C:\GREENCORE\PROTOCOLS\site03a.py", [
    ('ROOT = os.path.dirname(os.path.abspath(__file__)); SNAP = r"C:\\GREENCORE\\AUDITS\\GREAT-CULL-02-2026-10-10\\snapshots"',
     'ROOT = os.path.dirname(os.path.abspath(__file__)); SNAP = os.environ.get("SITE03A_SNAP") or r"C:\\GREENCORE\\AUDITS\\GREAT-CULL-02-2026-10-10\\snapshots"   # ECO-OPS-01: the nightly image sets the paths'),
    ('LANE = r"C:\\GREENCORE\\AUDITS\\SITE-03A-2026-10-28"; OUT', 'LANE = os.environ.get("SITE03A_LANE") or r"C:\\GREENCORE\\AUDITS\\SITE-03A-2026-10-28"; OUT'),
    ('os.makedirs(LANE, exist_ok=True); json.dump(log,',
     'os.makedirs(LANE, exist_ok=True)\n'
     '# GH-01: registry.json — the 49 members in registry order, the fields the order names, from the same roster read the pages use\n'
     'json.dump({"standard": "SM-ECO-10060", "apex": "https://sm-eco-10060.org/", "operator": OPERATOR, "licence": "MIT", "members": 49, "roster_read_at": READ_AT, "roster_source": "https://mcp.getissuer.ai/mcp list_nodes",\n'
     '           "registry": [{"code": r["code"], "namespace": r["namespace"], "jurisdiction": r["jurisdiction"], "member": r["member"], "canonical_node": r["canonical"], "allooloo_node": r["allooloo_node"], "record_door": r["record_door"], "agent_card": r.get("agent_card"), "duty": r.get("duty")} for r in MEMBER_RECORDS]},\n'
     '          open(os.path.join(LANE, "registry.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)\n'
     'json.dump(log,'),
])
patch(r"C:\GREENCORE\AUDITS\GREAT-CULL-02-2026-10-10\pages_app.py", [
    ('L = r"C:\\GREENCORE\\AUDITS\\GREAT-CULL-02-2026-10-10"; TOK = io.open(r"C:\\GREENCORE\\AGENT KEYS\\cloudflare-pages.txt", encoding="utf-8").read().strip();',
     'L = os.environ.get("CULL_ROOT") or r"C:\\GREENCORE\\AUDITS\\GREAT-CULL-02-2026-10-10"; TOK = os.environ.get("CLOUDFLARE_PAGES_TOKEN") or io.open(r"C:\\GREENCORE\\AGENT KEYS\\cloudflare-pages.txt", encoding="utf-8").read().strip();   # ECO-OPS-01: env in the nightly image'),
])
patch(r"C:\GREENCORE\AUDITS\SITE-03A-2026-10-28\grep_banned.py", [
    ('SNAP = r"C:\\GREENCORE\\AUDITS\\GREAT-CULL-02-2026-10-10\\snapshots"', 'SNAP = os.environ.get("SITE03A_SNAP") or r"C:\\GREENCORE\\AUDITS\\GREAT-CULL-02-2026-10-10\\snapshots"; LANE = os.environ.get("SITE03A_LANE") or r"C:\\GREENCORE\\AUDITS\\SITE-03A-2026-10-28"'),
    ('REG = json.load(open(r"C:\\GREENCORE\\PROTOCOLS\\_canon\\registry\\estate.json", encoding="utf-8"))', 'REG = json.load(open(os.environ.get("SITE03A_REGISTRY") or r"C:\\GREENCORE\\PROTOCOLS\\_canon\\registry\\estate.json", encoding="utf-8"))'),
    ('open(r"C:\\GREENCORE\\AUDITS\\SITE-03A-2026-10-28\\grep-banned.json", "w", encoding="utf-8")', 'open(os.path.join(LANE, "grep-banned.json"), "w", encoding="utf-8")'),
])
patch(r"C:\GREENCORE\AUDITS\SITE-03A-2026-10-28\verify_site03a.py", [
    ('import json, re, urllib.request, concurrent.futures as cf, collections', 'import json, re, os, urllib.request, concurrent.futures as cf, collections\nLANE = os.environ.get("SITE03A_LANE") or r"C:\\GREENCORE\\AUDITS\\SITE-03A-2026-10-28"'),
    ('REG = json.load(open(r"C:\\GREENCORE\\PROTOCOLS\\_canon\\registry\\estate.json", encoding="utf-8"))', 'REG = json.load(open(os.environ.get("SITE03A_REGISTRY") or r"C:\\GREENCORE\\PROTOCOLS\\_canon\\registry\\estate.json", encoding="utf-8"))'),
    ('G = json.load(open(r"C:\\GREENCORE\\AUDITS\\SITE-03A-2026-10-28\\grep-banned.json", encoding="utf-8"))', 'G = json.load(open(os.path.join(LANE, "grep-banned.json"), encoding="utf-8"))'),
    ('json.dump(R, open(r"C:\\GREENCORE\\AUDITS\\SITE-03A-2026-10-28\\verify-live.json", "w", encoding="utf-8"), indent=1)', 'json.dump(R, open(os.path.join(LANE, "verify-live.json"), "w", encoding="utf-8"), indent=1)'),
])
