// ORDER-034 wire captures (capture_034.py) — read-only calls to the public doors; never typed.
export const KYP_CAPTURE = {
 "captured": "2026-10-22T23:38:38Z",
 "door": "https://mcp.getissuer.ai/mcp",
 "request": {
  "tool": "get_record",
  "arguments": {
   "identifier": "LSE:SHEL"
  }
 },
 "response": {
  "cmr": "uk-cm-kg/LSE/SHEL",
  "node": "uk-cm-kg",
  "as_of": "2026-10-17",
  "version": 1,
  "identity": {
   "name": {
    "value": "SHELL PLC",
    "source_url": "https://www.londonstockexchange.com/live-markets/market-data-dashboard/price-explorer (price-explorer feed api.londonstockexchange.com/api/v1/components/refresh, markets=MAINMARKET, categories=EQUITY, showonlylse=true)",
    "read_by": "LSE price explorer (exchange list)",
    "state": "sourced"
   },
   "isin": {
    "value": "GB00BP6MXD84",
    "source_url": "https://api.londonstockexchange.com/api/gw/lse/instruments/alldata/SHEL",
    "read_by": "LSE instrument reference record (exchange site)",
    "state": "confirmed",
    "second_source_url": "https://mapping.gleif.org/api/v2/isin-lei/latest",
    "second_read_by": "GLEIF ISIN-to-LEI mapping file carries this ISIN against the issuer's LEI"
   },
   "lei": {
    "value": "21380068P1DRHMJ8KU70",
    "source_url": "https://mapping.gleif.org/api/v2/isin-lei/latest (isin-lei-20260911T071509.zip)",
    "read_by": "GLEIF ISIN-to-LEI mapping file (exact ISIN match)",
    "state": "sourced",
    "second_read_by": "no second independent LEI source for this row"
   }
  }
 }
};
export const IW_CAPTURE = {
 "captured": "2026-10-22T23:38:38Z",
 "door": "https://mcp.issuerwire.ai/mcp",
 "request": {
  "tool": "get_row",
  "arguments": {
   "id": "83f95500ddc7c5015d9320747ebe025f"
  }
 },
 "response": {
  "row": {
   "id": "83f95500ddc7c5015d9320747ebe025f",
   "issuer_key": "uk:ch:04366849",
   "type": "filing",
   "date": "2026-10-21",
   "title": "Transaction in Own Shares"
  },
  "notice": "Artificial intelligence (AI) makes mistakes; Issuerwire reads filings, it does not vouch for issuers. Nothing here is investment advice.",
  "payment_required": {
   "x402Version": 2,
   "resource": {
    "url": "https://mcp.issuerwire.ai/mcp",
    "description": "AgentMarketNews.ai — one signed news row, or the signed delta for an issuer since your last read, with the source page on every row (US, UK, Canada). One cent inside the call.",
    "mimeType": "application/json"
   },
   "accepts": [
    {
     "scheme": "exact",
     "network": "eip155:8453",
     "amount": "10000",
     "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
     "maxTimeoutSeconds": 60,
     "extra": {
      "assetTransferMethod": "eip3009",
      "name": "USD Coin",
      "version": "2"
     }
    },
    {
     "scheme": "exact",
     "network": "eip155:8453",
     "amount": "10000",
     "asset": "0xB2000000000000000000002fEb517dFeC7415344",
     "maxTimeoutSeconds": 60,
     "extra": {
      "assetTransferMethod": "permit2",
      "name": "OpenUSD",
      "version": "1",
      "eip2612GasSponsoring": true
     }
    }
   ],
   "extensions": {},
   "how": "retry this call with a PAYMENT-SIGNATURE header (x402 v2) against these terms; the receive address is in the 402 payload on https://mcp.issuerwire.ai/api",
   "paid_door": "https://x402.a2a-amn.ai/mcp"
  }
 }
};
