"""Summon, buff, mount, and job-specific skill timing policies."""

from __future__ import annotations

from typing import Callable
import random
from spiritvale_config import (
    BotConfig,
    NAVIGATION_ATTACK_KEYS_BY_JOB_TYPE,
    NAVIGATION_UPKEEP_JOB_TYPES,
    SUMMONER_BUFF_IDS,
    SUMMONER_CHECK_ORDER,
    SUMMONER_SUMMON_IDS,
    SUMMONER_TARGET_SUMMON_IDS,
)
from spiritvale_models import (
    MemoryPlayer,
    SummonMountKeyState,
    SummonerCheckState,
)


def summon_mount_blocks_navigation(
    config: BotConfig,
    player: MemoryPlayer,
    *,
    send_input: bool,
    active: bool,
) -> bool:
    """Pause movement while Python sends the fixed 9 then 0 key sequence."""
    return bool(
        config.job_type in NAVIGATION_UPKEEP_JOB_TYPES
        and send_input
        and active
        and player.mounted_summon_state_available
        and player.summon_mount_action_available
        and not player.is_mounted_summon
    )


def reset_summon_mount_key_state(state: SummonMountKeyState) -> None:
    state.phase = "idle"
    state.stage_started_at = 0.0
    state.next_mount_retry_at = 0.0
    state.retry_after = 0.0
    state.error = ""


def advance_summon_mount_hotkeys(
    state: SummonMountKeyState,
    *,
    mounted: bool,
    summon_ready: bool,
    enabled: bool,
    now: float,
    reanimation_key: str,
    mount_key: str,
    key_hold_ms: int,
    reanimation_delay_ms: int,
    confirm_timeout_ms: int,
    mount_key_retry_delay_ms: int,
    retry_delay_ms: int,
    press_key: Callable[[str, int], None],
) -> bool:
    """Send reanimation, wait for the summon to exist, then mount.

    ``summon_ready`` reflects whether an active summon actually exists (the
    game's active summon state): only press the mount key once a summon is on
    the field. While waiting for mount confirmation, retry only the mount key at
    ``mount_key_retry_delay_ms`` intervals. The confirmation timeout always runs
    from the first mount-key press; retries do not extend it. If mounting is not
    confirmed, retry_wait re-presses reanimation after ``retry_delay_ms``.
    """
    if not enabled:
        reset_summon_mount_key_state(state)
        return False
    if mounted:
        state.phase = "mounted"
        state.stage_started_at = 0.0
        state.next_mount_retry_at = 0.0
        state.retry_after = 0.0
        state.error = ""
        return False
    if now < state.retry_after:
        state.phase = "retry_wait"
        return True

    try:
        if state.phase in {"idle", "inactive", "mounted", "retry_wait"}:
            press_key(reanimation_key, max(0, int(key_hold_ms)))
            state.phase = "reanimation_sent"
            state.stage_started_at = now
            state.next_mount_retry_at = 0.0
            state.error = ""
        elif state.phase == "reanimation_sent":
            elapsed_ms = (now - state.stage_started_at) * 1000
            if summon_ready and elapsed_ms >= max(0, int(reanimation_delay_ms)):
                press_key(mount_key, max(0, int(key_hold_ms)))
                state.phase = "mount_sent"
                state.stage_started_at = now
                state.next_mount_retry_at = (
                    now + max(0, int(mount_key_retry_delay_ms)) / 1000
                )
                state.error = ""
            elif elapsed_ms >= max(1, int(confirm_timeout_ms)):
                state.phase = "retry_wait"
                state.error = "summon was not ready"
                state.retry_after = now + max(0, int(retry_delay_ms)) / 1000
        elif state.phase == "mount_sent":
            elapsed_ms = (now - state.stage_started_at) * 1000
            if elapsed_ms >= max(1, int(confirm_timeout_ms)):
                state.phase = "retry_wait"
                state.next_mount_retry_at = 0.0
                state.error = "mount was not confirmed"
                state.retry_after = now + max(0, int(retry_delay_ms)) / 1000
            elif summon_ready and now >= state.next_mount_retry_at:
                press_key(mount_key, max(0, int(key_hold_ms)))
                state.next_mount_retry_at = (
                    now + max(0, int(mount_key_retry_delay_ms)) / 1000
                )
    except Exception as error:
        state.phase = "retry_wait"
        state.next_mount_retry_at = 0.0
        state.error = f"{type(error).__name__}: {error}"
        state.retry_after = now + max(0, int(retry_delay_ms)) / 1000
    return True


def summon_mount_wait_status(
    state: SummonMountKeyState, reanimation_key: str = "9", mount_key: str = "0"
) -> str:
    phase = state.phase.strip().upper() or "WAITING"
    error = f" ERROR={state.error}" if state.error else ""
    return f"SUMMON MOUNT {phase} KEY={reanimation_key}->{mount_key}{error}"


def reset_summoner_check_state(state: SummonerCheckState) -> None:
    state.phase = "idle"
    state.item_id = ""
    state.settle_until = 0.0
    state.retry_after.clear()
    state.error = ""


def summoner_checks_enabled(
    config: BotConfig,
    player: MemoryPlayer,
    *,
    send_input: bool,
    active: bool,
    follow_mode: bool,
) -> bool:
    return bool(
        config.job_type in NAVIGATION_UPKEEP_JOB_TYPES
        and send_input
        and (active or follow_mode)
        and player.alive
        and any(
            bool(config.summoner_checks[check_id]["enabled"])
            for check_id in SUMMONER_CHECK_ORDER
        )
    )


def missing_summoner_checks(
    config: BotConfig, player: MemoryPlayer
) -> tuple[tuple[str, ...], str]:
    """Return missing configured IDs and an unavailable-source error."""
    enabled_ids = tuple(
        check_id
        for check_id in SUMMONER_CHECK_ORDER
        if bool(config.summoner_checks[check_id]["enabled"])
    )
    if not enabled_ids:
        return (), ""
    needs_summons = any(item in SUMMONER_SUMMON_IDS for item in enabled_ids)
    needs_buffs = any(
        item in SUMMONER_BUFF_IDS and item != "GuardianBond" for item in enabled_ids
    )
    unavailable: list[str] = []
    if "GuardianBond" in enabled_ids and not player.guardian_bond_available:
        unavailable.append(
            "GuardianBond ownership/bond state unavailable; updated probe required"
            + (f": {player.guardian_bond_error}" if player.guardian_bond_error else "")
        )
    if needs_summons and not player.summon_displays_available:
        unavailable.append(
            "SummonDisplays_C"
            + (
                f": {player.summon_displays_error}"
                if player.summon_displays_error
                else ""
            )
        )
    if needs_buffs and not player.active_statuses_available:
        unavailable.append(
            "StatusDisplays_C"
            + (
                f": {player.active_statuses_error}"
                if player.active_statuses_error
                else ""
            )
        )
    if unavailable:
        return (), "; ".join(unavailable)

    summon_ids = {value.casefold() for value in player.summon_display_skill_ids}
    status_ids = {value.casefold() for value in player.active_status_ids}
    missing = tuple(
        check_id
        for check_id in enabled_ids
        if (
            not player.guardian_bond_active
            if check_id == "GuardianBond"
            else (
                check_id.casefold() not in summon_ids
                if check_id in SUMMONER_SUMMON_IDS
                else check_id.casefold() not in status_ids
            )
        )
    )
    return missing, ""


def summoner_checks_block_navigation(
    config: BotConfig,
    player: MemoryPlayer,
    *,
    send_input: bool,
    active: bool,
    follow_mode: bool,
) -> bool:
    """Gate movement and attacks on confirmed state, not a skill request."""
    return summoner_checks_enabled(
        config, player, send_input=send_input, active=active, follow_mode=follow_mode
    ) and any(missing_summoner_checks(config, player))


def advance_summoner_checks(
    state: SummonerCheckState,
    config: BotConfig,
    player: MemoryPlayer,
    *,
    enabled: bool,
    now: float,
    press_key: Callable[..., bool | None],
) -> bool:
    """Maintain selected summons/buffs and report whether navigation is gated."""
    if not enabled:
        reset_summoner_check_state(state)
        return False

    missing, unavailable_error = missing_summoner_checks(config, player)
    if unavailable_error:
        state.phase = "unavailable"
        state.item_id = ""
        state.error = unavailable_error
        state.settle_until = 0.0
        return True

    present = set(SUMMONER_CHECK_ORDER).difference(missing)
    for check_id in present:
        state.retry_after.pop(check_id, None)
    if not missing:
        state.phase = "ready"
        state.item_id = ""
        state.error = ""
        state.settle_until = 0.0
        return False
    if now < state.settle_until:
        state.phase = "settling"
        if state.item_id == "GuardianBond":
            state.error = player.guardian_bond_cast_error
        return True

    for check_id in missing:
        if now < state.retry_after.get(check_id, 0.0):
            continue
        if check_id == "GuardianBond" and player.guardian_bond_candidate_id <= 0:
            state.phase = "waiting"
            state.item_id = check_id
            state.error = "No living summon owned by the local player"
            continue
        key = str(config.summoner_checks[check_id]["key"])
        try:
            sent = press_key(key, check_id in SUMMONER_TARGET_SUMMON_IDS)
            state.phase = "sent" if sent is not False else "blocked"
            state.error = "" if sent is not False else "skill request was blocked"
        except Exception as error:
            state.phase = "error"
            state.error = f"{type(error).__name__}: {error}"
        state.item_id = check_id
        state.retry_after[check_id] = now + max(
            2500 if check_id == "GuardianBond" else 0,
            int(config.summoner_check_retry_delay_ms),
        ) / 1000
        state.settle_until = now + max(
            2500 if check_id == "GuardianBond" else 0,
            int(config.summoner_check_settle_ms),
        ) / 1000
        return True

    state.phase = "waiting"
    state.item_id = missing[0]
    state.error = (
        ("No living summon owned by the local player"
         if player.guardian_bond_candidate_id <= 0 else player.guardian_bond_cast_error)
        if state.item_id == "GuardianBond" else ""
    )
    return True


def summoner_check_wait_status(state: SummonerCheckState) -> str:
    phase = state.phase.strip().upper() or "WAITING"
    item = f" ITEM={state.item_id}" if state.item_id else ""
    error = f" ERROR={state.error}" if state.error else ""
    return f"SUMMONER CHECK {phase}{item}{error}"


def navigation_attack_keys(config: BotConfig) -> tuple[str, ...]:
    """Return held attack keys for navigation; priest attacks use separate taps."""
    try:
        return NAVIGATION_ATTACK_KEYS_BY_JOB_TYPE[config.job_type]
    except KeyError as error:
        raise ValueError(
            "job_type must be 0 (under level 64), 1 (summoner), or 2 (priest)"
        ) from error


def next_priest_attack_at(now: float, config: BotConfig) -> float:
    """Schedule the next priest Left Shift attack using the configured interval."""
    interval_ms = random.uniform(
        config.priest_left_shift_tap_min_interval_ms,
        config.priest_left_shift_tap_max_interval_ms,
    )
    return now + interval_ms / 1000


# Preserve imports used by older diagnostics; runtime code uses attack semantics.
f8_shift_keys = navigation_attack_keys
next_priest_shift_tap_at = next_priest_attack_at
