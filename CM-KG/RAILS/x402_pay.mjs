// x402 v2 test client — 402 → signed EIP-3009 authorization → 200 + receipt. Packages @x402/fetch + @x402/evm (x402-foundation, protocol v2, CAIP-2 networks).
// The payer key is read from AGENT KEYS/x402-payer-key.txt (generated 2026-09-13, never printed); X402_PRIVATE_KEY in the env overrides.
//   node x402_pay.mjs https://agentic-x402.ai/api                                       (Base Sepolia, test USDC)
//   node x402_pay.mjs "https://agentic-x402.ai/api?record=uk-cm-kg/LSE/BARC"
//   node x402_pay.mjs https://agentic-trades.ai/x402/record/uk-cm-kg/LSE/BARC          (Base mainnet, $0.01 real)
// Prints the status, the PAYMENT-RESPONSE (tx hash, network, amount) and the receipt URL; never prints the key.
import { readFileSync } from 'fs';
import { wrapFetchWithPaymentFromConfig, decodePaymentResponseHeader } from '@x402/fetch';
import { ExactEvmScheme } from '@x402/evm';
import { privateKeyToAccount } from 'viem/accounts';
const url = process.argv[2]; if (!url) { console.error('usage: node x402_pay.mjs <url>'); process.exit(2); }
let pk = process.env.X402_PRIVATE_KEY; if (!pk) { try { pk = readFileSync('C:/ALLOOLOO/AGENT KEYS/x402-payer-key.txt', 'utf8').trim(); } catch (e) { console.error('no key: set X402_PRIVATE_KEY or place AGENT KEYS/x402-payer-key.txt'); process.exit(2); } }
const account = privateKeyToAccount(pk);
console.log('payer', account.address);
const paidFetch = wrapFetchWithPaymentFromConfig(fetch, { schemes: [{ network: 'eip155:*', client: new ExactEvmScheme(account) }] });
let r;
try { r = await paidFetch(url, { method: 'GET', headers: { accept: 'application/json', 'user-agent': 'Allooloo Technologies Corp. developers@allooloo.ai' } }); }
catch (e) { console.error('client error:', e && e.message ? e.message : e); process.exit(1); }
console.log('status', r.status);
const pr = r.headers.get('payment-response') || r.headers.get('x-payment-response');
if (pr) { try { console.log('payment-response', JSON.stringify(decodePaymentResponseHeader(pr))); } catch (e) { console.log('payment-response (raw b64)', pr.slice(0, 80) + '…'); } }
console.log('receipt url', r.headers.get('x-x402-receipt') || '(none — the trades route carries the receipt in PAYMENT-RESPONSE only)');
const body = await r.text(); console.log(body.slice(0, 1500));
