r"""patch_cov_twopass.py — RESLATE-01: the coverage read in two passes, YIELD FIRST across the two readers. Idempotent."""
import pathlib, ast
p = pathlib.Path(r'C:\ALLOOLOO\CM-KG\RAILS\research\coverage.py'); s = p.read_text(encoding='utf-8')
if 'second=False' in s: raise SystemExit('already patched')
def rep(o, n):
    global s
    assert s.count(o) == 1, (s.count(o), o[:70]); s = s.replace(o, n)
rep("def read_one(o, cc):\n", "def read_one(o, cc, second=False):\n    \"\"\"pass one (second=False): the Perplexity read. pass two (second=True): the Grok second read of an issuer whose first answer was thin.\"\"\"\n")
rep("    j = post('https://api.perplexity.ai/chat/completions',", "    j = {'choices': [{'message': {'content': '{}'}}]} if second else post('https://api.perplexity.ai/chat/completions',")
rep("    with LOCK: SP['calls'] += 1; SP['prompt_tokens'] += u.get('prompt_tokens', 0);", "    with LOCK: SP['calls'] += 0 if second else 1; SP['prompt_tokens'] += u.get('prompt_tokens', 0);")
rep("    if thin and GROK and (METER is None or SP['cost'] < METER):", "    res['thin'] = bool(thin)\n    if thin and second and GROK:")
rep("        return read_one(o, cc)\n", "        return read_one(o, cc)\n    thin = []\n")
rep("            out.write(json.dumps(res, ensure_ascii=False) + '\\n'); out.flush(); n[0] += 1\n", "            out.write(json.dumps(res, ensure_ascii=False) + '\\n'); out.flush(); n[0] += 1\n            if res.get('thin'): thin.append(res['cmr'])\n")
rep("    sp = os.path.join(d, 'spend.json'); prev",
    "    # pass two, YIELD FIRST across the two readers: every Perplexity read is done first (the cheap read returns the most per dollar); what is left of the\n"
    "    # meter buys Grok second reads on the thin answers, in the same order of yield; the thin issuers not reached are the Grok tail\n"
    "    gtail = []; g2 = 0\n"
    "    if GROK and thin:\n"
    "        by = {o['cmr']: o for o in todo}; order = [by[c] for c in sorted(thin, key=lambda c: (-by[c]['disclosure']['filings'], c)) if c in by]\n"
    "        def second(o):\n"
    "            if meter is not None and SP['cost'] >= meter: return {'cmr': o['cmr'], 'tail': True}\n"
    "            return read_one(o, cc, second=True)\n"
    "        with open(raw, 'a', encoding='utf-8') as out, cf.ThreadPoolExecutor(max(2, th // 6)) as ex:\n"
    "            for res in ex.map(second, order):\n"
    "                if res.get('tail'): gtail.append(res['cmr']); continue\n"
    "                if res.get('error'): continue\n"
    "                if not res.get('thin'): out.write(json.dumps(res, ensure_ascii=False) + '\\n'); out.flush(); g2 += 1   # the later line of an issuer is its read of record\n"
    "        print(cc, 'second reads (Grok) that returned a page or a note:', g2, 'of', len(order) - len(gtail), 'asked; not reached at the meter:', len(gtail), flush=True)\n"
    "    sp = os.path.join(d, 'spend.json'); prev")
rep("json.dump({'meter': meter, 'unread': len(tail), 'tail': tail},", "json.dump({'meter': meter, 'unread': len(tail), 'tail': tail, 'thin_after_first_read': len(thin), 'grok_second_reads_not_reached': len(gtail), 'grok_tail': gtail},")
ast.parse(s); p.write_text(s, encoding='utf-8'); print('patched')
