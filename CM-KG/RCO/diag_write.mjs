// diag_write.mjs — RCO-A-01 read-the-wire diagnostic: the resolver's receipt module, run once from the laptop with the keys read by file name (never printed).
import fs from 'node:fs';
import { decisionId, writeReceipt } from '../DOOR/apex/rco.js';
const env = { RCO_SIGNING_JWK: fs.readFileSync('C:/ALLOOLOO/AGENT KEYS/rco-signing-jwk.txt', 'utf8'), RCO_WRITE_KEY: fs.readFileSync('C:/ALLOOLOO/AGENT KEYS/rco-write-key.txt', 'utf8').trim() };
const id = decisionId();
const out = await writeReceipt(env, { decision_id: id, object: { type: 'isin', id: 'FR0000120271' }, actor_class: 'ai-agent (MCP client)', rule: { id: 'getissuer resolve_issuer — diagnostic', version: '0.14.0' },
  records_read: [{ url: 'https://mcp.fr-cm-kg.ai/record/XPAR/FR0000120271', as_of: '2026-10-23', sha256: null, signature: null }], signal: 'ACM-200', decided_at: new Date().toISOString(), issuing_door: 'https://mcp.getissuer.ai/mcp' });
console.log(id, JSON.stringify(out).slice(0, 600));
