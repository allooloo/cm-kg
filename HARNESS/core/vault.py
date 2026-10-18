"""vault.py — read each estate's keys at launch from the vault named in C:\\STARTHERE\\STARTHERE.md; never copy, never print.
The harness holds no key of its own. A key is read into memory for the process and handed to the engine client; nothing is written."""
import os

# Vault paths per estate, as STARTHERE's rows give them (2026-09-29). agent-bev and the office read the Allooloo lab keys under the two-brands ruling.
VAULTS = {
    "agent-bev": r"C:\ALLOOLOO\AGENT KEYS",
    "allooloo": r"C:\ALLOOLOO\AGENT KEYS",
    "office": r"C:\ALLOOLOO\AGENT KEYS",
    "gsc": r"C:\GREENCORE\AGENT KEYS\LLM-LABS",
    "a2a-cosmetics": r"C:\GREENCORE\AGENT KEYS\LLM-LABS",
    "a2a-peptides": r"C:\GREENCORE\AGENT KEYS\LLM-LABS",
}
# Cloudflare token pointer per estate (the office and agent-bev borrow Allooloo's; GSC lanes use GREENCORE's)
CF_TOKEN = {"agent-bev": r"C:\ALLOOLOO\AGENT KEYS\cloudflare.txt", "allooloo": r"C:\ALLOOLOO\AGENT KEYS\cloudflare-d1.txt", "office": r"C:\ALLOOLOO\AGENT KEYS\cloudflare.txt",
            "gsc": r"C:\GREENCORE\AGENT KEYS\cloudflare.txt", "a2a-cosmetics": r"C:\GREENCORE\AGENT KEYS\cloudflare.txt", "a2a-peptides": None}
LAB_FILES = {"sonar": "perplexity", "grok": "grok", "openai": "chatgpt", "gemini": "gemini", "mistral": "mistral", "tavily": "tavily", "claude": "claude"}
# login directories per estate root (STARTHERE rows); the harness sets them for its own process and children, never signs in
LOGIN_DIRS = {
    "agent-bev": {"GH_CONFIG_DIR": r"C:\AGENTBEV\.gh"},
    "allooloo": {"AZURE_CONFIG_DIR": r"C:\ALLOOLOO\.azure", "GH_CONFIG_DIR": r"C:\ALLOOLOO\.gh"},
    "office": {"AZURE_CONFIG_DIR": r"C:\MATTHEWKEDDY\.azure", "GH_CONFIG_DIR": r"C:\MATTHEWKEDDY\.gh"},
    "gsc": {"AZURE_CONFIG_DIR": r"C:\GREENCORE\.azure", "GH_CONFIG_DIR": r"C:\GREENCORE\.gh"},
    "a2a-cosmetics": {"AZURE_CONFIG_DIR": r"C:\A2ACOSMETICS\.azure", "GH_CONFIG_DIR": r"C:\A2ACOSMETICS\.gh"},
    "a2a-peptides": {"AZURE_CONFIG_DIR": r"C:\A2APEPTIDES\.azure", "GH_CONFIG_DIR": r"C:\A2APEPTIDES\.gh"},
}
ROOTS = {"agent-bev": r"C:\AGENTBEV", "allooloo": r"C:\ALLOOLOO", "office": r"C:\MATTHEWKEDDY", "gsc": r"C:\GREENCORE", "a2a-cosmetics": r"C:\A2ACOSMETICS", "a2a-peptides": r"C:\A2APEPTIDES"}


def set_login_dirs(estate):
    for k, v in LOGIN_DIRS.get(estate, {}).items(): os.environ[k] = v
    os.environ["CI"] = "1"; os.environ["WRANGLER_SEND_METRICS"] = "false"; os.environ["PYTHONIOENCODING"] = "utf-8"


def key(lab, estate):
    """The key text for a lab from the estate's vault, or None when the file is absent (the lab is then 'no key' for this estate)."""
    p = os.path.join(VAULTS[estate], LAB_FILES.get(lab, lab) + ".txt")
    if not os.path.exists(p): return None
    txt = open(p, encoding="utf-8", errors="ignore").read()
    return max(txt.replace("=", " ").split(), key=len) if txt.strip() else None


def cloudflare_token(estate):
    p = CF_TOKEN.get(estate)
    if not p or not os.path.exists(p): return None
    return open(p, encoding="utf-8").read().strip().splitlines()[0].strip()


def available(estate):
    """Which labs have a key file in this estate's vault (names only; nothing printed beyond that)."""
    return {lab: (key(lab, estate) is not None) for lab in LAB_FILES}
