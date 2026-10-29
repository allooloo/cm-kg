r"""shared_text_z2.py — ZONES-02: shared text between every two of the nine pages (the method of shared_text_do5.py: visible text, contact block and footer
included; 5-word shingles; the pair figure is the larger of the two directions). Reads live by default; --dir <folder> reads saved renders z2-<host>.html.
Usage: python -X utf8 -I shared_text_z2.py [--dir <folder>]  -> shared-text-z2.json"""
import re, sys, json, os, html, itertools, urllib.request
HOSTS = ['data-now.ai', 'data-vintage.ai', 'data-ark.ai', 'hunter-agent.ai', 'hedge-agent.ai', 'ark-agent.ai', 'data-record.ai', 'data-eco.ai', 'data-rco.ai']
D = sys.argv[sys.argv.index('--dir') + 1] if '--dir' in sys.argv else None
def words(h):
    t = open(os.path.join(D, f'z2-{h}.html'), encoding='utf-8').read() if D else urllib.request.urlopen(urllib.request.Request(f'https://{h}/', headers={'User-Agent': 'Mozilla/5.0 (Allooloo shared-text check)'}), timeout=30).read().decode('utf-8', 'replace')
    t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', t); t = html.unescape(re.sub(r'(?s)<[^>]+>', ' ', t))
    t = t.replace(h, ' ')
    return re.findall(r"[\w’'.-]+", t.lower())
sh = {}
for h in HOSTS:
    w = words(h); sh[h] = {' '.join(w[i:i + 5]) for i in range(len(w) - 4)}
pairs = []
for a, b in itertools.combinations(HOSTS, 2):
    x = len(sh[a] & sh[b]); pairs.append((round(max(x / max(1, len(sh[a])), x / max(1, len(sh[b]))), 3), a, b))
pairs.sort(reverse=True)
json.dump({'source': 'saved renders' if D else 'live', 'pages': len(HOSTS), 'pairs': len(pairs), 'max': pairs[0], 'all': pairs, 'over_40': [p for p in pairs if p[0] >= 0.4]}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared-text-z2.json'), 'w'), indent=1)
print('pages', len(HOSTS), 'pairs', len(pairs), 'max', pairs[0], 'over 40%:', sum(1 for p in pairs if p[0] >= 0.4)); [print(' ', p) for p in pairs[:8]]
