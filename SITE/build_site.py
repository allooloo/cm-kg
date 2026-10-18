"""Renders public/index.html from template.html + public/hero.json. Run after build_facts.py."""
import json, html
h = json.load(open('public/hero.json', encoding='utf-8'))
e = html.escape
def src(u):
    if not u: return ''
    if u.startswith('http'):
        show = u.replace('https://', '').replace('http://', '')
        if len(show) > 60: show = show[:57] + '...'
        return f'<a class="src" href="{e(u)}" rel="noopener">{e(show)}</a>'
    return e(u)
rows = []
for f in h['fields']:
    v = e(f['value'])
    if f['field'] == 'SEDAR+ profile' and f['value'].startswith('http'):
        v = f'<a href="{e(f["value"])}" rel="noopener">{e(f["value"].replace("https://", ""))}</a>'
    if f.get('note'): v += f'<span class="n">{e(f["note"])}</span>'
    rows.append(f'<tr><td class="f">{e(f["field"])}</td><td class="v">{v}</td><td class="s">{src(f["source"])}</td><td class="r">{e(f["read_by"])}</td></tr>')
hero = f'''<figure class="record" id="cmr" aria-label="Capital Markets Record for {e(h['issuer'])}">
  <div class="head"><span class="kind">Capital Markets Record</span><span class="status">{e(h['version'])}, as of {e(h['as_of'])}. {e(h['status'])}</span></div>
  <div class="issuer">{e(h['issuer'])}</div>
  <div class="tick">{e(h['exchange'])}: {e(h['ticker'])}</div>
  <table>
    <thead><tr><th scope="col">Field</th><th scope="col">Value</th><th scope="col">Source</th><th scope="col">Read by</th></tr></thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
  </table>
  <div class="foot">Gaps on this record: <span class="g">{e(h['gaps'] or 'none')}</span>. Record as data: <a href="/hero.json">hero.json</a>. Sweep of record: Canada Width 0, {e(h['as_of'])}.</div>
</figure>'''
t = open('template.html', encoding='utf-8').read()
assert '<!--HERO-->' in t
open('public/index.html', 'w', encoding='utf-8').write(t.replace('<!--HERO-->', hero))
print('index.html written;', len(rows), 'record rows')
