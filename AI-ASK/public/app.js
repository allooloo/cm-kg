(function () {
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const link = (u, t) => u ? `<a href="${esc(u)}" rel="noopener">${esc(t || u.replace(/^https?:\/\//, '').slice(0, 70))}</a>` : '';
  let filledOnce = false; let current = null;
  function setParsed(idf) {
    const p = $('parsed');
    if (!idf || !idf.picked) { p.innerHTML = idf && idf.candidates && idf.candidates.length ? `<b>${esc(idf.candidates.join(', '))}</b><span class="sep">·</span>${esc(idf.kind ? 'no match' : 'unresolved')}` : ''; return; }
    const m = idf.matches[0];
    p.innerHTML = `<b>${esc(m.ticker)}</b><span class="sep">·</span>${esc(m.exchange)}<span class="sep">·</span>${esc(m.isin || 'ISIN blank')}<span class="sep">·</span>${esc(m.node === 'ca-cm-kg' ? 'Canada node' : m.node)}${idf.kind === 'alias' ? '<span class="sep">·</span>matched on a sourced alias' : ''}`;
  }
  function fillRecord(rec) {
    const box = $('record'); const dl = $('rec');
    if (!rec) { dl.querySelectorAll('dd').forEach(d => { d.textContent = '—'; d.className = ''; }); $('recmeta').textContent = ''; return; }
    dl.querySelectorAll('dd').forEach(d => {
      const f = rec.identity[d.dataset.f];
      if (!f || f.value === null) { d.innerHTML = `<span>blank</span>`; d.className = 'null'; d.title = (f && f.reason) || ''; return; }
      d.className = ''; d.innerHTML = `${esc(f.value)}${f.state ? `<span class="st ${esc(f.state)}">${esc(f.state)}</span>` : ''}`; d.title = (f.read_by || '') + (f.source_url ? ' · ' + f.source_url : '');
    });
    $('recmeta').textContent = `${rec.cmr} · as of ${rec.as_of} · version ${rec.version} · ${rec.event_count} events · ${rec.aliases.length} sourced alias${rec.aliases.length === 1 ? '' : 'es'}`;
    if (!filledOnce) { box.classList.add('fill'); filledOnce = true; }
  }
  function renderAnswer(r) {
    const a = r.answer; const b = $('abody'); let h = '';
    if (!a) { b.innerHTML = '<p class="muted">No answer.</p>'; return; }
    h += `<h3>${esc(a.title)}</h3>`;
    if (a.kind === 'field') {
      if (a.value !== null && a.value !== undefined) {
        h += `<div class="value">${/^https?:\/\//.test(a.value) ? link(a.value) : esc(a.value)}<span class="state ${esc(a.state || '')}">${esc(a.state || 'sourced')}</span></div>`;
        if (a.source_url) h += `<p class="src">source: ${link(a.source_url)}</p>`;
        h += `<p class="src">read by: ${esc(a.read_by || '')}</p>`;
        if (a.second_source_url) h += `<p class="src">second source: ${link(a.second_source_url)}${a.second_read_by ? ' · ' + esc(a.second_read_by) : ''}</p>`;
        if (a.note) h += `<p class="src">note: ${esc(a.note)}</p>`;
      } else { h += `<div class="value">blank<span class="state blank">blank</span></div><p>${esc(a.text)}</p>`; }
    } else if (a.kind === 'list' || a.kind === 'facts' || a.kind === 'pick') {
      if (a.text) h += `<p>${esc(a.text)}</p>`;
      if (a.rows && a.rows.length) {
        h += '<table><thead><tr><th>Date</th><th>Event</th><th>Read by</th></tr></thead><tbody>';
        for (const e of a.rows) h += `<tr><td class="d">${esc(e.date || '')}</td><td>${e.pick ? `<button type="button" class="pick" data-pick="${esc(e.pick)}">${esc(e.title)}</button>` : (e.url ? link(e.url, e.title) : esc(e.title))}${e.type ? ` <span class="state">${esc(e.type)}</span>` : ''}</td><td class="d">${esc(e.read_by || '')}${e.state ? ` · ${esc(e.state)}` : ''}</td></tr>`;
        h += '</tbody></table>';
        if (a.total != null) h += `<p class="cites">${a.total} row${a.total === 1 ? '' : 's'}</p>`;
      }
    } else { h += `<p>${esc(a.text).replace(/\n/g, '<br>')}</p>`; }
    if (a.cites && a.cites.length) h += `<p class="cites">cited: ${esc(a.cites.join(' · '))}</p>`;
    b.innerHTML = h;
    b.querySelectorAll('.pick').forEach(btn => btn.addEventListener('click', () => { $('ident').value = btn.dataset.pick; run(); }));
    const f = r.footer || {};
    $('f-state').textContent = f.state || '—'; $('f-node').textContent = f.node ? `${f.node}${f.as_of ? ' · as of ' + f.as_of : ''}${f.version ? ' · v' + f.version : ''}` : '—'; $('f-read').textContent = f.read_by ? 'read by ' + f.read_by.replace(/^read by /, '') : '—';
    $('copy').disabled = !r.share_url; $('copy').dataset.url = r.share_url || '';
    const open = $('open'); if (r.record) { open.href = r.record.events_url.replace('/events/', '/record/'); open.hidden = false; } else open.hidden = true;
    const also = $('also'); const chips = $('alsochips'); chips.innerHTML = '';
    if (r.also && r.also.length) { also.hidden = false; for (const c of r.also) { const btn = document.createElement('button'); btn.type = 'button'; btn.textContent = c.label; btn.addEventListener('click', () => { $('q').value = c.q; run(); }); chips.appendChild(btn); } } else also.hidden = true;
    const sg = $('sugg'); const ul = $('sugglist'); ul.innerHTML = '';
    if (r.suggested && r.suggested.length) { sg.hidden = false; for (const s of r.suggested) ul.insertAdjacentHTML('beforeend', `<li>${link(s.href, s.label)}<span class="src">${esc(s.src || '')}</span></li>`); } else sg.hidden = true;
  }
  async function run() {
    const q = $('q').value.trim(); const id = $('ident').value.trim();
    if (!q && !id) return;
    $('status').textContent = 'reading the record…'; $('go').disabled = true;
    try {
      const r = await fetch('/api/ask', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ q: q || (id ? 'record' : ''), id }) });
      const j = await r.json(); current = j;
      if (j.error) { $('abody').innerHTML = `<p>${esc(j.message || j.error)}</p>`; $('status').textContent = ''; return; }
      setParsed(j.identifier); fillRecord(j.record); renderAnswer(j);
      if (j.identifier && j.identifier.picked && !id) $('ident').value = `${j.identifier.matches[0].exchange}:${j.identifier.matches[0].ticker}`;
      const u = new URL(location.href); if (j.identifier && j.identifier.picked) u.searchParams.set('id', `${j.identifier.matches[0].exchange}:${j.identifier.matches[0].ticker}`); else u.searchParams.delete('id'); if (q) u.searchParams.set('q', q); history.replaceState(null, '', u.toString());
      $('status').textContent = '';
    } catch (e) { $('abody').innerHTML = '<p>The desk could not reach the door. Try again.</p>'; $('status').textContent = ''; }
    $('go').disabled = false;
  }
  $('ask').addEventListener('submit', e => { e.preventDefault(); run(); });
  $('ident').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); if (!$('q').value.trim()) $('q').value = 'record'; run(); } });
  document.querySelectorAll('.sample').forEach(b => b.addEventListener('click', () => { if (b.dataset.id) $('ident').value = b.dataset.id; $('q').value = b.dataset.q; run(); }));
  $('copy').addEventListener('click', async () => { try { await navigator.clipboard.writeText($('copy').dataset.url); $('copy').textContent = 'copied'; setTimeout(() => { $('copy').textContent = 'copy link'; }, 1500); } catch (e) { prompt('Copy this link', $('copy').dataset.url); } });
  const u = new URL(location.href);
  if (u.searchParams.get('id') || u.searchParams.get('q')) { $('ident').value = u.searchParams.get('id') || ''; $('q').value = u.searchParams.get('q') || ''; run(); }
})();
