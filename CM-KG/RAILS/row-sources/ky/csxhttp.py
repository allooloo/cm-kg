"""Shared HTTP helper for the Cayman (CSX) readers.

www.csx.ky serves its leaf certificate without the intermediate (Starfield TLS Intermediate CA DV - R1v1), so Python
requests (certifi) fails with CERTIFICATE_VERIFY_FAILED while browsers / Windows schannel fill the gap via AIA.
This helper keeps full verification: on the first SSL failure it reads the leaf's Authority Information Access
"CA Issuers" URL, downloads the missing intermediate(s) from the CA (certificates.starfieldtech.com), and verifies
against certifi + those intermediates (bundle cached in cache/csx-chain.pem). Never verify=False.
Gentle: at most ~1.5 requests per second across all callers in the process.
"""
import os, ssl, time, threading
import requests, certifi

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'cache')
HOST = 'www.csx.ky'
BASE = 'https://www.csx.ky'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36'}
_lock = threading.Lock(); _last = [0.0]; _verify = [None]; _built = [None]


def _pace():
    with _lock:
        wait = 0.7 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()


def _build_bundle():
    from cryptography import x509
    from cryptography.x509.oid import ExtensionOID, AuthorityInformationAccessOID
    from cryptography.hazmat.primitives.serialization import Encoding
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, 'csx-chain.pem')
    pem = ssl.get_server_certificate((HOST, 443))        # leaf only; read without verification just to find its issuer URL
    cert = x509.load_pem_x509_certificate(pem.encode())
    extra = []
    for _ in range(3):
        try:
            aia = cert.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS).value
        except x509.ExtensionNotFound:
            break
        urls = [d.access_location.value for d in aia if d.access_method == AuthorityInformationAccessOID.CA_ISSUERS]
        if not urls:
            break
        der = requests.get(urls[0], headers=UA, timeout=60).content
        try:
            cert = x509.load_der_x509_certificate(der)
        except ValueError:
            cert = x509.load_pem_x509_certificate(der)
        extra.append(cert.public_bytes(Encoding.PEM).decode())
        if cert.issuer == cert.subject:
            break
    with open(path, 'w', encoding='ascii') as f:
        f.write(open(certifi.where(), encoding='ascii', errors='ignore').read() + '\n' + '\n'.join(extra))
    return path


def get(url, tries=4, **kw):
    url = url if url.startswith('http') else BASE + url
    for i in range(tries):
        _pace()
        try:
            r = requests.get(url, headers=UA, timeout=90, verify=_verify[0] or certifi.where(), **kw)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(4 * (i + 1)); continue
            return r
        except requests.exceptions.SSLError:
            cached = os.path.join(CACHE, 'csx-chain.pem')
            with _lock:
                if _built[0] is None:
                    if _verify[0] is None and os.path.exists(cached):
                        _verify[0] = cached                   # try the cached chain first
                    else:
                        _built[0] = _verify[0] = _build_bundle()
                else:
                    time.sleep(3 * (i + 1))
            continue
        except requests.RequestException:
            time.sleep(3 * (i + 1))
    raise RuntimeError(f'csx.ky did not answer: {url}')


def text(url, **kw):
    """Pages mix UTF-8 (pasted announcement bodies) and Windows-1252 (the ASP templates): UTF-8 if it decodes, else cp1252."""
    b = get(url, **kw).content
    try:
        return b.decode('utf-8')
    except UnicodeDecodeError:
        return b.decode('windows-1252', errors='replace')
