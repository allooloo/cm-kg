r"""shared_text_do5.py — ISSUER-PAGES-01 (DAY ORDER 5): shared text between every two issuer pages, read live. Text = the page's visible text (tags stripped,
the contact block and footer included — what a reader sees). Shared = 5-word shingles of page A also in page B, over A's shingles; the pair figure is the
larger of the two directions. Usage: python -X utf8 -I shared_text_do5.py  -> shared-text-do5.json"""
import re, json, os, html, itertools, urllib.request
HOSTS = [f'{c}-issuer.ai' for c in 'lu ky bm je in tw ae br mx'.split()] + [f'{c}.eu-issuer.ai' for c in 'it es se dk no fi be ie at pl pt gr cz'.split()] + ['eu-issuer.ai']
def words(h):
    t = urllib.request.urlopen(urllib.request.Request(f'https://{h}/', headers={'User-Agent': 'Mozilla/5.0 (Allooloo shared-text check)'}), timeout=30).read().decode('utf-8', 'replace')
    t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', t); t = html.unescape(re.sub(r'(?s)<[^>]+>', ' ', t))
    t = t.replace(h, ' ')   # the page's own hostname is not shared text
    return re.findall(r"[\w’'.-]+", t.lower())
sh = {}
for h in HOSTS:
    w = words(h); sh[h] = {' '.join(w[i:i + 5]) for i in range(len(w) - 4)}
pairs = []
for a, b in itertools.combinations(HOSTS, 2):
    x = len(sh[a] & sh[b]); pairs.append((round(max(x / max(1, len(sh[a])), x / max(1, len(sh[b]))), 3), a, b))
pairs.sort(reverse=True)
json.dump({'pages': len(HOSTS), 'pairs': len(pairs), 'max': pairs[0], 'top10': pairs[:10], 'over_40': [p for p in pairs if p[0] >= 0.4]}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared-text-do5.json'), 'w'), indent=1)
print('pages', len(HOSTS), 'pairs', len(pairs), 'max', pairs[0], 'over 40%:', sum(1 for p in pairs if p[0] >= 0.4)); [print(' ', p) for p in pairs[:8]]
