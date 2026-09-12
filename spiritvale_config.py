"""Configuration schema, defaults, validation, and JSON persistence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
import math


VK_BY_KEY = {
    "0": ord("0"),
    "9": ord("9"),
    "w": ord("W"),
    "a": ord("A"),
    "s": ord("S"),
    "d": ord("D"),
    "v": ord("V"),
    "lshift": 0xA0,
    "rshift": 0xA1,
}


# Fixed game attack bindings. These are attacks, not movement modifiers.
ATTACK_KEYS = ("lshift", "rshift")
# Compatibility for existing diagnostics and imports.
HELD_SHIFT_KEYS = ATTACK_KEYS


JOB_TYPE_LABELS = {
    0: "未滿 64 等",
    1: "召喚",
    2: "牧師",
}


NAVIGATION_ATTACK_KEYS_BY_JOB_TYPE = {
    0: ("lshift",),
    1: ATTACK_KEYS,
    2: (),
}
F8_SHIFT_KEYS_BY_JOB_TYPE = NAVIGATION_ATTACK_KEYS_BY_JOB_TYPE


# These jobs must finish summon/buff and mount upkeep before navigation inputs.
NAVIGATION_UPKEEP_JOB_TYPES = frozenset({1})


SUMMONER_CHECK_ORDER = (
    "SummonSkeleton",
    "SummonAbomination",
    "SummonSkeletonMage",
    "Invoker",
    "Conjurer",
    "DeathBramble",
    "GuardianBond",
)


SUMMONER_SUMMON_IDS = frozenset(SUMMONER_CHECK_ORDER[:3])


SUMMONER_BUFF_IDS = frozenset(SUMMONER_CHECK_ORDER[3:])


# The probe must resolve an owned summon and target the skill in the same input.
SUMMONER_TARGET_SUMMON_IDS = frozenset({"GuardianBond"})


SUMMONER_CHECK_LABELS = {
    "SummonSkeleton": "Summon Skeleton",
    "SummonAbomination": "Summon Abomination",
    "SummonSkeletonMage": "Summon Skeleton Mage",
    "Invoker": "Invoker",
    "Conjurer": "Conjurer",
    "DeathBramble": "Necrotic Presence",
    "GuardianBond": "Guardian Bond",
}


NUMPAD_SKILL_KEYS = tuple(f"numpad{number}" for number in range(10))


def default_summoner_checks() -> dict[str, dict[str, object]]:
    return {
        check_id: {"enabled": False, "key": ""}
        for check_id in SUMMONER_CHECK_ORDER
    }


@dataclass
class BotConfig:
    window_title: str = "SpiritVale"
    loop_delay_ms: int = 25
    target_lost_wait_ms: int = 100
    memory_snapshot_timeout_ms: int = 750
    axis_deadzone_ratio: float = 0.28
    arrival_padding_world: float = 0.75
    map_exit_avoidance_padding_world: float = 3.0
    path_waypoint_tolerance_world: float = 0.35
    target_max_chase_sec: float = 8.0
    target_skip_cooldown_sec: float = 15.0
    path_invalid_grace_sec: float = 1.0
    combat_health_progress_epsilon: float = 0.001
    combat_no_progress_sec: float = 6.0
    combat_reengage_back_ms: int = 450
    combat_reengage_side_ms: int = 650
    combat_blacklist_absence_reset_sec: float = 5.0
    stuck_timeout_sec: float = 1.6
    stuck_position_epsilon_world: float = 0.2
    unstuck_back_ms: int = 450
    unstuck_back_diagonal_ms: int = 550
    unstuck_side_ms: int = 500
    unstuck_diagonal_ms: int = 700
    unstuck_return_ms: int = 550
    unstuck_forward_ms: int = 350
    unstuck_min_success_world: float = 0.8
    unstuck_max_attempts: int = 2
    memory_loot_min_rarity: str = "Legendary"
    memory_loot_range_padding_world: float = 0.75
    # Once pickup preparation starts, tolerate small position jitter up to the
    # loot's real interaction radius instead of restarting the release timer.
    memory_loot_pickup_hysteresis_world: float = 0.25
    memory_loot_max_distance_world: float = 3.0
    memory_loot_confirm_frames: int = 2
    # Keep every movement/Shift key released long enough for the probe to
    # observe a neutral request before sending the targeted loot click.
    memory_loot_release_settle_ms: int = 50
    memory_loot_interact_cooldown_ms: int = 500
    memory_loot_clear_confirm_frames: int = 5
    memory_loot_chase_timeout_sec: float = 20.0
    memory_loot_retry_cooldown_sec: float = 15.0
    auto_relogin_enabled: bool = True
    auto_relogin_disconnect_grace_sec: float = 3.0
    auto_relogin_builtin_wait_max_sec: float = 30.0
    auto_relogin_attempt_timeout_sec: float = 30.0
    auto_relogin_retry_delay_sec: float = 10.0
    auto_relogin_max_attempts: int = 5
    debug_window: bool = False
    # When true the bot launches idle (navigation off); open the F8 menu and
    # pick 一般導航 to start. Default false keeps the classic --run behavior of
    # starting to navigate immediately.
    start_paused: bool = False
    radar_size_px: int = 660
    pricing_enabled: bool = True
    pricing_auto_start: bool = False
    pricing_window_enabled: bool = True
    pricing_high_value_threshold: int = 50_000
    pricing_page_rows: int = 8
    pricing_timeout_sec: float = 25.0
    pricing_request_delay_sec: float = 0.2
    follow_player_enabled: bool = True
    follow_monster_radius_world: float = 50.0
    # Boss avoidance: the map boss is detected as the strictly-highest-level,
    # unique living enemy. When avoid_boss is true the bot never targets it.
    # boss_response picks what else it does: "switch_channel" hops to the next
    # channel (current+1, wrapping) so the fresh instance is boss-free;
    # "flee" instead walks away whenever the boss comes within
    # boss_flee_radius_world. switch_channel falls back to flee for any frame
    # where channel data is not yet known.
    avoid_boss: bool = False
    boss_response: str = "switch_channel"
    boss_flee_radius_world: float = 15.0
    boss_channel_switch_settle_sec: float = 6.0
    follow_player_stop_padding_world: float = 2.0
    follow_player_rejoin_distance_world: float = 10.0
    _comment_job_type: str = (
        "0=未滿64等；1=召喚；2=牧師（一般導航每 300-1300ms 短按 Left Shift）"
    )
    job_type: int = 1
    priest_left_shift_tap_hold_ms: int = 50
    priest_left_shift_tap_min_interval_ms: int = 300
    priest_left_shift_tap_max_interval_ms: int = 1300
    summon_reanimation_key: str = "9"
    summon_mount_key: str = "0"
    summon_skill_key_hold_ms: int = 50
    summon_reanimation_delay_ms: int = 750
    summon_mount_confirm_timeout_ms: int = 4000
    summon_mount_key_retry_delay_ms: int = 400
    summon_mount_retry_delay_ms: int = 2500
    summoner_checks: dict[str, dict[str, object]] = field(
        default_factory=default_summoner_checks
    )
    summoner_check_settle_ms: int = 500
    summoner_check_retry_delay_ms: int = 800


@dataclass(frozen=True)
class ModeConfig:
    mode: int = 1
    boss_name: str = ""
    boss_summon_item_name: str = ""
    boss_spawn_timeout_sec: float = 10.0
    boss_death_confirm_sec: float = 1.0
    boss_loot_settle_sec: float = 3.0
    boss_use_key_release_settle_sec: float = 0.25
    lock_mouse_to_monster: bool = False
    left_click_after_mouse_lock: bool = False


def load_config(path: Path) -> BotConfig:
    if not path.exists():
        config = BotConfig()
        save_config(path, config)
        return config
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    known = BotConfig.__dataclass_fields__
    config = BotConfig(**{key: value for key, value in raw.items() if key in known})
    if type(config.job_type) is not int or config.job_type not in (0, 1, 2):
        raise ValueError(
            "job_type must be 0 (under level 64), 1 (summoner), or 2 (priest)"
        )
    if type(config.avoid_boss) is not bool:
        raise ValueError("avoid_boss must be true or false")
    if config.boss_response not in {"flee", "switch_channel"}:
        raise ValueError("boss_response must be flee or switch_channel")
    if config.boss_flee_radius_world < 0:
        raise ValueError("boss_flee_radius_world must be non-negative")
    if config.boss_channel_switch_settle_sec < 0:
        raise ValueError("boss_channel_switch_settle_sec must be non-negative")
    if config.summon_reanimation_key not in VK_BY_KEY:
        raise ValueError("summon_reanimation_key is not a supported key")
    if config.summon_mount_key not in VK_BY_KEY:
        raise ValueError("summon_mount_key is not a supported key")
    config.summoner_checks = normalize_summoner_checks(config.summoner_checks)
    if min(
        config.memory_loot_release_settle_ms,
        config.memory_loot_interact_cooldown_ms,
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
    return config


def normalize_summoner_checks(
    value: object,
) -> dict[str, dict[str, object]]:
    """Return the fixed summoner check configuration (one entry per check)."""
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError("summoner_checks must be an object")
    normalized = default_summoner_checks()
    for check_id in SUMMONER_CHECK_ORDER:
        raw = value.get(check_id, {})
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise ValueError(f"summoner_checks.{check_id} must be an object")
        enabled = raw.get("enabled", False)
        if type(enabled) is not bool:
            raise ValueError(
                f"summoner_checks.{check_id}.enabled must be true or false"
            )
        key = str(raw.get("key", "") or "").strip().casefold()
        if key and key not in NUMPAD_SKILL_KEYS:
            raise ValueError(
                f"summoner_checks.{check_id}.key must be numpad0 through numpad9"
            )
        if enabled and not key:
            raise ValueError(
                f"summoner_checks.{check_id} is enabled but has no NumPad key"
            )
        normalized[check_id] = {"enabled": enabled, "key": key}
    return normalized


def load_mode_config(path: Path) -> ModeConfig:
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError("mode config must be a JSON object")
    mode = raw.get("mode")
    if type(mode) is not int or mode not in (1, 2, 3):
        raise ValueError("mode must be 1 (normal), 2 (train), or 3 (boss farm)")
    boss_name = str(raw.get("boss_name", "")).strip()
    boss_summon_item_name = str(raw.get("boss_summon_item_name", "")).strip()
    if mode == 3 and not boss_name:
        raise ValueError("boss_name is required for mode 3")
    if mode == 3 and not boss_summon_item_name:
        raise ValueError("boss_summon_item_name is required for mode 3")
    timings: dict[str, float] = {}
    for key, default in (
        ("boss_spawn_timeout_sec", 10.0),
        ("boss_death_confirm_sec", 1.0),
        ("boss_loot_settle_sec", 3.0),
        ("boss_use_key_release_settle_sec", 0.25),
    ):
        try:
            value = float(raw.get(key, default))
        except (TypeError, ValueError) as error:
            raise ValueError(f"{key} must be a finite non-negative number") from error
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{key} must be a finite non-negative number")
        timings[key] = value
    lock_mouse_to_monster = raw.get("lock_mouse_to_monster", False)
    if type(lock_mouse_to_monster) is not bool:
        raise ValueError("lock_mouse_to_monster must be true or false")
    left_click_after_mouse_lock = raw.get("left_click_after_mouse_lock", False)
    if type(left_click_after_mouse_lock) is not bool:
        raise ValueError("left_click_after_mouse_lock must be true or false")
    return ModeConfig(
        mode=mode,
        boss_name=boss_name,
        boss_summon_item_name=boss_summon_item_name,
        boss_spawn_timeout_sec=timings["boss_spawn_timeout_sec"],
        boss_death_confirm_sec=timings["boss_death_confirm_sec"],
        boss_loot_settle_sec=timings["boss_loot_settle_sec"],
        boss_use_key_release_settle_sec=timings[
            "boss_use_key_release_settle_sec"
        ],
        lock_mouse_to_monster=lock_mouse_to_monster,
        left_click_after_mouse_lock=left_click_after_mouse_lock,
    )


def save_config(path: Path, config: BotConfig) -> None:
    path.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


MODE_NAMES = {
    1: "正常",
    2: "火車",
    3: "自動刷王",
}
