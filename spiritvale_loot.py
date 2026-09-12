"""Loot eligibility, approach recovery, and pickup decisions without game I/O."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal
from spiritvale_config import BotConfig
from spiritvale_models import (
    LootChaseState,
    MemoryLoot,
    MemoryPlayer,
    MemorySnapshot,
)
from spiritvale_navigation import (
    horizontal_distance,
    request_path_matches,
    path_enters_map_exit_keepout,
    select_path_waypoint,
    movement_keys_for_world_waypoint,
    unstuck_keys,
)


@dataclass(frozen=True)
class LootNotice:
    message: str
    force: bool = False
    dedupe_key: str | None = None


@dataclass(frozen=True)
class LootApproachDecision:
    movement_keys: tuple[str, ...]
    path_ready: bool
    failure_reason: str | None
    status: str
    notices: tuple[LootNotice, ...] = ()


@dataclass(frozen=True)
class LootInteractionDecision:
    phase: Literal['confirm', 'chase', 'release', 'interact', 'stop']
    started_release: bool = False
    wait_seconds: float = 0.0
    interaction_due: bool = False
    pickup_object_id: int | None = None


def plan_loot_interaction(
    state: LootChaseState,
    player: MemoryPlayer,
    loot: MemoryLoot,
    config: BotConfig,
    *,
    now: float,
    confirmed_frames: int,
    last_interact_at: float,
    send_input: bool,
    in_exit_keepout: bool = False,
    enabled: bool = True,
) -> LootInteractionDecision:
    """Advance pickup preparation without sending keys or writing IPC.

    The caller must release movement/skills before executing pickup_object_id.
    Cooldown is session-wide: only the caller records a dispatched (or previewed)
    interaction, so changing targets does not reset the retry budget.
    """
    if not enabled or not player.alive:
        state.release_started_at = None
        return LootInteractionDecision('stop')
    if confirmed_frames < max(1, config.memory_loot_confirm_frames):
        return LootInteractionDecision('confirm')

    in_range = loot_is_within_pickup_range(
        player, loot,
        range_padding_world=config.memory_loot_range_padding_world,
        max_distance_world=config.memory_loot_max_distance_world,
    )
    holding_range = (
        state.release_started_at is not None
        and horizontal_distance(player.position, loot.position)
        <= loot_pickup_hold_radius(
            player, loot,
            range_padding_world=config.memory_loot_range_padding_world,
            hysteresis_world=config.memory_loot_pickup_hysteresis_world,
            max_distance_world=config.memory_loot_max_distance_world,
        )
    )
    if in_exit_keepout or not (in_range or holding_range):
        state.release_started_at = None
        return LootInteractionDecision('chase')

    started = state.release_started_at is None
    if started:
        state.release_started_at = now
    wait = max(0.0, config.memory_loot_release_settle_ms / 1000
               - (now - state.release_started_at))
    if wait > 0:
        return LootInteractionDecision('release', started, wait)
    due = now - last_interact_at >= config.memory_loot_interact_cooldown_ms / 1000
    return LootInteractionDecision(
        'interact', started_release=started, interaction_due=due,
        pickup_object_id=loot.object_id if due and send_input else None,
    )


def loot_is_equipment(loot: MemoryLoot) -> bool:
    return loot.loot_type.strip().casefold() in {"equip", "equipment"}


def select_boss_legendary_loot(
    loots: Iterable[MemoryLoot],
    player_position: tuple[float, float, float],
    previous_object_id: int | None = None,
) -> MemoryLoot | None:
    candidates = [
        loot
        for loot in loots
        if loot.owned_by_local_player and loot.rarity_value >= LOOT_RARITY_VALUES["legendary"]
    ]
    if previous_object_id is not None:
        previous = next(
            (loot for loot in candidates if loot.object_id == previous_object_id),
            None,
        )
        if previous is not None:
            return previous
    return (
        min(
            candidates,
            key=lambda loot: horizontal_distance(player_position, loot.position),
        )
        if candidates
        else None
    )


LOOT_RARITY_VALUES = {
    "common": 0,
    "rare": 1,
    "unique": 2,
    "legendary": 3,
}


def loot_minimum_rarity_value(value: str | int) -> int:
    if isinstance(value, int):
        return min(3, max(0, value))
    normalized = str(value).strip().casefold()
    if normalized not in LOOT_RARITY_VALUES:
        raise ValueError(
            "memory_loot_min_rarity must be Common, Rare, Unique, or Legendary"
        )
    return LOOT_RARITY_VALUES[normalized]


def loot_ownership_label(loot: MemoryLoot) -> str:
    if loot.owned_by_local_player:
        return "OWN"
    return "FOREIGN" if loot.owner_player_id else "PUBLIC"


def select_memory_loot(
    loots: Iterable[MemoryLoot],
    player: MemoryPlayer,
    minimum_rarity: str | int,
    previous_object_id: int | None = None,
    *,
    skipped_until: dict[int, float] | None = None,
    now: float = 0.0,
    range_padding_world: float = 0.75,
    max_distance_world: float = 3.0,
) -> MemoryLoot | None:
    minimum = loot_minimum_rarity_value(minimum_rarity)
    active_skips = {
        object_id: expiry
        for object_id, expiry in (skipped_until or {}).items()
        if expiry > now
    }
    eligible: list[MemoryLoot] = []
    for loot in loots:
        if loot.locked or loot_is_equipment(loot):
            continue
        if loot.rarity_value >= minimum:
            eligible.append(loot)
    nearby = [
        loot
        for loot in eligible
        if loot_is_within_pickup_range(
            player,
            loot,
            range_padding_world=range_padding_world,
            max_distance_world=max_distance_world,
        )
    ]
    if previous_object_id is not None:
        previous = next(
            (loot for loot in nearby if loot.object_id == previous_object_id), None
        )
        if previous is not None:
            return previous
    if nearby:
        return min(
            nearby,
            key=lambda loot: (
                horizontal_distance(player.position, loot.position),
                -loot.rarity_value,
                loot.object_id,
            ),
        )
    remote_owned = [
        loot
        for loot in eligible
        if loot.owned_by_local_player and loot.object_id not in active_skips
    ]
    if previous_object_id is not None:
        previous = next(
            (
                loot
                for loot in remote_owned
                if loot.object_id == previous_object_id
            ),
            None,
        )
        if previous is not None:
            return previous
    return min(
        remote_owned,
        key=lambda loot: (
            -loot.rarity_value,
            horizontal_distance(player.position, loot.position),
            loot.object_id,
        ),
        default=None,
    )


def loot_pickup_radius(
    player: MemoryPlayer,
    loot: MemoryLoot,
    *,
    range_padding_world: float,
    max_distance_world: float,
) -> float:
    # The server accepts pickup only when the player *center* is within the
    # loot's InteractionRange; it does NOT credit the player's collider radius
    # (empirically a 2.83-world-unit centre gap was rejected at IR=1.0 with a
    # 2.0 collider). Approaching by interaction_range plus a small (often
    # negative) padding, without adding collider_radius, keeps the press point
    # inside the range the game actually honours.
    interaction_radius = max(0.0, loot.interaction_range) + range_padding_world
    return min(max(0.0, max_distance_world), max(0.0, interaction_radius))


def loot_is_within_pickup_range(
    player: MemoryPlayer,
    loot: MemoryLoot,
    *,
    range_padding_world: float,
    max_distance_world: float,
) -> bool:
    return horizontal_distance(player.position, loot.position) <= loot_pickup_radius(
        player,
        loot,
        range_padding_world=range_padding_world,
        max_distance_world=max_distance_world,
    )


def loot_pickup_hold_radius(
    player: MemoryPlayer,
    loot: MemoryLoot,
    *,
    range_padding_world: float,
    hysteresis_world: float,
    max_distance_world: float,
) -> float:
    """Return the safe exit radius after pickup preparation has started.

    The entry radius may intentionally sit inside ``InteractionRange`` (for
    example 0.8 for a 1.0-range drop).  Once all keys are being released, keep
    the player stopped through small snapshot/movement overshoot, but never
    widen the hold radius past the server's real interaction range.
    """
    entry_radius = loot_pickup_radius(
        player,
        loot,
        range_padding_world=range_padding_world,
        max_distance_world=max_distance_world,
    )
    server_radius = min(
        max(0.0, max_distance_world),
        max(0.0, loot.interaction_range),
    )
    return max(
        entry_radius,
        min(
            server_radius,
            entry_radius + max(0.0, hysteresis_world),
        ),
    )


def reset_loot_chase(
    state: LootChaseState,
    *,
    now: float,
    target_object_id: int | None = None,
    player_position: tuple[float, float, float] | None = None,
) -> None:
    state.target_object_id = target_object_id
    state.started_at = now
    state.path_invalid_since = None
    state.progress_anchor = player_position
    state.progress_started_at = now
    state.unstuck_started_at = None
    state.unstuck_anchor = None
    state.unstuck_attempt = 0
    state.release_started_at = None


def loot_chase_failure_reason(
    state: LootChaseState,
    *,
    now: float,
    path_invalid_grace_sec: float,
    chase_timeout_sec: float,
    enforce_timeout: bool,
    unstuck_failed: bool = False,
) -> str | None:
    if unstuck_failed:
        return "unstuck"
    if (
        state.path_invalid_since is not None
        and now - state.path_invalid_since >= max(0.0, path_invalid_grace_sec)
    ):
        return "path"
    if enforce_timeout and now - state.started_at >= max(0.1, chase_timeout_sec):
        return "timeout"
    return None


def track_memory_loot_candidate(
    selected: MemoryLoot | None,
    previous_object_id: int | None,
    previous_frames: int,
) -> tuple[int | None, int]:
    if selected is None:
        return None, 0
    if selected.object_id == previous_object_id:
        return selected.object_id, previous_frames + 1
    return selected.object_id, 1


def plan_loot_approach(
    snapshot: MemorySnapshot,
    loot_target: MemoryLoot,
    loot_chase: LootChaseState,
    config: BotConfig,
    *,
    request_id: int,
    now: float,
    send_input: bool,
    loot_rule_label: str,
) -> LootApproachDecision:
    """Evaluate a loot path and advance chase recovery, with no external I/O.

    Request the loot path before calling this function, then pass the request
    ID actually written. This preserves rejection of paths for older targets.
    Failure handling (retry versus pausing boss farming) belongs to the caller.
    """
    notices: list[LootNotice] = []

    def announce(message: str, *, force: bool = False,
                 dedupe_key: str | None = None) -> None:
        notices.append(LootNotice(message, force, dedupe_key))

    distance_to_loot = horizontal_distance(snapshot.player.position, loot_target.position)
    safe_loot_path = request_path_matches(
        snapshot.path,
        request_id,
        loot_target.object_id,
        target_kind="loot",
    )
    loot_keys: tuple[str, ...] = ()
    failure_reason: str | None = None
    if safe_loot_path and path_enters_map_exit_keepout(
        snapshot.player,
        snapshot.path.corners,
        snapshot.map_exits,
        config.map_exit_avoidance_padding_world,
    ) is not None:
        safe_loot_path = False
        failure_reason = "map_exit"
    if safe_loot_path:
        loot_chase.path_invalid_since = None
        waypoint = select_path_waypoint(
            snapshot.player.position,
            snapshot.path.corners,
            config.path_waypoint_tolerance_world,
        )
        loot_keys = (
            movement_keys_for_world_waypoint(
                snapshot.player, waypoint, config
            )
            if waypoint is not None
            else ()
        )
        status = (
            f"{'OWN LOOT CHASE' if send_input else 'WOULD CHASE OWN LOOT'} "
            f"{loot_target.object_id} D={distance_to_loot:.2f} "
            f"{'KEYS' if send_input else 'WOULD'}="
            f"{''.join(loot_keys).upper() or '-'}"
        )

        if send_input and loot_keys and loot_chase.unstuck_started_at is None:
            if loot_chase.progress_anchor is None:
                loot_chase.progress_anchor = snapshot.player.position
                loot_chase.progress_started_at = now
            moved = horizontal_distance(
                snapshot.player.position, loot_chase.progress_anchor
            )
            if moved >= config.stuck_position_epsilon_world:
                loot_chase.progress_anchor = snapshot.player.position
                loot_chase.progress_started_at = now
            elif now - loot_chase.progress_started_at >= config.stuck_timeout_sec:
                loot_chase.unstuck_started_at = now
                loot_chase.unstuck_anchor = snapshot.player.position
                loot_chase.unstuck_attempt = 1
                announce(
                    f"{loot_rule_label} {loot_target.object_id} "
                    "導航未前進，開始脫困。",
                    force=True,
                )

        if send_input and loot_chase.unstuck_started_at is not None:
            maneuver = unstuck_keys(
                (now - loot_chase.unstuck_started_at) * 1000,
                loot_chase.unstuck_side,
                config,
            )
            if maneuver is not None:
                loot_keys = maneuver
                status = (
                    f"LOOT UNSTUCK {loot_target.object_id} "
                    f"{loot_chase.unstuck_attempt} "
                    f"{''.join(loot_keys).upper()}"
                )
            else:
                moved = (
                    horizontal_distance(
                        snapshot.player.position,
                        loot_chase.unstuck_anchor,
                    )
                    if loot_chase.unstuck_anchor is not None
                    else 0.0
                )
                if moved >= config.unstuck_min_success_world:
                    announce(
                        f"{loot_rule_label}導航脫困成功，"
                        f"世界位移 {moved:.2f}。",
                        force=True,
                    )
                    loot_chase.unstuck_started_at = None
                    loot_chase.unstuck_anchor = None
                    loot_chase.unstuck_attempt = 0
                    loot_chase.unstuck_side = (
                        "d" if loot_chase.unstuck_side == "a" else "a"
                    )
                    loot_chase.progress_anchor = snapshot.player.position
                    loot_chase.progress_started_at = now
                elif loot_chase.unstuck_attempt < max(
                    1, config.unstuck_max_attempts
                ):
                    loot_chase.unstuck_attempt += 1
                    loot_chase.unstuck_side = (
                        "d" if loot_chase.unstuck_side == "a" else "a"
                    )
                    loot_chase.unstuck_started_at = now
                    loot_chase.unstuck_anchor = snapshot.player.position
                    loot_keys = ("s",)
                else:
                    failure_reason = "unstuck"
    else:
        loot_chase.path_invalid_since = (
            loot_chase.path_invalid_since or now
        )
        status = (
            f"LOOT WAIT PATH request={request_id} "
            f"response={snapshot.path.request_id} "
            f"kind={snapshot.path.target_kind} "
            f"status={snapshot.path.status}"
        )
        if (
            snapshot.path.request_id == request_id
            and snapshot.path.target_object_id == loot_target.object_id
            and snapshot.path.target_kind != "loot"
        ):
            announce(
                f"{loot_rule_label}導航需要新版探針；"
                "請安裝新版 DLL 並重啟遊戲。",
                dedupe_key="loot_target_kind_probe_upgrade_required",
            )

    failure_reason = failure_reason or loot_chase_failure_reason(
        loot_chase,
        now=now,
        path_invalid_grace_sec=config.path_invalid_grace_sec,
        chase_timeout_sec=config.memory_loot_chase_timeout_sec,
        enforce_timeout=send_input,
    )
    return LootApproachDecision(
        loot_keys, safe_loot_path, failure_reason, status, tuple(notices),
    )
