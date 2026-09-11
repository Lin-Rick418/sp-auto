"""Bounded GuardianBond probe check; --cast explicitly sends one skill request."""
import argparse
import json
import os
from pathlib import Path
import time

parser = argparse.ArgumentParser()
parser.add_argument('--cast', action='store_true')
parser.add_argument('--seconds', type=float, default=6)
parser.add_argument('--summon-key', default='')
args = parser.parse_args()
ipc = Path(os.environ['LOCALAPPDATA']) / 'SpiritValeBot'
path = ipc / 'spiritvale_navigation_request.json'
state_path = ipc / 'spiritvale_memory_state.json'
config = json.loads((Path(__file__).resolve().parents[2] / 'spiritvale_bot_config.json').read_text(encoding='utf-8-sig'))
request = json.loads(path.read_text(encoding='utf-8-sig'))
if request.get('bot_active') and time.time()*1000-request.get('timestamp_ms', 0) < 3000:
    raise SystemExit('Another active bot owns navigation IPC; stop it before verification.')
request.update(target_kind='none', target_object_id=0, probe_active=True,
    bot_active=False, loot_scan_active=False, party_follow_active=False,
    movement_keys='', movement_world=[0,0,0], shift_keys='', summon_action='',
    loot_interact=0, loot_interact_object_id=0, skill_key_request_id=0,
    skill_key='', skill_key_target_summon=False, focus_target_object_id=0,
    focus_target_world=[0,0,0], background_input_mode='send_process',
    background_skill_mode='capture', auto_relogin_enabled=False)
def write():
    request['timestamp_ms'] = time.time_ns()//1_000_000
    request['request_id'] = request['timestamp_ms']
    temporary = path.with_suffix('.guardian.tmp')
    temporary.write_text(json.dumps(request), encoding='utf-8')
    os.replace(temporary, path)
start = time.time()
sent = False
summoned = False
last = None
evidence = []
try:
    while time.time()-start < args.seconds:
        write()
        time.sleep(.15)
        try:
            snapshot = json.loads(state_path.read_text(encoding='utf-8-sig'))
        except (OSError, json.JSONDecodeError):
            continue
        if snapshot.get('timestamp_ms', 0) < start*1000:
            continue
        bond = (snapshot.get('player') or {}).get('guardian_bond')
        if args.summon_key and not summoned and bond and bond.get('available') and bond.get('candidate_unit_id', 0) == 0:
            request.update(bot_active=True, skill_key=args.summon_key,
                skill_key_target_summon=False, skill_key_request_id=time.time_ns()//1_000_000)
            summoned = True
            print('Sending configured summon key once', flush=True)
        if bond != last:
            last = bond
            row = {'timestamp_ms': snapshot.get('timestamp_ms'), 'status': snapshot.get('status'), 'guardian_bond': bond}
            evidence.append(row)
            print(json.dumps(row), flush=True)
        if bond and bond.get('has_owned_bond'):
            print('CONFIRMED: outgoing GuardianBond to a living owned summon', flush=True)
            break
        if args.cast and not sent and bond and bond.get('available') and bond.get('candidate_unit_id', 0) > 0:
            request.update(bot_active=True,
                skill_key=config['summoner_checks']['GuardianBond']['key'],
                skill_key_target_summon=True,
                skill_key_request_id=time.time_ns()//1_000_000)
            sent = True
            print('Sending one GuardianBond input request', flush=True)
    else:
        print('NOT CONFIRMED: no owned bond observed within verification window', flush=True)
finally:
    request.update(bot_active=False, probe_active=False, skill_key_request_id=0,
                   skill_key='', skill_key_target_summon=False)
    write()
    (Path(__file__).parent / 'live_result.json').write_text(json.dumps(
        {'cast_requested': sent, 'observations': evidence}, indent=2), encoding='utf-8')
