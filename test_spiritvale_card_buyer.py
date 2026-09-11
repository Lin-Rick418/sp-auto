import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import spiritvale_card_buyer as buyer
import spiritvale_red_dot_bot as bot


def wait_until_stopped(controller, timeout=1.0):
    deadline = time.monotonic() + timeout
    while controller.running and time.monotonic() < deadline:
        time.sleep(0.002)
    if controller.running:
        raise AssertionError("controller did not stop")
    return controller.state


class CardBuyerTests(unittest.TestCase):
    def test_amount_parsers_accept_commas_and_validate_zero(self):
        self.assertEqual(buyer.parse_reserve_coins(" 50,000 "), 50_000)
        self.assertEqual(buyer.parse_reserve_coins("0"), 0)
        self.assertEqual(buyer.parse_unit_price_limit(" 12,345 "), 12_345)
        for value in ("", "-1", "1.5", "coins"):
            with self.subTest(kind="reserve", value=value), self.assertRaises(ValueError):
                buyer.parse_reserve_coins(value)
        for value in ("", "0", "-1", "1.5", "coins"):
            with self.subTest(kind="limit", value=value), self.assertRaises(ValueError):
                buyer.parse_unit_price_limit(value)

    def test_affordable_quantity_preserves_reserve_and_caps_stack(self):
        self.assertEqual(buyer.affordable_quantity(1_000, 500, 120, 99), 4)
        self.assertEqual(buyer.affordable_quantity(1_000, 500, 120, 3), 3)
        self.assertEqual(buyer.affordable_quantity(500, 500, 120, 3), 0)
        self.assertEqual(buyer.affordable_quantity(499, 500, 120, 3), 0)

    def test_request_has_reserve_exclusive_limit_and_confirmation(self):
        request = buyer.build_request(5_000, 12_345)
        self.assertEqual(request["schema_version"], 2)
        self.assertEqual(request["query"], "Card")
        self.assertEqual(request["item_type"], "Card")
        self.assertEqual(request["reserve_coins"], 5_000)
        self.assertEqual(request["unit_price_limit_exclusive"], 12_345)
        self.assertNotIn("quantity", request)
        self.assertEqual(request["confirmation"], buyer.PURCHASE_CONFIRMATION)

    def test_read_result_ignores_an_old_request(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text(json.dumps({"request_id": 1, "status": "ok"}), encoding="utf-8")
            with patch.object(buyer, "RESULT_PATH", path), self.assertRaises(TimeoutError):
                buyer.read_result(2, 0.01)

    def test_result_state_preserves_stack_purchase_details(self):
        state = buyer.state_from_result({
            "status": "ok", "success": True, "reserve_coins": 50_000,
            "unit_price_limit_exclusive": 10_000,
            "item_display_name": "Poring Card", "unit_price": 2_500,
            "quantity": 4, "total_spent": 10_000,
            "balance_before": 70_000, "balance_after": 60_000,
            "code": "Success",
        })
        self.assertEqual(state.phase, "purchased")
        self.assertEqual(state.last_item_display_name, "Poring Card")
        self.assertEqual(state.last_quantity, 4)
        self.assertEqual(state.total_spent, 10_000)
        self.assertEqual(state.current_balance, 60_000)

    def test_controller_accumulates_and_stops_at_reserve(self):
        result = {
            "status": "ok", "success": True, "quantity": 3,
            "unit_price": 100, "total_spent": 300,
            "item_display_name": "A Card", "balance_before": 800,
            "balance_after": 500,
        }
        controller = buyer.CardPurchaseController(
            timeout=1.0, poll_interval=0.001, runner=lambda **_kwargs: result
        )
        self.assertTrue(controller.start(500, 101))
        state = wait_until_stopped(controller)
        self.assertEqual(state.phase, "budget_exhausted")
        self.assertEqual(state.purchased_quantity, 3)
        self.assertEqual(state.total_spent, 300)
        self.assertEqual(state.current_balance, 500)

    def test_no_match_waits_before_polling_again(self):
        calls = []
        def runner(**_kwargs):
            calls.append(time.monotonic())
            return {"status": "no_match", "balance_before": 1_000}

        controller = buyer.CardPurchaseController(timeout=1.0, poll_interval=0.03, runner=runner)
        controller.start(500, 100)
        deadline = time.monotonic() + 0.5
        while len(calls) < 2 and time.monotonic() < deadline:
            time.sleep(0.002)
        controller.request_stop()
        state = wait_until_stopped(controller)
        self.assertGreaterEqual(len(calls), 2)
        self.assertGreaterEqual(calls[1] - calls[0], 0.02)
        self.assertEqual(state.phase, "stopped")

    def test_price_change_requeries_but_fatal_error_stops(self):
        results = iter((
            {"status": "error", "code": "PriceChanged", "balance_before": 1_000},
            {"status": "error", "code": "InventoryFull", "balance_before": 1_000},
        ))
        calls = 0
        def runner(**_kwargs):
            nonlocal calls
            calls += 1
            return next(results)

        controller = buyer.CardPurchaseController(timeout=1.0, poll_interval=0.001, runner=runner)
        controller.start(100, 500)
        state = wait_until_stopped(controller)
        self.assertEqual(calls, 2)
        self.assertEqual(state.phase, "error")
        self.assertEqual(state.code, "InventoryFull")

    def test_unknown_outcome_stops_without_resending(self):
        calls = 0
        def runner(**_kwargs):
            nonlocal calls
            calls += 1
            return {"status": "unknown", "purchase_may_have_completed": True}

        controller = buyer.CardPurchaseController(timeout=1.0, poll_interval=0.001, runner=runner)
        controller.start(0, 500)
        state = wait_until_stopped(controller)
        self.assertEqual(calls, 1)
        self.assertEqual(state.phase, "unknown")

    def test_stop_waits_for_inflight_result_and_does_not_resend(self):
        entered = threading.Event()
        release = threading.Event()
        calls = 0
        def runner(**_kwargs):
            nonlocal calls
            calls += 1
            entered.set()
            release.wait(0.5)
            return {
                "status": "ok", "success": True, "quantity": 2,
                "unit_price": 100, "total_spent": 200,
                "balance_before": 1_000, "balance_after": 800,
            }

        controller = buyer.CardPurchaseController(timeout=1.0, runner=runner)
        controller.start(500, 101)
        self.assertTrue(entered.wait(0.2))
        self.assertTrue(controller.request_stop())
        self.assertEqual(controller.state.phase, "stopping")
        release.set()
        state = wait_until_stopped(controller)
        self.assertEqual(calls, 1)
        self.assertEqual(state.phase, "stopped")
        self.assertEqual(state.purchased_quantity, 2)

    def test_repeated_f4_brings_forward_the_same_window(self):
        class FakeCardController:
            def __init__(self):
                self.stop_calls = 0
                self.state = buyer.CardPurchaseState()
            @property
            def running(self): return False
            def request_stop(self): return False
            def poll_latest(self): return None
            def stop(self): self.stop_calls += 1

        class FakeWindow:
            def __init__(self, controller):
                self.controller = controller
                self.show_calls = 0
                self.stop_calls = 0
            def show(self): self.show_calls += 1
            def stop(self): self.stop_calls += 1

        class FakeFilterController:
            def start(self): pass
            def stop(self): pass
            def poll_latest(self): return None
            def request_immediate(self): pass

        class FakeEditor:
            def toggle(self): pass
            def stop(self): pass
            def set_status(self, _message): pass

        controller = FakeCardController()
        window = FakeWindow(controller)
        with patch.object(bot.card_buyer, "CardPurchaseController", return_value=controller), \
             patch.object(bot.card_buyer, "CardPurchaseWindow", return_value=window), \
             patch.object(
                 bot, "control_menu_hotkey_down",
                 side_effect=[False, True, False, True],
             ), \
             patch.object(bot, "show_control_menu", return_value="card"), \
             patch.object(bot.equipment_filter, "EquipmentFilterController", return_value=FakeFilterController()), \
             patch.object(bot.equipment_filter, "EquipmentFilterEditor", return_value=FakeEditor()), \
             patch.object(
                 bot.win32gui, "IsWindow", side_effect=[True, True, True, False]
             ), \
             patch.object(bot.win32api, "GetAsyncKeyState", return_value=0), \
             patch.object(bot, "load_memory_snapshot", side_effect=bot.SnapshotUnavailable("offline")), \
             patch.object(bot, "write_navigation_request"), \
             patch.object(bot, "update_held_keys", side_effect=lambda hwnd, held, desired: set(desired)), \
             patch.object(bot, "post_key"), patch.object(bot.time, "sleep"):
            bot.run_bot(123, bot.BotConfig(
                debug_window=False, pricing_enabled=False,
                follow_player_enabled=False,
            ), True)

        self.assertEqual(window.show_calls, 2)
        self.assertEqual(window.stop_calls, 1)
        self.assertEqual(controller.stop_calls, 1)

    def test_f9_requests_card_monitor_stop_before_bot_exit(self):
        class FakeCardController:
            timeout = 0.01
            def __init__(self):
                self.running = True
                self.state = buyer.CardPurchaseState(phase="purchasing")
                self.stop_requests = 0
            def request_stop(self):
                self.stop_requests += 1
                self.running = False
                return True
            def poll_latest(self): return None
            def stop(self): pass

        class FakeWindow:
            def __init__(self, _controller): pass
            def show(self): pass
            def stop(self): pass

        class FakeFilterController:
            def start(self): pass
            def stop(self): pass
            def poll_latest(self): return None
            def request_immediate(self): pass

        class FakeEditor:
            def toggle(self): pass
            def stop(self): pass
            def set_status(self, _message): pass

        controller = FakeCardController()
        with patch.object(bot.card_buyer, "CardPurchaseController", return_value=controller), \
             patch.object(bot.card_buyer, "CardPurchaseWindow", FakeWindow), \
             patch.object(bot.equipment_filter, "EquipmentFilterController", return_value=FakeFilterController()), \
             patch.object(bot.equipment_filter, "EquipmentFilterEditor", return_value=FakeEditor()), \
             patch.object(bot, "control_menu_hotkey_down", side_effect=[False, False, True]), \
             patch.object(bot, "show_control_menu", return_value="exit"), \
             patch.object(bot.win32gui, "IsWindow", return_value=True), \
             patch.object(bot.win32api, "GetAsyncKeyState", return_value=0), \
             patch.object(bot, "write_navigation_request"), \
             patch.object(bot, "update_held_keys", side_effect=lambda hwnd, held, desired: set(desired)), \
             patch.object(bot, "post_key"):
            bot.run_bot(123, bot.BotConfig(
                debug_window=False, pricing_enabled=False,
                follow_player_enabled=False,
            ), True)

        self.assertGreaterEqual(controller.stop_requests, 1)


if __name__ == "__main__":
    unittest.main()
