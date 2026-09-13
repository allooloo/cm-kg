// x402 test client for the CEO's funded wallet — 402 → signed EIP-3009 authorization → 200 + receipt.
// The private key never goes through CC: put it in an env var from your own file and run this yourself.
//   npm i x402-fetch viem            (once, in C:\ALLOOLOO\CM-KG\RAILS)
//   set X402_PRIVATE_KEY=0x…          (a Base Sepolia wallet holding test USDC; Base mainnet for the trades route)
//   node x402_pay.mjs https://agentic-x402.ai/api
//   node x402_pay.mjs "https://agentic-x402.ai/api?record=uk-cm-kg/LSE/BARC"
//   node x402_pay.mjs https://agentic-trades.ai/x402/record/uk-cm-kg/LSE/BARC      (Base mainnet, $0.01 real)
// Prints the status, the PAYMENT-RESPONSE (tx hash, network, amount) and the receipt URL; never prints the key.
import { wrapFetchWithPayment, decodeXPaymentResponse } from 'x402-fetch';
import { privateKeyToAccount } from 'viem/accounts';
const url = process.argv[2]; if (!url) { console.error('usage: node x402_pay.mjs <url>'); process.exit(2); }
const pk = process.env.X402_PRIVATE_KEY; if (!pk) { console.error('X402_PRIVATE_KEY is not set'); process.exit(2); }
const account = privateKeyToAccount(pk);
console.log('payer', account.address);
const paidFetch = wrapFetchWithPayment(fetch, account);
const r = await paidFetch(url, { headers: { accept: 'application/json', 'user-agent': 'Allooloo Technologies Corp. developers@allooloo.ai' } });
console.log('status', r.status);
const pr = r.headers.get('payment-response') || r.headers.get('x-payment-response');
if (pr) { try { console.log('payment-response', JSON.stringify(decodeXPaymentResponse(pr))); } catch (e) { console.log('payment-response (raw b64)', pr.slice(0, 80) + '…'); } }
console.log('receipt url', r.headers.get('x-x402-receipt') || '(none — the trades route carries the receipt in PAYMENT-RESPONSE only)');
const body = await r.text(); console.log(body.slice(0, 1200));
