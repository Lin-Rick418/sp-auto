from dataclasses import replace
import unittest
from unittest.mock import Mock
import spiritvale_red_dot_bot as bot


class GuardianBondTests(unittest.TestCase):
    def setUp(self):
        self.config = bot.BotConfig()
        self.config.summoner_checks['GuardianBond'] = {'enabled': True, 'key': 'numpad9'}
        self.player = bot.MemoryPlayer(
            position=(0, 0, 0), camera_forward_xz=(0, 1),
            camera_right_xz=(1, 0), collider_radius=1,
            guardian_bond_available=True, guardian_bond_candidate_id=12,
        )

    def test_incoming_status_does_not_satisfy_outgoing_owned_bond(self):
        player = replace(self.player, active_statuses_available=True,
                         active_status_ids=('GuardianBond',))
        self.assertEqual(bot.missing_summoner_checks(self.config, player),
                         (('GuardianBond',), ''))

    def test_owned_link_is_sufficient_without_player_status_catalog(self):
        self.assertEqual(bot.missing_summoner_checks(
            self.config, replace(self.player, guardian_bond_active=True)), ((), ''))

    def test_older_probe_blocks_cast_with_actionable_reason(self):
        callback = Mock()
        state = bot.SummonerCheckState()
        self.assertTrue(bot.advance_summoner_checks(state, self.config,
            replace(self.player, guardian_bond_available=False), enabled=True,
            now=10, press_key=callback))
        callback.assert_not_called()
        self.assertEqual(state.phase, 'unavailable')
        self.assertIn('updated probe required', state.error)

    def test_no_owned_summon_does_not_press_skill(self):
        callback = Mock()
        state = bot.SummonerCheckState()
        bot.advance_summoner_checks(state, self.config,
            replace(self.player, guardian_bond_candidate_id=0), enabled=True,
            now=10, press_key=callback)
        callback.assert_not_called()
        self.assertIn('No living summon', state.error)

    def test_cast_waits_for_confirmation_without_interrupting_one_second_cast(self):
        callback = Mock(return_value=True)
        state = bot.SummonerCheckState()
        for now in (10, 10.5, 10.8, 11.1, 12.4):
            self.assertTrue(bot.advance_summoner_checks(state, self.config,
                self.player, enabled=True, now=now, press_key=callback))
        callback.assert_called_once_with('numpad9', True)
        self.assertFalse(bot.advance_summoner_checks(state, self.config,
            replace(self.player, guardian_bond_active=True), enabled=True,
            now=12.45, press_key=callback))
        callback.assert_called_once()

    def test_failed_cast_retries_after_wait(self):
        callback = Mock(return_value=True)
        state = bot.SummonerCheckState()
        for now in (10, 12.6):
            bot.advance_summoner_checks(state, self.config, self.player,
                enabled=True, now=now, press_key=callback)
        self.assertEqual(callback.call_count, 2)

    def test_other_missing_summon_can_be_created_first(self):
        self.config.summoner_checks['SummonSkeleton'] = {'enabled': True, 'key': 'numpad5'}
        callback = Mock(return_value=True)
        bot.advance_summoner_checks(bot.SummonerCheckState(), self.config,
            replace(self.player, guardian_bond_candidate_id=0, summon_displays_available=True),
            enabled=True, now=10, press_key=callback)
        callback.assert_called_once_with('numpad5', False)


if __name__ == '__main__':
    unittest.main()
