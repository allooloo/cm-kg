r"""Ops / code split of the C:\ALLOOLOO tree (CEO 2026-10-18: cm-kg stays public and carries code only; ops content lives in the private allooloo/cm-kg-ops).
One rule set, used three ways:
  python ops_split.py classify            print the verdict on every path tracked at HEAD (counts + the ops list)
  python ops_split.py index-drop-ops      (git filter-branch --index-filter) remove ops paths from the index of the commit being rewritten -> public history
  python ops_split.py index-keep-ops      (git filter-branch --index-filter) keep only ops paths in the index -> the private ops history
  python ops_split.py gitignore           print the .gitignore block that keeps ops paths out of the public tree from now on
Ops = START_ME_UP/ · .pre copies and anchor folders · AZURE/ except code · AWS/ · CM-KG/SWEEPS/ · CM-KG/SPEND/ · CM-KG/POND/ lock records · zones-027/zones-032 state ·
      every *.log · RAILS audits · COMPANY RECORDS/ · CLAUDE.md · ROOT-CONFIG.json · ORDER-*.md at the root. Everything else (code, published assets) is public."""
import re, subprocess, sys
CODE_EXT = ('.py', '.ps1', '.sh')
def is_ops(p):
    n = p.split('/')[-1]
    if p.startswith(('START_ME_UP/', 'AWS/', 'COMPANY RECORDS/', 'CM-KG/SWEEPS/', 'CM-KG/SPEND/', 'CM-KG/POND/')): return True
    if p in ('CLAUDE.md', 'ROOT-CONFIG.json') or re.match(r'^ORDER-[^/]*\.md$', p): return True
    if re.search(r'\.pre[-.]', n) or re.search(r'(^|/)(_anchors-[^/]+|_pre-refurb[^/]*|apic-pre-[^/]+)/', p): return True
    if p.startswith('AZURE/') and not n.endswith(CODE_EXT): return True
    if n.endswith('.log'): return True
    if re.search(r'(^|/)(\.wrangler|\.claude)/', p): return True   # local tool state (wrangler caches incl. the account id, miniflare databases, launch configs)
    if re.match(r'^CM-KG/RAILS/(estate-audit-|estate-surface-)', p): return True
    if re.match(r'^CM-KG/RAILS/zones-0(27|32)/', p) and not n.endswith(('.py', '.js')): return True
    return False
def ls(): return subprocess.run(['git', 'ls-files', '-z'], capture_output=True, check=True).stdout.decode('utf-8', 'surrogateescape').split('\0')[:-1]
def rm(paths):
    for i in range(0, len(paths), 200):
        subprocess.run(['git', 'rm', '-q', '--cached', '--ignore-unmatch', '--'] + paths[i:i + 200], check=True)
mode = sys.argv[1]
if mode == 'classify':
    files = subprocess.run(['git', 'ls-tree', '-r', '--name-only', '-z', 'HEAD'], capture_output=True, check=True).stdout.decode('utf-8').split('\0')[:-1]
    ops = [f for f in files if is_ops(f)]; code = [f for f in files if not is_ops(f)]
    print('tracked', len(files), '· ops', len(ops), '· public', len(code))
    from collections import Counter
    print('ops by top folder:', dict(Counter(f.split('/')[0] for f in ops)))
    print('public by top folder:', dict(Counter(f.split('/')[0] for f in code)))
    if len(sys.argv) > 2: print('\n'.join(ops if sys.argv[2] == 'ops' else code))
elif mode == 'index-drop-ops': rm([f for f in ls() if is_ops(f)])
elif mode == 'index-keep-ops': rm([f for f in ls() if not is_ops(f)])
elif mode == 'gitignore':
    print('\n'.join(['', '# ops content lives in the private allooloo/cm-kg-ops (CEO 2026-10-18); cm-kg is code only', '/START_ME_UP/', '/AWS/', '/COMPANY RECORDS/', '/CM-KG/SWEEPS/',
                     '/CM-KG/SPEND/', '/CM-KG/POND/', '/CLAUDE.md', '/ROOT-CONFIG.json', '/ORDER-*.md', '*.pre-*', '*.pre.*', '_anchors-*/', '_pre-refurb*/', '/AZURE/*', '!/AZURE/*.py', '!/AZURE/*.ps1', '!/AZURE/*.sh',
                     '/AZURE/apic-pre-*/', '*.log', '/CM-KG/RAILS/estate-audit-*', '/CM-KG/RAILS/estate-surface-*', '/CM-KG/RAILS/zones-027/*', '!/CM-KG/RAILS/zones-027/*.py',
                     '/CM-KG/RAILS/zones-032/*', '!/CM-KG/RAILS/zones-032/*.py', '!/CM-KG/RAILS/zones-032/*.js', '.wrangler/', '.claude/', '/.git-ops/', '']))
