"""Report the latest player position from the versioned memory-state file."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import time

from spiritvale_paths import IPC_DIR, request_probe_load


DEFAULT_SOURCE = IPC_DIR / "spiritvale_memory_state.json"
NAVIGATION_REQUEST_PATH = IPC_DIR / "spiritvale_navigation_request.json"


def write_snapshot_heartbeat(active: bool) -> None:
    payload = {
        "schema_version": 1,
        "request_id": 0,
        "target_kind": "none",
        "target_object_id": 0,
        "timestamp_ms": time.time_ns() // 1_000_000,
        "probe_active": bool(active),
        "bot_active": False,
        "auto_relogin_enabled": False,
    }
    temporary = NAVIGATION_REQUEST_PATH.with_name(
        f"{NAVIGATION_REQUEST_PATH.name}.{os.getpid()}.tmp"
    )
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, NAVIGATION_REQUEST_PATH)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--interval", type=float, default=1.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    request_probe_load()
    interval = max(0.1, args.interval)
    next_report = time.monotonic()
    next_heartbeat = -1.0
    try:
        while True:
            now_monotonic = time.monotonic()
            if now_monotonic >= next_heartbeat:
                write_snapshot_heartbeat(True)
                next_heartbeat = now_monotonic + 0.5
            try:
                state = json.loads(args.source.read_text(encoding="utf-8"))
                if state.get("schema_version") != 1 or state.get("status") != "ok":
                    raise ValueError(f"probe status={state.get('status', 'missing')}")
                player = state.get("player")
                if not isinstance(player, dict):
                    raise ValueError("player unavailable")
                x, y, z = map(float, player["position"])
                loots = state.get("loots", [])
                if not isinstance(loots, list):
                    loots = []
                loot_labels = [
                    f"{item.get('object_id', '?')}:{item.get('rarity', '?')}:"
                    f"{item.get('display_name') or item.get('item_id') or '?'}"
                    for item in loots
                    if isinstance(item, dict)
                ]
                now = datetime.now().astimezone().isoformat(timespec="seconds")
                print(
                    f"{now} X={x:.6f} Y={y:.6f} Z={z:.6f} "
                    f"MAP={int(state['map_id'])}/{int(state['instance_id'])} "
                    f"MONSTERS={len(state.get('monsters', []))} "
                    f"LOOTS={len(loots)} "
                    f"LOOT_ITEMS={' | '.join(loot_labels) if loot_labels else '-'} "
                    f"SOURCE_MS={int(state['timestamp_ms'])}",
                    flush=True,
                )
            except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                print(
                    f"POSITION_UNAVAILABLE {type(error).__name__}: {error}",
                    flush=True,
                )
            next_report += interval
            time.sleep(max(0.0, next_report - time.monotonic()))
    finally:
        write_snapshot_heartbeat(False)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
