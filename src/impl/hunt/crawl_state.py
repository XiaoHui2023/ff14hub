from __future__ import annotations

from ff14_the_hunt import HuntCrawlPacket
from ff14_the_hunt.models import HuntMarkRecord, SpawnWindowPhase, TimerDisplay

CrawlStateKey = tuple[tuple[object, ...], ...]


def _timer_phase(timer: TimerDisplay | None) -> SpawnWindowPhase | None:
    if timer is None:
        return None
    return timer.phase


def mark_window_state_key(mark: HuntMarkRecord) -> tuple[object, ...]:
    """单条狩猎的窗口状态指纹，不含倒计时秒数与 summary。"""
    return (
        mark.hunt_key,
        mark.world_name,
        mark.last_death_time,
        mark.last_mark_time,
        mark.missing_counter,
        _timer_phase(mark.trigger_timer),
        _timer_phase(mark.condition_timer),
        _timer_phase(mark.fate_timer),
        mark.recently_spawned,
    )


def crawl_packet_state_key(packet: HuntCrawlPacket) -> CrawlStateKey:
    """整包狩猎记录的状态指纹，按单条指纹排序后组成元组。"""
    return tuple(sorted(mark_window_state_key(mark) for mark in packet.marks))


def should_emit_crawl_log(
    packet: HuntCrawlPacket,
    last_state_key: CrawlStateKey | None,
) -> bool:
    """是否应向终端输出本轮爬取摘要。

    Args:
        packet: 本轮爬取结果。
        last_state_key: 上一轮已打印时的 ``crawl_packet_state_key``；首轮为 ``None``。

    Returns:
        新检出、首轮，或窗口阶段等指纹变化时为 ``True``。
    """
    if packet.newly_spawned_marks:
        return True
    if last_state_key is None:
        return True
    return crawl_packet_state_key(packet) != last_state_key
