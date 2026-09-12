"""GLEIF golden copy (LEI-CDF level 1, full file, CSV) into the pond drop POND\estate\gleif-golden\<date>\ - one download a build day, shared by every
node rail that keys on registeredAs or on names without a national register API (Japan, Korea, United States, Hong Kong). Public, no key."""
import requests, json, os, datetime
os.makedirs('raw', exist_ok=True)
_j = requests.get('https://goldencopy.gleif.org/api/v2/golden-copies/publishes/lei2/latest', headers={'Accept': 'application/json'}, timeout=60).json(); meta = _j.get('data', _j)
csv = meta['full_file']['csv']; print('golden copy', meta['publish_date'], csv['record_count'], csv['size_human_readable'], flush=True)
fn = 'raw/' + os.path.basename(csv['url'])
if not os.path.exists(fn) or os.path.getsize(fn) < csv['size']:
    with requests.get(csv['url'], stream=True, timeout=1800) as r:
        r.raise_for_status(); n = 0
        with open(fn, 'wb') as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk); n += len(chunk)
                if n % (50 << 20) < (1 << 20): print(f'{n / (1 << 20):.0f} MB', flush=True)
json.dump({'publish_date': meta['publish_date'], 'record_count': csv['record_count'], 'size': csv['size'], 'url': csv['url'], 'file': fn, 'fetched': datetime.date.today().isoformat(), 'cdf_version': csv.get('cdf_version')}, open('raw/golden.meta.json', 'w'))
print('DOWNLOAD DONE', fn, os.path.getsize(fn), flush=True)
