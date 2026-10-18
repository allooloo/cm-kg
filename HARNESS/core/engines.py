"""engines.py — the laboratory clients the harness uses for width1 and fill. Roles come from the PROGRAM file (core.program.engine_roles), never from here.
Every call is metered into a Spend object (calls, tokens, $ where the lab meters it). A lab whose key is absent or whose account is out of credit
is marked EXHAUSTED and skipped; the run continues. NOTHING here is called in a --dry-run; the Engines object refuses to call unless live=True.
Endpoints of record: Sonar = the Perplexity Agent API (POST https://api.perplexity.ai/v1/responses; agent-bev AB-006 rider; Allooloo 'Perplexity (agent, low)');
Grok = xAI Responses (grok-4-1-fast, web_search); OpenAI = Responses (gpt-5.5, web_search); Gemini = generateContent; Mistral = chat completions; Tavily = search."""
import json, time, urllib.request, urllib.error

from . import vault

ENDPOINTS = {
    "sonar": "https://api.perplexity.ai/v1/responses",
    "grok": "https://api.x.ai/v1/responses",
    "openai": "https://api.openai.com/v1/responses",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    "mistral": "https://api.mistral.ai/v1/chat/completions",
    "tavily": "https://api.tavily.com/search",
}
MODELS = {"sonar": "sonar-pro", "grok": "grok-4-1-fast", "openai": "gpt-5.5", "gemini": "gemini-3.8-flash", "mistral": "mistral-small-latest"}
EXHAUST_CODES = {402, 429}


class Exhausted(Exception): pass


class Spend:
    def __init__(self): self.by_lab = {}

    def add(self, lab, usd=None, tokens=0, calls=1, error=False):
        e = self.by_lab.setdefault(lab, {"calls": 0, "usd": 0.0, "usd_metered": True, "tokens": 0, "errors": 0})
        e["calls"] += calls; e["tokens"] += tokens; e["errors"] += int(error)
        if usd is None: e["usd_metered"] = False
        else: e["usd"] = round(e["usd"] + usd, 6)

    def runs(self, run_id):
        return [{"lab": lab, "amount": (round(e["usd"], 4) if e["usd_metered"] else None), "calls": e["calls"], "run_id": run_id, "tokens": e["tokens"], "errors": e["errors"],
                 "source": "harness meter (usage on each answer)" if e["usd_metered"] else "harness meter: the lab returns no cost field; amount null, tokens recorded"} for lab, e in self.by_lab.items()]


class Engines:
    def __init__(self, estate, roles, live=False, log=print):
        self.estate, self.roles, self.live, self.log = estate, roles, live, log
        self.keys = {lab: vault.key(lab, estate) for lab in vault.LAB_FILES}
        self.exhausted = {lab for lab, k in self.keys.items() if k is None}
        self.spend = Spend()

    def _post(self, url, body, headers, timeout=120):
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=dict(headers, **{"Content-Type": "application/json", "User-Agent": "compound-hunter/1.0"}), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            return e.code, {"error": e.read().decode("utf-8", "replace")[:500]}

    def ask(self, lab, prompt, system=None, want_sources=True, preset="fast"):
        """One read from one lab. Returns {"lab", "text", "sources": [urls], "raw"} or None when the lab is exhausted or refused.
        preset: Sonar's Agent API preset ("low" = grounded page recovery, the agent-bev list reads; "fast" = cold read)."""
        if not self.live: raise RuntimeError("dry run: no laboratory call is made")
        if lab in self.exhausted: return None
        k = self.keys.get(lab)
        try:
            if lab == "sonar":
                # a 429 backs off and asks again (the agent-bev rail's rule), never marks Sonar exhausted
                for k429 in range(8):
                    st, j = self._post(ENDPOINTS[lab], {"preset": preset, "input": prompt}, {"Authorization": "Bearer " + k})
                    if st != 429: break
                    time.sleep(min(300, 15 * (2 ** k429)))
                usd = ((j.get("usage") or {}).get("cost") or {}).get("total_cost") if st == 200 else None
                text, srcs = "", []
                for o in j.get("output", []) or []:
                    if o.get("type") == "search_results": srcs += [s.get("url") for s in (o.get("results") or []) if s.get("url")]
                    if o.get("type") == "message": text += "".join(c.get("text", "") for c in (o.get("content") or []) if isinstance(c, dict) and c.get("type") == "output_text")
                if not text: text = j.get("output_text") or ""
            elif lab in ("grok", "openai"):
                st, j = self._post(ENDPOINTS[lab], {"model": MODELS[lab], "input": ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}], "tools": [{"type": "web_search"}]}, {"Authorization": "Bearer " + k})
                usd = None; text = j.get("output_text") or "".join(c.get("text", "") for o in j.get("output", []) for c in o.get("content", []) if isinstance(c, dict))
                srcs = [a.get("url") for o in j.get("output", []) for c in o.get("content", []) if isinstance(c, dict) for a in c.get("annotations", []) if a.get("url")]
            elif lab == "gemini":
                st, j = self._post(ENDPOINTS[lab].format(model=MODELS[lab]) + "?key=" + k, {"contents": [{"parts": [{"text": ((system + "\n\n") if system else "") + prompt}]}], "tools": [{"google_search": {}}]}, {})
                usd = None; cands = j.get("candidates") or [{}]; text = "".join(p.get("text", "") for p in (cands[0].get("content") or {}).get("parts", []))
                srcs = [c.get("web", {}).get("uri") for c in ((cands[0].get("groundingMetadata") or {}).get("groundingChunks") or []) if c.get("web")]
            elif lab == "mistral":
                st, j = self._post(ENDPOINTS[lab], {"model": MODELS[lab], "messages": ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]}, {"Authorization": "Bearer " + k})
                usd = None; text = ((j.get("choices") or [{}])[0].get("message") or {}).get("content", ""); srcs = []
            elif lab == "tavily":
                st, j = self._post(ENDPOINTS[lab], {"api_key": k, "query": prompt, "max_results": 10}, {})
                usd = None; text = "\n".join(r.get("content", "") for r in j.get("results", [])); srcs = [r.get("url") for r in j.get("results", []) if r.get("url")]
            else:
                return None
        except Exception as e:
            self.spend.add(lab, error=True); self.log(f"[engines] {lab} transport error {e!r}"[:200]); return None
        tokens = 0
        u = j.get("usage") or j.get("usageMetadata") or {}
        if isinstance(u, dict): tokens = (u.get("total_tokens") or u.get("totalTokenCount") or 0)
        if st in EXHAUST_CODES or (st == 400 and "credit" in json.dumps(j).lower()):
            self.exhausted.add(lab); self.spend.add(lab, error=True); self.log(f"[engines] {lab} EXHAUSTED (http {st}); skipped from here"); return None
        self.spend.add(lab, usd=usd, tokens=tokens, error=(st != 200))
        if st != 200: return None
        return {"lab": lab, "text": text, "sources": [s for s in srcs if s], "raw": j}
