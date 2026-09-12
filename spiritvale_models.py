"""Shared world snapshots and per-feature state, independent of I/O."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MemoryPlayer:
    position: tuple[float, float, float]
    camera_forward_xz: tuple[float, float]
    camera_right_xz: tuple[float, float]
    collider_radius: float
    is_mounted_summon: bool = False
    is_mountable_summon: bool = False
    active_summon_count: int = 0
    has_primary_summon: bool = False
    summon_id: str = ""
    mounted_summon_state_available: bool = False
    summon_mount_action_available: bool = False
    summon_displays_available: bool = False
    summon_displays_error: str = ""
    summon_display_skill_ids: tuple[str, ...] = ()
    active_statuses_available: bool = False
    active_statuses_error: str = ""
    active_status_ids: tuple[str, ...] = ()
    guardian_bond_available: bool = False
    guardian_bond_error: str = ""
    guardian_bond_active: bool = False
    guardian_bond_candidate_id: int = 0
    guardian_bond_cast_error: str = ""
    wallet_coins: int = 0
    wallet_coins_available: bool = False
    wallet_coins_error: str = ""
    alive: bool = True


@dataclass(frozen=True)
class MemoryObservedPlayer:
    object_id: int
    player_id: str
    display_name: str
    position: tuple[float, float, float]
    collider_radius: float
    alive: bool
    visible: bool
    party_member: bool
    selected: bool


@dataclass(frozen=True)
class MemoryPartyMember:
    display_name: str
    player_id: str
    object_id: int
    map_id: int
    instance_id: str
    channel_index: int
    is_local: bool


@dataclass(frozen=True)
class MemoryMonster:
    object_id: int
    config_id: str
    display_name: str
    rank: str
    position: tuple[float, float, float]
    health_ratio: float
    collider_radius: float
    team: str = "enemy"
    alive: bool = True
    visible: bool = True
    training_dummy: bool = False
    viewport_position: tuple[float, float, float] | None = None
    viewport_visible: bool = False
    # Numeric level parsed from display_name ("Lv.40" -> 40); 0 when absent.
    level: int = 0
    # True only for the detected boss while avoid_boss is enabled: the bot must
    # keep away from it. False means the monster is a normal, attackable target.
    avoid: bool = False


@dataclass(frozen=True)
class MemoryLoot:
    object_id: int
    item_id: str
    display_name: str
    sprite_id: str
    rarity: str
    rarity_value: int
    loot_type: str
    position: tuple[float, float, float]
    viewport_position: tuple[float, float, float]
    viewport_visible: bool
    locked: bool
    owner_player_id: str
    owner_party_id: int
    owned_by_local_player: bool
    interaction_range: float


@dataclass(frozen=True)
class MemoryMapExit:
    position: tuple[float, float, float]
    interaction_range: float


@dataclass(frozen=True)
class MemoryPath:
    request_id: int
    target_object_id: int
    status: str
    corners: tuple[tuple[float, float, float], ...]
    target_kind: str = "monster"


@dataclass(frozen=True)
class MemoryConsumableUse:
    request_id: int = 0
    status: str = "idle"
    item_id: str = ""
    display_name: str = ""
    remaining_count: int = -1
    error: str = ""


@dataclass(frozen=True)
class MemorySnapshot:
    timestamp_ms: int
    map_id: int
    instance_id: int
    player: MemoryPlayer
    monsters: tuple[MemoryMonster, ...]
    path: MemoryPath
    channel_index: int = -1
    channel_count: int = 0
    players: tuple[MemoryObservedPlayer, ...] = ()
    party_members: tuple[MemoryPartyMember, ...] = ()
    party_state_available: bool = False
    loots: tuple[MemoryLoot, ...] = ()
    map_exits: tuple[MemoryMapExit, ...] = ()
    map_exit_state_available: bool = True
    player_scan: dict[str, object] | None = None
    monster_scan: dict[str, object] | None = None
    loot_scan: dict[str, object] | None = None
    consumable_use: MemoryConsumableUse = MemoryConsumableUse()


@dataclass
class CombatWatchdogState:
    target_object_id: int | None = None
    best_health_ratio: float = 1.0
    last_progress_at: float = 0.0
    was_in_range: bool = False
    reengage_attempted: bool = False
    reposition_started_at: float | None = None


@dataclass
class LootChaseState:
    target_object_id: int | None = None
    started_at: float = 0.0
    path_invalid_since: float | None = None
    progress_anchor: tuple[float, float, float] | None = None
    progress_started_at: float = 0.0
    unstuck_started_at: float | None = None
    unstuck_anchor: tuple[float, float, float] | None = None
    unstuck_attempt: int = 0
    unstuck_side: str = "a"
    release_started_at: float | None = None


@dataclass
class SummonMountKeyState:
    phase: str = "idle"
    stage_started_at: float = 0.0
    next_mount_retry_at: float = 0.0
    retry_after: float = 0.0
    error: str = ""


@dataclass
class SummonerCheckState:
    phase: str = "idle"
    item_id: str = ""
    settle_until: float = 0.0
    retry_after: dict[str, float] = field(default_factory=dict)
    error: str = ""


@dataclass
class NavigationEarningsState:
    session_active: bool = False
    tracking_active: bool = False
    segment_started_at: float = 0.0
    elapsed_seconds: float = 0.0
    gross_income: int = 0
    last_wallet_coins: int | None = None
    current_wallet_coins: int | None = None
    last_snapshot_timestamp_ms: int = 0
    wallet_sample_count: int = 0
    data_incomplete: bool = False
    final_balance_from_last_sample: bool = False


@dataclass(frozen=True)
class NavigationEarningsReport:
    elapsed_seconds: float
    gross_income: int
    current_wallet_coins: int | None
    wallet_sample_count: int
    data_incomplete: bool
    final_balance_from_last_sample: bool


@dataclass
class BossFarmState:
    phase: str = "startup"
    tracked_boss_object_id: int | None = None
    boss_missing_since: float | None = None
    loot_settle_until: float = 0.0
    use_request_id: int = 0
    use_requested_at: float = 0.0
    key_release_started_at: float | None = None
    fault: str = ""


class SnapshotUnavailable(RuntimeError):
    """The probe state cannot safely drive movement."""
