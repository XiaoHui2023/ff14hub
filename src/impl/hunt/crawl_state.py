from __future__ import annotations

from ff14_the_hunt import HuntCrawlPacket
from ff14_the_hunt.models import HuntMarkRecord, SpawnWindowPhase, TimerDisplay

CrawlStateKey = tuple[tuple[object, ...], ...]


def _timer_window_state(timer: TimerDisplay | None) -> tuple[object, ...]:
    """单条计时器的窗口指纹：阶段与开窗进度是否已达 100%。"""
    if timer is None:
        return (None,)
    phase = timer.phase
    reached_full: bool | None = None
    if phase == SpawnWindowPhase.OPEN:
        if timer.progress_percent is not None:
            reached_full = timer.progress_percent >= 100.0
        else:
            reached_full = False
    return (phase, reached_full)


def mark_window_state_key(mark: HuntMarkRecord) -> tuple[object, ...]:
    """单条狩猎的窗口状态指纹，不含倒计时秒数与 summary。"""
    return (
        mark.hunt_key,
        mark.world_name,
        mark.last_death_time,
        mark.last_mark_time,
        mark.missing_counter,
        _timer_window_state(mark.trigger_timer),
        _timer_window_state(mark.condition_timer),
        _timer_window_state(mark.fate_timer),
        mark.recently_spawned,
    )


def crawl_packet_state_key(packet: HuntCrawlPacket) -> CrawlStateKey:
    """整包狩猎记录的状态指纹，按单条指纹排序后组成元组。"""
    return tuple(sorted(mark_window_state_key(mark) for mark in packet.marks))


def should_emit_crawl_log(
    packet: HuntCrawlPacket,
    *,
    previous_key: CrawlStateKey | None,
    print_every_crawl: bool = False,
) -> bool:
    """是否应向终端输出本轮爬取摘要。

    Args:
        packet: 本轮爬取结果。
        previous_key: 上一轮已打印时的整包状态指纹；首轮为 ``None``。
        print_every_crawl: 为 ``True`` 时每轮都打印，用于调试。

    Returns:
        需要打印时为 ``True``。
    """
    if print_every_crawl:
        return True
    state_key = crawl_packet_state_key(packet)
    if previous_key is None:
        return True
    if state_key != previous_key:
        return True
    return bool(packet.newly_spawned_marks)
