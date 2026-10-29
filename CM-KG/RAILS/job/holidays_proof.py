r"""holidays_proof.py — CHAIN-CLOSE B3 proof: runs job_node.py's own market clock (the lines from STD_OFFSET through last_trading, exactly as the job
executes them) for the night after a known exchange closure in each of the three largest markets by records, and the weekend-only rule of the
anchor job_node.py.pre-chainclose-2026-10-29 beside it, plus one plain weekday as a control. Prints one line per case; writes holidays-proof-2026-10-29.json.
MDATE = last_trading(NIGHT - 1 day), as job_node.py line 'MDATE = …' computes it."""
import os, sys, json, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
def clock(path, cc):
    src = open(path, encoding='utf-8').read(); i = src.index('STD_OFFSET = {'); j = src.index('NIGHT = os.environ.get')
    ns = {'datetime': datetime, 'CC': cc, 'os': os, 'sys': sys}; exec(src[i:j], ns); return ns['last_trading']
import holidays
CASES = [  # (market, night, the closure, the exchange's own line)
    ('us', '2026-11-27', '2026-11-26', 'NYSE · Thanksgiving Day · Thursday, November 26'),
    ('ca', '2026-10-13', '2026-10-12', 'TSX · Thanksgiving Day - Monday, October 12, 2026'),
    ('in', '2026-11-11', '2026-11-10', 'NSE · 10-Nov-2026 Tuesday Diwali-Balipratipada'),
    ('ca', '2026-12-29', '2026-12-28', 'TSX · In Lieu of Boxing Day - Monday, December 28, 2026 (and Christmas Day, Friday December 25)'),
    ('us', '2026-11-25', None, 'control — a plain Tuesday, no closure'),
]
out = []
for cc, night, closure, line in CASES:
    new = clock(os.path.join(HERE, 'job_node.py'), cc); old = clock(os.path.join(HERE, 'job_node.py.pre-chainclose-2026-10-29'), cc)
    d = datetime.date.fromisoformat(night) - datetime.timedelta(days=1)
    m_new, m_old = new(d).isoformat(), old(d).isoformat()
    ok = (m_new != m_old and not holidays.closed(cc, datetime.date.fromisoformat(m_new)) and datetime.date.fromisoformat(m_new).weekday() < 5) if closure else (m_new == m_old)
    row = {'market': cc, 'night': night, 'market_date_rule': m_new, 'market_date_before': m_old, 'closure': closure, 'source': holidays.HOLIDAYS[cc]['source_url'], 'line': line, 'verdict': 'PASS' if ok else 'FAIL'}
    out.append(row)
    print(f"market-date · {cc}-cm-kg · night {night} · rule {m_new} (weekends-only rule: {m_old}) · {line} · {row['verdict']}")
json.dump(out, open(os.path.join(HERE, 'holidays-proof-2026-10-29.json'), 'w', encoding='utf-8'), indent=1)
print('table:', len(holidays.HOLIDAYS), 'markets ·', sum(len(r['dates']) for r in holidays.HOLIDAYS.values()), 'dates · blank:', [c for c, r in holidays.HOLIDAYS.items() if not r['dates']])
