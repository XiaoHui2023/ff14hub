from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ff14_the_hunt import HuntCrawlPacket, HuntQueryFilter
from ff14_the_hunt.bear_tracker.timer_theme import build_timer_display
from ff14_the_hunt.models import (
    HuntMarkRecord,
    SpawnWindowPhase,
    TimerBarColor,
    TimerKind,
)

from impl.hunt.crawl_state import (
    crawl_packet_state_key,
    mark_window_state_key,
    should_emit_crawl_log,
)


def _almost_open_mark(*, remaining_seconds: float, summary: str) -> HuntMarkRecord:
    return HuntMarkRecord(
        hunt_key="hunt_a",
        hunt_name="Hunt A",
        world_name="静语庄园",
        last_death_time=1_700_000_000.0,
        trigger_timer=build_timer_display(
            kind=TimerKind.TRIGGER,
            phase=SpawnWindowPhase.ALMOST_OPEN,
            bar_color=TimerBarColor.ERROR,
            counts_up=False,
            remaining_seconds=remaining_seconds,
            summary=summary,
        ),
    )


def _packet(*marks: HuntMarkRecord) -> HuntCrawlPacket:
    return HuntCrawlPacket(
        crawled_at=1_700_000_100.0,
        next_fetch_at=1_700_000_700.0,
        marks=list(marks),
        query=HuntQueryFilter(),
    )


def test_mark_window_state_key_ignores_remaining_seconds() -> None:
    mark_a = _almost_open_mark(remaining_seconds=900.0, summary="15:00")
    mark_b = _almost_open_mark(remaining_seconds=600.0, summary="10:00")
    assert mark_window_state_key(mark_a) == mark_window_state_key(mark_b)


def test_should_emit_crawl_log_first_time() -> None:
    packet = _packet(_almost_open_mark(remaining_seconds=900.0, summary="15:00"))
    assert should_emit_crawl_log(packet, None) is True


def test_should_emit_crawl_log_suppresses_unchanged_window_state() -> None:
    packet = _packet(_almost_open_mark(remaining_seconds=900.0, summary="15:00"))
    last_key = crawl_packet_state_key(packet)
    later = _packet(_almost_open_mark(remaining_seconds=600.0, summary="10:00"))
    assert should_emit_crawl_log(later, last_key) is False


def test_should_emit_crawl_log_emits_on_phase_change() -> None:
    packet = _packet(_almost_open_mark(remaining_seconds=900.0, summary="15:00"))
    last_key = crawl_packet_state_key(packet)
    opened = HuntMarkRecord(
        hunt_key="hunt_a",
        hunt_name="Hunt A",
        world_name="静语庄园",
        last_death_time=1_700_000_000.0,
        trigger_timer=build_timer_display(
            kind=TimerKind.TRIGGER,
            phase=SpawnWindowPhase.OPEN,
            bar_color=TimerBarColor.SUCCESS,
            counts_up=False,
            remaining_seconds=3600.0,
            summary="开窗中",
        ),
    )
    changed = _packet(opened)
    assert should_emit_crawl_log(changed, last_key) is True


def test_should_emit_crawl_log_always_emits_for_newly_spawned() -> None:
    packet = _packet(_almost_open_mark(remaining_seconds=900.0, summary="15:00"))
    last_key = crawl_packet_state_key(packet)
    spawned = _almost_open_mark(remaining_seconds=900.0, summary="15:00")
    spawned.newly_spawned = True
    fresh = _packet(spawned)
    assert should_emit_crawl_log(fresh, last_key) is True
