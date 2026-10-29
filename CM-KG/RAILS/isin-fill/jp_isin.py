r"""jp_isin.py — DOORS-04 (2026-10-26): the ISIN of a TSE issue read at the exchange of record, JPX Listed Company Search (www2.jpx.co.jp/tseHpFront),
"Listed company details (basic information)": Code · ISIN Code · Market Segment … One session, one detail read per code (POST JJK020030Action.do, BaseJh).
fetch(codes) -> {code: {'isin', 'name', 'segment', 'source_url', 'read_by', 'read_at'} or {'error'}}. Usage: python jp_isin.py 7203 3333 445A"""
import re, sys, json, datetime, html, urllib.request, urllib.parse, http.cookiejar
BASE = 'https://www2.jpx.co.jp/tseHpFront/'
READ_BY = 'JPX Listed Company Search — Listed company details (basic information), ISIN Code (www2.jpx.co.jp/tseHpFront)'
def _op():
    cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [('User-Agent', 'Mozilla/5.0 (Allooloo ISIN re-read; developers@allooloo.ai)'), ('Accept-Language', 'en')]
    op.open(BASE + 'JJK020010Action.do?Show=Show', timeout=40).read(); return op
def _text(b): t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', b); return re.sub(r'\s+', ' ', html.unescape(re.sub(r'(?s)<[^>]+>', ' ', t)))
def fetch(codes):
    op = _op(); out = {}
    for c in codes:
        mc = str(c).upper() + '0' if len(str(c)) == 4 else str(c).upper()
        try:
            data = urllib.parse.urlencode({'BaseJh': 'BaseJh', 'mgrCd': mc, 'jjHisiFlg': '1', 'sniMtGmnId': 'JJK020010'}).encode()
            t = _text(op.open(urllib.request.Request(BASE + 'JJK020030Action.do', data=data), timeout=40).read().decode('utf-8', 'replace'))
            m = re.search(r'Code ISIN Code Market Segment .*? ' + re.escape(mc) + r' (JP[0-9A-Z]{9}\d) (\S+)', t)
            nm = re.search(r'Notes on the use of this data (.+?) Basic information', t)
            out[str(c)] = {'isin': m.group(1), 'segment': m.group(2), 'name': nm.group(1).strip() if nm else None, 'source_url': BASE + f'JJK020030Action.do (Listed company details, code {mc})',
                           'read_by': READ_BY, 'read_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} if m else {'error': 'no ISIN on the detail page', 'head': t[:200]}
        except Exception as e: out[str(c)] = {'error': repr(e)[:160]}
    return out
if __name__ == '__main__': print(json.dumps(fetch(sys.argv[1:]), ensure_ascii=False, indent=1))
