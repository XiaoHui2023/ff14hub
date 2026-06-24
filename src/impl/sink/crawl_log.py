from __future__ import annotations

from pathlib import Path

from ff14_the_hunt import HuntCrawlPacket
from ff14_the_hunt.models import HuntMarkRecord
from ff14_the_hunt.locale.names import translate_hunt_name, translate_region
from ff14_the_hunt.locale.tag import HuntDisplayLocale
from rich.console import Group
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from impl.hunt.crawl_state import CrawlStateKey, crawl_packet_state_key, should_emit_crawl_log
from impl.hunt.format import format_crawl_summary_text, format_mark_message_text
from impl.hunt.map_image import render_mark_map_image
from impl.sink.theme import make_console

_TIMER_STYLE = {
    "error": "hunt.timer.error",
    "success": "hunt.timer.success",
    "info": "hunt.timer.info",
    "warning": "hunt.timer.warning",
}


class HuntCrawlLogSink:
    """将单次爬取结果渲染到终端。"""

    def __init__(
        self,
        *,
        locale: HuntDisplayLocale = HuntDisplayLocale.ZH,
        show_next_fetch: bool = True,
        print_every_crawl: bool = False,
    ) -> None:
        self._locale = locale
        self._show_next_fetch = show_next_fetch
        self._print_every_crawl = print_every_crawl
        self._last_state_key: CrawlStateKey | None = None
        self._console = make_console()

    def on_crawl(self, packet: HuntCrawlPacket) -> bool:
        if not should_emit_crawl_log(
            packet,
            previous_key=self._last_state_key,
            print_every_crawl=self._print_every_crawl,
        ):
            return False

        self._last_state_key = crawl_packet_state_key(packet)

        summary = format_crawl_summary_text(
            packet,
            show_next_fetch=self._show_next_fetch,
        )
        self._console.print(Panel(summary, title="🎯 狩猎追踪", border_style="hunt.title"))

        if not packet.marks:
            self._console.print("[hunt.dim]（无匹配记录）[/]")
            return True

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

        return True

    def notify_export(self, bundle_dir: Path) -> None:
        self._console.print(f"[hunt.spawn]📁 已写入 {escape(str(bundle_dir))}[/]")

    def notify_stopped(self) -> None:
        self._console.print("[hunt.dim]已停止[/]")

    def _print_spawn_detail(self, mark: HuntMarkRecord) -> None:
        body_lines: list[object] = [
            Text(format_mark_message_text(mark, locale=self._locale)),
        ]
        map_image = render_mark_map_image(mark, console_width=self._console.width)
        if map_image is not None:
            body_lines.append(map_image)
        self._console.print(
            Panel(
                Group(*body_lines),
                border_style="hunt.spawn",
            ),
        )
