"""Continuously buy inexpensive SpiritVale auction cards through the probe."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
import json
import os
from pathlib import Path
import queue
import threading
import time
from typing import Any

from spiritvale_auction_query import auction_ipc_lock
from spiritvale_paths import IPC_DIR, request_probe_load


REQUEST_PATH = IPC_DIR / "spiritvale_card_purchase_request.json"
RESULT_PATH = IPC_DIR / "spiritvale_card_purchase_result.json"
TERMINAL_STATUSES = {
    "ok", "no_match", "budget_exhausted", "error", "timeout", "unknown"
}
MAX_COIN_AMOUNT = 9_223_372_036_854_775_807
PURCHASE_CONFIRMATION = "BULK_BUY_CARD_WITH_RESERVE"
RETRYABLE_REJECTIONS = {
    "alreadysold", "inactive", "itemunavailable", "listingchanged",
    "listinginactive", "listingnotactive", "listingnotfound",
    "listingunavailable", "listingexpired", "listingsold", "notfound",
    "outofstock", "pricechanged", "sold", "soldout", "stalelisting",
    "staleversion",
}


class CardPurchaseOutcomeUnknown(RuntimeError):
    """The server mutation may have finished even though no result arrived."""


def _parse_coin_amount(value: object, *, allow_zero: bool, label: str) -> int:
    normalized = str(value).strip().replace(",", "")
    minimum = 0 if allow_zero else 1
    if not normalized or not normalized.isdecimal():
        qualifier = "大於或等於 0" if allow_zero else "大於 0"
        raise ValueError(f"{label}必須是{qualifier}的整數")
    amount = int(normalized)
    if amount < minimum or amount > MAX_COIN_AMOUNT:
        qualifier = "大於或等於 0" if allow_zero else "大於 0"
        raise ValueError(f"{label}必須是{qualifier}的整數")
    return amount


def parse_reserve_coins(value: object) -> int:
    """Parse the minimum wallet balance, accepting zero and commas."""

    return _parse_coin_amount(value, allow_zero=True, label="保留金額")


def parse_unit_price_limit(value: object) -> int:
    """Parse the strict per-card ceiling, accepting commas."""

    return _parse_coin_amount(value, allow_zero=False, label="單卡價格上限")


def parse_max_unit_price(value: object) -> int:
    """Compatibility alias for older callers."""

    return parse_unit_price_limit(value)


def affordable_quantity(
    balance: int,
    reserve_coins: int,
    unit_price: int,
    available_quantity: int,
) -> int:
    """Return the maximum stack quantity that cannot spend into the reserve."""

    values = (balance, reserve_coins, unit_price, available_quantity)
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        raise TypeError("餘額、保留金額、單價與數量都必須是整數")
    if reserve_coins < 0 or unit_price <= 0 or available_quantity <= 0:
        return 0
    spendable = balance - reserve_coins
    if spendable <= 0:
        return 0
    return min(available_quantity, spendable // unit_price)


def build_request(
    reserve_coins: int,
    unit_price_limit: int,
) -> dict[str, object]:
    reserve = parse_reserve_coins(reserve_coins)
    limit = parse_unit_price_limit(unit_price_limit)
    return {
        "schema_version": 2,
        "request_id": time.time_ns() // 1_000,
        "timestamp_ms": time.time_ns() // 1_000_000,
        "query": "Card",
        "item_type": "Card",
        "reserve_coins": reserve,
        "unit_price_limit_exclusive": limit,
        "confirmation": PURCHASE_CONFIRMATION,
    }


def atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def read_result(
    request_id: int,
    timeout: float,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    latest_status = ""
    reported_status = ""
    while time.monotonic() < deadline:
        try:
            result = json.loads(RESULT_PATH.read_text(encoding="utf-8-sig"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            time.sleep(0.05)
            continue
        if result.get("request_id") != request_id:
            time.sleep(0.05)
            continue
        latest_status = str(result.get("status", ""))
        if latest_status in TERMINAL_STATUSES:
            return result
        if progress_callback is not None and latest_status != reported_status:
            progress_callback(result)
            reported_status = latest_status
        time.sleep(0.05)

    if latest_status == "purchasing":
        raise CardPurchaseOutcomeUnknown(
            "購買結果逾時；交易可能已完成，請檢查背包或交易紀錄。"
            "BOT 不會自動重試。"
        )
    raise TimeoutError("F4 拍賣搜尋逾時；未送出新的購買要求。")


def run_card_purchase_attempt(
    reserve_coins: int,
    unit_price_limit: int,
    timeout: float = 45.0,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Search once and buy at most one listing; never retry an unknown result."""

    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    request = build_request(reserve_coins, unit_price_limit)
    request_probe_load()
    with auction_ipc_lock():
        atomic_write_json(REQUEST_PATH, request)
        return read_result(
            int(request["request_id"]), timeout, progress_callback
        )


@dataclass(frozen=True)
class CardPurchaseState:
    phase: str = "idle"
    message: str = ""
    reserve_coins: int = 0
    unit_price_limit: int = 0
    purchased_quantity: int = 0
    total_spent: int = 0
    current_balance: int | None = None
    last_item_display_name: str = ""
    last_unit_price: int = 0
    last_quantity: int = 0
    last_spent: int = 0
    code: str = ""

    @property
    def max_unit_price(self) -> int:
        return self.unit_price_limit

    @property
    def item_display_name(self) -> str:
        return self.last_item_display_name

    @property
    def unit_price(self) -> int:
        return self.last_unit_price

    @property
    def quantity(self) -> int:
        return self.last_quantity


def _integer(result: dict[str, Any], *names: str) -> int | None:
    for name in names:
        value = result.get(name)
        if isinstance(value, bool) or value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def state_from_result(result: dict[str, Any]) -> CardPurchaseState:
    """Convert one probe response into a non-accumulated display state."""

    status = str(result.get("status", "error"))
    success = status == "ok" and bool(result.get("success", False))
    quantity = max(0, _integer(result, "quantity") or 0)
    unit_price = max(0, _integer(result, "unit_price") or 0)
    spent = max(0, _integer(result, "total_spent") or unit_price * quantity)
    return CardPurchaseState(
        phase="purchased" if success else ("error" if status == "ok" else status),
        message=str(result.get("message", "")),
        reserve_coins=max(0, _integer(result, "reserve_coins") or 0),
        unit_price_limit=max(
            0,
            _integer(result, "unit_price_limit_exclusive", "maximum_unit_price")
            or 0,
        ),
        purchased_quantity=quantity if success else 0,
        total_spent=spent if success else 0,
        current_balance=_integer(
            result, "balance_after", "wallet_coins", "balance_before"
        ),
        last_item_display_name=str(result.get("item_display_name", "")),
        last_unit_price=unit_price,
        last_quantity=quantity if success else 0,
        last_spent=spent if success else 0,
        code=str(result.get("code", "")),
    )


def _rejection_is_retryable(result: dict[str, Any]) -> bool:
    for field in ("code", "reason"):
        raw = str(result.get(field, "")).strip().casefold()
        compact = "".join(character for character in raw if character.isalnum())
        if raw in RETRYABLE_REJECTIONS or compact in RETRYABLE_REJECTIONS:
            return True
    return False


class CardPurchaseController:
    """Continuously issue serialized search/purchase attempts in the background."""

    def __init__(
        self,
        *,
        timeout: float = 45.0,
        poll_interval: float = 1.0,
        runner: Callable[..., dict[str, Any]] = run_card_purchase_attempt,
    ) -> None:
        if timeout <= 0 or poll_interval < 0:
            raise ValueError("timeout must be positive and poll_interval non-negative")
        self.timeout = float(timeout)
        self.poll_interval = float(poll_interval)
        self._runner = runner
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._active = False
        self._stop_event = threading.Event()
        self._updates: queue.SimpleQueue[CardPurchaseState] = queue.SimpleQueue()
        self._state = CardPurchaseState()

    @property
    def running(self) -> bool:
        with self._lock:
            return self._active

    @property
    def state(self) -> CardPurchaseState:
        with self._lock:
            return self._state

    def _publish(self, state: CardPurchaseState) -> None:
        with self._lock:
            self._state = state
            if state.phase in {
                "budget_exhausted", "stopped", "error", "timeout", "unknown"
            }:
                self._active = False
        self._updates.put(state)

    def start(self, reserve_coins: int, unit_price_limit: int) -> bool:
        reserve = parse_reserve_coins(reserve_coins)
        limit = parse_unit_price_limit(unit_price_limit)
        with self._lock:
            if self.running:
                return False
            self._stop_event.clear()
            self._active = True
            initial = CardPurchaseState(
                phase="searching",
                message="正在搜尋符合條件的 Card",
                reserve_coins=reserve,
                unit_price_limit=limit,
            )
            self._state = initial
            self._updates.put(initial)
            self._thread = threading.Thread(
                target=self._run,
                args=(reserve, limit),
                name="SpiritValeCardPurchaseMonitor",
                daemon=True,
            )
            self._thread.start()
            return True

    def _session_state(
        self,
        *,
        phase: str,
        message: str,
        reserve: int,
        limit: int,
        purchased: int,
        spent: int,
        balance: int | None,
        last: CardPurchaseState | None,
        code: str = "",
    ) -> CardPurchaseState:
        return CardPurchaseState(
            phase=phase,
            message=message,
            reserve_coins=reserve,
            unit_price_limit=limit,
            purchased_quantity=purchased,
            total_spent=spent,
            current_balance=balance,
            last_item_display_name=(last.last_item_display_name if last else ""),
            last_unit_price=(last.last_unit_price if last else 0),
            last_quantity=(last.last_quantity if last else 0),
            last_spent=(last.last_spent if last else 0),
            code=code,
        )

    def _run(self, reserve: int, limit: int) -> None:
        purchased = 0
        spent = 0
        balance: int | None = None
        last: CardPurchaseState | None = None
        while not self._stop_event.is_set():
            self._publish(self._session_state(
                phase="searching", message="正在搜尋符合條件的 Card",
                reserve=reserve, limit=limit, purchased=purchased, spent=spent,
                balance=balance, last=last,
            ))
            try:
                def report_progress(progress: dict[str, Any]) -> None:
                    nonlocal balance
                    progress_balance = _integer(
                        progress, "balance_after", "wallet_coins", "balance_before"
                    )
                    if progress_balance is not None:
                        balance = progress_balance
                    stopping = self._stop_event.is_set()
                    status = str(progress.get("status", "searching"))
                    phase = "stopping" if stopping else status
                    message = (
                        "停止中；等待已送出的單筆交易結果。"
                        if stopping
                        else (
                            "正在送出並等待這筆 Card 交易結果"
                            if status == "purchasing"
                            else "正在搜尋符合條件的 Card"
                        )
                    )
                    self._publish(self._session_state(
                        phase=phase, message=message, reserve=reserve,
                        limit=limit, purchased=purchased, spent=spent,
                        balance=balance, last=last,
                    ))

                result = self._runner(
                    reserve_coins=reserve,
                    unit_price_limit=limit,
                    timeout=self.timeout,
                    progress_callback=report_progress,
                )
                attempt = state_from_result(result)
            except CardPurchaseOutcomeUnknown as error:
                self._publish(self._session_state(
                    phase="unknown", message=str(error), reserve=reserve,
                    limit=limit, purchased=purchased, spent=spent,
                    balance=balance, last=last, code="Timeout",
                ))
                return
            except Exception as error:
                self._publish(self._session_state(
                    phase="error", message=str(error), reserve=reserve,
                    limit=limit, purchased=purchased, spent=spent,
                    balance=balance, last=last,
                ))
                return

            if attempt.current_balance is not None:
                balance = attempt.current_balance

            if attempt.phase == "purchased":
                purchased += attempt.purchased_quantity
                spent += attempt.total_spent
                last = attempt
                if balance is None:
                    before = _integer(result, "balance_before")
                    if before is not None:
                        balance = before - attempt.total_spent
                if balance is not None and balance < reserve:
                    self._publish(self._session_state(
                        phase="error",
                        message="實際餘額已低於保留金額，已立即停止。請確認監看期間是否有其他消費。",
                        reserve=reserve, limit=limit, purchased=purchased,
                        spent=spent, balance=balance, last=last,
                        code="ReserveViolated",
                    ))
                    return
                if self._stop_event.is_set():
                    self._publish(self._session_state(
                        phase="stopped",
                        message="已停止；送出中的最後一筆交易已取得結果。",
                        reserve=reserve, limit=limit, purchased=purchased,
                        spent=spent, balance=balance, last=last,
                    ))
                    return
                if balance is not None and balance <= reserve:
                    self._publish(self._session_state(
                        phase="budget_exhausted",
                        message="目前餘額已達保留金額，監看已自動停止。",
                        reserve=reserve, limit=limit, purchased=purchased,
                        spent=spent, balance=balance, last=last,
                    ))
                    return
                self._publish(self._session_state(
                    phase="purchased", message="成交後立即搜尋下一筆 Card",
                    reserve=reserve, limit=limit, purchased=purchased,
                    spent=spent, balance=balance, last=last,
                ))
                continue

            status = str(result.get("status", "error"))
            if status == "budget_exhausted" or (
                balance is not None and balance <= reserve
            ):
                phase = (
                    "error" if balance is not None and balance < reserve
                    else "budget_exhausted"
                )
                message = attempt.message or (
                    "目前餘額低於保留金額，監看已停止。"
                    if phase == "error"
                    else "目前餘額已達保留金額，監看已自動停止。"
                )
                self._publish(self._session_state(
                    phase=phase, message=message, reserve=reserve, limit=limit,
                    purchased=purchased, spent=spent, balance=balance,
                    last=last, code=attempt.code,
                ))
                return

            if status == "no_match" or _rejection_is_retryable(result):
                if self._stop_event.is_set():
                    break
                self._publish(self._session_state(
                    phase="waiting",
                    message=(
                        "目前沒有可買的 Card；1 秒後重新搜尋。"
                        if status == "no_match"
                        else "上架內容已變動；1 秒後重新搜尋。"
                    ),
                    reserve=reserve, limit=limit, purchased=purchased,
                    spent=spent, balance=balance, last=last, code=attempt.code,
                ))
                if self._stop_event.wait(self.poll_interval):
                    break
                continue

            unknown = status in {"timeout", "unknown"} or bool(
                result.get("purchase_may_have_completed", False)
            )
            self._publish(self._session_state(
                phase="unknown" if unknown else "error",
                message=attempt.message or (
                    "購買結果不明，為避免重複成交已停止。"
                    if unknown else "購買未完成，監看已停止。"
                ),
                reserve=reserve, limit=limit, purchased=purchased, spent=spent,
                balance=balance, last=last, code=attempt.code,
            ))
            return

        self._publish(self._session_state(
            phase="stopped", message="已停止監看；沒有建立新的購買要求。",
            reserve=reserve, limit=limit, purchased=purchased, spent=spent,
            balance=balance, last=last,
        ))

    def request_stop(self) -> bool:
        with self._lock:
            if not self._active:
                return False
            self._stop_event.set()
            stopping = replace(
                self._state,
                phase="stopping",
                message="停止中；若交易已送出，將等待這一筆結果且不再新增要求。",
            )
            self._state = stopping
            self._updates.put(stopping)
        return True

    def poll_latest(self) -> CardPurchaseState | None:
        latest: CardPurchaseState | None = None
        while True:
            try:
                latest = self._updates.get_nowait()
            except queue.Empty:
                return latest

    def stop(self, timeout: float = 0.2) -> None:
        self.request_stop()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(max(0.0, float(timeout)))


class CardPurchaseWindow:
    """Persistent non-blocking F4 input and progress window."""

    def __init__(self, controller: CardPurchaseController) -> None:
        self.controller = controller
        self._commands: queue.SimpleQueue[str] = queue.SimpleQueue()
        self._thread: threading.Thread | None = None
        self._thread_lock = threading.Lock()

    def show(self) -> None:
        with self._thread_lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(
                    target=self._ui_main,
                    name="SpiritValeCardPurchaseWindow",
                    daemon=True,
                )
                self._thread.start()
        self._commands.put("show")

    def stop(self) -> None:
        self.controller.request_stop()
        self._commands.put("close")
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(2.0)

    def _ui_main(self) -> None:
        try:
            self._ui_loop()
        finally:
            # Tk variables and callback closures can form cycles.  Collect them
            # here, on the thread that owns Tcl, instead of during interpreter
            # shutdown on the BOT thread.
            import gc

            gc.collect()

    def _ui_loop(self) -> None:
        import tkinter as tk
        from tkinter import messagebox, ttk

        root = tk.Tk()
        root.title("SpiritVale F4 持續限價大量購買 Card")
        root.geometry("520x430")
        root.resizable(False, False)
        root.withdraw()

        reserve_var = tk.StringVar(value="0")
        limit_var = tk.StringVar(value="")
        status_var = tk.StringVar(value="等待設定")
        purchased_var = tk.StringVar(value="0")
        spent_var = tk.StringVar(value="0")
        balance_var = tk.StringVar(value="—")
        last_var = tk.StringVar(value="尚未成交")

        form = ttk.Frame(root, padding=16)
        form.pack(fill="both", expand=True)
        ttk.Label(
            form,
            text="BOT 會保留指定餘額，並持續購買單價嚴格低於上限的 Card。",
            wraplength=475,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))
        ttk.Label(form, text="必須保留的金幣餘額：").grid(
            row=1, column=0, sticky="w", pady=5
        )
        reserve_entry = ttk.Entry(form, textvariable=reserve_var, width=25)
        reserve_entry.grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Label(form, text="單張 Card 價格上限（不含）：").grid(
            row=2, column=0, sticky="w", pady=5
        )
        limit_entry = ttk.Entry(form, textvariable=limit_var, width=25)
        limit_entry.grid(row=2, column=1, sticky="ew", pady=5)
        ttk.Separator(form).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=14
        )
        labels = (
            ("已購數量：", purchased_var), ("總花費：", spent_var),
            ("目前餘額：", balance_var), ("最後成交：", last_var),
            ("執行狀態：", status_var),
        )
        for row, (label, variable) in enumerate(labels, 4):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="nw", pady=4)
            ttk.Label(
                form, textvariable=variable, wraplength=320, justify="left"
            ).grid(row=row, column=1, sticky="w", pady=4)

        buttons = ttk.Frame(form)
        buttons.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(18, 0))

        def start_monitoring() -> None:
            try:
                reserve = parse_reserve_coins(reserve_var.get())
                limit = parse_unit_price_limit(limit_var.get())
            except ValueError as error:
                messagebox.showerror("輸入錯誤", str(error), parent=root)
                return
            if not self.controller.start(reserve, limit):
                status_var.set("大量購買已在執行；請先停止目前工作。")
                return
            refresh_state(force=True)

        def stop_monitoring() -> None:
            if not self.controller.request_stop():
                status_var.set("目前沒有執行中的監看。")

        start_button = ttk.Button(
            buttons, text="開始大量購買", command=start_monitoring
        )
        start_button.pack(side="left")
        stop_button = ttk.Button(buttons, text="停止", command=stop_monitoring)
        stop_button.pack(side="left", padx=10)

        last_rendered: CardPurchaseState | None = None

        def refresh_state(*, force: bool = False) -> None:
            nonlocal last_rendered
            state = self.controller.state
            if not force and state == last_rendered:
                return
            last_rendered = state
            purchased_var.set(f"{state.purchased_quantity:,}")
            spent_var.set(f"{state.total_spent:,}")
            balance_var.set(
                "—" if state.current_balance is None else f"{state.current_balance:,}"
            )
            last_var.set(
                f"{state.last_item_display_name or 'Card'} × {state.last_quantity:,}，"
                f"單價 {state.last_unit_price:,}，花費 {state.last_spent:,}"
                if state.last_quantity > 0 else "尚未成交"
            )
            status_var.set(state.message or state.phase)
            active = self.controller.running
            entry_state = "disabled" if active else "normal"
            reserve_entry.configure(state=entry_state)
            limit_entry.configure(state=entry_state)
            start_button.configure(state="disabled" if active else "normal")
            stop_button.configure(state="normal" if active else "disabled")

        def close_window() -> None:
            self.controller.request_stop()
            root.destroy()

        ttk.Button(buttons, text="關閉", command=close_window).pack(side="right")
        form.columnconfigure(1, weight=1)
        root.protocol("WM_DELETE_WINDOW", close_window)

        def poll() -> None:
            while True:
                try:
                    command = self._commands.get_nowait()
                except queue.Empty:
                    break
                if command == "show":
                    root.deiconify()
                    root.lift()
                    root.attributes("-topmost", True)
                    root.after(300, lambda: root.attributes("-topmost", False))
                    limit_entry.focus_set()
                elif command == "close":
                    close_window()
                    return
            refresh_state()
            root.after(100, poll)

        refresh_state(force=True)
        root.after(50, poll)
        root.mainloop()
