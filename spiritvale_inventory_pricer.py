"""Price non-favorite backpack equipment by exact displayed substats."""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import json
import msvcrt
import os
from pathlib import Path
import re
import statistics
import sys
import time
from typing import Any

from spiritvale_auction_query import (
    REQUEST_PATH as AUCTION_REQUEST_PATH,
    atomic_write_json,
    read_result as read_auction_result,
)
from spiritvale_paths import IPC_DIR, request_probe_load


ROOT = Path(__file__).resolve().parent
INVENTORY_REQUEST_PATH = IPC_DIR / "spiritvale_inventory_request.json"
INVENTORY_RESULT_PATH = IPC_DIR / "spiritvale_inventory_equips.json"
REPORT_PATH = ROOT / "spiritvale_inventory_price_report.json"
PRICING_LOCK_PATH = IPC_DIR / "spiritvale_inventory_pricer.lock"
AUCTION_IPC_LOCK_PATH = IPC_DIR / "spiritvale_auction_ipc.lock"

CancellationCheck = Callable[[], bool]
ProgressCallback = Callable[[dict[str, Any]], None]
AuctionFetcher = Callable[[str, float, float], list[dict[str, Any]]]


class PricingCancelled(InterruptedError):
    """Raised when a pricing run is cooperatively cancelled."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read non-favorite backpack equips from probe v2.16.0 and price "
            "them using auction listings with exactly identical displayed substats."
        )
    )
    parser.add_argument("--threshold", type=int, default=50_000)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument(
        "--request-delay",
        type=float,
        default=0.2,
        help="delay between auction pages (default: 0.2 seconds)",
    )
    return parser.parse_args(argv)


def request_id() -> int:
    return time.time_ns() // 1_000


def _cancelled(cancel_check: CancellationCheck | None) -> bool:
    return cancel_check is not None and cancel_check()


def _raise_if_cancelled(cancel_check: CancellationCheck | None) -> None:
    if _cancelled(cancel_check):
        raise PricingCancelled("Pricing cancelled")


def _interruptible_wait(
    seconds: float, cancel_check: CancellationCheck | None
) -> None:
    deadline = time.monotonic() + max(0.0, seconds)
    while True:
        _raise_if_cancelled(cancel_check)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(0.05, remaining))


def _emit_progress(
    callback: ProgressCallback | None,
    phase: str,
    *,
    current: int = 0,
    total: int = 0,
    message: str = "",
    **values: Any,
) -> None:
    if callback is None:
        return
    callback(
        {
            "phase": phase,
            "current": current,
            "total": total,
            "message": message,
            "timestamp_ms": time.time_ns() // 1_000_000,
            **values,
        }
    )


@contextmanager
def pricing_session_lock(
    *,
    cancel_check: CancellationCheck | None = None,
    progress: ProgressCallback | None = None,
    path: Path = PRICING_LOCK_PATH,
) -> Iterator[None]:
    """Serialize inventory/auction IPC between embedded and CLI pricing runs."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = path.open("a+b")
    locked = False
    announced_wait = False
    try:
        if lock_file.seek(0, os.SEEK_END) == 0:
            lock_file.write(b"0")
            lock_file.flush()
        while not locked:
            _raise_if_cancelled(cancel_check)
            try:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                locked = True
            except OSError:
                if not announced_wait:
                    _emit_progress(
                        progress,
                        "waiting_lock",
                        message="Waiting for another pricing run",
                    )
                    announced_wait = True
                _interruptible_wait(0.1, cancel_check)
        yield
    finally:
        if locked:
            try:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        lock_file.close()


def read_inventory(
    timeout: float,
    *,
    cancel_check: CancellationCheck | None = None,
) -> dict[str, Any]:
    current_id = request_id()
    request = {
        "schema_version": 1,
        "request_id": current_id,
        "timestamp_ms": time.time_ns() // 1_000_000,
    }
    atomic_write_json(INVENTORY_REQUEST_PATH, request)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        _raise_if_cancelled(cancel_check)
        try:
            result = json.loads(
                INVENTORY_RESULT_PATH.read_text(encoding="utf-8-sig")
            )
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            _interruptible_wait(0.05, cancel_check)
            continue
        if result.get("request_id") != current_id:
            _interruptible_wait(0.05, cancel_check)
            continue
        if result.get("status") != "ok":
            raise RuntimeError(
                f"Inventory export failed: {result.get('message', 'unknown error')}"
            )
        return result
    raise TimeoutError(
        "Inventory export timed out. Check that SpiritVale is logged in and "
        "BepInEx loaded SpiritVale Position Probe 2.16.0."
    )


def normalize_value_string(value: Any) -> str:
    return "" if value is None else str(value)


def normalize_number(value: Any) -> str:
    try:
        normalized = Decimal(str(value)).normalize()
    except (InvalidOperation, ValueError):
        return str(value)
    return "0" if normalized == 0 else format(normalized, "f")


def display_signature(
    item: dict[str, Any],
) -> tuple[tuple[int, str, str, str, str], ...] | None:
    stats = item.get("display_substats")
    if not isinstance(stats, list):
        return None
    signature = []
    for stat in stats:
        if not isinstance(stat, dict):
            continue
        signature.append(
            (
                int(stat.get("type_value", -1)),
                normalize_number(stat.get("value", 0)),
                normalize_number(stat.get("value_lv", 0)),
                normalize_value_string(stat.get("value_str")),
                normalize_value_string(stat.get("value_str2")),
            )
        )
    return tuple(sorted(signature))


def inventory_signature(item: dict[str, Any]):
    return display_signature(item)


def listing_signature(item: dict[str, Any]):
    return display_signature(item)


def normalized_item_name(value: Any) -> str:
    name = re.sub(r"^\s*\+\d+\s+", "", str(value or "").strip())
    return " ".join(name.split()).casefold()


def _same_base_item(owned: dict[str, Any], listing: dict[str, Any]) -> bool:
    owned_id = str(owned.get("item_id") or "").strip().casefold()
    listing_id = str(listing.get("item_id") or "").strip().casefold()
    if owned_id and listing_id:
        return owned_id == listing_id
    owned_name = owned.get("display_name") or owned.get("full_display_name")
    listing_name = listing.get("display_name") or listing.get("item_display_name")
    return normalized_item_name(owned_name) == normalized_item_name(listing_name)


def auction_page(
    query: str,
    cursor: str,
    timeout: float,
    *,
    cancel_check: CancellationCheck | None = None,
) -> dict[str, Any]:
    _raise_if_cancelled(cancel_check)
    with pricing_session_lock(
        cancel_check=cancel_check, path=AUCTION_IPC_LOCK_PATH
    ):
        current_id = request_id()
        request = {
            "schema_version": 1,
            "request_id": current_id,
            "timestamp_ms": time.time_ns() // 1_000_000,
            "query": query,
            "cursor": cursor,
            "page_size": 100,
        }
        atomic_write_json(AUCTION_REQUEST_PATH, request)
        try:
            result = read_auction_result(
                current_id, timeout, cancel_check=cancel_check
            )
        except InterruptedError as error:
            raise PricingCancelled("Pricing cancelled") from error
    if result.get("status") != "ok" or not result.get("success"):
        raise RuntimeError(
            f"Auction search failed for {query!r}: "
            f"{result.get('code', result.get('status'))} "
            f"{result.get('message', '')}".rstrip()
        )
    return result


def all_auction_items(
    query: str,
    timeout: float,
    request_delay: float,
    *,
    cancel_check: CancellationCheck | None = None,
) -> list[dict[str, Any]]:
    cursor = ""
    seen_cursors: set[str] = set()
    items: list[dict[str, Any]] = []
    for _ in range(100):
        _raise_if_cancelled(cancel_check)
        page = auction_page(
            query,
            cursor,
            timeout,
            cancel_check=cancel_check,
        )
        items.extend(
            item for item in page.get("items", []) if isinstance(item, dict)
        )
        if not page.get("has_more"):
            return items
        next_cursor = str(page.get("next_cursor", ""))
        if not next_cursor or next_cursor in seen_cursors:
            raise RuntimeError(f"Auction pagination cursor repeated for {query!r}")
        seen_cursors.add(next_cursor)
        cursor = next_cursor
        _interruptible_wait(request_delay, cancel_check)
    raise RuntimeError(f"Auction pagination exceeded 100 pages for {query!r}")


def _signed_value(value: Any) -> str:
    normalized = normalize_number(value)
    try:
        return f"+{normalized}" if Decimal(normalized) > 0 else normalized
    except InvalidOperation:
        return normalized


def stat_label(item: dict[str, Any]) -> str:
    parts = []
    stats = item.get("display_substats")
    if not isinstance(stats, list):
        return "(substat conversion failed)"
    for stat in stats:
        if not isinstance(stat, dict):
            continue
        label = str(stat.get("type") or stat.get("type_value"))
        suffix = "%" if label.endswith("Mult") else ""
        if suffix:
            label = label[:-4]
        value_string = normalize_value_string(stat.get("value_str"))
        rendered = f"{label}{_signed_value(stat.get('value', 0))}{suffix}"
        if value_string:
            rendered += f":{value_string}"
        parts.append(rendered)
    return ", ".join(parts) if parts else "(no substats)"


def exact_auction_matches(
    owned: dict[str, Any], listings: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    signature = inventory_signature(owned)
    if signature is None:
        return []
    return [
        listing
        for listing in listings
        if _same_base_item(owned, listing)
        and listing_signature(listing) == signature
    ]


def _sample_key(sample: dict[str, Any]) -> tuple[Any, ...]:
    listing_id = sample.get("listing_id")
    if listing_id:
        return ("id", str(listing_id))
    return (
        "fallback",
        sample.get("seller_name"),
        sample.get("item_display_name"),
        int(sample.get("unit_price", 0)),
    )


def group_report_items(
    report_items: list[dict[str, Any]], threshold: int
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, Any], dict[str, Any]] = {}
    samples: dict[tuple[str, Any], dict[tuple[Any, ...], dict[str, Any]]] = {}
    for item in report_items:
        signature = inventory_signature(item)
        visible_name = item.get("display_name") or item.get("item_id") or "(unknown)"
        key = (normalized_item_name(visible_name), signature)
        if key not in grouped:
            grouped[key] = {
                "display_name": str(visible_name),
                "item_id": item.get("item_id"),
                "quantity": 0,
                "uids": [],
                "display_substats": item.get("display_substats", []),
                "display_substat_signature": item.get("display_substat_signature"),
                "stat_text": stat_label(item),
            }
            samples[key] = {}
        group = grouped[key]
        group["quantity"] += 1
        if item.get("uid"):
            group["uids"].append(item["uid"])
        for sample in item.get("auction_samples", []):
            if isinstance(sample, dict):
                samples[key][_sample_key(sample)] = sample

    result = []
    for key, group in grouped.items():
        exact_samples = list(samples[key].values())
        prices = sorted(int(sample.get("unit_price", 0)) for sample in exact_samples)
        lowest = prices[0] if prices else None
        median = int(statistics.median(prices)) if prices else None
        result.append(
            {
                **group,
                "exact_listing_count": len(exact_samples),
                "exact_prices": prices,
                "lowest_exact_price": lowest,
                "median_exact_price": median,
                "over_threshold": lowest is not None and lowest > threshold,
            }
        )

    def sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
        price = item.get("lowest_exact_price")
        category = 0 if item.get("over_threshold") else 1 if price is not None else 2
        return category, -int(price or 0), normalized_item_name(item["display_name"])

    result.sort(key=sort_key)
    return result


def build_report(
    inventory: dict[str, Any],
    timeout: float,
    delay: float,
    threshold: int,
    *,
    progress: ProgressCallback | None = None,
    cancel_check: CancellationCheck | None = None,
    auction_fetcher: AuctionFetcher | None = None,
) -> dict[str, Any]:
    equipment = [
        item for item in inventory.get("items", []) if isinstance(item, dict)
    ]
    favorite_count = sum(item.get("favorite") is True for item in equipment)
    eligible = [item for item in equipment if item.get("favorite") is not True]
    by_item_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in eligible:
        by_item_id[str(item.get("item_id", ""))].append(item)

    common_counts = {
        "equipment_count": len(equipment),
        "eligible_equipment_count": len(eligible),
        "favorite_skipped_count": favorite_count,
    }
    _emit_progress(
        progress,
        "inventory_ready",
        message="Fresh inventory received",
        **common_counts,
    )

    market_by_id: dict[str, list[dict[str, Any]]] = {}
    market_by_query: dict[str, list[dict[str, Any]]] = {}
    total_types = len(by_item_id)
    for index, (item_id, owned) in enumerate(by_item_id.items(), 1):
        _raise_if_cancelled(cancel_check)
        query = str(owned[0].get("display_name") or item_id)
        _emit_progress(
            progress,
            "querying",
            current=index,
            total=total_types,
            message=query,
            **common_counts,
        )
        query_key = normalized_item_name(query)
        if query_key not in market_by_query:
            if auction_fetcher is None:
                listings = all_auction_items(
                    query,
                    timeout,
                    delay,
                    cancel_check=cancel_check,
                )
            else:
                listings = auction_fetcher(query, timeout, delay)
            market_by_query[query_key] = listings
        market_by_id[item_id] = market_by_query[query_key]
        if delay > 0 and index < total_types:
            _interruptible_wait(delay, cancel_check)

    _emit_progress(
        progress,
        "matching",
        current=total_types,
        total=total_types,
        message="Matching exact names and substats",
        **common_counts,
    )
    cache: dict[tuple[str, Any], list[dict[str, Any]]] = {}
    report_items = []
    for owned in eligible:
        _raise_if_cancelled(cancel_check)
        item_id = str(owned.get("item_id", ""))
        signature = inventory_signature(owned)
        cache_key = (item_id.casefold(), signature)
        if cache_key not in cache:
            cache[cache_key] = exact_auction_matches(
                owned, market_by_id.get(item_id, [])
            )
        exact = cache[cache_key]
        prices = sorted(int(listing.get("unit_price", 0)) for listing in exact)
        lowest = prices[0] if prices else None
        median = int(statistics.median(prices)) if prices else None
        report_items.append(
            {
                **owned,
                "display_substat_signature": (
                    [list(entry) for entry in signature]
                    if signature is not None
                    else None
                ),
                "exact_listing_count": len(exact),
                "exact_prices": prices,
                "lowest_exact_price": lowest,
                "median_exact_price": median,
                "over_threshold": lowest is not None and lowest > threshold,
                "auction_samples": [
                    {
                        "listing_id": listing.get("listing_id"),
                        "seller_name": listing.get("seller_name"),
                        "item_display_name": listing.get("item_display_name"),
                        "unit_price": int(listing.get("unit_price", 0)),
                    }
                    for listing in exact
                ],
            }
        )

    grouped_items = group_report_items(report_items, threshold)
    priced_count = sum(item["lowest_exact_price"] is not None for item in report_items)
    no_sample_count = len(report_items) - priced_count
    over_threshold_count = sum(bool(item["over_threshold"]) for item in report_items)
    report = {
        "schema_version": 2,
        "timestamp_ms": time.time_ns() // 1_000_000,
        "match_policy": {
            "name": (
                "exact base item id when available; otherwise exact display name "
                "after removing only the leading +refine token"
            ),
            "substats": (
                "exact unordered game-converted "
                "(Type, Value, ValueLv, ValueStr, ValueStr2)"
            ),
            "ignored": ["refine", "cards", "potential", "quantity"],
            "favorite": "favorite=true items are skipped before auction queries",
        },
        "threshold": threshold,
        "equipment_count": len(equipment),
        "eligible_equipment_count": len(eligible),
        "favorite_skipped_count": favorite_count,
        "priced_count": priced_count,
        "no_exact_sample_count": no_sample_count,
        "over_threshold_count": over_threshold_count,
        "group_count": len(grouped_items),
        "over_threshold_group_count": sum(
            bool(item["over_threshold"]) for item in grouped_items
        ),
        "grouped_items": grouped_items,
        "items": report_items,
    }
    _emit_progress(
        progress,
        "report_ready",
        message="Writing price report",
        **{
            key: report[key]
            for key in (
                "equipment_count",
                "eligible_equipment_count",
                "favorite_skipped_count",
                "priced_count",
                "no_exact_sample_count",
                "over_threshold_count",
            )
        },
    )
    return report


def price_backpack(
    *,
    timeout: float = 25.0,
    request_delay: float = 0.2,
    threshold: int = 50_000,
    progress: ProgressCallback | None = None,
    cancel_check: CancellationCheck | None = None,
    report_path: Path = REPORT_PATH,
    lock_path: Path = PRICING_LOCK_PATH,
) -> dict[str, Any]:
    """Run one serialized, cancellable memory-to-auction pricing session."""

    with pricing_session_lock(
        cancel_check=cancel_check, progress=progress, path=lock_path
    ):
        _raise_if_cancelled(cancel_check)
        _emit_progress(progress, "reading_inventory", message="Reading fresh inventory")
        inventory = read_inventory(timeout, cancel_check=cancel_check)
        report = build_report(
            inventory,
            timeout,
            request_delay,
            threshold,
            progress=progress,
            cancel_check=cancel_check,
        )
        _raise_if_cancelled(cancel_check)
        atomic_write_json(report_path, report)
        return report


def print_report(report: dict[str, Any]) -> None:
    threshold = int(report["threshold"])
    print(
        f"\n背包裝備：{report['equipment_count']} 件｜"
        f"收藏略過 {report['favorite_skipped_count']}｜"
        f"查價 {report['eligible_equipment_count']}"
    )
    for item in report.get("grouped_items", []):
        price = item.get("lowest_exact_price")
        price_text = f"{int(price):,}" if price is not None else "無同詞條樣本"
        quantity = int(item.get("quantity", 1))
        print(
            f"- {item.get('display_name', item.get('item_id'))} ×{quantity}｜"
            f"{item.get('stat_text', stat_label(item))}｜"
            f"最低價 {price_text}｜樣本 {item['exact_listing_count']}"
        )

    expensive = [
        item for item in report.get("grouped_items", []) if item.get("over_threshold")
    ]
    print(f"\n最低同詞條價格超過 {threshold:,}：{len(expensive)} 組")
    for item in expensive:
        print(
            f"- {item['display_name']} ×{item['quantity']}："
            f"{int(item['lowest_exact_price']):,}"
        )


def _console_progress(event: dict[str, Any]) -> None:
    phase = event.get("phase")
    if phase == "waiting_lock":
        print("等待另一個查價工作完成…", flush=True)
    elif phase == "reading_inventory":
        print("讀取最新背包記憶體…", flush=True)
    elif phase == "querying":
        print(
            f"[{event.get('current', 0)}/{event.get('total', 0)}] "
            f"查詢 {event.get('message', '')}…",
            flush=True,
        )


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    if args.timeout <= 0 or args.request_delay < 0:
        print(
            "timeout must be positive and request-delay cannot be negative",
            file=sys.stderr,
        )
        return 2
    try:
        request_probe_load()
        report = price_backpack(
            timeout=args.timeout,
            request_delay=args.request_delay,
            threshold=args.threshold,
            progress=_console_progress,
        )
    except PricingCancelled:
        print("Pricing cancelled", file=sys.stderr)
        return 130
    except (TimeoutError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print_report(report)
    print(f"\n完整報告：{REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
