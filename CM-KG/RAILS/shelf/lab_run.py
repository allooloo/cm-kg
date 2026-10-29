r"""SHELF-01 proof (Bench) — run three labs against one published bench through the apex, then score each at the scoring door's rule and publish
the three scorecards. Each lab gets the question and one tool, call_door(tool, arguments): an MCP tools/call on the apex router (mcp.getissuer.ai),
which forwards to the market door (get_record with as_of — Replay —, list_events_since, get_timeline, resolve_issuer). The lab answers in JSON
{"answer": ...}. Keys are read in-process from AGENT KEYS (never printed). A fixed first N questions of the bench (default 100) bounds the paid calls;
the scorecard names N. Scorecards are signed by the bench door when it is up (score_bench), else by the same rule here and signed with the CMR key.
Usage: python -X utf8 lab_run.py <cc> <year> [N=100] [--labs claude,chatgpt,gemini]"""
import os, sys, json, re, time, datetime, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'backfill')]
KEYS = r'C:\ALLOOLOO\AGENT KEYS'
APEX = 'https://mcp.getissuer.ai/mcp'; BENCH_DOOR = 'https://mcp.data-bench.ai/mcp'
MODELS = {'claude': 'claude-sonnet-5-5', 'chatgpt': 'gpt-4.1', 'gemini': 'gemini-3.1-pro-preview'}   # gemini-2.5-pro retired for this key (404, 2026-10-28)
SYS = ('You answer questions about listed companies from the Capital Markets Record. Use the tool call_door to read it: the apex router forwards to the '
       'market door. Useful tools: resolve_issuer {identifier}; get_record {identifier, as_of: "YYYY-MM-DD"} (the record as it stood on a date, from the sealed '
       'market-year, with its dated lines); list_events_since {identifier, since}; get_timeline {identifier}. Answer only from what the door returns. '
       'Reply at the end with one line of JSON: {"answer": <integer | "YYYY-MM-DD" | "firm name">}.')
def key(n): return open(os.path.join(KEYS, n), encoding='utf-8').read().strip()
def post(u, body, headers):
    r = urllib.request.urlopen(urllib.request.Request(u, data=json.dumps(body).encode(), headers=dict({'content-type': 'application/json'}, **headers)), timeout=180)
    t = r.read().decode(); return json.loads(t[t.index('{'):]) if t.strip() else {}
def door(u, tool, args):
    j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': tool, 'arguments': args}}, {'accept': 'application/json, text/event-stream', 'user-agent': 'Allooloo lab run (SHELF-01)'})
    return (j.get('result') or {}).get('structuredContent') or j.get('result') or j
TOOL = {'name': 'call_door', 'description': 'MCP tools/call on the Capital Markets Record apex router.', 'parameters': {'type': 'object', 'properties': {'tool': {'type': 'string'}, 'arguments': {'type': 'object'}}, 'required': ['tool', 'arguments']}}
def run_tool(a):
    out = door(APEX, a.get('tool'), a.get('arguments') or {}); s = json.dumps(out, ensure_ascii=False); return s[:20000]
def final(text):
    m = re.findall(r'\{[^{}]*"answer"[^{}]*\}', text or '');
    try: return json.loads(m[-1])['answer'] if m else None
    except Exception: return None
def ask_claude(q):
    msgs = [{'role': 'user', 'content': q}]; h = {'x-api-key': key('claude.txt'), 'anthropic-version': '2023-06-01'}
    for _ in range(8):
        r = post('https://api.anthropic.com/v1/messages', {'model': MODELS['claude'], 'max_tokens': 1500, 'system': SYS, 'tools': [{'name': TOOL['name'], 'description': TOOL['description'], 'input_schema': TOOL['parameters']}], 'messages': msgs}, h)
        msgs.append({'role': 'assistant', 'content': r.get('content', [])}); uses = [c for c in r.get('content', []) if c.get('type') == 'tool_use']
        if not uses: return final(' '.join(c.get('text', '') for c in r.get('content', []) if c.get('type') == 'text'))
        msgs.append({'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': u['id'], 'content': run_tool(u['input'])} for u in uses]})
def ask_chatgpt(q):
    msgs = [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': q}]; h = {'authorization': 'Bearer ' + key('chatgpt.txt')}
    for _ in range(8):
        r = post('https://api.openai.com/v1/chat/completions', {'model': MODELS['chatgpt'], 'messages': msgs, 'tools': [{'type': 'function', 'function': TOOL}]}, h)
        m = r['choices'][0]['message']; msgs.append(m)
        if not m.get('tool_calls'): return final(m.get('content'))
        for tc in m['tool_calls']: msgs.append({'role': 'tool', 'tool_call_id': tc['id'], 'content': run_tool(json.loads(tc['function']['arguments'] or '{}'))})
def ask_gemini(q):
    k = key('gemini.txt'); cont = [{'role': 'user', 'parts': [{'text': q}]}]
    for _ in range(8):
        r = post(f"https://generativelanguage.googleapis.com/v1beta/models/{MODELS['gemini']}:generateContent?key={k}", {'systemInstruction': {'parts': [{'text': SYS}]}, 'contents': cont, 'tools': [{'functionDeclarations': [TOOL]}]}, {})
        parts = ((r.get('candidates') or [{}])[0].get('content') or {}).get('parts') or []; cont.append({'role': 'model', 'parts': parts})
        calls = [p['functionCall'] for p in parts if 'functionCall' in p]
        if not calls: return final(' '.join(p.get('text', '') for p in parts))
        cont.append({'role': 'user', 'parts': [{'functionResponse': {'name': c['name'], 'response': {'result': run_tool(c.get('args') or {})}}} for c in calls]})
ASK = {'claude': ask_claude, 'chatgpt': ask_chatgpt, 'gemini': ask_gemini}
def main():
    a = sys.argv[1:]; cc, year = a[0], int(a[1]); N = int(a[2]) if len(a) > 2 and a[2].isdigit() else 100
    labs = (a[a.index('--labs') + 1].split(',') if '--labs' in a else list(ASK))
    import backfill as BF
    from bench import apex_cont, score
    bench = json.loads(apex_cont('shelf').download_blob(f'bench/bench-{cc}-{year}.json').readall()); Q = bench['questions'][:N]
    keyset = json.loads(apex_cont('shelf-private').download_blob(f'bench/answers-{cc}-{year}.json').readall())
    keyQ = {x['id']: x for x in keyset['answers']}; key_n = [keyQ[q['id']] for q in Q]
    for lab in labs:
        given = []; t0 = time.time()
        for q in Q:
            try: ans = ASK[lab](q['question'])
            except Exception as e: ans = None
            given.append({'id': q['id'], 'answer': ans})
        sc = score(key_n, given)
        card = BF.sign({'scorecard': f'bench-{cc}-{year}', 'agent': f"{lab} ({MODELS[lab]})", 'route': 'through the apex router (mcp.getissuer.ai)', 'questions_run': N, 'of_questions': len(bench['questions']),
                        'manifest_root': bench['manifest']['hash_tree_root'], **{k: sc[k] for k in ('answered', 'passed', 'score')}, 'per_question': sc['per_question'],
                        'scored_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'seconds': round(time.time() - t0), 'rule': 'the scoring door\'s rule (bench.score): exact integer · ISO date · firm name with case, punctuation and LLP set aside'})
        apex_cont('shelf').upload_blob(f'bench/scorecards/{cc}-{year}-{lab}.json', json.dumps(card, ensure_ascii=False).encode(), overwrite=True)
        print(lab, MODELS[lab], 'score', sc['score'], 'passed', sc['passed'], 'of', N, flush=True)
if __name__ == '__main__': main()
