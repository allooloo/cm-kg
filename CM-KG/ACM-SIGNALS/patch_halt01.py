r"""patch_halt01.py — NODE-HALT-01 (DAY ORDER 4, 2026-10-24): ACM-403 is a state the resolver answers, not an advisory.
The twelve nodes carry a halt flag read from each market's halts page; get_signal answers ACM-403 from it. index.js.pre-halt01-20261024 beside."""
import io
p = r"C:\ALLOOLOO\CM-KG\ACM-SIGNALS\worker\index.js"; t = io.open(p, encoding="utf-8", newline="").read()
R = [("kind: 'advisory', when: 'Trading in the line is halted or suspended by the exchange or regulator. Advisory: the nodes carry no halt flag yet, so the resolver never answers ACM-403 today — read the market\\'s halts page.' },",
      "kind: 'state', when: 'Trading in the line is halted or suspended by the exchange or regulator: the home node\\'s record carries a halt flag read nightly from the market\\'s halts page, and the resolver answers ACM-403 with the halt (since, reason, the page it was read from).', candidates: ['8366.T'] },"),
     ("    else if (code === '403') { const a = await signal(S['200'].candidates[0]); v = { identifier: S['200'].candidates[0], answer: a, advisory: true }; }",
      "    else if (code === '403') { for (const id of s.candidates) { const a = await signal(id); if (a.signal === 'ACM-403') { v = { identifier: id, answer: a }; break; } } if (!v) v = { identifier: s.candidates[0], answer: await signal(s.candidates[0]), note: 'no halt among the page\\'s candidates answered ACM-403 at render (the halt has lifted); every node reads its halts page every night' }; }"),
     ("ACM-500 SYSTEM ERROR; ACM-403 HALTED advisory.`", "ACM-500 SYSTEM ERROR · ACM-403 HALTED (from the home node\\'s halt flag).`")]
for o, n in R:
    assert t.count(o) == 1, o[:60]; t = t.replace(o, n)
io.open(p, "w", encoding="utf-8", newline="").write(t); print("acm-403 state")
