# halt_in.py — NODE-ROW (DAY ORDER 5): shim; the reader lives with its helpers in RAILS\row-sources\in\halt.py (loaded from there, in the job image too)
import os, sys, importlib.util
_d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'row-sources', 'in'); sys.path.insert(0, _d)
_s = importlib.util.spec_from_file_location('row_in_halt', os.path.join(_d, 'halt.py')); _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
fetch = _m.fetch
