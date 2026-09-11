"""Set one exact currently-equipped item as favorite through the game probe."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import spiritvale_inventory_pricer as inventory_pricer
from spiritvale_paths import IPC_DIR, request_probe_load


REQUEST_PATH = IPC_DIR / "spiritvale_favorite_request.json"
RESULT_PATH = IPC_DIR / "spiritvale_favorite_result.json"
CONFIRMATION = "SET_FAVORITE"


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


def equipped_items(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for slot_entry in inventory.get("equipped_items", []):
        if not isinstance(slot_entry, dict):
            continue
        item = slot_entry.get("item")
        if isinstance(item, dict):
            result.append(item)
    return result


def set_equipped_favorite(
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
        for item in equipped_items(inventory)
        if item.get("uid") == uid and item.get("item_id") == item_id
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "The exact UID and item ID were not found exactly once among "
            "currently-equipped items"
        )
    if matches[0].get("favorite") is True:
        return {
            "schema_version": 1,
            "status": "ok",
            "uid": uid,
            "item_id": item_id,
            "message": "Equipped item was already a favorite; no toggle was sent",
            "favorite": True,
        }

    request_id = time.time_ns() // 1_000
    atomic_write_json(
        REQUEST_PATH,
        {
            "schema_version": 1,
            "request_id": request_id,
            "timestamp_ms": time.time_ns() // 1_000_000,
            "uid": uid,
            "item_id": item_id,
            "location": "equipped",
            "desired": True,
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
            "Favorite verification timed out after status="
            + str(last_result.get("status"))
        )
    raise TimeoutError("Favorite request timed out; confirm probe v2.16.0 is loaded")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set one exact currently-equipped item as favorite."
    )
    parser.add_argument("--uid", required=True)
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--timeout", type=float, default=18.0)
    args = parser.parse_args()

    result = set_equipped_favorite(
        args.uid,
        args.item_id,
        confirmation=args.confirm,
        timeout=max(1.0, args.timeout),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
