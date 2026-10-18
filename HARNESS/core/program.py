"""program.py — read PROGRAM\\<estate>.md: sections, tables, the scope block, engine roles, sources. Engine roles come from here, never from code."""
import os, re

COMPOUND = r"C:\COMPOUND"


def load(estate, root=COMPOUND):
    p = os.path.join(root, "PROGRAM", f"{estate}.md")
    if not os.path.exists(p): raise FileNotFoundError(f"no program file for {estate}: {p}")
    txt = open(p, encoding="utf-8").read()
    secs, cur = {}, None
    for line in txt.splitlines():
        m = re.match(r"^##\s+(.*)", line)
        if m: cur = m.group(1).strip(); secs[cur] = []
        elif cur is not None: secs[cur].append(line)
    return Program(estate, p, {k: "\n".join(v) for k, v in secs.items()})


def table(section):
    rows = []
    for line in (section or "").splitlines():
        if line.startswith("|") and not re.match(r"^\|\s*-", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[1:] if rows else []


def bullets(section):
    return [re.sub(r"^\s*(\d+\.|-)\s*", "", l) for l in (section or "").splitlines() if re.match(r"^\s*(\d+\.|-)\s+", l)]


class Program:
    def __init__(self, estate, path, secs):
        self.estate, self.path, self.secs = estate, path, secs

    def section(self, name): return self.secs.get(name, "")

    def scope(self):
        s = self.section("Standing scope")
        sid = re.search(r"^\s*-?\s*id:\s*(.+)$", s, re.M); go = re.search(r"^\s*-?\s*go:\s*(.+)$", s, re.M)
        go_v = go.group(1).strip() if go else None
        return {"id": sid.group(1).strip() if sid else None, "go": None if (go_v in (None, "none", "")) else go_v}

    def engine_roles(self):
        """lead, second, review_only, touch_up, search_layer — read from the Engine roles bullets; a lab named nowhere has no role."""
        roles = {"lead": None, "second": [], "review_only": [], "touch_up": [], "fallback": [], "search_layer": None, "lead_reads_on": {}}
        LABS = ("sonar", "perplexity", "grok", "mistral", "openai", "gemini", "tavily", "claude", "chatgpt")
        for b in bullets(self.section("Engine roles")):
            # a bullet may name several labs, one clause each ("Gemini touch-up: …; Mistral review-only …"); each clause is judged on its own
            for clause in re.split(r";", b):
                low = clause.strip().lower()
                m = re.match(r"^(?:and\s+)?(%s)" % "|".join(LABS), low)
                if not m: continue
                lab = {"perplexity": "sonar", "chatgpt": "openai"}.get(m.group(1), m.group(1))
                if "reads on" in low:
                    mm = re.search(r"leads reads on ([^.]+)", low)
                    if mm: roles["lead_reads_on"][lab] = [x.strip() for x in re.split(r",| and ", re.sub(r"\(.*?\)", "", mm.group(1))) if x.strip()]
                    continue
                if re.search(r"\blead(s)?\b", low) and not re.search(r"never lead|not lead", low) and not roles["lead"]: roles["lead"] = lab
                if "search layer" in low and not roles["search_layer"]: roles["search_layer"] = lab
                if "second" in low: roles["second"].append(lab)
                if "review-only" in low or "review only" in low: roles["review_only"].append(lab)
                if "touch-up" in low or "touch up" in low: roles["touch_up"].append(lab)
                if "fallback" in low or "support only" in low: roles["fallback"].append(lab)
        if not roles["lead"]: roles["lead"] = roles["search_layer"] or "sonar"  # Book § 3: Sonar leads by default
        return roles

    def published_totals(self): return table(self.section("Published totals"))

    def extras(self): return table(self.section("Extras"))

    def nodes(self):
        """node codes named in § Nodes as `<cc>-<suffix>` tokens, in order, unique."""
        seen, out = set(), []
        for m in re.finditer(r"\b([a-z]{2}-[a-z][a-z-]*kg|[a-z]{2}-bev|[A-Z]{2})\b", self.section("Nodes")):
            t = m.group(1)
            if t not in seen: seen.add(t); out.append(t)
        return out

    def vault(self):
        return bullets(self.section("Keys and vault"))
