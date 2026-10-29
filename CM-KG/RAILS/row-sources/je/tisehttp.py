"""Shared HTTP helper for the Jersey (TISE) readers: tisegroup.com public JSON (the same calls the site's own pages make).
Gentle (<= ~1.5 requests/second), retries with backoff. No key, no login (MyTISE login is not used)."""
import time, threading
import requests

BASE = 'https://tisegroup.com'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept': 'application/json, text/plain, */*', 'Accept-Language': 'en-GB,en;q=0.9'}
_lock = threading.Lock(); _last = [0.0]
_s = requests.Session(); _s.headers.update(UA)


def _pace():
    with _lock:
        wait = 0.7 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()


def call(path, body=None, tries=4):
    url = path if path.startswith('http') else BASE + path
    for i in range(tries):
        _pace()
        try:
            r = _s.post(url, json=body, timeout=120) if body is not None else _s.get(url, timeout=120)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (400, 404):
                return None
        except (requests.RequestException, ValueError):
            pass
        time.sleep(4 * (i + 1))
    raise RuntimeError(f'tisegroup.com did not answer: {url}')
