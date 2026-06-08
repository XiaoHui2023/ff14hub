from __future__ import annotations

import logging
import signal
import threading

from config import (
    HubConfig,
    hub_config_to_hunt_settings,
    hub_config_to_news_settings,
)
from runtime.hunt_runtime import HuntAgentRuntime
from runtime.news_runtime import create_news_runtime

_log = logging.getLogger(__name__)


class HubRuntime:
    """按配置启动各独立信息源，彼此无共享状态。"""

    def __init__(self, config: HubConfig) -> None:
        self._config = config
        self._hunt: HuntAgentRuntime | None = None
        if config.hunt is not None and config.hunt.enabled:
            self._hunt = HuntAgentRuntime(hub_config_to_hunt_settings(config))
        self._news: NewsAgentRuntime | None = None
        if config.news is not None and config.news.enabled:
            self._news = create_news_runtime(hub_config_to_news_settings(config))
        if self._hunt is None and self._news is None:
            raise ValueError("未启用任何信息源（hunt / news 均未配置或 enabled: false）")
        self._news_thread: threading.Thread | None = None
        _log.info(
            "ff14hub 启动 hunt=%s news=%s once=%s",
            self._hunt is not None,
            self._news is not None,
            config.once,
        )

    def crawl_once(self) -> None:
        try:
            if self._hunt is not None:
                self._hunt.crawl_once()
            if self._news is not None:
                self._news.crawl_once()
        finally:
            if self._hunt is not None:
                self._hunt.shutdown()
            if self._news is not None:
                self._news.shutdown()

    def run(self) -> None:
        if self._news is not None:
            self._news_thread = threading.Thread(
                target=self._run_news,
                daemon=True,
                name="ff14hub-news",
            )
            self._news_thread.start()

        previous_handler = signal.getsignal(signal.SIGINT)

        def _on_sigint(_signum: int, _frame: object | None) -> None:
            if self._hunt is not None:
                self._hunt.hunt.stop(join=False)
            if self._news is not None:
                self._news.stop()

        signal.signal(signal.SIGINT, _on_sigint)
        try:
            if self._hunt is not None:
                self._hunt.run()
            elif self._news_thread is not None:
                self._news_thread.join()
        finally:
            signal.signal(signal.SIGINT, previous_handler)
            if self._news is not None:
                self._news.stop()
                if self._news_thread is not None:
                    self._news_thread.join(timeout=30.0)

    def _run_news(self) -> None:
        if self._news is None:
            return
        self._news.run()
