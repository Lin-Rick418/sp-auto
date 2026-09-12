"""Exercise pickup decisions without a window, clock sleeps, or probe IPC."""
from dataclasses import replace
import math
import unittest

from spiritvale_config import BotConfig
from spiritvale_loot import plan_loot_approach, plan_loot_interaction, reset_loot_chase
from spiritvale_models import (
    LootChaseState, MemoryLoot, MemoryMapExit, MemoryPath, MemoryPlayer, MemorySnapshot,
)


def player_at(x: float = 0.0) -> MemoryPlayer:
    return MemoryPlayer((x, 0.0, 0.0), (0.0, 1.0), (1.0, 0.0), 0.2)


def drop_at(x: float, object_id: int = 501) -> MemoryLoot:
    return MemoryLoot(
        object_id=object_id, item_id='Flax', display_name='Flax', sprite_id='',
        rarity='Legendary', rarity_value=3, loot_type='Material',
        position=(x, 0.0, 0.0), viewport_position=(0.0, 0.0, 0.0),
        viewport_visible=False, locked=False, owner_player_id='local',
        owner_party_id=0, owned_by_local_player=True, interaction_range=1.0,
    )


class LootInteractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = BotConfig(memory_loot_range_padding_world=-0.2)
        self.state = LootChaseState()
        self.loot = drop_at(0.75)

    def step(self, now: float, **overrides):
        arguments = dict(
            now=now, confirmed_frames=2, last_interact_at=-math.inf,
            send_input=True,
        )
        arguments.update(overrides)
        return plan_loot_interaction(
            self.state, player_at(), self.loot, self.config, **arguments,
        )

    def test_confirmation_precedes_release_and_pickup(self) -> None:
        first = self.step(10.0, confirmed_frames=1)
        self.assertEqual(first.phase, 'confirm')
        self.assertIsNone(self.state.release_started_at)
        release = self.step(10.01)
        self.assertEqual(release.phase, 'release')
        self.assertTrue(release.started_release)
        self.assertIsNone(release.pickup_object_id)
        pickup = self.step(10.07)
        self.assertEqual(pickup.pickup_object_id, 501)

    def test_boundary_jitter_does_not_restart_release(self) -> None:
        self.step(10.0)
        self.loot = replace(self.loot, position=(0.95, 0.0, 0.0))
        pickup = self.step(10.06)
        self.assertEqual(pickup.pickup_object_id, 501)
        self.assertEqual(self.state.release_started_at, 10.0)

    def test_leaving_server_range_requires_a_new_release_on_return(self) -> None:
        self.step(10.0)
        self.loot = replace(self.loot, position=(1.01, 0.0, 0.0))
        self.assertEqual(self.step(10.06).phase, 'chase')
        self.assertIsNone(self.state.release_started_at)
        self.loot = replace(self.loot, position=(0.75, 0.0, 0.0))
        self.assertEqual(self.step(10.07).phase, 'release')
        self.assertEqual(self.step(10.13).pickup_object_id, 501)

    def test_preview_never_returns_an_executable_pickup(self) -> None:
        self.step(10.0, send_input=False)
        preview = self.step(10.06, send_input=False)
        self.assertTrue(preview.interaction_due)
        self.assertIsNone(preview.pickup_object_id)

    def test_cooldown_applies_even_after_target_changes(self) -> None:
        self.step(10.0)
        self.assertEqual(self.step(10.06).pickup_object_id, 501)
        self.loot = replace(self.loot, object_id=502)
        reset_loot_chase(self.state, now=10.1, target_object_id=502)
        self.step(10.1, last_interact_at=10.06)
        waiting = self.step(10.2, last_interact_at=10.06)
        self.assertFalse(waiting.interaction_due)
        self.assertIsNone(waiting.pickup_object_id)
        self.assertEqual(self.step(10.57, last_interact_at=10.06).pickup_object_id, 502)

    def test_pause_and_death_cancel_release_before_resuming(self) -> None:
        for reason in ('paused', 'dead'):
            with self.subTest(reason=reason):
                self.step(10.0)
                stopped = plan_loot_interaction(
                    self.state, replace(player_at(), alive=reason != 'dead'),
                    self.loot, self.config, now=10.06, confirmed_frames=2,
                    last_interact_at=-math.inf, send_input=True,
                    enabled=reason != 'paused',
                )
                self.assertEqual(stopped.phase, 'stop')
                self.assertIsNone(stopped.pickup_object_id)
                self.assertIsNone(self.state.release_started_at)
                self.assertEqual(self.step(11.0).phase, 'release')
                reset_loot_chase(self.state, now=12.0)

    def test_exit_keepout_cancels_pending_pickup(self) -> None:
        self.step(10.0)
        decision = self.step(10.06, in_exit_keepout=True)
        self.assertEqual(decision.phase, 'chase')
        self.assertIsNone(decision.pickup_object_id)
        self.assertIsNone(self.state.release_started_at)

    def test_hard_distance_cap_limits_hysteresis(self) -> None:
        self.config.memory_loot_max_distance_world = 0.8
        self.step(10.0)
        self.loot = replace(self.loot, position=(0.85, 0.0, 0.0))
        self.assertEqual(self.step(10.06).phase, 'chase')


class LootApproachTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loot = drop_at(5.0)
        self.config = BotConfig(memory_loot_chase_timeout_sec=100.0)
        self.state = LootChaseState()
        reset_loot_chase(self.state, now=10.0, target_object_id=501,
                         player_position=player_at().position)
        self.snapshot = MemorySnapshot(
            timestamp_ms=10_000, map_id=1, instance_id=1, player=player_at(),
            monsters=(), loots=(self.loot,), path=MemoryPath(
                7, 501, 'complete', ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0)), 'loot',
            ),
        )

    def step(self, now: float = 10.1, **overrides):
        arguments = dict(request_id=7, now=now, send_input=True, loot_rule_label='Legendary')
        arguments.update(overrides)
        return plan_loot_approach(self.snapshot, self.loot, self.state,
                                  self.config, **arguments)

    def test_valid_path_returns_movement_without_skill_or_pickup_input(self) -> None:
        decision = self.step()
        self.assertTrue(decision.path_ready)
        self.assertEqual(decision.movement_keys, ('d',))
        self.assertIsNone(decision.failure_reason)

    def test_old_response_is_rejected_then_expires(self) -> None:
        waiting = self.step(request_id=8)
        self.assertFalse(waiting.path_ready)
        self.assertEqual(waiting.movement_keys, ())
        self.assertIsNone(waiting.failure_reason)
        self.assertEqual(self.step(11.2, request_id=8).failure_reason, 'path')

    def test_wrong_target_kind_cannot_drive_loot_navigation(self) -> None:
        self.snapshot = replace(self.snapshot, path=replace(self.snapshot.path, target_kind='monster'))
        decision = self.step()
        self.assertFalse(decision.path_ready)
        self.assertEqual(decision.movement_keys, ())
        self.assertEqual(decision.notices[0].dedupe_key, 'loot_target_kind_probe_upgrade_required')

    def test_path_crossing_exit_returns_failure_for_caller_to_handle(self) -> None:
        self.config.map_exit_avoidance_padding_world = 0.0
        self.snapshot = replace(self.snapshot, map_exits=(MemoryMapExit((2.5, 0.0, 0.0), 0.5),))
        decision = self.step()
        self.assertEqual(decision.failure_reason, 'map_exit')
        self.assertFalse(decision.path_ready)
        self.assertEqual(decision.movement_keys, ())

    def test_no_progress_starts_recovery_and_exhaustion_reports_failure(self) -> None:
        recovery = self.step(12.0)
        self.assertEqual(recovery.movement_keys, ('s',))
        self.assertEqual(self.state.unstuck_attempt, 1)
        self.config.unstuck_max_attempts = 1
        self.assertEqual(self.step(20.0).failure_reason, 'unstuck')

    def test_preview_does_not_start_recovery_or_enforce_chase_timeout(self) -> None:
        self.config.memory_loot_chase_timeout_sec = 0.1
        decision = self.step(20.0, send_input=False)
        self.assertEqual(decision.movement_keys, ('d',))
        self.assertIsNone(decision.failure_reason)
        self.assertIsNone(self.state.unstuck_started_at)


if __name__ == '__main__':
    unittest.main()
