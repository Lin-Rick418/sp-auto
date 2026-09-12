"""Request publication must preserve path identity and stop-input delivery."""
from pathlib import Path
import unittest
from unittest.mock import Mock

from spiritvale_ipc import NavigationRequestPublisher


class NavigationRequestPublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.publisher = NavigationRequestPublisher(Path('unused.json'))
        self.writer = Mock()

    def publish(self, now: float, object_id: int = 501, **changes) -> bool:
        intent = dict(
            probe_active=True, loot_scan_active=True, party_follow_active=False,
            bot_active=True, movement_keys=('w',), shift_keys=('lshift',),
            summon_action='', loot_interact=0,
        )
        force = changes.pop('force', False)
        intent.update(changes)
        return self.publisher.publish(
            object_id, 'loot' if object_id else 'none', now=now, force=force,
            writer=self.writer, **intent,
        )

    def test_repeated_intent_is_suppressed_until_heartbeat(self) -> None:
        self.assertTrue(self.publish(10.0))
        self.assertFalse(self.publish(10.49))
        self.assertTrue(self.publish(10.5))
        self.assertEqual(self.writer.call_count, 2)
        self.assertEqual(self.publisher.request_id, 1)

    def test_movement_release_and_pickup_do_not_invalidate_path(self) -> None:
        self.publish(10.0)
        self.assertTrue(self.publish(10.01, movement_keys=(), shift_keys=()))
        self.assertEqual(self.publisher.request_id, 1)
        self.assertTrue(self.publish(10.02, loot_interact=1))
        self.assertEqual(self.publisher.request_id, 1)

    def test_target_and_mode_changes_require_new_path_revision(self) -> None:
        self.publish(10.0)
        self.publish(10.01, object_id=502)
        self.assertEqual(self.publisher.request_id, 2)
        self.publish(10.02, object_id=502, party_follow_active=True, probe_active=False)
        self.assertEqual(self.publisher.request_id, 3)

    def test_new_skill_request_invalidates_previous_revision(self) -> None:
        self.publish(10.0, skill_key_request_id=1, skill_key='numpad5')
        self.publish(10.01, skill_key_request_id=2, skill_key='numpad5')
        self.assertEqual(self.publisher.request_id, 2)

    def test_shutdown_force_writes_even_within_suppression_window(self) -> None:
        self.publish(10.0, object_id=0, bot_active=False, probe_active=False)
        self.assertTrue(self.publish(10.01, object_id=0, bot_active=False,
                                     probe_active=False, force=True))
        self.assertEqual(self.publisher.request_id, 1)

    def test_failed_write_does_not_consume_revision_or_suppress_retry(self) -> None:
        self.publish(10.0)
        self.writer.side_effect = PermissionError('sharing violation')
        with self.assertRaises(PermissionError):
            self.publish(10.01, object_id=502)
        self.assertEqual(self.publisher.request_id, 1)
        self.assertEqual(self.publisher.target_object_id, 501)
        self.writer.side_effect = None
        self.assertTrue(self.publish(10.02, object_id=502))
        self.assertEqual(self.publisher.request_id, 2)


if __name__ == '__main__':
    unittest.main()
