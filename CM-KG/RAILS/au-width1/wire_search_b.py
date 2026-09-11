"""Second shard of wire_search for the 2026-09-11 build: same fetch, issuers in reverse order, skipping keys already in raw/wire_search.jsonl at start;
writes raw/wire_search_b.jsonl (merged into wire_search.jsonl by key before assembly)."""
import json, os
from wire_search import fetch, issuers
import common
done = set()
for line in open('raw/wire_search.jsonl', encoding='utf-8'):
    try: done.add(json.loads(line)['key'])
    except Exception: pass
items = [r for r in reversed(issuers) if common.key(r) not in done]
common.run_workers('wire_search_b', fetch, items, threads=int(os.environ.get('THREADS', '4')))
