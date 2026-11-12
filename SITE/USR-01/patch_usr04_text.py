import pathlib
p = pathlib.Path(r'C:\ALLOOLOO\CM-KG\ESTATE\worker\research.js'); s = p.read_text(encoding='utf-8')
for o, n in (("the page store ledger, list_nodes and the router counter, read at render", "the page store ledger, list_nodes and the receipt chain (the Record of Cleared Orders), read at render"),
             ("and the router's receipt counter</p>", "and the receipt chain (the Record of Cleared Orders)</p>"),
             ("'receipts written', 'get_research reads, receipted', 'key']", "'receipts written', 'get_research reads on the receipt chain', 'key']")):
    assert s.count(o) == 1, o; s = s.replace(o, n)
p.write_text(s, encoding='utf-8'); print('ok')
