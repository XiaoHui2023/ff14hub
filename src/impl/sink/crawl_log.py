from __future__ import annotations

from datetime import datetime

from pathlib import Path

from ff14_the_hunt import HuntCrawlPacket, mark_to_display_dict
from ff14_the_hunt.models import HuntMarkRecord
from ff14_the_hunt.locale.names import translate_hunt_name, translate_region
from ff14_the_hunt.locale.tag import HuntDisplayLocale
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from impl.sink.theme import make_console

_TIMER_STYLE = {
    "error": "hunt.timer.error",
    "success": "hunt.timer.success",
    "info": "hunt.timer.info",
    "warning": "hunt.timer.warning",
}


class HuntCrawlLogSink:
    """将单次爬取结果渲染到终端。"""

    def __init__(self, *, locale: HuntDisplayLocale = HuntDisplayLocale.ZH) -> None:
        self._locale = locale
        self._console = make_console()

    def on_crawl(self, packet: HuntCrawlPacket) -> None:
        crawled = datetime.fromtimestamp(packet.crawled_at).strftime("%Y-%m-%d %H:%M:%S")
        new_count = len(packet.newly_spawned_marks)
        summary = (
            f"爬取 {crawled} · 共 {len(packet.marks)} 条"
            f" · 新检出 {new_count} 条"
        )
        self._console.print(Panel(summary, title="🎯 狩猎追踪", border_style="hunt.title"))

        if not packet.marks:
            self._console.print("[hunt.dim]（无匹配记录）[/]")
            return

        table = Table(show_header=True, header_style="hunt.dim", expand=True)
        table.add_column("狩猎", style="hunt.title")
        table.add_column("世界", style="hunt.world")
        table.add_column("区域", style="hunt.region")
        table.add_column("触发", overflow="fold")
        table.add_column("状态", justify="center")

        for mark in packet.marks:
            name = translate_hunt_name(mark.hunt_key, self._locale)
            region = translate_region(mark.region, self._locale)
            trigger_text = Text("—", style="hunt.dim")
            if mark.trigger_timer is not None:
                timer = mark.trigger_timer
                style = _TIMER_STYLE.get(timer.bar_color.value, "hunt.dim")
                trigger_text = Text(timer.summary, style=style)

            status = Text("—", style="hunt.dim")
            if mark.newly_spawned:
                status = Text("新检出", style="bold hunt.new")
            elif mark.recently_spawned:
                status = Text("宽限内", style="hunt.spawn")

            table.add_row(
                escape(name),
                escape(mark.world_name),
                escape(region),
                trigger_text,
                status,
            )

        self._console.print(table)

        for mark in packet.newly_spawned_marks:
            self._print_spawn_detail(mark)

    def notify_export(self, bundle_dir: Path) -> None:
        self._console.print(f"[hunt.spawn]📁 已写入 {escape(str(bundle_dir))}[/]")

    def _print_spawn_detail(self, mark: HuntMarkRecord) -> None:
        display = mark_to_display_dict(
            mark,
            locale=self._locale,
            embed_region_map_data=False,
        )
        name = str(display.get("狩猎名") or display.get("hunt_name") or mark.hunt_key)
        lines = [f"[bold hunt.new]✨ {escape(name)}[/] · {escape(mark.world_name)}"]
        if mark.spawn_points:
            for point in mark.spawn_points:
                px = point.pixel_x
                py = point.pixel_y
                coord = (
                    f"{point.point_key} "
                    f"norm=({point.x:.3f}, {point.y:.3f})"
                )
                if px is not None and py is not None:
                    coord += f" px=({px:.0f}, {py:.0f})"
                lines.append(f"  [hunt.spawn]📍 {escape(coord)}[/]")
        self._console.print(Panel("\n".join(lines), border_style="hunt.spawn"))
