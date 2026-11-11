r"""au01_kit.py — AUDIT-01 F1 (2026-11-11): an A2A Agent Card must carry name, version, description, supportedInterfaces and a non-empty skills[].
The stack-pages cards are reference surfaces (they serve no tools), so they get only what is missing, true to the host:
  supportedInterfaces  the page itself (HTTP+JSON, as the member cards of site03a name it), plus the MCP door the card already names ('door'), if any
  skills               one skill: read the page and its llms.txt (and the descriptors or door the card already names)
A card that already carries either field keeps it. Used by stack_pages.py card() (and cpg02.py through it) and by the one-off bundle patch."""
def complete(c):
    url = c.get('url') or ''; door = c.get('door') if isinstance(c.get('door'), str) else None
    if not c.get('supportedInterfaces'):
        si = [{'url': url, 'protocolBinding': 'HTTP+JSON', 'protocolVersion': '1.0'}]
        if door: si.append({'url': door, 'protocolBinding': 'HTTP+JSON', 'transport': 'streamable-http', 'description': 'the MCP door this page names'})
        c['supportedInterfaces'] = si
    if not c.get('skills'):
        d = str(c.get('description') or c.get('name') or '').strip(); first = d.split('. ')[0].rstrip('.')[:300]
        more = []
        if isinstance(c.get('descriptors'), list) and c['descriptors']: more.append('its descriptors: ' + ', '.join(c['descriptors']))
        if isinstance(c.get('descriptor'), str): more.append('its descriptor: ' + c['descriptor'])
        if door: more.append('the door it names: ' + door)
        c['skills'] = [{'id': 'read', 'name': 'Read ' + str(c.get('name') or url), 'description': (first + '. ' if first else '') + f'The page is {url}; its text for agents is {url}llms.txt' + ('; ' + '; '.join(more) if more else '') + '.',
                        'tags': ['reference', 'read'], 'examples': [url + 'llms.txt']}]
    return c
