"""Estate adapters — only where the estate's sources need one. The core stays one codebase. Folder names use the ledger estate names."""
import importlib.util, os


def load(estate):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), estate, "adapter.py")
    if not os.path.exists(p): raise FileNotFoundError(f"no adapter for {estate} ({p})")
    spec = importlib.util.spec_from_file_location(f"adapter_{estate.replace('-', '_')}", p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.Adapter
