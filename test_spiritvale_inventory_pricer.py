import unittest
from unittest.mock import patch

import spiritvale_inventory_pricer as pricer


class ExactSubstatTests(unittest.TestCase):
    def test_inventory_and_listing_signatures_match_unordered(self):
        owned = {
            "display_substats": [
                {
                    "type_value": 70,
                    "value": "0.02",
                    "value_lv": "0",
                    "value_str": "",
                    "value_str2": "",
                },
                {
                    "type_value": 4,
                    "value": "3",
                    "value_lv": "0",
                    "value_str": "",
                    "value_str2": "",
                },
            ]
        }
        listing = {
            "display_substats": [
                {
                    "type_value": 4,
                    "value": "3.0",
                    "value_lv": "0.0",
                    "value_str": None,
                    "value_str2": "",
                },
                {
                    "type_value": 70,
                    "value": "0.020",
                    "value_lv": "0",
                    "value_str": "",
                    "value_str2": "",
                },
            ]
        }
        self.assertEqual(
            pricer.inventory_signature(owned), pricer.listing_signature(listing)
        )

    def test_different_value_or_extra_stat_does_not_match(self):
        owned = {
            "display_substats": [
                {"type_value": 4, "value": "3", "value_lv": "0"}
            ]
        }
        different_value = {
            "display_substats": [
                {"type_value": 4, "value": "4", "value_lv": "0"}
            ]
        }
        extra_stat = {
            "display_substats": [
                {"type_value": 4, "value": "3", "value_lv": "0"},
                {"type_value": 10, "value": "2", "value_lv": "0"},
            ]
        }
        signature = pricer.inventory_signature(owned)
        self.assertNotEqual(signature, pricer.listing_signature(different_value))
        self.assertNotEqual(signature, pricer.listing_signature(extra_stat))

    def test_refine_cards_and_potential_are_not_in_signature(self):
        first = {
            "refine": 0,
            "cards": [],
            "potential": 1,
            "display_substats": [
                {"type_value": 10, "value": "2", "value_lv": "0"}
            ],
        }
        second = {
            "refine": 15,
            "cards": ["Card A", "Card B"],
            "potential": 99,
            "display_substats": [
                {"type_value": 10, "value": "2", "value_lv": "0"}
            ],
        }
        self.assertEqual(
            pricer.inventory_signature(first), pricer.inventory_signature(second)
        )

    def test_name_ignores_only_leading_refine(self):
        self.assertEqual(
            pricer.normalized_item_name("+6 Double Mind Sapphire Crown"),
            pricer.normalized_item_name("Double Mind Sapphire Crown"),
        )
        self.assertNotEqual(
            pricer.normalized_item_name("Double Mind Sapphire Crown"),
            pricer.normalized_item_name("Sapphire Crown"),
        )

    def test_stat_label_renders_the_requested_base_values(self):
        item = {
            "display_substats": [
                {"type": "Int", "type_value": 4, "value": "3"},
                {"type": "Matk", "type_value": 10, "value": "2"},
                {"type": "MatkMult", "type_value": 70, "value": "2"},
            ]
        }
        self.assertEqual(pricer.stat_label(item), "Int+3, Matk+2, Matk+2%")


def equipment(
    item_id: str,
    name: str,
    value: int,
    *,
    uid: str,
    favorite: bool = False,
) -> dict:
    return {
        "item_id": item_id,
        "display_name": name,
        "full_display_name": name,
        "uid": uid,
        "favorite": favorite,
        "refine": 0,
        "cards": [],
        "potential": 10,
        "display_substats": [
            {
                "type": "Int",
                "type_value": 4,
                "value": str(value),
                "value_lv": "0",
                "value_str": "",
                "value_str2": "",
            }
        ],
    }


def listing(item_id: str, name: str, value: int, price: int, listing_id: str) -> dict:
    return {
        "item_id": item_id,
        "item_display_name": name,
        "listing_id": listing_id,
        "seller_name": "seller",
        "unit_price": price,
        "display_substats": [
            {
                "type": "Int",
                "type_value": 4,
                "value": str(value),
                "value_lv": "0",
                "value_str": "",
                "value_str2": "",
            }
        ],
    }


class ReportTests(unittest.TestCase):
    def test_favorites_are_removed_before_queries_and_counts(self):
        inventory = {
            "items": [
                equipment("FavoriteOnly", "Favorite Only", 3, uid="fav-1", favorite=True),
                equipment("Mixed", "Mixed Item", 3, uid="fav-2", favorite=True),
                equipment("Mixed", "Mixed Item", 3, uid="sell-1"),
            ]
        }
        queries = []

        def fetch(query, _timeout, _delay):
            queries.append(query)
            return [listing("Mixed", "Mixed Item", 3, 75_000, "listing-1")]

        report = pricer.build_report(
            inventory, 1.0, 0.0, 50_000, auction_fetcher=fetch
        )
        self.assertEqual(queries, ["Mixed Item"])
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["equipment_count"], 3)
        self.assertEqual(report["favorite_skipped_count"], 2)
        self.assertEqual(report["eligible_equipment_count"], 1)
        self.assertEqual(report["priced_count"], 1)
        self.assertEqual(report["over_threshold_count"], 1)
        self.assertEqual([item["uid"] for item in report["items"]], ["sell-1"])

    def test_identical_name_and_stats_are_grouped_without_duplicate_samples(self):
        inventory = {
            "items": [
                equipment("Mind", "Mind Gloves", 3, uid="one"),
                equipment("Mind", "Mind Gloves", 3, uid="two"),
            ]
        }
        queries = []

        def fetch(query, _timeout, _delay):
            queries.append(query)
            return [listing("Mind", "+6 Mind Gloves", 3, 60_000, "listing-1")]

        report = pricer.build_report(
            inventory, 1.0, 0.0, 50_000, auction_fetcher=fetch
        )
        self.assertEqual(queries, ["Mind Gloves"])
        self.assertEqual(len(report["items"]), 2)
        self.assertEqual(len(report["grouped_items"]), 1)
        group = report["grouped_items"][0]
        self.assertEqual(group["quantity"], 2)
        self.assertEqual(group["exact_listing_count"], 1)
        self.assertEqual(group["lowest_exact_price"], 60_000)
        self.assertEqual(report["over_threshold_count"], 2)
        self.assertEqual(report["over_threshold_group_count"], 1)

    def test_threshold_is_strictly_greater_than_fifty_thousand(self):
        inventory = {
            "items": [
                equipment("Equal", "Equal", 3, uid="equal"),
                equipment("Higher", "Higher", 4, uid="higher"),
            ]
        }

        def fetch(query, _timeout, _delay):
            if query == "Equal":
                return [listing("Equal", "Equal", 3, 50_000, "equal-listing")]
            return [listing("Higher", "Higher", 4, 50_001, "higher-listing")]

        report = pricer.build_report(
            inventory, 1.0, 0.0, 50_000, auction_fetcher=fetch
        )
        by_id = {item["item_id"]: item for item in report["items"]}
        self.assertFalse(by_id["Equal"]["over_threshold"])
        self.assertTrue(by_id["Higher"]["over_threshold"])
        self.assertEqual(report["over_threshold_count"], 1)
        self.assertEqual(report["grouped_items"][0]["item_id"], "Higher")

    def test_name_or_stat_mismatch_never_uses_nearby_listing(self):
        inventory = {"items": [equipment("Mind", "Mind Gloves", 3, uid="one")]}

        def fetch(_query, _timeout, _delay):
            return [
                listing("Other", "Mind Gloves", 3, 10_000, "wrong-name"),
                listing("Mind", "Mind Gloves", 4, 20_000, "wrong-stat"),
            ]

        report = pricer.build_report(
            inventory, 1.0, 0.0, 50_000, auction_fetcher=fetch
        )
        self.assertEqual(report["priced_count"], 0)
        self.assertEqual(report["no_exact_sample_count"], 1)
        self.assertIsNone(report["items"][0]["lowest_exact_price"])


if __name__ == "__main__":
    unittest.main()
