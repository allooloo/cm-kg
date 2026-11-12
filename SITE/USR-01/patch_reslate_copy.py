r"""patch_reslate_copy.py — RESLATE-01 item 4: copy, text only. Wherever an estate surface says the record is re-slated nightly or "every night", the line
reads "every week, after the Friday close". Lines about things the weekly run now carries (the sweep, the halt read, the ark copy, the backfill, the
target-market re-fetch, the RADAR delta) move with it, because they are no longer nightly. Names ("Overnight Engineering", "Overnight OpsAgents") are
names, not schedule lines: untouched. Icons, scaffolding and layout untouched. A .pre-reslate01-2026-11-12 copy beside every file. Each pair must match
exactly once (or the count given), else the file is left as it was and named. Writes copy-changes.json (file, was, now). Usage: python -X utf8 -I patch_reslate_copy.py"""
import pathlib, shutil, json
W = pathlib.Path(r'C:\ALLOOLOO\CM-KG\ESTATE\worker'); F = 'every week, after the Friday close'; LOG = []
E = {
 'site.js': [("disclosures, signed every night", f"disclosures, signed {F}", 1), ("Re-slated every night by 14 Allooloo OpsAgents", f"Re-slated {F}, by 14 Allooloo OpsAgents", 2), ("disclosures · signed, every night", f"disclosures · signed, {F}", 1),
             ("The latest nightly cut, as of its market date", "The latest weekly cut, as of its market date", 1), ("Built every night by 14 Overnight OpsAgents", f"Built {F}, by 14 Overnight OpsAgents", 1),
             ("Every night, in every market, fourteen Allooloo OpsAgents", "Every week, after the Friday close, in every market, fourteen Allooloo OpsAgents", 1), ("swept after the Friday close, Canada daily:", "swept after the Friday close, Canada on the same schedule:", 1),
             ("re-slated every night by agents", f"re-slated {F}, by agents", 1)],
 'about-copy.js': [("The whole record is re-slated every night by our own OpsAgents", f"The whole record is re-slated {F}, by our own OpsAgents", 1), ("The record is never older than last night, in every time zone, every market, every day.", "The record is never older than the last Friday close, in every time zone, every market.", 1),
                   ("The record is re-slated nightly by our own OpsAgents", f"The record is re-slated {F}, by our own OpsAgents", 1), ("every night\\'s run makes the dataset", "every week\\'s run makes the dataset", 1)],
 'asof.js': [("Nightly: the OpsAgents re-slate the trading day;", "Every week, after the Friday close: the OpsAgents re-slate the trading week;", 1)],
 'doors027.js': [("the halt flag read nightly from", f"the halt flag read {F}, from", 1), ("the halt flag, read nightly from", f"the halt flag, read {F}, from", 1), ("Re-slated every night by 14 Allooloo OpsAgents", f"Re-slated {F}, by 14 Allooloo OpsAgents", 1),
                 ("and the last night the record reached its second cloud", "and the last run in which the record reached its second cloud", 1), ("reaches a second cloud the same night", "reaches a second cloud in the same weekly run", 1)],
 'zones02.js': [("markets, swept nightly;", f"markets, swept {F};", 1), ("as read on the most recent nightly sweep of its home market", "as read on the most recent weekly sweep of its home market", 1), ("It is the state of the public record tonight,", "It is the state of the public record as of the last Friday close,", 1),
                ("A nightly sweep per market at 02:00 local standard time rebuilds", "A weekly sweep per market, after its Friday close, rebuilds", 1), ("Live tonight:", "Live now:", 1), ("halt page, read nightly, with the time it was read", f"halt page, read {F}, with the time it was read", 1),
                ("What changed since last night:", "What changed since the last weekly sweep:", 1), ("by a nightly backfill run per market", "by a weekly backfill run per market", 1), ("on the night it lands", "in the run it lands", 1), ("copied nightly, put-only,", f"copied {F}, put-only,", 1),
                ("nightly close, with the market date they carry", "weekly close, with the market date they carry", 1), ("mirrored on the night they land", "mirrored in the run they land", 1), ("halts and releases each night,", "halts and releases each week,", 1),
                ("nightly close and before the desk opens", "weekly close and before the desk opens", 1), ("sweeps a long list every night", "sweeps a long list every week", 1), ("and the night’s copy sits under object lock", "and the week’s copy sits under object lock", 1)],
 'nodes.js': [("Sweep clock: nightly at 02:00 Hong Kong standard time (18:00 UTC), seven nights a week; Width 1 over a three-day window every night, Fill and Confirm on the rotation night.", "Sweep clock: every week, after the Friday close in Hong Kong; Width 1 over an eight-day window, then Fill and Confirm.", 1)],
 'nav02.js': [("OpsAgents on the fleet, nightly", "OpsAgents on the fleet, weekly", 1)],
 'tm-copy.js': [("are re-fetched nightly", f"are re-fetched {F}", 1)],
 'radar.js': [("Delta per market, night of ${esc(dl_.night)}", "Delta per market, run of ${esc(dl_.night)}", 1), ("landed last night", "landed in the last run", 1)],
}
for name, pairs in E.items():
    p = W / name; s = p.read_text(encoding='utf-8'); bad = [(o, s.count(o), k) for o, n, k in pairs if s.count(o) != k and s.count(n) == 0]
    done = all(s.count(o) == 0 for o, n, k in pairs)
    if done: print(name, 'already changed'); continue
    if bad: print(name, 'LEFT AS IT WAS — not matched:', [(o[:50], c, k) for o, c, k in bad]); LOG.append({'file': name, 'left': [o for o, c, k in bad]}); continue
    pre = W / (name.replace('.js', '.pre-reslate01-2026-11-12.js'))
    if not pre.exists(): shutil.copy2(p, pre)
    for o, n, k in pairs:
        if s.count(o): LOG.append({'file': name, 'was': o, 'now': n, 'times': s.count(o)}); s = s.replace(o, n)
    p.write_text(s, encoding='utf-8'); print(name, 'changed', len(pairs), 'lines')
json.dump(LOG, open(pathlib.Path(__file__).with_name('copy-changes.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False); print('lines changed', sum(x.get('times', 0) for x in LOG))
