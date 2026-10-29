// prompt.js — PROMPT-01 (DAY ORDER 6, 2026-10-25): on every signal page (acm-000 … acm-500.ai) one copyable prompt block — the exact text an agent user
// pastes into Claude or ChatGPT to read this signal through the apex door — and the Add-to buttons for the doors. Generated from the signal register (S in
// index.js: code, standard, action, meaning, example) and the live roster count (list_nodes); nothing typed per page.
const APEX = 'https://mcp.getissuer.ai/mcp', SIGNALS = 'https://mcp.getissuer.ai/signals/mcp';
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
export function signalPrompt(code, s, id) {
  return [`Use the ACM-68000 signals MCP server at ${SIGNALS} (Allooloo; read-only, no sign-in).`,
    `Call get_signal with ${id ? `"${id}"` : 'the identifier I give you (ticker, ISIN or LEI)'} and tell me the signal it answers.`,
    `If it is ACM-${code} (${s.std}): ${s.when} The action of the standard is: ${s.action}`,
    `Quote the signal, the issuer, its home node and as-of date, and the receipt decision_id; answer only from the tool. For the full record use ${APEX} (resolve_issuer, get_record).`].join('\n');
}
const b64 = t => btoa(unescape(encodeURIComponent(t)));
const addTo = (name, url) => [['Claude', 'https://claude.ai/settings/connectors', 'Settings → Connectors → Add custom connector → paste the door URL'],
  ['ChatGPT', 'https://chatgpt.com/#settings/Connectors', 'Settings → Connectors (developer mode) → Create → paste the door URL'],
  ['Cursor', `cursor://anysphere.cursor-deeplink/mcp/install?name=${encodeURIComponent(name)}&config=${encodeURIComponent(b64(JSON.stringify({ url })))}`, 'opens Cursor with the server filled in'],
  ['VS Code', `vscode:mcp/install?${encodeURIComponent(JSON.stringify({ name, type: 'http', url }))}`, 'opens VS Code with the server filled in']];
export function signalBlock(code, s, id) {
  const doors = [['acm-signals (the signal door)', 'acm-signals', SIGNALS], ['getissuer (the apex door, records)', 'getissuer', APEX]];
  const btns = doors.map(([label, name, url]) => `<p style="margin:.4em 0"><strong>${esc(label)}</strong> <code>${esc(url)}</code><br>${addTo(name, url).map(([who, href, how]) => `<a href="${esc(href)}" rel="noopener" title="${esc(how)}" style="display:inline-block;margin:.2em .4em .2em 0;padding:.2em .7em;border:1px solid currentColor;border-radius:4px;text-decoration:none">Add to ${esc(who)}</a>`).join('')}</p>`).join('');
  return `<section id="ask"><h2>Ask an agent — ACM-${esc(code)}</h2><p>Paste this into Claude or ChatGPT once the door is connected (one click selects it all):</p><pre style="white-space:pre-wrap;user-select:all;-webkit-user-select:all;padding:.8em;border:1px solid #ccc;border-radius:4px;background:rgba(0,0,0,.03)">${esc(signalPrompt(code, s, id))}</pre>${btns}<p class="meta" style="font-size:.85em">Generated from the ACM-68000 signal register at render — PROMPT-01.</p></section>`;
}
