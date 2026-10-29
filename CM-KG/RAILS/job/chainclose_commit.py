r"""CHAIN-CLOSE B1 (CEO order 2026-10-29): commit the uncommitted work in allooloo/cm-kg, cm-kg-ops, issuerwire and issuerwire-door. Commits and pushes only —
no tag, no release, no workflow dispatch. Every file staged in every repo is key-shape scanned (public_scan.py's patterns) before its commit; a hit stops that repo.
  cm-kg (public, code only — CEO 2026-10-18): tracked changes outside the ops rule + NEW files whose kind is code (py js mjs ts css html toml ps1 sh cff, Dockerfile, LICENSE).
  cm-kg-ops (private, C:\ALLOOLOO\.git-ops on the same tree): tracked ops changes + NEW files by the ops rule, and the new non-code files the public repo does not take.
  Left out of both: AGENT KEYS, .azure, .gh, node_modules, .wrangler, CM-KG/POND (local pond mirrors), */cache/* and */raw/* (downloaded source caches), GH/work/ (nested
  working copies), *.zip, *.pem, files over 25 MB, and CM-KG/RAILS/job/holidays* (item 3's own work, committed with item 3).
  issuerwire / issuerwire-door (C:\A2AAMN\GITHUB\agentmarketnews · a2a-amn): the live tree C:\A2AAMN is copied over each tracked file that differs, plus the new code files
  in the tracked folders; .pre-* anchors stay untracked (as ISSUERWIRE-03 left them).
Usage: python -I -X utf8 chainclose_commit.py plan|commit   (plan prints the sets and the scan; commit also commits and pushes)"""
import os, re, sys, subprocess, shutil, json
MODE = sys.argv[1]; ROOT = r'C:\ALLOOLOO'; AMN = r'C:\A2AAMN'
src = open(os.path.join(ROOT, r'CM-KG\RAILS\job\ops_split.py'), encoding='utf-8').read(); ns = {}; exec(src.split('def ls():')[0], ns); is_ops = ns['is_ops']
ps = open(os.path.join(ROOT, r'CM-KG\RAILS\job\public_scan.py'), encoding='utf-8').read(); PAT = eval(ps[ps.index('PAT = ') + 6: ps.index('}\n', ps.index('PAT = ')) + 1])
CODE = ('.py', '.js', '.mjs', '.ts', '.css', '.html', '.toml', '.ps1', '.sh', '.cff')
MSG = 'CHAIN-CLOSE (2026-10-29): the uncommitted work since 2026-10-23, committed as it stands on the laptop tree\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'
def git(args, cwd, gd=None, check=True):
    pre = ['git', '-c', 'core.quotepath=false'] + ([f'--git-dir={gd}', f'--work-tree={cwd}'] if gd else [])
    r = subprocess.run(pre + args, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and r.returncode: raise SystemExit(f'git {args[:3]} failed in {cwd}: {(r.stderr or r.stdout)[-400:]}')
    return r.stdout
def out_of_scope(p):
    return (p.startswith(('AGENT KEYS/', '.azure/', '.gh/', 'CM-KG/POND/', 'GH/work/')) or re.search(r'(^|/)(node_modules|\.wrangler|cache|raw|__pycache__)/', p)
            or p.endswith(('.zip', '.pem', '.pyc')) or p.startswith('CM-KG/RAILS/job/holidays'))
def big(path): return os.path.getsize(path) > 25 * 1024 * 1024
def scan(paths, base):
    hits = []
    for p in paths:
        f = os.path.join(base, p)
        if not os.path.isfile(f): continue
        b = open(f, 'rb').read()
        if b[:4] == b'PK\x03\x04' or b'\x00' in b[:2000]: continue
        t = b.decode('utf-8', 'replace')
        for name, rx in PAT.items():
            for m in re.finditer(rx, t): hits.append(f'{p}:{t.count(chr(10), 0, m.start()) + 1} {name}')
    return hits
def lines(s): return [l for l in s.split('\n') if l]
report = {}
# ---- cm-kg + cm-kg-ops on C:\ALLOOLOO
st = lines(git(['status', '--porcelain', '-uall'], ROOT))
tracked = [l[3:].strip('"') for l in st if not l.startswith('??')]; new = [l[3:].strip('"') for l in st if l.startswith('??')]
pub = [p for p in tracked if not is_ops(p) and not out_of_scope(p)] + [p for p in new if not out_of_scope(p) and not is_ops(p) and not big(os.path.join(ROOT, p))
       and (p.endswith(CODE) or os.path.basename(p) in ('Dockerfile', 'LICENSE'))]
ops_st = lines(git(['status', '--porcelain', '--untracked-files=no'], ROOT, gd=os.path.join(ROOT, '.git-ops')))
ops_tracked = [l[3:].strip('"') for l in ops_st]
ops_new = [p for p in new if not out_of_scope(p) and p not in pub and not big(os.path.join(ROOT, p))]
ign = lines(git(['ls-files', '--others', '-i', '--exclude-standard'], ROOT))   # ops paper the public .gitignore hides (START_ME_UP, COMPANY RECORDS, .pre copies …)
PAPER = ('START_ME_UP/', 'COMPANY RECORDS/', 'CM-KG/SWEEPS/', 'CM-KG/SPEND/')
SENSITIVE = ('AZURE/certs/', 'AGENT KEYS/', 'CM-KG/DOOR/data/', 'CM-KG/DISCLOSURE/', 'CM-KG/ISSUERS/', 'CM-KG/RAILS/logs/')   # ignored on purpose: keys, certs, data mirrors
paper = lambda p: (p.startswith(PAPER) or p in ('CLAUDE.md', 'ROOT-CONFIG.json') or re.match(r'^ORDER-[^/]*\.md$', p) or re.search(r'\.pre[-.]', os.path.basename(p))) and not p.startswith(SENSITIVE)
ops_new += [p for p in ign if is_ops(p) and paper(p) and not out_of_scope(p) and not big(os.path.join(ROOT, p))
            and not git(['ls-files', '--', p], ROOT, gd=os.path.join(ROOT, '.git-ops')).strip()]
ops = sorted(set(ops_tracked + ops_new))
report['cm-kg'] = {'files': len(pub), 'scan': scan(pub, ROOT)}; report['cm-kg-ops'] = {'files': len(ops), 'scan': scan(ops, ROOT)}
left = [p for p in new if p not in pub and p not in ops]
report['left_out'] = {'count': len(left), 'by_top': {}}
for p in left: k = '/'.join(p.split('/')[:3]); report['left_out']['by_top'][k] = report['left_out']['by_top'].get(k, 0) + 1
# ---- issuerwire repos: sync live → copy
for name, rel in (('issuerwire', r'GITHUB\agentmarketnews'), ('issuerwire-door', r'GITHUB\a2a-amn')):
    R = os.path.join(AMN, rel); sync = []
    for f in lines(git(['ls-files'], R)):
        L = os.path.join(AMN, f)
        if os.path.isfile(L) and open(L, 'rb').read() != open(os.path.join(R, f), 'rb').read(): sync.append(f)
    for d in sorted({os.path.dirname(f) for f in lines(git(['ls-files'], R)) if '/' in f}):
        D = os.path.join(AMN, d)
        if os.path.isdir(D):
            for n in os.listdir(D):
                f = f'{d}/{n}'
                if os.path.isfile(os.path.join(D, n)) and not re.search(r'\.pre[-.]', n) and (n.endswith(CODE + ('.txt',)) or n == 'Dockerfile') and not os.path.exists(os.path.join(R, f)): sync.append(f)
    mod = [l[3:] for l in lines(git(['status', '--porcelain', '--untracked-files=no'], R))]
    report[name] = {'sync_from_live': sync, 'already_modified': mod, 'scan': scan(sync, AMN) + scan(mod, R)}
    if MODE == 'commit':
        for f in sync: os.makedirs(os.path.dirname(os.path.join(R, f)), exist_ok=True); shutil.copy2(os.path.join(AMN, f), os.path.join(R, f))
        if report[name]['scan']: raise SystemExit(f'STOP {name}: key-shaped hits {report[name]["scan"]}')
        git(['add', '--'] + sorted(set(sync + mod)), R)
        if git(['diff', '--cached', '--name-only'], R).strip():
            git(['commit', '-q', '-m', MSG], R); report[name]['commit'] = git(['rev-parse', 'HEAD'], R).strip(); git(['push', '-q', 'origin', git(['branch', '--show-current'], R).strip()], R)
if MODE == 'commit':
    if report['cm-kg']['scan'] or report['cm-kg-ops']['scan']: raise SystemExit(f'STOP cm-kg: key-shaped hits {report["cm-kg"]["scan"] + report["cm-kg-ops"]["scan"]}')
    for i in range(0, len(pub), 200): git(['add', '--'] + pub[i:i + 200], ROOT)
    git(['commit', '-q', '-m', MSG], ROOT); report['cm-kg']['commit'] = git(['rev-parse', 'HEAD'], ROOT).strip(); git(['push', '-q', 'origin', 'main'], ROOT)
    gd = os.path.join(ROOT, '.git-ops')
    for i in range(0, len(ops), 200): git(['add', '-f', '--'] + ops[i:i + 200], ROOT, gd=gd)
    git(['commit', '-q', '-m', MSG], ROOT, gd=gd); report['cm-kg-ops']['commit'] = git(['rev-parse', 'HEAD'], ROOT, gd=gd).strip(); git(['push', '-q', 'origin', 'main'], ROOT, gd=gd)
json.dump(report, open(os.path.join(ROOT, r'START_ME_UP\.chainclose-commit-2026-10-29.json'), 'w', encoding='utf-8'), indent=1)
for k in ('cm-kg', 'cm-kg-ops'): print(k, report[k]['files'], 'files · scan hits', len(report[k]['scan']), report[k]['scan'][:6], report[k].get('commit', ''))
for k in ('issuerwire', 'issuerwire-door'): print(k, 'sync', len(report[k]['sync_from_live']), report[k]['sync_from_live'], '· modified', report[k]['already_modified'], '· scan', report[k]['scan'], report[k].get('commit', ''))
print('left out (untracked, not work):', report['left_out']['count'], dict(sorted(report['left_out']['by_top'].items(), key=lambda x: -x[1])[:15]))
