from __future__ import annotations

from pathlib import Path
import tempfile
import threading
import time
import unittest

import spiritvale_equipment_filter as equipment_filter


def item(
    uid: str,
    *,
    item_id: str | None = None,
    display_name: str | None = None,
    favorite: bool = False,
    stats: tuple[tuple[str, str], ...] = (),
) -> dict[str, object]:
    stable_id = item_id or f"item-{uid}"
    return {
        "uid": uid,
        "item_id": stable_id,
        "display_name": display_name or stable_id,
        "favorite": favorite,
        "display_substats": [
            {"type": stat_type, "value": value}
            for stat_type, value in stats
        ],
    }


def profile(
    item_id: str,
    *,
    minimum_matches: int = 1,
    rules: tuple[tuple[str, float], ...] = (),
    always_dismantle: bool = False,
) -> equipment_filter.EquipmentFilterProfile:
    return equipment_filter.EquipmentFilterProfile(
        item_id=item_id,
        display_name=f"Display {item_id}",
        minimum_matches=minimum_matches,
        rules=tuple(
            equipment_filter.EquipmentFilterRule(stat_type, minimum)
            for stat_type, minimum in rules
        ),
        always_dismantle=always_dismantle,
    )


class EquipmentFilterRuleTests(unittest.TestCase):
    def test_all_game_stat_types_are_available_once(self) -> None:
        self.assertEqual(equipment_filter.FILTER_INTERVAL_SEC, 100.0)
        self.assertEqual(len(equipment_filter.STAT_TYPES), 232)
        self.assertEqual(len(set(equipment_filter.STAT_TYPES)), 232)
        self.assertEqual(len(equipment_filter.STAT_TYPE_ZH), 232)
        self.assertEqual(
            set(equipment_filter.STAT_TYPE_ZH),
            set(equipment_filter.STAT_TYPES),
        )
        self.assertIn("MatkMult", equipment_filter.STAT_TYPES)
        self.assertEqual(
            equipment_filter.stat_display_label("MatkMult"),
            "MATK%  (MatkMult) — 魔法攻擊力百分比",
        )
        self.assertEqual(
            equipment_filter.stat_display_label("MoveSpd"),
            "MoveSpd — 移動速度",
        )

    def test_matk_two_percent_meets_two_but_one_does_not(self) -> None:
        selected = profile(
            "item-a",
            minimum_matches=1,
            rules=(("MatkMult", 2),),
        )
        accepted = equipment_filter.evaluate_equipment(
            item("a", stats=(("MatkMult", "2"),)), selected
        )
        rejected_profile = profile(
            "item-b", minimum_matches=1, rules=(("MatkMult", 2),)
        )
        rejected = equipment_filter.evaluate_equipment(
            item("b", stats=(("MatkMult", "1"),)), rejected_profile
        )
        self.assertTrue(accepted.keep)
        self.assertEqual(accepted.matched_count, 1)
        self.assertFalse(rejected.keep)
        self.assertEqual(rejected.matched_count, 0)

    def test_n_of_m_counts_only_rules_meeting_their_minimum(self) -> None:
        selected = profile(
            "item-n",
            minimum_matches=2,
            rules=(("MatkMult", 2), ("Int", 3), ("Mdef", 8)),
        )
        decision = equipment_filter.evaluate_equipment(
            item(
                "n",
                stats=(("MatkMult", "2"), ("Int", "3"), ("Mdef", "7")),
            ),
            selected,
        )
        self.assertTrue(decision.keep)
        self.assertEqual(decision.matched_types, ("MatkMult", "Int"))

    def test_config_round_trip(self) -> None:
        config = equipment_filter.EquipmentFilterConfig(
            enabled=True,
            profiles=(
                profile("helmet", rules=(("MatkMult", 2.5),)),
                profile(
                    "boots",
                    minimum_matches=2,
                    rules=(("MoveSpd", 10), ("Agi", 3)),
                ),
                profile("trash-name", always_dismantle=True),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "filter.json"
            equipment_filter.save_filter_config(path, config)
            loaded = equipment_filter.load_filter_config(path)
        self.assertEqual(loaded, config)

    def test_enabled_without_named_rules_is_safe_to_store_but_not_run(self) -> None:
        config = equipment_filter.EquipmentFilterConfig(
            enabled=True,
            profiles=(profile("helmet"),),
        )
        equipment_filter.validate_filter_config(config)
        with self.assertRaisesRegex(ValueError, "no named profiles with rules"):
            equipment_filter.EquipmentFilterRunner(
                inventory_reader=lambda _timeout: {"items": []},
                lock_factory=equipment_filter.no_lock_factory,
            ).run(config)

    def test_catalog_combines_backpack_and_nested_equipped_items(self) -> None:
        catalog = equipment_filter.equipment_catalog(
            {
                "items": [item("a", item_id="helmet", display_name="Helmet")],
                "equipped_items": [
                    {
                        "slot": "Feet",
                        "item": item(
                            "b", item_id="boots", display_name="Swift Boots"
                        ),
                    }
                ],
            }
        )
        self.assertEqual(catalog, {"helmet": "Helmet", "boots": "Swift Boots"})

    def test_legacy_global_config_is_disabled_instead_of_applied_to_all_names(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "filter.json"
            path.write_text(
                '{"schema_version":1,"enabled":true,"minimum_matches":1,'
                '"rules":[{"stat_type":"MatkMult","minimum":2}]}',
                encoding="utf-8",
            )
            loaded = equipment_filter.load_filter_config(path)
        self.assertFalse(loaded.enabled)
        self.assertEqual(loaded.profiles, ())

    def test_schema_two_profiles_migrate_with_force_mode_off(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "filter.json"
            path.write_text(
                '{"schema_version":2,"enabled":true,"profiles":['
                '{"item_id":"helmet","display_name":"Helmet",'
                '"minimum_matches":1,"rules":['
                '{"stat_type":"MatkMult","minimum":2}]}]}',
                encoding="utf-8",
            )
            loaded = equipment_filter.load_filter_config(path)
        self.assertTrue(loaded.enabled)
        self.assertEqual(len(loaded.profiles), 1)
        self.assertFalse(loaded.profiles[0].always_dismantle)

    def test_always_dismantle_profile_ignores_every_stat(self) -> None:
        forced = profile(
            "helmet",
            minimum_matches=232,
            rules=(("MatkMult", 999),),
            always_dismantle=True,
        )
        self.assertIn(
            forced,
            equipment_filter.active_profiles(
                equipment_filter.EquipmentFilterConfig(
                    enabled=True,
                    profiles=(forced,),
                )
            ),
        )
        decision = equipment_filter.evaluate_equipment(
            item(
                "forced",
                item_id="helmet",
                stats=(("MatkMult", "999"), ("MoveSpd", "999")),
            ),
            forced,
        )
        self.assertFalse(decision.keep)
        self.assertTrue(decision.forced_dismantle)
        self.assertEqual(decision.matched_count, 0)
        self.assertEqual(decision.required_count, 0)


class EquipmentFilterRunnerTests(unittest.TestCase):
    def test_matching_items_are_favorited_and_nonmatching_items_dismantled(
        self,
    ) -> None:
        favorite_calls: list[tuple[str, bool, str]] = []
        dismantle_calls: list[str] = []

        def favorite(uid: str, _item_id: str, **kwargs: object) -> dict[str, object]:
            favorite_calls.append(
                (uid, bool(kwargs["desired"]), str(kwargs["location"]))
            )
            return {"status": "ok", "favorite": kwargs["desired"]}

        def dismantle(uid: str, _item_id: str, **_kwargs: object) -> dict[str, object]:
            dismantle_calls.append(uid)
            return {"status": "ok", "verified_absent": True}

        runner = equipment_filter.EquipmentFilterRunner(
            inventory_reader=lambda _timeout: {
                "items": [
                    item("keep", item_id="helmet", stats=(("MatkMult", "2"),)),
                    item(
                        "old-favorite",
                        item_id="helmet",
                        favorite=True,
                        stats=(("MatkMult", "1"),),
                    ),
                    item("trash", item_id="helmet", stats=(("Int", "1"),)),
                    item("unknown", item_id="ring", stats=(("MatkMult", "9"),)),
                ]
            },
            favorite_mutator=favorite,
            dismantler=dismantle,
            lock_factory=equipment_filter.no_lock_factory,
        )
        result = runner.run(
            equipment_filter.EquipmentFilterConfig(
                enabled=True,
                profiles=(
                    profile("helmet", rules=(("MatkMult", 2),)),
                ),
            )
        )

        self.assertEqual(
            favorite_calls,
            [("keep", True, "backpack")],
        )
        self.assertEqual(dismantle_calls, ["trash"])
        self.assertEqual(result.scanned, 4)
        self.assertEqual(result.kept, 1)
        self.assertEqual(result.protected, 1)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.favorited, 1)
        self.assertEqual(result.dismantled, 1)
        self.assertEqual(result.errors, 0)

    def test_favorite_nonmatching_item_is_never_mutated_or_dismantled(self) -> None:
        favorite_calls: list[str] = []
        dismantle_calls: list[str] = []

        def favorite(uid: str, *_args: object, **_kwargs: object) -> dict[str, object]:
            favorite_calls.append(uid)
            return {"status": "ok"}

        def dismantle(uid: str, _item_id: str, **_kwargs: object) -> dict[str, object]:
            dismantle_calls.append(uid)
            return {"status": "ok"}

        runner = equipment_filter.EquipmentFilterRunner(
            inventory_reader=lambda _timeout: {
                "items": [item("protected", item_id="helmet", favorite=True)]
            },
            favorite_mutator=favorite,
            dismantler=dismantle,
            lock_factory=equipment_filter.no_lock_factory,
        )
        result = runner.run(
            equipment_filter.EquipmentFilterConfig(
                enabled=True,
                profiles=(profile("helmet", rules=(("MatkMult", 2),)),),
            )
        )
        self.assertEqual(favorite_calls, [])
        self.assertEqual(dismantle_calls, [])
        self.assertEqual(result.protected, 1)
        self.assertEqual(result.errors, 0)
        self.assertEqual(result.dismantled, 0)

    def test_different_names_use_different_stat_rules(self) -> None:
        dismantle_calls: list[str] = []
        favorite_calls: list[str] = []

        runner = equipment_filter.EquipmentFilterRunner(
            inventory_reader=lambda _timeout: {
                "items": [
                    item("h", item_id="helmet", stats=(("MatkMult", "2"),)),
                    item(
                        "b",
                        item_id="boots",
                        stats=(("MatkMult", "2"), ("MoveSpd", "9")),
                    ),
                ]
            },
            favorite_mutator=lambda uid, _item_id, **_kwargs: (
                favorite_calls.append(uid) or {"status": "ok"}
            ),
            dismantler=lambda uid, _item_id, **_kwargs: (
                dismantle_calls.append(uid) or {"status": "ok"}
            ),
            lock_factory=equipment_filter.no_lock_factory,
        )
        result = runner.run(
            equipment_filter.EquipmentFilterConfig(
                enabled=True,
                profiles=(
                    profile("helmet", rules=(("MatkMult", 2),)),
                    profile("boots", rules=(("MoveSpd", 10),)),
                ),
            )
        )
        self.assertEqual(favorite_calls, ["h"])
        self.assertEqual(dismantle_calls, ["b"])
        self.assertEqual(result.kept, 1)
        self.assertEqual(result.dismantled, 1)

    def test_always_dismantle_still_never_touches_favorites(self) -> None:
        dismantle_calls: list[str] = []
        runner = equipment_filter.EquipmentFilterRunner(
            inventory_reader=lambda _timeout: {
                "items": [
                    item("protected", item_id="helmet", favorite=True),
                    item(
                        "forced",
                        item_id="helmet",
                        stats=(("MatkMult", "999"),),
                    ),
                ]
            },
            dismantler=lambda uid, _item_id, **_kwargs: (
                dismantle_calls.append(uid) or {"status": "ok"}
            ),
            lock_factory=equipment_filter.no_lock_factory,
        )
        result = runner.run(
            equipment_filter.EquipmentFilterConfig(
                enabled=True,
                profiles=(profile("helmet", always_dismantle=True),),
            )
        )
        self.assertEqual(dismantle_calls, ["forced"])
        self.assertEqual(result.protected, 1)
        self.assertEqual(result.dismantled, 1)
        self.assertEqual(result.forced_dismantled, 1)


class EquipmentFilterScheduleTests(unittest.TestCase):
    def test_enabled_rules_run_automatically_after_the_interval(self) -> None:
        called = threading.Event()

        class FakeRunner:
            def run(self, _config, *, cancel_check, progress):
                self.cancel_check = cancel_check
                self.progress = progress
                called.set()
                return equipment_filter.EquipmentFilterState(
                    phase="complete",
                    message="scheduled run complete",
                    timestamp_ms=1,
                )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "filter.json"
            equipment_filter.save_filter_config(
                path,
                equipment_filter.EquipmentFilterConfig(
                    enabled=True,
                    profiles=(
                        profile("helmet", rules=(("MatkMult", 2),)),
                    ),
                ),
            )
            controller = equipment_filter.EquipmentFilterController(
                config_path=path,
                runner=FakeRunner(),  # type: ignore[arg-type]
                interval_sec=0.1,
            )
            controller.start()
            self.assertTrue(called.wait(0.6))
            controller.stop(0.5)
        self.assertFalse(controller.running)


if __name__ == "__main__":
    unittest.main()
