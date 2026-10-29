r"""ZONES-03 — shared-text pass 2: a 'What it leaves out' section on each of the seven pages, in its own words."""
p = r'C:\ALLOOLOO\CM-KG\ESTATE\worker\zones03.js'
s = open(p, encoding='utf-8').read()
OUT = {
 'replay': ['Restated figures: Replay shows the record as filed then, and a later correction stays in the later version.', 'Prices and quotes of the day; the record carries none.', 'Anything that was not on the public record on that date, however soon it appeared after.'],
 'bench': ['Opinions, forecasts and price questions: every item has one answer a public page settles.', 'The scoring of any particular vendor; the set measures, it does not rank.'],
 'review': ['A league table of individual issuers: the report speaks for a market and a year.', 'Any judgement of whether a disclosure was good, only when and how many.', 'Prices, volumes and market data.'],
 'score': ['A view to buy, sell or hold; a cadence number is not advice.', 'Price, volume and the contents of the results themselves — only their dates.'],
 'timeline': ['Summaries written by us: each line keeps the title its source gave.', 'Commentary, rumour and the press’s own stories about the company.', 'Market prices around each date.'],
 'events': ['Share-capital actions such as splits and dividends, unless the source itself typed them as an event.', 'Deal rumours and reported talks: a change enters when a register or an exchange records it.'],
 'cleanroom': ['Live records and tonight’s sweep: those are read call by call on the doors.', 'Any personal data beyond what an issuer itself filed on the public record.'],
}
n = 0
for k, items in OUT.items():
    a = s.index(f'    {k}: {{'); b = s.index('${payBlock(', a)
    seg = s[a:b]
    if 'What it leaves out' in seg: continue
    ins = "${who('What it leaves out', " + repr(items).replace("\\'", "’") + ")}\n"
    s = s[:b] + ins + s[b:]; n += 1
open(p, 'w', encoding='utf-8').write(s)
print('sections added', n)
