"""Step 1 — Eurex derivatives reference data from the Deutsche Börse developer portal (app allooloo-cm-kg, API "Eurex-Data via GraphQL"), CEO go of
2026-09-11. Endpoint https://api.developer.deutsche-boerse.com/eurex-prod-graphql/ with the key from AGENT KEYS\\deutsche-boerse.txt (read in-process,
never printed). Scope by order: ProductInfos, Contracts, Expirations, TradingHours, TESProfiles. Not read: SettlementPrices (prices — never carried),
TickRules, VendorCodes, Holidays, DeliverableBonds, Changelog, Enlight, FlexibleContracts (outside the order). Price-shaped fields on the in-scope
types are dropped at fetch (PreviousDaySettlementPrice, OptionsDelta, MaxPrice). Every page is paginated by cursor and written to raw/<Query>.jsonl
(raw\\ = junction to the open pond drop POND\\de-cm-kg\\eurex\\<date>\\) with raw/<Query>.meta.json carrying the data date the API stamps, the row count
and the source URL. No paid Deutsche Börse product is touched (A7, Cloud Stream, Data Shop)."""
import json, os, sys, time, urllib.request, datetime
URL = 'https://api.developer.deutsche-boerse.com/eurex-prod-graphql/'
KEY = open(r'C:\ALLOOLOO\AGENT KEYS\deutsche-boerse.txt', encoding='utf-8').read().strip()
READ_BY = 'Eurex Reference Data API (Deutsche Börse developer portal, GraphQL, app allooloo-cm-kg)'
FIELDS = {
    'ProductInfos': 'ProductID Product Name ProductISIN ProductLine ProductType ProductTypeCode TSLProductGroup LiquidityClass Currency PriceNotation USapproval PreTradeLimits SettlementType ContractSize TickSize TickValue Partition MaxOrderQty MaxOrderValue MaxTESQty MaxFutureSpreadQty MaxMarketOrderQty PositionLimit VolaInterruptStaticPercentage AllowMMP Underlying UnderlyingISIN UnderlyingName EquityISIN UnderlyingCategory',
    'Contracts': 'ProductID Product ProductLine InstrumentID ContractID ISIN MasterContract Contract PrimaryContract ContractCycle CallPut Strike OriginalStrike SettlementType ExerciseStyle VersionNr GenerationNr ContractSize DeliverySize CashFraction CFI FirstTradingDate ContractDate ContractDateType LastTradingDate ExpirationDate FinalSettlementDate UnderlyingContract',
    'Expirations': 'ProductID Product MasterContract LastTradingDate ExpirationDate ExpDay ExpMonth ExpYear MonthWeek Weekday WeekNumber DaysToExpiration LTDOffset ContractDate ExpirationIndex',
    'TradingHours': 'ProductID Product StartContinuousTrading EndOpeningAuction EndContinuousTrading EndClosingAuction StartTES EndTES LTDBook LTDTES',
    'TESProfiles': 'ProductID Product InstrumentType TESType PriceValidationRule AllowAutoApproval AllowBroker MaxTrader MinLotSize MinLotSizeNonPrimary NonDisclosureLimit MinExpiryRange LegPriceEntry TESminStep'}
PAGE = int(os.environ.get('PAGE', '1000'))  # the API caps a page at 1,000 rows; larger asks answer Internal Server Error
def gql(query, variables=None, tries=5):
    body = json.dumps({'query': query, 'variables': variables or {}}).encode()
    for i in range(tries):
        req = urllib.request.Request(URL, data=body, headers={'X-DBP-APIKEY': KEY, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            r = urllib.request.urlopen(req, timeout=180); j = json.load(r)
            if j.get('errors'): raise RuntimeError(json.dumps(j['errors'])[:300])
            return j['data']
        except urllib.error.HTTPError as e:
            msg = e.read()[:300]
            if e.code in (429, 500, 502, 503, 504): time.sleep(5 * (i + 1)); continue
            raise RuntimeError(f'HTTP {e.code} {msg}')
        except RuntimeError: raise
        except Exception: time.sleep(3 * (i + 1))
    raise RuntimeError('exhausted')
def fetch(name, filt=None):
    fn = f'raw/{name}.jsonl'; meta_fn = f'raw/{name}.meta.json'
    meta = json.load(open(meta_fn)) if os.path.exists(meta_fn) else {'rows': 0, 'cursor': None, 'done': False}
    if meta.get('done'): print(name, 'already complete', meta['rows']); return meta
    out = open(fn, 'a', encoding='utf-8'); cursor = meta.get('cursor'); n = meta['rows']; pages = 0
    q = 'query($page: PaginationInput, $filter: %sFilter) { %s(page: $page, filter: $filter) { date pageInfo { hasNextPage endCursor } data { %s } } }' % (name, name, FIELDS[name])
    while True:
        page = {'first': PAGE}
        if cursor: page['after'] = cursor
        d = gql(q, {'page': page, 'filter': filt} if filt else {'page': page})[name]
        rows = d.get('data') or []
        for r in rows: out.write(json.dumps(r, ensure_ascii=False) + '\n')
        out.flush(); n += len(rows); pages += 1; meta.update({'rows': n, 'cursor': d['pageInfo'].get('endCursor'), 'date': d.get('date'), 'src': URL, 'query': name, 'read_by': READ_BY, 'fetched': datetime.date.today().isoformat(), 'page_size': PAGE})
        json.dump(meta, open(meta_fn, 'w'))
        if pages % 10 == 0: print(name, n, 'rows', flush=True)
        if not d['pageInfo'].get('hasNextPage') or not rows: break
        cursor = d['pageInfo']['endCursor']
    meta['done'] = True; json.dump(meta, open(meta_fn, 'w')); print(name, 'DONE rows', n, 'data date', meta.get('date'), flush=True); return meta
if __name__ == '__main__':
    os.makedirs('raw', exist_ok=True)
    for name in (sys.argv[1:] or ['ProductInfos', 'TradingHours', 'TESProfiles', 'Expirations', 'Contracts']): fetch(name)
