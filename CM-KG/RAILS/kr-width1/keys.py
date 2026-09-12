import os
KEYDIR=r"C:\ALLOOLOO\AGENT KEYS"
MAP={'TAVILY_API_KEY':'tavily.txt','PERPLEXITY_API_KEY':'perplexity.txt','OPENAI_API_KEY':'chatgpt.txt','ANTHROPIC_API_KEY':'claude.txt','GEMINI_API_KEY':'gemini.txt','XAI_API_KEY':'grok.txt','MISTRAL_API_KEY':'mistral.txt','DART_API_KEY':'dart.txt','EDINET_API_KEY':'edinet.txt'}
def load():
    for env,fn in MAP.items():
        p=os.path.join(KEYDIR,fn)
        if os.path.exists(p) and not os.environ.get(env):
            os.environ[env]=open(p,encoding='utf-8').read().strip()
load()
