"""Navigation-session timing and gross coin income accounting."""

from __future__ import annotations

from spiritvale_models import (
    NavigationEarningsReport,
    NavigationEarningsState,
)


def start_navigation_earnings(
    state: NavigationEarningsState, *, now: float, tracking: bool = True
) -> None:
    """Start one non-persistent formal-navigation earnings session."""
    state.session_active = True
    state.tracking_active = bool(tracking)
    state.segment_started_at = now if tracking else 0.0
    state.elapsed_seconds = 0.0
    state.gross_income = 0
    state.last_wallet_coins = None
    state.current_wallet_coins = None
    state.last_snapshot_timestamp_ms = 0
    state.wallet_sample_count = 0
    state.data_incomplete = False
    state.final_balance_from_last_sample = False


def pause_navigation_earnings(
    state: NavigationEarningsState, *, now: float
) -> None:
    """Exclude following mode from both elapsed time and wallet sampling."""
    if not state.session_active or not state.tracking_active:
        return
    state.elapsed_seconds += max(0.0, now - state.segment_started_at)
    state.tracking_active = False
    state.segment_started_at = 0.0
    state.last_wallet_coins = None
    state.last_snapshot_timestamp_ms = 0


def resume_navigation_earnings(
    state: NavigationEarningsState, *, now: float
) -> None:
    """Resume navigation after following without bridging wallet deltas."""
    if not state.session_active or state.tracking_active:
        return
    state.tracking_active = True
    state.segment_started_at = now
    state.last_wallet_coins = None
    state.last_snapshot_timestamp_ms = 0


def mark_navigation_earnings_incomplete(
    state: NavigationEarningsState, *, final_balance_from_last_sample: bool = False
) -> None:
    if state.session_active and state.tracking_active:
        state.data_incomplete = True
        if final_balance_from_last_sample:
            state.final_balance_from_last_sample = True


def observe_navigation_wallet(
    state: NavigationEarningsState,
    *,
    snapshot_timestamp_ms: int,
    wallet_coins_available: bool,
    wallet_coins: int = 0,
) -> None:
    """Accumulate positive wallet deltas from each new navigation snapshot."""
    if not state.session_active or not state.tracking_active:
        return
    timestamp_ms = int(snapshot_timestamp_ms)
    if timestamp_ms <= state.last_snapshot_timestamp_ms:
        return
    state.last_snapshot_timestamp_ms = timestamp_ms
    if not wallet_coins_available or type(wallet_coins) is not int or wallet_coins < 0:
        state.data_incomplete = True
        return
    if state.last_wallet_coins is not None and wallet_coins > state.last_wallet_coins:
        state.gross_income += wallet_coins - state.last_wallet_coins
    state.last_wallet_coins = wallet_coins
    state.current_wallet_coins = wallet_coins
    state.wallet_sample_count += 1


def finish_navigation_earnings(
    state: NavigationEarningsState, *, now: float
) -> NavigationEarningsReport | None:
    """Finish once; subsequent stop paths return no duplicate report."""
    if not state.session_active:
        return None
    pause_navigation_earnings(state, now=now)
    report = NavigationEarningsReport(
        elapsed_seconds=state.elapsed_seconds,
        gross_income=state.gross_income,
        current_wallet_coins=state.current_wallet_coins,
        wallet_sample_count=state.wallet_sample_count,
        data_incomplete=state.data_incomplete,
        final_balance_from_last_sample=state.final_balance_from_last_sample,
    )
    state.session_active = False
    return report


def format_navigation_earnings_report(report: NavigationEarningsReport) -> str:
    total_seconds = max(0, int(report.elapsed_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    if report.wallet_sample_count <= 0 or report.current_wallet_coins is None:
        wallet_text = "金幣總收入 無法計算；目前餘額 無法取得"
    else:
        wallet_text = (
            f"金幣總收入 {report.gross_income:,}；"
            f"目前餘額 {report.current_wallet_coins:,}"
        )
    warning = ""
    if report.data_incomplete:
        warning = "（金幣資料曾中斷，收入可能低估"
        if report.final_balance_from_last_sample and report.current_wallet_coins is not None:
            warning += "；停止餘額採最後有效值"
        warning += "）"
    return f"導航統計：運行 {duration}；{wallet_text}。{warning}"
