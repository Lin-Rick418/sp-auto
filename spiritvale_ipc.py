"""Probe JSON transport, Windows shared-file reads, and request publication."""

from __future__ import annotations

from ctypes import wintypes
from pathlib import Path
from typing import Callable, Iterable
import ctypes
import json
import math
import msvcrt
import os
import threading
import time
from spiritvale_config import (
    HELD_SHIFT_KEYS,
    NUMPAD_SKILL_KEYS,
)
from spiritvale_models import (
    MemorySnapshot,
    SnapshotUnavailable,
)
from spiritvale_snapshot import (
    MEMORY_SCHEMA_VERSION,
    parse_memory_snapshot,
)


_CREATE_FILE = ctypes.windll.kernel32.CreateFileW
_CREATE_FILE.argtypes = (
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
)
_CREATE_FILE.restype = wintypes.HANDLE
_CLOSE_HANDLE = ctypes.windll.kernel32.CloseHandle
_CLOSE_HANDLE.argtypes = (wintypes.HANDLE,)
_CLOSE_HANDLE.restype = wintypes.BOOL

_GENERIC_READ = 0x80000000
_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_FILE_SHARE_DELETE = 0x00000004
_OPEN_EXISTING = 3
_FILE_ATTRIBUTE_NORMAL = 0x00000080
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


IPC_READ_ATTEMPTS = 5


IPC_WRITE_ATTEMPTS = 5


IPC_RETRY_DELAY_SEC = 0.002


class NavigationRequestPublisher:
    """Own request revisions, duplicate suppression, and heartbeat timing.

    Moving or retrying a pickup keeps the current path revision. A new target,
    mode, focus, channel/consumable request, or skill request invalidates it.
    Only a successful write advances the remembered state.
    """

    _REVISION_FIELDS = (
        'probe_active', 'loot_scan_active', 'party_follow_active', 'bot_active',
        'follow_channel_request_id', 'follow_player_id', 'channel_switch_request_id',
        'consumable_use_request_id', 'skill_key_request_id', 'skill_key',
        'skill_key_target_summon', 'focus_target_object_id',
    )
    _INPUT_FIELDS = ('movement_keys', 'shift_keys', 'summon_action', 'loot_interact')

    def __init__(self, path: Path) -> None:
        self.path = path
        self.request_id = 0
        self.target_object_id = 0
        self.target_kind = 'none'
        self._revision_key: tuple[object, ...] | None = None
        self._input_key: tuple[object, ...] | None = None
        self._written_at = -math.inf

    def publish(
        self, object_id: int, target_kind: str, *, now: float,
        force: bool = False, writer: Callable[..., None] | None = None,
        **intent: object,
    ) -> bool:
        revision_key = (object_id, target_kind) + tuple(
            intent.get(name) for name in self._REVISION_FIELDS
        )
        input_key = tuple(intent.get(name) for name in self._INPUT_FIELDS)
        same_revision = revision_key == self._revision_key
        same_input = same_revision and input_key == self._input_key
        if not force and same_input and now - self._written_at < 0.5:
            return False
        request_id = self.request_id + int(not same_revision)
        write = writer or write_navigation_request
        write(self.path, request_id, object_id, target_kind=target_kind, **intent)
        self.request_id = request_id
        self.target_object_id = object_id
        self.target_kind = target_kind
        self._revision_key = revision_key
        self._input_key = input_key
        self._written_at = now
        return True


def load_memory_snapshot(
    path: Path,
    max_age_ms: int,
    *,
    now_ms: int | None = None,
    avoid_boss: bool = False,
) -> MemorySnapshot:
    last_error: OSError | json.JSONDecodeError | None = None
    raw: object | None = None
    for attempt in range(IPC_READ_ATTEMPTS):
        try:
            raw = json.loads(_read_windows_shared_text(path))
            break
        except (OSError, json.JSONDecodeError) as error:
            last_error = error
            if attempt + 1 < IPC_READ_ATTEMPTS:
                time.sleep(IPC_RETRY_DELAY_SEC * (2**attempt))
    if raw is None:
        raise SnapshotUnavailable(
            f"cannot read memory state after {IPC_READ_ATTEMPTS} attempts: {last_error}"
        ) from last_error
    return parse_memory_snapshot(
        raw,
        now_ms=int(time.time() * 1000) if now_ms is None else now_ms,
        max_age_ms=max(1, int(max_age_ms)),
        avoid_boss=avoid_boss,
    )


def wait_for_wallet_snapshot(
    path: Path,
    max_age_ms: int,
    *,
    after_timestamp_ms: int,
    wait_timeout_ms: int = 1000,
    avoid_boss: bool = False,
    snapshot_reader: Callable[..., MemorySnapshot] | None = None,
) -> MemorySnapshot:
    """Wait briefly for a post-stop-request snapshot with wallet data."""
    read_snapshot = snapshot_reader or load_memory_snapshot
    deadline = time.monotonic() + max(100, int(wait_timeout_ms)) / 1000
    last_error: SnapshotUnavailable | None = None
    while True:
        try:
            snapshot = read_snapshot(
                path, max_age_ms, avoid_boss=avoid_boss
            )
            if snapshot.timestamp_ms < int(after_timestamp_ms):
                last_error = SnapshotUnavailable(
                    "wallet snapshot has not refreshed yet"
                )
            elif not snapshot.player.wallet_coins_available:
                detail = snapshot.player.wallet_coins_error or "unavailable"
                last_error = SnapshotUnavailable(f"wallet coins unavailable: {detail}")
            else:
                return snapshot
        except SnapshotUnavailable as error:
            last_error = error
        if time.monotonic() >= deadline:
            assert last_error is not None
            raise SnapshotUnavailable(
                f"timed out waiting for wallet snapshot: {last_error}"
            ) from last_error
        time.sleep(0.05)


def wait_for_party_snapshot(
    path: Path,
    max_age_ms: int,
    *,
    after_timestamp_ms: int,
    wait_timeout_ms: int = 1500,
    snapshot_reader: Callable[..., MemorySnapshot] | None = None,
) -> MemorySnapshot:
    """Wait for a fresh party-only probe response after an F2 wake request."""
    read_snapshot = snapshot_reader or load_memory_snapshot
    deadline = time.monotonic() + max(100, int(wait_timeout_ms)) / 1000
    last_error: SnapshotUnavailable | None = None
    while True:
        try:
            snapshot = read_snapshot(path, max_age_ms)
            if (
                snapshot.timestamp_ms >= int(after_timestamp_ms)
                and snapshot.party_state_available
            ):
                return snapshot
            last_error = SnapshotUnavailable("party snapshot has not refreshed yet")
        except SnapshotUnavailable as error:
            last_error = error
        if time.monotonic() >= deadline:
            assert last_error is not None
            raise SnapshotUnavailable(
                f"timed out waiting for party snapshot: {last_error}"
            ) from last_error
        time.sleep(0.05)


def _read_windows_shared_text(path: Path) -> str:
    """Read one stable generation while allowing the probe to replace the path."""
    handle = _CREATE_FILE(
        str(path),
        _GENERIC_READ,
        _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE,
        None,
        _OPEN_EXISTING,
        _FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == _INVALID_HANDLE_VALUE:
        raise ctypes.WinError()

    descriptor: int | None = None
    try:
        descriptor = msvcrt.open_osfhandle(
            int(handle), os.O_RDONLY | getattr(os, "O_BINARY", 0)
        )
    except Exception:
        _CLOSE_HANDLE(handle)
        raise

    with os.fdopen(descriptor, "rb") as stream:
        return stream.read().decode("utf-8")


def atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    # 用「行程 + 執行緒」唯一的暫存檔名，避免多個實例（或多執行緒）共用同一個
    # 固定 .tmp 檔而互搶：先搶到的 os.replace 會把 .tmp 移走，另一個就會拿到
    # WinError 2（找不到檔案）而整個 crash。
    temporary = path.with_name(
        f"{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    last_error: OSError | None = None
    for attempt in range(IPC_WRITE_ATTEMPTS):
        try:
            os.replace(temporary, path)
            return
        except OSError as error:
            last_error = error
            if attempt + 1 < IPC_WRITE_ATTEMPTS:
                time.sleep(IPC_RETRY_DELAY_SEC * (2**attempt))
    # 持續失敗時清掉殘留的暫存檔，避免留下垃圾。
    try:
        temporary.unlink()
    except OSError:
        pass
    assert last_error is not None
    raise last_error


def write_navigation_request(
    path: Path,
    request_id: int,
    target_object_id: int,
    *,
    target_kind: str = "monster",
    now_ms: int | None = None,
    probe_active: bool = False,
    loot_scan_active: bool = False,
    party_follow_active: bool = False,
    bot_active: bool = False,
    movement_keys: Iterable[str] = (),
    movement_world: tuple[int, int, int] = (0, 0, 0),
    shift_keys: Iterable[str] = (),
    summon_action: str = "",
    skill_key_request_id: int = 0,
    skill_key: str = "",
    skill_key_target_summon: bool = False,
    loot_interact: int = 0,
    loot_interact_object_id: int = 0,
    focus_target_object_id: int = 0,
    focus_target_world: tuple[float, float, float] = (0.0, 0.0, 0.0),
    background_input_mode: str = "inputs",
    background_skill_mode: str = "capture",
    auto_relogin_enabled: bool = False,
    auto_relogin_disconnect_grace_sec: float = 3.0,
    auto_relogin_builtin_wait_max_sec: float = 30.0,
    auto_relogin_attempt_timeout_sec: float = 30.0,
    auto_relogin_retry_delay_sec: float = 10.0,
    auto_relogin_max_attempts: int = 5,
    follow_channel_request_id: int = 0,
    follow_player_id: str = "",
    channel_switch_request_id: int = 0,
    channel_switch_index: int = -1,
    consumable_use_request_id: int = 0,
    consumable_name: str = "",
) -> None:
    normalized_kind = str(target_kind).strip().casefold()
    if normalized_kind not in {"none", "monster", "loot", "player"}:
        raise ValueError("target_kind must be none, monster, loot, or player")
    movement_key_set = set(movement_keys)
    shift_key_set = set(shift_keys)
    normalized_movement_world = tuple(
        max(-1, min(1, int(component))) for component in movement_world
    )
    if len(normalized_movement_world) != 3:
        raise ValueError("movement_world must contain exactly three components")
    normalized_focus_target_world = tuple(
        float(component) for component in focus_target_world
    )
    if len(normalized_focus_target_world) != 3:
        raise ValueError("focus_target_world must contain exactly three components")
    if not all(math.isfinite(component) for component in normalized_focus_target_world):
        raise ValueError("focus_target_world components must be finite")
    normalized_background_input_mode = str(background_input_mode).strip().casefold()
    if normalized_background_input_mode not in {
        "inputs",
        "both",
        "apply",
        "send",
        "send_apply",
        "send_process",
    }:
        raise ValueError(
            "background_input_mode must be inputs, both, apply, send, "
            "send_apply, or send_process"
        )
    normalized_background_skill_mode = str(background_skill_mode).strip().casefold()
    if normalized_background_skill_mode not in {
        "capture",
        "process",
        "click",
        "process_click",
    }:
        raise ValueError(
            "background_skill_mode must be capture, process, click, or process_click"
        )
    normalized_skill_key = str(skill_key).strip().casefold()
    if normalized_skill_key and normalized_skill_key not in NUMPAD_SKILL_KEYS:
        raise ValueError("skill_key must be numpad0 through numpad9")
    payload: dict[str, object] = {
        "schema_version": MEMORY_SCHEMA_VERSION,
        "request_id": int(request_id),
        "target_kind": normalized_kind,
        "target_object_id": int(target_object_id),
        "timestamp_ms": int(time.time() * 1000) if now_ms is None else int(now_ms),
        "probe_active": bool(probe_active),
        "loot_scan_active": bool(loot_scan_active),
        "party_follow_active": bool(party_follow_active),
        "bot_active": bool(bot_active),
        "movement_keys": "".join(
            key for key in ("w", "a", "s", "d") if key in movement_key_set
        ),
        "movement_world": list(normalized_movement_world),
        "shift_keys": ",".join(
            key for key in HELD_SHIFT_KEYS if key in shift_key_set
        ),
        "summon_action": (
            str(summon_action).strip().casefold()
            if str(summon_action).strip().casefold() in {"reanimation", "mount"}
            else ""
        ),
        "skill_key_request_id": max(0, int(skill_key_request_id)),
        "skill_key": normalized_skill_key,
        "skill_key_target_summon": bool(skill_key_target_summon),
        "loot_interact": max(0, int(loot_interact)),
        "loot_interact_object_id": max(0, int(loot_interact_object_id)),
        "focus_target_object_id": max(0, int(focus_target_object_id)),
        "focus_target_world": list(normalized_focus_target_world),
        "background_input_mode": normalized_background_input_mode,
        "background_skill_mode": normalized_background_skill_mode,
        "auto_relogin_enabled": bool(auto_relogin_enabled),
        "auto_relogin_disconnect_grace_sec": max(
            0.5, float(auto_relogin_disconnect_grace_sec)
        ),
        "auto_relogin_builtin_wait_max_sec": max(
            0.0, float(auto_relogin_builtin_wait_max_sec)
        ),
        "auto_relogin_attempt_timeout_sec": max(
            1.0, float(auto_relogin_attempt_timeout_sec)
        ),
        "auto_relogin_retry_delay_sec": max(
            0.0, float(auto_relogin_retry_delay_sec)
        ),
        "auto_relogin_max_attempts": min(
            20, max(1, int(auto_relogin_max_attempts))
        ),
    }
    normalized_follow_player_id = str(follow_player_id).strip()
    if normalized_follow_player_id and (
        bool(party_follow_active) or int(follow_channel_request_id) > 0
    ):
        payload["follow_player_id"] = normalized_follow_player_id
        if int(follow_channel_request_id) > 0:
            payload["follow_channel_request_id"] = int(follow_channel_request_id)
    if int(channel_switch_request_id) > 0 and int(channel_switch_index) >= 0:
        payload["channel_switch_request_id"] = int(channel_switch_request_id)
        payload["channel_switch_index"] = int(channel_switch_index)
    normalized_consumable_name = str(consumable_name).strip()
    if int(consumable_use_request_id) > 0 and normalized_consumable_name:
        payload["consumable_use_request_id"] = int(consumable_use_request_id)
        payload["consumable_name"] = normalized_consumable_name
    atomic_write_json(path, payload)
