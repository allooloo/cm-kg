r"""Lab spend per engine for passes 2 and 3, summed from the worker outputs (tokens, calls, credits). Prices are list prices at 2026-09-11 and are
estimates; the counts are exact. Written to raw/spend.json and appended to CM-KG\SPEND\uk-cm-kg-<yyyy-mm>.jsonl."""
from fc_common import *
from collections import Counter
def usage_sum(rows, keys):
    t = Counter(); n = 0
    for d in rows:
        u = d.get('usage') or {}
        if not u: continue
        n += 1
        for k in keys: t[k] += int(u.get(k, 0) or 0)
    return n, t
out = {}
c1 = jload('raw/claude_lei.jsonl') + jload('raw/claude_ch.jsonl') + jload('raw/claude_auditor.jsonl') + jload('raw/conflict_rulings.jsonl')
c2 = [c for d in jload('raw/rematch.jsonl') for c in d.get('conflicts', [])]
n, t = usage_sum(c1 + c2, ['input_tokens', 'output_tokens']); out['Claude (claude-sonnet-5)'] = {'calls': n, 'input_tokens': t['input_tokens'], 'output_tokens': t['output_tokens'], 'est_usd': round(t['input_tokens'] * 3 / 1e6 + t['output_tokens'] * 15 / 1e6, 2)}
ua = json.load(open('raw/chatgpt_accounts_usage.json')) if os.path.exists('raw/chatgpt_accounts_usage.json') else {}
ur = json.load(open('raw/chatgpt_results_usage.json')) if os.path.exists('raw/chatgpt_results_usage.json') else {}
ti = ua.get('usage', {}).get('input', 0) + ur.get('usage', {}).get('input', 0); to = ua.get('usage', {}).get('output', 0) + ur.get('usage', {}).get('output', 0)
out['ChatGPT (gpt-4.1-mini, Batch)'] = {'calls': ua.get('n', 0) + ur.get('n', 0), 'accounts_parts': ua.get('n', 0), 'results_reads': ur.get('n', 0), 'input_tokens': ti, 'output_tokens': to, 'est_usd': round(ti * 0.20 / 1e6 + to * 0.80 / 1e6, 2), 'note': 'batch pricing (50% of list); accounts PDFs read as page images'}
n, t = usage_sum(jload('raw/gemini_agm.jsonl'), ['promptTokenCount', 'candidatesTokenCount']); out['Gemini (gemini-flash-latest)'] = {'calls': n, 'input_tokens': t['promptTokenCount'], 'output_tokens': t['candidatesTokenCount'], 'est_usd': round(t['promptTokenCount'] * 0.30 / 1e6 + t['candidatesTokenCount'] * 2.50 / 1e6, 2)}
pp = jload('raw/perplexity_pages.jsonl'); n, t = usage_sum(pp, ['prompt_tokens', 'completion_tokens', 'input_tokens', 'output_tokens'])
metered = sum(float((d.get('cost') or {}).get('total_cost') or 0) for d in pp)
out['Perplexity'] = {'calls': n, 'input_tokens': t['prompt_tokens'] + t['input_tokens'], 'output_tokens': t['completion_tokens'] + t['output_tokens'], 'est_usd': round(metered, 2) if metered else round(n * 0.006 + t['prompt_tokens'] * 3 / 1e6 + t['completion_tokens'] * 15 / 1e6, 2), 'note': 'Agent API usage.cost when present (metered), else sonar-pro request fee + tokens (estimate)'}
g = json.load(open('raw/grok_live_usage.json')) if os.path.exists('raw/grok_live_usage.json') else {}
gu = Counter()
for u in g.get('usage') or []:
    for k in ('input_tokens', 'output_tokens'): gu[k] += int((u or {}).get(k, 0) or 0)
out['Grok (grok-4.6, Responses + search)'] = {'calls': len(g.get('usage') or []), 'input_tokens': gu['input_tokens'], 'output_tokens': gu['output_tokens'], 'est_usd': round(gu['input_tokens'] * 3 / 1e6 + gu['output_tokens'] * 15 / 1e6 + 0.025 * len(g.get('usage') or []), 2), 'note': 'validation queries on the backfill day; live layer runs weekly'}
n, t = usage_sum(jload('raw/mistral_reads.jsonl'), ['prompt_tokens', 'completion_tokens']); out['Mistral (mistral-small-latest)'] = {'calls': n, 'input_tokens': t['prompt_tokens'], 'output_tokens': t['completion_tokens'], 'est_usd': round(t['prompt_tokens'] * 0.10 / 1e6 + t['completion_tokens'] * 0.30 / 1e6, 2)}
try:
    tv = requests.get('https://api.tavily.com/usage', headers=TH, timeout=30).json().get('account', {})
except Exception: tv = {}
start = json.load(open('raw/tavily_start.json')).get('plan_usage') if os.path.exists('raw/tavily_start.json') else None
out['Tavily'] = {'plan_usage_now': tv.get('plan_usage'), 'plan_limit': tv.get('plan_limit'), 'used_in_passes_2_3': ((tv.get('plan_usage') or 0) - start) if start is not None else None, 'note': f'plan counter read at order start: {start}'}
out['Cloudflare'] = {'calls': 0, 'note': 'not used in passes 2 and 3'}
json.dump(out, open('raw/spend.json', 'w'), indent=1)
os.makedirs(r'C:\ALLOOLOO\CM-KG\SPEND', exist_ok=True)
with open(r'C:\ALLOOLOO\CM-KG\SPEND\uk-cm-kg-' + TODAY.strftime('%Y-%m') + '.jsonl', 'a', encoding='utf-8') as f:
    f.write(json.dumps({'date': TODAY.isoformat(), 'order': 'ORDER-009', 'spend': out}) + '\n')
for k, v in out.items(): print(k, v)
