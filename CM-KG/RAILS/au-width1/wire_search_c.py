"""Third shard of wire_search for the 2026-09-11 build: same fetch, issuers from the middle forward, skipping keys already in raw/wire_search.jsonl at start;
writes raw/wire_search_c.jsonl (merged into wire_search.jsonl by key before assembly)."""
import json, os
from wire_search import fetch, issuers
import common
done = set()
for fn in ('raw/wire_search.jsonl', 'raw/wire_search_b.jsonl'):
  for line in open(fn, encoding='utf-8'):
    try: done.add(json.loads(line)['key'])
    except Exception: pass
items = [r for r in issuers[len(issuers) // 2:] if common.key(r) not in done]
common.run_workers('wire_search_c', fetch, items, threads=int(os.environ.get('THREADS', '4')))
