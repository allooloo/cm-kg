"""land.py — the landing stage, one shape for every estate (Book § 3, ORDER-C02 stage 5):
take the estate's landing lock → merge into the estate's own store (the adapter knows the store) → rebuild index parts → byte-compare →
release the lock with a dated entry → landing event. Published totals on any surface are NEVER touched: a landing that would change one
writes a QUESTION line and stops that surface's update (the adapter reports which surfaces carry typed totals; the harness never writes them).
In a dry run the merge happens in a scratch copy under HARNESS\\dryrun\\ and no lock, no store, no surface and no ledger line is touched."""
import datetime, hashlib, json, os, time

TODAY = datetime.date.today().isoformat()


class Lock:
    """Atomic-mkdir lock (the agent-bev RECORD\\.land-lock shape). Stale after two hours. The adapter names the path."""
    def __init__(self, path, wait=30, stale=7200, dry=False, log=print):
        self.path, self.wait, self.stale, self.dry, self.log = path, wait, stale, dry, log

    def __enter__(self):
        if self.dry: self.log(f"[land] dry run: lock {self.path} not taken"); return self
        while True:
            try: os.mkdir(self.path); return self
            except FileExistsError:
                try:
                    if time.time() - os.stat(self.path).st_mtime > self.stale: os.rmdir(self.path); continue
                except FileNotFoundError: continue
                self.log("[land] waiting for the landing in progress"); time.sleep(self.wait)

    def __exit__(self, *a):
        if not self.dry and os.path.isdir(self.path): os.rmdir(self.path)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()


def byte_compare(a, b):
    return sha(a) == sha(b)


def lock_entry(node, counts, extra=""):
    """The dated lock-release line (the agent-bev LANDED line shape)."""
    return (f"- LANDED {node} {TODAY}: " + " · ".join(f"{v:,} {k}" if isinstance(v, int) else f"{k} {v}" for k, v in counts.items()) + (" · " + extra if extra else "")).strip()


def landing_data(node, before, after, index_parts, coverage, lock_path, week, **more):
    d = {"node": node, "records_before": before.get("records"), "records_after": after.get("records"), "verified_after": after.get("verified"), "listed_after": after.get("listed"),
         "fields_after": after.get("fields"), "index_parts": index_parts, "source_url_coverage": coverage, "lock_entry": lock_path, "week": week}
    d.update(more); return d
