r"""IW-01 — the hk drop of market date 2026-10-26 explained (window roll) and released once: door-release/2026-10-26.json in the hk store, read by door_gate.py
(0.35.14+). The note carries the held build's counts (the floor a release build must meet) and the classification file. Usage: python -X utf8 -I hk_release.py"""
import json, os, glob, subprocess, datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
os.environ['AZURE_CONFIG_DIR'] = r'C:\ALLOOLOO\.azure'; HERE = os.path.dirname(os.path.abspath(__file__))
cls = json.load(open(sorted(glob.glob(os.path.join(HERE, 'hk-411-*.json')))[-1], encoding='utf-8'))
assert list(cls['left_by_class']) and all(k.startswith('window roll') for k in cls['left_by_class']) and cls['net'] == -411, 'not a pure window roll: no release'
note = {'node': 'hk-cm-kg', 'market_date': '2026-10-26', 'reason': 'window roll', 'records_min': 2796, 'events_min': 163011,
        'explained': {'events_left': cls['left'], 'left_by_class': cls['left_by_class'], 'left_days': cls['left_days'], 'events_came': cls['came'], 'net': cls['net'],
                      'window_first_day_before': cls['wire_first_day'], 'window_first_day_after': cls['new_first_day'], 'duplicates_collapsed': 0, 'other': 0},
        'explained_by': 'IW-01 RAILS\doors-03\hk_events_diff.py (assembled 2026-10-25 vs 2026-10-26)', 'released_by': 'IW-01, CEO order 2026-10-26: if window roll, release the door',
        'written_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
key = subprocess.run(['az', 'storage', 'account', 'keys', 'list', '-g', 'allooloo-cmkg-eastasia', '-n', 'allooloocmkghkpond', '--query', '[0].value', '-o', 'tsv'], capture_output=True, text=True, shell=True).stdout.strip()
c = BlobServiceClient('https://allooloocmkghkpond.blob.core.windows.net', credential=key).get_container_client('pond')
c.upload_blob('door-release/2026-10-26.json', json.dumps(note, indent=1).encode(), overwrite=False, content_settings=ContentSettings(content_type='application/json'))
print('written door-release/2026-10-26.json', json.dumps(note['explained']))
