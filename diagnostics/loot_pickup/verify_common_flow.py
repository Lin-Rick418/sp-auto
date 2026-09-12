"""Run the real bot for at most 60 seconds with a temporary Common threshold."""
import dataclasses
import json
import math
import sys
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import spiritvale_red_dot_bot as bot

original_config = bot.CONFIG_PATH.read_bytes()
config = dataclasses.replace(bot.load_config(bot.CONFIG_PATH),
    memory_loot_min_rarity='Common', start_paused=False, debug_window=False,
    pricing_enabled=False, pricing_auto_start=False)
mode = bot.load_mode_config(bot.MODE_CONFIG_PATH)
hwnd, _ = bot.find_window(config.window_title)
bot.request_probe_load()
started = time.monotonic()
real_window = bot.win32gui.IsWindow
real_load = bot.load_memory_snapshot
real_write = bot.write_navigation_request
real_print = print
latest = None
last_timestamp = 0
last_seq = 0
attempts = {}
paths = {}
release_counts = {}
confirmed = set()
events = []

def observe(*args, **kwargs):
    global latest, last_timestamp
    latest = real_load(*args, **kwargs)
    if latest.timestamp_ms != last_timestamp:
        last_timestamp = latest.timestamp_ms
        live_ids = {item.object_id for item in latest.loots}
        for object_id, record in attempts.items():
            if object_id in confirmed:
                continue
            if record['map'] != (latest.map_id, latest.instance_id):
                continue
            record['absent_frames'] = record['absent_frames'] + 1 if object_id not in live_ids else 0
            if record['absent_frames'] >= 3:
                confirmed.add(object_id)
                event = {'event': 'disappeared', 'id': object_id, 'snapshot_ms': latest.timestamp_ms,
                         'elapsed_seconds': round(time.monotonic()-started, 2),
                         'seconds_after_request': round(time.monotonic()-record['sent'], 2)}
                events.append(event)
                print('CHECK ' + json.dumps(event), flush=True)
    return latest

def write(*args, **kwargs):
    global last_seq
    real_write(*args, **kwargs)
    if latest is None:
        return
    target_id = args[2]
    if kwargs.get('target_kind') == 'loot' and target_id not in paths:
        target = next((item for item in latest.loots if item.object_id == target_id), None)
        if target:
            paths[target_id] = math.dist(latest.player.position, target.position)
            events.append({'event': 'approach', 'id': target_id, 'distance': paths[target_id],
                           'elapsed_seconds': round(time.monotonic()-started, 2)})
    seq = kwargs.get('loot_interact', 0)
    if seq > 0 and seq != last_seq:
        last_seq = seq
        target_id = kwargs['loot_interact_object_id']
        target = next((item for item in latest.loots if item.object_id == target_id), None)
        if target:
            if target_id not in attempts:
                attempts[target_id] = {'map': (latest.map_id, latest.instance_id),
                                      'sent': time.monotonic(), 'absent_frames': 0}
            event = {'event': 'request', 'seq': seq, 'id': target_id, 'rarity': target.rarity,
                     'name': target.display_name, 'distance': math.dist(latest.player.position, target.position),
                     'owned': target.owned_by_local_player,
                     'elapsed_seconds': round(time.monotonic()-started, 2)}
            events.append(event)
            print('CHECK ' + json.dumps(event), flush=True)

def observe_print(*args, **kwargs):
    message = args[0] if args and isinstance(args[0], str) else ''
    if message.startswith('拾取 ') and ' 前先放開所有移動鍵與 Shift' in message:
        try:
            object_id = int(message.split()[1])
        except (IndexError, ValueError):
            object_id = 0
        if object_id:
            release_counts[object_id] = release_counts.get(object_id, 0) + 1
            event = {'event': 'release', 'id': object_id,
                     'count': release_counts[object_id],
                     'elapsed_seconds': round(time.monotonic()-started, 2)}
            events.append(event)
            real_print('CHECK ' + json.dumps(event), flush=True)
    return real_print(*args, **kwargs)

def keep_running(window):
    enough = len(confirmed) >= 5 and any(i in confirmed for i in paths)
    return real_window(window) and time.monotonic()-started < 60 and not enough

try:
    with patch.object(bot, 'load_memory_snapshot', observe), patch.object(bot, 'write_navigation_request', write), \
         patch('builtins.print', observe_print), \
         patch.object(bot.win32gui, 'IsWindow', keep_running):
        bot.run_bot(hwnd, config, True, mode=mode.mode,
                    lock_mouse_to_monster=mode.lock_mouse_to_monster)
finally:
    report = {'threshold': 'Common', 'elapsed_seconds': round(time.monotonic()-started, 2),
              'confirmed_ids': sorted(confirmed), 'approached_ids': paths, 'events': events,
              'release_counts': release_counts,
              'original_config_unchanged': bot.CONFIG_PATH.read_bytes() == original_config}
    (Path(__file__).parent / 'common_full_flow_result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('RESULT ' + json.dumps(report), flush=True)
