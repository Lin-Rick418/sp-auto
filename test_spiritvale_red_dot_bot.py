from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import spiritvale_red_dot_bot as bot
from spiritvale_red_dot_bot import (
    BotConfig,
    CombatWatchdogState,
    LootChaseState,
    MemoryLoot,
    MemoryMapExit,
    MemoryMonster,
    MemoryObservedPlayer,
    MemoryPartyMember,
    MemoryPath,
    MemoryPlayer,
    MemorySnapshot,
    NavigationEarningsState,
    SnapshotUnavailable,
    SummonerCheckState,
    SummonMountKeyState,
    advance_summoner_checks,
    advance_summon_mount_hotkeys,
    arrival_radius,
    combat_reengage_keys,
    draw_memory_radar,
    finish_combat_reengage,
    finish_navigation_earnings,
    format_navigation_earnings_report,
    find_follow_player,
    find_follow_player_by_name,
    find_follow_party_member,
    find_follow_party_member_by_name,
    find_local_party_member,
    follow_stop_distance_world,
    key_transitions,
    loot_is_within_pickup_range,
    loot_chase_failure_reason,
    loot_pickup_radius,
    load_mode_config,
    missing_summoner_checks,
    movement_keys_for_world_waypoint,
    movement_world_for_keys,
    map_exit_avoidance_radius,
    move_mouse_to_monster,
    no_enemy_status,
    observe_navigation_wallet,
    pause_navigation_earnings,
    pause_combat_watchdog,
    path_enters_map_exit_keepout,
    party_channel_number,
    party_member_needs_channel_switch,
    parse_memory_snapshot,
    parse_monster_level,
    detect_boss_object_id,
    monster_matches_boss,
    normalize_boss_name,
    post_left_click_to_monster,
    point_inside_map_exit_keepout,
    load_memory_snapshot,
    request_path_matches,
    refresh_combat_blacklist,
    reset_combat_watchdog,
    reset_loot_chase,
    resume_navigation_earnings,
    select_memory_loot,
    select_memory_target,
    select_boss_farm_target,
    select_boss_legendary_loot,
    select_follow_memory_target,
    select_path_waypoint,
    snapshot_error_log_key,
    start_navigation_earnings,
    summon_mount_blocks_navigation,
    summon_mount_wait_status,
    summoner_checks_enabled,
    should_advance_train_target,
    track_memory_loot_candidate,
    post_key_tap,
    unstuck_keys,
    update_combat_watchdog,
    update_follow_rejoin_state,
    viewport_to_client_point,
    wait_for_wallet_snapshot,
    write_navigation_request,
)


NOW_MS = 1_800_000_000_000


def monster(
    object_id: int,
    x: float,
    z: float,
    *,
    health: float = 1.0,
    team: str = "enemy",
    alive: bool = True,
    visible: bool = True,
    training_dummy: bool = False,
    viewport: tuple[float, float, float] | None = None,
    viewport_visible: bool = False,
    level: int = 0,
    avoid: bool = False,
) -> MemoryMonster:
    return MemoryMonster(
        object_id=object_id,
        config_id=f"monster-{object_id}",
        display_name=f"Monster {object_id}",
        rank="Normal",
        position=(x, 0.0, z),
        health_ratio=health,
        collider_radius=0.5,
        team=team,
        alive=alive,
        visible=visible,
        training_dummy=training_dummy,
        viewport_position=viewport,
        viewport_visible=viewport_visible,
        level=level,
        avoid=avoid,
    )


def observed_player(
    object_id: int,
    player_id: str,
    x: float,
    z: float,
    *,
    selected: bool = False,
    alive: bool = True,
    visible: bool = True,
) -> MemoryObservedPlayer:
    return MemoryObservedPlayer(
        object_id=object_id,
        player_id=player_id,
        display_name=f"Player {player_id}",
        position=(x, 0.0, z),
        collider_radius=0.5,
        alive=alive,
        visible=visible,
        party_member=False,
        selected=selected,
    )


def party_member(
    player_id: str,
    *,
    channel_index: int,
    map_id: int = 1,
    instance_id: str = "server-a",
    is_local: bool = False,
    object_id: int = 0,
) -> MemoryPartyMember:
    return MemoryPartyMember(
        display_name=f"Player {player_id}",
        player_id=player_id,
        object_id=object_id,
        map_id=map_id,
        instance_id=instance_id,
        channel_index=channel_index,
        is_local=is_local,
    )


def same_channel_party_members(
    target_player_id: str = "follow-id",
) -> tuple[MemoryPartyMember, MemoryPartyMember]:
    return (
        party_member("local", channel_index=0, is_local=True),
        party_member(target_player_id, channel_index=0),
    )


def loot(
    object_id: int,
    x: float,
    z: float,
    *,
    rarity: str = "Unique",
    rarity_value: int = 2,
    viewport: tuple[float, float, float] = (0.5, 0.5, 10.0),
    visible: bool = True,
    locked: bool = False,
    owned: bool = True,
    interaction_range: float = 3.0,
    loot_type: str = "Material",
) -> MemoryLoot:
    return MemoryLoot(
        object_id=object_id,
        item_id=f"item-{object_id}",
        display_name=f"Loot {object_id}",
        sprite_id=f"sprite-{object_id}",
        rarity=rarity,
        rarity_value=rarity_value,
        loot_type=loot_type,
        position=(x, 0.0, z),
        viewport_position=viewport,
        viewport_visible=visible,
        locked=locked,
        owner_player_id="local-player" if owned else "other-player",
        owner_party_id=0,
        owned_by_local_player=owned,
        interaction_range=interaction_range,
    )


def valid_raw_state() -> dict[str, object]:
    return {
        "schema_version": 1,
        "timestamp_ms": NOW_MS - 100,
        "status": "ok",
        "map_id": 3,
        "instance_id": 9,
        "player": {
            "position": [10.0, 2.0, 20.0],
            "camera_forward_xz": [0.0, 1.0],
            "camera_right_xz": [1.0, 0.0],
            "collider_radius": 0.45,
            "alive": True,
            "wallet_coins_available": True,
            "wallet_coins": 123_456,
            "wallet_coins_error": "",
            "is_mounted_summon": True,
            "summon_mount_state_source": "mount_controller",
        },
        "monsters": [
            {
                "object_id": 101,
                "config_id": "slime",
                "display_name": "Slime",
                "rank": "Normal",
                "position": [13.0, 2.0, 24.0],
                "viewport_position": [0.4, 0.6, 12.0],
                "viewport_visible": True,
                "health_ratio": 0.8,
                "collider_radius": 0.6,
                "team": "enemy",
                "alive": True,
                "visible": True,
                "training_dummy": False,
            }
        ],
        "loots": [
            {
                "object_id": 501,
                "item_id": "sword-unique",
                "display_name": "Ancient Sword",
                "sprite_id": "sword_01",
                "rarity": "Unique",
                "rarity_value": 2,
                "loot_type": "Equip",
                "position": [14.0, 2.0, 22.0],
                "viewport_position": [0.25, 0.75, 12.0],
                "viewport_visible": True,
                "locked": False,
                "owner_player_id": "local-player",
                "owner_party_id": 0,
                "owned_by_local_player": True,
                "interaction_range": 3.0,
            }
        ],
        "map_exits": [
            {
                "position": [30.0, 2.0, 40.0],
                "interaction_range": 1.25,
            }
        ],
        "path": {
            "request_id": 7,
            "target_kind": "monster",
            "target_object_id": 101,
            "status": "complete",
            "corners": [[10.0, 2.0, 20.0], [12.0, 2.0, 21.0], [13.0, 2.0, 24.0]],
        },
    }


class MemoryProtocolTests(unittest.TestCase):
    def test_parses_fresh_versioned_snapshot(self) -> None:
        snapshot = parse_memory_snapshot(
            valid_raw_state(), now_ms=NOW_MS, max_age_ms=750
        )
        self.assertEqual((snapshot.map_id, snapshot.instance_id), (3, 9))
        self.assertEqual(snapshot.player.position, (10.0, 2.0, 20.0))
        self.assertTrue(snapshot.player.alive)
        self.assertTrue(snapshot.player.wallet_coins_available)
        self.assertEqual(snapshot.player.wallet_coins, 123_456)
        self.assertTrue(snapshot.player.is_mounted_summon)
        self.assertTrue(snapshot.player.mounted_summon_state_available)
        self.assertTrue(snapshot.player.summon_mount_action_available)
        self.assertEqual(snapshot.monsters[0].object_id, 101)
        self.assertEqual(snapshot.monsters[0].viewport_position, (0.4, 0.6, 12.0))
        self.assertTrue(snapshot.monsters[0].viewport_visible)
        self.assertEqual(snapshot.loots[0].display_name, "Ancient Sword")
        self.assertEqual(snapshot.loots[0].rarity_value, 2)
        self.assertEqual(snapshot.map_exits[0].position, (30.0, 2.0, 40.0))
        self.assertEqual(snapshot.map_exits[0].interaction_range, 1.25)
        self.assertEqual(snapshot.path.status, "complete")
        self.assertEqual(snapshot.path.target_kind, "monster")
        self.assertEqual(snapshot.consumable_use.status, "idle")

    def test_parses_current_summons_and_active_status_ids(self) -> None:
        raw = valid_raw_state()
        raw["player"]["summon_displays"] = {
            "available": True,
            "error": "",
            "items": [
                {"skill_id": "SummonSkeleton", "id": "Skeleton", "level": 5},
                {"skill_id": "SummonSkeleton", "id": "Skeleton", "level": 5},
                {
                    "skill_id": "SummonSkeletonMage",
                    "id": "Skeleton Mage",
                    "level": 4,
                },
            ],
        }
        raw["player"]["status_component"] = {
            "available": True,
            "error": "",
            "active_statuses_available": True,
            "active_statuses_error": "",
            "active_status_ids": ["Invoker"],
            "buffs": ["Conjurer"],
            "debuffs": [],
            "effects": [],
        }
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertTrue(snapshot.player.summon_displays_available)
        self.assertEqual(
            snapshot.player.summon_display_skill_ids,
            ("SummonSkeleton", "SummonSkeleton", "SummonSkeletonMage"),
        )
        self.assertTrue(snapshot.player.active_statuses_available)
        self.assertEqual(snapshot.player.active_status_ids, ("Invoker",))

    def test_missing_or_invalid_wallet_fields_do_not_reject_snapshot(self) -> None:
        old_raw = valid_raw_state()
        del old_raw["player"]["wallet_coins_available"]  # type: ignore[index]
        del old_raw["player"]["wallet_coins"]  # type: ignore[index]
        del old_raw["player"]["wallet_coins_error"]  # type: ignore[index]
        old_snapshot = parse_memory_snapshot(
            old_raw, now_ms=NOW_MS, max_age_ms=750
        )
        self.assertFalse(old_snapshot.player.wallet_coins_available)

        invalid_raw = valid_raw_state()
        invalid_raw["player"]["wallet_coins"] = "123"  # type: ignore[index]
        invalid_snapshot = parse_memory_snapshot(
            invalid_raw, now_ms=NOW_MS, max_age_ms=750
        )
        self.assertFalse(invalid_snapshot.player.wallet_coins_available)
        self.assertIn("non-negative integer", invalid_snapshot.player.wallet_coins_error)

    def test_skill_key_request_is_limited_to_numpad(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            write_navigation_request(
                path,
                1,
                0,
                skill_key_request_id=77,
                skill_key="NumPad4",
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["skill_key_request_id"], 77)
            self.assertEqual(payload["skill_key"], "numpad4")
            with self.assertRaisesRegex(ValueError, "numpad0 through numpad9"):
                write_navigation_request(path, 2, 0, skill_key="4")

    def test_parses_consumable_use_result(self) -> None:
        raw = valid_raw_state()
        raw["consumable_use"] = {
            "request_id": 42,
            "status": "accepted",
            "item_id": "soldier-termite",
            "display_name": "Soldier Termite",
            "remaining_count": 7,
            "error": "",
        }
        result = parse_memory_snapshot(
            raw, now_ms=NOW_MS, max_age_ms=750
        ).consumable_use
        self.assertEqual(result.request_id, 42)
        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.item_id, "soldier-termite")
        self.assertEqual(result.remaining_count, 7)

    def test_old_summon_mount_probe_state_is_not_actionable(self) -> None:
        raw = valid_raw_state()
        del raw["player"]["summon_mount_state_source"]
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertTrue(snapshot.player.is_mounted_summon)
        self.assertFalse(snapshot.player.mounted_summon_state_available)
        self.assertFalse(snapshot.player.summon_mount_action_available)

    def test_missing_local_player_alive_state_forces_safe_stop(self) -> None:
        raw = valid_raw_state()
        del raw["player"]["alive"]
        with self.assertRaisesRegex(SnapshotUnavailable, "player.alive"):
            parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)

    def test_parses_dead_local_player_without_rejecting_snapshot(self) -> None:
        raw = valid_raw_state()
        raw["player"]["alive"] = False
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertFalse(snapshot.player.alive)

    def test_parses_remote_player_identity_selection_and_state(self) -> None:
        raw = valid_raw_state()
        raw["players"] = [
            {
                "object_id": 701,
                "player_id": "account-character-1",
                "display_name": "同行者",
                "position": [18.0, 2.0, 25.0],
                "collider_radius": 0.55,
                "alive": True,
                "visible": True,
                "party_member": True,
                "selected": True,
            }
        ]
        raw["player_scan"] = {"source": "map", "accepted": 1}
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertEqual(snapshot.players[0].object_id, 701)
        self.assertEqual(snapshot.players[0].player_id, "account-character-1")
        self.assertEqual(snapshot.players[0].display_name, "同行者")
        self.assertTrue(snapshot.players[0].selected)
        self.assertTrue(snapshot.players[0].party_member)
        self.assertEqual(snapshot.player_scan["accepted"], 1)  # type: ignore[index]

    def test_legacy_path_without_target_kind_defaults_to_monster(self) -> None:
        raw = valid_raw_state()
        del raw["path"]["target_kind"]  # type: ignore[index]
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertEqual(snapshot.path.target_kind, "monster")

    def test_legacy_probe_without_map_exits_is_marked_unavailable(self) -> None:
        raw = valid_raw_state()
        del raw["map_exits"]
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertFalse(snapshot.map_exit_state_available)
        self.assertEqual(snapshot.map_exits, ())

    def test_legacy_monster_without_viewport_remains_navigable(self) -> None:
        raw = valid_raw_state()
        monster_raw = raw["monsters"][0]  # type: ignore[index]
        del monster_raw["viewport_position"]  # type: ignore[index]
        del monster_raw["viewport_visible"]  # type: ignore[index]
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertEqual(snapshot.monsters[0].object_id, 101)
        self.assertIsNone(snapshot.monsters[0].viewport_position)
        self.assertFalse(snapshot.monsters[0].viewport_visible)

    def test_malformed_optional_monster_viewport_does_not_drop_monster(self) -> None:
        raw = valid_raw_state()
        raw["monsters"][0]["viewport_position"] = [0.5]  # type: ignore[index]
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertEqual(snapshot.monsters[0].object_id, 101)
        self.assertIsNone(snapshot.monsters[0].viewport_position)
        self.assertFalse(snapshot.monsters[0].viewport_visible)

    def test_mode_config_accepts_normal_train_or_boss_farm(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mode.json"
            for value in (1, 2):
                path.write_text(json.dumps({"mode": value}), encoding="utf-8")
                self.assertEqual(load_mode_config(path).mode, value)
            path.write_text(
                json.dumps(
                    {
                        "mode": 3,
                        "boss_name": "Scorpion King",
                        "boss_summon_item_name": "Soldier Termite",
                    }
                ),
                encoding="utf-8",
            )
            boss = load_mode_config(path)
            self.assertEqual(boss.mode, 3)
            self.assertEqual(boss.boss_name, "Scorpion King")
            self.assertEqual(boss.boss_summon_item_name, "Soldier Termite")
            self.assertEqual(boss.boss_spawn_timeout_sec, 10.0)
            self.assertEqual(boss.boss_death_confirm_sec, 1.0)
            self.assertEqual(boss.boss_loot_settle_sec, 3.0)
            path.write_text('{"mode": 4}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "boss farm"):
                load_mode_config(path)

    def test_mode_three_requires_names_and_valid_timings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mode.json"
            path.write_text('{"mode": 3}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "boss_name"):
                load_mode_config(path)
            base = {
                "mode": 3,
                "boss_name": "Scorpion King",
                "boss_summon_item_name": "Soldier Termite",
            }
            for field, value in (
                ("boss_spawn_timeout_sec", -1),
                ("boss_death_confirm_sec", "nan"),
                ("boss_loot_settle_sec", "bad"),
            ):
                path.write_text(
                    json.dumps({**base, field: value}), encoding="utf-8"
                )
                with self.assertRaisesRegex(ValueError, field):
                    load_mode_config(path)

    def test_mode_config_validates_optional_mouse_lock_boolean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mode.json"
            path.write_text('{"mode": 1}', encoding="utf-8")
            self.assertFalse(load_mode_config(path).lock_mouse_to_monster)
            for value in (False, True):
                path.write_text(
                    json.dumps(
                        {"mode": 1, "lock_mouse_to_monster": value}
                    ),
                    encoding="utf-8",
                )
                self.assertIs(
                    load_mode_config(path).lock_mouse_to_monster,
                    value,
                )
            path.write_text(
                '{"mode": 1, "lock_mouse_to_monster": 1}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "must be true or false"):
                load_mode_config(path)

    def test_mode_config_validates_optional_left_click_boolean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mode.json"
            path.write_text('{"mode": 1}', encoding="utf-8")
            self.assertFalse(load_mode_config(path).left_click_after_mouse_lock)
            for value in (False, True):
                path.write_text(
                    json.dumps(
                        {"mode": 1, "left_click_after_mouse_lock": value}
                    ),
                    encoding="utf-8",
                )
                self.assertIs(
                    load_mode_config(path).left_click_after_mouse_lock,
                    value,
                )
            path.write_text(
                '{"mode": 1, "left_click_after_mouse_lock": 1}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "must be true or false"):
                load_mode_config(path)

    def test_job_type_accepts_zero_one_two_and_defaults_to_summoner(self) -> None:
        self.assertEqual(BotConfig().job_type, 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            for value in (0, 1, 2):
                path.write_text(json.dumps({"job_type": value}), encoding="utf-8")
                self.assertEqual(bot.load_config(path).job_type, value)
            for value in (True, -1, 3):
                path.write_text(json.dumps({"job_type": value}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "job_type must be 0"):
                    bot.load_config(path)

    def test_priest_shift_tap_timing_requires_a_valid_interval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "priest_left_shift_tap_min_interval_ms": 1301,
                        "priest_left_shift_tap_max_interval_ms": 1300,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "minimum interval"):
                bot.load_config(path)

            path.write_text(
                json.dumps({"priest_left_shift_tap_hold_ms": -1}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "non-negative"):
                bot.load_config(path)

    def test_legacy_always_hold_shift_field_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps({"job_type": 0, "always_hold_lshift": False}),
                encoding="utf-8",
            )
            config = bot.load_config(path)
        self.assertEqual(config.job_type, 0)
        self.assertFalse(hasattr(config, "always_hold_lshift"))

    def test_viewport_to_client_point_flips_unity_y_axis(self) -> None:
        self.assertEqual(viewport_to_client_point((0.5, 0.5, 1.0), 201, 101), (100, 50))
        self.assertEqual(viewport_to_client_point((0.0, 0.0, 1.0), 201, 101), (0, 100))
        self.assertEqual(viewport_to_client_point((1.0, 1.0, 1.0), 201, 101), (200, 0))
        with self.assertRaisesRegex(ValueError, "visible"):
            viewport_to_client_point((1.1, 0.5, 1.0), 201, 101)

    def test_move_mouse_posts_background_message_without_moving_cursor(self) -> None:
        target = monster(
            101,
            1,
            0,
            viewport=(0.5, 0.5, 5.0),
            viewport_visible=True,
        )
        with patch.object(
            bot.win32gui, "GetClientRect", return_value=(0, 0, 201, 101)
        ), patch.object(bot.win32gui, "PostMessage") as post_message, patch.object(
            bot.win32api, "SetCursorPos"
        ) as set_cursor:
            self.assertTrue(move_mouse_to_monster(123, target))
        lparam = 100 | (50 << 16)
        post_message.assert_called_once_with(
            123, bot.win32con.WM_MOUSEMOVE, 0, lparam
        )
        set_cursor.assert_not_called()

    def test_move_mouse_skips_hidden_but_allows_minimized_target(self) -> None:
        hidden = monster(
            101,
            1,
            0,
            viewport=(0.5, 0.5, 5.0),
            viewport_visible=False,
        )
        with patch.object(bot.win32gui, "PostMessage") as post_message:
            self.assertFalse(move_mouse_to_monster(123, hidden))
        post_message.assert_not_called()

        visible = monster(
            101,
            1,
            0,
            viewport=(0.5, 0.5, 5.0),
            viewport_visible=True,
        )
        with patch.object(
            bot.win32gui, "IsIconic", return_value=True
        ) as is_iconic, patch.object(
            bot.win32gui, "GetClientRect", return_value=(0, 0, 201, 101)
        ), patch.object(bot.win32gui, "PostMessage") as post_message:
            self.assertTrue(move_mouse_to_monster(123, visible))
        is_iconic.assert_not_called()
        post_message.assert_called_once()

    def test_background_left_click_uses_monster_client_coordinates(self) -> None:
        target = monster(
            101,
            1,
            0,
            viewport=(0.5, 0.5, 5.0),
            viewport_visible=True,
        )
        with patch.object(
            bot.win32gui, "GetClientRect", return_value=(0, 0, 201, 101)
        ), patch.object(bot.win32gui, "PostMessage") as post_message:
            self.assertTrue(post_left_click_to_monster(123, target))
        lparam = 100 | (50 << 16)
        self.assertEqual(
            [call.args for call in post_message.call_args_list],
            [
                (123, bot.win32con.WM_MOUSEMOVE, 0, lparam),
                (123, bot.win32con.WM_LBUTTONDOWN, bot.win32con.MK_LBUTTON, lparam),
                (123, bot.win32con.WM_LBUTTONUP, 0, lparam),
            ],
        )

    def test_background_left_click_skips_hidden_but_allows_minimized_target(self) -> None:
        hidden = monster(
            101,
            1,
            0,
            viewport=(0.5, 0.5, 5.0),
            viewport_visible=False,
        )
        with patch.object(bot.win32gui, "PostMessage") as post_message:
            self.assertFalse(post_left_click_to_monster(123, hidden))
        post_message.assert_not_called()

        visible = monster(
            101,
            1,
            0,
            viewport=(0.5, 0.5, 5.0),
            viewport_visible=True,
        )
        with patch.object(
            bot.win32gui, "IsIconic", return_value=True
        ) as is_iconic, patch.object(
            bot.win32gui, "GetClientRect", return_value=(0, 0, 201, 101)
        ), patch.object(bot.win32gui, "PostMessage") as post_message:
            self.assertTrue(post_left_click_to_monster(123, visible))
        is_iconic.assert_not_called()
        self.assertEqual(post_message.call_count, 3)

    def test_f8_mouse_lock_runs_only_during_real_monster_navigation(self) -> None:
        local = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        target = monster(
            101,
            10,
            0,
            viewport=(0.5, 0.5, 5.0),
            viewport_visible=True,
        )
        snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            monsters=(target,),
            path=MemoryPath(
                1,
                target.object_id,
                "complete",
                ((0, 0, 0), (10, 0, 0)),
            ),
        )

        def run_once(
            send_input: bool,
            *,
            job_type: int = 1,
            configured_lock: bool = True,
            click_after_lock: bool = False,
        ):
            with patch.object(
                bot.win32gui, "IsWindow", side_effect=[True, False]
            ), patch.object(
                bot.win32api, "GetAsyncKeyState", return_value=0
            ), patch.object(
                bot, "control_menu_hotkey_down", return_value=False
            ), patch.object(
                bot, "load_memory_snapshot", return_value=snapshot
            ), patch.object(
                bot, "write_navigation_request"
            ) as write_request, patch.object(
                bot, "post_key"
            ), patch.object(
                bot, "move_mouse_to_monster"
            ) as move_mouse, patch.object(
                bot, "post_left_click_to_monster"
            ) as left_click, patch.object(bot.time, "sleep"):
                bot.run_bot(
                    123,
                    BotConfig(
                        debug_window=False,
                        pricing_enabled=False,
                        job_type=job_type,
                    ),
                    send_input,
                    disable_loot=True,
                    lock_mouse_to_monster=configured_lock,
                    left_click_after_mouse_lock=click_after_lock,
                )
            return move_mouse, left_click

        move_mouse, left_click = run_once(True)
        move_mouse.assert_called_once_with(123, target)
        left_click.assert_not_called()
        preview_move, preview_click = run_once(False, click_after_lock=True)
        preview_move.assert_not_called()
        preview_click.assert_not_called()

        priest_move, priest_click = run_once(
            True,
            job_type=2,
            configured_lock=False,
            click_after_lock=True,
        )
        priest_move.assert_not_called()
        priest_click.assert_not_called()

    def test_left_click_runs_once_retries_failure_and_resets_after_reacquire(self) -> None:
        local = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        target = monster(
            101,
            10,
            0,
            viewport=(0.5, 0.5, 5.0),
            viewport_visible=True,
        )
        target_snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            monsters=(target,),
            path=MemoryPath(
                1,
                target.object_id,
                "complete",
                ((0, 0, 0), (10, 0, 0)),
            ),
        )
        next_target = monster(
            102,
            9,
            0,
            viewport=(0.6, 0.5, 5.0),
            viewport_visible=True,
        )
        next_target_snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            monsters=(next_target,),
            path=MemoryPath(
                2,
                next_target.object_id,
                "complete",
                ((0, 0, 0), (9, 0, 0)),
            ),
        )
        empty_snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            monsters=(),
            path=MemoryPath(0, 0, "missing", ()),
        )

        def run_snapshots(
            snapshots, click_results, *, click_after_lock: bool = True
        ):
            with patch.object(
                bot.win32gui,
                "IsWindow",
                side_effect=[True] * len(snapshots) + [False],
            ), patch.object(
                bot.win32api, "GetAsyncKeyState", return_value=0
            ), patch.object(
                bot, "control_menu_hotkey_down", return_value=False
            ), patch.object(
                bot, "load_memory_snapshot", side_effect=snapshots
            ), patch.object(
                bot, "write_navigation_request"
            ), patch.object(
                bot, "post_key"
            ), patch.object(
                bot, "move_mouse_to_monster", return_value=True
            ) as move_mouse, patch.object(
                bot,
                "post_left_click_to_monster",
                side_effect=click_results,
            ) as left_click, patch.object(bot.time, "sleep"):
                bot.run_bot(
                    123,
                    BotConfig(debug_window=False, pricing_enabled=False),
                    True,
                    disable_loot=True,
                    lock_mouse_to_monster=True,
                    left_click_after_mouse_lock=click_after_lock,
                )
            return move_mouse, left_click

        one_move, one_click = run_snapshots(
            [target_snapshot, target_snapshot], [True]
        )
        self.assertEqual(one_move.call_count, 1)
        self.assertEqual(one_click.call_count, 1)

        retried_move, retried_click = run_snapshots(
            [target_snapshot, target_snapshot], [False, True]
        )
        self.assertEqual(retried_move.call_count, 2)
        self.assertEqual(retried_click.call_count, 2)

        reacquired_move, reacquired_click = run_snapshots(
            [target_snapshot, empty_snapshot, target_snapshot],
            [True, True],
        )
        self.assertEqual(reacquired_move.call_count, 2)
        self.assertEqual(reacquired_click.call_count, 2)

        changed_move, changed_click = run_snapshots(
            [target_snapshot, next_target_snapshot],
            [True, True],
        )
        self.assertEqual(changed_move.call_count, 2)
        self.assertEqual(
            [call.args[1].object_id for call in changed_click.call_args_list],
            [101, 102],
        )

        continuous_move, disabled_click = run_snapshots(
            [target_snapshot, target_snapshot],
            [],
            click_after_lock=False,
        )
        self.assertEqual(continuous_move.call_count, 2)
        disabled_click.assert_not_called()

    def test_f8_job_shift_strategy_applies_to_monster_and_loot_navigation(self) -> None:
        local = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        enemy = monster(
            101,
            10,
            0,
            viewport=(0.5, 0.5, 5.0),
            viewport_visible=True,
        )
        monster_snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            monsters=(enemy,),
            path=MemoryPath(
                1,
                enemy.object_id,
                "complete",
                ((0, 0, 0), (10, 0, 0)),
            ),
        )
        drop = loot(202, 10, 0, rarity="Legendary", rarity_value=3)
        loot_snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            monsters=(),
            loots=(drop,),
            path=MemoryPath(
                1,
                drop.object_id,
                "complete",
                ((0, 0, 0), (10, 0, 0)),
                target_kind="loot",
            ),
            loot_scan={"ownership_filter": "all"},
        )

        def captured_navigation_keys(snapshot, job_type: int, *, disable_loot: bool):
            desired_sets: list[set[str]] = []

            def capture_keys(_hwnd, _held, desired):
                captured = set(desired)
                desired_sets.append(captured)
                return captured

            with patch.object(
                bot.win32gui, "IsWindow", side_effect=[True, False]
            ), patch.object(
                bot.win32api, "GetAsyncKeyState", return_value=0
            ), patch.object(
                bot, "control_menu_hotkey_down", return_value=False
            ), patch.object(
                bot, "load_memory_snapshot", return_value=snapshot
            ), patch.object(
                bot, "write_navigation_request"
            ) as write_request, patch.object(
                bot, "request_path_matches", return_value=True
            ), patch.object(
                bot, "update_held_keys", side_effect=capture_keys
            ), patch.object(
                bot, "move_mouse_to_monster", return_value=True
            ), patch.object(
                bot, "post_left_click_to_monster"
            ) as left_click, patch.object(
                bot, "post_key_tap"
            ) as shift_tap, patch.object(bot, "post_key"), patch.object(
                bot.time, "sleep"
            ):
                bot.run_bot(
                    123,
                    BotConfig(
                        debug_window=False,
                        pricing_enabled=False,
                        job_type=job_type,
                        memory_loot_confirm_frames=1,
                    ),
                    True,
                    disable_loot=disable_loot,
                    lock_mouse_to_monster=True,
                    left_click_after_mouse_lock=True,
                )
            movement_keys = next(
                keys for keys in desired_sets if keys & {"w", "a", "s", "d"}
            )
            return (
                movement_keys,
                left_click.call_count,
                [call.args for call in shift_tap.call_args_list],
                [
                    set(call.kwargs.get("shift_keys", ()))
                    for call in write_request.call_args_list
                ],
            )

        expected = {
            0: {"lshift"},
            1: {"lshift", "rshift"},
            2: set(),
        }
        for job_type, shift_keys in expected.items():
            with self.subTest(job_type=job_type, target="monster"):
                keys, click_count, tap_calls, background_shift_states = (
                    captured_navigation_keys(
                    monster_snapshot,
                    job_type,
                    disable_loot=True,
                    )
                )
                self.assertEqual(keys & set(bot.HELD_SHIFT_KEYS), shift_keys)
                self.assertEqual(click_count, 1)
                self.assertEqual(tap_calls, [])
                expected_background = (
                    {"lshift"} if job_type == 2 else shift_keys
                )
                self.assertIn(expected_background, background_shift_states)
            with self.subTest(job_type=job_type, target="loot"):
                keys, click_count, tap_calls, _ = captured_navigation_keys(
                    loot_snapshot,
                    job_type,
                    disable_loot=False,
                )
                self.assertEqual(keys & set(bot.HELD_SHIFT_KEYS), shift_keys)
                self.assertEqual(click_count, 0)
                self.assertEqual(tap_calls, [])

    def test_train_mode_switches_only_after_real_run_arrival(self) -> None:
        self.assertFalse(
            should_advance_train_target(1, arrived=True, send_input=True)
        )
        self.assertFalse(
            should_advance_train_target(2, arrived=False, send_input=True)
        )
        self.assertFalse(
            should_advance_train_target(2, arrived=True, send_input=False)
        )
        self.assertTrue(
            should_advance_train_target(2, arrived=True, send_input=True)
        )

    def test_rejects_stale_snapshot(self) -> None:
        raw = valid_raw_state()
        raw["timestamp_ms"] = NOW_MS - 751
        with self.assertRaisesRegex(SnapshotUnavailable, "stale"):
            parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)

    def test_rejects_future_snapshot_outside_tolerance(self) -> None:
        raw = valid_raw_state()
        raw["timestamp_ms"] = NOW_MS + 1000
        with self.assertRaisesRegex(SnapshotUnavailable, "stale"):
            parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)

    def test_rejects_wrong_schema_and_probe_error(self) -> None:
        raw = valid_raw_state()
        raw["schema_version"] = 2
        with self.assertRaisesRegex(SnapshotUnavailable, "schema"):
            parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        raw = valid_raw_state()
        raw["status"] = "no_map"
        with self.assertRaisesRegex(SnapshotUnavailable, "no_map"):
            parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)

    def test_relogin_probe_status_includes_phase_attempt_and_message(self) -> None:
        raw = valid_raw_state()
        raw["status"] = "relogin_connecting"
        raw["relogin"] = {
            "state": "CONNECTING",
            "attempt": 2,
            "max_attempts": 5,
            "message": "Connecting to the previous server",
        }
        with self.assertRaisesRegex(
            SnapshotUnavailable,
            "CONNECTING 2/5: Connecting to the previous server",
        ):
            parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)

    def test_defensively_filters_non_hostile_or_unusable_monsters(self) -> None:
        raw = valid_raw_state()
        template = dict(raw["monsters"][0])  # type: ignore[index]
        candidates = [template]
        for object_id, changes in (
            (102, {"team": "ally"}),
            (103, {"alive": False}),
            (104, {"visible": False}),
            (105, {"training_dummy": True}),
            (106, {"health_ratio": 0.0}),
        ):
            item = dict(template)
            item["object_id"] = object_id
            item.update(changes)
            candidates.append(item)
        raw["monsters"] = candidates
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertEqual([item.object_id for item in snapshot.monsters], [101])

    def test_atomic_request_contains_version_identity_and_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            write_navigation_request(
                path,
                12,
                345,
                now_ms=NOW_MS,
                probe_active=True,
                loot_scan_active=True,
                bot_active=True,
                movement_keys=("d", "w", "lshift", "w"),
                movement_world=(4, 0, -7),
                shift_keys=("rshift", "lshift", "lshift"),
                focus_target_object_id=345,
                focus_target_world=(12.5, 3.0, -45.25),
                background_input_mode="both",
                background_skill_mode="click",
                auto_relogin_enabled=True,
                auto_relogin_disconnect_grace_sec=3,
                auto_relogin_builtin_wait_max_sec=30,
                auto_relogin_attempt_timeout_sec=30,
                auto_relogin_retry_delay_sec=10,
                auto_relogin_max_attempts=5,
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            payload,
            {
                "schema_version": 1,
                "request_id": 12,
                "target_kind": "monster",
                "target_object_id": 345,
                "timestamp_ms": NOW_MS,
                "probe_active": True,
                "loot_scan_active": True,
                "party_follow_active": False,
                "bot_active": True,
                "movement_keys": "wd",
                "movement_world": [1, 0, -1],
                "shift_keys": "lshift,rshift",
                "summon_action": "",
                "skill_key_request_id": 0,
                "skill_key": "",
                "skill_key_target_summon": False,
                "loot_interact": 0,
                "loot_interact_object_id": 0,
                "focus_target_object_id": 345,
                "focus_target_world": [12.5, 3.0, -45.25],
                "background_input_mode": "both",
                "background_skill_mode": "click",
                "auto_relogin_enabled": True,
                "auto_relogin_disconnect_grace_sec": 3.0,
                "auto_relogin_builtin_wait_max_sec": 30.0,
                "auto_relogin_attempt_timeout_sec": 30.0,
                "auto_relogin_retry_delay_sec": 10.0,
                "auto_relogin_max_attempts": 5,
            },
        )

    def test_summon_action_is_serialized_and_validated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            write_navigation_request(
                path, 0, 0, target_kind="none", now_ms=NOW_MS,
                bot_active=True, summon_action="mount",
            )
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["summon_action"],
                "mount",
            )
            write_navigation_request(
                path, 0, 0, target_kind="none", now_ms=NOW_MS,
                bot_active=True, summon_action="reanimation",
            )
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["summon_action"],
                "reanimation",
            )
            # Unknown values are dropped to an empty intent.
            write_navigation_request(
                path, 0, 0, target_kind="none", now_ms=NOW_MS,
                bot_active=True, summon_action="jump",
            )
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["summon_action"],
                "",
            )

    def test_consumable_use_request_is_serialized_only_when_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            write_navigation_request(
                path,
                0,
                0,
                target_kind="none",
                now_ms=NOW_MS,
                bot_active=True,
                consumable_use_request_id=987,
                consumable_name=" Soldier Termite ",
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["consumable_use_request_id"], 987)
            self.assertEqual(payload["consumable_name"], "Soldier Termite")
            write_navigation_request(
                path,
                0,
                0,
                target_kind="none",
                now_ms=NOW_MS,
                consumable_use_request_id=988,
                consumable_name=" ",
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("consumable_use_request_id", payload)
            self.assertNotIn("consumable_name", payload)

    def test_follow_channel_request_is_serialized_only_with_a_player(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            write_navigation_request(
                path,
                0,
                0,
                target_kind="none",
                now_ms=NOW_MS,
                bot_active=True,
                follow_channel_request_id=4,
                follow_player_id="party-target",
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["follow_channel_request_id"], 4)
            self.assertEqual(payload["follow_player_id"], "party-target")

            write_navigation_request(
                path,
                0,
                0,
                target_kind="none",
                now_ms=NOW_MS,
                follow_channel_request_id=5,
                follow_player_id="",
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("follow_channel_request_id", payload)
        self.assertNotIn("follow_player_id", payload)

    def test_party_follow_serializes_identity_without_channel_switch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            write_navigation_request(
                path,
                8,
                70,
                target_kind="player",
                now_ms=NOW_MS,
                party_follow_active=True,
                bot_active=True,
                follow_player_id="party-target",
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(payload["probe_active"])
        self.assertTrue(payload["party_follow_active"])
        self.assertEqual(payload["follow_player_id"], "party-target")
        self.assertNotIn("follow_channel_request_id", payload)

    def test_party_member_channel_state_is_parsed(self) -> None:
        raw = valid_raw_state()
        raw["party_members"] = [
            {
                "display_name": "Target",
                "player_id": "target-id",
                "object_id": 0,
                "map_id": 8,
                "instance_id": "server-b",
                "channel_index": 2,
                "is_local": False,
            }
        ]
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertTrue(snapshot.party_state_available)
        self.assertEqual(snapshot.party_members[0].player_id, "target-id")
        self.assertEqual(party_channel_number(snapshot.party_members[0]), 3)

    def test_relogin_request_defaults_are_safe_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            write_navigation_request(
                path,
                0,
                0,
                target_kind="none",
                now_ms=NOW_MS,
                auto_relogin_max_attempts=100,
                auto_relogin_disconnect_grace_sec=0,
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(payload["bot_active"])
        self.assertNotIn("job_type", payload)
        self.assertNotIn("ensure_mounted_summon", payload)
        self.assertFalse(payload["auto_relogin_enabled"])
        self.assertEqual(payload["auto_relogin_max_attempts"], 20)
        self.assertEqual(payload["auto_relogin_disconnect_grace_sec"], 0.5)
        self.assertEqual(BotConfig().auto_relogin_max_attempts, 5)

    def test_summoner_checks_default_off_and_old_config_is_compatible(self) -> None:
        self.assertTrue(
            all(not item["enabled"] for item in BotConfig().summoner_checks.values())
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"job_type": 1}), encoding="utf-8")
            config = bot.load_config(path)
        self.assertEqual(tuple(config.summoner_checks), bot.SUMMONER_CHECK_ORDER)

    def test_enabled_summoner_check_requires_valid_numpad_key(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(
                    {"summoner_checks": {"Invoker": {"enabled": True, "key": ""}}}
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "has no NumPad key"):
                bot.load_config(path)
            path.write_text(
                json.dumps(
                    {"summoner_checks": {"Invoker": {"enabled": True, "key": "5"}}}
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "numpad0 through numpad9"):
                bot.load_config(path)

    def test_summoner_check_presence_uses_current_ids_case_insensitively(self) -> None:
        config = BotConfig()
        config.summoner_checks["SummonSkeleton"] = {
            "enabled": True,
            "key": "numpad1",
        }
        config.summoner_checks["Invoker"] = {"enabled": True, "key": "numpad2"}
        player = MemoryPlayer(
            (0, 0, 0),
            (0, 1),
            (1, 0),
            0.4,
            summon_displays_available=True,
            summon_display_skill_ids=("summonskeleton", "SummonSkeleton"),
            active_statuses_available=True,
            active_status_ids=("INVOKER",),
        )
        self.assertEqual(missing_summoner_checks(config, player), ((), ""))

    def test_summoner_check_safely_waits_for_required_source(self) -> None:
        config = BotConfig()
        config.summoner_checks["Conjurer"] = {
            "enabled": True,
            "key": "numpad3",
        }
        player = MemoryPlayer(
            (0, 0, 0),
            (0, 1),
            (1, 0),
            0.4,
            active_statuses_available=False,
            active_statuses_error="not exported",
        )
        state = SummonerCheckState()
        pressed: list[str] = []
        self.assertTrue(
            advance_summoner_checks(
                state,
                config,
                player,
                enabled=True,
                now=1.0,
                press_key=lambda key, target_summon=False: pressed.append(key),
            )
        )
        self.assertEqual(state.phase, "unavailable")
        self.assertEqual(pressed, [])

    def test_summoner_check_retries_each_missing_item_without_spam(self) -> None:
        config = BotConfig(
            summoner_check_settle_ms=750,
            summoner_check_retry_delay_ms=2500,
        )
        config.summoner_checks["SummonSkeleton"] = {
            "enabled": True,
            "key": "numpad1",
        }
        config.summoner_checks["Invoker"] = {"enabled": True, "key": "numpad2"}
        player = MemoryPlayer(
            (0, 0, 0),
            (0, 1),
            (1, 0),
            0.4,
            summon_displays_available=True,
            active_statuses_available=True,
        )
        state = SummonerCheckState()
        pressed: list[str] = []

        def press(key: str, target_summon: bool = False) -> bool:
            pressed.append(key)
            return True

        for now in (1.0, 1.5, 1.75):
            self.assertTrue(
                advance_summoner_checks(
                    state, config, player, enabled=True, now=now, press_key=press
                )
            )
        self.assertEqual(pressed, ["numpad1", "numpad2"])

        restored = replace(
            player,
            summon_display_skill_ids=("SummonSkeleton",),
            active_status_ids=("Invoker",),
        )
        self.assertFalse(
            advance_summoner_checks(
                state, config, restored, enabled=True, now=2.5, press_key=press
            )
        )
        self.assertEqual(state.phase, "ready")

    def test_summoner_checks_only_enable_for_live_job_one_f8(self) -> None:
        config = BotConfig()
        config.summoner_checks["Invoker"] = {"enabled": True, "key": "numpad2"}
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        self.assertTrue(
            summoner_checks_enabled(
                config,
                player,
                send_input=True,
                active=True,
                follow_mode=False,
            )
        )
        for job_type, send_input, active, follow_mode in (
            (2, True, True, False),
            (1, False, True, False),
            (1, True, False, False),
            (1, True, True, True),
        ):
            config.job_type = job_type
            self.assertFalse(
                summoner_checks_enabled(
                    config,
                    player,
                    send_input=send_input,
                    active=active,
                    follow_mode=follow_mode,
                )
            )
        self.assertFalse(
            summoner_checks_enabled(
                BotConfig(),
                player,
                send_input=True,
                active=True,
                follow_mode=False,
            )
        )

    def test_summon_mount_blocks_only_job_type_one_with_probe_state(self) -> None:
        player = MemoryPlayer(
            position=(0.0, 0.0, 0.0),
            camera_forward_xz=(0.0, 1.0),
            camera_right_xz=(1.0, 0.0),
            collider_radius=0.5,
            is_mounted_summon=False,
            mounted_summon_state_available=True,
            summon_mount_action_available=True,
        )
        self.assertTrue(
            summon_mount_blocks_navigation(
                BotConfig(job_type=1), player, send_input=True, active=True
            )
        )
        self.assertFalse(
            summon_mount_blocks_navigation(
                BotConfig(job_type=2), player, send_input=True, active=True
            )
        )
        self.assertFalse(
            summon_mount_blocks_navigation(
                BotConfig(job_type=0), player, send_input=True, active=True
            )
        )
        self.assertFalse(
            summon_mount_blocks_navigation(
                BotConfig(job_type=1), player, send_input=False, active=True
            )
        )
        self.assertFalse(
            summon_mount_blocks_navigation(
                BotConfig(job_type=1), player, send_input=True, active=False
            )
        )
        self.assertFalse(
            summon_mount_blocks_navigation(
                BotConfig(job_type=1),
                MemoryPlayer(
                    position=player.position,
                    camera_forward_xz=player.camera_forward_xz,
                    camera_right_xz=player.camera_right_xz,
                    collider_radius=player.collider_radius,
                    is_mounted_summon=False,
                    mounted_summon_state_available=False,
                    summon_mount_action_available=False,
                ),
                send_input=True,
                active=True,
            )
        )
        self.assertFalse(
            summon_mount_blocks_navigation(
                BotConfig(job_type=1),
                MemoryPlayer(
                    position=player.position,
                    camera_forward_xz=player.camera_forward_xz,
                    camera_right_xz=player.camera_right_xz,
                    collider_radius=player.collider_radius,
                    is_mounted_summon=True,
                    mounted_summon_state_available=True,
                    summon_mount_action_available=True,
                ),
                send_input=True,
                active=True,
            )
        )
        state = SummonMountKeyState()
        pressed: list[tuple[str, int]] = []
        common = {
            "state": state,
            "mounted": False,
            "summon_ready": True,
            "enabled": True,
            "reanimation_key": "9",
            "mount_key": "0",
            "key_hold_ms": 50,
            "reanimation_delay_ms": 750,
            "confirm_timeout_ms": 4000,
            "mount_key_retry_delay_ms": 400,
            "retry_delay_ms": 2500,
            "press_key": lambda key, hold_ms: pressed.append((key, hold_ms)),
        }
        self.assertTrue(advance_summon_mount_hotkeys(now=1.0, **common))
        self.assertEqual(pressed, [("9", 50)])
        self.assertIn("REANIMATION_SENT", summon_mount_wait_status(state))
        self.assertTrue(advance_summon_mount_hotkeys(now=1.74, **common))
        self.assertEqual(pressed, [("9", 50)])
        self.assertTrue(advance_summon_mount_hotkeys(now=1.75, **common))
        self.assertEqual(pressed, [("9", 50), ("0", 50)])
        self.assertIn("MOUNT_SENT", summon_mount_wait_status(state))
        self.assertTrue(advance_summon_mount_hotkeys(now=2.14, **common))
        self.assertEqual(pressed, [("9", 50), ("0", 50)])
        self.assertTrue(advance_summon_mount_hotkeys(now=2.15, **common))
        self.assertEqual(pressed, [("9", 50), ("0", 50), ("0", 50)])
        mounted = dict(common)
        mounted["mounted"] = True
        self.assertFalse(advance_summon_mount_hotkeys(now=2.2, **mounted))
        self.assertEqual(state.phase, "mounted")

        retry_state = SummonMountKeyState()
        retry_pressed: list[tuple[str, int]] = []
        retry_common = dict(common)
        retry_common["state"] = retry_state
        retry_common["press_key"] = (
            lambda key, hold_ms: retry_pressed.append((key, hold_ms))
        )
        self.assertTrue(advance_summon_mount_hotkeys(now=10.0, **retry_common))
        self.assertTrue(advance_summon_mount_hotkeys(now=10.75, **retry_common))
        self.assertTrue(advance_summon_mount_hotkeys(now=11.14, **retry_common))
        self.assertEqual(retry_pressed, [("9", 50), ("0", 50)])
        self.assertTrue(advance_summon_mount_hotkeys(now=11.15, **retry_common))
        self.assertTrue(advance_summon_mount_hotkeys(now=14.74, **retry_common))
        self.assertEqual(
            retry_pressed, [("9", 50), ("0", 50), ("0", 50), ("0", 50)]
        )
        self.assertTrue(advance_summon_mount_hotkeys(now=14.75, **retry_common))
        self.assertEqual(retry_state.phase, "retry_wait")
        self.assertTrue(advance_summon_mount_hotkeys(now=17.24, **retry_common))
        self.assertEqual(
            retry_pressed, [("9", 50), ("0", 50), ("0", 50), ("0", 50)]
        )
        self.assertTrue(advance_summon_mount_hotkeys(now=17.25, **retry_common))
        self.assertEqual(
            retry_pressed,
            [("9", 50), ("0", 50), ("0", 50), ("0", 50), ("9", 50)],
        )

        retry_common["enabled"] = False
        self.assertFalse(advance_summon_mount_hotkeys(now=18.0, **retry_common))
        self.assertEqual(retry_state.phase, "idle")

    def test_summon_mount_waits_for_mountable_summon(self) -> None:
        state = SummonMountKeyState()
        pressed: list[tuple[str, int]] = []
        common = {
            "state": state,
            "mounted": False,
            "enabled": True,
            "reanimation_key": "9",
            "mount_key": "0",
            "key_hold_ms": 50,
            "reanimation_delay_ms": 750,
            "confirm_timeout_ms": 4000,
            "mount_key_retry_delay_ms": 400,
            "retry_delay_ms": 2500,
            "press_key": lambda key, hold_ms: pressed.append((key, hold_ms)),
        }
        # Reanimation is sent, but the summon has not appeared yet.
        self.assertTrue(
            advance_summon_mount_hotkeys(now=1.0, summon_ready=False, **common)
        )
        self.assertEqual(pressed, [("9", 50)])
        # Past the reanimation delay, the mount key is still withheld because
        # no mountable summon exists.
        self.assertTrue(
            advance_summon_mount_hotkeys(now=2.0, summon_ready=False, **common)
        )
        self.assertEqual(pressed, [("9", 50)])
        self.assertIn("REANIMATION_SENT", summon_mount_wait_status(state))
        # Once the summon exists, the mount key fires.
        self.assertTrue(
            advance_summon_mount_hotkeys(now=2.5, summon_ready=True, **common)
        )
        self.assertEqual(pressed, [("9", 50), ("0", 50)])
        self.assertIn("MOUNT_SENT", summon_mount_wait_status(state))

    def test_summon_mount_reanimates_again_when_summon_never_ready(self) -> None:
        state = SummonMountKeyState()
        pressed: list[tuple[str, int]] = []
        common = {
            "state": state,
            "mounted": False,
            "summon_ready": False,
            "enabled": True,
            "reanimation_key": "9",
            "mount_key": "0",
            "key_hold_ms": 50,
            "reanimation_delay_ms": 750,
            "confirm_timeout_ms": 4000,
            "mount_key_retry_delay_ms": 400,
            "retry_delay_ms": 2500,
            "press_key": lambda key, hold_ms: pressed.append((key, hold_ms)),
        }
        self.assertTrue(advance_summon_mount_hotkeys(now=1.0, **common))
        self.assertEqual(pressed, [("9", 50)])
        # Summon never becomes ready: after confirm_timeout the state falls
        # back to retry_wait with the not-ready reason, and never presses "0".
        self.assertTrue(advance_summon_mount_hotkeys(now=5.0, **common))
        self.assertEqual(state.phase, "retry_wait")
        self.assertIn("summon was not ready", summon_mount_wait_status(state))
        self.assertEqual(pressed, [("9", 50)])
        # After the retry delay the reanimation key is pressed again.
        self.assertTrue(advance_summon_mount_hotkeys(now=7.5, **common))
        self.assertEqual(pressed, [("9", 50), ("9", 50)])

    def test_job_type_two_never_auto_taps_zero(self) -> None:
        player = MemoryPlayer(
            position=(0.0, 0.0, 0.0),
            camera_forward_xz=(0.0, 1.0),
            camera_right_xz=(1.0, 0.0),
            collider_radius=0.45,
            alive=True,
        )
        snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=player,
            monsters=(),
            path=MemoryPath(0, 0, "missing", ()),
        )

        with patch.object(
            bot.win32gui, "IsWindow", side_effect=[True, False]
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "control_menu_hotkey_down", return_value=False
        ), patch.object(
            bot, "load_memory_snapshot", return_value=snapshot
        ), patch.object(
            bot, "write_navigation_request"
        ), patch.object(
            bot, "post_key_tap"
        ) as tap, patch.object(
            bot, "post_key"
        ), patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                BotConfig(
                    debug_window=False,
                    pricing_enabled=False,
                    job_type=2,
                ),
                True,
                disable_loot=True,
            )

        tap.assert_not_called()

    def test_summon_mount_gate_precedes_f2_and_f8_navigation(self) -> None:
        source = Path(bot.__file__).read_text(encoding="utf-8")
        gate = "if update_summon_mount_keys(snapshot.player, now):"
        self.assertEqual(source.count(gate), 1)
        marker = source.index(
            "# Summoner mount maintenance gates either general F8 navigation or"
        )
        check_marker = source.index(
            "# Selected job-type-1 summons/buffs gate formal F8 navigation only."
        )
        self.assertLess(check_marker, marker)
        self.assertLess(marker, source.index("if follow_mode:", marker))
        self.assertLess(marker, source.index("if loot_target is not None:", marker))
        self.assertLess(marker, source.index("if target is None:", marker))

    def test_local_player_death_releases_keys_before_any_other_action(self) -> None:
        alive_player = MemoryPlayer(
            position=(0.0, 0.0, 0.0),
            camera_forward_xz=(0.0, 1.0),
            camera_right_xz=(1.0, 0.0),
            collider_radius=0.45,
            is_mounted_summon=True,
            mounted_summon_state_available=True,
            summon_mount_action_available=True,
            alive=True,
        )
        dead_player = MemoryPlayer(
            position=alive_player.position,
            camera_forward_xz=alive_player.camera_forward_xz,
            camera_right_xz=alive_player.camera_right_xz,
            collider_radius=alive_player.collider_radius,
            is_mounted_summon=False,
            mounted_summon_state_available=True,
            summon_mount_action_available=True,
            alive=False,
        )
        enemy = monster(101, 10, 0)

        def snapshot(player: MemoryPlayer) -> MemorySnapshot:
            return MemorySnapshot(
                timestamp_ms=NOW_MS,
                map_id=1,
                instance_id=1,
                player=player,
                monsters=(enemy,),
                path=MemoryPath(
                    1,
                    enemy.object_id,
                    "complete",
                    ((0, 0, 0), (10, 0, 0)),
                ),
            )

        desired_sets: list[set[str]] = []

        def capture_keys(_hwnd, _held, desired):
            captured = set(desired)
            desired_sets.append(captured)
            return captured

        with patch.object(
            bot.win32gui, "IsWindow", side_effect=[True, True, False]
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "control_menu_hotkey_down", return_value=False
        ), patch.object(
            bot,
            "load_memory_snapshot",
            side_effect=[snapshot(alive_player), snapshot(dead_player)],
        ), patch.object(
            bot, "request_path_matches", return_value=True
        ), patch.object(
            bot, "write_navigation_request"
        ), patch.object(
            bot, "update_held_keys", side_effect=capture_keys
        ), patch.object(
            bot, "post_key_tap"
        ) as tap, patch.object(
            bot, "post_key"
        ), patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                BotConfig(
                    debug_window=False,
                    pricing_enabled=False,
                    job_type=1,
                    loop_delay_ms=0,
                ),
                True,
                disable_loot=True,
            )

        active_index = next(
            index for index, desired in enumerate(desired_sets) if desired
        )
        self.assertTrue({"lshift", "rshift"} <= desired_sets[active_index])
        self.assertTrue(desired_sets[active_index + 1 :])
        self.assertTrue(
            all(not desired for desired in desired_sets[active_index + 1 :])
        )
        tap.assert_not_called()

    def test_loot_request_serializes_target_kind_and_rejects_unknown_kind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            write_navigation_request(
                path,
                13,
                501,
                target_kind="loot",
                now_ms=NOW_MS,
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["target_kind"], "loot")
            write_navigation_request(
                path,
                14,
                701,
                target_kind="player",
                now_ms=NOW_MS,
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["target_kind"], "player")
            with self.assertRaisesRegex(ValueError, "target_kind"):
                write_navigation_request(path, 15, 501, target_kind="chest")

    def test_snapshot_read_retries_transient_windows_share_error(self) -> None:
        encoded = json.dumps(valid_raw_state())
        with patch.object(
            bot,
            "_read_windows_shared_text",
            side_effect=[PermissionError(13, "sharing violation"), encoded],
        ), patch.object(bot.time, "sleep") as sleep:
            snapshot = load_memory_snapshot(
                Path("state.json"), 750, now_ms=NOW_MS
            )
        self.assertEqual(snapshot.monsters[0].object_id, 101)
        sleep.assert_called_once()

    def test_no_enemy_status_includes_probe_scan_diagnostics(self) -> None:
        raw = valid_raw_state()
        raw["monsters"] = []
        raw["monster_scan"] = {
            "source": "units",
            "monsters_count": 0,
            "units_count": 4,
            "scene_count": 7,
            "scene_status": "ok",
            "source_count": 4,
            "castable": 3,
            "rejected_no_network_object": 0,
            "rejected_other_map": 1,
            "unknown_map_candidates": 2,
            "accepted_by_navmesh": 1,
            "rejected_no_navmesh": 1,
            "navmesh_filter_error": "",
            "rejected_inactive": 1,
            "rejected_not_displayed": 1,
            "rejected_dead": 0,
            "rejected_no_data": 0,
            "rejected_not_enemy": 1,
            "team_values": [0],
            "network_maps": {"35/0": 3},
        }
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        status = no_enemy_status(snapshot)
        self.assertIn("source=units", status)
        self.assertIn("Monsters/Units=0/4", status)
        self.assertIn("scene=7", status)
        self.assertIn("scene-status=ok", status)
        self.assertIn("other-map=1", status)
        self.assertIn("unknown/nav-ok/nav-bad=2/1/1", status)
        self.assertIn("network-maps={'35/0': 3}", status)
        self.assertIn("teams=[0]", status)

    def test_stale_snapshot_log_key_ignores_changing_age(self) -> None:
        first = snapshot_error_log_key(
            SnapshotUnavailable("memory state is stale (50065 ms)")
        )
        second = snapshot_error_log_key(
            SnapshotUnavailable("memory state is stale (60068 ms)")
        )
        self.assertEqual(first, second)

    def test_control_menu_hotkey_only_fires_for_foreground_window(self) -> None:
        # Key up: never fires regardless of foreground.
        with patch.object(bot.win32api, "GetAsyncKeyState", return_value=0):
            self.assertFalse(bot.control_menu_hotkey_down(123))
        # Key down but a different game window is focused: ignored so other
        # running bot instances don't all pop their menu on one F8 press.
        with patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0x8000
        ), patch.object(bot.win32gui, "GetForegroundWindow", return_value=999):
            self.assertFalse(bot.control_menu_hotkey_down(123))
        # Key down and this bot's window is focused: fires.
        with patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0x8000
        ), patch.object(bot.win32gui, "GetForegroundWindow", return_value=123):
            self.assertTrue(bot.control_menu_hotkey_down(123))
        # Foreground unreadable: do NOT open, so an error can never revert to
        # popping every instance's menu.
        with patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0x8000
        ), patch.object(
            bot.win32gui, "GetForegroundWindow", side_effect=OSError("boom")
        ):
            self.assertFalse(bot.control_menu_hotkey_down(123))

    def test_start_paused_config_launches_with_navigation_off(self) -> None:
        with patch.object(
            bot.win32gui, "IsWindow", side_effect=[True, False]
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "control_menu_hotkey_down", return_value=False
        ), patch.object(
            bot, "write_navigation_request"
        ) as write_request, patch.object(
            bot, "update_held_keys", side_effect=lambda hwnd, held, desired: set(desired)
        ), patch.object(bot, "post_key"), patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                BotConfig(
                    debug_window=False,
                    pricing_enabled=False,
                    start_paused=True,
                ),
                True,
            )
        # With start_paused the very first heartbeat is already inactive.
        self.assertFalse(write_request.call_args_list[0].kwargs["bot_active"])

    def test_f8_pause_publishes_inactive_relogin_heartbeat(self) -> None:
        with patch.object(
            bot.win32gui, "IsWindow", side_effect=[True, False]
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "control_menu_hotkey_down", side_effect=[False, True]
        ), patch.object(
            bot, "show_control_menu", return_value="navigation"
        ), patch.object(
            bot, "write_navigation_request"
        ) as write_request, patch.object(
            bot, "move_mouse_to_monster"
        ) as move_mouse, patch.object(
            bot, "update_held_keys", side_effect=lambda hwnd, held, desired: set(desired)
        ), patch.object(
            bot,
            "wait_for_wallet_snapshot",
            side_effect=SnapshotUnavailable("test wallet unavailable"),
        ), patch.object(bot, "post_key") as post_key, patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                BotConfig(debug_window=False, pricing_enabled=False),
                True,
                lock_mouse_to_monster=True,
            )

        self.assertTrue(write_request.call_args_list[0].kwargs["bot_active"])
        self.assertTrue(write_request.call_args_list[1].kwargs["bot_active"])
        self.assertFalse(write_request.call_args_list[-1].kwargs["bot_active"])
        move_mouse.assert_not_called()
        self.assertIn(((123, "lshift", False), {}), [
            (call.args, call.kwargs) for call in post_key.call_args_list
        ])
        self.assertIn(((123, "rshift", False), {}), [
            (call.args, call.kwargs) for call in post_key.call_args_list
        ])

    def test_f9_shutdown_publishes_inactive_relogin_heartbeat(self) -> None:
        with patch.object(
            bot.win32gui, "IsWindow", return_value=True
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "control_menu_hotkey_down", side_effect=[False, True]
        ), patch.object(
            bot, "show_control_menu", return_value="exit"
        ), patch.object(
            bot, "write_navigation_request"
        ) as write_request, patch.object(
            bot, "update_held_keys", side_effect=lambda hwnd, held, desired: set(desired)
        ), patch.object(
            bot,
            "wait_for_wallet_snapshot",
            side_effect=SnapshotUnavailable("test wallet unavailable"),
        ), patch.object(bot, "post_key") as post_key:
            bot.run_bot(
                123, BotConfig(debug_window=False, pricing_enabled=False), True
            )

        self.assertTrue(write_request.call_args_list[0].kwargs["bot_active"])
        self.assertFalse(write_request.call_args_list[-1].kwargs["bot_active"])
        post_key.assert_any_call(123, "lshift", False)
        post_key.assert_any_call(123, "rshift", False)


class NavigationEarningsTests(unittest.TestCase):
    def test_accumulates_only_positive_wallet_changes_and_deduplicates(self) -> None:
        state = NavigationEarningsState()
        start_navigation_earnings(state, now=10.0)
        observe_navigation_wallet(
            state,
            snapshot_timestamp_ms=1,
            wallet_coins_available=True,
            wallet_coins=100,
        )
        observe_navigation_wallet(
            state,
            snapshot_timestamp_ms=2,
            wallet_coins_available=True,
            wallet_coins=120,
        )
        observe_navigation_wallet(
            state,
            snapshot_timestamp_ms=2,
            wallet_coins_available=True,
            wallet_coins=999,
        )
        observe_navigation_wallet(
            state,
            snapshot_timestamp_ms=3,
            wallet_coins_available=True,
            wallet_coins=90,
        )
        observe_navigation_wallet(
            state,
            snapshot_timestamp_ms=4,
            wallet_coins_available=True,
            wallet_coins=110,
        )
        report = finish_navigation_earnings(state, now=70.0)
        self.assertIsNotNone(report)
        assert report is not None
        self.assertEqual(report.gross_income, 40)
        self.assertEqual(report.current_wallet_coins, 110)
        self.assertEqual(report.wallet_sample_count, 4)
        self.assertIn("運行 00:01:00", format_navigation_earnings_report(report))
        self.assertIn("金幣總收入 40", format_navigation_earnings_report(report))

    def test_follow_pause_excludes_time_and_does_not_bridge_wallet_delta(self) -> None:
        state = NavigationEarningsState()
        start_navigation_earnings(state, now=0.0)
        observe_navigation_wallet(
            state,
            snapshot_timestamp_ms=1,
            wallet_coins_available=True,
            wallet_coins=100,
        )
        pause_navigation_earnings(state, now=10.0)
        observe_navigation_wallet(
            state,
            snapshot_timestamp_ms=2,
            wallet_coins_available=True,
            wallet_coins=200,
        )
        resume_navigation_earnings(state, now=30.0)
        observe_navigation_wallet(
            state,
            snapshot_timestamp_ms=3,
            wallet_coins_available=True,
            wallet_coins=200,
        )
        observe_navigation_wallet(
            state,
            snapshot_timestamp_ms=4,
            wallet_coins_available=True,
            wallet_coins=205,
        )
        report = finish_navigation_earnings(state, now=40.0)
        self.assertIsNotNone(report)
        assert report is not None
        self.assertEqual(report.elapsed_seconds, 20.0)
        self.assertEqual(report.gross_income, 5)
        self.assertEqual(report.current_wallet_coins, 205)

    def test_unavailable_wallet_warns_and_finish_is_idempotent(self) -> None:
        state = NavigationEarningsState()
        start_navigation_earnings(state, now=1.0)
        observe_navigation_wallet(
            state,
            snapshot_timestamp_ms=1,
            wallet_coins_available=False,
        )
        report = finish_navigation_earnings(state, now=2.0)
        self.assertIsNotNone(report)
        assert report is not None
        self.assertTrue(report.data_incomplete)
        self.assertEqual(report.wallet_sample_count, 0)
        text = format_navigation_earnings_report(report)
        self.assertIn("金幣總收入 無法計算", text)
        self.assertIn("收入可能低估", text)
        self.assertIsNone(finish_navigation_earnings(state, now=3.0))

    def test_wait_for_wallet_snapshot_requires_new_available_sample(self) -> None:
        base = parse_memory_snapshot(
            valid_raw_state(), now_ms=NOW_MS, max_age_ms=750
        )
        stale = replace(base, timestamp_ms=99)
        fresh = replace(base, timestamp_ms=100)
        with patch.object(bot, "load_memory_snapshot", side_effect=[stale, fresh]):
            result = wait_for_wallet_snapshot(
                Path("ignored.json"),
                750,
                after_timestamp_ms=100,
                wait_timeout_ms=200,
            )
        self.assertIs(result, fresh)


class TargetAndPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.player_position = (0.0, 0.0, 0.0)

    def test_selects_nearest_living_enemy(self) -> None:
        target, skipped = select_memory_target(
            [monster(1, 10, 0), monster(2, 3, 4), monster(3, 2, 0, team="ally")],
            self.player_position,
            None,
            {},
            now=10.0,
        )
        self.assertEqual(target.object_id, 2)  # type: ignore[union-attr]
        self.assertEqual(skipped, {})

    def test_keeps_object_identity_even_if_another_enemy_gets_closer(self) -> None:
        target, _ = select_memory_target(
            [monster(1, 9, 0), monster(2, 1, 0)],
            self.player_position,
            1,
            {},
            now=10.0,
        )
        self.assertEqual(target.object_id, 1)  # type: ignore[union-attr]

    def test_switches_when_locked_enemy_dies_or_is_skipped(self) -> None:
        target, active_skips = select_memory_target(
            [monster(1, 1, 0, alive=False), monster(2, 2, 0), monster(3, 3, 0)],
            self.player_position,
            1,
            {2: 20.0, 99: 5.0},
            now=10.0,
        )
        self.assertEqual(target.object_id, 3)  # type: ignore[union-attr]
        self.assertEqual(active_skips, {2: 20.0})

    def test_combat_blocked_target_is_not_selected(self) -> None:
        target, _ = select_memory_target(
            [monster(1, 1, 0), monster(2, 2, 0)],
            self.player_position,
            1,
            {},
            now=10.0,
            blocked_object_ids={1},
        )
        self.assertEqual(target.object_id, 2)  # type: ignore[union-attr]

    def test_requires_matching_complete_path_response(self) -> None:
        path = MemoryPath(7, 101, "complete", ((0, 0, 0), (1, 0, 1)))
        self.assertTrue(request_path_matches(path, 7, 101))
        self.assertFalse(request_path_matches(path, 8, 101))
        self.assertFalse(request_path_matches(path, 7, 999))
        self.assertFalse(
            request_path_matches(MemoryPath(7, 101, "partial", path.corners), 7, 101)
        )
        loot_path = MemoryPath(
            8,
            501,
            "complete",
            ((0, 0, 0), (4, 0, 1)),
            target_kind="loot",
        )
        self.assertTrue(
            request_path_matches(loot_path, 8, 501, target_kind="loot")
        )
        self.assertFalse(request_path_matches(loot_path, 8, 501))

    def test_waypoint_skips_source_corner_inside_tolerance(self) -> None:
        point = select_path_waypoint(
            (0.0, 0.0, 0.0),
            ((0.1, 0.0, 0.1), (2.0, 0.0, 0.0), (5.0, 0.0, 0.0)),
            0.35,
        )
        self.assertEqual(point, (2.0, 0.0, 0.0))

    def test_arrival_radius_uses_both_colliders_and_padding(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        target = monster(1, 1, 0)
        self.assertAlmostEqual(arrival_radius(player, target, BotConfig()), 1.65)

    def test_map_exit_keepout_uses_interaction_player_and_padding(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        map_exit = MemoryMapExit((5, 0, 0), 1.25)
        self.assertAlmostEqual(map_exit_avoidance_radius(player, map_exit, 3.0), 4.65)
        self.assertIs(
            point_inside_map_exit_keepout(player, (1, 0, 0), (map_exit,), 3.0),
            map_exit,
        )
        self.assertIsNone(
            point_inside_map_exit_keepout(player, (-1, 0, 0), (map_exit,), 3.0)
        )

    def test_path_crossing_map_exit_keepout_is_rejected(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.5)
        map_exit = MemoryMapExit((5, 0, 0), 1.0)
        self.assertIs(
            path_enters_map_exit_keepout(
                player,
                ((0, 0, 0), (10, 0, 0)),
                (map_exit,),
                3.0,
            ),
            map_exit,
        )
        self.assertIsNone(
            path_enters_map_exit_keepout(
                player,
                ((0, 0, 0), (0, 0, 10), (10, 0, 10)),
                (map_exit,),
                3.0,
            )
        )

    def test_player_inside_keepout_can_only_follow_path_outward(self) -> None:
        map_exit = MemoryMapExit((5, 0, 0), 1.0)
        player = MemoryPlayer((4, 0, 0), (0, 1), (1, 0), 0.5)
        self.assertIsNone(
            path_enters_map_exit_keepout(
                player, ((4, 0, 0), (0, 0, 0)), (map_exit,), 3.0
            )
        )
        self.assertIs(
            path_enters_map_exit_keepout(
                player, ((4, 0, 0), (5, 0, 0)), (map_exit,), 3.0
            ),
            map_exit,
        )


class FollowPlayerTests(unittest.TestCase):
    def test_party_target_resolves_channel_and_switch_requirement(self) -> None:
        local = party_member(
            "local", channel_index=0, instance_id="server-a", is_local=True
        )
        target = party_member(
            "target", channel_index=2, instance_id="server-a"
        )
        members = (local, target)
        self.assertIs(
            find_follow_party_member_by_name(members, "PLAYER TARGET"), target
        )
        self.assertIs(find_follow_party_member(members, "target"), target)
        self.assertIs(find_local_party_member(members), local)
        self.assertEqual(party_channel_number(target), 3)
        self.assertTrue(party_member_needs_channel_switch(target, local, 1))
        self.assertFalse(
            party_member_needs_channel_switch(
                party_member("target", channel_index=0), local, 1
            )
        )
        self.assertFalse(
            party_member_needs_channel_switch(
                party_member("target", channel_index=2, map_id=9), local, 1
            )
        )

    def test_f2_requests_party_channel_then_follows_when_player_appears(self) -> None:
        local = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        remote_members = (
            party_member(
                "local", channel_index=0, instance_id="server-a", is_local=True
            ),
            party_member("follow-id", channel_index=2, instance_id="server-a"),
        )
        remote_snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            players=(),
            party_members=remote_members,
            party_state_available=True,
            monsters=(),
            path=MemoryPath(0, 0, "missing", ()),
            player_scan={"source": "map", "accepted": 0},
        )
        followed = observed_player(70, "follow-id", 12, 0)
        local_members = (
            party_member(
                "local", channel_index=2, instance_id="server-a", is_local=True
            ),
            party_member("follow-id", channel_index=2, instance_id="server-a"),
        )
        arrived_snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=2,
            player=local,
            players=(followed,),
            party_members=local_members,
            party_state_available=True,
            monsters=(),
            path=MemoryPath(
                1,
                70,
                "complete",
                ((0, 0, 0), (12, 0, 0)),
                target_kind="player",
            ),
            player_scan={"source": "map", "accepted": 1},
        )
        with patch.object(
            bot.win32gui, "IsWindow", side_effect=[True, True, False]
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "control_menu_hotkey_down", side_effect=[False, True, False]
        ), patch.object(
            bot, "show_control_menu", return_value="follow"
        ), patch.object(
            bot, "prompt_follow_player_name", return_value="Player follow-id"
        ), patch.object(
            bot,
            "load_memory_snapshot",
            side_effect=[remote_snapshot, remote_snapshot, arrived_snapshot],
        ), patch.object(
            bot, "request_path_matches", return_value=True
        ), patch.object(
            bot, "write_navigation_request"
        ) as write_request, patch.object(
            bot, "post_key"
        ), patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                BotConfig(
                    debug_window=False,
                    pricing_enabled=False,
                    job_type=0,
                ),
                True,
                disable_loot=True,
            )

        self.assertTrue(
            any(
                call.kwargs.get("follow_channel_request_id", 0) > 0
                and call.kwargs.get("follow_player_id") == "follow-id"
                for call in write_request.call_args_list
            )
        )
        self.assertTrue(
            any(
                call.args[2] == 70 and call.kwargs["target_kind"] == "player"
                for call in write_request.call_args_list
            )
        )

    def test_f2_is_pure_player_navigation_until_toggled_off(self) -> None:
        local = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        followed = observed_player(
            70, "follow-id", 12, 0, selected=True, visible=False
        )
        enemy = monster(80, 13, 0)
        snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            players=(followed,),
            party_members=same_channel_party_members(),
            party_state_available=True,
            monsters=(enemy,),
            path=MemoryPath(
                1,
                70,
                "complete",
                ((0, 0, 0), (12, 0, 0)),
                target_kind="player",
            ),
            player_scan={"source": "map", "accepted": 1},
        )
        config = BotConfig(debug_window=False, pricing_enabled=False)
        desired_sets: list[set[str]] = []

        def capture_keys(_hwnd, _held, desired):
            captured = set(desired)
            desired_sets.append(captured)
            return captured

        with patch.object(
            bot.win32gui,
            "IsWindow",
            side_effect=[True, True, True, True, False],
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot,
            "control_menu_hotkey_down",
            side_effect=[False, False, True, False, True],
        ), patch.object(
            bot, "show_control_menu", return_value="follow"
        ), patch.object(
            bot, "prompt_follow_player_name", return_value="Player follow-id"
        ), patch.object(
            bot, "load_memory_snapshot", return_value=snapshot
        ), patch.object(
            bot, "request_path_matches", return_value=True
        ), patch.object(
            bot, "write_navigation_request"
        ) as write_request, patch.object(
            bot,
            "update_held_keys",
            side_effect=capture_keys,
        ), patch.object(bot, "post_key"), patch.object(bot.time, "sleep"):
            bot.run_bot(123, config, True, disable_loot=True)

        requests = [
            (
                call.args[2],
                call.kwargs["target_kind"],
            )
            for call in write_request.call_args_list
        ]
        player_request_index = requests.index((70, "player"))
        monster_after_follow = requests.index(
            (80, "monster"), player_request_index + 1
        )
        self.assertTrue(
            all(
                target_kind != "monster"
                for _, target_kind in requests[
                    player_request_index:monster_after_follow
                ]
            )
        )
        self.assertTrue(
            any({"lshift", "rshift"} <= keys for keys in desired_sets)
        )
        self.assertGreaterEqual(desired_sets.count(set()), 2)

    def test_f2_runs_while_f8_is_paused_and_f8_does_not_release_shift(self) -> None:
        local = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        followed = observed_player(70, "follow-id", 12, 0, selected=True)
        snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            players=(followed,),
            party_members=same_channel_party_members(),
            party_state_available=True,
            monsters=(monster(80, 1, 0),),
            loots=(loot(90, 1, 0, rarity="Legendary", rarity_value=3),),
            path=MemoryPath(
                1,
                70,
                "complete",
                ((0, 0, 0), (12, 0, 0)),
                target_kind="player",
            ),
            player_scan={"source": "map", "accepted": 1},
            loot_scan={"ownership_filter": "all"},
        )
        # F8 now only opens the control menu; "follow" starts pure follow and a
        # later "navigation" pick pauses/resumes general navigation. Pausing
        # navigation while following must not release the follow shifts.
        with patch.object(
            bot.win32gui, "IsWindow", side_effect=[True, True, True, True, False]
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot,
            "control_menu_hotkey_down",
            side_effect=[False, True, False, True, False],
        ), patch.object(
            bot, "show_control_menu", side_effect=["follow", "navigation"]
        ), patch.object(
            bot, "prompt_follow_player_name", return_value="Player follow-id"
        ), patch.object(
            bot, "load_memory_snapshot", return_value=snapshot
        ) as load_snapshot, patch.object(
            bot, "request_path_matches", return_value=True
        ), patch.object(
            bot, "write_navigation_request"
        ) as write_request, patch.object(
            bot, "post_key"
        ) as post_key, patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                BotConfig(debug_window=False, pricing_enabled=False),
                True,
            )

        self.assertGreaterEqual(load_snapshot.call_count, 3)
        requests = [
            (call.args[2], call.kwargs["target_kind"], call.kwargs["bot_active"])
            for call in write_request.call_args_list
        ]
        self.assertIn((70, "player", True), requests)
        self.assertNotIn("monster", {kind for _, kind, _ in requests})
        self.assertNotIn("loot", {kind for _, kind, _ in requests})
        self.assertFalse(
            any(
                call.args[1] == "v" and call.args[2]
                for call in post_key.call_args_list
            )
        )
        self.assertTrue(
            any(
                call.kwargs["party_follow_active"]
                and not call.kwargs["probe_active"]
                for call in write_request.call_args_list
            )
        )
        shift_states = [
            set(call.kwargs.get("shift_keys", ()))
            for call in write_request.call_args_list
        ]
        self.assertIn({"lshift", "rshift"}, shift_states)
        self.assertEqual(shift_states[-1], set())
        self.assertFalse(
            any(
                call.args[1] in bot.HELD_SHIFT_KEYS and call.args[2]
                for call in post_key.call_args_list
            )
        )

    def test_f2_holds_only_both_shifts_inside_stop_distance(self) -> None:
        local = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        followed = observed_player(70, "follow-id", 1, 0, selected=True)
        snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            players=(followed,),
            party_members=same_channel_party_members(),
            party_state_available=True,
            monsters=(monster(80, 1, 0),),
            path=MemoryPath(
                1,
                70,
                "complete",
                ((0, 0, 0), (1, 0, 0)),
                target_kind="player",
            ),
            player_scan={"source": "map", "accepted": 1},
        )
        desired_sets: list[set[str]] = []

        def capture_keys(_hwnd, _held, desired):
            captured = set(desired)
            desired_sets.append(captured)
            return captured

        with patch.object(
            bot.win32gui, "IsWindow", side_effect=[True, True, False]
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "control_menu_hotkey_down", side_effect=[False, True, False]
        ), patch.object(
            bot, "show_control_menu", return_value="follow"
        ), patch.object(
            bot, "prompt_follow_player_name", return_value="Player follow-id"
        ), patch.object(
            bot, "load_memory_snapshot", return_value=snapshot
        ), patch.object(
            bot, "request_path_matches", return_value=True
        ), patch.object(
            bot, "write_navigation_request"
        ) as write_request, patch.object(
            bot, "update_held_keys", side_effect=capture_keys
        ), patch.object(bot, "post_key"), patch.object(
            bot, "post_left_click_to_monster"
        ) as left_click, patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                BotConfig(
                    debug_window=False,
                    pricing_enabled=False,
                    job_type=2,
                ),
                True,
                left_click_after_mouse_lock=True,
            )

        self.assertIn({"lshift", "rshift"}, desired_sets)
        self.assertFalse(
            any(keys & {"w", "a", "s", "d"} for keys in desired_sets)
        )
        left_click.assert_not_called()

    def test_f2_releases_shift_when_player_path_becomes_invalid(self) -> None:
        local = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        followed = observed_player(70, "follow-id", 12, 0, selected=True)
        snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            players=(followed,),
            party_members=same_channel_party_members(),
            party_state_available=True,
            monsters=(),
            path=MemoryPath(
                1,
                70,
                "complete",
                ((0, 0, 0), (12, 0, 0)),
                target_kind="player",
            ),
            player_scan={"source": "map", "accepted": 1},
        )
        with patch.object(
            bot.win32gui, "IsWindow", side_effect=[True] * 3
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "control_menu_hotkey_down",
            side_effect=[False, True, False, True],
        ), patch.object(
            bot, "show_control_menu", side_effect=["follow", "exit"]
        ), patch.object(
            bot, "prompt_follow_player_name", return_value="Player follow-id"
        ), patch.object(
            bot, "load_memory_snapshot", return_value=snapshot
        ), patch.object(
            bot, "request_path_matches", side_effect=[True, False]
        ), patch.object(
            bot, "write_navigation_request"
        ) as write_request, patch.object(
            bot, "post_key"
        ) as post_key, patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                BotConfig(debug_window=False, pricing_enabled=False),
                True,
            )

        shift_states = [
            set(call.kwargs.get("shift_keys", ()))
            for call in write_request.call_args_list
        ]
        self.assertIn({"lshift", "rshift"}, shift_states)
        self.assertEqual(shift_states[-1], set())
        self.assertFalse(
            any(
                call.args[1] in bot.HELD_SHIFT_KEYS and call.args[2]
                for call in post_key.call_args_list
            )
        )

    def test_f2_releases_shift_when_snapshot_or_player_is_unavailable(self) -> None:
        local = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        followed = observed_player(70, "follow-id", 12, 0, selected=True)
        snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            players=(followed,),
            party_members=same_channel_party_members(),
            party_state_available=True,
            monsters=(),
            path=MemoryPath(
                1,
                70,
                "complete",
                ((0, 0, 0), (12, 0, 0)),
                target_kind="player",
            ),
            player_scan={"source": "map", "accepted": 1},
        )
        lost_snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=local,
            players=(),
            monsters=(),
            path=snapshot.path,
            player_scan={"source": "map", "accepted": 0},
        )

        for label, unavailable in (
            ("player lost", lost_snapshot),
            ("snapshot unavailable", SnapshotUnavailable("offline")),
        ):
            with self.subTest(label=label):
                with patch.object(
                    bot.win32gui,
                    "IsWindow",
                    side_effect=[True, True, False],
                ), patch.object(
                    bot.win32api, "GetAsyncKeyState", return_value=0
                ), patch.object(
                    bot,
                    "control_menu_hotkey_down",
                    side_effect=[False, True, False],
                ), patch.object(
                    bot, "show_control_menu", return_value="follow"
                ), patch.object(
                    bot,
                    "prompt_follow_player_name",
                    return_value="Player follow-id",
                ), patch.object(
                    bot,
                    "load_memory_snapshot",
                    side_effect=[snapshot, snapshot, unavailable],
                ), patch.object(
                    bot, "request_path_matches", return_value=True
                ), patch.object(
                    bot, "write_navigation_request"
                ) as write_request, patch.object(
                    bot, "post_key"
                ) as post_key, patch.object(bot.time, "sleep"):
                    bot.run_bot(
                        123,
                        BotConfig(debug_window=False, pricing_enabled=False),
                        True,
                    )

                shift_states = [
                    set(call.kwargs.get("shift_keys", ()))
                    for call in write_request.call_args_list
                ]
                self.assertIn({"lshift", "rshift"}, shift_states)
                self.assertEqual(shift_states[-1], set())
                self.assertFalse(
                    any(
                        call.args[1] in bot.HELD_SHIFT_KEYS and call.args[2]
                        for call in post_key.call_args_list
                    )
                )

    def test_name_match_includes_living_player_outside_visible_range(self) -> None:
        hidden = observed_player(1, "hidden", 0, 0, visible=False)
        named = observed_player(2, "chosen", 1, 0)
        self.assertEqual(
            find_follow_player_by_name((hidden, named), "PLAYER CHOSEN").player_id,  # type: ignore[union-attr]
            "chosen",
        )
        self.assertIsNone(
            find_follow_player_by_name((named,), "Player")
        )
        self.assertIs(
            find_follow_player_by_name((hidden,), "Player hidden"), hidden
        )
        self.assertIsNone(
            find_follow_player_by_name(
                (observed_player(3, "dead", 0, 0, alive=False),),
                "Player dead",
            )
        )

    def test_player_id_rebinds_when_object_id_changes(self) -> None:
        rebound = find_follow_player(
            (
                observed_player(99, "same-player", 3, 4),
                observed_player(100, "other", 2, 2),
            ),
            "same-player",
        )
        self.assertEqual(rebound.object_id, 99)  # type: ignore[union-attr]
        hidden_rebound = observed_player(
            102, "same-player", 5, 6, visible=False
        )
        self.assertIs(
            find_follow_player((hidden_rebound,), "same-player"),
            hidden_rebound,
        )
        self.assertIsNone(
            find_follow_player(
                (observed_player(101, "same-player", 0, 0, alive=False),),
                "same-player",
            )
        )

    def test_monster_radius_includes_15_and_excludes_above_15(self) -> None:
        followed = observed_player(50, "follow", 0, 0)
        inside = monster(1, 15.0, 0)
        outside = monster(2, 15.0001, 0)
        target, _ = select_follow_memory_target(
            (outside, inside),
            followed,
            None,
            {},
            now=1.0,
            radius_world=15.0,
        )
        self.assertEqual(target.object_id, 1)  # type: ignore[union-attr]
        target, _ = select_follow_memory_target(
            (inside, outside),
            followed,
            2,
            {},
            now=1.0,
            radius_world=15.0,
        )
        self.assertEqual(target.object_id, 1)  # type: ignore[union-attr]

    def test_rejoin_hysteresis_enters_above_10_and_exits_at_stop_radius(self) -> None:
        self.assertFalse(
            update_follow_rejoin_state(
                False,
                distance_world=10.0,
                stop_distance_world=3.0,
                rejoin_distance_world=10.0,
            )
        )
        self.assertTrue(
            update_follow_rejoin_state(
                False,
                distance_world=10.001,
                stop_distance_world=3.0,
                rejoin_distance_world=10.0,
            )
        )
        self.assertTrue(
            update_follow_rejoin_state(
                True,
                distance_world=3.001,
                stop_distance_world=3.0,
                rejoin_distance_world=10.0,
            )
        )
        self.assertFalse(
            update_follow_rejoin_state(
                True,
                distance_world=3.0,
                stop_distance_world=3.0,
                rejoin_distance_world=10.0,
            )
        )

    def test_follow_stop_distance_uses_both_colliders_and_padding(self) -> None:
        local = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        followed = observed_player(50, "follow", 0, 0)
        self.assertAlmostEqual(
            follow_stop_distance_world(local, followed, 2.0), 2.9
        )

    def test_player_path_requires_matching_kind_and_identity(self) -> None:
        path = MemoryPath(
            12,
            701,
            "complete",
            ((0, 0, 0), (2, 0, 0)),
            target_kind="player",
        )
        self.assertTrue(
            request_path_matches(path, 12, 701, target_kind="player")
        )
        self.assertFalse(request_path_matches(path, 12, 701))
        self.assertFalse(
            request_path_matches(path, 12, 702, target_kind="player")
        )


class CombatWatchdogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = BotConfig(
            combat_health_progress_epsilon=0.001,
            combat_no_progress_sec=6.0,
            combat_reengage_back_ms=450,
            combat_reengage_side_ms=650,
            combat_blacklist_absence_reset_sec=5.0,
        )
        self.state = CombatWatchdogState()

    def observe(
        self,
        health: float,
        now: float,
        *,
        arrived: bool = True,
        enabled: bool = True,
    ) -> str:
        return update_combat_watchdog(
            self.state,
            monster(1, 1, 0, health=health),
            arrived=arrived,
            now=now,
            enabled=enabled,
            config=self.config,
        )

    def test_health_reaching_new_low_resets_no_progress_timer(self) -> None:
        self.assertEqual(self.observe(1.0, 0.0), "attack")
        self.assertEqual(self.observe(0.9, 5.0), "progress")
        self.assertEqual(self.observe(0.9, 10.9), "attack")
        self.assertFalse(self.state.reengage_attempted)

    def test_stalled_target_reengages_once_then_blocks(self) -> None:
        self.assertEqual(self.observe(1.0, 0.0), "attack")
        self.assertEqual(self.observe(1.0, 6.0), "stalled")
        self.assertEqual(combat_reengage_keys(0, "a", self.config), ("s",))
        self.assertEqual(combat_reengage_keys(500, "a", self.config), ("a",))
        self.assertIsNone(combat_reengage_keys(1100, "a", self.config))
        finish_combat_reengage(self.state, 7.1)
        self.assertEqual(self.observe(1.0, 7.2), "attack")
        self.assertEqual(self.observe(1.0, 13.3), "block")

    def test_healing_and_fluctuation_without_new_low_do_not_count(self) -> None:
        reset_combat_watchdog(self.state, monster(1, 1, 0, health=0.8), 0.0)
        self.assertEqual(self.observe(0.8, 0.0), "attack")
        self.assertEqual(self.observe(0.9, 2.0), "attack")
        self.assertEqual(self.observe(0.81, 6.1), "stalled")
        self.assertAlmostEqual(self.state.best_health_ratio, 0.8)

    def test_progress_after_reengage_allows_a_future_reengage(self) -> None:
        self.assertEqual(self.observe(1.0, 0.0), "attack")
        self.assertEqual(self.observe(1.0, 6.0), "stalled")
        finish_combat_reengage(self.state, 7.1)
        self.assertEqual(self.observe(1.0, 7.2), "attack")
        self.assertEqual(self.observe(0.8, 10.0), "progress")
        self.assertFalse(self.state.reengage_attempted)
        self.assertEqual(self.observe(0.8, 16.1), "stalled")

    def test_preview_and_pause_never_trigger_reengage_or_block(self) -> None:
        self.assertEqual(self.observe(1.0, 0.0, enabled=False), "preview")
        self.assertEqual(self.observe(1.0, 100.0, enabled=False), "preview")
        self.assertIsNone(self.state.reposition_started_at)
        self.assertFalse(self.state.reengage_attempted)
        self.assertEqual(self.observe(1.0, 101.0), "attack")
        pause_combat_watchdog(self.state, 106.9)
        self.assertEqual(self.observe(1.0, 200.0), "attack")

    def test_blacklist_resets_only_after_continuous_absence(self) -> None:
        blocked = {1}
        absent_since: dict[int, float] = {}
        refresh_combat_blacklist(
            blocked, absent_since, set(), now=0.0, absence_reset_sec=5.0
        )
        refresh_combat_blacklist(
            blocked, absent_since, set(), now=4.9, absence_reset_sec=5.0
        )
        self.assertEqual(blocked, {1})
        refresh_combat_blacklist(
            blocked, absent_since, {1}, now=5.0, absence_reset_sec=5.0
        )
        self.assertEqual(absent_since, {})
        refresh_combat_blacklist(
            blocked, absent_since, set(), now=6.0, absence_reset_sec=5.0
        )
        refresh_combat_blacklist(
            blocked, absent_since, set(), now=11.1, absence_reset_sec=5.0
        )
        self.assertEqual(blocked, set())


class MovementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = BotConfig(axis_deadzone_ratio=0.28)
        self.player = MemoryPlayer(
            position=(0.0, 0.0, 0.0),
            camera_forward_xz=(0.0, 1.0),
            camera_right_xz=(1.0, 0.0),
            collider_radius=0.4,
        )

    def test_world_directions_project_to_all_wasd_combinations(self) -> None:
        expected = {
            (0, 1): ("w",),
            (0, -1): ("s",),
            (1, 0): ("d",),
            (-1, 0): ("a",),
            (1, 1): ("w", "d"),
            (-1, 1): ("w", "a"),
            (1, -1): ("s", "d"),
            (-1, -1): ("s", "a"),
        }
        for (x, z), keys in expected.items():
            with self.subTest(x=x, z=z):
                self.assertEqual(
                    movement_keys_for_world_waypoint(
                        self.player, (float(x), 0.0, float(z)), self.config
                    ),
                    keys,
                )

    def test_camera_rotation_changes_key_projection(self) -> None:
        east_facing = MemoryPlayer((0, 0, 0), (1, 0), (0, -1), 0.4)
        self.assertEqual(
            movement_keys_for_world_waypoint(east_facing, (10, 0, 0), self.config),
            ("w",),
        )
        self.assertEqual(
            movement_keys_for_world_waypoint(east_facing, (0, 0, 10), self.config),
            ("a",),
        )

    def test_camera_relative_keys_convert_to_world_vector3int(self) -> None:
        east_facing = MemoryPlayer((0, 0, 0), (1, 0), (0, -1), 0.4)
        self.assertEqual(movement_world_for_keys(("w",), east_facing), (1, 0, 0))
        self.assertEqual(movement_world_for_keys(("a",), east_facing), (0, 0, 1))
        self.assertEqual(
            movement_world_for_keys(("s", "a"), east_facing), (-1, 0, 1)
        )
        self.assertEqual(movement_world_for_keys(("w",), None), (0, 0, 0))

    def test_continuous_key_transitions_only_change_differences(self) -> None:
        held = {"w", "lshift", "rshift"}
        desired = {"w", "d", "lshift", "rshift"}
        releases, presses = key_transitions(held, desired)
        self.assertEqual(releases, ())
        self.assertEqual(presses, ("d",))
        releases, presses = key_transitions(desired, ())
        self.assertEqual(releases, ("rshift", "lshift", "d", "w"))
        self.assertEqual(presses, ())

    def test_f8_shift_keys_are_selected_by_job_type(self) -> None:
        self.assertEqual(bot.f8_shift_keys(BotConfig(job_type=0)), ("lshift",))
        self.assertEqual(
            bot.f8_shift_keys(BotConfig(job_type=1)),
            ("lshift", "rshift"),
        )
        self.assertEqual(bot.f8_shift_keys(BotConfig(job_type=2)), ())

    def test_priest_shift_tap_uses_configured_random_interval(self) -> None:
        config = BotConfig(
            priest_left_shift_tap_min_interval_ms=300,
            priest_left_shift_tap_max_interval_ms=1300,
        )
        with patch.object(bot.random, "uniform", return_value=800) as uniform:
            self.assertAlmostEqual(bot.next_priest_shift_tap_at(10.0, config), 10.8)
        uniform.assert_called_once_with(300, 1300)

    def test_unstuck_sequence_is_bounded_and_finishes(self) -> None:
        config = BotConfig(
            unstuck_back_ms=100,
            unstuck_back_diagonal_ms=100,
            unstuck_side_ms=100,
            unstuck_diagonal_ms=100,
            unstuck_return_ms=100,
            unstuck_forward_ms=100,
        )
        self.assertEqual(unstuck_keys(0, "a", config), ("s",))
        self.assertEqual(unstuck_keys(150, "a", config), ("s", "a"))
        self.assertEqual(unstuck_keys(250, "a", config), ("a",))
        self.assertEqual(unstuck_keys(350, "a", config), ("w", "a"))
        self.assertEqual(unstuck_keys(450, "a", config), ("w", "d"))
        self.assertEqual(unstuck_keys(550, "a", config), ("w",))
        self.assertIsNone(unstuck_keys(650, "a", config))


class LootTests(unittest.TestCase):
    def test_mode2_far_legendary_requests_loot_path_then_presses_v_in_range(self) -> None:
        config = BotConfig(
            debug_window=False,
            pricing_enabled=False,
            loop_delay_ms=0,
            memory_loot_min_rarity="Legendary",
            memory_loot_confirm_frames=2,
        )
        player_far = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        # Distance 1.5 to the loot at x=10: inside the collider-independent
        # pickup radius (interaction_range 1.0 + padding 0.75 = 1.75).
        player_near = MemoryPlayer((8.5, 0, 0), (0, 1), (1, 0), 0.45)
        legendary = loot(
            99,
            10,
            0,
            rarity="Legendary",
            rarity_value=3,
            interaction_range=1.0,
        )
        enemy = monster(7, 5, 0)

        def snapshot(player: MemoryPlayer, path: MemoryPath) -> MemorySnapshot:
            return MemorySnapshot(
                timestamp_ms=NOW_MS,
                map_id=1,
                instance_id=1,
                player=player,
                monsters=(enemy,),
                path=path,
                loots=(legendary,),
                loot_scan={"ownership_filter": "all"},
            )

        snapshots = (
            snapshot(player_far, MemoryPath(0, 0, "missing", (), "none")),
            snapshot(player_far, MemoryPath(0, 0, "missing", (), "none")),
            snapshot(
                player_far,
                MemoryPath(
                    1,
                    99,
                    "complete",
                    ((0, 0, 0), (5, 0, 0), (10, 0, 0)),
                    "loot",
                ),
            ),
            snapshot(player_near, MemoryPath(1, 99, "complete", ((8.5, 0, 0),), "loot")),
        )
        with tempfile.TemporaryDirectory() as directory, patch.object(
            bot.win32gui,
            "IsWindow",
            side_effect=[True, True, True, True, False],
        ), patch.object(
            bot.win32api,
            "GetAsyncKeyState",
            return_value=0,
        ), patch.object(
            bot,
            "load_memory_snapshot",
            side_effect=snapshots,
        ), patch.object(
            bot,
            "write_navigation_request",
        ) as write_request, patch.object(
            bot,
            "update_held_keys",
            side_effect=lambda hwnd, held, desired: set(desired),
        ), patch.object(
            bot,
            "post_key_tap",
        ) as tap, patch.object(
            bot,
            "post_key",
        ), patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                config,
                True,
                mode=2,
                request_path=Path(directory) / "request.json",
            )

        self.assertTrue(
            any(
                call.args[2] == 99 and call.kwargs.get("target_kind") == "loot"
                for call in write_request.call_args_list
            )
        )
        # Pickup is routed through the probe (loot_interact intent), not a
        # background PostMessage tap.
        tap.assert_not_called()
        loot_pickups = [
            (
                call.kwargs.get("loot_interact", 0),
                call.kwargs.get("loot_interact_object_id", 0),
            )
            for call in write_request.call_args_list
        ]
        self.assertEqual(max(seq for seq, _ in loot_pickups), 1)
        self.assertIn((1, 99), loot_pickups)

    def test_preview_and_no_loot_never_press_v(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        legendary = loot(
            99,
            1,
            0,
            rarity="Legendary",
            rarity_value=3,
            interaction_range=1.0,
        )
        snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=player,
            monsters=(monster(7, 5, 0),),
            path=MemoryPath(0, 0, "missing", (), "none"),
            loots=(legendary,),
            loot_scan={"ownership_filter": "all"},
        )
        scenarios = (
            ("preview", False, False),
            ("no-loot", True, True),
        )
        for name, send_input, disable_loot in scenarios:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory, patch.object(
                bot.win32gui,
                "IsWindow",
                side_effect=[True, True, False],
            ), patch.object(
                bot.win32api,
                "GetAsyncKeyState",
                return_value=0,
            ), patch.object(
                bot,
                "load_memory_snapshot",
                side_effect=[snapshot, snapshot],
            ), patch.object(
                bot,
                "write_navigation_request",
            ), patch.object(
                bot,
                "update_held_keys",
                side_effect=lambda hwnd, held, desired: set(desired),
            ), patch.object(
                bot,
                "post_key_tap",
            ) as tap, patch.object(
                bot,
                "post_key",
            ), patch.object(bot.time, "sleep"):
                bot.run_bot(
                    123,
                    BotConfig(
                        debug_window=False,
                        pricing_enabled=False,
                        loop_delay_ms=0,
                        memory_loot_confirm_frames=2,
                    ),
                    send_input,
                    mode=2,
                    request_path=Path(directory) / "request.json",
                    disable_loot=disable_loot,
                )

            tap.assert_not_called()

    def test_in_range_loot_retries_v_while_object_still_exists(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        legendary = loot(
            99,
            1,
            0,
            rarity="Legendary",
            rarity_value=3,
            interaction_range=1.0,
        )
        snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=1,
            player=player,
            monsters=(monster(7, 5, 0),),
            path=MemoryPath(0, 0, "missing", (), "none"),
            loots=(legendary,),
            loot_scan={"ownership_filter": "all"},
        )
        config = BotConfig(
            debug_window=False,
            pricing_enabled=False,
            loop_delay_ms=0,
            memory_loot_confirm_frames=1,
            memory_loot_interact_cooldown_ms=0,
        )
        with tempfile.TemporaryDirectory() as directory, patch.object(
            bot.win32gui,
            "IsWindow",
            side_effect=[True, True, True, False],
        ), patch.object(
            bot.win32api,
            "GetAsyncKeyState",
            return_value=0,
        ), patch.object(
            bot,
            "load_memory_snapshot",
            side_effect=[snapshot, snapshot, snapshot],
        ), patch.object(
            bot,
            "write_navigation_request",
        ) as write_request, patch.object(
            bot,
            "update_held_keys",
            side_effect=lambda hwnd, held, desired: set(desired),
        ), patch.object(
            bot,
            "post_key_tap",
        ) as tap, patch.object(
            bot,
            "post_key",
        ), patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                config,
                True,
                mode=2,
                request_path=Path(directory) / "request.json",
            )

        # Each retry bumps the probe loot_interact counter rather than sending a
        # background PostMessage V tap.
        tap.assert_not_called()
        loot_seqs = [
            call.kwargs.get("loot_interact", 0)
            for call in write_request.call_args_list
        ]
        self.assertEqual(max(loot_seqs), 3)
        self.assertTrue(
            all(
                call.kwargs.get("loot_interact_object_id", 0) == 99
                for call in write_request.call_args_list
                if call.kwargs.get("loot_interact", 0) > 0
            )
        )
        self.assertEqual(BotConfig().memory_loot_interact_cooldown_ms, 500)

    def test_mode2_foreign_legendary_is_ignored_far_and_v_only_in_range(self) -> None:
        config = BotConfig(
            debug_window=False,
            pricing_enabled=False,
            loop_delay_ms=0,
            memory_loot_min_rarity="Legendary",
            memory_loot_confirm_frames=2,
        )
        player_far = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        # Distance 1.5 to the loot at x=10: inside the collider-independent
        # pickup radius (interaction_range 1.0 + padding 0.75 = 1.75).
        player_near = MemoryPlayer((8.5, 0, 0), (0, 1), (1, 0), 0.45)
        foreign = loot(
            99,
            10,
            0,
            rarity="Legendary",
            rarity_value=3,
            owned=False,
            interaction_range=1.0,
        )
        enemy = monster(7, 5, 0)

        def snapshot(player: MemoryPlayer) -> MemorySnapshot:
            return MemorySnapshot(
                timestamp_ms=NOW_MS,
                map_id=1,
                instance_id=1,
                player=player,
                monsters=(enemy,),
                path=MemoryPath(0, 0, "missing", (), "none"),
                loots=(foreign,),
                loot_scan={"ownership_filter": "all"},
            )

        snapshots = (
            snapshot(player_far),
            snapshot(player_far),
            snapshot(player_near),
            snapshot(player_near),
        )
        with tempfile.TemporaryDirectory() as directory, patch.object(
            bot.win32gui,
            "IsWindow",
            side_effect=[True, True, True, True, False],
        ), patch.object(
            bot.win32api,
            "GetAsyncKeyState",
            return_value=0,
        ), patch.object(
            bot,
            "load_memory_snapshot",
            side_effect=snapshots,
        ), patch.object(
            bot,
            "write_navigation_request",
        ) as write_request, patch.object(
            bot,
            "update_held_keys",
            side_effect=lambda hwnd, held, desired: set(desired),
        ), patch.object(
            bot,
            "post_key_tap",
        ) as tap, patch.object(
            bot,
            "post_key",
        ), patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                config,
                True,
                mode=2,
                request_path=Path(directory) / "request.json",
            )

        self.assertFalse(
            any(
                call.args[2] == 99 and call.kwargs.get("target_kind") == "loot"
                for call in write_request.call_args_list
            )
        )
        # Foreign loot is never navigated to, but is picked up once in range via
        # the probe loot_interact intent (carrying its object id independently of
        # the nav target).
        tap.assert_not_called()
        loot_pickups = [
            (
                call.kwargs.get("loot_interact", 0),
                call.kwargs.get("loot_interact_object_id", 0),
            )
            for call in write_request.call_args_list
        ]
        self.assertEqual(max(seq for seq, _ in loot_pickups), 1)
        self.assertIn((1, 99), loot_pickups)

    def test_post_key_tap_sends_down_wait_then_up(self) -> None:
        events: list[tuple[object, ...]] = []

        def record_key(hwnd: int, key: str, is_down: bool) -> None:
            events.append(("key", hwnd, key, is_down))

        def record_sleep(seconds: float) -> None:
            events.append(("sleep", seconds))

        with patch.object(bot, "post_key", side_effect=record_key), patch.object(
            bot.time, "sleep", side_effect=record_sleep
        ):
            post_key_tap(123, "v", 50)

        self.assertEqual(
            events,
            [("key", 123, "v", True), ("sleep", 0.05), ("key", 123, "v", False)],
        )

    def test_post_key_tap_releases_v_when_wait_raises(self) -> None:
        events: list[tuple[int, str, bool]] = []

        with patch.object(
            bot,
            "post_key",
            side_effect=lambda hwnd, key, is_down: events.append(
                (hwnd, key, is_down)
            ),
        ), patch.object(bot.time, "sleep", side_effect=RuntimeError("wait failed")):
            with self.assertRaisesRegex(RuntimeError, "wait failed"):
                post_key_tap(123, "v", 50)

        self.assertEqual(events, [(123, "v", True), (123, "v", False)])

    def test_in_range_selection_prefers_nearest_and_keeps_lock(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        nearby_unique = loot(10, 2, 0)
        far_legendary = loot(20, 2.5, 0, rarity="Legendary", rarity_value=3)
        selected = select_memory_loot(
            (nearby_unique, far_legendary), player, "Unique"
        )
        self.assertEqual(selected.object_id, 10)  # type: ignore[union-attr]
        selected = select_memory_loot(
            (nearby_unique, far_legendary), player, "Unique", 10
        )
        self.assertEqual(selected.object_id, 10)  # type: ignore[union-attr]

    def test_filters_below_threshold_and_locked_loot(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        common = loot(1, 1, 0, rarity="Common", rarity_value=0)
        rare = loot(2, 2, 0, rarity="Rare", rarity_value=1)
        unique = loot(3, 3, 0, rarity="Unique", rarity_value=2)
        locked = loot(4, 4, 0, rarity="Legendary", rarity_value=3, locked=True)
        self.assertIsNone(
            select_memory_loot((common, rare, unique, locked), player, "Legendary")
        )

    def test_equipment_is_excluded_even_when_owned_and_legendary(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        local_legendary_equipment = loot(
            51,
            1,
            0,
            rarity="Legendary",
            rarity_value=3,
            loot_type="Equip",
        )
        nearby_legendary_material = loot(
            52,
            2,
            0,
            rarity="Legendary",
            rarity_value=3,
        )
        selected = select_memory_loot(
            (local_legendary_equipment, nearby_legendary_material),
            player,
            "Legendary",
        )
        self.assertEqual(selected.object_id, 52)  # type: ignore[union-attr]
        self.assertIsNone(
            select_memory_loot(
                (local_legendary_equipment,),
                player,
                "Legendary",
            )
        )

    def test_foreign_and_public_loot_are_preserved_in_snapshot(self) -> None:
        raw = valid_raw_state()
        own = dict(raw["loots"][0])  # type: ignore[index]
        foreign = dict(own)
        foreign["object_id"] = 502
        foreign["owner_player_id"] = "other-player"
        foreign["owned_by_local_player"] = False
        public = dict(own)
        public["object_id"] = 503
        public["owner_player_id"] = ""
        public["owned_by_local_player"] = False
        raw["loots"] = [own, foreign, public]
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertEqual(
            [item.object_id for item in snapshot.loots],
            [501, 502, 503],
        )
        self.assertEqual(
            [item.owned_by_local_player for item in snapshot.loots],
            [True, False, False],
        )
        self.assertEqual(
            [bot.loot_ownership_label(item) for item in snapshot.loots],
            ["OWN", "FOREIGN", "PUBLIC"],
        )

    def test_foreign_legendary_requires_unlock_and_pickup_range(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        # Within the collider-independent pickup radius (interaction_range 1.0 +
        # default padding 0.75 = 1.75); collider radius no longer widens it.
        nearby = loot(
            99,
            1.5,
            0,
            rarity="Legendary",
            rarity_value=3,
            owned=False,
            interaction_range=1.0,
        )
        selected = select_memory_loot((nearby,), player, "Legendary")
        self.assertEqual(selected.object_id, 99)  # type: ignore[union-attr]
        self.assertIsNone(
            select_memory_loot(
                (loot(100, 2.0, 0, rarity="Legendary", rarity_value=3, owned=False, locked=True),),
                player,
                "Legendary",
            )
        )
        self.assertIsNone(
            select_memory_loot(
                (loot(101, 12.0, 0, rarity="Legendary", rarity_value=3, owned=False),),
                player,
                "Legendary",
            )
        )
        self.assertIsNone(
            select_memory_loot(
                (loot(102, 1.0, 0, rarity="Unique", rarity_value=2, owned=False),),
                player,
                "Legendary",
            )
        )

    def test_nearby_foreign_legendary_preempts_remote_owned_target(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        remote_owned = loot(20, 12, 0, rarity="Legendary", rarity_value=3)
        nearby_foreign = loot(
            30,
            1.5,
            0,
            rarity="Legendary",
            rarity_value=3,
            owned=False,
            interaction_range=1.0,
        )
        selected = select_memory_loot(
            (remote_owned, nearby_foreign),
            player,
            "Legendary",
            previous_object_id=20,
        )
        self.assertEqual(selected.object_id, 30)  # type: ignore[union-attr]

    def test_far_unlocked_legendary_is_selected_for_active_chase(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        far_legendary = loot(
            99,
            12.0,
            0,
            rarity="Legendary",
            rarity_value=3,
            locked=False,
            interaction_range=1.0,
        )
        self.assertEqual(
            select_memory_loot((far_legendary,), player, "Legendary").object_id,  # type: ignore[union-attr]
            99,
        )

    def test_legendary_selection_keeps_lock_and_obeys_retry_cooldown(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.45)
        near = loot(10, 4, 0, rarity="Legendary", rarity_value=3)
        far = loot(20, 12, 0, rarity="Legendary", rarity_value=3)
        selected = select_memory_loot((far, near), player, "Legendary", None, now=5.0)
        self.assertEqual(selected.object_id, 10)  # type: ignore[union-attr]
        selected = select_memory_loot((near, far), player, "Legendary", 20, now=5.0)
        self.assertEqual(selected.object_id, 20)  # type: ignore[union-attr]
        selected = select_memory_loot(
            (near, far),
            player,
            "Legendary",
            20,
            skipped_until={20: 20.0},
            now=5.0,
        )
        self.assertEqual(selected.object_id, 10)  # type: ignore[union-attr]

    def test_loot_chase_failure_policy_covers_path_timeout_and_unstuck(self) -> None:
        state = LootChaseState()
        reset_loot_chase(
            state,
            now=10.0,
            target_object_id=99,
            player_position=(0.0, 0.0, 0.0),
        )
        self.assertIsNone(
            loot_chase_failure_reason(
                state,
                now=29.9,
                path_invalid_grace_sec=1.0,
                chase_timeout_sec=20.0,
                enforce_timeout=True,
            )
        )
        self.assertEqual(
            loot_chase_failure_reason(
                state,
                now=30.0,
                path_invalid_grace_sec=1.0,
                chase_timeout_sec=20.0,
                enforce_timeout=True,
            ),
            "timeout",
        )
        state.path_invalid_since = 40.0
        self.assertEqual(
            loot_chase_failure_reason(
                state,
                now=41.0,
                path_invalid_grace_sec=1.0,
                chase_timeout_sec=20.0,
                enforce_timeout=False,
            ),
            "path",
        )
        self.assertEqual(
            loot_chase_failure_reason(
                state,
                now=40.1,
                path_invalid_grace_sec=1.0,
                chase_timeout_sec=20.0,
                enforce_timeout=False,
                unstuck_failed=True,
            ),
            "unstuck",
        )

    def test_pickup_range_ignores_collider_and_hard_cap(self) -> None:
        # A large collider radius must NOT inflate the pickup radius: the server
        # only credits the loot's InteractionRange against the player centre.
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 2.0)
        within = loot(1, 1.6, 0, interaction_range=1.0)
        beyond = loot(2, 1.9, 0, interaction_range=1.0)
        oversized = loot(3, 3.1, 0, interaction_range=100.0)
        self.assertAlmostEqual(
            loot_pickup_radius(
                player,
                within,
                range_padding_world=0.75,
                max_distance_world=3.0,
            ),
            1.75,
        )
        self.assertTrue(
            loot_is_within_pickup_range(
                player,
                within,
                range_padding_world=0.75,
                max_distance_world=3.0,
            )
        )
        self.assertFalse(
            loot_is_within_pickup_range(
                player,
                beyond,
                range_padding_world=0.75,
                max_distance_world=3.0,
            )
        )
        self.assertFalse(
            loot_is_within_pickup_range(
                player,
                oversized,
                range_padding_world=0.75,
                max_distance_world=3.0,
            )
        )
        # A negative padding pulls the press point safely inside InteractionRange.
        self.assertAlmostEqual(
            loot_pickup_radius(
                player,
                within,
                range_padding_world=-0.2,
                max_distance_world=3.0,
            ),
            0.8,
        )

    def test_candidate_requires_consecutive_object_id(self) -> None:
        first = loot(10, 2, 0)
        object_id, frames = track_memory_loot_candidate(first, None, 0)
        self.assertEqual((object_id, frames), (10, 1))
        object_id, frames = track_memory_loot_candidate(first, object_id, frames)
        self.assertEqual((object_id, frames), (10, 2))
        object_id, frames = track_memory_loot_candidate(
            loot(11, 3, 0), object_id, frames
        )
        self.assertEqual((object_id, frames), (11, 1))

    def test_malformed_loot_is_ignored_without_invalidating_navigation(self) -> None:
        raw = valid_raw_state()
        raw["loots"] = [raw["loots"][0], {"object_id": 999}]  # type: ignore[index]
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertEqual([item.object_id for item in snapshot.loots], [501])


class PricingIntegrationTests(unittest.TestCase):
    def test_backpack_pricing_is_manual_by_default(self) -> None:
        self.assertFalse(BotConfig().pricing_auto_start)

    def test_startup_does_not_query_or_open_price_window_by_default(self) -> None:
        class FakeController:
            def __init__(self):
                self.start_calls = 0

            def start(self):
                self.start_calls += 1
                return True

            def poll_latest(self):
                return None

            def stop(self):
                return None

        controller = FakeController()
        with patch.object(
            bot, "PricingController", return_value=controller
        ), patch.object(
            bot.win32gui, "IsWindow", side_effect=[True, False]
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "load_memory_snapshot", side_effect=SnapshotUnavailable("offline")
        ), patch.object(
            bot, "write_navigation_request"
        ), patch.object(
            bot, "update_held_keys", side_effect=lambda hwnd, held, desired: set(desired)
        ), patch.object(
            bot, "post_key"
        ), patch.object(
            bot.cv2, "namedWindow"
        ) as named_window, patch.object(bot.time, "sleep"):
            bot.run_bot(123, BotConfig(debug_window=False), True)

        self.assertEqual(controller.start_calls, 0)
        named_window.assert_not_called()

    def test_f6_starts_manual_pricing_without_waiting_for_navigation(self) -> None:
        class FakeController:
            def __init__(self):
                self.start_calls = 0
                self.stop_calls = 0

            def start(self):
                self.start_calls += 1
                return True

            def poll_latest(self):
                return None

            def stop(self):
                self.stop_calls += 1

        controller = FakeController()
        with patch.object(
            bot, "PricingController", return_value=controller
        ), patch.object(
            bot.win32gui, "IsWindow", side_effect=[True, False]
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "control_menu_hotkey_down", side_effect=[False, True]
        ), patch.object(
            bot, "show_control_menu", return_value="reprice"
        ), patch.object(
            bot,
            "load_memory_snapshot",
            side_effect=SnapshotUnavailable("offline"),
        ), patch.object(
            bot, "write_navigation_request"
        ), patch.object(
            bot, "update_held_keys", side_effect=lambda hwnd, held, desired: set(desired)
        ), patch.object(
            bot, "post_key"
        ), patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                BotConfig(
                    debug_window=False,
                    pricing_enabled=True,
                    pricing_auto_start=False,
                    pricing_window_enabled=False,
                ),
                True,
            )

        self.assertEqual(controller.start_calls, 1)
        self.assertEqual(controller.stop_calls, 1)

    def test_controller_runs_in_background_rejects_duplicate_and_cancels(self) -> None:
        entered = threading.Event()

        def runner(*, progress, cancel_check, **_kwargs):
            progress({"phase": "reading_inventory", "message": "reading"})
            entered.set()
            while not cancel_check():
                time.sleep(0.005)
            raise bot.inventory_pricer.PricingCancelled()

        controller = bot.PricingController(
            timeout=1.0,
            request_delay=0.0,
            threshold=50_000,
            runner=runner,
        )
        self.assertTrue(controller.start())
        self.assertTrue(entered.wait(0.5))
        self.assertFalse(controller.start())
        controller.stop(0.5)
        self.assertFalse(controller.running)
        latest = controller.poll_latest()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.phase, "cancelled")  # type: ignore[union-attr]

    def test_controller_converts_completed_report_to_immutable_rows(self) -> None:
        report = {
            "timestamp_ms": NOW_MS,
            "threshold": 50_000,
            "equipment_count": 3,
            "eligible_equipment_count": 2,
            "favorite_skipped_count": 1,
            "priced_count": 2,
            "no_exact_sample_count": 0,
            "over_threshold_count": 2,
            "grouped_items": [
                {
                    "display_name": "心靈手套",
                    "quantity": 2,
                    "stat_text": "Int+3, Matk+2, Matk+2%",
                    "lowest_exact_price": 75_000,
                    "exact_listing_count": 3,
                    "over_threshold": True,
                }
            ],
        }

        def runner(**_kwargs):
            return report

        controller = bot.PricingController(
            timeout=1.0,
            request_delay=0.0,
            threshold=50_000,
            runner=runner,
        )
        self.assertTrue(controller.start())
        deadline = time.monotonic() + 0.5
        while controller.running and time.monotonic() < deadline:
            time.sleep(0.005)
        latest = controller.poll_latest()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.phase, "complete")  # type: ignore[union-attr]
        self.assertEqual(latest.favorite_skipped_count, 1)  # type: ignore[union-attr]
        self.assertEqual(latest.rows[0].quantity, 2)  # type: ignore[union-attr]
        self.assertIn("FAV-SKIP 1", bot.pricing_radar_summary(latest))  # type: ignore[arg-type]

    def test_price_window_renders_unicode_and_clamps_pages(self) -> None:
        rows = tuple(
            bot.PricingDisplayRow(
                display_name=f"心靈手套 {index}",
                quantity=1,
                stat_text="Int+3, Matk+2, Matk+2%",
                lowest_exact_price=50_001 + index,
                exact_listing_count=2,
                over_threshold=True,
            )
            for index in range(10)
        )
        state = bot.PricingViewState(
            phase="complete",
            message="Pricing complete",
            threshold=50_000,
            equipment_count=12,
            eligible_equipment_count=10,
            favorite_skipped_count=2,
            priced_count=10,
            over_threshold_count=10,
            rows=rows,
        )
        canvas, page, page_count = bot.draw_pricing_window(state, 99, 4)
        self.assertEqual(canvas.shape, (760, 760, 3))
        self.assertEqual(page, 2)
        self.assertEqual(page_count, 3)
        self.assertGreater(float(canvas.std()), 1.0)


class EquipmentFilterIntegrationTests(unittest.TestCase):
    def test_delete_toggles_filter_editor_and_controller_lifecycle(self) -> None:
        class FakeFilterController:
            def __init__(self):
                self.start_calls = 0
                self.stop_calls = 0

            def start(self):
                self.start_calls += 1

            def stop(self):
                self.stop_calls += 1

            def request_immediate(self):
                return None

            def poll_latest(self):
                return None

        class FakeEditor:
            def __init__(self):
                self.toggle_calls = 0
                self.stop_calls = 0

            def toggle(self):
                self.toggle_calls += 1

            def stop(self):
                self.stop_calls += 1

            def set_status(self, _message):
                return None

        controller = FakeFilterController()
        editor = FakeEditor()
        with patch.object(
            bot.equipment_filter,
            "EquipmentFilterController",
            return_value=controller,
        ), patch.object(
            bot.equipment_filter,
            "EquipmentFilterEditor",
            return_value=editor,
        ), patch.object(
            bot,
            "control_menu_hotkey_down",
            side_effect=[False, True],
        ), patch.object(
            bot, "show_control_menu", return_value="filter"
        ), patch.object(
            bot.win32gui, "IsWindow", side_effect=[True, False]
        ), patch.object(
            bot.win32api, "GetAsyncKeyState", return_value=0
        ), patch.object(
            bot, "load_memory_snapshot", side_effect=SnapshotUnavailable("offline")
        ), patch.object(
            bot, "write_navigation_request"
        ), patch.object(
            bot, "update_held_keys", side_effect=lambda hwnd, held, desired: set(desired)
        ), patch.object(
            bot, "post_key"
        ), patch.object(bot.time, "sleep"):
            bot.run_bot(
                123,
                BotConfig(debug_window=False, pricing_enabled=False),
                True,
            )

        self.assertEqual(controller.start_calls, 1)
        self.assertEqual(controller.stop_calls, 1)
        self.assertEqual(editor.toggle_calls, 1)
        self.assertEqual(editor.stop_calls, 1)


class RadarAndRemovalTests(unittest.TestCase):
    def test_radar_window_is_disabled_by_default(self) -> None:
        self.assertFalse(BotConfig().debug_window)

    def test_memory_radar_renders_without_game_frame(self) -> None:
        player = MemoryPlayer((0, 0, 0), (0, 1), (1, 0), 0.4)
        target = monster(1, 5, 4)
        snapshot = MemorySnapshot(
            timestamp_ms=NOW_MS,
            map_id=1,
            instance_id=2,
            player=player,
            monsters=(target,),
            path=MemoryPath(1, 1, "complete", ((0, 0, 0), (2, 0, 2), (5, 0, 4))),
            players=(observed_player(70, "follow", 2, 1, selected=True),),
            loots=(loot(50, 3, -2),),
        )
        radar = draw_memory_radar(
            snapshot,
            target,
            ("w", "d"),
            True,
            "FOLLOW",
            BotConfig(radar_size_px=420),
            follow_player=snapshot.players[0],
            follow_radius_world=15.0,
        )
        self.assertEqual(radar.shape, (420, 420, 3))
        self.assertGreater(float(radar.std()), 1.0)

    def test_minimap_navigation_functions_are_removed(self) -> None:
        removed = (
            "detect_red_dots",
            "detect_player_pose",
            "terrain_obstacle_mask",
            "blue_hazard_mask",
            "plan_terrain_waypoint",
            "calibrate_movement_vectors",
            "record_blocked_area",
            "capture_client",
            "detect_purple_loot_beams",
            "detect_green_test_loot_beams",
            "track_stable_loot_candidate",
        )
        for name in removed:
            with self.subTest(name=name):
                self.assertFalse(hasattr(bot, name))


class BossAvoidanceTests(unittest.TestCase):
    def test_parse_monster_level_reads_label(self) -> None:
        self.assertEqual(
            parse_monster_level("Scorpion King <sprite name=fire> Lv.40"), 40
        )
        self.assertEqual(parse_monster_level("Slime Lv. 7"), 7)
        self.assertEqual(parse_monster_level("Nameless"), 0)
        self.assertEqual(parse_monster_level(""), 0)

    def test_detect_boss_is_unique_highest_level(self) -> None:
        monsters = [
            monster(101, 1.0, 0.0, level=33),
            monster(102, 2.0, 0.0, level=35),
            monster(103, 3.0, 0.0, level=40),
        ]
        self.assertEqual(detect_boss_object_id(monsters), 103)

    def test_detect_boss_none_when_top_level_is_tied(self) -> None:
        monsters = [
            monster(101, 1.0, 0.0, level=40),
            monster(102, 2.0, 0.0, level=40),
            monster(103, 3.0, 0.0, level=33),
        ]
        self.assertIsNone(detect_boss_object_id(monsters))

    def test_detect_boss_none_without_levels(self) -> None:
        monsters = [monster(101, 1.0, 0.0), monster(102, 2.0, 0.0)]
        self.assertIsNone(detect_boss_object_id(monsters))

    def test_parse_marks_boss_avoid_only_when_enabled(self) -> None:
        raw = valid_raw_state()
        raw["monsters"] = [
            {
                "object_id": 201,
                "config_id": "Scorpion",
                "display_name": "Scorpion Lv.33",
                "rank": "Normal",
                "position": [11.0, 2.0, 20.0],
                "health_ratio": 1.0,
                "collider_radius": 0.5,
                "team": "enemy",
                "alive": True,
                "visible": True,
                "training_dummy": False,
            },
            {
                "object_id": 202,
                "config_id": "Scorpion King",
                "display_name": "Scorpion King <sprite name=fire> Lv.40",
                "rank": "Normal",
                "position": [12.0, 2.0, 20.0],
                "health_ratio": 1.0,
                "collider_radius": 0.5,
                "team": "enemy",
                "alive": True,
                "visible": True,
                "training_dummy": False,
            },
        ]

        default = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertEqual({m.object_id: m.level for m in default.monsters},
                         {201: 33, 202: 40})
        self.assertFalse(any(m.avoid for m in default.monsters))

        avoiding = parse_memory_snapshot(
            raw, now_ms=NOW_MS, max_age_ms=750, avoid_boss=True
        )
        by_id = {m.object_id: m for m in avoiding.monsters}
        self.assertTrue(by_id[202].avoid)
        self.assertFalse(by_id[201].avoid)

    def test_avoid_boss_is_excluded_from_targeting(self) -> None:
        monsters = [
            monster(202, 1.0, 0.0, level=40, avoid=True),
            monster(201, 9.0, 0.0, level=33),
        ]
        target, _ = select_memory_target(
            monsters, (0.0, 0.0, 0.0), None, {}, now=0.0
        )
        # The nearer monster is the boss, but avoidance skips it for the farther
        # attackable enemy.
        self.assertIsNotNone(target)
        self.assertEqual(target.object_id, 201)

    def test_parse_reads_channel_fields(self) -> None:
        raw = valid_raw_state()
        raw["channel_index"] = 0
        raw["channel_count"] = 10
        snapshot = parse_memory_snapshot(raw, now_ms=NOW_MS, max_age_ms=750)
        self.assertEqual(snapshot.channel_index, 0)
        self.assertEqual(snapshot.channel_count, 10)

    def test_parse_channel_fields_default_when_absent(self) -> None:
        snapshot = parse_memory_snapshot(
            valid_raw_state(), now_ms=NOW_MS, max_age_ms=750
        )
        self.assertEqual(snapshot.channel_index, -1)
        self.assertEqual(snapshot.channel_count, 0)

    def test_navigation_request_includes_channel_switch_when_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            write_navigation_request(
                path,
                7,
                0,
                target_kind="none",
                now_ms=NOW_MS,
                bot_active=True,
                channel_switch_request_id=999,
                channel_switch_index=3,
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["channel_switch_request_id"], 999)
        self.assertEqual(payload["channel_switch_index"], 3)

    def test_navigation_request_omits_channel_switch_when_index_negative(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            write_navigation_request(
                path,
                7,
                0,
                target_kind="none",
                now_ms=NOW_MS,
                channel_switch_request_id=999,
                channel_switch_index=-1,
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertNotIn("channel_switch_request_id", payload)
        self.assertNotIn("channel_switch_index", payload)

    def test_config_rejects_invalid_boss_response(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps({"boss_response": "teleport"}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "boss_response"):
                bot.load_config(path)

    def test_config_accepts_switch_channel_response(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "boss_response": "switch_channel",
                        "boss_channel_switch_settle_sec": 4.0,
                    }
                ),
                encoding="utf-8",
            )
            config = bot.load_config(path)
        self.assertEqual(config.boss_response, "switch_channel")
        self.assertEqual(config.boss_channel_switch_settle_sec, 4.0)


class BossFarmTests(unittest.TestCase):
    def test_boss_name_normalization_strips_rich_text_and_level(self) -> None:
        self.assertEqual(
            normalize_boss_name("Scorpion King <sprite name=fire> Lv.40"),
            "scorpion king",
        )
        candidate = bot.replace(
            monster(301, 4.0, 0.0),
            config_id="scorpion-king",
            display_name="Scorpion King <sprite name=fire> Lv.40",
        )
        self.assertTrue(monster_matches_boss(candidate, "Scorpion King"))
        self.assertFalse(monster_matches_boss(candidate, "Termite King"))

    def test_boss_selector_ignores_other_monsters_and_sticks_to_object_id(self) -> None:
        normal = bot.replace(
            monster(300, 1.0, 0.0), display_name="Scorpion Lv.35"
        )
        near = bot.replace(
            monster(301, 3.0, 0.0), display_name="Scorpion King Lv.40"
        )
        far = bot.replace(
            monster(302, 8.0, 0.0), config_id="Scorpion King"
        )
        self.assertEqual(
            select_boss_farm_target(
                (normal, far, near), (0.0, 0.0, 0.0), "Scorpion King"
            ).object_id,
            301,
        )
        self.assertEqual(
            select_boss_farm_target(
                (normal, far, near),
                (0.0, 0.0, 0.0),
                "Scorpion King",
                previous_object_id=302,
            ).object_id,
            302,
        )

    def test_boss_loot_selector_accepts_only_own_legendary_and_sticks(self) -> None:
        own_unique = loot(401, 1.0, 0.0)
        foreign_legendary = loot(
            402, 2.0, 0.0, rarity="Legendary", rarity_value=3, owned=False
        )
        own_near = loot(
            403, 3.0, 0.0, rarity="Legendary", rarity_value=3
        )
        own_far = loot(
            404, 8.0, 0.0, rarity="Legendary", rarity_value=3
        )
        self.assertEqual(
            select_boss_legendary_loot(
                (own_unique, foreign_legendary, own_far, own_near),
                (0.0, 0.0, 0.0),
            ).object_id,
            403,
        )
        self.assertEqual(
            select_boss_legendary_loot(
                (own_unique, foreign_legendary, own_far, own_near),
                (0.0, 0.0, 0.0),
                previous_object_id=404,
            ).object_id,
            404,
        )


if __name__ == "__main__":
    unittest.main()
