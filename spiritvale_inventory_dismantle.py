"""Submit one guarded equipment dismantle request through the in-game probe."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import spiritvale_inventory_pricer as inventory_pricer
from spiritvale_paths import IPC_DIR, request_probe_load


REQUEST_PATH = IPC_DIR / "spiritvale_dismantle_request.json"
RESULT_PATH = IPC_DIR / "spiritvale_dismantle_result.json"
CONFIRMATION = "DISMANTLE_EQUIP"


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def dismantle_equipment(
    uid: str,
    item_id: str,
    *,
    confirmation: str,
    timeout: float = 18.0,
) -> dict[str, Any]:
    if confirmation != CONFIRMATION:
        raise ValueError(f"--confirm must equal {CONFIRMATION}")

    request_probe_load(timeout_sec=min(12.0, timeout))
    inventory = inventory_pricer.read_inventory(min(8.0, timeout))
    matches = [
        item
        for item in inventory.get("items", [])
        if isinstance(item, dict)
        and item.get("uid") == uid
        and item.get("item_id") == item_id
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "The exact UID and item ID were not found exactly once in the fresh backpack"
        )
    if matches[0].get("favorite") is True:
        raise RuntimeError("Refusing to dismantle favorite equipment")

    request_id = time.time_ns() // 1_000
    atomic_write_json(
        REQUEST_PATH,
        {
            "schema_version": 1,
            "request_id": request_id,
            "timestamp_ms": time.time_ns() // 1_000_000,
            "uid": uid,
            "item_id": item_id,
            "confirm": confirmation,
        },
    )

    deadline = time.monotonic() + timeout
    last_result: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        try:
            candidate = json.loads(RESULT_PATH.read_text(encoding="utf-8-sig"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            time.sleep(0.05)
            continue
        if not isinstance(candidate, dict) or candidate.get("request_id") != request_id:
            time.sleep(0.05)
            continue
        last_result = candidate
        if candidate.get("status") in {"ok", "error", "unverified"}:
            return candidate
        time.sleep(0.05)

    if last_result is not None:
        raise TimeoutError(
            "Dismantle verification timed out after status="
            + str(last_result.get("status"))
        )
    raise TimeoutError(
        "Dismantle request timed out; confirm probe v2.16.0 is loaded"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Permanently dismantle one exact, non-favorite backpack equip."
    )
    parser.add_argument("--uid", required=True)
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--timeout", type=float, default=18.0)
    args = parser.parse_args()

    result = dismantle_equipment(
        args.uid,
        args.item_id,
        confirmation=args.confirm,
        timeout=max(1.0, args.timeout),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
