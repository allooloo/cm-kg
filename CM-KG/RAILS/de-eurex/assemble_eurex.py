"""Step 2 — the Eurex reference-data door records for the Germany node (CEO go, 2026-09-11). Pond-native: reads every drop under POND\\de-cm-kg\\eurex\\
(newest wins per product) and writes, into a new versioned drop POND\\de-cm-kg\\assembled\\<date>\\:
  de-ref-records.jsonl  one door record per Eurex product, exchange code EUREX, key de-cm-kg/EUREX/<Product>; every identity field carries the source
                        URL (endpoint + query + product filter), the read-by label and State sourced; trading hours and TES profiles ride on the
                        product record; contracts are counted and summarised (master contracts, first / last expiration) — the contract rows stay in
                        the drop; the underlying's Xetra record is linked when the underlying ISIN is on the de-issuers roster
  de-ref-events.jsonl   one event per expiration (event_type contract_expiration, dated on the expiration date, last trading date in Detail)
  de-eurex.xlsx         the human mirror (Products, Trading hours, TES profiles, Expirations, Contracts summary, Method) — copied beside the issuers
                        workbook as CM-KG\\REFERENCE\\de-eurex.xlsx (new file, nothing overwritten)
No price is carried: SettlementPrices is never queried and price-shaped fields were dropped at fetch. The Xetra Regulated Market / Scale segment flag
is not in this API either: that column on de-issuers stays blank with its reason."""
import json, os, re, sys, datetime, shutil
from collections import Counter, defaultdict
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
import pond
NODE = 'de-cm-kg'; TODAY = datetime.date.today().isoformat(); URL = 'https://api.developer.deutsche-boerse.com/eurex-prod-graphql/'
READ_BY = 'Eurex Reference Data API (Deutsche Börse developer portal, GraphQL, app allooloo-cm-kg)'
PORTAL = 'https://developer.deutsche-boerse.com/'
def rows_of(fn, key):
    return pond.read_jsonl_all(NODE, 'eurex', fn, key=key)
def meta_of(fn):
    p = pond.latest(NODE, 'eurex', fn); return json.load(open(p)) if p else {}
products = rows_of('ProductInfos.jsonl', 'Product'); M = {q: meta_of(f'{q}.meta.json') for q in ('ProductInfos', 'TradingHours', 'TESProfiles', 'Expirations', 'Contracts')}
hours = defaultdict(list)
for h in pond.read_jsonl_all(NODE, 'eurex', 'TradingHours.jsonl'): hours[h['Product']].append(h)
tes = defaultdict(list)
for t in pond.read_jsonl_all(NODE, 'eurex', 'TESProfiles.jsonl'): tes[t['Product']].append(t)
exps = defaultdict(list); seen_exp = set()
for e in pond.read_jsonl_all(NODE, 'eurex', 'Expirations.jsonl'):
    k = (e['Product'], e.get('MasterContract'), e.get('ExpirationDate'))
    if k in seen_exp: continue
    seen_exp.add(k); exps[e['Product']].append(e)
contracts = defaultdict(lambda: {'n': 0, 'calls': 0, 'puts': 0, 'futures': 0, 'masters': set(), 'first': None, 'last': None, 'isins': 0})
seen_c = set()
for c in pond.read_jsonl_all(NODE, 'eurex', 'Contracts.jsonl'):
    k = c.get('ContractID') or (c['Product'], c.get('Contract'), c.get('Strike'), c.get('CallPut'))
    if k in seen_c: continue
    seen_c.add(k); s = contracts[c['Product']]; s['n'] += 1
    if c.get('CallPut') == 'C': s['calls'] += 1
    elif c.get('CallPut') == 'P': s['puts'] += 1
    else: s['futures'] += 1
    if c.get('MasterContract'): s['masters'].add(c['MasterContract'])
    if c.get('ISIN'): s['isins'] += 1
    d = c.get('ExpirationDate')
    if d: s['first'] = d if not s['first'] or d < s['first'] else s['first']; s['last'] = d if not s['last'] or d > s['last'] else s['last']
# Xetra roster (latest assembled de-issuers): ISIN -> ticker, name; the link runs both ways (the loader adds the products to the issuer record)
xetra = {}
xp = pond.latest_assembled(NODE, 'de-issuers.xlsx')
if xp:
    wb0 = openpyxl.load_workbook(xp, read_only=True); ws0 = wb0['Xetra']; it = ws0.iter_rows(values_only=True); hdr = next(it)
    for r in it:
        d = dict(zip(hdr, r))
        if d.get('ISIN') and d.get('Symbol'): xetra[d['ISIN']] = {'ticker': d['Symbol'], 'name': d.get('Legal name') or ''}
def src(query, product): return f'{URL}#{query}?Product={product}'
def f(value, query, product, state='sourced'):
    return {'value': value, 'source_url': src(query, product), 'read_by': READ_BY, 'state': state}
records = []; events = []; linked = 0
for p in sorted(products, key=lambda x: x['Product']):
    P = p['Product']; ident = {}
    ident['name'] = f(p.get('Name'), 'ProductInfos', P); ident['ticker'] = f(P, 'ProductInfos', P); ident['exchange'] = f('Eurex', 'ProductInfos', P); ident['product_id'] = f(p.get('ProductID'), 'ProductInfos', P)
    for k, col in (('isin', 'ProductISIN'), ('product_line', 'ProductLine'), ('product_type', 'ProductType'), ('product_type_code', 'ProductTypeCode'), ('tsl_product_group', 'TSLProductGroup'), ('currency', 'Currency'), ('price_notation', 'PriceNotation'), ('us_approval', 'USapproval'), ('pre_trade_limits', 'PreTradeLimits'), ('settlement_type', 'SettlementType'), ('contract_size', 'ContractSize'), ('tick_size', 'TickSize'), ('tick_value', 'TickValue'), ('partition', 'Partition'), ('max_order_qty', 'MaxOrderQty'), ('max_tes_qty', 'MaxTESQty'), ('position_limit', 'PositionLimit'), ('allow_mmp', 'AllowMMP'), ('underlying', 'Underlying'), ('underlying_isin', 'UnderlyingISIN'), ('underlying_name', 'UnderlyingName'), ('equity_isin', 'EquityISIN'), ('underlying_category', 'UnderlyingCategory')):
        if p.get(col) not in (None, ''): ident[k] = f(p[col], 'ProductInfos', P)
    ident['security_type'] = f('Derivative (Eurex ' + (p.get('ProductLine') or '').lower() + ')', 'ProductInfos', P)
    u = p.get('UnderlyingISIN') or p.get('EquityISIN')
    if u and u in xetra: ident['underlying_cmr'] = f(f"de-cm-kg/XETRA/{xetra[u]['ticker']}", 'ProductInfos', P); ident['underlying_cmr']['note'] = 'underlying ISIN on the de-issuers Xetra roster'; linked += 1
    hs = hours.get(P) or []
    if hs:
        h = hs[0]; ident['trading_hours'] = f({k2: h.get(k2) for k2 in ('StartContinuousTrading', 'EndOpeningAuction', 'EndContinuousTrading', 'EndClosingAuction', 'StartTES', 'EndTES', 'LTDBook', 'LTDTES')}, 'TradingHours', P)
    ts = tes.get(P) or []
    if ts: ident['tes_profiles'] = f([{k2: t.get(k2) for k2 in ('InstrumentType', 'TESType', 'PriceValidationRule', 'AllowAutoApproval', 'AllowBroker', 'MaxTrader', 'MinLotSize', 'MinLotSizeNonPrimary', 'NonDisclosureLimit', 'MinExpiryRange', 'LegPriceEntry', 'TESminStep')} for t in ts], 'TESProfiles', P)
    ex = sorted(exps.get(P) or [], key=lambda e: e.get('ExpirationDate') or '')
    ident['expirations'] = f({'count': len(ex), 'first': ex[0]['ExpirationDate'] if ex else None, 'last': ex[-1]['ExpirationDate'] if ex else None}, 'Expirations', P)
    cs = contracts.get(P)
    if cs: ident['contracts'] = f({'count': cs['n'], 'futures': cs['futures'], 'calls': cs['calls'], 'puts': cs['puts'], 'master_contracts': sorted(cs['masters']), 'with_isin': cs['isins'], 'first_expiration': cs['first'], 'last_expiration': cs['last']}, 'Contracts', P)
    aliases = []
    if p.get('Name'): aliases.append({'value': p['Name'], 'source_url': src('ProductInfos', P), 'read_by': READ_BY})
    if p.get('UnderlyingName'): aliases.append({'value': f"{p['UnderlyingName']} ({p.get('ProductLine', '').lower()})", 'source_url': src('ProductInfos', P), 'read_by': READ_BY})
    gaps = []
    if not hs: gaps.append({'field': 'trading_hours', 'reason': 'no TradingHours row for this product in the API'})
    if not ts: gaps.append({'field': 'tes_profiles', 'reason': 'no TESProfiles row for this product in the API'})
    if not ex: gaps.append({'field': 'expirations', 'reason': 'no Expirations row for this product in the API'})
    if not cs: gaps.append({'field': 'contracts', 'reason': 'no Contracts row for this product in the API' if M['Contracts'].get('done') else 'Contracts table not yet complete at assembly'})
    gaps.append({'field': 'xetra_segment', 'reason': 'the Regulated Market / Scale flag is not in this API (standing note on de-issuers)'})
    records.append({'cmr': f'de-cm-kg/EUREX/{P}', 'node': NODE, 'exchange': 'EUREX', 'ticker': P, 'name': p.get('Name') or P, 'isin': p.get('ProductISIN') or '', 'lei': '', 'as_of': M['ProductInfos'].get('date') or TODAY, 'version': 1, 'kind': 'reference (derivative product)', 'identity': ident, 'aliases': aliases, 'gaps': gaps,
                    'sources': [{'query': q, 'url': URL, 'data_date': M[q].get('date'), 'rows': M[q].get('rows'), 'read_by': READ_BY} for q in M if M[q]], 'portal': PORTAL})
    for e in ex:
        events.append({'exchange': 'EUREX', 'ticker': P, 'isin': p.get('ProductISIN') or '', 'lei': '', 'issuer': p.get('Name') or P, 'event_type': 'contract_expiration', 'date': e['ExpirationDate'], 'title': f"Expiration {e.get('MasterContract') or ''} — {p.get('Name') or P}", 'category': p.get('ProductLine') or '', 'reference': str(e.get('ExpirationIndex') or ''), 'language': '', 'wire': 'Eurex', 'source': 'Eurex Reference Data API — Expirations', 'url': src('Expirations', P), 'read_by': READ_BY, 'detail': f"last trading date {e.get('LastTradingDate')}; contract date {e.get('ContractDate')}; month week {e.get('MonthWeek')}; weekday {e.get('Weekday')}; LTD offset {e.get('LTDOffset')}", 'state': 'sourced', 'as_of': M['Expirations'].get('date') or TODAY, 'node': NODE, 'width': 'reference'})
outdir = pond.assembled(NODE)
with open(os.path.join(outdir, 'de-ref-records.jsonl'), 'w', encoding='utf-8') as fo:
    for r in records: fo.write(json.dumps(r, ensure_ascii=False) + '\n')
with open(os.path.join(outdir, 'de-ref-events.jsonl'), 'w', encoding='utf-8') as fo:
    for e in events: fo.write(json.dumps(e, ensure_ascii=False) + '\n')
# workbook
ARIAL = Font(name='Arial', size=10); BOLD = Font(name='Arial', size=10, bold=True); HFILL = PatternFill('solid', fgColor='DDE4EE'); CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
wb = Workbook(); wb.remove(wb.active)
def sheet(name, cols, rows, widths=None):
    ws = wb.create_sheet(name); ws.append(cols)
    for c in ws[1]: c.font = BOLD; c.fill = HFILL; c.alignment = Alignment(wrap_text=True, vertical='top')
    for r in rows: ws.append([CTRL.sub('', v) if isinstance(v, str) else (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for v in r])
    for row in ws.iter_rows(min_row=2):
        for c in row: c.font = ARIAL
    ws.freeze_panes = 'A2'; ws.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{max(len(rows) + 1, 2)}'
    for i, w in enumerate(widths or [14] * len(cols), 1): ws.column_dimensions[get_column_letter(i)].width = w
    return ws
PC = ['Product', 'Name', 'Product ISIN', 'Product line', 'Product type', 'Type code', 'TSL group', 'Currency', 'Settlement type', 'Contract size', 'Tick size', 'Tick value', 'Underlying', 'Underlying ISIN', 'Underlying name', 'Equity ISIN', 'Underlying category', 'Xetra record (de-cm-kg)', 'Expirations', 'Contracts', 'TES profiles', 'Source', 'Read by', 'State', 'Data date']
prow = []
for r in records:
    i = r['identity']; g = lambda k: (i.get(k) or {}).get('value')
    prow.append([r['ticker'], r['name'], g('isin'), g('product_line'), g('product_type'), g('product_type_code'), g('tsl_product_group'), g('currency'), g('settlement_type'), g('contract_size'), g('tick_size'), g('tick_value'), g('underlying'), g('underlying_isin'), g('underlying_name'), g('equity_isin'), g('underlying_category'), g('underlying_cmr'), (g('expirations') or {}).get('count'), (g('contracts') or {}).get('count'), len(g('tes_profiles') or []), src('ProductInfos', r['ticker']), READ_BY, 'sourced', r['as_of']])
sheet('Products', PC, prow, [10, 34, 16, 12, 24, 10, 10, 9, 12, 12, 10, 10, 12, 16, 30, 16, 18, 24, 11, 11, 11, 60, 40, 9, 11])
HC = ['Product', 'Start continuous trading', 'End opening auction', 'End continuous trading', 'End closing auction', 'Start TES', 'End TES', 'LTD book', 'LTD TES', 'Source', 'Read by']
sheet('Trading hours', HC, [[h['Product'], h.get('StartContinuousTrading'), h.get('EndOpeningAuction'), h.get('EndContinuousTrading'), h.get('EndClosingAuction'), h.get('StartTES'), h.get('EndTES'), h.get('LTDBook'), h.get('LTDTES'), src('TradingHours', h['Product']), READ_BY] for P in sorted(hours) for h in hours[P]], [10] + [14] * 8 + [60, 40])
TC = ['Product', 'Instrument type', 'TES type', 'Price validation rule', 'Auto approval', 'Broker', 'Max trader', 'Min lot size', 'Min lot size non-primary', 'Non-disclosure limit', 'Min expiry range', 'Leg price entry', 'TES min step', 'Source', 'Read by']
sheet('TES profiles', TC, [[t['Product'], t.get('InstrumentType'), t.get('TESType'), t.get('PriceValidationRule'), t.get('AllowAutoApproval'), t.get('AllowBroker'), t.get('MaxTrader'), t.get('MinLotSize'), t.get('MinLotSizeNonPrimary'), t.get('NonDisclosureLimit'), t.get('MinExpiryRange'), t.get('LegPriceEntry'), t.get('TESminStep'), src('TESProfiles', t['Product']), READ_BY] for P in sorted(tes) for t in tes[P]], [10] + [14] * 12 + [60, 40])
EC = ['Product', 'Master contract', 'Expiration date', 'Last trading date', 'Contract date', 'Month week', 'Weekday', 'Days to expiration', 'LTD offset', 'Source', 'Read by']
sheet('Expirations', EC, [[e['Product'], e.get('MasterContract'), e.get('ExpirationDate'), e.get('LastTradingDate'), e.get('ContractDate'), e.get('MonthWeek'), e.get('Weekday'), e.get('DaysToExpiration'), e.get('LTDOffset'), src('Expirations', e['Product']), READ_BY] for P in sorted(exps) for e in sorted(exps[P], key=lambda x: x.get('ExpirationDate') or '')], [10, 14, 14, 14, 14, 10, 10, 10, 10, 60, 40])
CC = ['Product', 'Contracts', 'Futures', 'Calls', 'Puts', 'Master contracts', 'With ISIN', 'First expiration', 'Last expiration', 'Source', 'Read by']
sheet('Contracts summary', CC, [[P, s['n'], s['futures'], s['calls'], s['puts'], ', '.join(sorted(s['masters']))[:2000], s['isins'], s['first'], s['last'], src('Contracts', P), READ_BY] for P, s in sorted(contracts.items())], [10, 10, 10, 10, 10, 60, 10, 14, 14, 60, 40])
mt = wb.create_sheet('Method'); mt.append(['Item', 'Detail'])
for c in mt[1]: c.font = BOLD; c.fill = HFILL
METHOD = [('Order', f'Deutsche Börse door on the Germany node (CEO go, Sept 11 2026): Eurex derivatives reference data attached to de-cm-kg as a sourced reference-data door. Assembled {TODAY}. Fly by wire; sourced or blank; pond-native.'),
          ('Source', f'{READ_BY}. Endpoint {URL}, header X-DBP-APIKEY from AGENT KEYS\\deutsche-boerse.txt (never printed). Queries read: ProductInfos ({M["ProductInfos"].get("rows")} rows, data date {M["ProductInfos"].get("date")}), TradingHours ({M["TradingHours"].get("rows")}, {M["TradingHours"].get("date")}), TESProfiles ({M["TESProfiles"].get("rows")}, {M["TESProfiles"].get("date")}), Expirations ({M["Expirations"].get("rows")}, {M["Expirations"].get("date")}), Contracts ({M["Contracts"].get("rows")}, {M["Contracts"].get("date")}{"" if M["Contracts"].get("done") else " — table still loading at assembly"}). Pages of 1,000 rows by cursor.'),
          ('Not read', 'SettlementPrices (prices are never carried on CM-KG); TickRules, VendorCodes, Holidays, DeliverableBonds, Changelog, Enlight, EnlightResponders, FlexibleContracts (outside the order). Price-shaped fields on the in-scope types dropped at fetch: PreviousDaySettlementPrice, OptionsDelta, MaxPrice.'),
          ('Door shape', 'One record per Eurex product, key de-cm-kg/EUREX/<Product>; the same five MCP tools as every node door. Expirations are events (contract_expiration, dated on the expiration date). Contracts are counted and summarised on the record; the full contract rows stay in the pond drop. When the underlying ISIN sits on the Xetra roster the record carries underlying_cmr and the issuer record lists its Eurex products.'),
          ('Xetra segment', 'This API does not carry the Xetra Regulated Market / Scale segment flag; that column on de-issuers stays blank with its reason. No paid Deutsche Börse product (A7, Cloud Stream, Data Shop) is subscribed.'),
          ('State', 'sourced = read from the API with the query URL as source; nothing inferred.')]
for a, b in METHOD: mt.append([a, b])
for row in mt.iter_rows(min_row=2):
    for c in row: c.font = ARIAL; c.alignment = Alignment(wrap_text=True, vertical='top')
mt.column_dimensions['A'].width = 24; mt.column_dimensions['B'].width = 150
out = os.path.join(outdir, 'de-eurex.xlsx'); wb.save(out)
ref = r'C:\ALLOOLOO\CM-KG\REFERENCE'; os.makedirs(ref, exist_ok=True); shutil.copy(out, os.path.join(ref, 'de-eurex.xlsx'))
print('saved', out, '| records', len(records), 'events', len(events), 'linked to Xetra', linked, 'products with contracts', len(contracts), 'contracts rows', sum(s['n'] for s in contracts.values()))
print(Counter((r['identity'].get('product_line') or {}).get('value') for r in records), Counter((r['identity'].get('underlying_category') or {}).get('value') for r in records).most_common(6))
