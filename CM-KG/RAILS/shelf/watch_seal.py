r"""SHELF-01 — wait for a market's ledger entry to turn complete, then light its shelf at once (auto.py <cc>: Replay split, Score, Bench, Review),
then run its proofs. Checks the ledger every 10 minutes (one blob read); gives up at the deadline (UTC hour, default 23:30) and says so.
Usage: python -X utf8 watch_seal.py <cc> [deadline HH:MM]"""
import os, sys, time, json, datetime, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [os.path.join(HERE, '..', 'backfill')]
os.environ.setdefault('AZURE_CONFIG_DIR', r'C:\ALLOOLOO\.azure')
import backfill as BF
cc = sys.argv[1]; dl = sys.argv[2] if len(sys.argv) > 2 else '23:30'
deadline = datetime.datetime.now(datetime.timezone.utc).replace(hour=int(dl[:2]), minute=int(dl[3:]), second=0)
while True:
    e = BF.order_get(cc) or {}
    now = datetime.datetime.now(datetime.timezone.utc)
    print(now.strftime('%H:%M'), cc, 'complete' if e.get('complete') else f"left {e.get('left')}", flush=True)
    if e.get('complete'): break
    if now >= deadline: print('deadline reached; not complete'); sys.exit(2)
    time.sleep(600)
p = subprocess.run([sys.executable, '-X', 'utf8', 'auto.py', cc], cwd=HERE, capture_output=True, text=True, encoding='utf-8', errors='replace'); print(p.stdout[-3000:], p.stderr[-2000:], flush=True)
print('lit at', datetime.datetime.now(datetime.timezone.utc).isoformat(), flush=True)
