from __future__ import annotations

from ff14_the_hunt.locale.names import translate_hunt_name, translate_region
from ff14_the_hunt.locale.tag import HuntDisplayLocale
from ff14_the_hunt.models import HuntCrawlPacket, HuntMarkRecord


def format_mark_message_text(
    mark: HuntMarkRecord,
    *,
    locale: HuntDisplayLocale = HuntDisplayLocale.ZH,
) -> str:
    """将单条狩猎记录排版为纯文本消息。"""
    name = translate_hunt_name(mark.hunt_key, locale)
    region = translate_region(mark.region, locale)
    lines = [
        f"🎯 新检出 · {name}",
        f"世界：{mark.world_name}",
        f"区域：{region}",
    ]
    if mark.trigger_timer is not None:
        lines.append(f"触发：{mark.trigger_timer.summary}")
    if mark.condition_timer is not None:
        lines.append(f"条件：{mark.condition_timer.summary}")
    if mark.fate_timer is not None:
        lines.append(f"FATE：{mark.fate_timer.summary}")
    for point in mark.spawn_points:
        coord = f"{point.point_key} norm=({point.x:.3f}, {point.y:.3f})"
        if point.pixel_x is not None and point.pixel_y is not None:
            coord += f" px=({point.pixel_x:.0f}, {point.pixel_y:.0f})"
        lines.append(f"刷点：{coord}")
    return "\n".join(lines)


def format_crawl_summary_text(
    packet: HuntCrawlPacket,
    *,
    show_next_fetch: bool,
) -> str:
    """单次爬取摘要行。"""
    from datetime import datetime

    crawled = datetime.fromtimestamp(packet.crawled_at).strftime("%Y-%m-%d %H:%M:%S")
    new_count = len(packet.newly_spawned_marks)
    summary = f"爬取 {crawled} · 共 {len(packet.marks)} 条 · 新检出 {new_count} 条"
    if show_next_fetch:
        next_fetch = datetime.fromtimestamp(packet.next_fetch_at).strftime("%Y-%m-%d %H:%M:%S")
        summary += f" · 下次 {next_fetch}"
    return summary
