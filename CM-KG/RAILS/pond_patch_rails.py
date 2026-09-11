r"""One-off patch (2026-09-11), idempotent: bring the Canada and UK refresh scripts and the fill-confirm loaders under the pond rule.
  run_refresh.ps1 (width0 / width1 / fill-confirm, both nodes): open a new drop at the start (python ..\pond_open.py <node> <rail> <source>) instead of
  deleting or moving worker outputs; skip on the node lock.
  fc_common.py (both fill-confirm rails): jload('raw/<file>') reads the file from every drop of the rail (newest wins per 'key' when rows carry one,
  union otherwise), so resume-safe workers skip keys done in any earlier drop and the readers see the whole history."""
import os, re
RAILS = r'C:\ALLOOLOO\CM-KG\RAILS'
def patch(fn, fnc):
    p = os.path.join(RAILS, fn); s = open(p, encoding='utf-8').read(); t = fnc(s)
    if t != s: open(p, 'w', encoding='utf-8').write(t); print('patched', fn)
    else: print('unchanged', fn)
def ps_open(node, rail, source, guard_var='$PSScriptRoot'):
    return (f"# pond rule: skip on the node lock; open a new dated drop (raw\\ becomes a junction to it); nothing is deleted or moved\n"
            f"if (Test-Path 'C:\\ALLOOLOO\\CM-KG\\POND\\{node}\\.lock') {{ '{node} locked (build order in flight): refresh skipped'; exit 0 }}\n"
            f"python ..\\pond_open.py {node} {rail} {source}\n")
# --- Canada width1: replace the Remove-Item line
patch(r'ca-width1\run_refresh.ps1', lambda s: s.replace("# fresh worker outputs for the daily window; the assembler merges into the existing events file\nRemove-Item -Path 'raw\\wire_pages.jsonl','raw\\wire_search.jsonl','raw\\release_dates.jsonl','raw\\tsxv_bulletins.jsonl','raw\\cse_bulletins.jsonl' -ErrorAction SilentlyContinue\n", ps_open('ca-cm-kg', 'ca-width1', 'width1')) if 'pond_open' not in s else s)
# --- Canada width0 / fill-confirm and UK width0 / width1 / fill-confirm: insert after Set-Location $PSScriptRoot
def insert_after_setloc(node, rail, source):
    def f(s):
        if 'pond_open' in s: return s
        return s.replace("Set-Location $PSScriptRoot\n", "Set-Location $PSScriptRoot\n" + ps_open(node, rail, source), 1)
    return f
patch(r'ca-width0\run_refresh.ps1', insert_after_setloc('ca-cm-kg', 'ca-width0', 'width0'))
patch(r'ca-fill-confirm\run_refresh.ps1', insert_after_setloc('ca-cm-kg', 'ca-fill-confirm', 'fill-confirm'))
patch(r'uk-width0\run_refresh.ps1', insert_after_setloc('uk-cm-kg', 'uk-width0', 'width0'))
patch(r'uk-fill-confirm\run_refresh.ps1', insert_after_setloc('uk-cm-kg', 'uk-fill-confirm', 'fill-confirm'))
def uk_w1(s):
    if 'pond_open' in s: return s
    a = s.find('# prior worker outputs move aside'); b = s.find('Move-Item -Destination $prior -Force\n')
    if a > 0 and b > 0: s = s[:a] + ps_open('uk-cm-kg', 'uk-width1', 'width1') + s[b + len('Move-Item -Destination $prior -Force\n'):]
    return s
patch(r'uk-width1\run_refresh.ps1', uk_w1)
# --- fc_common jload pond-aware
JLOAD_OLD = """def jload(fn):
    out = []
    if os.path.exists(fn):
        for line in open(fn, encoding='utf-8'):
            try: out.append(json.loads(line))
            except Exception: pass
    return out"""
def jload_new(node):
    return f"""import pond
NODE = '{node}'
def jload(fn):
    \"\"\"pond rule 3: a raw/<file> is read from every drop of this rail (newest wins per 'key' when rows carry one, union otherwise) plus the working folder\"\"\"
    out = []; seen = set()
    paths = ([p for d, p in pond.drops(NODE, 'fill-confirm')] + (['raw'] if os.path.isdir('raw') else [])) if fn.startswith('raw/') and fn.count('/') == 1 else [None]
    for p in paths:
        f = fn if p is None else os.path.join(p, os.path.basename(fn)); rp = os.path.realpath(f)
        if not os.path.exists(f) or rp in seen: continue
        seen.add(rp)
        for line in open(f, encoding='utf-8'):
            try: out.append(json.loads(line))
            except Exception: pass
    if out and all(isinstance(d, dict) and 'key' in d for d in out[:50]):
        byk = {{}}
        for d in out: byk[d.get('key')] = d   # newest drop last -> wins
        return list(byk.values())
    return out"""
for rail, node in (('ca-fill-confirm', 'ca-cm-kg'), ('uk-fill-confirm', 'uk-cm-kg')):
    patch(rail + r'\fc_common.py', lambda s, node=node: s.replace(JLOAD_OLD, jload_new(node), 1) if JLOAD_OLD in s and 'pond.drops' not in s else s)
print('done')
