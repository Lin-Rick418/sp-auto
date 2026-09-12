"""Exercise upkeep priority through the real bot loop and captured probe IPC."""

from contextlib import ExitStack
from dataclasses import replace
import unittest
from unittest.mock import patch

import spiritvale_red_dot_bot as bot
from test_spiritvale_red_dot_bot import monster, party_member


class UpkeepPriorityTests(unittest.TestCase):
    def snapshot(self, *, summons=(), buffs=(), available=True, instance_id=1):
        enemy = monster(101, 10, 0, viewport=(0.5, 0.5, 1), viewport_visible=True)
        return bot.MemorySnapshot(
            timestamp_ms=1_800_000_000_000,
            map_id=1,
            instance_id=instance_id,
            player=bot.MemoryPlayer(
                (0, 0, 0), (0, 1), (1, 0), 0.4,
                summon_displays_available=available,
                summon_display_skill_ids=summons,
                active_statuses_available=available,
                active_status_ids=buffs,
                is_mounted_summon=True,
                mounted_summon_state_available=True,
                summon_mount_action_available=True,
            ),
            monsters=(enemy,),
            path=bot.MemoryPath(
                1, 101, "complete", ((0, 0, 0), (10, 0, 0))
            ),
        )

    def run_snapshots(self, snapshots, *, mode=1, follow=False):
        config = bot.BotConfig(
            debug_window=False, pricing_enabled=False, job_type=1,
            start_paused=follow, loop_delay_ms=0,
            summoner_check_settle_ms=0, summoner_check_retry_delay_ms=100_000,
        )
        config.summoner_checks["SummonSkeleton"] = {
            "enabled": True, "key": "numpad5"
        }
        config.summoner_checks["Conjurer"] = {
            "enabled": True, "key": "numpad2"
        }
        frame = -1
        requests = []
        key_updates = []

        def read_snapshot(*_args, **_kwargs):
            nonlocal frame
            frame += 1
            return snapshots[frame]

        def write_request(*args, **kwargs):
            requests.append((frame, args[2], kwargs))

        def update_keys(_hwnd, _held, desired):
            keys = set(desired)
            key_updates.append((frame, keys))
            return keys

        with ExitStack() as stack:
            for owner, name, kwargs in (
                (bot.win32gui, "IsWindow", {"side_effect": [True] * len(snapshots) + [False]}),
                (bot.win32api, "GetAsyncKeyState", {"return_value": 0}),
                (bot, "control_menu_hotkey_down", {
                    "side_effect": [False, follow] + [False] * (len(snapshots) - 1)
                }),
                (bot, "show_control_menu", {"return_value": "follow"}),
                (bot, "wait_for_party_snapshot", {"return_value": snapshots[0]}),
                (bot, "prompt_follow_player_name", {"return_value": "Player follow-id"}),
                (bot, "load_memory_snapshot", {"side_effect": read_snapshot}),
                (bot, "write_navigation_request", {"side_effect": write_request}),
                (bot, "update_held_keys", {"side_effect": update_keys}),
                (bot, "request_path_matches", {"return_value": True}),
                (bot, "move_mouse_to_monster", {"return_value": True}),
                (bot, "post_key", {}),
                (bot, "post_key_tap", {}),
                (bot.time, "sleep", {}),
            ):
                stack.enter_context(patch.object(owner, name, **kwargs))
            bot.run_bot(
                123, config, True, mode=mode, disable_loot=True,
                lock_mouse_to_monster=True,
            )
        return requests, key_updates

    def assert_blocked(self, requests, key_updates, frames):
        blocked = [(target, data) for frame, target, data in requests if frame in frames]
        self.assertTrue(blocked)
        for target, data in blocked:
            self.assertEqual(target, 0)
            self.assertFalse(data["movement_keys"])
            self.assertFalse(data["shift_keys"])
            self.assertEqual(data["focus_target_object_id"], 0)
        self.assertTrue(all(not keys for frame, keys in key_updates if frame in frames))

    def assert_attacking(self, requests, frame):
        self.assertTrue(any(
            index == frame and target == 101
            and set(data["shift_keys"]) == {"lshift", "rshift"}
            and data["focus_target_object_id"] == 101
            for index, target, data in requests
        ))

    def test_startup_confirms_every_summon_and_buff_before_navigation(self):
        for mode in (1, 2):
            with self.subTest(mode=mode):
                requests, keys = self.run_snapshots([
                    self.snapshot(),
                    self.snapshot(summons=("SummonSkeleton",)),
                    self.snapshot(summons=("SummonSkeleton",)),
                    self.snapshot(summons=("SummonSkeleton",), buffs=("Conjurer",)),
                ], mode=mode)
                self.assert_blocked(requests, keys, {-1, 0, 1, 2})
                self.assertTrue(any(f == 0 and d["skill_key"] == "numpad5" for f, _, d in requests))
                self.assertTrue(any(f == 1 and d["skill_key"] == "numpad2" for f, _, d in requests))
                self.assert_attacking(requests, 3)

    def test_buff_loss_interrupts_existing_attacks_and_focus_until_confirmed(self):
        for instance_id in (1, 2):
            with self.subTest(instance_id=instance_id):
                ready = self.snapshot(summons=("SummonSkeleton",), buffs=("Conjurer",))
                missing = self.snapshot(summons=("SummonSkeleton",), instance_id=instance_id)
                requests, keys = self.run_snapshots([
                    ready, missing, missing,
                    replace(missing, player=ready.player),
                ])
                self.assert_attacking(requests, 0)
                self.assert_blocked(requests, keys, {1, 2})
                self.assertTrue(any(f == 1 and d["skill_key"] == "numpad2" for f, _, d in requests))
                self.assert_attacking(requests, 3)

    def test_unavailable_status_stops_attacks_without_blind_casting(self):
        ready = self.snapshot(summons=("SummonSkeleton",), buffs=("Conjurer",))
        requests, keys = self.run_snapshots([
            ready, self.snapshot(available=False), ready,
        ])
        self.assert_attacking(requests, 0)
        self.assert_blocked(requests, keys, {1})
        self.assertTrue(all(not d["skill_key"] for f, _, d in requests if f == 1))
        self.assert_attacking(requests, 2)

    def test_follow_repairs_buff_before_requesting_channel_switch(self):
        missing = replace(
            self.snapshot(summons=("SummonSkeleton",)),
            party_members=(
                party_member("local", channel_index=0, instance_id="server-a", is_local=True),
                party_member("follow-id", channel_index=2, instance_id="server-a"),
            ),
            party_state_available=True,
        )
        ready = replace(missing, player=replace(missing.player, active_status_ids=("Conjurer",)))
        requests, keys = self.run_snapshots([missing, ready], follow=True)
        self.assert_blocked(requests, keys, {0})
        self.assertTrue(any(f == 0 and d["skill_key"] == "numpad2" for f, _, d in requests))
        self.assertTrue(all(d["follow_channel_request_id"] == 0 for f, _, d in requests if f == 0))
        self.assertTrue(any(f == 1 and d["follow_channel_request_id"] > 0 for f, _, d in requests))


if __name__ == "__main__":
    unittest.main()
