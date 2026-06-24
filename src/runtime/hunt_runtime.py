from __future__ import annotations

import logging
import signal
from dataclasses import dataclass
from pathlib import Path

from ff14_the_hunt import FF14TheHunt, HuntCrawlPacket, HuntRankKind
from ff14_the_hunt.locale.tag import HuntDisplayLocale

from impl.broadcast.http_notify import HttpSendNotifier
from impl.export.spawn_bundle import write_spawn_bundle
from impl.hunt.onebot_adapt import mark_to_message_payload
from impl.sink.crawl_log import HuntCrawlLogSink

_log = logging.getLogger(__name__)


@dataclass
class AgentSettings:
    data_centers: list[str]
    worlds: list[str]
    rank_kinds: list[HuntRankKind]
    patches: list[str]
    spawn_output: Path | None
    recent_grace_seconds: float
    continuous_poll: bool = True
    broadcast_url: str | None = None
    print_every_crawl: bool = False


class HuntAgentRuntime:
    """注册狩猎爬取回调，驱动日志与新检出导出。"""

    def __init__(self, settings: AgentSettings) -> None:
        self._settings = settings
        self._sink = HuntCrawlLogSink(
            locale=HuntDisplayLocale.ZH,
            show_next_fetch=settings.continuous_poll,
            print_every_crawl=settings.print_every_crawl,
        )
        self._hunt = FF14TheHunt(
            data_centers=settings.data_centers,
            worlds=settings.worlds,
            rank_kinds=settings.rank_kinds,
            patches=settings.patches,
            recent_grace_seconds=settings.recent_grace_seconds,
            include_spawn_maps=True,
        )
        self._hunt.on_crawl(self._on_crawl)
        self._notifier: HttpSendNotifier | None = None
        if settings.broadcast_url is not None:
            self._notifier = HttpSendNotifier(settings.broadcast_url)
            self._notifier.start()
            _log.info("狩猎源 onebot HTTP 推送 %s", settings.broadcast_url)

    @property
    def hunt(self) -> FF14TheHunt:
        return self._hunt

    def run(self) -> None:
        def _on_sigint(_signum: int, _frame: object | None) -> None:
            self._hunt.stop(join=False)

        previous_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, _on_sigint)
        try:
            self._hunt.run()
        finally:
            signal.signal(signal.SIGINT, previous_handler)
        self._sink.notify_stopped()
        self.shutdown()

    def crawl_once(self) -> HuntCrawlPacket:
        return self._hunt.crawl_once()

    def shutdown(self) -> None:
        if self._notifier is not None:
            self._notifier.stop()
            self._notifier = None

    def _on_crawl(self, packet: HuntCrawlPacket) -> None:
        try:
            emitted = self._sink.on_crawl(packet)
            if emitted:
                _log.info(
                    "狩猎爬取完成 marks=%s new=%s",
                    len(packet.marks),
                    len(packet.newly_spawned_marks),
                )
            else:
                _log.debug(
                    "狩猎爬取完成（无新检出，已跳过终端摘要） marks=%s",
                    len(packet.marks),
                )
            for mark in packet.newly_spawned_marks:
                if self._notifier is not None:
                    payload = mark_to_message_payload(
                        mark,
                        locale=HuntDisplayLocale.ZH,
                    )
                    self._notifier.broadcast(payload)
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
        except Exception as exc:
            _log.exception("狩猎展示或导出失败，已跳过本轮：%s", exc)
