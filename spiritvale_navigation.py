"""Target selection, path geometry, follow distances, and combat recovery."""

from __future__ import annotations

from typing import Iterable
import math
import re
from spiritvale_config import (
    BotConfig,
)
from spiritvale_models import (
    CombatWatchdogState,
    MemoryMapExit,
    MemoryMonster,
    MemoryObservedPlayer,
    MemoryPartyMember,
    MemoryPath,
    MemoryPlayer,
)


_MONSTER_LEVEL_PATTERN = re.compile(r"Lv\.?\s*(\d+)", re.IGNORECASE)
_RICH_TEXT_PATTERN = re.compile(r"<[^>]*>")
_TRAILING_LEVEL_PATTERN = re.compile(r"\s*Lv\.?\s*\d+\s*$", re.IGNORECASE)


def parse_monster_level(display_name: str) -> int:
    """Extract the numeric level embedded in a monster display name.

    Names arrive as e.g. ``"Scorpion King <sprite ...> Lv.40"``; the level is
    the only per-monster ordering signal the probe exposes, so we lift it out of
    the label. Returns 0 when no ``Lv.NN`` token is present.
    """
    match = _MONSTER_LEVEL_PATTERN.search(display_name or "")
    return int(match.group(1)) if match else 0


def detect_boss_object_id(monsters: Iterable[MemoryMonster]) -> int | None:
    """Identify the map boss as the strictly-highest-level, unique monster.

    The game reports every monster (boss included) with rank "Normal", so rank
    cannot distinguish the boss. Empirically the boss is the single monster whose
    level tops the map (e.g. a lone Lv.40 among Lv.31-35 trash). Returns that
    monster's object_id, or None when nothing stands out cleanly: no levels
    parsed, or two or more monsters share the top level.
    """
    ranked = [(m.level, m.object_id) for m in monsters if m.level > 0]
    if not ranked:
        return None
    top_level = max(level for level, _ in ranked)
    top = [object_id for level, object_id in ranked if level == top_level]
    if len(top) != 1:
        return None
    return top[0]


def normalize_boss_name(value: str) -> str:
    """Normalize a config/display boss name without weakening exact matching."""
    # The in-game display name puts the monster name on the first line and an
    # element/level decoration on the next, e.g.
    # "Lady Fey\n<sprite name=holy> <color=#FCE9EBFF>Holy</color> Lv.40".
    # Stripping the rich-text tags leaves the element word ("Holy") as plain
    # text, so the whole string would normalize to "lady fey holy" and never
    # match a boss_name of "Lady Fey". Keep only the first line (the name).
    first_line = str(value or "").split("\n", 1)[0]
    plain = _RICH_TEXT_PATTERN.sub(" ", first_line)
    plain = _TRAILING_LEVEL_PATTERN.sub("", plain)
    return " ".join(plain.split()).casefold()


def monster_matches_boss(monster: MemoryMonster, boss_name: str) -> bool:
    wanted = normalize_boss_name(boss_name)
    return bool(wanted) and wanted in {
        normalize_boss_name(monster.config_id),
        normalize_boss_name(monster.display_name),
    }


def select_boss_farm_target(
    monsters: Iterable[MemoryMonster],
    player_position: tuple[float, float, float],
    boss_name: str,
    previous_object_id: int | None = None,
) -> MemoryMonster | None:
    candidates = [
        monster
        for monster in monsters
        if monster_matches_boss(monster, boss_name)
        and monster.team == "enemy"
        and monster.alive
        and monster.visible
        and not monster.training_dummy
        and monster.health_ratio > 0.0
    ]
    if previous_object_id is not None:
        previous = next(
            (
                monster
                for monster in candidates
                if monster.object_id == previous_object_id
            ),
            None,
        )
        if previous is not None:
            return previous
    return (
        min(
            candidates,
            key=lambda monster: horizontal_distance(
                player_position, monster.position
            ),
        )
        if candidates
        else None
    )


def horizontal_distance(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> float:
    return math.hypot(left[0] - right[0], left[2] - right[2])


def should_advance_train_target(
    mode: int,
    *,
    arrived: bool,
    send_input: bool,
) -> bool:
    """Only a running train-mode bot switches immediately on arrival."""
    return mode == 2 and arrived and send_input


def select_memory_target(
    monsters: Iterable[MemoryMonster],
    player_position: tuple[float, float, float],
    previous_object_id: int | None,
    skipped_until: dict[int, float],
    *,
    now: float,
    blocked_object_ids: set[int] | frozenset[int] = frozenset(),
) -> tuple[MemoryMonster | None, dict[int, float]]:
    active_skips = {
        object_id: expiry for object_id, expiry in skipped_until.items() if expiry > now
    }
    candidates = [
        monster
        for monster in monsters
        if monster.team == "enemy"
        and monster.alive
        and monster.visible
        and not monster.training_dummy
        and monster.health_ratio > 0.0
        and not monster.avoid
        and monster.object_id not in active_skips
        and monster.object_id not in blocked_object_ids
    ]
    if previous_object_id is not None:
        previous = next(
            (monster for monster in candidates if monster.object_id == previous_object_id),
            None,
        )
        if previous is not None:
            return previous, active_skips
    if not candidates:
        return None, active_skips
    return (
        min(candidates, key=lambda monster: horizontal_distance(player_position, monster.position)),
        active_skips,
    )


def find_follow_player_by_name(
    players: Iterable[MemoryObservedPlayer], name: str
) -> MemoryObservedPlayer | None:
    """Resolve one living same-map player by exact display name or PlayerId."""
    query = str(name).strip().casefold()
    if not query:
        return None
    matches = [
        player
        for player in players
        if player.object_id > 0
        and bool(player.player_id)
        and player.alive
        and (
            player.display_name.strip().casefold() == query
            or player.player_id.strip().casefold() == query
        )
    ]
    return matches[0] if len(matches) == 1 else None


def find_follow_party_member_by_name(
    party_members: Iterable[MemoryPartyMember], name: str
) -> MemoryPartyMember | None:
    """Resolve one non-local party member by exact display name or PlayerId."""
    query = str(name).strip().casefold()
    if not query:
        return None
    matches = [
        member
        for member in party_members
        if member.player_id
        and not member.is_local
        and (
            member.display_name.strip().casefold() == query
            or member.player_id.strip().casefold() == query
        )
    ]
    return matches[0] if len(matches) == 1 else None


def find_follow_party_member(
    party_members: Iterable[MemoryPartyMember], player_id: str
) -> MemoryPartyMember | None:
    if not player_id:
        return None
    return next(
        (
            member
            for member in party_members
            if member.player_id == player_id and not member.is_local
        ),
        None,
    )


def find_local_party_member(
    party_members: Iterable[MemoryPartyMember],
) -> MemoryPartyMember | None:
    return next((member for member in party_members if member.is_local), None)


def party_channel_number(member: MemoryPartyMember) -> int | None:
    """Convert the game's zero-based ChannelIndex to its displayed number."""
    return member.channel_index + 1 if member.channel_index >= 0 else None


def party_member_needs_channel_switch(
    target: MemoryPartyMember,
    local: MemoryPartyMember | None,
    current_map_id: int,
) -> bool:
    if target.map_id > 0 and target.map_id != current_map_id:
        return False
    if local is None or target.channel_index < 0:
        return True
    return (
        bool(target.instance_id)
        and target.instance_id != local.instance_id
    ) or target.channel_index != local.channel_index


def find_follow_player(
    players: Iterable[MemoryObservedPlayer], player_id: str
) -> MemoryObservedPlayer | None:
    """Rebind a follow identity after its transient ObjectId changes."""
    if not player_id:
        return None
    return next(
        (
            player
            for player in players
            if player.player_id == player_id
            and player.object_id > 0
            and player.alive
        ),
        None,
    )


def follow_stop_distance_world(
    local_player: MemoryPlayer,
    followed_player: MemoryObservedPlayer,
    padding_world: float,
) -> float:
    return (
        max(0.0, local_player.collider_radius)
        + max(0.0, followed_player.collider_radius)
        + max(0.0, padding_world)
    )


def update_follow_rejoin_state(
    rejoining: bool,
    *,
    distance_world: float,
    stop_distance_world: float,
    rejoin_distance_world: float,
) -> bool:
    """Apply hysteresis: enter far away, leave only at the close stop radius."""
    if rejoining:
        return distance_world > max(0.0, stop_distance_world)
    return distance_world > max(
        max(0.0, stop_distance_world), max(0.0, rejoin_distance_world)
    )


def select_follow_memory_target(
    monsters: Iterable[MemoryMonster],
    followed_player: MemoryObservedPlayer,
    previous_object_id: int | None,
    skipped_until: dict[int, float],
    *,
    now: float,
    radius_world: float,
    blocked_object_ids: set[int] | frozenset[int] = frozenset(),
) -> tuple[MemoryMonster | None, dict[int, float]]:
    """Select only enemies inside the followed player's horizontal radius."""
    active_skips = {
        object_id: expiry for object_id, expiry in skipped_until.items() if expiry > now
    }
    radius = max(0.0, float(radius_world))
    candidates = [
        monster
        for monster in monsters
        if monster.team == "enemy"
        and monster.alive
        and monster.visible
        and not monster.training_dummy
        and monster.health_ratio > 0.0
        and not monster.avoid
        and monster.object_id not in active_skips
        and monster.object_id not in blocked_object_ids
        and horizontal_distance(monster.position, followed_player.position) <= radius
    ]
    if previous_object_id is not None:
        previous = next(
            (monster for monster in candidates if monster.object_id == previous_object_id),
            None,
        )
        if previous is not None:
            return previous, active_skips
    return (
        min(
            candidates,
            key=lambda monster: (
                horizontal_distance(monster.position, followed_player.position),
                monster.object_id,
            ),
            default=None,
        ),
        active_skips,
    )


def reset_combat_watchdog(
    state: CombatWatchdogState,
    target: MemoryMonster | None,
    now: float,
) -> None:
    state.target_object_id = target.object_id if target is not None else None
    state.best_health_ratio = target.health_ratio if target is not None else 1.0
    state.last_progress_at = now
    state.was_in_range = False
    state.reengage_attempted = False
    state.reposition_started_at = None


def pause_combat_watchdog(state: CombatWatchdogState, now: float) -> None:
    state.last_progress_at = now
    state.was_in_range = False
    state.reengage_attempted = False
    state.reposition_started_at = None


def update_combat_watchdog(
    state: CombatWatchdogState,
    target: MemoryMonster,
    *,
    arrived: bool,
    now: float,
    enabled: bool,
    config: BotConfig,
) -> str:
    if state.target_object_id != target.object_id:
        reset_combat_watchdog(state, target, now)

    epsilon = max(0.000001, config.combat_health_progress_epsilon)
    if target.health_ratio <= state.best_health_ratio - epsilon:
        state.best_health_ratio = target.health_ratio
        state.last_progress_at = now
        state.reengage_attempted = False
        state.reposition_started_at = None
        state.was_in_range = arrived
        return "progress"

    if not enabled:
        state.last_progress_at = now
        state.was_in_range = arrived
        state.reengage_attempted = False
        state.reposition_started_at = None
        return "preview"

    if state.reposition_started_at is not None:
        return "reengage"

    if not arrived:
        state.last_progress_at = now
        state.was_in_range = False
        return "chase"

    if not state.was_in_range:
        state.last_progress_at = now
        state.was_in_range = True
        return "attack"

    if now - state.last_progress_at < max(0.1, config.combat_no_progress_sec):
        return "attack"

    if not state.reengage_attempted:
        state.reengage_attempted = True
        state.reposition_started_at = now
        state.was_in_range = False
        return "stalled"
    return "block"


def combat_reengage_keys(
    elapsed_ms: float,
    side: str,
    config: BotConfig,
) -> tuple[str, ...] | None:
    if elapsed_ms < max(0, config.combat_reengage_back_ms):
        return ("s",)
    elapsed_ms -= max(0, config.combat_reengage_back_ms)
    if elapsed_ms < max(0, config.combat_reengage_side_ms):
        return (side,)
    return None


def finish_combat_reengage(state: CombatWatchdogState, now: float) -> None:
    state.reposition_started_at = None
    state.last_progress_at = now
    state.was_in_range = False


def refresh_combat_blacklist(
    blocked_object_ids: set[int],
    absent_since: dict[int, float],
    present_object_ids: set[int],
    *,
    now: float,
    absence_reset_sec: float,
) -> None:
    reset_after = max(0.1, absence_reset_sec)
    for object_id in tuple(blocked_object_ids):
        if object_id in present_object_ids:
            absent_since.pop(object_id, None)
            continue
        missing_at = absent_since.setdefault(object_id, now)
        if now - missing_at >= reset_after:
            blocked_object_ids.discard(object_id)
            absent_since.pop(object_id, None)


def request_path_matches(
    path: MemoryPath,
    request_id: int,
    target_object_id: int,
    *,
    target_kind: str = "monster",
) -> bool:
    return (
        path.request_id == request_id
        and path.target_kind == target_kind
        and path.target_object_id == target_object_id
        and path.status == "complete"
        and len(path.corners) >= 1
    )


def select_path_waypoint(
    player_position: tuple[float, float, float],
    corners: Iterable[tuple[float, float, float]],
    tolerance_world: float,
) -> tuple[float, float, float] | None:
    points = tuple(corners)
    if not points:
        return None
    tolerance = max(0.05, tolerance_world)
    for point in points:
        if horizontal_distance(player_position, point) > tolerance:
            return point
    return points[-1]


def _normalize2(vector: tuple[float, float]) -> tuple[float, float] | None:
    length = math.hypot(*vector)
    if length < 0.01:
        return None
    return vector[0] / length, vector[1] / length


def movement_world_for_keys(
    keys: Iterable[str], player: MemoryPlayer | None
) -> tuple[int, int, int]:
    """Convert camera-relative WASD into the world-space Vector3Int sent by the game."""
    if player is None:
        return (0, 0, 0)
    key_set = set(keys)
    horizontal = int("d" in key_set) - int("a" in key_set)
    forward_amount = int("w" in key_set) - int("s" in key_set)
    forward = _normalize2(player.camera_forward_xz)
    right = _normalize2(player.camera_right_xz)
    if forward is None or right is None:
        return (0, 0, 0)

    world_x = forward_amount * forward[0] + horizontal * right[0]
    world_z = forward_amount * forward[1] + horizontal * right[1]

    def discrete(value: float) -> int:
        if value > 0.25:
            return 1
        if value < -0.25:
            return -1
        return 0

    return (discrete(world_x), 0, discrete(world_z))


def movement_keys_for_world_waypoint(
    player: MemoryPlayer,
    waypoint: tuple[float, float, float],
    config: BotConfig,
) -> tuple[str, ...]:
    desired = _normalize2(
        (waypoint[0] - player.position[0], waypoint[2] - player.position[2])
    )
    forward = _normalize2(player.camera_forward_xz)
    right = _normalize2(player.camera_right_xz)
    if desired is None or forward is None or right is None:
        return ()
    forward_amount = desired[0] * forward[0] + desired[1] * forward[1]
    right_amount = desired[0] * right[0] + desired[1] * right[1]
    threshold = max(0.0, min(0.95, config.axis_deadzone_ratio)) * max(
        abs(forward_amount), abs(right_amount), 0.01
    )
    keys: list[str] = []
    if forward_amount > threshold:
        keys.append("w")
    elif forward_amount < -threshold:
        keys.append("s")
    if right_amount > threshold:
        keys.append("d")
    elif right_amount < -threshold:
        keys.append("a")
    return tuple(keys)


def arrival_radius(player: MemoryPlayer, target: MemoryMonster, config: BotConfig) -> float:
    return max(
        0.25,
        player.collider_radius
        + target.collider_radius
        + max(0.0, config.arrival_padding_world),
    )


def map_exit_avoidance_radius(
    player: MemoryPlayer,
    map_exit: MemoryMapExit,
    padding_world: float,
) -> float:
    """Return the F8 keep-out radius around one automatic map exit."""
    return max(
        0.25,
        player.collider_radius
        + map_exit.interaction_range
        + max(0.0, padding_world),
    )


def point_inside_map_exit_keepout(
    player: MemoryPlayer,
    point: tuple[float, float, float],
    map_exits: Iterable[MemoryMapExit],
    padding_world: float,
) -> MemoryMapExit | None:
    for map_exit in map_exits:
        if horizontal_distance(point, map_exit.position) < map_exit_avoidance_radius(
            player, map_exit, padding_world
        ):
            return map_exit
    return None


def _horizontal_segment_distance(
    point: tuple[float, float, float],
    start: tuple[float, float, float],
    end: tuple[float, float, float],
) -> float:
    segment_x = end[0] - start[0]
    segment_z = end[2] - start[2]
    length_squared = segment_x * segment_x + segment_z * segment_z
    if length_squared <= 1e-9:
        return horizontal_distance(point, start)
    projected = (
        (point[0] - start[0]) * segment_x
        + (point[2] - start[2]) * segment_z
    ) / length_squared
    projected = max(0.0, min(1.0, projected))
    closest = (
        start[0] + segment_x * projected,
        start[1],
        start[2] + segment_z * projected,
    )
    return horizontal_distance(point, closest)


def path_enters_map_exit_keepout(
    player: MemoryPlayer,
    corners: Iterable[tuple[float, float, float]],
    map_exits: Iterable[MemoryMapExit],
    padding_world: float,
) -> MemoryMapExit | None:
    """Find an exit whose keep-out circle would be entered by an F8 path.

    When the player is already inside a circle, outward-only path segments are
    allowed until the path leaves it.  This prevents the guard from trapping a
    character who starts near an exit while still rejecting paths that approach
    or re-enter the automatic transition area.
    """
    points = [player.position]
    for corner in corners:
        if horizontal_distance(points[-1], corner) > 0.01:
            points.append(corner)
    if len(points) < 2:
        return None

    for map_exit in map_exits:
        radius = map_exit_avoidance_radius(player, map_exit, padding_world)
        inside = horizontal_distance(player.position, map_exit.position) < radius
        for start, end in zip(points, points[1:]):
            start_distance = horizontal_distance(start, map_exit.position)
            end_distance = horizontal_distance(end, map_exit.position)
            if inside:
                if end_distance <= start_distance + 0.01:
                    return map_exit
                if end_distance >= radius:
                    inside = False
                continue
            if _horizontal_segment_distance(map_exit.position, start, end) < radius:
                return map_exit
    return None


def unstuck_keys(elapsed_ms: float, side: str, config: BotConfig) -> tuple[str, ...] | None:
    opposite = "d" if side == "a" else "a"
    if elapsed_ms < config.unstuck_back_ms:
        return ("s",)
    elapsed_ms -= config.unstuck_back_ms
    if elapsed_ms < config.unstuck_back_diagonal_ms:
        return ("s", side)
    elapsed_ms -= config.unstuck_back_diagonal_ms
    if elapsed_ms < config.unstuck_side_ms:
        return (side,)
    elapsed_ms -= config.unstuck_side_ms
    if elapsed_ms < config.unstuck_diagonal_ms:
        return ("w", side)
    elapsed_ms -= config.unstuck_diagonal_ms
    if elapsed_ms < config.unstuck_return_ms:
        return ("w", opposite)
    elapsed_ms -= config.unstuck_return_ms
    if elapsed_ms < config.unstuck_forward_ms:
        return ("w",)
    return None
