from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ff14_the_hunt import FF14TheHunt, HuntCrawlPacket, HuntRankKind
from ff14_the_hunt.locale.tag import HuntDisplayLocale

from impl.export.spawn_bundle import write_spawn_bundle
from impl.sink.crawl_log import HuntCrawlLogSink


@dataclass
class AgentSettings:
    data_centers: list[str]
    worlds: list[str]
    rank_kinds: list[HuntRankKind]
    patches: list[str]
    spawn_output: Path | None
    recent_grace_seconds: float


class HuntAgentRuntime:
    """注册狩猎爬取回调，驱动日志与新检出导出。"""

    def __init__(self, settings: AgentSettings) -> None:
        self._settings = settings
        self._sink = HuntCrawlLogSink(locale=HuntDisplayLocale.ZH)
        self._hunt = FF14TheHunt(
            data_centers=settings.data_centers,
            worlds=settings.worlds,
            rank_kinds=settings.rank_kinds,
            patches=settings.patches,
            recent_grace_seconds=settings.recent_grace_seconds,
            include_spawn_maps=True,
        )
        self._hunt.on_crawl(self._on_crawl)

    @property
    def hunt(self) -> FF14TheHunt:
        return self._hunt

    def run(self) -> None:
        self._hunt.run()

    def crawl_once(self) -> HuntCrawlPacket:
        return self._hunt.crawl_once()

    def _on_crawl(self, packet: HuntCrawlPacket) -> None:
        self._sink.on_crawl(packet)
        output_root = self._settings.spawn_output
        if output_root is None:
            return
        for mark in packet.newly_spawned_marks:
            bundle_dir = write_spawn_bundle(
                output_root,
                packet=packet,
                mark=mark,
            )
            self._sink.notify_export(bundle_dir)
