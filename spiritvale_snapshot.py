"""Validate and decode probe snapshots without reading files or sending input."""

from __future__ import annotations

from dataclasses import replace
import math
from spiritvale_models import (
    MemoryConsumableUse,
    MemoryLoot,
    MemoryMapExit,
    MemoryMonster,
    MemoryObservedPlayer,
    MemoryPartyMember,
    MemoryPath,
    MemoryPlayer,
    MemorySnapshot,
    SnapshotUnavailable,
)
from spiritvale_navigation import (
    detect_boss_object_id,
    parse_monster_level,
)


MEMORY_SCHEMA_VERSION = 1


def _finite_float(value: object, field: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise SnapshotUnavailable(f"{field} is not finite")
    return number


def _vector3(value: object, field: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise SnapshotUnavailable(f"{field} must be a three-number array")
    return tuple(_finite_float(item, field) for item in value)  # type: ignore[return-value]


def _vector2(value: object, field: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise SnapshotUnavailable(f"{field} must be a two-number array")
    result = tuple(_finite_float(item, field) for item in value)
    if math.hypot(*result) < 0.01:
        raise SnapshotUnavailable(f"{field} has zero length")
    return result  # type: ignore[return-value]


def parse_memory_snapshot(
    raw: object,
    *,
    now_ms: int,
    max_age_ms: int,
    avoid_boss: bool = False,
) -> MemorySnapshot:
    if not isinstance(raw, dict):
        raise SnapshotUnavailable("memory state is not an object")
    if raw.get("schema_version") != MEMORY_SCHEMA_VERSION:
        raise SnapshotUnavailable("memory state schema mismatch")
    status = str(raw.get("status", "missing"))
    if status != "ok":
        detail = raw.get("error")
        relogin = raw.get("relogin")
        if isinstance(relogin, dict):
            phase = str(relogin.get("state", status)).strip() or status
            attempt = int(relogin.get("attempt", 0))
            maximum = int(relogin.get("max_attempts", 0))
            message = str(relogin.get("message", "")).strip()
            attempt_text = f" {attempt}/{maximum}" if maximum > 0 else ""
            detail = f"{phase}{attempt_text}" + (f": {message}" if message else "")
        raise SnapshotUnavailable(f"probe status={status}" + (f": {detail}" if detail else ""))

    timestamp_ms = int(raw["timestamp_ms"])
    age_ms = now_ms - timestamp_ms
    if age_ms < -max_age_ms or age_ms > max_age_ms:
        raise SnapshotUnavailable(f"memory state is stale ({age_ms} ms)")

    player_raw = raw.get("player")
    if not isinstance(player_raw, dict):
        raise SnapshotUnavailable("player is unavailable")
    player_alive = player_raw.get("alive")
    if type(player_alive) is not bool:
        raise SnapshotUnavailable("player.alive is unavailable")
    summon_mount_state_available = (
        player_raw.get("summon_mount_state_source") == "mount_controller"
    )
    summon_displays_raw = player_raw.get("summon_displays")
    summon_displays_available = bool(
        isinstance(summon_displays_raw, dict)
        and summon_displays_raw.get("available") is True
    )
    summon_displays_error = (
        str(summon_displays_raw.get("error", "") or "")
        if isinstance(summon_displays_raw, dict)
        else "summon_displays is unavailable"
    )
    summon_display_skill_ids: list[str] = []
    if isinstance(summon_displays_raw, dict):
        summon_items = summon_displays_raw.get("items", [])
        if isinstance(summon_items, list):
            for item in summon_items:
                if not isinstance(item, dict):
                    continue
                skill_id = str(item.get("skill_id", "") or "").strip()
                if skill_id:
                    summon_display_skill_ids.append(skill_id)

    status_component_raw = player_raw.get("status_component")
    active_statuses_available = bool(
        isinstance(status_component_raw, dict)
        and status_component_raw.get("active_statuses_available") is True
    )
    active_statuses_error = (
        str(status_component_raw.get("active_statuses_error", "") or "")
        if isinstance(status_component_raw, dict)
        else "status_component is unavailable"
    )
    active_status_ids: list[str] = []
    if isinstance(status_component_raw, dict):
        active_status_values = status_component_raw.get("active_status_ids", [])
        if isinstance(active_status_values, list):
            active_status_ids = [
                str(value).strip()
                for value in active_status_values
                if str(value).strip()
            ]
    guardian_bond = player_raw.get("guardian_bond")
    if not isinstance(guardian_bond, dict):
        guardian_bond = {}
    guardian_candidate = guardian_bond.get("candidate_unit_id", 0)
    if type(guardian_candidate) is not int or guardian_candidate < 0:
        guardian_candidate = 0
    wallet_coins_available = player_raw.get("wallet_coins_available") is True
    wallet_coins_error = str(player_raw.get("wallet_coins_error", "") or "")
    wallet_coins = 0
    if wallet_coins_available:
        wallet_value = player_raw.get("wallet_coins")
        if type(wallet_value) is int and wallet_value >= 0:
            wallet_coins = wallet_value
        else:
            wallet_coins_available = False
            wallet_coins_error = "player.wallet_coins is not a non-negative integer"
    elif not wallet_coins_error:
        wallet_coins_error = "wallet coins are unavailable"
    player = MemoryPlayer(
        position=_vector3(player_raw.get("position"), "player.position"),
        camera_forward_xz=_vector2(
            player_raw.get("camera_forward_xz"), "player.camera_forward_xz"
        ),
        camera_right_xz=_vector2(
            player_raw.get("camera_right_xz"), "player.camera_right_xz"
        ),
        collider_radius=max(
            0.0,
            _finite_float(player_raw.get("collider_radius", 0.0), "player radius"),
        ),
        is_mounted_summon=bool(player_raw.get("is_mounted_summon", False)),
        is_mountable_summon=bool(player_raw.get("is_mountable_summon", False)),
        active_summon_count=max(
            0, int(player_raw.get("active_summon_count", 0) or 0)
        ),
        has_primary_summon=bool(player_raw.get("has_primary_summon", False)),
        summon_id=str(player_raw.get("summon_id", "") or ""),
        mounted_summon_state_available=summon_mount_state_available,
        summon_mount_action_available=summon_mount_state_available,
        summon_displays_available=summon_displays_available,
        summon_displays_error=summon_displays_error,
        summon_display_skill_ids=tuple(summon_display_skill_ids),
        active_statuses_available=active_statuses_available,
        active_statuses_error=active_statuses_error,
        active_status_ids=tuple(active_status_ids),
        guardian_bond_available=guardian_bond.get("available") is True,
        guardian_bond_error=str(guardian_bond.get("error", "") or ""),
        guardian_bond_active=guardian_bond.get("has_owned_bond") is True,
        guardian_bond_candidate_id=guardian_candidate,
        guardian_bond_cast_error=str(guardian_bond.get("cast_error", "") or ""),
        wallet_coins=wallet_coins,
        wallet_coins_available=wallet_coins_available,
        wallet_coins_error=wallet_coins_error,
        alive=player_alive,
    )

    players: list[MemoryObservedPlayer] = []
    players_raw = raw.get("players", [])
    if not isinstance(players_raw, list):
        raise SnapshotUnavailable("players is not an array")
    for item in players_raw:
        if not isinstance(item, dict):
            continue
        try:
            observed_player = MemoryObservedPlayer(
                object_id=int(item.get("object_id", 0)),
                player_id=str(item.get("player_id", "")),
                display_name=str(item.get("display_name", "")),
                position=_vector3(item.get("position"), "observed player.position"),
                collider_radius=max(
                    0.0,
                    _finite_float(
                        item.get("collider_radius", 0.0),
                        "observed player radius",
                    ),
                ),
                alive=bool(item.get("alive", False)),
                visible=bool(item.get("visible", False)),
                party_member=bool(item.get("party_member", False)),
                selected=bool(item.get("selected", False)),
            )
        except (SnapshotUnavailable, TypeError, ValueError):
            continue
        if observed_player.object_id > 0:
            players.append(observed_player)

    party_members: list[MemoryPartyMember] = []
    party_members_raw = raw.get("party_members", [])
    if not isinstance(party_members_raw, list):
        raise SnapshotUnavailable("party_members is not an array")
    for item in party_members_raw:
        if not isinstance(item, dict):
            continue
        try:
            party_member = MemoryPartyMember(
                display_name=str(item.get("display_name", "")),
                player_id=str(item.get("player_id", "")),
                object_id=int(item.get("object_id", 0)),
                map_id=int(item.get("map_id", 0)),
                instance_id=str(item.get("instance_id", "")),
                channel_index=int(item.get("channel_index", -1)),
                is_local=bool(item.get("is_local", False)),
            )
        except (TypeError, ValueError):
            continue
        if party_member.player_id:
            party_members.append(party_member)

    monsters: list[MemoryMonster] = []
    monsters_raw = raw.get("monsters", [])
    if not isinstance(monsters_raw, list):
        raise SnapshotUnavailable("monsters is not an array")
    for item in monsters_raw:
        if not isinstance(item, dict):
            continue
        viewport_position: tuple[float, float, float] | None = None
        if "viewport_position" in item:
            try:
                viewport_position = _vector3(
                    item.get("viewport_position"), "monster.viewport_position"
                )
            except (SnapshotUnavailable, TypeError, ValueError):
                viewport_position = None
        display_name = str(item.get("display_name", ""))
        monster = MemoryMonster(
            object_id=int(item.get("object_id", 0)),
            config_id=str(item.get("config_id", "")),
            display_name=display_name,
            rank=str(item.get("rank", "")),
            level=parse_monster_level(display_name),
            position=_vector3(item.get("position"), "monster.position"),
            health_ratio=_finite_float(item.get("health_ratio", 0.0), "monster health"),
            collider_radius=max(
                0.0,
                _finite_float(item.get("collider_radius", 0.0), "monster radius"),
            ),
            team=str(item.get("team", "enemy")),
            alive=bool(item.get("alive", True)),
            visible=bool(item.get("visible", True)),
            training_dummy=bool(item.get("training_dummy", False)),
            viewport_position=viewport_position,
            viewport_visible=(
                viewport_position is not None
                and bool(item.get("viewport_visible", False))
            ),
        )
        if (
            monster.object_id > 0
            and monster.team == "enemy"
            and monster.alive
            and monster.visible
            and not monster.training_dummy
            and monster.health_ratio > 0.0
        ):
            monsters.append(monster)

    if avoid_boss:
        boss_object_id = detect_boss_object_id(monsters)
        if boss_object_id is not None:
            monsters = [
                replace(monster, avoid=True)
                if monster.object_id == boss_object_id
                else monster
                for monster in monsters
            ]

    loots: list[MemoryLoot] = []
    loots_raw = raw.get("loots", [])
    if not isinstance(loots_raw, list):
        raise SnapshotUnavailable("loots is not an array")
    for item in loots_raw:
        if not isinstance(item, dict):
            continue
        try:
            loot = MemoryLoot(
                object_id=int(item.get("object_id", 0)),
                item_id=str(item.get("item_id", "")),
                display_name=str(item.get("display_name", "")),
                sprite_id=str(item.get("sprite_id", "")),
                rarity=str(item.get("rarity", "")),
                rarity_value=int(item.get("rarity_value", 0)),
                loot_type=str(item.get("loot_type", "")),
                position=_vector3(item.get("position"), "loot.position"),
                viewport_position=_vector3(
                    item.get("viewport_position"), "loot.viewport_position"
                ),
                viewport_visible=bool(item.get("viewport_visible", False)),
                locked=bool(item.get("locked", False)),
                owner_player_id=str(item.get("owner_player_id", "")),
                owner_party_id=int(item.get("owner_party_id", 0)),
                owned_by_local_player=bool(
                    item.get("owned_by_local_player", False)
                ),
                interaction_range=max(
                    0.0,
                    _finite_float(
                        item.get("interaction_range", 0.0),
                        "loot interaction range",
                    ),
                ),
            )
        except (SnapshotUnavailable, TypeError, ValueError):
            continue
        if loot.object_id > 0:
            loots.append(loot)

    map_exits: list[MemoryMapExit] = []
    map_exits_raw = raw.get("map_exits", [])
    if not isinstance(map_exits_raw, list):
        raise SnapshotUnavailable("map_exits is not an array")
    for item in map_exits_raw:
        if not isinstance(item, dict):
            continue
        try:
            map_exit = MemoryMapExit(
                position=_vector3(item.get("position"), "map exit.position"),
                interaction_range=max(
                    0.0,
                    _finite_float(
                        item.get("interaction_range", 0.0),
                        "map exit interaction range",
                    ),
                ),
            )
        except (SnapshotUnavailable, TypeError, ValueError):
            continue
        map_exits.append(map_exit)

    path_raw = raw.get("path", {})
    if not isinstance(path_raw, dict):
        path_raw = {}
    corners_raw = path_raw.get("corners", [])
    corners = (
        tuple(_vector3(value, "path.corner") for value in corners_raw)
        if isinstance(corners_raw, list)
        else ()
    )
    path = MemoryPath(
        request_id=int(path_raw.get("request_id", 0)),
        target_object_id=int(path_raw.get("target_object_id", 0)),
        status=str(path_raw.get("status", "missing")),
        corners=corners,
        target_kind=str(path_raw.get("target_kind", "monster")).casefold(),
    )
    consumable_raw = raw.get("consumable_use", {})
    if not isinstance(consumable_raw, dict):
        consumable_raw = {}
    consumable_use = MemoryConsumableUse(
        request_id=max(0, int(consumable_raw.get("request_id", 0) or 0)),
        status=str(consumable_raw.get("status", "idle") or "idle").casefold(),
        item_id=str(consumable_raw.get("item_id", "") or ""),
        display_name=str(consumable_raw.get("display_name", "") or ""),
        remaining_count=int(consumable_raw.get("remaining_count", -1) or 0),
        error=str(consumable_raw.get("error", "") or ""),
    )
    return MemorySnapshot(
        timestamp_ms=timestamp_ms,
        map_id=int(raw.get("map_id", 0)),
        instance_id=int(raw.get("instance_id", 0)),
        channel_index=int(raw.get("channel_index", -1)),
        channel_count=int(raw.get("channel_count", 0)),
        player=player,
        players=tuple(players),
        party_members=tuple(party_members),
        party_state_available="party_members" in raw,
        monsters=tuple(monsters),
        loots=tuple(loots),
        map_exits=tuple(map_exits),
        map_exit_state_available="map_exits" in raw,
        path=path,
        player_scan=(
            dict(raw["player_scan"])
            if isinstance(raw.get("player_scan"), dict)
            else None
        ),
        monster_scan=(
            dict(raw["monster_scan"])
            if isinstance(raw.get("monster_scan"), dict)
            else None
        ),
        loot_scan=(
            dict(raw["loot_scan"])
            if isinstance(raw.get("loot_scan"), dict)
            else None
        ),
        consumable_use=consumable_use,
    )


def no_enemy_status(snapshot: MemorySnapshot) -> str:
    scan = snapshot.monster_scan
    if not scan:
        return "NO LIVING ENEMY"
    return (
        "NO LIVING ENEMY - "
        f"source={scan.get('source', '?')} "
        f"Monsters/Units={scan.get('monsters_count', '?')}/"
        f"{scan.get('units_count', '?')} "
        f"scene={scan.get('scene_count', '?')} "
        f"scene-status={scan.get('scene_status', '?')} "
        f"source/cast={scan.get('source_count', '?')}/"
        f"{scan.get('castable', '?')} "
        f"no-network={scan.get('rejected_no_network_object', '?')} "
        f"other-map={scan.get('rejected_other_map', '?')} "
        f"unknown/nav-ok/nav-bad={scan.get('unknown_map_candidates', '?')}/"
        f"{scan.get('accepted_by_navmesh', '?')}/"
        f"{scan.get('rejected_no_navmesh', '?')} "
        f"inactive/hidden/dead={scan.get('rejected_inactive', '?')}/"
        f"{scan.get('rejected_not_displayed', '?')}/"
        f"{scan.get('rejected_dead', '?')} "
        f"no-data/not-enemy={scan.get('rejected_no_data', '?')}/"
        f"{scan.get('rejected_not_enemy', '?')} "
        f"teams={scan.get('team_values', '?')} "
        f"network-maps={scan.get('network_maps', '?')} "
        f"nav-error={scan.get('navmesh_filter_error', '')}"
    )


def snapshot_error_log_key(error: SnapshotUnavailable) -> str:
    """Collapse changing age/details so repeated safe stops are rate limited."""
    return "snapshot:" + str(error).split(" (", 1)[0]
