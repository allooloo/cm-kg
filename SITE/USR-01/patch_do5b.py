import pathlib
p = pathlib.Path(r'C:\ALLOOLOO\CM-KG\ESTATE\worker\do5.js'); s = p.read_text(encoding='utf-8')
if 'USR-01b' in s: raise SystemExit('already patched')
def rep(o, n):
    global s
    assert s.count(o) == 1, (s.count(o), o[:70]); s = s.replace(o, n)
rep("<td>${a(cardOf(cc), 'card')}</td><td>${n.live ?", "<td>${a(cardOf(cc), 'card')}</td><td>${esc((venueOf(cc) || {}).coverage || 'not on the market file')}</td><td>${n.live ?")   # USR-01b
rep('<th scope="col">Card</th><th scope="col">Records · events · as of</th>', '<th scope="col">Card</th><th scope="col">Coverage</th><th scope="col">Records · events · as of</th>')
rep("door: doorOf(cc), agent_card: cardOf(cc), live: !!(live[`${cc}-cm-kg`] || {}).live,", "door: doorOf(cc), agent_card: cardOf(cc), coverage: (venueOf(cc) || {}).coverage || null, venues: venueOf(cc), live: !!(live[`${cc}-cm-kg`] || {}).live,")
s = s.replace("const venueOf = cc =>", "// USR-01b: the European doors page (eu-cm-kg.ai) carries each market's Coverage line and venue block: the node page of the markets with no zone of their own\nconst venueOf = cc =>", 1)
p.write_text(s, encoding='utf-8'); print('patched')
