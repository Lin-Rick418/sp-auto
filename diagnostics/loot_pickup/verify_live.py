"""Bounded, stationary probe check. Default scans only; --pickup ID sends one click."""
import argparse
import json
import math
import os
from pathlib import Path
import time

parser = argparse.ArgumentParser()
parser.add_argument('--seconds', type=float, default=20)
parser.add_argument('--pickup', type=int, default=0)
parser.add_argument('--test-common', action='store_true', help='Permit one ordinary material for transport verification')
args = parser.parse_args()
ipc = Path(os.environ['LOCALAPPDATA']) / 'SpiritValeBot'
path = ipc / 'spiritvale_navigation_request.json'
state_path = ipc / 'spiritvale_memory_state.json'
request = json.loads(path.read_text(encoding='utf-8-sig'))
if request.get('probe_active') and time.time()*1000-request.get('timestamp_ms', 0) < 3000:
    raise SystemExit('Another controller owns fresh navigation IPC; stop it before verification.')
request.update(target_kind='none', target_object_id=0, probe_active=True,
    bot_active=False, loot_scan_active=True, party_follow_active=False,
    movement_keys='', movement_world=[0, 0, 0], shift_keys='', summon_action='',
    loot_interact=0, loot_interact_object_id=0, skill_key_request_id=0,
    skill_key='', skill_key_target_summon=False, focus_target_object_id=0,
    focus_target_world=[0, 0, 0], background_input_mode='send_process',
    background_skill_mode='capture', auto_relogin_enabled=False)
request.pop('channel_switch_request_id', None)
request.pop('channel_switch_index', None)

def write():
    request['timestamp_ms'] = time.time_ns() // 1_000_000
    request['request_id'] = request['timestamp_ms']
    temporary = path.with_suffix('.pickup.tmp')
    temporary.write_text(json.dumps(request), encoding='utf-8')
    os.replace(temporary, path)

start = time.time()
load_request = {'request_id': time.time_ns() // 1_000_000,
                'timestamp_ms': time.time_ns() // 1_000_000}
(ipc / 'spiritvale_probe_load_request.json').write_text(json.dumps(load_request), encoding='utf-8')
sent_at = None
seen_frames = absent_frames = 0
evidence = []
last_signature = None
last_timestamp = 0
try:
    while time.time() - start < args.seconds:
        write()
        time.sleep(.2)
        try:
            state = json.loads(state_path.read_text(encoding='utf-8-sig'))
        except (OSError, json.JSONDecodeError):
            continue
        timestamp = state.get('timestamp_ms', 0)
        if timestamp < start * 1000 or timestamp <= last_timestamp:
            continue
        last_timestamp = timestamp
        player = state.get('player') or {}
        origin = player.get('position', [0, 0, 0])
        loots = state.get('loots', [])
        nearest = sorted(loots, key=lambda row: math.dist(row['position'], origin))[:12]
        summary = {'status': state.get('status'), 'player': player.get('object_id'),
            'position': origin, 'loot_count': len(loots), 'nearest': nearest}
        signature = (summary['status'], tuple(round(c) for c in origin), len(loots))
        if signature != last_signature:
            last_signature = signature
            print(json.dumps({'status': summary['status'], 'position': origin, 'loot_count': len(loots),
                'nearest': [{k: row[k] for k in ('object_id', 'rarity', 'display_name', 'locked')}
                            for row in nearest[:3]]}, ensure_ascii=True), flush=True)
        (Path(__file__).parent / 'last_state.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
        if not args.pickup:
            continue
        target = next((row for row in loots if row['object_id'] == args.pickup), None)
        if target and sent_at is None:
            seen_frames += 1
            distance = math.dist(target['position'], origin)
            allowed_rarity = target.get('rarity') == 'Legendary' or (args.test_common and target.get('loot_type') == 'Junk')
            max_distance = target['interaction_range']
            if target.get('locked') or not allowed_rarity or distance > max_distance:
                raise RuntimeError('Target must be unlocked permitted loot within the test distance')
            if seen_frames >= 2:
                request.update(bot_active=True, loot_interact=int(time.time()) & 0x7fffffff,
                               loot_interact_object_id=args.pickup)
                sent_at = time.time()
                evidence.append({'before': target, 'distance': distance, 'sent_at': sent_at,
                                 'snapshot_timestamp_ms': timestamp})
                print('Sending one stationary targeted pickup: ' + str(args.pickup), flush=True)
        elif sent_at is not None:
            absent_frames = absent_frames + 1 if target is None else 0
            if absent_frames >= 3 and state.get('status') == 'ok':
                evidence.append({'absent_at': time.time(), 'absent_frames': absent_frames,
                                 'snapshot_timestamp_ms': timestamp})
                print('OBSERVED: target absent in three fresh snapshots after request', flush=True)
                break
finally:
    request.update(bot_active=False, probe_active=False, loot_scan_active=False,
                   loot_interact=0, loot_interact_object_id=0)
    write()
    (Path(__file__).parent / 'live_result.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
