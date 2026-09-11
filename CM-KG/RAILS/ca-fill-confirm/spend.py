"""Lab spend per engine for passes 2 and 3, summed from the worker outputs (tokens, calls, credits). Prices are list prices at 2026-09-10
and are shown as estimates; the counts are exact."""
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
c1 = jload('raw/claude_isin.jsonl') + jload('raw/claude_auditor.jsonl')
c2 = [x for d in jload('raw/rematch.jsonl') for x in [d] if d.get('conflicts')]
n, t = usage_sum(c1, ['input_tokens', 'output_tokens']); out['Claude (claude-sonnet-5)'] = {'calls': n + sum(len(d.get('conflicts', [])) for d in jload('raw/rematch.jsonl')), 'input_tokens': t['input_tokens'], 'output_tokens': t['output_tokens'], 'est_usd': round(t['input_tokens'] * 3 / 1e6 + t['output_tokens'] * 15 / 1e6, 2), 'note': 'rematch collision calls not token-metered in the log'}
b = json.load(open('raw/openai_batch_usage.json')) if os.path.exists('raw/openai_batch_usage.json') else {}
out['ChatGPT (gpt-4.1-mini, Batch)'] = {'calls': b.get('n', 0), 'input_tokens': b.get('usage', {}).get('input', 0), 'output_tokens': b.get('usage', {}).get('output', 0), 'est_usd': round(b.get('usage', {}).get('input', 0) * 0.20 / 1e6 + b.get('usage', {}).get('output', 0) * 0.80 / 1e6, 2), 'note': 'batch pricing (50% of list)'}
n, t = usage_sum(jload('raw/gemini_agm.jsonl'), ['promptTokenCount', 'candidatesTokenCount', 'totalTokenCount']); out['Gemini (gemini-flash-latest)'] = {'calls': n, 'input_tokens': t['promptTokenCount'], 'output_tokens': t['candidatesTokenCount'], 'est_usd': round(t['promptTokenCount'] * 0.30 / 1e6 + t['candidatesTokenCount'] * 2.50 / 1e6, 2)}
n, t = usage_sum(jload('raw/perplexity_pages.jsonl'), ['prompt_tokens', 'completion_tokens']); out['Perplexity (sonar-pro)'] = {'calls': n, 'input_tokens': t['prompt_tokens'], 'output_tokens': t['completion_tokens'], 'est_usd': round(n * 0.006 + t['prompt_tokens'] * 3 / 1e6 + t['completion_tokens'] * 15 / 1e6, 2), 'note': 'sonar-pro: request fee + tokens'}
g = json.load(open('raw/grok_live_usage.json')) if os.path.exists('raw/grok_live_usage.json') else {}
out['Grok (grok-4.6, Responses + search)'] = {'calls': 1, 'input_tokens': 243532, 'output_tokens': 6017, 'est_usd': 0.66, 'note': 'one validation query on 2026-09-10 (cost_in_usd_ticks 6,597,960,000 = $0.66); live layer runs from 2026-09-11'}
n, t = usage_sum(jload('raw/mistral_fr.jsonl'), ['prompt_tokens', 'completion_tokens']); out['Mistral (mistral-small-latest)'] = {'calls': n, 'input_tokens': t['prompt_tokens'], 'output_tokens': t['completion_tokens'], 'est_usd': round(t['prompt_tokens'] * 0.10 / 1e6 + t['completion_tokens'] * 0.30 / 1e6, 2)}
tv = requests.get('https://api.tavily.com/usage', headers=TH, timeout=30).json().get('account', {})
out['Tavily'] = {'plan_usage_now': tv.get('plan_usage'), 'plan_limit': tv.get('plan_limit'), 'used_in_passes_2_3': (tv.get('plan_usage') or 0) - 19768, 'note': 'plan counter read at order start: 19,768'}
out['Cloudflare'] = {'calls': 0, 'note': 'not used in passes 2 and 3'}
json.dump(out, open('raw/spend.json', 'w'), indent=1)
for k, v in out.items(): print(k, v)
