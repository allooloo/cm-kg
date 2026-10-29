"""Shared HTTP helper for the Bermuda (BSX) readers: gentle (<= ~1.5 requests/second), retries with backoff."""
import time, threading
import requests

BASE = 'https://www.bsx.com'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.9'}
_lock = threading.Lock(); _last = [0.0]
_s = requests.Session(); _s.headers.update(UA)


def text(url, params=None, tries=4):
    url = url if url.startswith('http') else BASE + url
    for i in range(tries):
        with _lock:
            wait = 0.7 - (time.time() - _last[0])
            if wait > 0:
                time.sleep(wait)
            _last[0] = time.time()
        try:
            r = _s.get(url, params=params, timeout=90)
            if r.status_code == 200:
                r.encoding = 'utf-8'
                return r.text
            if r.status_code == 404:
                return ''
        except requests.RequestException:
            pass
        time.sleep(4 * (i + 1))
    raise RuntimeError(f'bsx.com did not answer: {url}')
