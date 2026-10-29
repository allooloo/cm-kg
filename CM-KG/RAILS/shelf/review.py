r"""SHELF-01 step 5 (Review) — the per market-year disclosure report from the sealed layer: counts by type, latency distribution, auditor concentration
(share by firm), listings and delistings, silent issuers. Numbers and shares only — no opinion words, no ratings.
Built once per sealed market-year (ledger complete, manifest verified), rebuilt only on a manifest change. Every figure is read from the sealed rows;
a measure the rows do not state (no period end, no auditor named) is printed as 'not stated in the sealed rows' with its count, never estimated.
Writes review-<cc>-<year>.json (signed) to the apex store shelf/review/ (served per read at the review door) and review-<cc>-<year>.pdf (the house
template; figures from the JSON) to shelf-private/review/ (per licence).
Usage: python -X utf8 -I review.py <cc> <year> [--dry]"""
import os, sys, json, re, datetime, hashlib, statistics, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'isin-dis'), os.path.join(HERE, '..', 'backfill')]
from score import pe_of
from lifecycle import kind_of
def build(cc, year, rows, man, mn, issuers_listed):
    by_type = collections.Counter(r.get('event_type') for r in rows)
    lat = sorted(d for d in ((datetime.date.fromisoformat(r['date'][:10]) - datetime.date.fromisoformat(pe_of(r))).days for r in rows if pe_of(r)) if 0 <= d <= 400)
    q = lambda p: lat[min(len(lat) - 1, int(round(p * (len(lat) - 1))))] if lat else None
    aud = collections.Counter(r['auditor_named'] for r in rows if r.get('auditor_named'))
    life = collections.defaultdict(list)
    for r in rows:
        t = kind_of(cc, r)
        if t in ('listing', 'delisting'): life[t].append({'date': r['date'][:10], 'issuer': r.get('issuer'), 'ticker': r.get('ticker'), 'title': r.get('title'), 'url': r.get('url')})
    with_rows = {(r.get('exchange'), r.get('ticker')) for r in rows}
    silent = sorted(k for k in issuers_listed if k not in with_rows)
    per_iss = collections.Counter((r.get('exchange'), r.get('ticker')) for r in rows); top = per_iss.most_common()
    tot = sum(per_iss.values()); top10 = sum(n for _, n in top[:10])
    return {'review': f'review-{cc}-{year}', 'market': cc, 'year': year, 'manifest': {'name': mn, 'hash_tree_root': man['hash_tree_root'], 'rows': man['rows'], 'signature': man['signature']},
            'counts_by_type': dict(by_type.most_common()), 'rows': len(rows), 'issuers_with_rows': len(with_rows),
            'volume_concentration': {'top10_issuers_share_pct': round(100.0 * top10 / tot, 1) if tot else None, 'top10': [{'exchange': k[0], 'ticker': k[1], 'rows': n} for k, n in top[:10]]},
            'latency_days': ({'filings_with_period_end': len(lat), 'median': statistics.median(lat), 'p25': q(0.25), 'p75': q(0.75), 'p90': q(0.9), 'max': lat[-1]} if lat else
                             {'filings_with_period_end': 0, 'note': 'not stated in the sealed rows (no filing in this year states its period end)'}),
            'auditor_concentration': ({'annual_reports_naming_auditor': sum(aud.values()), 'share_by_firm_pct': {f: round(100.0 * n / sum(aud.values()), 1) for f, n in aud.most_common()}} if aud else
                                      {'annual_reports_naming_auditor': 0, 'note': 'not stated in the sealed rows (no row names an auditor)'}),
            'listings': {'count': len(life['listing']), 'lines': life['listing']}, 'delistings': {'count': len(life['delisting']), 'lines': life['delisting']},
            'silent_issuers': {'count': len(silent), 'of_listed': len(issuers_listed), 'note': 'issuers on the market list today with no line in the sealed year (the list is today\'s, so an issuer listed after the year counts here)'},
            'built_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'method': 'every figure from the sealed rows of the market-year (manifest above); numbers and shares only'}
def pdf(doc, path):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    st = getSampleStyleSheet(); H = st['Heading2']; B = st['BodyText']; story = []
    story += [Paragraph(f"Allooloo · Review · {doc['market'].upper()} {doc['year']}", st['Title']), Paragraph(f"Disclosure report from the sealed market-year. Manifest root {doc['manifest']['hash_tree_root'][:16]}… · {doc['rows']:,} rows · {doc['issuers_with_rows']:,} issuers with rows.", B), Spacer(1, 8)]
    def tbl(rows, head):
        t = Table([head] + rows, hAlign='LEFT'); t.setStyle(TableStyle([('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'), ('GRID', (0, 0), (-1, -1), 0.25, colors.grey), ('FONTSIZE', (0, 0), (-1, -1), 8)])); return t
    story += [Paragraph('1 Counts by type', H), tbl([[k, f'{v:,}'] for k, v in doc['counts_by_type'].items()], ['type', 'lines'])]
    lt = doc['latency_days']; story += [Paragraph('2 Latency (days from period end to filing)', H), Paragraph(lt.get('note') or f"{lt['filings_with_period_end']:,} filings state a period end · median {lt['median']} · p25 {lt['p25']} · p75 {lt['p75']} · p90 {lt['p90']} · max {lt['max']}", B)]
    ac = doc['auditor_concentration']; story += [Paragraph('3 Auditor concentration (share by firm)', H), Paragraph(ac['note'], B) if ac.get('note') else tbl([[f, f'{p}%'] for f, p in list(ac['share_by_firm_pct'].items())[:15]], ['firm', 'share of annual reports naming an auditor'])]
    story += [Paragraph('4 Listings and delistings', H), Paragraph(f"Listings {doc['listings']['count']:,} · delistings {doc['delistings']['count']:,} (as the register's own lines type them).", B)]
    vc = doc['volume_concentration']; story += [Paragraph('5 Volume concentration and silent issuers', H), Paragraph(f"Top ten issuers carry {vc['top10_issuers_share_pct']}% of the year's lines. Silent: {doc['silent_issuers']['count']:,} of {doc['silent_issuers']['of_listed']:,} issuers on today's list have no line in the year.", B)]
    story += [Spacer(1, 12), Paragraph('Figures are read from the signed JSON of this review; numbers and shares only. Allooloo Technologies Corp. · allooloo.ai', B)]
    SimpleDocTemplate(path, pagesize=A4, title=doc['review']).build(story)
def main():
    a = sys.argv[1:]; cc, year, dry = a[0], int(a[1]), '--dry' in a
    import store, backfill as BF
    from replay_index import newest_manifest, year_rows
    from bench import apex_cont
    c = store.cont(cc); led = BF.order_get(cc)
    if not (led and led.get('complete')): print(f'{cc}: ledger entry not complete — no review'); return
    mn = newest_manifest(c, year); man = store.bj(c, mn); ok, rows = year_rows(c, man)   # streamed and checked (SHELF-01 2026-10-27, us scale)
    if not ok: print(f'{cc} {year}: manifest does not verify — no review'); return
    ix = store.bj(c, 'door/index.json'); listed = {(k.split('/')[1], k.split('/', 2)[2]) for k in ix.get('keys') or []}
    doc = BF.sign(build(cc, year, rows, man, mn, listed))
    lp = os.path.join(os.environ.get('TEMP', '/tmp'), f'review-{cc}-{year}.pdf'); pdf(doc, lp)
    json.dump(doc, open(os.path.join(os.environ.get('TEMP', '/tmp'), f'review-{cc}-{year}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"review-{cc}-{year}: {doc['rows']:,} rows · types {len(doc['counts_by_type'])} · latency n={doc['latency_days']['filings_with_period_end']} · auditors n={doc['auditor_concentration']['annual_reports_naming_auditor']} · listings {doc['listings']['count']} · delistings {doc['delistings']['count']} · silent {doc['silent_issuers']['count']}")
    if not dry:
        for cont, name, data in (('shelf', f'review/review-{cc}-{year}.json', json.dumps(doc, ensure_ascii=False).encode()), ('shelf-private', f'review/review-{cc}-{year}.pdf', open(lp, 'rb').read())):
            k = apex_cont(cont)
            try: k.create_container()
            except Exception: pass
            k.upload_blob(name, data, overwrite=True)
        print('published', f'shelf/review/review-{cc}-{year}.json', '· PDF held at', f'shelf-private/review/review-{cc}-{year}.pdf')
if __name__ == '__main__': main()
