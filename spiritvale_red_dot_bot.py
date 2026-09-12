"""SpiritVale world-coordinate navigator for Windows.

The BepInEx probe exposes the local player, hostile monsters, dropped loot,
camera axes and a Unity NavMesh path through versioned JSON files. This process
follows world-space waypoints with background WASD and requests targeted
interaction with eligible loot. It never captures the game image.

Use only where the game's rules permit automation.
"""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import queue
import sys
import threading
import time
from typing import Any, Callable, Iterable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import win32api
import win32con
import win32gui

import spiritvale_card_buyer as card_buyer
import spiritvale_equipment_filter as equipment_filter
import spiritvale_inventory_pricer as inventory_pricer
from spiritvale_paths import IPC_DIR, request_probe_load


# Re-export the established API for existing launchers and diagnostics.
from spiritvale_config import (
    BotConfig,
    ModeConfig,
    default_summoner_checks,
    load_config,
    normalize_summoner_checks,
    load_mode_config,
    save_config,
    VK_BY_KEY,
    HELD_SHIFT_KEYS,
    JOB_TYPE_LABELS,
    F8_SHIFT_KEYS_BY_JOB_TYPE,
    NAVIGATION_UPKEEP_JOB_TYPES,
    SUMMONER_CHECK_ORDER,
    SUMMONER_SUMMON_IDS,
    SUMMONER_BUFF_IDS,
    SUMMONER_TARGET_SUMMON_IDS,
    SUMMONER_CHECK_LABELS,
    NUMPAD_SKILL_KEYS,
    MODE_NAMES,
)
from spiritvale_models import (
    MemoryPlayer,
    MemoryObservedPlayer,
    MemoryPartyMember,
    MemoryMonster,
    MemoryLoot,
    MemoryMapExit,
    MemoryPath,
    MemoryConsumableUse,
    MemorySnapshot,
    CombatWatchdogState,
    LootChaseState,
    SummonMountKeyState,
    SummonerCheckState,
    NavigationEarningsState,
    NavigationEarningsReport,
    BossFarmState,
    SnapshotUnavailable,
)
from spiritvale_snapshot import (
    MEMORY_SCHEMA_VERSION,
    _finite_float,
    _vector3,
    _vector2,
    parse_memory_snapshot,
    no_enemy_status,
    snapshot_error_log_key,
)
from spiritvale_ipc import (
    NavigationRequestPublisher,
    IPC_READ_ATTEMPTS,
    IPC_WRITE_ATTEMPTS,
    IPC_RETRY_DELAY_SEC,
    load_memory_snapshot,
    wait_for_wallet_snapshot,
    wait_for_party_snapshot,
    _read_windows_shared_text,
    atomic_write_json,
    write_navigation_request,
)
from spiritvale_navigation import (
    horizontal_distance,
    parse_monster_level,
    detect_boss_object_id,
    normalize_boss_name,
    monster_matches_boss,
    select_boss_farm_target,
    should_advance_train_target,
    select_memory_target,
    find_follow_player_by_name,
    find_follow_party_member_by_name,
    find_follow_party_member,
    find_local_party_member,
    party_channel_number,
    party_member_needs_channel_switch,
    find_follow_player,
    follow_stop_distance_world,
    update_follow_rejoin_state,
    select_follow_memory_target,
    reset_combat_watchdog,
    pause_combat_watchdog,
    update_combat_watchdog,
    combat_reengage_keys,
    finish_combat_reengage,
    refresh_combat_blacklist,
    request_path_matches,
    select_path_waypoint,
    _normalize2,
    movement_world_for_keys,
    movement_keys_for_world_waypoint,
    arrival_radius,
    map_exit_avoidance_radius,
    point_inside_map_exit_keepout,
    _horizontal_segment_distance,
    path_enters_map_exit_keepout,
    unstuck_keys,
)
from spiritvale_loot import (
    plan_loot_interaction,
    plan_loot_approach,
    LOOT_RARITY_VALUES,
    loot_is_equipment,
    select_boss_legendary_loot,
    loot_minimum_rarity_value,
    loot_ownership_label,
    select_memory_loot,
    loot_pickup_radius,
    loot_is_within_pickup_range,
    loot_pickup_hold_radius,
    reset_loot_chase,
    loot_chase_failure_reason,
    track_memory_loot_candidate,
)
from spiritvale_upkeep import (
    summon_mount_blocks_navigation,
    reset_summon_mount_key_state,
    advance_summon_mount_hotkeys,
    summon_mount_wait_status,
    reset_summoner_check_state,
    summoner_checks_enabled,
    missing_summoner_checks,
    advance_summoner_checks,
    summoner_check_wait_status,
    f8_shift_keys,
    next_priest_shift_tap_at,
)
from spiritvale_earnings import (
    start_navigation_earnings,
    pause_navigation_earnings,
    resume_navigation_earnings,
    mark_navigation_earnings_incomplete,
    observe_navigation_wallet,
    finish_navigation_earnings,
    format_navigation_earnings_report,
)


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "spiritvale_bot_config.json"
MODE_CONFIG_PATH = BASE_DIR / "spiritvale_mode_config.json"
MEMORY_STATE_PATH = IPC_DIR / "spiritvale_memory_state.json"
NAVIGATION_REQUEST_PATH = IPC_DIR / "spiritvale_navigation_request.json"
RADAR_WINDOW_NAME = "SpiritVale Navigator - Memory / NavMesh"
PRICE_WINDOW_NAME = "SpiritVale Backpack Prices"
PRICE_WINDOW_WIDTH = 760
PRICE_WINDOW_HEIGHT = 760
FOLLOW_CHANNEL_RETRY_SEC = 5.0

def control_menu_hotkey_down(hwnd: int) -> bool:
    """Read the single control hotkey (F8) that opens the consolidated menu.

    This is the only physical hotkey the bot listens for; every former function
    key (F2/F4/F5/F6/F7/F9/Del and the navigation toggle) is now chosen inside
    :func:`show_control_menu`. Kept as a standalone reader so the menu trigger
    stays independently patchable in tests.

    ``GetAsyncKeyState`` is global, so with several bots running at once every
    instance would otherwise pop its own menu on one F8 press. F8 therefore only
    acts when this bot's own game window is the foreground window: click the
    client you want to control, then press F8. If the foreground can't be read we
    do NOT open, so an unreadable state can never revert to popping every menu.
    """
    if not (win32api.GetAsyncKeyState(win32con.VK_F8) & 0x8000):
        return False
    try:
        return win32gui.GetForegroundWindow() == hwnd
    except Exception:
        return False


@dataclass(frozen=True)
class PricingDisplayRow:
    display_name: str
    quantity: int
    stat_text: str
    lowest_exact_price: int | None
    exact_listing_count: int
    over_threshold: bool


@dataclass(frozen=True)
class PricingViewState:
    phase: str = "idle"
    message: str = "Pricing has not started"
    running: bool = False
    current: int = 0
    total: int = 0
    timestamp_ms: int = 0
    threshold: int = 50_000
    equipment_count: int = 0
    eligible_equipment_count: int = 0
    favorite_skipped_count: int = 0
    priced_count: int = 0
    no_exact_sample_count: int = 0
    over_threshold_count: int = 0
    rows: tuple[PricingDisplayRow, ...] = ()


PricingRunner = Callable[..., dict[str, Any]]


def pricing_state_from_progress(
    event: dict[str, Any], threshold: int
) -> PricingViewState:
    phase = str(event.get("phase") or "working")
    return PricingViewState(
        phase=phase,
        message=str(event.get("message") or phase.replace("_", " ").title()),
        running=phase not in ("complete", "error", "cancelled", "idle"),
        current=int(event.get("current", 0)),
        total=int(event.get("total", 0)),
        timestamp_ms=int(event.get("timestamp_ms", 0)),
        threshold=threshold,
        equipment_count=int(event.get("equipment_count", 0)),
        eligible_equipment_count=int(event.get("eligible_equipment_count", 0)),
        favorite_skipped_count=int(event.get("favorite_skipped_count", 0)),
        priced_count=int(event.get("priced_count", 0)),
        no_exact_sample_count=int(event.get("no_exact_sample_count", 0)),
        over_threshold_count=int(event.get("over_threshold_count", 0)),
    )


def pricing_state_from_report(report: dict[str, Any]) -> PricingViewState:
    rows = tuple(
        PricingDisplayRow(
            display_name=str(item.get("display_name") or item.get("item_id") or "?"),
            quantity=max(1, int(item.get("quantity", 1))),
            stat_text=str(item.get("stat_text") or inventory_pricer.stat_label(item)),
            lowest_exact_price=(
                int(item["lowest_exact_price"])
                if item.get("lowest_exact_price") is not None
                else None
            ),
            exact_listing_count=int(item.get("exact_listing_count", 0)),
            over_threshold=bool(item.get("over_threshold")),
        )
        for item in report.get("grouped_items", [])
        if isinstance(item, dict)
    )
    return PricingViewState(
        phase="complete",
        message="Pricing complete",
        running=False,
        timestamp_ms=int(report.get("timestamp_ms", time.time_ns() // 1_000_000)),
        threshold=int(report.get("threshold", 50_000)),
        equipment_count=int(report.get("equipment_count", 0)),
        eligible_equipment_count=int(report.get("eligible_equipment_count", 0)),
        favorite_skipped_count=int(report.get("favorite_skipped_count", 0)),
        priced_count=int(report.get("priced_count", 0)),
        no_exact_sample_count=int(report.get("no_exact_sample_count", 0)),
        over_threshold_count=int(report.get("over_threshold_count", 0)),
        rows=rows,
    )


class PricingController:
    """Run inventory pricing off the navigation/UI thread."""

    def __init__(
        self,
        *,
        timeout: float,
        request_delay: float,
        threshold: int,
        runner: PricingRunner = inventory_pricer.price_backpack,
    ) -> None:
        self.timeout = timeout
        self.request_delay = request_delay
        self.threshold = threshold
        self._runner = runner
        self._updates: queue.SimpleQueue[PricingViewState] = queue.SimpleQueue()
        self._mutex = threading.Lock()
        self._cancel_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        with self._mutex:
            return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        with self._mutex:
            if self._thread is not None and self._thread.is_alive():
                return False
            while True:
                try:
                    self._updates.get_nowait()
                except queue.Empty:
                    break
            self._cancel_event = threading.Event()
            self._updates.put(
                PricingViewState(
                    phase="starting",
                    message="Starting background pricing",
                    running=True,
                    timestamp_ms=time.time_ns() // 1_000_000,
                    threshold=self.threshold,
                )
            )
            thread = threading.Thread(
                target=self._run,
                args=(self._cancel_event,),
                name="SpiritValePricing",
                daemon=True,
            )
            self._thread = thread
            thread.start()
            return True

    def _run(self, cancel_event: threading.Event) -> None:
        known: dict[str, Any] = {}

        def progress(event: dict[str, Any]) -> None:
            known.update(event)
            self._updates.put(pricing_state_from_progress(known, self.threshold))

        try:
            report = self._runner(
                timeout=self.timeout,
                request_delay=self.request_delay,
                threshold=self.threshold,
                progress=progress,
                cancel_check=cancel_event.is_set,
            )
        except inventory_pricer.PricingCancelled:
            known.update(
                phase="cancelled",
                message="Pricing cancelled",
                timestamp_ms=time.time_ns() // 1_000_000,
            )
            self._updates.put(pricing_state_from_progress(known, self.threshold))
        except Exception as error:
            known.update(
                phase="error",
                message=str(error),
                timestamp_ms=time.time_ns() // 1_000_000,
            )
            self._updates.put(pricing_state_from_progress(known, self.threshold))
        else:
            self._updates.put(pricing_state_from_report(report))

    def poll_latest(self) -> PricingViewState | None:
        latest = None
        while True:
            try:
                latest = self._updates.get_nowait()
            except queue.Empty:
                return latest

    def stop(self, join_timeout: float = 2.0) -> None:
        with self._mutex:
            cancel_event = self._cancel_event
            thread = self._thread
        cancel_event.set()
        if thread is not None and thread is not threading.current_thread():
            thread.join(max(0.0, join_timeout))


def pricing_radar_summary(state: PricingViewState) -> str:
    if state.phase == "complete":
        return (
            f"PRICE P{state.priced_count}/{state.eligible_equipment_count} "
            f"FAV-SKIP {state.favorite_skipped_count} "
            f"NO-EXACT {state.no_exact_sample_count} "
            f">{state.threshold:,} {state.over_threshold_count}"
        )
    if state.phase == "querying":
        return (
            f"PRICE QUERY {state.current}/{state.total} "
            f"FAV-SKIP {state.favorite_skipped_count}"
        )
    if state.phase == "error":
        return f"PRICE ERROR {state.message}"[:90]
    if state.phase == "cancelled":
        return "PRICE CANCELLED"
    if state.running:
        return f"PRICE {state.phase.replace('_', ' ').upper()}"
    return "PRICE IDLE - 選單重新查價"


@lru_cache(maxsize=16)
def _price_font(size: int, bold: bool = False):
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    candidates = (
        fonts / ("msjhbd.ttc" if bold else "msjh.ttc"),
        fonts / ("arialbd.ttf" if bold else "arial.ttf"),
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_price_text(draw, text: str, font, max_width: int) -> str:
    if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
        return text
    suffix = "…"
    shortened = text
    while shortened:
        shortened = shortened[:-1]
        candidate = shortened.rstrip() + suffix
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            return candidate
    return suffix


def draw_pricing_window(
    state: PricingViewState,
    page: int,
    rows_per_page: int,
    *,
    width: int = PRICE_WINDOW_WIDTH,
    height: int = PRICE_WINDOW_HEIGHT,
) -> tuple[np.ndarray, int, int]:
    """Render the standalone price window and return canvas/page/page-count."""

    rows_per_page = max(4, min(12, int(rows_per_page)))
    page_count = max(1, math.ceil(len(state.rows) / rows_per_page))
    page = max(0, min(int(page), page_count - 1))
    image = Image.new("RGB", (width, height), (17, 20, 27))
    draw = ImageDraw.Draw(image)
    title_font = _price_font(27, True)
    section_font = _price_font(16, True)
    body_font = _price_font(15)
    small_font = _price_font(13)

    draw.text((24, 18), "BACKPACK PRICES", font=title_font, fill=(232, 239, 248))
    if state.phase == "error":
        status_color = (255, 105, 105)
    elif state.running:
        status_color = (100, 195, 255)
    elif state.phase == "complete":
        status_color = (105, 225, 145)
    else:
        status_color = (160, 165, 175)
    status = state.message
    if state.phase == "querying" and state.total:
        status = f"Query {state.current}/{state.total}: {state.message}"
    draw.text(
        (25, 57),
        _fit_price_text(draw, status, body_font, width - 230),
        font=body_font,
        fill=status_color,
    )
    if state.timestamp_ms:
        updated = time.strftime(
            "%H:%M:%S", time.localtime(state.timestamp_ms / 1000)
        )
        draw.text(
            (width - 174, 58),
            f"Updated {updated}",
            font=small_font,
            fill=(145, 153, 166),
        )

    draw.rounded_rectangle((20, 88, width - 20, 139), 8, fill=(27, 32, 42))
    draw.text(
        (32, 98),
        f"TOTAL {state.equipment_count}   ELIGIBLE {state.eligible_equipment_count}   "
        f"FAVORITES SKIPPED {state.favorite_skipped_count}",
        font=section_font,
        fill=(202, 210, 222),
    )
    draw.text(
        (32, 119),
        f"PRICED {state.priced_count}   NO EXACT {state.no_exact_sample_count}   "
        f"OVER {state.threshold:,}: {state.over_threshold_count}",
        font=small_font,
        fill=(166, 178, 194),
    )

    row_top = 153
    footer_top = height - 55
    row_height = max(39, min(65, (footer_top - row_top - 4) // rows_per_page))
    visible_rows = state.rows[
        page * rows_per_page : (page + 1) * rows_per_page
    ]
    if not visible_rows:
        empty_message = (
            "Waiting for results…" if state.running else "No eligible equipment results"
        )
        draw.text(
            (width // 2, 320),
            empty_message,
            anchor="mm",
            font=section_font,
            fill=(135, 145, 160),
        )
    for index, row in enumerate(visible_rows):
        top = row_top + index * row_height
        bottom = top + row_height - 5
        fill = (29, 34, 44) if index % 2 == 0 else (25, 30, 39)
        draw.rounded_rectangle((20, top, width - 20, bottom), 6, fill=fill)
        price_color = (
            (255, 135, 68)
            if row.over_threshold
            else (105, 225, 145)
            if row.lowest_exact_price is not None
            else (145, 151, 162)
        )
        tag = "HIGH" if row.over_threshold else ""
        name = f"{tag + '  ' if tag else ''}{row.display_name}  x{row.quantity}"
        draw.text(
            (31, top + 6),
            _fit_price_text(draw, name, body_font, width - 260),
            font=body_font,
            fill=(232, 237, 244),
        )
        if row.lowest_exact_price is None:
            price_text = "NO EXACT SAMPLE"
        else:
            price_text = f"{row.lowest_exact_price:,}  (n={row.exact_listing_count})"
        price_width = draw.textbbox((0, 0), price_text, font=body_font)[2]
        draw.text(
            (width - 31 - price_width, top + 6),
            price_text,
            font=body_font,
            fill=price_color,
        )
        draw.text(
            (31, top + 29),
            _fit_price_text(draw, row.stat_text, small_font, width - 62),
            font=small_font,
            fill=(157, 175, 198),
        )

    previous_rect = (24, height - 43, 155, height - 13)
    next_rect = (width - 155, height - 43, width - 24, height - 13)
    draw.rounded_rectangle(previous_rect, 6, fill=(39, 48, 62))
    draw.rounded_rectangle(next_rect, 6, fill=(39, 48, 62))
    draw.text(
        ((previous_rect[0] + previous_rect[2]) // 2, height - 28),
        "Previous",
        anchor="mm",
        font=small_font,
        fill=(214, 222, 233),
    )
    draw.text(
        ((next_rect[0] + next_rect[2]) // 2, height - 28),
        "Next",
        anchor="mm",
        font=small_font,
        fill=(214, 222, 233),
    )
    draw.text(
        (width // 2, height - 28),
        f"Page {page + 1}/{page_count}  •  mouse wheel",
        anchor="mm",
        font=small_font,
        fill=(154, 165, 180),
    )
    canvas = np.asarray(image, dtype=np.uint8)[:, :, ::-1].copy()
    return canvas, page, page_count


def enable_dpi_awareness() -> None:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass






def prompt_follow_player_name(
    party_members: Iterable[MemoryPartyMember],
) -> str | None:
    """Show a native text-entry dialog containing only remote party members."""
    candidates = {
        member.display_name.strip() or member.player_id.strip()
        for member in party_members
        if member.player_id and not member.is_local
    }
    names = sorted(candidates, key=str.casefold)
    candidate_text = "、".join(names) if names else "目前隊伍沒有其他成員"
    try:
        import tkinter as tk
        from tkinter import simpledialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            value = simpledialog.askstring(
                "F2 跟隨玩家",
                "請輸入完整角色名稱（不分大小寫）。\n"
                f"目前同地圖的隊伍成員：{candidate_text}",
                parent=root,
            )
        finally:
            root.destroy()
    except Exception as error:
        print(f"F2：無法開啟名稱輸入視窗：{error}", flush=True)
        return None
    normalized = str(value).strip() if value is not None else ""
    return normalized or None


def show_summoner_check_settings(
    checks: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]] | None:
    """Edit the five persisted job-type-1 checks; return None on cancel."""
    try:
        import tkinter as tk
        from tkinter import messagebox, ttk

        current = normalize_summoner_checks(checks)
        result: list[dict[str, dict[str, object]] | None] = [None]
        root = tk.Tk()
        root.title("召喚／Buff 檢查設定")
        root.attributes("-topmost", True)
        root.resizable(False, False)
        enabled_vars: dict[str, Any] = {}
        key_vars: dict[str, Any] = {}
        display_keys = [f"NumPad {number}" for number in range(10)]

        tk.Label(
            root,
            text="勾選要維持的召喚物或 Buff，並指定右側數字鍵盤技能鍵。",
            justify="left",
            padx=12,
            pady=10,
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        tk.Label(root, text="檢查", padx=8).grid(row=1, column=0)
        tk.Label(root, text="項目", padx=8).grid(row=1, column=1, sticky="w")
        tk.Label(root, text="補回按鍵", padx=8).grid(row=1, column=2)

        for row, check_id in enumerate(SUMMONER_CHECK_ORDER, start=2):
            item = current[check_id]
            enabled_var = tk.BooleanVar(value=bool(item["enabled"]))
            key = str(item["key"])
            key_var = tk.StringVar(
                value=(f"NumPad {key[-1]}" if key in NUMPAD_SKILL_KEYS else "")
            )
            enabled_vars[check_id] = enabled_var
            key_vars[check_id] = key_var
            tk.Checkbutton(root, variable=enabled_var).grid(row=row, column=0)
            tk.Label(
                root,
                text=SUMMONER_CHECK_LABELS[check_id],
                anchor="w",
                width=25,
            ).grid(row=row, column=1, sticky="w", padx=4, pady=3)
            ttk.Combobox(
                root,
                textvariable=key_var,
                values=display_keys,
                state="readonly",
                width=12,
            ).grid(row=row, column=2, padx=8, pady=3)

        def _save() -> None:
            updated = default_summoner_checks()
            for check_id in SUMMONER_CHECK_ORDER:
                enabled = bool(enabled_vars[check_id].get())
                display_key = str(key_vars[check_id].get()).strip()
                if enabled and not display_key:
                    messagebox.showerror(
                        "缺少按鍵",
                        f"{SUMMONER_CHECK_LABELS[check_id]} 已啟用，請指定 NumPad 按鍵。",
                        parent=root,
                    )
                    return
                key = (
                    "numpad" + display_key.rsplit(" ", 1)[-1]
                    if display_key
                    else ""
                )
                updated[check_id] = {"enabled": enabled, "key": key}
            result[0] = normalize_summoner_checks(updated)
            root.destroy()

        button_row = 2 + len(SUMMONER_CHECK_ORDER)
        buttons = tk.Frame(root)
        buttons.grid(row=button_row, column=0, columnspan=3, pady=12)
        tk.Button(buttons, text="保存", width=12, command=_save).pack(
            side="left", padx=5
        )
        tk.Button(buttons, text="取消", width=12, command=root.destroy).pack(
            side="left", padx=5
        )
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.bind("<Escape>", lambda _event: root.destroy())
        root.update_idletasks()
        root.after(0, lambda: (root.lift(), root.focus_force()))
        root.mainloop()
        return result[0]
    except Exception as error:  # pragma: no cover - GUI failure fallback
        print(f"召喚／Buff 設定：無法開啟視窗：{error}", flush=True)
        return None


def show_loot_rarity_menu(current_rarity: str) -> str | None:
    """Choose and return the persisted minimum loot rarity; cancel is None."""
    choices = ("Common", "Rare", "Unique", "Legendary")
    current_value = loot_minimum_rarity_value(current_rarity)
    result: list[str | None] = [None]
    try:
        import tkinter as tk

        root = tk.Tk()
        root.title("拾取品質設定")
        root.attributes("-topmost", True)
        root.resizable(False, False)

        def _choose(rarity: str) -> None:
            result[0] = rarity
            root.destroy()

        tk.Label(
            root,
            text="選擇最低拾取品質；會拾取所選品質與更高品質的非裝備物品。",
            justify="left",
            padx=12,
            pady=10,
        ).pack(fill="x")
        for rarity in choices:
            value = LOOT_RARITY_VALUES[rarity.casefold()]
            label = f"{rarity} 以上"
            if rarity == "Common":
                label += "（全部品質）"
            if value == current_value:
                label += "　✓ 目前設定"
            tk.Button(
                root,
                text=label,
                width=36,
                anchor="w",
                padx=10,
                pady=4,
                command=lambda selected=rarity: _choose(selected),
            ).pack(fill="x", padx=12, pady=2)
        tk.Button(
            root,
            text="取消（不變更）",
            width=36,
            anchor="w",
            padx=10,
            pady=4,
            command=root.destroy,
        ).pack(fill="x", padx=12, pady=(6, 12))
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.bind("<Escape>", lambda _event: root.destroy())
        root.update_idletasks()
        root.after(0, lambda: (root.lift(), root.focus_force()))
        root.mainloop()
    except Exception as error:  # pragma: no cover - GUI failure fallback
        print(f"拾取品質設定：無法開啟視窗：{error}", flush=True)
        return None
    return result[0]


def show_control_menu(state: dict[str, Any]) -> str:
    """Show the single-hotkey control menu and return the chosen action code.

    All former function hotkeys (F2/F4/F5/F6/F7/F9/Del and the F8 navigation
    toggle) are consolidated here: F8 now only opens this menu, and every action
    is picked from it. Returns one of the action codes below, or "" when the
    user closes the menu without choosing anything.

    Recognized codes: "navigation", "summoner_checks", "follow", "loot",
    "loot_rarity", "filter", "card", "price_toggle", "reprice", "exit".

    ``state`` carries the current toggles and which optional features are
    available so unavailable buttons are hidden and every button can label its
    live on/off state.
    """
    result: list[str] = [""]

    def _on_off(flag: bool) -> str:
        return "開啟" if flag else "關閉"

    # (code, label) pairs; None entries are dropped so unavailable features
    # never render a button.
    nav_active = bool(state.get("navigation_active"))
    follow_mode = bool(state.get("follow_mode"))
    follow_name = str(state.get("follow_player_name") or "")
    loot_enabled = bool(state.get("loot_enabled"))
    loot_minimum_rarity = str(
        state.get("loot_minimum_rarity") or "Legendary"
    )
    price_visible = bool(state.get("price_window_visible"))

    entries: list[tuple[str, str]] = []
    entries.append(
        ("navigation", f"一般導航（目前{_on_off(nav_active)}）→ 切換")
    )
    if state.get("job_type") == 1:
        enabled_count = max(0, int(state.get("summoner_check_count", 0)))
        entries.append(
            (
                "summoner_checks",
                f"召喚／Buff 檢查設定（已啟用 {enabled_count}/{len(SUMMONER_CHECK_ORDER)}）",
            )
        )
    if state.get("follow_available"):
        if follow_mode:
            label = f"純跟隨模式（跟隨中：{follow_name or '玩家'}）→ 關閉"
        else:
            label = "純跟隨模式（目前關閉）→ 開啟並輸入名稱"
        entries.append(("follow", label))
    entries.append(("loot", f"內存拾取（目前{_on_off(loot_enabled)}）→ 切換"))
    entries.append(
        (
            "loot_rarity",
            f"拾取品質（目前 {loot_minimum_rarity} 以上）→ 設定",
        )
    )
    entries.append(("filter", "裝備詞條篩選表 → 開啟/關閉編輯器"))
    if state.get("card_available"):
        running = "，監看中" if state.get("card_running") else ""
        entries.append(("card", f"大量購買 Card 視窗{running}"))
    if state.get("price_window_available"):
        entries.append(
            (
                "price_toggle",
                f"價格視窗（目前{'顯示' if price_visible else '隱藏'}）→ 切換",
            )
        )
    if state.get("pricing_available"):
        running = "（查價進行中）" if state.get("pricing_running") else ""
        entries.append(("reprice", f"重新讀取背包並查價{running}"))
    entries.append(("exit", "安全結束程式（放開所有按鍵）"))

    try:
        import tkinter as tk

        root = tk.Tk()
        root.title("SpiritVale 控制選單")
        root.attributes("-topmost", True)
        root.resizable(False, False)

        def _choose(code: str) -> None:
            result[0] = code
            root.destroy()

        tk.Label(
            root,
            text="按 F8 隨時叫出此選單；選擇一項功能，其餘按鍵已整合於此。",
            justify="left",
            padx=12,
            pady=8,
        ).pack(fill="x")

        for code, label in entries:
            tk.Button(
                root,
                text=label,
                width=36,
                anchor="w",
                padx=10,
                pady=4,
                command=lambda c=code: _choose(c),
            ).pack(fill="x", padx=12, pady=2)

        tk.Button(
            root,
            text="關閉選單（不執行任何動作）",
            width=36,
            anchor="w",
            padx=10,
            pady=4,
            command=lambda: _choose(""),
        ).pack(fill="x", padx=12, pady=(6, 12))

        # Esc / window close both cancel without performing an action.
        root.protocol("WM_DELETE_WINDOW", lambda: _choose(""))
        root.bind("<Escape>", lambda _event: _choose(""))
        root.update_idletasks()
        root.after(0, lambda: (root.lift(), root.focus_force()))
        root.mainloop()
    except Exception as error:  # pragma: no cover - GUI failure fallback
        print(f"F8：無法開啟控制選單：{error}", flush=True)
        return ""
    return result[0]


def list_windows() -> list[tuple[int, str]]:
    windows: list[tuple[int, str]] = []

    def callback(hwnd: int, _: object) -> None:
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).strip()
            if title:
                windows.append((hwnd, title))

    win32gui.EnumWindows(callback, None)
    return windows


def find_window(title_fragment: str) -> tuple[int, str]:
    matches = [
        item
        for item in list_windows()
        if title_fragment.casefold() in item[1].casefold()
    ]
    if not matches:
        raise RuntimeError(
            f"找不到標題包含 {title_fragment!r} 的視窗；可先使用 --list-windows。"
        )
    exact = [item for item in matches if item[1].casefold() == title_fragment.casefold()]
    return (exact or matches)[0]


def viewport_to_client_point(
    viewport_position: tuple[float, float, float],
    client_width: int,
    client_height: int,
) -> tuple[int, int]:
    """Convert a visible Unity viewport point to Windows client coordinates."""
    x, y, z = viewport_position
    if (
        not all(math.isfinite(value) for value in viewport_position)
        or z <= 0.0
        or x < 0.0
        or x > 1.0
        or y < 0.0
        or y > 1.0
    ):
        raise ValueError("viewport position must be visible")
    if client_width <= 0 or client_height <= 0:
        raise ValueError("client dimensions must be positive")
    return (
        round(x * (client_width - 1)),
        round((1.0 - y) * (client_height - 1)),
    )


def monster_client_point(
    hwnd: int, monster: MemoryMonster
) -> tuple[int, int] | None:
    """Return a visible monster's client point, including for minimized windows."""
    if not monster.viewport_visible or monster.viewport_position is None:
        return None
    try:
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        return viewport_to_client_point(
            monster.viewport_position,
            right - left,
            bottom - top,
        )
    except (OSError, ValueError, win32gui.error):
        return None


def move_mouse_to_monster(hwnd: int, monster: MemoryMonster) -> bool:
    """Post a background mouse move without moving the physical Windows cursor."""
    client_point = monster_client_point(hwnd, monster)
    if client_point is None:
        return False
    x, y = client_point
    lparam = (x & 0xFFFF) | ((y & 0xFFFF) << 16)
    try:
        win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
        return True
    except (OSError, ValueError, win32gui.error):
        return False


def post_left_click_to_monster(hwnd: int, monster: MemoryMonster) -> bool:
    """Post one background left click at a visible monster without focusing it."""
    client_point = monster_client_point(hwnd, monster)
    if client_point is None:
        return False
    x, y = client_point
    lparam = (x & 0xFFFF) | ((y & 0xFFFF) << 16)
    down_sent = False
    try:
        win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
        win32gui.PostMessage(
            hwnd,
            win32con.WM_LBUTTONDOWN,
            win32con.MK_LBUTTON,
            lparam,
        )
        down_sent = True
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
        return True
    except (OSError, ValueError, win32gui.error):
        if down_sent:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
            except (OSError, ValueError, win32gui.error):
                pass
        return False


def post_key(hwnd: int, key: str, is_down: bool) -> None:
    vk = VK_BY_KEY[key]
    scan_code = win32api.MapVirtualKey(vk, 0)
    lparam = 1 | (scan_code << 16)
    message = win32con.WM_KEYDOWN
    if not is_down:
        message = win32con.WM_KEYUP
        lparam |= (1 << 30) | (1 << 31)
    win32gui.PostMessage(hwnd, message, vk, lparam)


def post_key_tap(hwnd: int, key: str, hold_ms: int = 50) -> None:
    """Send a background key tap and always release the key."""
    post_key(hwnd, key, True)
    try:
        time.sleep(max(0.0, hold_ms / 1000))
    finally:
        post_key(hwnd, key, False)


def key_transitions(
    held: Iterable[str], desired: Iterable[str]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    held_set, desired_set = set(held), set(desired)
    order = tuple(VK_BY_KEY)
    releases = tuple(key for key in reversed(order) if key in held_set - desired_set)
    presses = tuple(key for key in order if key in desired_set - held_set)
    return releases, presses


def update_held_keys(
    hwnd: int,
    held: set[str],
    desired: Iterable[str],
) -> set[str]:
    desired_set = set(desired)
    releases, presses = key_transitions(held, desired_set)
    for key in releases:
        if key in HELD_SHIFT_KEYS:
            continue
        post_key(hwnd, key, False)
    for key in presses:
        if key in HELD_SHIFT_KEYS:
            continue
        post_key(hwnd, key, True)
    return desired_set


def _radar_point(
    position: tuple[float, float, float],
    player_position: tuple[float, float, float],
    center: tuple[int, int],
    pixels_per_world: float,
) -> tuple[int, int]:
    return (
        round(center[0] + (position[0] - player_position[0]) * pixels_per_world),
        round(center[1] - (position[2] - player_position[2]) * pixels_per_world),
    )


def draw_memory_radar(
    snapshot: MemorySnapshot | None,
    target: MemoryMonster | None,
    keys: Iterable[str],
    active: bool,
    status: str,
    config: BotConfig,
    loot_target: MemoryLoot | None = None,
    pricing_summary: str = "",
    follow_player: MemoryObservedPlayer | None = None,
    follow_radius_world: float = 0.0,
) -> np.ndarray:
    size = max(360, int(config.radar_size_px))
    canvas = np.full((size, size, 3), (15, 17, 22), dtype=np.uint8)
    center = (size // 2, size // 2 + 20)
    cv2.putText(
        canvas,
        "MEMORY / NAVMESH",
        (20, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        (225, 235, 245),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        status[:80],
        (20, 59),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (140, 210, 255) if active else (150, 150, 150),
        1,
        cv2.LINE_AA,
    )
    if pricing_summary:
        cv2.putText(
            canvas,
            pricing_summary[:92],
            (20, 82),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (105, 220, 155),
            1,
            cv2.LINE_AA,
        )
    if snapshot is None:
        cv2.putText(
            canvas,
            "NO SAFE MEMORY SNAPSHOT - ALL KEYS RELEASED",
            (30, center[1]),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (80, 80, 255),
            2,
            cv2.LINE_AA,
        )
        return canvas

    positions = [monster.position for monster in snapshot.monsters]
    positions.extend(player.position for player in snapshot.players)
    positions.extend(loot.position for loot in snapshot.loots)
    positions.extend(map_exit.position for map_exit in snapshot.map_exits)
    positions.extend(snapshot.path.corners)
    distances = sorted(horizontal_distance(snapshot.player.position, p) for p in positions)
    visible_radius = max(12.0, distances[min(len(distances) - 1, 8)] * 1.15) if distances else 20.0
    if follow_player is not None:
        visible_radius = max(
            visible_radius,
            (
                horizontal_distance(snapshot.player.position, follow_player.position)
                + max(0.0, follow_radius_world)
            )
            * 1.1,
        )
    visible_radius = min(120.0, visible_radius)
    pixels_per_world = (size * 0.39) / visible_radius
    for radius_fraction in (0.25, 0.5, 0.75, 1.0):
        cv2.circle(
            canvas,
            center,
            round(size * 0.39 * radius_fraction),
            (48, 52, 60),
            1,
            cv2.LINE_AA,
        )

    path_points = [
        _radar_point(point, snapshot.player.position, center, pixels_per_world)
        for point in snapshot.path.corners
    ]
    for start, end in zip(path_points, path_points[1:]):
        cv2.line(canvas, start, end, (0, 210, 255), 2, cv2.LINE_AA)
    if path_points:
        cv2.line(canvas, center, path_points[0], (0, 150, 210), 1, cv2.LINE_AA)

    for map_exit in snapshot.map_exits:
        point = _radar_point(
            map_exit.position,
            snapshot.player.position,
            center,
            pixels_per_world,
        )
        keepout_radius = map_exit_avoidance_radius(
            snapshot.player,
            map_exit,
            config.map_exit_avoidance_padding_world,
        )
        cv2.circle(
            canvas,
            point,
            max(2, round(keepout_radius * pixels_per_world)),
            (50, 80, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.drawMarker(
            canvas,
            point,
            (50, 80, 255),
            cv2.MARKER_TILTED_CROSS,
            12,
            2,
            cv2.LINE_AA,
        )

    followed_object_id = follow_player.object_id if follow_player else None
    if follow_player is not None and follow_radius_world > 0:
        follow_center = _radar_point(
            follow_player.position,
            snapshot.player.position,
            center,
            pixels_per_world,
        )
        cv2.circle(
            canvas,
            follow_center,
            max(1, round(follow_radius_world * pixels_per_world)),
            (170, 125, 35),
            1,
            cv2.LINE_AA,
        )
    for observed_player in snapshot.players:
        point = _radar_point(
            observed_player.position,
            snapshot.player.position,
            center,
            pixels_per_world,
        )
        followed = observed_player.object_id == followed_object_id
        selected = observed_player.selected
        color = (255, 225, 65) if followed else (230, 180, 45)
        cv2.circle(
            canvas,
            point,
            9 if followed else (7 if selected else 5),
            color,
            2 if followed or selected else 1,
            cv2.LINE_AA,
        )

    target_id = target.object_id if target else None
    for monster in snapshot.monsters:
        point = _radar_point(
            monster.position, snapshot.player.position, center, pixels_per_world
        )
        selected = monster.object_id == target_id
        color = (255, 0, 255) if selected else (60, 70, 235)
        cv2.circle(canvas, point, 8 if selected else 5, color, 2 if selected else -1)
    loot_target_id = loot_target.object_id if loot_target else None
    loot_colors = {
        0: (190, 190, 190),
        1: (90, 220, 90),
        2: (220, 90, 220),
        3: (30, 170, 255),
    }
    for loot in snapshot.loots:
        point = _radar_point(
            loot.position, snapshot.player.position, center, pixels_per_world
        )
        selected = loot.object_id == loot_target_id
        color = loot_colors.get(loot.rarity_value, (200, 200, 200))
        radius = 9 if selected else 5
        vertices = np.array(
            [
                (point[0], point[1] - radius),
                (point[0] + radius, point[1]),
                (point[0], point[1] + radius),
                (point[0] - radius, point[1]),
            ],
            dtype=np.int32,
        )
        cv2.polylines(canvas, [vertices], True, color, 2 if selected else 1)
    cv2.circle(canvas, center, 8, (255, 220, 40), -1, cv2.LINE_AA)
    forward = snapshot.player.camera_forward_xz
    forward_tip = (
        round(center[0] + forward[0] * 38),
        round(center[1] - forward[1] * 38),
    )
    cv2.arrowedLine(canvas, center, forward_tip, (60, 240, 100), 2, tipLength=0.3)

    if follow_player is not None:
        follow_distance = horizontal_distance(
            snapshot.player.position, follow_player.position
        )
        cv2.putText(
            canvas,
            (
                f"FOLLOW {follow_player.display_name or follow_player.player_id} "
                f"D={follow_distance:.2f} R={max(0.0, follow_radius_world):.1f}"
            )[:88],
            (20, size - 76),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.46,
            (255, 225, 90),
            1,
            cv2.LINE_AA,
        )

    target_text = "TARGET NONE"
    if target is not None:
        target_text = (
            f"TARGET {target.object_id} {target.display_name or target.config_id} "
            f"D={horizontal_distance(snapshot.player.position, target.position):.2f}"
        )
    cv2.putText(
        canvas,
        target_text[:88],
        (20, size - 52),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (220, 205, 255),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        f"MAP {snapshot.map_id}/{snapshot.instance_id}  ENEMIES {len(snapshot.monsters)}  "
        f"LOOT {len(snapshot.loots)}  EXIT {len(snapshot.map_exits)}  "
        f"PATH {snapshot.path.status.upper()}  KEYS {''.join(keys).upper() or '-'}",
        (20, size - 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.46,
        (190, 200, 210),
        1,
        cv2.LINE_AA,
    )
    return canvas


def run_bot(
    hwnd: int,
    config: BotConfig,
    send_input: bool,
    *,
    config_path: Path = CONFIG_PATH,
    mode: int = 1,
    state_path: Path = MEMORY_STATE_PATH,
    request_path: Path = NAVIGATION_REQUEST_PATH,
    disable_loot: bool = False,
    lock_mouse_to_monster: bool = False,
    left_click_after_mouse_lock: bool = False,
    boss_name: str = "",
    boss_summon_item_name: str = "",
    boss_spawn_timeout_sec: float = 10.0,
    boss_death_confirm_sec: float = 1.0,
    boss_loot_settle_sec: float = 3.0,
    boss_use_key_release_settle_sec: float = 0.25,
) -> None:
    if mode not in MODE_NAMES:
        raise ValueError("mode must be 1 (normal), 2 (train), or 3 (boss farm)")
    if mode == 3 and not str(boss_name).strip():
        raise ValueError("boss_name is required for mode 3")
    if mode == 3 and not str(boss_summon_item_name).strip():
        raise ValueError("boss_summon_item_name is required for mode 3")
    if any(
        not math.isfinite(value) or value < 0
        for value in (
            boss_spawn_timeout_sec,
            boss_death_confirm_sec,
            boss_loot_settle_sec,
            boss_use_key_release_settle_sec,
        )
    ):
        raise ValueError("boss farm timing settings must be finite and non-negative")
    if type(config.job_type) is not int or config.job_type not in (0, 1, 2):
        raise ValueError(
            "job_type must be 0 (under level 64), 1 (summoner), or 2 (priest)"
        )
    if config.summon_reanimation_key not in VK_BY_KEY:
        raise ValueError("summon_reanimation_key is not a supported key")
    if config.summon_mount_key not in VK_BY_KEY:
        raise ValueError("summon_mount_key is not a supported key")
    config.summoner_checks = normalize_summoner_checks(config.summoner_checks)
    if min(
        config.priest_left_shift_tap_hold_ms,
        config.priest_left_shift_tap_min_interval_ms,
        config.priest_left_shift_tap_max_interval_ms,
        config.summon_skill_key_hold_ms,
        config.summon_reanimation_delay_ms,
        config.summon_mount_confirm_timeout_ms,
        config.summon_mount_key_retry_delay_ms,
        config.summon_mount_retry_delay_ms,
        config.summoner_check_settle_ms,
        config.summoner_check_retry_delay_ms,
    ) < 0:
        raise ValueError("key timing settings must be non-negative")
    if (
        config.priest_left_shift_tap_min_interval_ms
        > config.priest_left_shift_tap_max_interval_ms
    ):
        raise ValueError(
            "priest Left Shift minimum interval cannot exceed maximum interval"
        )
    if config.pricing_enabled and (
        config.pricing_timeout_sec <= 0 or config.pricing_request_delay_sec < 0
    ):
        raise ValueError(
            "pricing_timeout_sec must be positive and "
            "pricing_request_delay_sec cannot be negative"
        )
    if config.follow_player_enabled and (
        config.follow_monster_radius_world < 0
        or config.follow_player_stop_padding_world < 0
        or config.follow_player_rejoin_distance_world < 0
    ):
        raise ValueError("follow-player distances must be non-negative")
    if config.memory_loot_pickup_hysteresis_world < 0:
        raise ValueError(
            "memory_loot_pickup_hysteresis_world must be non-negative"
        )
    # Mouse locking is controlled only by the mode configuration. Job-specific
    # behavior must not silently override the user's cursor preference.
    effective_mouse_lock = lock_mouse_to_monster
    menu_items: list[str] = ["一般導航"]
    if config.follow_player_enabled:
        menu_items.append("純跟隨")
    menu_items.append("內存拾取")
    menu_items.append("拾取品質")
    menu_items.append("裝備篩選表")
    if send_input:
        menu_items.append("大量購買 Card")
    if config.pricing_enabled:
        menu_items.extend(["價格視窗", "重新查價"])
    menu_items.append("安全結束")
    print(
        "唯一快捷鍵 F8（需先讓此遊戲視窗在前景，多開時只有前景的實例會回應）："
        "叫出控制選單，於選單內選擇 "
        + "、".join(menu_items)
        + "。",
        flush=True,
    )
    print(
        "啟動狀態：一般導航"
        + ("關閉（於選單開啟）" if config.start_paused else "開啟")
        + "。",
        flush=True,
    )
    print(f"模式：{'背景 WASD' if send_input else '預覽（不送按鍵）'}", flush=True)
    print(
        f"移動模式：{mode} {MODE_NAMES[mode]}"
        + (
            "（抵達後等待怪物死亡）"
            if mode == 1
            else "（抵達後立刻換下一隻）"
            if mode == 2
            else f"（只打 {boss_name}；使用 {boss_summon_item_name} 召喚）"
        ),
        flush=True,
    )
    print(
        "一般導航怪物滑鼠鎖定："
        + ("開啟" if effective_mouse_lock else "關閉")
        + "。",
        flush=True,
    )
    print(
        "鎖定新怪物後背景左鍵："
        + ("開啟" if left_click_after_mouse_lock else "關閉")
        + "。",
        flush=True,
    )
    print("導航來源：遊戲內存敵怪座標 + Unity NavMesh；不辨識小地圖。", flush=True)
    print(
        f"職業類型：{config.job_type} {JOB_TYPE_LABELS[config.job_type]}"
        + (
            "（找路前固定按 "
            f"{config.summon_reanimation_key}，再按 "
            f"{config.summon_mount_key} 上坐騎）"
            if config.job_type == 1
            else (
                "（一般導航鎖怪後每 "
                f"{config.priest_left_shift_tap_min_interval_ms}-"
                f"{config.priest_left_shift_tap_max_interval_ms} ms "
                "短按 Left Shift）"
                if config.job_type == 2
                else ""
            )
        )
        + "。",
        flush=True,
    )
    loot_enabled = not disable_loot
    print(
        f"掉落物來源：遊戲內存（{config.memory_loot_min_rarity} 以上）；"
        f"{'開啟' if loot_enabled else '關閉'}，"
        f"自己的物品可主動導航；別人或公開物品只在 "
        f"{config.memory_loot_max_distance_world:.1f} 世界單位內拾取"
        "（裝備一律排除）。",
        flush=True,
    )
    if config.follow_player_enabled:
        print(
            "純跟隨模式：於 F8 選單選「純跟隨」後輸入同地圖隊伍成員的完整角色名稱；"
            "只讀取隊伍名單，不掃描全部玩家，"
            "同地圖隊員不同頻時會自動切頻，不需開啟一般導航，且不會打怪或拾取。",
            flush=True,
        )

    pricing_controller = (
        PricingController(
            timeout=float(config.pricing_timeout_sec),
            request_delay=float(config.pricing_request_delay_sec),
            threshold=int(config.pricing_high_value_threshold),
        )
        if config.pricing_enabled
        else None
    )
    pricing_state = PricingViewState(
        threshold=int(config.pricing_high_value_threshold)
    )
    card_purchase_controller = (
        card_buyer.CardPurchaseController() if send_input else None
    )
    card_purchase_window = (
        card_buyer.CardPurchaseWindow(card_purchase_controller)
        if card_purchase_controller is not None
        else None
    )
    card_purchase_state = card_buyer.CardPurchaseState()
    equipment_filter_controller = equipment_filter.EquipmentFilterController()
    equipment_filter_editor = equipment_filter.EquipmentFilterEditor(
        run_now=equipment_filter_controller.request_immediate
    )
    equipment_filter_state = equipment_filter.EquipmentFilterState()
    price_window_visible = False
    price_window_created = False
    price_page = 0
    price_page_count = 1
    price_render_key: tuple[Any, ...] | None = None
    price_canvas: np.ndarray | None = None
    # Single control hotkey: F8 only opens the consolidated control menu.
    # Every former function key (F2/F4/F5/F6/F7/F9/Del) is now a menu entry.
    menu_was_down = control_menu_hotkey_down(hwnd)
    active = not config.start_paused
    input_allowed = False
    held_keys: set[str] = set()
    tapped_shift_keys: set[str] = set()
    snapshot: MemorySnapshot | None = None
    target: MemoryMonster | None = None
    follow_mode = False
    follow_discovery_active = False
    follow_player_id = ""
    follow_player_name = ""
    follow_player_object_id: int | None = None
    followed_player: MemoryObservedPlayer | None = None
    follow_channel_request_id = 0
    last_follow_channel_request_at = -math.inf
    channel_switch_request_id = 0
    channel_switch_index = -1
    last_channel_switch_at = -math.inf
    request_publisher = NavigationRequestPublisher(request_path)
    request_id = 0
    requested_target_kind = "none"
    requested_target_id = 0
    pending_summon_action = ""
    pending_skill_key_request_id = 0
    pending_skill_key = ""
    pending_skill_key_target_summon = False
    pending_loot_interact = 0
    pending_loot_interact_object_id = 0
    pending_consumable_use_request_id = 0
    pending_consumable_name = ""
    skipped_until: dict[int, float] = {}
    combat_blocked_object_ids: set[int] = set()
    combat_blocked_absent_since: dict[int, float] = {}
    combat_watchdog = CombatWatchdogState()
    combat_reengage_side = "a"
    map_identity: tuple[int, int] | None = None
    chase_started_at = time.monotonic()
    path_invalid_since: float | None = None
    progress_anchor: tuple[float, float, float] | None = None
    progress_started_at = time.monotonic()
    unstuck_started_at: float | None = None
    unstuck_anchor: tuple[float, float, float] | None = None
    unstuck_attempt = 0
    unstuck_side = "a"
    loot_candidate_object_id: int | None = None
    loot_candidate_frames = 0
    loot_clear_frames = 0
    memory_loot_active = False
    loot_skipped_until: dict[int, float] = {}
    loot_chase = LootChaseState()
    observed_loot_object_ids: set[int] = set()
    last_loot_interact = -math.inf
    last_status_log = ""
    last_status_log_at = -math.inf
    status = "STARTING"
    summon_mount_keys = SummonMountKeyState()
    summoner_check_state = SummonerCheckState()
    navigation_earnings = NavigationEarningsState()
    boss_farm = BossFarmState()
    mouse_click_completed_for_target = False
    priest_shift_next_tap_at = -math.inf
    if send_input and active:
        start_navigation_earnings(
            navigation_earnings, now=time.monotonic(), tracking=True
        )

    if config.debug_window:
        cv2.namedWindow(RADAR_WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(RADAR_WINDOW_NAME, config.radar_size_px, config.radar_size_px)

    def set_keys(desired: Iterable[str]) -> None:
        nonlocal held_keys
        held_keys = update_held_keys(
            hwnd,
            held_keys,
            desired if send_input and input_allowed else (),
        )
        publish_navigation_intent(requested_target_id, requested_target_kind)

    def tap_game_key(key: str, hold_ms: int) -> bool:
        """Send one game key only while the latest local-player state is alive."""
        nonlocal pending_summon_action, pending_loot_interact
        if not send_input or not input_allowed:
            return False
        if key in HELD_SHIFT_KEYS:
            tapped_shift_keys.add(key)
            publish_navigation_intent(requested_target_id, requested_target_kind)
            try:
                time.sleep(max(0.0, hold_ms / 1000))
            finally:
                tapped_shift_keys.discard(key)
                publish_navigation_intent(requested_target_id, requested_target_kind)
            return True
        summon_action = ""
        if key == config.summon_reanimation_key:
            summon_action = "reanimation"
        elif key == config.summon_mount_key:
            summon_action = "mount"
        if summon_action:
            # Route summon/mount through the probe (IPC intent) instead of a
            # background keypress: Unity ignores PostMessage'd keys for an
            # unfocused window, so the probe fires the bound hotkey in-game.
            pending_summon_action = summon_action
            publish_navigation_intent(requested_target_id, requested_target_kind)
            try:
                time.sleep(max(0.0, hold_ms / 1000))
            finally:
                pending_summon_action = ""
                publish_navigation_intent(requested_target_id, requested_target_kind)
            return True
        post_key_tap(hwnd, key, hold_ms)
        return True

    def request_loot_pickup(object_id: int) -> bool:
        # Route loot pickup through the probe (IPC intent) instead of a
        # background keypress: Unity ignores PostMessage'd keys for an
        # unfocused window, so the probe fires LootDrop.Interact in-game.
        # A monotonic counter lets the probe edge-detect each pickup even when
        # navigation requests coalesce; the object id is carried separately
        # because movement (and the nav target) are intentionally cleared to 0
        # before pickup so the player stops moving.
        nonlocal pending_loot_interact, pending_loot_interact_object_id
        if not send_input or not input_allowed:
            return False
        if int(object_id) <= 0:
            return False
        pending_loot_interact += 1
        pending_loot_interact_object_id = int(object_id)
        publish_navigation_intent(requested_target_id, requested_target_kind)
        return True

    def request_skill_key(key: str, target_summon: bool = False) -> bool:
        """Ask the probe to click a NumPad-bound skill once in-process.

        ``target_summon`` routes the cast at one of the player's own summons:
        the probe verifies ownership and processes the skill and summon UnitId
        together. Guardian Bond completion comes from its outgoing bond entry.
        """
        nonlocal pending_skill_key_request_id, pending_skill_key
        nonlocal pending_skill_key_target_summon
        if not send_input or not input_allowed:
            return False
        normalized = str(key).strip().casefold()
        if normalized not in NUMPAD_SKILL_KEYS:
            return False
        pending_skill_key_request_id = max(
            pending_skill_key_request_id + 1,
            int(time.time() * 1000),
        )
        pending_skill_key = normalized
        pending_skill_key_target_summon = bool(target_summon)
        publish_navigation_intent(requested_target_id, requested_target_kind)
        return True

    def publish_navigation_intent(
        object_id: int, target_kind: str = "monster", *, force: bool = False
    ) -> None:
        """Translate current mode/input state into one complete probe request."""
        nonlocal request_id, requested_target_kind, requested_target_id
        write_now = time.monotonic()
        normalized_kind = "none" if object_id <= 0 else target_kind
        party_follow_active = bool(follow_discovery_active or follow_mode)
        probe_active = bool(active and not party_follow_active)
        loot_scan_active = bool(probe_active and (loot_enabled or mode == 3))
        bot_active = bool(send_input and (active or follow_mode))
        movement_keys = tuple(
            key for key in ("w", "a", "s", "d") if key in held_keys
        )
        shift_keys = tuple(
            key
            for key in HELD_SHIFT_KEYS
            if key in held_keys or key in tapped_shift_keys
        )
        focus_target_object_id = 0
        focus_target_world = (0.0, 0.0, 0.0)
        if (
            effective_mouse_lock
            and send_input
            and input_allowed
            and normalized_kind == "monster"
            and target is not None
            and target.object_id == object_id
            and target.viewport_visible
            and target.viewport_position is not None
        ):
            focus_target_object_id = target.object_id
            focus_target_world = target.position
        request_publisher.publish(
            object_id, normalized_kind, now=write_now, force=force,
            writer=write_navigation_request,
            probe_active=probe_active,
            loot_scan_active=loot_scan_active,
            party_follow_active=party_follow_active,
            bot_active=bot_active,
            movement_keys=movement_keys,
            movement_world=movement_world_for_keys(
                movement_keys, snapshot.player if snapshot is not None else None
            ),
            shift_keys=shift_keys,
            focus_target_object_id=focus_target_object_id,
            focus_target_world=focus_target_world,
            background_input_mode=os.environ.get(
                "SPIRITVALE_BACKGROUND_INPUT_MODE", "send_process"
            ),
            background_skill_mode=os.environ.get(
                "SPIRITVALE_BACKGROUND_SKILL_MODE", "capture"
            ),
            auto_relogin_enabled=config.auto_relogin_enabled,
            auto_relogin_disconnect_grace_sec=config.auto_relogin_disconnect_grace_sec,
            auto_relogin_builtin_wait_max_sec=config.auto_relogin_builtin_wait_max_sec,
            auto_relogin_attempt_timeout_sec=config.auto_relogin_attempt_timeout_sec,
            auto_relogin_retry_delay_sec=config.auto_relogin_retry_delay_sec,
            auto_relogin_max_attempts=config.auto_relogin_max_attempts,
            follow_channel_request_id=follow_channel_request_id,
            follow_player_id=follow_player_id,
            channel_switch_request_id=channel_switch_request_id,
            channel_switch_index=channel_switch_index,
            consumable_use_request_id=pending_consumable_use_request_id,
            consumable_name=pending_consumable_name,
            summon_action=pending_summon_action,
            skill_key_request_id=pending_skill_key_request_id,
            skill_key=pending_skill_key,
            skill_key_target_summon=pending_skill_key_target_summon,
            loot_interact=pending_loot_interact,
            loot_interact_object_id=pending_loot_interact_object_id,
        )
        request_id = request_publisher.request_id
        requested_target_id = request_publisher.target_object_id
        requested_target_kind = request_publisher.target_kind


    def request_consumable_use(name: str) -> int:
        nonlocal pending_consumable_use_request_id, pending_consumable_name
        pending_consumable_use_request_id = max(
            pending_consumable_use_request_id + 1,
            int(time.time() * 1000),
        )
        pending_consumable_name = str(name).strip()
        publish_navigation_intent(0)
        return pending_consumable_use_request_id

    def request_channel_switch(index: int) -> None:
        """Ask the probe to hop to a 0-based channel index and flush the request."""
        nonlocal channel_switch_request_id, channel_switch_index
        nonlocal last_channel_switch_at
        channel_switch_index = int(index)
        channel_switch_request_id = max(
            channel_switch_request_id + 1, int(time.time() * 1000)
        )
        last_channel_switch_at = time.monotonic()
        publish_navigation_intent(requested_target_id, requested_target_kind)

    def update_summon_mount_keys(player: MemoryPlayer, now: float) -> bool:
        enabled = summon_mount_blocks_navigation(
            config,
            player,
            send_input=send_input,
            active=active or follow_mode,
        )
        return advance_summon_mount_hotkeys(
            summon_mount_keys,
            mounted=player.is_mounted_summon,
            summon_ready=(
                player.has_primary_summon
                or bool(player.summon_id)
                or player.active_summon_count > 0
            ),
            enabled=enabled,
            now=now,
            reanimation_key=config.summon_reanimation_key,
            mount_key=config.summon_mount_key,
            key_hold_ms=config.summon_skill_key_hold_ms,
            reanimation_delay_ms=config.summon_reanimation_delay_ms,
            confirm_timeout_ms=config.summon_mount_confirm_timeout_ms,
            mount_key_retry_delay_ms=config.summon_mount_key_retry_delay_ms,
            retry_delay_ms=config.summon_mount_retry_delay_ms,
            press_key=tap_game_key,
        )

    def announce(
        message: str,
        *,
        force: bool = False,
        dedupe_key: str | None = None,
    ) -> None:
        nonlocal last_status_log, last_status_log_at
        now = time.monotonic()
        log_key = message if dedupe_key is None else dedupe_key
        if force or log_key != last_status_log or now - last_status_log_at >= 5.0:
            print(message, flush=True)
            last_status_log = log_key
            last_status_log_at = now

    def observe_earnings_snapshot(current: MemorySnapshot) -> None:
        observe_navigation_wallet(
            navigation_earnings,
            snapshot_timestamp_ms=current.timestamp_ms,
            wallet_coins_available=current.player.wallet_coins_available,
            wallet_coins=current.player.wallet_coins,
        )

    def finalize_navigation_statistics(*, refresh_wallet: bool) -> None:
        nonlocal snapshot
        if not navigation_earnings.session_active:
            return
        if refresh_wallet and navigation_earnings.tracking_active:
            set_keys(())
            requested_at_ms = int(time.time() * 1000)
            publish_navigation_intent(0, force=True)
            try:
                snapshot = wait_for_wallet_snapshot(
                    state_path,
                    config.memory_snapshot_timeout_ms,
                    after_timestamp_ms=requested_at_ms,
                    snapshot_reader=load_memory_snapshot,
                    wait_timeout_ms=1000,
                    avoid_boss=config.avoid_boss and mode != 3,
                )
                observe_earnings_snapshot(snapshot)
            except SnapshotUnavailable:
                mark_navigation_earnings_incomplete(
                    navigation_earnings, final_balance_from_last_sample=True
                )
        report = finish_navigation_earnings(
            navigation_earnings, now=time.monotonic()
        )
        if report is not None:
            print(format_navigation_earnings_report(report), flush=True)

    def pause_boss_farm(reason: str) -> None:
        nonlocal active, target
        boss_farm.phase = "fault"
        boss_farm.fault = str(reason)
        boss_farm.key_release_started_at = None
        target = None
        reset_combat_watchdog(combat_watchdog, None, time.monotonic())
        set_keys(())
        finalize_navigation_statistics(refresh_wallet=True)
        active = False
        publish_navigation_intent(0, force=True)
        announce(
            "MODE 3 SAFE PAUSE - " + boss_farm.fault,
            force=True,
        )

    def close_price_window() -> None:
        nonlocal price_window_created
        if not price_window_created:
            return
        try:
            cv2.destroyWindow(PRICE_WINDOW_NAME)
        except cv2.error:
            pass
        price_window_created = False

    def price_window_mouse(
        event: int, x: int, y: int, flags: int, _parameter: object
    ) -> None:
        nonlocal price_page
        if event == cv2.EVENT_MOUSEWHEEL:
            if hasattr(cv2, "getMouseWheelDelta"):
                delta = cv2.getMouseWheelDelta(flags)
            else:
                delta = (flags >> 16) & 0xFFFF
                if delta & 0x8000:
                    delta -= 0x10000
            price_page += -1 if delta > 0 else 1
        elif event == cv2.EVENT_LBUTTONDOWN and y >= PRICE_WINDOW_HEIGHT - 55:
            if x <= 175:
                price_page -= 1
            elif x >= PRICE_WINDOW_WIDTH - 175:
                price_page += 1
        price_page = max(0, min(price_page, price_page_count - 1))

    def poll_pricing() -> None:
        nonlocal pricing_state, price_page
        if pricing_controller is None:
            return
        update = pricing_controller.poll_latest()
        if update is None:
            return
        old_phase = pricing_state.phase
        pricing_state = update
        if update.phase == "complete":
            price_page = 0
            if old_phase != "complete":
                announce(
                    f"查價完成：定價 {update.priced_count}、"
                    f"收藏略過 {update.favorite_skipped_count}、"
                    f"無樣本 {update.no_exact_sample_count}、"
                    f"超過 {update.threshold:,} 為 {update.over_threshold_count}。",
                    force=True,
                )
        elif update.phase == "error" and old_phase != "error":
            announce(f"查價失敗：{update.message}", force=True)

    def poll_card_purchase() -> None:
        nonlocal card_purchase_state
        if card_purchase_controller is None:
            return
        update = card_purchase_controller.poll_latest()
        if update is None:
            return
        previous = card_purchase_state
        card_purchase_state = update
        if update.purchased_quantity > previous.purchased_quantity:
            announce(
                f"購買：成交 {update.item_display_name or 'Card'} "
                f"x{update.quantity:,}，單價 {update.unit_price:,}；"
                f"累計 {update.purchased_quantity:,} 張、花費 "
                f"{update.total_spent:,}。",
                force=True,
            )
        if (
            update.phase in {"budget_exhausted", "stopped"}
            and previous.phase != update.phase
        ):
            announce(
                f"購買：{update.message} 累計購買 {update.purchased_quantity:,} 張、"
                f"花費 {update.total_spent:,}。",
                force=True,
            )
        elif (
            update.phase in {"error", "timeout", "unknown"}
            and previous.phase != update.phase
        ):
            detail = update.message or update.code or "未知錯誤"
            announce(f"購買：大量購買已停止：{detail}", force=True)

    def poll_equipment_filter() -> None:
        nonlocal equipment_filter_state
        update = equipment_filter_controller.poll_latest()
        if update is None:
            return
        previous = equipment_filter_state
        equipment_filter_state = update
        equipment_filter_editor.set_status(update.message)
        changed_terminal = (
            update.phase in {"complete", "error"}
            and (
                update.phase != previous.phase
                or update.timestamp_ms != previous.timestamp_ms
            )
        )
        if not changed_terminal:
            return
        if update.phase == "complete":
            announce(
                "裝備篩選完成："
                f"掃描 {update.scanned}、保留 {update.kept}、"
                f"收藏保護 {update.protected}、"
                f"未設定略過 {update.skipped}、"
                f"新收藏 {update.favorited}、分解 {update.dismantled}"
                f"（無條件 {update.forced_dismantled}）、"
                f"錯誤 {update.errors}。",
                force=True,
            )
        else:
            announce(f"裝備篩選失敗：{update.message}", force=True)

    def render_price_window() -> None:
        nonlocal price_window_created, price_window_visible
        nonlocal price_page, price_page_count
        nonlocal price_render_key, price_canvas
        if not price_window_visible:
            return
        if price_window_created:
            try:
                if cv2.getWindowProperty(PRICE_WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    price_window_created = False
                    price_window_visible = False
                    return
            except cv2.error:
                price_window_created = False
        if not price_window_created:
            cv2.namedWindow(PRICE_WINDOW_NAME, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(
                PRICE_WINDOW_NAME, PRICE_WINDOW_WIDTH, PRICE_WINDOW_HEIGHT
            )
            cv2.setMouseCallback(PRICE_WINDOW_NAME, price_window_mouse)
            price_window_created = True
        render_key = (pricing_state, price_page, int(config.pricing_page_rows))
        if price_canvas is None or render_key != price_render_key:
            price_canvas, price_page, price_page_count = draw_pricing_window(
                pricing_state,
                price_page,
                int(config.pricing_page_rows),
            )
            price_render_key = (
                pricing_state,
                price_page,
                int(config.pricing_page_rows),
            )
        cv2.imshow(PRICE_WINDOW_NAME, price_canvas)

    def draw_radar(
        radar_snapshot: MemorySnapshot | None,
        radar_target: MemoryMonster | None,
        radar_keys: Iterable[str],
        radar_active: bool,
        radar_status: str,
        radar_config: BotConfig,
        radar_loot_target: MemoryLoot | None = None,
    ) -> np.ndarray:
        return draw_memory_radar(
            radar_snapshot,
            radar_target,
            radar_keys,
            radar_active,
            radar_status,
            radar_config,
            radar_loot_target,
            pricing_radar_summary(pricing_state),
            followed_player if follow_mode else None,
            0.0,
        )

    if pricing_controller is not None and config.pricing_auto_start:
        pricing_controller.start()
        print("背包查價已在背景啟動；收藏裝備會直接略過。", flush=True)
    equipment_filter_controller.start()

    try:
        publish_navigation_intent(0)
        while win32gui.IsWindow(hwnd):
            now = time.monotonic()
            # F8 is the only hotkey. Its rising edge opens the control menu,
            # which returns exactly one action code to run this frame.
            menu_down = control_menu_hotkey_down(hwnd)
            menu_action = ""
            if menu_down and not menu_was_down:
                menu_action = show_control_menu(
                    {
                        "navigation_active": active,
                        "follow_mode": follow_mode,
                        "follow_player_name": follow_player_name,
                        "loot_enabled": loot_enabled,
                        "loot_minimum_rarity": config.memory_loot_min_rarity,
                        "price_window_visible": price_window_visible,
                        "follow_available": config.follow_player_enabled,
                        "card_available": (
                            card_purchase_controller is not None
                            and card_purchase_window is not None
                        ),
                        "card_running": bool(
                            getattr(card_purchase_controller, "running", False)
                        ),
                        "pricing_available": pricing_controller is not None,
                        "pricing_running": bool(
                            getattr(pricing_controller, "running", False)
                        ),
                        "price_window_available": (
                            pricing_controller is not None
                            and config.pricing_window_enabled
                        ),
                        "job_type": config.job_type,
                        "summoner_check_count": sum(
                            1
                            for check_id in SUMMONER_CHECK_ORDER
                            if bool(config.summoner_checks[check_id]["enabled"])
                        ),
                    }
                )
                # The menu can block briefly; refresh the frame clock so the
                # action bodies below reset timers against the current time.
                now = time.monotonic()
            menu_was_down = menu_down
            if menu_action == "exit":
                finalize_navigation_statistics(
                    refresh_wallet=not follow_mode
                )
                purchase_stopping = (
                    card_purchase_controller is not None
                    and card_purchase_controller.request_stop()
                )
                announce(
                    "選單：安全結束。"
                    + (
                        " 大量購買已停止建立新要求；已送出的單筆交易仍會等待結果。"
                        if purchase_stopping
                        else ""
                    ),
                    force=True,
                )
                if purchase_stopping and card_purchase_controller is not None:
                    set_keys(())
                    wait_deadline = time.monotonic() + float(
                        getattr(card_purchase_controller, "timeout", 45.0)
                    ) + 1.0
                    while (
                        card_purchase_controller.running
                        and time.monotonic() < wait_deadline
                    ):
                        poll_card_purchase()
                        time.sleep(0.05)
                    poll_card_purchase()
                break
            if menu_action == "filter":
                equipment_filter_editor.toggle()
                announce("選單：裝備詞條篩選表已切換。", force=True)
            if menu_action == "summoner_checks" and config.job_type == 1:
                updated_checks = show_summoner_check_settings(
                    config.summoner_checks
                )
                if updated_checks is not None:
                    config.summoner_checks = updated_checks
                    save_config(config_path, config)
                    reset_summoner_check_state(summoner_check_state)
                    enabled_count = sum(
                        1
                        for check_id in SUMMONER_CHECK_ORDER
                        if bool(config.summoner_checks[check_id]["enabled"])
                    )
                    announce(
                        f"選單：召喚／Buff 檢查設定已保存，啟用 {enabled_count}/{len(SUMMONER_CHECK_ORDER)}。",
                        force=True,
                    )
            if (
                menu_action == "card"
                and card_purchase_controller is not None
                and card_purchase_window is not None
            ):
                set_keys(())
                card_purchase_window.show()
                announce(
                    "選單：大量購買視窗已顯示。"
                    + ("目前監看仍在執行。" if card_purchase_controller.running else ""),
                    force=True,
                )
            if menu_action == "price_toggle":
                price_window_visible = not price_window_visible
                if not price_window_visible:
                    close_price_window()
                announce(
                    f"選單：價格視窗{'顯示' if price_window_visible else '隱藏'}。",
                    force=True,
                )
            if menu_action == "reprice" and pricing_controller is not None:
                if pricing_controller.start():
                    price_page = 0
                    price_window_visible = bool(config.pricing_window_enabled)
                    announce("選單：已在背景重新讀取背包並查價。", force=True)
                else:
                    announce("選單：查價仍在進行，本次不重複啟動。", force=True)
            if menu_action == "follow":
                if follow_mode:
                    follow_mode = False
                    if send_input and active:
                        resume_navigation_earnings(
                            navigation_earnings, now=time.monotonic()
                        )
                    follow_player_id = ""
                    follow_player_name = ""
                    follow_player_object_id = None
                    followed_player = None
                    last_follow_channel_request_at = -math.inf
                    target = None
                    if not active:
                        reset_summon_mount_key_state(summon_mount_keys)
                        reset_summoner_check_state(summoner_check_state)
                    reset_combat_watchdog(combat_watchdog, None, now)
                    publish_navigation_intent(0)
                    set_keys(())
                    announce(
                        "選單：純跟隨模式關閉；一般導航"
                        + ("恢復。" if active else "仍為暫停。"),
                        force=True,
                    )
                else:
                    if send_input and active:
                        pause_navigation_earnings(
                            navigation_earnings, now=time.monotonic()
                        )
                    target = None
                    memory_loot_active = False
                    loot_candidate_object_id = None
                    loot_candidate_frames = 0
                    loot_clear_frames = 0
                    reset_loot_chase(loot_chase, now=now)
                    reset_combat_watchdog(combat_watchdog, None, now)
                    follow_discovery_active = True
                    discovery_requested_at_ms = int(time.time() * 1000)
                    publish_navigation_intent(0)
                    set_keys(())
                    try:
                        selection_snapshot = wait_for_party_snapshot(
                            state_path,
                            config.memory_snapshot_timeout_ms,
                            after_timestamp_ms=discovery_requested_at_ms,
                            snapshot_reader=load_memory_snapshot,
                        )
                    except SnapshotUnavailable as error:
                        selection_snapshot = None
                        announce(
                            f"選單：無法取得最新隊伍快照，純跟隨模式未開啟：{error}",
                            force=True,
                        )
                    if selection_snapshot is not None:
                        snapshot = selection_snapshot
                        same_map_party_members = tuple(
                            member
                            for member in snapshot.party_members
                            if member.map_id <= 0
                            or member.map_id == snapshot.map_id
                        )
                        entered_name = prompt_follow_player_name(
                            same_map_party_members
                        )
                        named_party_member = (
                            find_follow_party_member_by_name(
                                same_map_party_members, entered_name
                            )
                            if entered_name is not None
                            else None
                        )
                        if entered_name is None:
                            announce(
                                "選單：已取消輸入，純跟隨模式未開啟。",
                                force=True,
                            )
                        elif named_party_member is None:
                            if not snapshot.party_state_available:
                                announce(
                                    "選單：目前探針沒有完整的隊伍快照；"
                                    "隊伍限定跟隨需要探針 v2.16.0 "
                                    "並重新啟動遊戲。",
                                    force=True,
                                )
                            available_names = {
                                member.display_name.strip()
                                or member.player_id.strip()
                                for member in same_map_party_members
                                if member.player_id and not member.is_local
                            }
                            available_names_sorted = sorted(
                                available_names, key=str.casefold
                            )
                            announce(
                                f"選單：找不到唯一符合名稱 {entered_name!r} "
                                "的同地圖隊伍成員。"
                                + (
                                    "目前隊員："
                                    + "、".join(available_names_sorted)
                                    + "。"
                                    if available_names_sorted
                                    else "目前隊伍沒有其他同地圖成員。"
                                ),
                                force=True,
                            )
                        else:
                            follow_mode = True
                            follow_player_id = named_party_member.player_id
                            follow_player_name = (
                                named_party_member.display_name
                                or named_party_member.player_id
                            )
                            followed_player = None
                            follow_player_object_id = None
                            channel_number = party_channel_number(
                                named_party_member
                            )
                            channel_text = (
                                f"第 {channel_number} 頻道"
                                if channel_number is not None
                                else "未知頻道"
                            )
                            announce(
                                f"選單：已鎖定隊伍玩家 {follow_player_name}，"
                                f"目前位於 {channel_text}；"
                                "若不同頻將立即切換並接續跟隨。",
                                force=True,
                            )
                    follow_discovery_active = False
                    publish_navigation_intent(0)
                    if not follow_mode and send_input and active:
                        resume_navigation_earnings(
                            navigation_earnings, now=time.monotonic()
                        )
            if menu_action == "loot":
                loot_enabled = not loot_enabled
                memory_loot_active = False
                loot_candidate_object_id = None
                loot_candidate_frames = 0
                loot_clear_frames = 0
                loot_skipped_until.clear()
                reset_loot_chase(loot_chase, now=now)
                announce(
                    f"選單：內存拾取{'開啟' if loot_enabled else '關閉'}。",
                    force=True,
                )
            if menu_action == "loot_rarity":
                selected_rarity = show_loot_rarity_menu(
                    config.memory_loot_min_rarity
                )
                if selected_rarity is not None:
                    config.memory_loot_min_rarity = selected_rarity
                    save_config(config_path, config)
                    memory_loot_active = False
                    loot_candidate_object_id = None
                    loot_candidate_frames = 0
                    loot_clear_frames = 0
                    loot_skipped_until.clear()
                    reset_loot_chase(loot_chase, now=now)
                    publish_navigation_intent(0)
                    set_keys(())
                    announce(
                        f"選單：最低拾取品質已設為 {selected_rarity} 以上。",
                        force=True,
                    )
            if menu_action == "navigation":
                if active:
                    finalize_navigation_statistics(
                        refresh_wallet=not follow_mode
                    )
                    active = False
                else:
                    active = True
                    if send_input:
                        start_navigation_earnings(
                            navigation_earnings,
                            now=time.monotonic(),
                            tracking=not follow_mode,
                        )
                now = time.monotonic()
                if mode == 3 and active:
                    boss_farm = BossFarmState()
                if follow_mode:
                    announce(
                        f"選單：一般導航{'開啟' if active else '關閉'}；"
                        "純跟隨持續運作。",
                        force=True,
                    )
                else:
                    reset_summon_mount_key_state(summon_mount_keys)
                    reset_summoner_check_state(summoner_check_state)
                    target = None
                    memory_loot_active = False
                    loot_candidate_object_id = None
                    loot_candidate_frames = 0
                    reset_loot_chase(loot_chase, now=now)
                    reset_combat_watchdog(combat_watchdog, None, now)
                    publish_navigation_intent(0)
                    set_keys(())
                    announce(
                        f"選單：一般導航{'開啟' if active else '關閉'}。",
                        force=True,
                    )
            poll_card_purchase()
            poll_pricing()
            poll_equipment_filter()
            render_price_window()
            if price_window_visible and not config.debug_window:
                cv2.waitKey(1)

            if not active and not follow_mode:
                input_allowed = False
                status = "PAUSED - 選單暫停"
                set_keys(())
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(snapshot, None, (), False, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(0.08)
                continue

            try:
                snapshot = load_memory_snapshot(
                    state_path,
                    config.memory_snapshot_timeout_ms,
                    avoid_boss=config.avoid_boss and mode != 3,
                )
            except SnapshotUnavailable as error:
                mark_navigation_earnings_incomplete(navigation_earnings)
                input_allowed = False
                snapshot = None
                reset_summon_mount_key_state(summon_mount_keys)
                reset_summoner_check_state(summoner_check_state)
                target = None
                followed_player = None
                follow_player_object_id = None
                memory_loot_active = False
                loot_candidate_object_id = None
                loot_candidate_frames = 0
                reset_loot_chase(loot_chase, now=now)
                reset_combat_watchdog(combat_watchdog, None, now)
                publish_navigation_intent(0)
                set_keys(())
                status = f"SAFE STOP - {error}"
                announce(status, dedupe_key=snapshot_error_log_key(error))
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(None, None, (), True, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                continue

            observe_earnings_snapshot(snapshot)
            input_allowed = snapshot.player.alive
            if not input_allowed:
                reset_summon_mount_key_state(summon_mount_keys)
                reset_summoner_check_state(summoner_check_state)
                target = None
                followed_player = None
                follow_player_object_id = None
                memory_loot_active = False
                loot_candidate_object_id = None
                loot_candidate_frames = 0
                loot_clear_frames = 0
                reset_loot_chase(loot_chase, now=now)
                reset_combat_watchdog(combat_watchdog, None, now)
                publish_navigation_intent(0)
                set_keys(())
                status = "PLAYER DEAD - ALL INPUT RELEASED"
                announce(status, dedupe_key="player_dead")
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(snapshot, None, (), False, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue

            if (
                config.job_type in NAVIGATION_UPKEEP_JOB_TYPES
                and send_input
                and not snapshot.player.summon_mount_action_available
            ):
                announce(
                    "召喚坐騎判斷需要新版探針提供 MountController_C 狀態；"
                    "目前不會自動按 9、0。",
                    dedupe_key="summon_mount_probe_upgrade_required",
                )

            current_map = (snapshot.map_id, snapshot.instance_id)
            if map_identity != current_map:
                map_identity = current_map
                reset_summon_mount_key_state(summon_mount_keys)
                reset_summoner_check_state(summoner_check_state)
                target = None
                followed_player = None
                follow_player_object_id = None
                memory_loot_active = False
                loot_candidate_object_id = None
                loot_candidate_frames = 0
                loot_clear_frames = 0
                loot_skipped_until.clear()
                reset_loot_chase(loot_chase, now=now)
                observed_loot_object_ids.clear()
                skipped_until.clear()
                combat_blocked_object_ids.clear()
                combat_blocked_absent_since.clear()
                reset_combat_watchdog(combat_watchdog, None, now)
                publish_navigation_intent(0)
                progress_anchor = snapshot.player.position
                progress_started_at = now
                unstuck_started_at = None
                announce(
                    f"地圖／分流切換為 {current_map[0]}/{current_map[1]}，"
                    + (
                        f"等待同一玩家 {follow_player_name or follow_player_id} 重現。"
                        if follow_mode
                        else "重新選怪。"
                    ),
                    force=True,
                )

            if follow_mode:
                rebound_player = find_follow_player(
                    snapshot.players, follow_player_id
                )
                if rebound_player is not None:
                    if (
                        follow_player_object_id is not None
                        and rebound_player.object_id != follow_player_object_id
                    ):
                        announce(
                            f"跟隨玩家 {follow_player_name or follow_player_id} "
                            f"ObjectId 已由 {follow_player_object_id} "
                            f"重新綁定為 {rebound_player.object_id}。",
                            force=True,
                        )
                    followed_player = rebound_player
                    follow_player_object_id = rebound_player.object_id
                    if rebound_player.display_name:
                        follow_player_name = rebound_player.display_name
                else:
                    followed_player = None
                    follow_player_object_id = None
            else:
                followed_player = None

            followed_party_member = (
                find_follow_party_member(
                    snapshot.party_members, follow_player_id
                )
                if follow_mode
                else None
            )
            if follow_mode and followed_player is None and followed_party_member:
                local_party_member = find_local_party_member(
                    snapshot.party_members
                )
                channel_number = party_channel_number(followed_party_member)
                channel_text = (
                    f"第 {channel_number} 頻道"
                    if channel_number is not None
                    else "未知頻道"
                )
                target_label = follow_player_name or follow_player_id
                different_map = (
                    followed_party_member.map_id > 0
                    and followed_party_member.map_id != snapshot.map_id
                )
                switch_required = party_member_needs_channel_switch(
                    followed_party_member,
                    local_party_member,
                    snapshot.map_id,
                )
                if different_map:
                    status = (
                        f"FOLLOW TARGET {target_label} ON MAP "
                        f"{followed_party_member.map_id} / {channel_text}"
                    )
                    dedupe_key = (
                        f"follow_other_map:{follow_player_id}:"
                        f"{followed_party_member.map_id}:"
                        f"{followed_party_member.channel_index}"
                    )
                elif switch_required:
                    if (
                        send_input
                        and now - last_follow_channel_request_at
                        >= FOLLOW_CHANNEL_RETRY_SEC
                    ):
                        follow_channel_request_id = max(
                            follow_channel_request_id + 1,
                            int(time.time() * 1000),
                        )
                        last_follow_channel_request_at = now
                    status = (
                        f"FOLLOW SWITCHING TO {target_label} / {channel_text}"
                        if send_input
                        else f"FOLLOW WOULD SWITCH TO {target_label} / {channel_text}"
                    )
                    dedupe_key = (
                        f"follow_switch:{follow_player_id}:"
                        f"{followed_party_member.instance_id}:"
                        f"{followed_party_member.channel_index}:"
                        f"{follow_channel_request_id}"
                    )
                else:
                    status = (
                        f"FOLLOW WAITING FOR {target_label} / {channel_text}"
                    )
                    dedupe_key = (
                        f"follow_same_channel_wait:{follow_player_id}:"
                        f"{followed_party_member.channel_index}"
                    )
                publish_navigation_intent(0)
                set_keys(())
                announce(status, dedupe_key=dedupe_key)
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(snapshot, None, (), True, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                continue

            # Selected job-type-1 summons/buffs gate every navigation mode,
            # including pure following. Stop WASD and both Shift keys before
            # emitting the one-shot skill IPC; navigation resumes only after a
            # later snapshot confirms that every selected item is present.
            check_enabled = summoner_checks_enabled(
                config,
                snapshot.player,
                send_input=send_input,
                active=active,
                follow_mode=follow_mode,
            )
            check_missing, check_unavailable = missing_summoner_checks(
                config, snapshot.player
            )
            if check_enabled and (check_missing or check_unavailable):
                set_keys(())
                # Clear the enemy focus as well as movement: a later probe
                # update must not replace GuardianBond's target mid-cast.
                publish_navigation_intent(0)
            if advance_summoner_checks(
                summoner_check_state,
                config,
                snapshot.player,
                enabled=check_enabled,
                now=now,
                press_key=request_skill_key,
            ):
                pause_combat_watchdog(combat_watchdog, now)
                chase_started_at = now
                path_invalid_since = None
                progress_anchor = snapshot.player.position
                progress_started_at = now
                unstuck_started_at = None
                unstuck_anchor = None
                unstuck_attempt = 0
                status = summoner_check_wait_status(summoner_check_state)
                announce(status, dedupe_key="summoner_check_wait")
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(snapshot, target, (), True, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue

            # Summoner mount maintenance gates either general F8 navigation or
            # independent F2 following. Keep the probe heartbeat fresh until
            # mounting is confirmed, even without a current movement target.
            publish_navigation_intent(requested_target_id, requested_target_kind)
            if update_summon_mount_keys(snapshot.player, now):
                pause_combat_watchdog(combat_watchdog, now)
                chase_started_at = now
                path_invalid_since = None
                progress_anchor = snapshot.player.position
                progress_started_at = now
                unstuck_started_at = None
                unstuck_anchor = None
                unstuck_attempt = 0
                if memory_loot_active:
                    reset_loot_chase(
                        loot_chase,
                        now=now,
                        target_object_id=loot_chase.target_object_id,
                        player_position=snapshot.player.position,
                    )
                set_keys(())
                status = summon_mount_wait_status(
                    summon_mount_keys,
                    config.summon_reanimation_key,
                    config.summon_mount_key,
                )
                announce(status, dedupe_key="summon_mount_wait")
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(snapshot, target, (), True, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue

            if follow_mode:
                target = None
                memory_loot_active = False
                loot_candidate_object_id = None
                loot_candidate_frames = 0
                loot_clear_frames = 0
                reset_loot_chase(loot_chase, now=now)
                reset_combat_watchdog(combat_watchdog, None, now)

                if followed_player is None:
                    publish_navigation_intent(0)
                    set_keys(())
                    status = (
                        "FOLLOW LOST - WAITING FOR "
                        f"{follow_player_name or follow_player_id}"
                    )
                    announce(
                        status,
                        dedupe_key="follow_lost:" + follow_player_id,
                    )
                    if config.debug_window:
                        cv2.imshow(
                            RADAR_WINDOW_NAME,
                            draw_radar(snapshot, None, (), True, status, config),
                        )
                        cv2.waitKey(1)
                    time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                    continue

                follow_distance = horizontal_distance(
                    snapshot.player.position, followed_player.position
                )
                follow_stop_distance = follow_stop_distance_world(
                    snapshot.player,
                    followed_player,
                    config.follow_player_stop_padding_world,
                )
                publish_navigation_intent(followed_player.object_id, "player")
                safe_follow_path = request_path_matches(
                    snapshot.path,
                    request_id,
                    followed_player.object_id,
                    target_kind="player",
                )
                waypoint = (
                    select_path_waypoint(
                        snapshot.player.position,
                        snapshot.path.corners,
                        config.path_waypoint_tolerance_world,
                    )
                    if safe_follow_path
                    else None
                )
                path_ready = bool(
                    safe_follow_path
                    and (
                        follow_distance <= follow_stop_distance
                        or waypoint is not None
                    )
                )
                movement_keys = (
                    movement_keys_for_world_waypoint(
                        snapshot.player, waypoint, config
                    )
                    if path_ready
                    and follow_distance > follow_stop_distance
                    and waypoint is not None
                    else ()
                )
                desired_follow_keys = (
                    (*movement_keys, *HELD_SHIFT_KEYS) if path_ready else ()
                )
                if path_ready:
                    status = (
                        f"FOLLOW {follow_player_name or follow_player_id} "
                        f"D={follow_distance:.2f} "
                        f"STOP={follow_stop_distance:.2f} "
                        f"{'KEYS' if send_input else 'WOULD'}="
                        f"{''.join(desired_follow_keys).upper()}"
                    )
                else:
                    status = (
                        f"FOLLOW WAIT PATH {follow_player_name or follow_player_id} "
                        f"D={follow_distance:.2f} request={request_id} "
                        f"response={snapshot.path.request_id} "
                        f"kind={snapshot.path.target_kind} "
                        f"status={snapshot.path.status}"
                    )
                    if (
                        snapshot.path.request_id == request_id
                        and snapshot.path.target_object_id
                        == followed_player.object_id
                        and snapshot.path.target_kind != "player"
                    ):
                        announce(
                            "跟隨導航需要探針 v2.16.0；"
                            "請安裝新版 DLL 並重新啟動遊戲。",
                            dedupe_key="follow_target_kind_probe_upgrade_required",
                        )
                set_keys(desired_follow_keys)
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(
                            snapshot,
                            None,
                            desired_follow_keys,
                            True,
                            status,
                            config,
                        ),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue

            if not snapshot.map_exit_state_available:
                target = None
                memory_loot_active = False
                loot_candidate_object_id = None
                loot_candidate_frames = 0
                loot_clear_frames = 0
                reset_loot_chase(loot_chase, now=now)
                reset_combat_watchdog(combat_watchdog, None, now)
                publish_navigation_intent(0)
                set_keys(())
                status = "SAFE STOP - MAP EXIT DATA UNAVAILABLE"
                announce(
                    "一般導航傳送出口避讓需要探針 v2.16.0；"
                    "安裝新版 DLL 並重啟遊戲前不會導航。",
                    dedupe_key="map_exit_probe_upgrade_required",
                )
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(snapshot, None, (), True, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue

            player_map_exit = point_inside_map_exit_keepout(
                snapshot.player,
                snapshot.player.position,
                snapshot.map_exits,
                config.map_exit_avoidance_padding_world,
            )
            if player_map_exit is not None:
                unstuck_started_at = None
                unstuck_anchor = None
                unstuck_attempt = 0
                progress_anchor = snapshot.player.position
                progress_started_at = now
                loot_chase.unstuck_started_at = None
                loot_chase.unstuck_anchor = None
                loot_chase.unstuck_attempt = 0
                loot_chase.progress_anchor = snapshot.player.position
                loot_chase.progress_started_at = now

            effective_loot_enabled = loot_enabled
            boss_legendary_target: MemoryLoot | None = None
            if mode == 3:
                matching_boss = select_boss_farm_target(
                    snapshot.monsters,
                    snapshot.player.position,
                    boss_name,
                    boss_farm.tracked_boss_object_id,
                )
                boss_legendary_target = select_boss_legendary_loot(
                    snapshot.loots,
                    snapshot.player.position,
                    loot_candidate_object_id,
                )

                if matching_boss is not None:
                    if boss_farm.phase != "fight":
                        announce(
                            f"MODE 3 BOSS READY - {boss_name} "
                            f"{matching_boss.object_id}",
                            force=True,
                        )
                    boss_farm.phase = "fight"
                    boss_farm.tracked_boss_object_id = matching_boss.object_id
                    boss_farm.boss_missing_since = None
                    boss_farm.key_release_started_at = None
                    boss_farm.fault = ""
                    effective_loot_enabled = False
                elif boss_farm.phase == "fight":
                    boss_farm.boss_missing_since = (
                        boss_farm.boss_missing_since or now
                    )
                    missing_for = now - boss_farm.boss_missing_since
                    if missing_for < boss_death_confirm_sec:
                        target = None
                        publish_navigation_intent(0)
                        set_keys(())
                        status = (
                            f"MODE 3 BOSS MISSING - CONFIRMING "
                            f"{missing_for:.2f}/{boss_death_confirm_sec:.2f}s"
                        )
                        time.sleep(config.loop_delay_ms / 1000)
                        continue
                    boss_farm.phase = "loot_wait"
                    boss_farm.tracked_boss_object_id = None
                    boss_farm.boss_missing_since = None
                    boss_farm.loot_settle_until = now + boss_loot_settle_sec
                    target = None
                    reset_combat_watchdog(combat_watchdog, None, now)
                    announce(
                        f"MODE 3 BOSS DEFEATED - 等待 {boss_loot_settle_sec:.1f}s "
                        "確認自己的 Legendary。",
                        force=True,
                    )

                if boss_farm.phase == "startup":
                    if boss_legendary_target is not None:
                        boss_farm.phase = "loot_wait"
                        boss_farm.loot_settle_until = now
                    elif matching_boss is None:
                        if not send_input:
                            target = None
                            publish_navigation_intent(0)
                            set_keys(())
                            status = (
                                f"MODE 3 PREVIEW - WOULD USE "
                                f"{boss_summon_item_name}"
                            )
                            announce(status, dedupe_key="boss_preview_use")
                            time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                            continue
                        # Release every held key (WASD + Left/Right Shift) and let
                        # it settle before using the summon item: using a consumable
                        # while a Shift skill is still held is rejected in-game. The
                        # probe only clears the held hotkeys once it processes a
                        # request with empty keys, so wait
                        # boss_use_key_release_settle_sec for that to reach the game
                        # before firing the use.
                        target = None
                        publish_navigation_intent(0)
                        set_keys(())
                        if boss_farm.key_release_started_at is None:
                            boss_farm.key_release_started_at = now
                        released_for = now - boss_farm.key_release_started_at
                        if released_for < boss_use_key_release_settle_sec:
                            status = (
                                f"MODE 3 RELEASE KEYS - {released_for:.2f}/"
                                f"{boss_use_key_release_settle_sec:.2f}s"
                            )
                            announce(status, dedupe_key="boss_release_keys")
                            time.sleep(config.loop_delay_ms / 1000)
                            continue
                        boss_farm.key_release_started_at = None
                        boss_farm.use_request_id = request_consumable_use(
                            boss_summon_item_name
                        )
                        boss_farm.use_requested_at = now
                        boss_farm.phase = "use_pending"
                        announce(
                            f"MODE 3 USE CONSUMABLE - {boss_summon_item_name} "
                            f"REQUEST={boss_farm.use_request_id}",
                            force=True,
                        )

                if boss_farm.phase in {"use_pending", "waiting_spawn"}:
                    use_result = snapshot.consumable_use
                    if (
                        boss_farm.phase == "use_pending"
                        and use_result.request_id == boss_farm.use_request_id
                    ):
                        if use_result.status == "accepted":
                            boss_farm.phase = "waiting_spawn"
                            announce(
                                f"MODE 3 CONSUMABLE ACCEPTED - "
                                f"{use_result.display_name or use_result.item_id}; "
                                f"REMAINING={use_result.remaining_count}",
                                force=True,
                            )
                        elif use_result.status not in {"idle", "pending"}:
                            detail = use_result.error or use_result.status
                            pause_boss_farm(
                                f"召喚物品使用失敗：{detail}"
                            )
                            time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                            continue
                    waited = now - boss_farm.use_requested_at
                    if waited >= boss_spawn_timeout_sec:
                        pause_boss_farm(
                            f"使用 {boss_summon_item_name} 後 "
                            f"{boss_spawn_timeout_sec:.1f}s 內未生成 {boss_name}"
                        )
                        time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                        continue
                    target = None
                    publish_navigation_intent(0)
                    set_keys(())
                    status = (
                        f"MODE 3 WAIT BOSS - {boss_name} "
                        f"{waited:.1f}/{boss_spawn_timeout_sec:.1f}s"
                    )
                    announce(status, dedupe_key="boss_wait_spawn")
                    time.sleep(config.loop_delay_ms / 1000)
                    continue

                if boss_farm.phase == "loot_wait":
                    effective_loot_enabled = True
                    if boss_legendary_target is None and not memory_loot_active:
                        if now < boss_farm.loot_settle_until:
                            target = None
                            publish_navigation_intent(0)
                            set_keys(())
                            remaining = boss_farm.loot_settle_until - now
                            status = (
                                f"MODE 3 LOOT SETTLE - {remaining:.1f}s"
                            )
                            announce(status, dedupe_key="boss_loot_settle")
                            time.sleep(config.loop_delay_ms / 1000)
                            continue
                        boss_farm.phase = "startup"
                        announce(
                            "MODE 3 LOOT CLEAR - 開始下一輪召喚。",
                            force=True,
                        )
                        publish_navigation_intent(0)
                        set_keys(())
                        time.sleep(config.loop_delay_ms / 1000)
                        continue

            ownership_filter = (
                snapshot.loot_scan.get("ownership_filter")
                if snapshot.loot_scan
                else None
            )
            if effective_loot_enabled and mode != 3 and ownership_filter != "all":
                announce(
                    "目前探針只提供自己的掉落物；請安裝探針 v2.5.0 "
                    "並重啟遊戲，才能拾取範圍內已解鎖的別人物品。",
                    dedupe_key="loot_ownership_probe_upgrade_required",
                )
            elif (
                effective_loot_enabled
                and snapshot.loot_scan
                and int(snapshot.loot_scan.get("rejected_error", 0)) > 0
            ):
                announce(
                    "內存掉落物有讀取錯誤："
                    f"{snapshot.loot_scan.get('last_error', 'unknown')}",
                    dedupe_key="loot_scan_error:"
                    + str(snapshot.loot_scan.get("last_error", "unknown")),
                )

            current_loot_ids = {loot.object_id for loot in snapshot.loots}
            if effective_loot_enabled:
                for new_loot in snapshot.loots:
                    if new_loot.object_id in observed_loot_object_ids:
                        continue
                    loot_label = (
                        new_loot.display_name
                        or new_loot.item_id
                        or new_loot.sprite_id
                        or "UNKNOWN"
                    )
                    loot_owner = loot_ownership_label(new_loot)
                    announce(
                        f"偵測到掉落物 {new_loot.object_id} "
                        f"[{loot_owner}/{new_loot.rarity}/{new_loot.loot_type}] "
                        f"{loot_label}"
                        f"{'（目前鎖定）' if new_loot.locked else ''}。",
                        force=True,
                    )
                observed_loot_object_ids.intersection_update(current_loot_ids)
                observed_loot_object_ids.update(current_loot_ids)
            else:
                observed_loot_object_ids.clear()

            loot_skipped_until = {
                object_id: expiry
                for object_id, expiry in loot_skipped_until.items()
                if expiry > now and object_id in current_loot_ids
            }
            loot_target = (
                (
                    boss_legendary_target
                    if mode == 3
                    else select_memory_loot(
                    snapshot.loots,
                    snapshot.player,
                    config.memory_loot_min_rarity,
                    loot_candidate_object_id,
                    skipped_until=loot_skipped_until,
                    now=now,
                    range_padding_world=config.memory_loot_range_padding_world,
                    max_distance_world=config.memory_loot_max_distance_world,
                    )
                )
                if effective_loot_enabled
                else None
            )
            if loot_target is not None:
                blocked_loot_exit = point_inside_map_exit_keepout(
                    snapshot.player,
                    loot_target.position,
                    snapshot.map_exits,
                    config.map_exit_avoidance_padding_world,
                )
                if blocked_loot_exit is not None:
                    if mode == 3:
                        pause_boss_farm(
                            f"Legendary {loot_target.object_id} 位於傳送出口避讓範圍"
                        )
                        time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                        continue
                    loot_skipped_until[loot_target.object_id] = (
                        now + config.memory_loot_retry_cooldown_sec
                    )
                    announce(
                        f"掉落物 {loot_target.object_id} 太靠近傳送出口，"
                        "一般導航不會接近。",
                        force=True,
                    )
                    loot_target = None
            loot_candidate_object_id, loot_candidate_frames = (
                track_memory_loot_candidate(
                    loot_target,
                    loot_candidate_object_id,
                    loot_candidate_frames,
                )
            )

            if loot_target is None and not memory_loot_active:
                reset_loot_chase(loot_chase, now=now)

            if loot_target is not None:
                loot_rule_label = (
                    "Legendary"
                    if mode == 3
                    else config.memory_loot_min_rarity
                )
                if loot_chase.target_object_id != loot_target.object_id:
                    reset_loot_chase(
                        loot_chase,
                        now=now,
                        target_object_id=loot_target.object_id,
                        player_position=snapshot.player.position,
                    )
                    announce(
                        f"{loot_rule_label}優先：鎖定"
                        f"{'自己的' if loot_target.owned_by_local_player else '範圍內別人／公開的'}"
                        f"掉落物 {loot_target.object_id}，"
                        "暫停目前怪物導航。",
                        force=True,
                    )
                memory_loot_active = True
                loot_clear_frames = 0
                pause_combat_watchdog(combat_watchdog, now)
                # Loot preemption must not consume the interrupted monster's
                # chase, path-grace, or unstuck budgets.
                chase_started_at = now
                path_invalid_since = None
                progress_anchor = snapshot.player.position
                progress_started_at = now
                unstuck_started_at = None
                unstuck_anchor = None
                unstuck_attempt = 0
                loot_label = (
                    loot_target.display_name
                    or loot_target.item_id
                    or loot_target.sprite_id
                    or "UNKNOWN"
                )
                interaction = plan_loot_interaction(
                    loot_chase, snapshot.player, loot_target, config,
                    now=now, confirmed_frames=loot_candidate_frames,
                    last_interact_at=last_loot_interact, send_input=send_input,
                    in_exit_keepout=player_map_exit is not None,
                )
                if interaction.phase in {"confirm", "stop"}:
                    publish_navigation_intent(0)
                    desired_loot_keys: tuple[str, ...] = ()
                    set_keys(())
                    status = (
                        f"MEMORY LOOT CANDIDATE {loot_target.object_id} "
                        f"{loot_target.rarity} {loot_label}"
                    )
                elif interaction.phase == "chase":
                    publish_navigation_intent(loot_target.object_id, "loot")
                    approach = plan_loot_approach(
                        snapshot, loot_target, loot_chase, config,
                        request_id=request_id, now=now, send_input=send_input,
                        loot_rule_label=loot_rule_label,
                    )
                    loot_keys = approach.movement_keys
                    safe_loot_path = approach.path_ready
                    failure_reason = approach.failure_reason
                    status = approach.status
                    for notice in approach.notices:
                        announce(notice.message, force=notice.force,
                                 dedupe_key=notice.dedupe_key)
                    if failure_reason is not None:
                        if mode == 3:
                            pause_boss_farm(
                                f"Legendary {loot_target.object_id} 拾取失敗"
                                f"（{failure_reason}）"
                            )
                            time.sleep(
                                max(0.05, config.target_lost_wait_ms / 1000)
                            )
                            continue
                        loot_skipped_until[loot_target.object_id] = (
                            now + config.memory_loot_retry_cooldown_sec
                        )
                        status = (
                            f"LOOT RETRY LATER {loot_target.object_id} "
                            f"REASON={failure_reason.upper()} "
                            f"AFTER={config.memory_loot_retry_cooldown_sec:.1f}s"
                        )
                        announce(
                            f"{loot_rule_label} {loot_target.object_id} 導航失敗"
                            f"（{failure_reason}），"
                            f"{config.memory_loot_retry_cooldown_sec:.1f}s 後重試。",
                            force=True,
                        )
                        memory_loot_active = False
                        loot_candidate_object_id = None
                        loot_candidate_frames = 0
                        reset_loot_chase(loot_chase, now=now)
                        publish_navigation_intent(0)
                        set_keys(())
                        if config.debug_window:
                            cv2.imshow(
                                RADAR_WINDOW_NAME,
                                draw_radar(
                                    snapshot,
                                    target,
                                    (),
                                    True,
                                    status,
                                    config,
                                    loot_target,
                                ),
                            )
                            cv2.waitKey(1)
                        time.sleep(config.loop_delay_ms / 1000)
                        continue

                    desired_loot_keys = loot_keys
                    if (
                        send_input
                        and safe_loot_path
                        and player_map_exit is None
                    ):
                        desired_loot_keys = (
                            *desired_loot_keys,
                            *f8_shift_keys(config),
                        )
                    set_keys(desired_loot_keys)
                    if config.debug_window:
                        cv2.imshow(
                            RADAR_WINDOW_NAME,
                            draw_radar(
                                snapshot,
                                target,
                                desired_loot_keys,
                                True,
                                status,
                                config,
                                loot_target,
                            ),
                        )
                        cv2.waitKey(1)
                    time.sleep(config.loop_delay_ms / 1000)
                    continue
                else:
                    publish_navigation_intent(0)
                    desired_loot_keys = ()
                    set_keys(desired_loot_keys)
                    if interaction.started_release:
                        announce(
                            f"拾取 {loot_target.object_id} 前先放開所有移動鍵與 Shift。",
                            force=True,
                        )
                    if interaction.phase == "release":
                        status = (
                            f"LOOT RELEASE ALL KEYS {loot_target.object_id} "
                            f"WAIT={interaction.wait_seconds:.2f}s"
                        )
                    else:
                        action = "LOOT PICK UP TARGET" if send_input else "WOULD PICK UP TARGET"
                        status = (
                            f"{loot_ownership_label(loot_target)} {action} "
                            f"{loot_target.object_id} "
                            f"{loot_target.rarity} {loot_label}"
                        )
                        if interaction.interaction_due:
                            if interaction.pickup_object_id is not None:
                                request_loot_pickup(interaction.pickup_object_id)
                            last_loot_interact = now
                            announce(
                                f"內存掉落物：{loot_target.object_id} "
                                f"[{loot_ownership_label(loot_target)}/"
                                f"{loot_target.rarity}/{loot_target.loot_type}] "
                                f"{loot_label}；"
                                f"{'已送撿取' if send_input else '預覽，不送撿取'}。",
                                force=True,
                            )
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(
                            snapshot,
                            target,
                            desired_loot_keys,
                            True,
                            status,
                            config,
                            loot_target,
                        ),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue

            if memory_loot_active:
                loot_clear_frames += 1
                if loot_clear_frames < max(1, config.memory_loot_clear_confirm_frames):
                    pause_combat_watchdog(combat_watchdog, now)
                    chase_started_at = now
                    path_invalid_since = None
                    progress_anchor = snapshot.player.position
                    progress_started_at = now
                    unstuck_started_at = None
                    unstuck_anchor = None
                    unstuck_attempt = 0
                    publish_navigation_intent(0)
                    set_keys(())
                    status = "LOOT CLEAR - CONFIRMING; NAVIGATION PAUSED"
                    time.sleep(config.loop_delay_ms / 1000)
                    continue
                memory_loot_active = False
                loot_clear_frames = 0
                reset_loot_chase(loot_chase, now=now)
                status = "LOOT CLEAR - RESUME NAVIGATION"
                announce("LOOT CLEAR：目標掉落物已消失，恢復導航。", force=True)

            refresh_combat_blacklist(
                combat_blocked_object_ids,
                combat_blocked_absent_since,
                {monster.object_id for monster in snapshot.monsters},
                now=now,
                absence_reset_sec=config.combat_blacklist_absence_reset_sec,
            )

            # Boss avoidance takes priority over combat. Either hop to the next
            # channel (fresh, boss-free instance) or walk away from the boss,
            # depending on boss_response. Both drop the current attack target.
            if config.avoid_boss and mode != 3:
                boss = next(
                    (monster for monster in snapshot.monsters if monster.avoid),
                    None,
                )
                if boss is not None and (
                    config.boss_response == "switch_channel"
                    and snapshot.channel_count > 0
                    and snapshot.channel_index >= 0
                ):
                    # After a switch, let the fresh channel's snapshot settle
                    # before deciding again so we never double-hop on the stale
                    # (pre-switch) frame that still shows the old boss.
                    if (
                        now - last_channel_switch_at
                        < config.boss_channel_switch_settle_sec
                    ):
                        reset_combat_watchdog(combat_watchdog, None, now)
                        target = None
                        publish_navigation_intent(0)
                        set_keys(())
                        status = "BOSS CHANNEL SWITCH - 等待新頻道載入"
                        announce(status, dedupe_key="boss_channel_settle")
                        time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                        continue
                    target_index = (
                        snapshot.channel_index + 1
                    ) % snapshot.channel_count
                    reset_combat_watchdog(combat_watchdog, None, now)
                    target = None
                    publish_navigation_intent(0)
                    set_keys(())
                    request_channel_switch(target_index)
                    status = (
                        f"BOSS CHANNEL SWITCH - 首領 {boss.object_id} "
                        f"Lv.{boss.level} → 頻道 {target_index + 1}"
                    )
                    announce(status, dedupe_key="boss_channel_switch")
                    if config.debug_window:
                        cv2.imshow(
                            RADAR_WINDOW_NAME,
                            draw_radar(snapshot, None, (), True, status, config),
                        )
                        cv2.waitKey(1)
                    time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                    continue

                if boss is not None:
                    boss_distance = horizontal_distance(
                        snapshot.player.position, boss.position
                    )
                    if boss_distance <= config.boss_flee_radius_world:
                        away_waypoint = (
                            2 * snapshot.player.position[0] - boss.position[0],
                            snapshot.player.position[1],
                            2 * snapshot.player.position[2] - boss.position[2],
                        )
                        flee_keys = movement_keys_for_world_waypoint(
                            snapshot.player, away_waypoint, config
                        )
                        reset_combat_watchdog(combat_watchdog, None, now)
                        target = None
                        publish_navigation_intent(0)
                        set_keys(flee_keys)
                        status = (
                            f"BOSS FLEE - 遠離首領 {boss.object_id} "
                            f"Lv.{boss.level} ({boss_distance:.1f}m)"
                        )
                        announce(status, dedupe_key="boss_flee")
                        if config.debug_window:
                            cv2.imshow(
                                RADAR_WINDOW_NAME,
                                draw_radar(
                                    snapshot, None, flee_keys, True, status, config
                                ),
                            )
                            cv2.waitKey(1)
                        time.sleep(max(0.01, config.loop_delay_ms / 1000))
                        continue

            previous_target_id = target.object_id if target else None
            if mode == 3:
                target = select_boss_farm_target(
                    snapshot.monsters,
                    snapshot.player.position,
                    boss_name,
                    boss_farm.tracked_boss_object_id,
                )
                skipped_until = {}
            else:
                target, skipped_until = select_memory_target(
                    snapshot.monsters,
                    snapshot.player.position,
                    previous_target_id,
                    skipped_until,
                    now=now,
                    blocked_object_ids=combat_blocked_object_ids,
                )
            while target is not None:
                blocked_target_exit = point_inside_map_exit_keepout(
                    snapshot.player,
                    target.position,
                    snapshot.map_exits,
                    config.map_exit_avoidance_padding_world,
                )
                if blocked_target_exit is None:
                    break
                skipped_until[target.object_id] = (
                    now + config.target_skip_cooldown_sec
                )
                announce(
                    f"怪物 {target.object_id} 太靠近傳送出口，一般導航暫時略過。",
                    force=True,
                )
                if mode == 3:
                    pause_boss_farm(
                        f"{boss_name} {target.object_id} 位於傳送出口避讓範圍"
                    )
                    target = None
                else:
                    target, skipped_until = select_memory_target(
                        snapshot.monsters,
                        snapshot.player.position,
                        None,
                        skipped_until,
                        now=now,
                        blocked_object_ids=combat_blocked_object_ids,
                    )
            if target is None:
                reset_combat_watchdog(combat_watchdog, None, now)
                publish_navigation_intent(0)
                set_keys(())
                status = (
                    f"NO AVAILABLE ENEMY - COMBAT BLOCKED "
                    f"{len(combat_blocked_object_ids)}"
                    if combat_blocked_object_ids
                    else no_enemy_status(snapshot)
                )
                announce(status, dedupe_key="no_living_enemy")
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(snapshot, None, (), True, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                continue

            # Refresh the same request id so the probe can detect a dead Python
            # process while continuously recomputing a moving target's path.
            publish_navigation_intent(target.object_id)
            if target.object_id != previous_target_id:
                mouse_click_completed_for_target = False
                priest_shift_next_tap_at = -math.inf
                chase_started_at = now
                path_invalid_since = None
                progress_anchor = snapshot.player.position
                progress_started_at = now
                unstuck_started_at = None
                unstuck_attempt = 0
                reset_combat_watchdog(combat_watchdog, target, now)
                announce(
                    (
                        f"MODE 3 鎖定王 {target.object_id} "
                        if mode == 3
                        else f"鎖定最近敵怪 {target.object_id} "
                    )
                    + f"{target.display_name or target.config_id}。",
                    force=True,
                )

            safe_path = request_path_matches(
                snapshot.path, request_id, target.object_id
            )
            blocked_path_exit = (
                path_enters_map_exit_keepout(
                    snapshot.player,
                    snapshot.path.corners,
                    snapshot.map_exits,
                    config.map_exit_avoidance_padding_world,
                )
                if safe_path
                else None
            )
            if blocked_path_exit is not None:
                blocked_target = target
                if mode == 3:
                    pause_boss_farm(
                        f"{boss_name} {blocked_target.object_id} 的路徑進入傳送出口避讓範圍"
                    )
                    time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                    continue
                skipped_until[blocked_target.object_id] = (
                    now + config.target_skip_cooldown_sec
                )
                target = None
                reset_combat_watchdog(combat_watchdog, None, now)
                publish_navigation_intent(0)
                set_keys(())
                status = (
                    f"MAP EXIT AVOID {blocked_target.object_id} "
                    f"PADDING={config.map_exit_avoidance_padding_world:.2f}"
                )
                announce(
                    f"怪物 {blocked_target.object_id} 的路徑太靠近傳送出口，"
                    "一般導航暫時略過。",
                    force=True,
                )
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(snapshot, blocked_target, (), True, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue

            mouse_moved = False
            if effective_mouse_lock and send_input and input_allowed:
                if target.viewport_position is None:
                    announce(
                        "一般導航怪物滑鼠鎖定需要探針 v2.16.0 的 viewport 資料。",
                        dedupe_key="monster_mouse_lock_probe_upgrade_required",
                    )
                elif not (
                    left_click_after_mouse_lock
                    and mouse_click_completed_for_target
                ):
                    # With automatic clicking enabled, the physical cursor only
                    # needs to reach the newly acquired target once.  Leaving it
                    # locked every loop makes foreground mouse input feel frozen.
                    mouse_moved = move_mouse_to_monster(hwnd, target)
                    if (
                        mouse_moved
                        and left_click_after_mouse_lock
                        and not mouse_click_completed_for_target
                    ):
                        mouse_click_completed_for_target = post_left_click_to_monster(
                            hwnd, target
                        )
                if (
                    config.job_type == 2
                    and player_map_exit is None
                    and now >= priest_shift_next_tap_at
                ):
                    if not mouse_moved:
                        mouse_moved = move_mouse_to_monster(hwnd, target)
                    if mouse_moved and tap_game_key(
                        "lshift", config.priest_left_shift_tap_hold_ms
                    ):
                        priest_shift_next_tap_at = next_priest_shift_tap_at(
                            now, config
                        )

            distance_to_target = horizontal_distance(
                snapshot.player.position, target.position
            )
            arrived = (
                player_map_exit is None
                and distance_to_target <= arrival_radius(
                    snapshot.player, target, config
                )
            )
            keys: tuple[str, ...] = ()
            if should_advance_train_target(
                mode, arrived=arrived, send_input=send_input
            ):
                reached_target = target
                skipped_until[reached_target.object_id] = (
                    now + config.target_skip_cooldown_sec
                )
                status = (
                    f"TRAIN REACHED {reached_target.object_id} "
                    f"D={distance_to_target:.2f} - NEXT TARGET"
                )
                announce(
                    f"火車模式：已抵達怪物 {reached_target.object_id}，"
                    "立刻選下一隻。",
                    force=True,
                )
                target = None
                reset_combat_watchdog(combat_watchdog, None, now)
                publish_navigation_intent(0)
                handoff_keys = f8_shift_keys(config)
                set_keys(handoff_keys)
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(
                            snapshot,
                            reached_target,
                            handoff_keys,
                            True,
                            status,
                            config,
                        ),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue
            was_in_range = combat_watchdog.was_in_range
            combat_action = update_combat_watchdog(
                combat_watchdog,
                target,
                arrived=arrived,
                now=now,
                enabled=send_input,
                config=config,
            )
            if arrived != was_in_range:
                chase_started_at = now

            combat_idle_sec = max(0.0, now - combat_watchdog.last_progress_at)
            if combat_action == "block":
                blocked_target = target
                if mode == 3:
                    pause_boss_farm(
                        f"{boss_name} {blocked_target.object_id} 戰鬥無生命值進展"
                    )
                    time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                    continue
                combat_blocked_object_ids.add(blocked_target.object_id)
                combat_blocked_absent_since.pop(blocked_target.object_id, None)
                status = (
                    f"COMBAT BLOCKED {blocked_target.object_id} "
                    f"HP={blocked_target.health_ratio * 100:.2f}% "
                    f"BEST={combat_watchdog.best_health_ratio * 100:.2f}% "
                    f"IDLE={combat_idle_sec:.1f}s"
                )
                announce(status, force=True)
                target = None
                reset_combat_watchdog(combat_watchdog, None, now)
                publish_navigation_intent(0)
                set_keys(())
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(
                            snapshot, blocked_target, (), True, status, config
                        ),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue

            if combat_action in ("stalled", "reengage"):
                if combat_action == "stalled":
                    announce(
                        f"COMBAT STALLED {target.object_id} "
                        f"HP={target.health_ratio * 100:.2f}% "
                        f"BEST={combat_watchdog.best_health_ratio * 100:.2f}% "
                        f"IDLE={combat_idle_sec:.1f}s，嘗試脫離重接。",
                        force=True,
                    )
                reposition_started_at = combat_watchdog.reposition_started_at
                assert reposition_started_at is not None
                keys = combat_reengage_keys(
                    (now - reposition_started_at) * 1000,
                    combat_reengage_side,
                    config,
                )
                if keys is None:
                    finish_combat_reengage(combat_watchdog, now)
                    chase_started_at = now
                    combat_reengage_side = (
                        "d" if combat_reengage_side == "a" else "a"
                    )
                    status = (
                        f"COMBAT REENGAGE {target.object_id} RETURN "
                        f"HP={target.health_ratio * 100:.2f}% "
                        f"BEST={combat_watchdog.best_health_ratio * 100:.2f}%"
                    )
                    announce(status, force=True)
                    set_keys(())
                else:
                    status = (
                        f"COMBAT REENGAGE {target.object_id} "
                        f"KEYS={''.join(keys).upper()} "
                        f"HP={target.health_ratio * 100:.2f}% "
                        f"BEST={combat_watchdog.best_health_ratio * 100:.2f}%"
                    )
                    set_keys(keys)
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(snapshot, target, keys or (), True, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue

            if arrived:
                path_invalid_since = None
                progress_anchor = snapshot.player.position
                progress_started_at = now
                unstuck_started_at = None
                status = (
                    f"{'TRAIN PREVIEW' if mode == 2 else 'IN RANGE'} "
                    f"{distance_to_target:.2f} - "
                    f"{'WOULD SWITCH' if mode == 2 else 'ATTACK'} "
                    f"HP={target.health_ratio * 100:.2f}% "
                    f"BEST={combat_watchdog.best_health_ratio * 100:.2f}% "
                    f"IDLE={combat_idle_sec:.1f}s"
                )
            elif not safe_path:
                set_keys(())
                path_invalid_since = path_invalid_since or now
                status = (
                    f"WAIT PATH request={request_id} response={snapshot.path.request_id} "
                    f"status={snapshot.path.status}"
                )
                if now - path_invalid_since >= config.path_invalid_grace_sec:
                    if mode == 3:
                        pause_boss_farm(
                            f"{boss_name} {target.object_id} 沒有完整 NavMesh 路徑"
                        )
                        time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                        continue
                    skipped_until[target.object_id] = now + config.target_skip_cooldown_sec
                    announce(
                        f"怪物 {target.object_id} 無完整 NavMesh 路徑，暫時略過。",
                        force=True,
                    )
                    target = None
                    reset_combat_watchdog(combat_watchdog, None, now)
                    publish_navigation_intent(0)
                if config.debug_window:
                    cv2.imshow(
                        RADAR_WINDOW_NAME,
                        draw_radar(snapshot, target, (), True, status, config),
                    )
                    cv2.waitKey(1)
                time.sleep(config.loop_delay_ms / 1000)
                continue
            else:
                path_invalid_since = None
                waypoint = select_path_waypoint(
                    snapshot.player.position,
                    snapshot.path.corners,
                    config.path_waypoint_tolerance_world,
                )
                keys = (
                    movement_keys_for_world_waypoint(snapshot.player, waypoint, config)
                    if waypoint is not None
                    else ()
                )
                status = (
                    f"{'TRAIN ' if mode == 2 else ''}"
                    f"{'CHASE' if send_input else 'PREVIEW'} {target.object_id} "
                    f"D={distance_to_target:.2f} "
                    f"{'KEYS' if send_input else 'WOULD'}="
                    f"{''.join(keys).upper() or '-'}"
                )

                if (
                    send_input
                    and now - chase_started_at >= config.target_max_chase_sec
                ):
                    if mode == 3:
                        pause_boss_farm(
                            f"追蹤 {boss_name} {target.object_id} 超過 "
                            f"{config.target_max_chase_sec:.1f}s"
                        )
                        time.sleep(max(0.05, config.target_lost_wait_ms / 1000))
                        continue
                    skipped_until[target.object_id] = now + config.target_skip_cooldown_sec
                    announce(
                        f"追蹤怪物 {target.object_id} 超過 "
                        f"{config.target_max_chase_sec:.1f}s，暫時略過。",
                        force=True,
                    )
                    target = None
                    reset_combat_watchdog(combat_watchdog, None, now)
                    publish_navigation_intent(0)
                    keys = ()
                elif send_input and keys and unstuck_started_at is None:
                    if progress_anchor is None:
                        progress_anchor = snapshot.player.position
                        progress_started_at = now
                    moved = horizontal_distance(
                        snapshot.player.position, progress_anchor
                    )
                    if moved >= config.stuck_position_epsilon_world:
                        progress_anchor = snapshot.player.position
                        progress_started_at = now
                    elif now - progress_started_at >= config.stuck_timeout_sec:
                        unstuck_started_at = now
                        unstuck_anchor = snapshot.player.position
                        unstuck_attempt = 1
                        announce("世界座標未前進，開始脫困。", force=True)

            if (
                send_input
                and unstuck_started_at is not None
                and snapshot is not None
            ):
                maneuver = unstuck_keys(
                    (now - unstuck_started_at) * 1000, unstuck_side, config
                )
                if maneuver is not None:
                    keys = maneuver
                    status = f"UNSTUCK {unstuck_attempt} {''.join(keys).upper()}"
                else:
                    moved = (
                        horizontal_distance(snapshot.player.position, unstuck_anchor)
                        if unstuck_anchor is not None
                        else 0.0
                    )
                    if moved >= config.unstuck_min_success_world:
                        announce(f"脫困成功，世界位移 {moved:.2f}。", force=True)
                        unstuck_started_at = None
                        unstuck_anchor = None
                        unstuck_attempt = 0
                        unstuck_side = "d" if unstuck_side == "a" else "a"
                        progress_anchor = snapshot.player.position
                        progress_started_at = now
                    elif unstuck_attempt < max(1, config.unstuck_max_attempts):
                        unstuck_attempt += 1
                        unstuck_side = "d" if unstuck_side == "a" else "a"
                        unstuck_started_at = now
                        unstuck_anchor = snapshot.player.position
                        keys = ("s",)
                    else:
                        if mode == 3:
                            pause_boss_farm(
                                f"{boss_name} {target.object_id} 導航脫困失敗"
                            )
                            time.sleep(
                                max(0.05, config.target_lost_wait_ms / 1000)
                            )
                            continue
                        skipped_until[target.object_id] = (
                            now + config.target_skip_cooldown_sec
                        )
                        announce(
                            f"怪物 {target.object_id} 脫困失敗，暫時略過。",
                            force=True,
                        )
                        target = None
                        reset_combat_watchdog(combat_watchdog, None, now)
                        publish_navigation_intent(0)
                        keys = ()
                        unstuck_started_at = None
                        unstuck_anchor = None
                        unstuck_attempt = 0

            desired_keys: tuple[str, ...] = keys
            if (
                send_input
                and target is not None
                and (safe_path or arrived)
                and player_map_exit is None
            ):
                desired_keys = (*desired_keys, *f8_shift_keys(config))
            set_keys(desired_keys)
            if config.debug_window:
                cv2.imshow(
                    RADAR_WINDOW_NAME,
                    draw_radar(
                        snapshot, target, desired_keys, True, status, config
                    ),
                )
                cv2.waitKey(1)
            time.sleep(config.loop_delay_ms / 1000)
    finally:
        finalize_navigation_statistics(refresh_wallet=False)
        equipment_filter_controller.stop()
        equipment_filter_editor.stop()
        if card_purchase_window is not None:
            card_purchase_window.stop()
        if card_purchase_controller is not None:
            card_purchase_controller.stop()
        if pricing_controller is not None:
            pricing_controller.stop()
        close_price_window()
        try:
            write_navigation_request(
                request_path,
                request_id + 1,
                0,
                target_kind="none",
                bot_active=False,
                movement_keys=(),
                shift_keys=(),
                auto_relogin_enabled=config.auto_relogin_enabled,
                auto_relogin_disconnect_grace_sec=config.auto_relogin_disconnect_grace_sec,
                auto_relogin_builtin_wait_max_sec=config.auto_relogin_builtin_wait_max_sec,
                auto_relogin_attempt_timeout_sec=config.auto_relogin_attempt_timeout_sec,
                auto_relogin_retry_delay_sec=config.auto_relogin_retry_delay_sec,
                auto_relogin_max_attempts=config.auto_relogin_max_attempts,
            )
        except OSError:
            pass
        for key in VK_BY_KEY:
            try:
                post_key(hwnd, key, False)
            except Exception:
                pass
        if config.debug_window:
            try:
                cv2.destroyWindow(RADAR_WINDOW_NAME)
            except cv2.error:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SpiritVale 內存敵怪座標與 NavMesh 背景 WASD 導航"
    )
    parser.add_argument("--list-windows", action="store_true", help="列出可見視窗")
    parser.add_argument("--title", help="遊戲視窗標題的一部分")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="設定檔")
    parser.add_argument(
        "--mode-config",
        type=Path,
        default=MODE_CONFIG_PATH,
        help="正常／火車／自動刷王模式設定檔",
    )
    parser.add_argument(
        "--run", action="store_true", help="實際傳送背景 WASD；省略時僅預覽"
    )
    parser.add_argument(
        "--no-loot",
        action="store_true",
        help="停用內存掉落物拾取",
    )
    return parser.parse_args()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    enable_dpi_awareness()
    args = parse_args()
    if args.list_windows:
        for hwnd, title in list_windows():
            print(f"0x{hwnd:08X}  {title}")
        return 0
    try:
        config = load_config(args.config)
        mode_config = load_mode_config(args.mode_config)
        if args.title:
            config.window_title = args.title
            save_config(args.config, config)
        hwnd, title = find_window(config.window_title)
        print(f"已找到視窗：0x{hwnd:08X}  {title}")
        print("正在要求 BepInEx 按需載入 SpiritVale 探針…", flush=True)
        load_result = request_probe_load()
        print(f"探針已就緒：{load_result}", flush=True)
        run_bot(
            hwnd,
            config,
            send_input=args.run,
            config_path=args.config,
            mode=mode_config.mode,
            disable_loot=args.no_loot,
            lock_mouse_to_monster=mode_config.lock_mouse_to_monster,
            left_click_after_mouse_lock=mode_config.left_click_after_mouse_lock,
            boss_name=mode_config.boss_name,
            boss_summon_item_name=mode_config.boss_summon_item_name,
            boss_spawn_timeout_sec=mode_config.boss_spawn_timeout_sec,
            boss_death_confirm_sec=mode_config.boss_death_confirm_sec,
            boss_loot_settle_sec=mode_config.boss_loot_settle_sec,
            boss_use_key_release_settle_sec=(
                mode_config.boss_use_key_release_settle_sec
            ),
        )
    except KeyboardInterrupt:
        print("已中斷；所有按鍵均已放開。")
        return 0
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError, cv2.error) as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
