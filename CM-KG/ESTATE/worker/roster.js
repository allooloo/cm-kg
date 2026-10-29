// roster.js — ENUM-01 (DAY ORDER 6, 2026-10-25): one market roster, read everywhere. The roster of record is the apex nodes.json, served by list_nodes;
// nothing in this Worker holds its own list of markets. setRoster() is called with every list_nodes read (surfaces.js liveNodes, the status probe) and
// rewrites, in place, the module values the pages already import: ORDER (the live node codes, roster order), REGION_FULL (a node's region, from its
// roster entry where no curated line exists), DUTY (the roster's duty line where the page has none), NODE_DATA (a stub with the roster's country for a
// node with no page content of its own — flagged stub, never classified as a node host). Policy keyed by market (page content, ESG sources) stays
// explicit; a roster node with no line prints blank (sourced or blank) and the gap is listed in /status.json under roster_gaps.
import { ORDER, DUTY } from './products.js';
import { REGION_FULL } from './chrome.js';
import NODE_DATA from './nodes.js';
export const APEX_MCP = 'https://mcp.getissuer.ai/mcp';
export const ROSTER = { nodes: [], read_at: null };
export const ccOf = n => String(n.node || '').split('-')[0];
export function setRoster(list) {
  const all = Array.isArray(list) ? list : Object.values(list || {});
  if (!all.length) return ROSTER;
  ROSTER.nodes = all; ROSTER.read_at = new Date().toISOString();
  const live = all.filter(n => n.live);
  ORDER.length = 0; for (const n of live) ORDER.push(ccOf(n));
  for (const n of live) {
    const cc = ccOf(n); const r = n.region || {};
    if (!REGION_FULL[cc] && r.azure) REGION_FULL[cc] = `${r.azure} (${r.city ? r.city + ', ' : ''}${n.country})`;
    if (!DUTY[cc] && n.duty) DUTY[cc] = n.duty;
    if (!NODE_DATA[cc]) NODE_DATA[cc] = { country: n.country, region: REGION_FULL[cc] || '', gaps: '', stub: true };
  }
  return ROSTER;
}
export async function readRoster() {
  const r = await fetch(APEX_MCP, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json', 'user-agent': 'Allooloo estate (ENUM-01 roster)' }, body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name: 'list_nodes', arguments: {} } }), signal: AbortSignal.timeout(20000) });
  const j = await r.json(); return setRoster(j.result.structuredContent.nodes);
}
// the public door of a node, from its roster entry (the field of record), never rebuilt from the code
export const doorOf = n => String((n && (n.door || n.regional_door)) || '').replace(/\/mcp$/, '').replace(/\/$/, '');
export const cardOf = n => { const d = doorOf(n); return d.includes('.eu-cm-kg.ai') ? `${d}/.well-known/agent-card.json` : `${d.replace('://mcp.', '://agent.')}/.well-known/agent-card.json`; };
