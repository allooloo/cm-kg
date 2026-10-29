r"""ORDER-032 — boot check of one standby without touching DNS: scale to 1, wait for the task, read its CloudWatch log for the ark bundle and the TLS
listener, scale back to 0. The door's security group admits Cloudflare only, so the log is the proof here; the wire proof is swap.py.
Usage: python standby_boot_check.py <cc>"""
import os, sys, json, time
import boto3
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__))); import infra_policy as _ip   # ENUM-01 (DAY ORDER 6): ark region, zone, ident read from the roster and the policy of record
ARK = _ip.Lazy(_ip.ark_region)
cc = sys.argv[1]; R = ARK[cc]; SVC = f'allooloo-standby-{cc}'; LG = f'/allooloo/standby/{cc}'
_k = open(r'C:\MATTHEWKEDDY\AGENT KEYS\aws-standby-deployer.txt', encoding='utf-8').read().split()
S = boto3.session.Session(aws_access_key_id=_k[0], aws_secret_access_key=_k[1], region_name=R); del _k
ecs, logs = S.client('ecs'), S.client('logs'); out = {'node': f'{cc}-cm-kg', 'region': R}
try:
    t0 = int(time.time() * 1000); ecs.update_service(cluster='allooloo-standby', service=SVC, desiredCount=1); print('scaled to 1', SVC, R, flush=True)
    ecs.get_waiter('services_stable').wait(cluster='allooloo-standby', services=[SVC], WaiterConfig={'Delay': 15, 'MaxAttempts': 40})
    time.sleep(180)   # hold the task up three minutes so its boot lines reach the log (our own task, not an external clock)
    # the deployer may filter its log groups (logs:FilterLogEvents) but not list streams; one read of the group since the scale-up
    ev = [e['message'] for e in logs.filter_log_events(logGroupName=LG, startTime=t0, limit=100).get('events', [])]
    out['log'] = ev[:20]; out['ark_loaded'] = any('ark bundle loaded' in m for m in ev); out['tls'] = any('tls on' in m for m in ev); out['index_keys'] = next((m for m in ev if 'index keys' in m), None)
    print('\n'.join('  ' + m[:200] for m in ev[:12]))
finally:
    ecs.update_service(cluster='allooloo-standby', service=SVC, desiredCount=0); print('scaled back to 0', flush=True)
out['pass'] = bool(out.get('ark_loaded') and out.get('tls') and out.get('index_keys') and ' 0' not in (out.get('index_keys') or ' 0'))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'standby-boot-{cc}.json'), 'w', encoding='utf-8'), indent=1)
print(f"{cc}-cm-kg standby boot check: {'PASS' if out['pass'] else 'FAIL'} (ark bundle {out.get('ark_loaded')}, tls {out.get('tls')}, {out.get('index_keys')})")
