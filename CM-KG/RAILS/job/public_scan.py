r"""Key-shape scan of every PUBLIC file (ops_split rule set) in a commit's tree — full content, not a diff. Usage: python public_scan.py [rev]   (default HEAD)
Prints file:line and the pattern name only — never the matched text."""
import re, subprocess, sys, importlib.util
spec = importlib.util.spec_from_file_location('ops_split_rules', r'C:\ALLOOLOO\CM-KG\RAILS\job\ops_split.py')
src = open(r'C:\ALLOOLOO\CM-KG\RAILS\job\ops_split.py', encoding='utf-8').read(); src = src[:src.index("mode = sys.argv[1]")]
ns = {}; exec(src, ns); is_ops = ns['is_ops']
rev = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
PAT = {'anthropic': r'sk-ant-[A-Za-z0-9_-]{20,}', 'openai': r'\bsk-(proj-)?[A-Za-z0-9_-]{32,}', 'xai': r'\bxai-[A-Za-z0-9]{20,}', 'tavily': r'\btvly-[A-Za-z0-9_-]{10,}',
       'perplexity': r'\bpplx-[A-Za-z0-9]{20,}', 'aws key id': r'\b(AKIA|ASIA)[0-9A-Z]{16}\b', 'google': r'\bAIza[0-9A-Za-z_-]{30,}', 'github': r'\b(ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}',
       'private key': r'-----BEGIN (RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----', 'azure storage key': r'AccountKey=[A-Za-z0-9+/]{60,}={0,2}', 'stripe': r'\b(sk|rk)_(live|test)_[A-Za-z0-9]{20,}',
       'cloudflare-ish token': r'(?i)(api[_-]?token|bearer)["\'\s:=]+[A-Za-z0-9_-]{36,}', 'jwk private d': r'"d"\s*:\s*"[A-Za-z0-9_-]{40,}"', 'mistral/gemini-ish': r'(?i)(api[_-]?key)["\'\s:=]+[A-Za-z0-9_-]{30,}'}
files = subprocess.run(['git', 'ls-tree', '-r', '--name-only', '-z', rev], capture_output=True, check=True, cwd=r'C:\ALLOOLOO').stdout.decode('utf-8').split('\0')[:-1]
pub = [f for f in files if not is_ops(f)]; hits = []
for f in pub:
    b = subprocess.run(['git', 'show', f'{rev}:{f}'], capture_output=True, cwd=r'C:\ALLOOLOO').stdout
    if b[:4] in (b'PK\x03\x04',) or b'\x00' in b[:2000]: continue   # binary (xlsx, fonts, sqlite) — listed below for review
    t = b.decode('utf-8', 'replace')
    for name, rx in PAT.items():
        for m in re.finditer(rx, t):
            hits.append((f, t.count('\n', 0, m.start()) + 1, name))
for h in hits: print(f'{h[0]}:{h[1]}  {h[2]}')
print(f'scanned {len(pub)} public files at {rev}: {len(hits)} key-shaped hits')
print('binary public files (not scanned):', [f for f in pub if subprocess.run(["git", "show", f"{rev}:{f}"], capture_output=True, cwd=r"C:\ALLOOLOO").stdout[:2000].count(b"\x00") or f.endswith((".xlsx", ".woff2", ".png", ".ico"))][:20])
