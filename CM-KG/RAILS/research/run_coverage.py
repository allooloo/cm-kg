r"""run_coverage.py — USR-04: coverage.py over a list of markets, one after another (each market its own drop of the day). A failed market is logged and the
next one runs. Usage: python -X utf8 run_coverage.py <threads> <cc> [<cc> ...]"""
import sys, subprocess, os
th = sys.argv[1]; here = os.path.dirname(os.path.abspath(__file__))
for cc in sys.argv[2:]:
    r = subprocess.run([sys.executable, '-X', 'utf8', 'coverage.py', cc, '--drop', '2026-11-12', '--threads', th], cwd=here)
    print(cc, 'exit', r.returncode, flush=True)
