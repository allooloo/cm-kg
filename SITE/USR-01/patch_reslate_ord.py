import pathlib, shutil
p = pathlib.Path(r'C:\ALLOOLOO\CM-KG\RAILS\research\orderability.mjs'); s = p.read_text(encoding='utf-8')
if 'CMKG_ROOT' in s: raise SystemExit('already patched')
shutil.copy2(p, p.with_name('orderability.pre-reslate01-2026-11-12.mjs'))
def rep(o, n):
    global s
    assert s.count(o) == 1, o[:60]; s = s.replace(o, n)
rep("const POND = 'C:\\ALLOOLOO\\CM-KG\\POND', OUT = 'C:\\ALLOOLOO\\CM-KG\\RESEARCH\\orderability'; fs.mkdirSync(OUT, { recursive: true });",
    "// RESLATE-01: the root is the image's (CMKG_ROOT) or the laptop's, so the rail runs in the fleet job as it stands\nconst ROOT = process.env.CMKG_ROOT || 'C:\\ALLOOLOO'; const POND = path.join(ROOT, 'CM-KG', 'POND'), OUT = path.join(ROOT, 'CM-KG', 'RESEARCH', 'orderability'); fs.mkdirSync(OUT, { recursive: true });")
rep("const NODES = JSON.parse(fs.readFileSync('C:\\ALLOOLOO\\SITE\\USR-01\\list_nodes.json', 'utf8')).result.structuredContent.nodes;",
    "const NODES = (await (await fetch('https://mcp.getissuer.ai/mcp', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json', 'user-agent': UA }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'list_nodes', arguments: {} } }), signal: AbortSignal.timeout(60000) })).json()).result.structuredContent.nodes;   // RESLATE-01: the roster read live")
p.write_text(s, encoding='utf-8'); print('ok')
