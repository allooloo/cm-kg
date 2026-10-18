r"""ORDER-031 (2026-10-17) — path shim for the in-country job image. The laptop rails run UNCHANGED inside a Linux container.

The rails name their root as C:\ALLOOLOO\... (raw-string Windows paths, backslash joins). This module loads at interpreter start (sitecustomize)
and translates every such path at the OS boundary to the image root (/job/ALLOOLOO/...), so no rail file is edited for the move:
  - builtins.open / io.open / io.open_code and the posix file functions (stat, listdir, scandir, mkdir, rename, symlink ...) translate their path arguments
  - os.path.abspath / realpath translate first, so a relative-looking Windows path never gets the container cwd glued in front of it
  - subprocess argv items are translated the same way, and shell=True with an argv LIST (a Windows az.cmd habit) becomes shell=False on Linux,
    where az is a real executable and a list with shell=True would run only "az"
  - a read of AGENT KEYS\<lab>.txt is served from the matching environment variable (the Key Vault secret the job's managed identity read),
    so no key is ever written to disk in the job; an unset key reads as "no such file", exactly as a missing key file does on the laptop
Nothing here changes behaviour on Windows: the module is only installed in the image."""
import os, sys, io, re, builtins, posix, posixpath, subprocess

WIN = os.environ.get('CMKG_ROOT_WIN', 'C:\\ALLOOLOO'); WIN_FWD = WIN.replace('\\', '/')
LIN = os.environ.get('CMKG_ROOT', '/job/ALLOOLOO')
KEYMAP = {'tavily.txt': 'TAVILY_API_KEY', 'grok.txt': 'XAI_API_KEY', 'perplexity.txt': 'PERPLEXITY_API_KEY', 'mistral.txt': 'MISTRAL_API_KEY',
          'gemini.txt': 'GEMINI_API_KEY', 'chatgpt.txt': 'OPENAI_API_KEY', 'claude.txt': 'ANTHROPIC_API_KEY', 'dart.txt': 'DART_API_KEY',
          'edinet.txt': 'EDINET_API_KEY', 'companieshouse.txt': 'COMPANIESHOUSE_API_KEY', 'cloudflare-d1.txt': 'CLOUDFLARE_API_TOKEN',
          'cloudflare.txt': 'CLOUDFLARE_ZONES_TOKEN', 'deutsche-boerse.txt': 'DEUTSCHE_BOERSE_API_KEY'}
_RX = re.compile(re.escape(WIN) + r'[^\s"\']*|' + re.escape(WIN_FWD) + r'[^\s"\']*')

def tr(p):
    """one path (str): the first occurrence of the Windows root onward becomes the Linux root with forward slashes"""
    if not isinstance(p, str): return p
    i = p.find(WIN); n = len(WIN)
    if i < 0:
        i = p.find(WIN_FWD); n = len(WIN_FWD)
        if i < 0: return p
    return LIN + p[i + n:].replace('\\', '/')

def tr_all(s):
    """a command string: every embedded Windows-root path"""
    return _RX.sub(lambda m: tr(m.group(0)), s) if isinstance(s, str) else s

def keyfile_env(p):
    if isinstance(p, str) and ('AGENT KEYS\\' in p or 'AGENT KEYS/' in p):
        fn = p.replace('\\', '/').rsplit('/', 1)[-1]
        return KEYMAP.get(fn, fn.rsplit('.', 1)[0].upper().replace('-', '_') + '_KEY')
    return None

_open = builtins.open
def _open_(file, mode='r', *a, **k):
    env = keyfile_env(file)
    if env:
        v = os.environ.get(env)
        if v is None: raise FileNotFoundError(2, 'no such key in the job vault', str(file))
        return io.BytesIO(v.encode('utf-8')) if 'b' in str(mode) else io.StringIO(v)
    return _open(tr(file), mode, *a, **k)
builtins.open = _open_; io.open = _open_
import _io
_open_code = _io.open_code
def _open_code_(path): return _open_code(tr(path))
_io.open_code = _open_code_; io.open_code = _open_code_

_devnull_stat = posix.stat('/dev/null')
def _wrap1(name):
    f = getattr(posix, name)
    def w(path, *a, **k):
        env = keyfile_env(path)
        if env:
            if os.environ.get(env) is None: raise FileNotFoundError(2, 'no such key in the job vault', str(path))
            if name in ('stat', 'lstat'): return _devnull_stat
        return f(tr(path), *a, **k)
    w.__name__ = name; setattr(posix, name, w); setattr(os, name, w)
def _wrap2(name):
    f = getattr(posix, name)
    def w(src, dst, *a, **k): return f(tr(src), tr(dst), *a, **k)
    w.__name__ = name; setattr(posix, name, w); setattr(os, name, w)
for _n in ('stat', 'lstat', 'open', 'listdir', 'mkdir', 'rmdir', 'remove', 'unlink', 'readlink', 'access', 'chdir', 'utime', 'chmod', 'truncate'):
    if hasattr(posix, _n): _wrap1(_n)
for _n in ('rename', 'replace', 'symlink', 'link'):
    if hasattr(posix, _n): _wrap2(_n)
_scandir = posix.scandir
def _scandir_(path='.', *a, **k): return _scandir(tr(path) if isinstance(path, str) else path, *a, **k)
posix.scandir = _scandir_; os.scandir = _scandir_
_makedirs = os.makedirs
def _makedirs_(name, mode=0o777, exist_ok=False): return _makedirs(tr(name), mode, exist_ok)
os.makedirs = _makedirs_
_abspath, _realpath = posixpath.abspath, posixpath.realpath
def _abspath_(p): return _abspath(tr(p))
def _realpath_(p, *a, **k): return _realpath(tr(p), *a, **k)
posixpath.abspath = _abspath_; posixpath.realpath = _realpath_; os.path.abspath = _abspath_; os.path.realpath = _realpath_
# pure string functions see the Windows path before any file call: dirname('C:\ALLOOLOO\...') is '' on Linux (dry run 2026-10-18, NL assembler
# makedirs(dirname(OUT_J)) -> ''); translate first so the result is a Linux path the file calls can use
for _n in ('dirname', 'basename', 'split', 'normpath', 'expanduser', 'isabs', 'splitdrive'):
    _f = getattr(posixpath, _n)
    def _mk(_f):
        def w(p, *a, **k): return _f(tr(p), *a, **k)
        return w
    setattr(posixpath, _n, _mk(_f)); setattr(os.path, _n, getattr(posixpath, _n))

_Popen_init = subprocess.Popen.__init__
def _popen_init(self, args, *a, **k):
    if isinstance(args, (list, tuple)):
        args = [tr(x) if isinstance(x, str) else x for x in args]
        if k.get('shell'): k['shell'] = False
    elif isinstance(args, str): args = tr_all(args)
    if k.get('cwd'): k['cwd'] = tr(k['cwd'])
    return _Popen_init(self, args, *a, **k)
subprocess.Popen.__init__ = _popen_init

# sys.path entries written as Windows paths (sys.path.insert(0, r'C:\ALLOOLOO\CM-KG\RAILS\<cc>-width0')) resolve through the patched posix functions above.
