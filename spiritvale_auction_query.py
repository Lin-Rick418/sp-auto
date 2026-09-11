"""Read-only SpiritVale auction search through the in-process BepInEx probe."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from contextlib import contextmanager
import json
import msvcrt
import os
import sys
import time
from pathlib import Path
from typing import Any

from spiritvale_paths import IPC_DIR, request_probe_load


ROOT = Path(__file__).resolve().parent
REQUEST_PATH = IPC_DIR / "spiritvale_auction_request.json"
RESULT_PATH = IPC_DIR / "spiritvale_auction_results.json"
AUCTION_IPC_LOCK_PATH = IPC_DIR / "spiritvale_auction_ipc.lock"

STAT_ALIASES = {
    "int": "Int",
    "matk": "Matk",
    "matk%": "MatkMult",
    "matkmult": "MatkMult",
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def stat_filter(value: str) -> dict[str, Any]:
    try:
        raw_type, raw_minimum = value.rsplit("=", 1)
        stat_type = STAT_ALIASES.get(raw_type.strip().lower(), raw_type.strip())
        minimum = int(raw_minimum)
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError(
            "use TYPE=VALUE, for example Int=3, Matk=2, or Matk%=2"
        ) from None
    if not stat_type or not stat_type.replace("_", "").isalnum():
        raise argparse.ArgumentTypeError("stat type must be an enum-style name")
    return {"type": stat_type, "minimum_value": minimum}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Search the SpiritVale auction without opening its normal UI. "
            "The game and v2.16.0 on-demand probe must already be running."
        )
    )
    parser.add_argument("query", help="auction item name or search text")
    parser.add_argument("--page-size", type=positive_int, default=50)
    parser.add_argument("--cursor", default="")
    parser.add_argument("--min-price", type=int)
    parser.add_argument("--max-price", type=int)
    parser.add_argument("--min-level", type=int)
    parser.add_argument("--max-level", type=int)
    parser.add_argument("--min-refine", type=int)
    parser.add_argument("--max-refine", type=int)
    parser.add_argument("--min-potential", type=int)
    parser.add_argument("--max-potential", type=int)
    parser.add_argument("--min-quantity", type=int)
    parser.add_argument("--has-gem", action=argparse.BooleanOptionalAction)
    parser.add_argument("--has-card", action=argparse.BooleanOptionalAction)
    parser.add_argument("--item-type", default="")
    parser.add_argument("--equip-type", default="")
    parser.add_argument("--archetype", default="")
    parser.add_argument("--item-category", default="")
    parser.add_argument(
        "--stat",
        action="append",
        type=stat_filter,
        default=[],
        metavar="TYPE=VALUE",
        help=(
            "require a base stat minimum; repeat for All matching, e.g. "
            "--stat Int=3 --stat Matk=2 --stat Matk%%=2"
        ),
    )
    parser.add_argument(
        "--over",
        type=int,
        default=50_000,
        help="also list entries above this unit price (default: 50000)",
    )
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument(
        "--json", action="store_true", help="print the complete result JSON"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the request without writing it or contacting the game",
    )
    return parser


def build_request(args: argparse.Namespace) -> dict[str, Any]:
    if args.page_size > 100:
        raise ValueError("--page-size must be at most 100")
    if args.timeout <= 0:
        raise ValueError("--timeout must be greater than zero")

    timestamp_ms = time.time_ns() // 1_000_000
    request: dict[str, Any] = {
        "schema_version": 1,
        "request_id": time.time_ns() // 1_000,
        "timestamp_ms": timestamp_ms,
        "query": args.query,
        "cursor": args.cursor,
        "page_size": args.page_size,
    }
    optional = {
        "minimum_unit_price": args.min_price,
        "maximum_unit_price": args.max_price,
        "minimum_level": args.min_level,
        "maximum_level": args.max_level,
        "minimum_refine": args.min_refine,
        "maximum_refine": args.max_refine,
        "minimum_potential": args.min_potential,
        "maximum_potential": args.max_potential,
        "minimum_quantity": args.min_quantity,
        "has_gem": args.has_gem,
        "has_card": args.has_card,
    }
    request.update({key: value for key, value in optional.items() if value is not None})
    strings = {
        "item_type": args.item_type,
        "equip_type": args.equip_type,
        "archetype": args.archetype,
        "item_category": args.item_category,
    }
    request.update({key: value for key, value in strings.items() if value})
    if args.stat:
        if len(args.stat) > 6:
            raise ValueError("at most six --stat filters are supported")
        request["stat_match_mode"] = "All"
        request["stat_filters"] = args.stat
    return request


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


@contextmanager
def auction_ipc_lock():
    """Keep a standalone CLI request from colliding with embedded requests."""

    AUCTION_IPC_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock_file = AUCTION_IPC_LOCK_PATH.open("a+b")
    locked = False
    try:
        if lock_file.seek(0, os.SEEK_END) == 0:
            lock_file.write(b"0")
            lock_file.flush()
        while not locked:
            try:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                locked = True
            except OSError:
                time.sleep(0.05)
        yield
    finally:
        if locked:
            try:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        lock_file.close()


def read_result(
    request_id: int,
    timeout: float,
    *,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    saw_pending = False
    while time.monotonic() < deadline:
        if cancel_check is not None and cancel_check():
            raise InterruptedError("Auction query cancelled")
        try:
            result = json.loads(RESULT_PATH.read_text(encoding="utf-8-sig"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            time.sleep(0.05)
            continue
        if result.get("request_id") != request_id:
            time.sleep(0.05)
            continue
        status = str(result.get("status", ""))
        if status == "pending":
            saw_pending = True
            time.sleep(0.05)
            continue
        return result
    detail = (
        "the game accepted the request but did not return a result"
        if saw_pending
        else "probe v2.16.0 did not accept the request"
    )
    raise TimeoutError(
        f"Auction query timed out: {detail}. Check that the game is logged in "
        "and BepInEx loaded SpiritVale Position Probe 2.16.0."
    )


def item_price(item: dict[str, Any]) -> int:
    try:
        return int(item.get("unit_price", 0))
    except (TypeError, ValueError):
        return 0


def format_item(item: dict[str, Any]) -> str:
    name = str(item.get("item_display_name") or item.get("item_id") or "(unknown)")
    seller = str(item.get("seller_name") or item.get("seller_id") or "(unknown)")
    quantity = item.get("available_quantity", 0)
    return f"{item_price(item):>12,}  x{quantity:<4}  {name}  [{seller}]"


def print_summary(result: dict[str, Any], threshold: int) -> None:
    items = [item for item in result.get("items", []) if isinstance(item, dict)]
    items.sort(key=item_price)
    print(
        f"查詢：{result.get('query', '')}｜結果 {len(items)} 筆｜"
        f"success={result.get('success', False)}"
    )
    if result.get("message"):
        print(f"伺服器訊息：{result['message']}")
    filters = result.get("stat_filters", [])
    if filters:
        rendered = ", ".join(
            f"{entry.get('type')} >= {entry.get('minimum_value')}"
            for entry in filters
            if isinstance(entry, dict)
        )
        print(f"基礎能力條件（全部符合）：{rendered}")
    if items:
        print("\n價格（由低到高）：")
        for item in items:
            print(format_item(item))
        print(f"\n最低單價：{item_price(items[0]):,}")
    else:
        print("沒有符合條件的上架項目。")

    expensive = [item for item in items if item_price(item) > threshold]
    print(f"\n單價超過 {threshold:,}：{len(expensive)} 筆")
    for item in expensive:
        print(format_item(item))
    if result.get("has_more"):
        print(f"\n尚有下一頁；cursor：{result.get('next_cursor', '')}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        request = build_request(args)
    except ValueError as error:
        parser.error(str(error))

    if args.dry_run:
        print(json.dumps(request, ensure_ascii=False, indent=2))
        return 0

    try:
        request_probe_load()
        with auction_ipc_lock():
            atomic_write_json(REQUEST_PATH, request)
            result = read_result(request["request_id"], args.timeout)
    except (TimeoutError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_summary(result, args.over)
    return 0 if result.get("status") == "ok" and result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
