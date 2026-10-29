"""Shared helper: probe an official Saudi host and report whether this network is let in.
Saudi Exchange (www.saudiexchange.sa) and Edaa (www.edaa.sa) sit behind Akamai. From the network these readers were built on
(2026-10-24) every path on both hosts, robots.txt included, answered 403 "Access Denied" (Akamai reference id in the body), in Python
and in a real browser alike: a host-level / network-level deny, not a challenge page. The readers do not try to get around it."""
import re, html, datetime
import requests

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.9'}
SAUDI_EXCHANGE = 'https://www.saudiexchange.sa/wps/portal/saudiexchange/home'
EDAA = 'https://www.edaa.sa/'


def probe(url):
    """-> {'url','status','blocked','reason','reference','server','checked_at'}"""
    out = {'url': url, 'checked_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
    try:
        r = requests.get(url, headers=UA, timeout=60)
    except requests.RequestException as e:
        out.update(status=None, blocked=True, reason=f'no connection: {type(e).__name__}')
        return out
    body = r.text[:2000]
    ref = re.search(r'Reference\s*&#32;&#35;([^<\s]+)|Reference #([^<\s]+)', body)
    denied = r.status_code == 403 and 'Access Denied' in body
    out.update(status=r.status_code, server=r.headers.get('server'), blocked=denied or r.status_code >= 400,
               reason='Akamai "Access Denied" (403) for this network' if denied else ('' if r.status_code < 400 else f'HTTP {r.status_code}'),
               reference=html.unescape((ref.group(1) or ref.group(2))) if ref else None)
    return out
