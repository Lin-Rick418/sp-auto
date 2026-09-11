"""Portable runtime paths shared by the SpiritVale probe and Python tools."""

from __future__ import annotations

import os
from pathlib import Path
import json
import time


def _local_app_data() -> Path:
    configured = os.environ.get("LOCALAPPDATA")
    if configured:
        return Path(configured)
    return Path.home() / "AppData" / "Local"


PORTABLE_IPC_DIR = _local_app_data() / "SpiritValeBot"
LEGACY_IPC_DIR = Path(__file__).resolve().parent
STATE_FILE_NAME = "spiritvale_memory_state.json"
PROBE_LOAD_REQUEST_FILE_NAME = "spiritvale_probe_load_request.json"
PROBE_LOADER_STATE_FILE_NAME = "spiritvale_probe_loader_state.json"


def _state_is_recent(directory: Path, *, now: float, max_age_sec: float) -> bool:
    try:
        modified = (directory / STATE_FILE_NAME).stat().st_mtime
    except OSError:
        return False
    return -1.0 <= now - modified <= max_age_sec


def resolve_ipc_directory(
    portable_directory: Path = PORTABLE_IPC_DIR,
    legacy_directory: Path = LEGACY_IPC_DIR,
    *,
    override: str | None = None,
    now: float | None = None,
    compatibility_max_age_sec: float = 5.0,
) -> Path:
    """Choose portable IPC, with a live legacy-probe compatibility fallback."""

    configured = override or os.environ.get("SPIRITVALE_BOT_IPC_DIR")
    if configured:
        return Path(configured).expanduser()

    checked_at = time.time() if now is None else float(now)
    if _state_is_recent(
        portable_directory,
        now=checked_at,
        max_age_sec=compatibility_max_age_sec,
    ):
        return portable_directory
    if _state_is_recent(
        legacy_directory,
        now=checked_at,
        max_age_sec=compatibility_max_age_sec,
    ):
        return legacy_directory
    return portable_directory


IPC_DIR = resolve_ipc_directory()
IPC_DIR.mkdir(parents=True, exist_ok=True)


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
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


def request_probe_load(
    *, timeout_sec: float = 12.0, poll_interval_sec: float = 0.05
) -> str:
    """Ask the resident BepInEx loader to load the probe and await its ack."""

    now = time.time()
    if _state_is_recent(IPC_DIR, now=now, max_age_sec=1.0):
        return "already_running"

    request_id = time.time_ns() // 1_000
    request_path = PORTABLE_IPC_DIR / PROBE_LOAD_REQUEST_FILE_NAME
    loader_state_path = PORTABLE_IPC_DIR / PROBE_LOADER_STATE_FILE_NAME
    _atomic_write_json(
        request_path,
        {
            "schema_version": 1,
            "request_id": request_id,
            "timestamp_ms": time.time_ns() // 1_000_000,
            "requester_pid": os.getpid(),
        },
    )

    deadline = time.monotonic() + max(0.05, float(timeout_sec))
    while time.monotonic() < deadline:
        try:
            state = json.loads(loader_state_path.read_text(encoding="utf-8-sig"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            state = None
        if isinstance(state, dict) and state.get("request_id") == request_id:
            status = str(state.get("status", ""))
            if status == "loaded":
                return "loaded_on_demand"
            if status == "error":
                raise RuntimeError(
                    "SpiritVale 探針按需載入失敗："
                    + str(state.get("error") or "未知錯誤")
                )

        # Compatibility with an older, startup-loaded probe that has no loader.
        if _state_is_recent(IPC_DIR, now=time.time(), max_age_sec=1.0):
            return "legacy_probe"
        time.sleep(max(0.01, min(0.25, float(poll_interval_sec))))

    raise RuntimeError(
        "等待 SpiritVale 探針載入逾時。請確認遊戲已啟動、BepInEx 已載入 "
        "SpiritVale Probe Loader 2.11.0，且已用 v2.16.0 INSTALL.cmd 安裝。"
    )
