// about-copy.js — NAV-02 (CEO, 2026-11-01): the copy of record of the About/Investor page, v1.0, verbatim (the CEO fine-tunes at v1.1). One page, two hosts:
// about.allooloo.ai lands at About Us, investor.allooloo.ai at Investor Relations. Blocks: ['p', text] · ['lead', bold lead, rest] · ['tiles'] (the eight live
// tiles, read from the record at render) · ['news', lead] (the latest release, read from the news of record at render). No typed count is added to the copy.
export default {
  version: '1.0 (with the CEO\'s three corrections of 2026-11-02)',
  about: {
    label: 'ABOUT US',
    head: 'We are defining a new market: products for AI agents.',
    blocks: [
      ['p', 'Half the jobs in capital markets go to AI agents in 2027. Every one of those agents reads the issuer before it acts — and nothing it could read was built for it. Terminals were built for eyes. Scraped pages have no source, no date, no signature. APIs were built to move prices, not to answer an agent in the middle of a call.'],
      ['p', 'So we built it. Allooloo makes the agentic capital markets record: the issuer\'s own filings, the market\'s own rule, whether a product may be ordered and for whom, the manufacturer\'s target market statement, and the issuer\'s news the moment it lands. Kept in the issuer\'s own country. Signed by that country\'s node. Receipted so an examiner can verify the read. Paid for in the call that reads it — no sales call, no account, no key.'],
      ['tiles'],
      ['p', 'Agents don\'t run on a terminal. They run inside the AI labs — Claude, ChatGPT, Gemini, Copilot, Grok, Perplexity, Mistral. Allooloo is where those agents read. The customers are already calling.'],
      ['lead', 'Made by agents, sold to agents.', 'The whole record is re-slated every week, after the Friday close, by our own OpsAgents — Overnight Engineering. No newsroom, no night shift, no start and no finish to the work day. The record is never older than the last Friday close, in every time zone, every market.'],
      ['lead', 'The Allooloo Way — three steps.', 'The product, security and compliance ship together or not at all. Sovereign: one node per market, in that market. Secure: the record in two clouds, keys in a vault, every read receipted, every door read from outside by simulated customer agents every day. Compliant: each market\'s rule read from the regulator\'s own text, re-read weekly, named on every outcome. Not all market data is created equal. Agentic data is a craft, not an industrial process.'],
      ['lead', 'Who\'s behind it.', 'Matthew Keddy, Chief Executive Officer — four-time CEO across three decades, Web 1.0, Web 2.0 e-commerce and consumer goods; coined Know Your Product (KYP) and AI Orderability (AIO).'],   // the CEO, 2026-11-02: "The rest of the staff are agents." struck
      ['lead', 'Where.', 'Vancouver, Canada — the record, the OpsAgents and the books. London, UK, planned for 2027 — the European banks and the manufacturers filing under MiFID II.'],
      ['news', 'In the news.'],
    ],
  },
  investor: {
    label: 'INVESTOR RELATIONS',
    head: 'Capital Markets: Data is Agent Fuel.',
    blocks: [
      ['p', 'Two markets are converging and Allooloo sits where they meet. The spend on AI in financial services is now the size of the market-data industry it is about to replace — and that industry sells seats to people. Nobody sells the record to the agent. We do.'],
      ['lead', 'The product is live.', 'Four doors, one per question an agent asks: the issuer, the orderability outcome, the manufacturer\'s target market statement, the issuer\'s news. One in-country node per market. Every answer signed, dated, sourced to the regulator\'s page and receipted. Five years of the record sealed by year — done, not building. Figures are read from the live record on every product page.'],
      ['lead', 'Two ways we are paid.', 'Pay as you go — agents pay by the read, in the call, on x402; the traffic at the door is the order book. Licence — firms license the record and the things built on it: the live record for every agent in the house, the dated record for replay and reconstruction, the archived record in a second cloud as the firm\'s own copy, and the named products on the shelf. The standards beneath are open and stay open; the record and the receipts are ours.'],
      ['lead', 'Why we win.', 'Revenue grows with agent traffic; cost does not. The record is re-slated every week, after the Friday close, by our own OpsAgents, run by our own OpsAgents — the economics of a data company with the headcount of a founder\'s office. Every frontier lab is a channel, not a competitor: their agents read our doors. And the record compounds — every week\'s run makes the dataset the next generation of finance agents is trained on.'],
      ['lead', 'What\'s next.', 'The first Agentic Desks and Issuer seats. The record licensed per market-year. London for the European banks. Sales and engineering grow; the agents keep running the record.'],
      ['lead', 'Governance.', 'Matthew Keddy, Chief Executive Officer.'],
      ['lead', 'For investors.', 'The investor presentation and company documents are available to qualified investors on request through the contact below.'],
      ['p', 'Not an offer to sell securities. Any offering is made only through official offering documents in accordance with applicable securities law.'],
    ],
  },
};
