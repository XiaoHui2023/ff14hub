from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from ff14_news import FF14News
from ff14_news.channels.cn_weibo.exceptions import WeiboAccessError

from impl.broadcast.onebot_port import OnebotPortBroadcaster
from impl.news.onebot_adapt import article_to_message_payload
from impl.news.window import select_articles_in_window
from impl.sink.news_feed_log import NewsFeedLogSink

_log = logging.getLogger(__name__)


@dataclass
class NewsAgentSettings:
    poll_interval_seconds: float
    limit_per_channel: int
    broadcast_port: int | None
    continuous_poll: bool
    enable_cn_official: bool = True
    enable_cn_weibo: bool = True
    enable_jp_official: bool = True
    cn_weibo_cookie: str | None = None
    cn_weibo_cookie_storage_path: Path | None = None


def create_news_runtime(settings: NewsAgentSettings) -> NewsAgentRuntime:
    """构造新闻运行时；官方微博缺 Playwright 时降级为跳过该渠道。"""
    try:
        return NewsAgentRuntime(settings)
    except WeiboAccessError as exc:
        if not settings.enable_cn_weibo:
            raise
        _log.warning("官方微博需要 Playwright Chromium，已跳过该渠道：%s", exc)
        return NewsAgentRuntime(replace(settings, enable_cn_weibo=False))


class NewsAgentRuntime:
    """按固定间隔抓取 FF14 新闻，终端展示并可选 onebot 端口广播。"""

    def __init__(self, settings: NewsAgentSettings) -> None:
        self._settings = settings
        self._started_at = datetime.now(timezone.utc)
        self._last_crawl_at = self._started_at
        self._stop = threading.Event()
        self._news = FF14News(
            enable_cn_official=settings.enable_cn_official,
            enable_cn_weibo=settings.enable_cn_weibo,
            enable_jp_official=settings.enable_jp_official,
            cn_weibo_cookie=settings.cn_weibo_cookie,
            cn_weibo_cookie_storage_path=settings.cn_weibo_cookie_storage_path,
        )
        channel_map = {
            channel_id: self._news.channel(channel_id)
            for channel_id in self._news.available_channels()
        }
        self._sink = NewsFeedLogSink(channels=channel_map)
        self._broadcaster: OnebotPortBroadcaster | None = None
        if settings.broadcast_port is not None:
            self._broadcaster = OnebotPortBroadcaster(settings.broadcast_port)
            self._broadcaster.start()
            _log.info("新闻源 onebot 广播端口 %s", settings.broadcast_port)

    def stop(self) -> None:
        self._stop.set()

    def shutdown(self) -> None:
        if self._broadcaster is not None:
            self._broadcaster.stop()
            self._broadcaster = None

    def crawl_once(self) -> int:
        window_start = self._last_crawl_at
        crawl_time = datetime.now(timezone.utc)
        bundle = self._news.fetch_articles(limit=self._settings.limit_per_channel)
        new_articles = select_articles_in_window(
            bundle,
            window_start=window_start,
            window_end=crawl_time,
        )
        self._last_crawl_at = crawl_time
        _log.info(
            "新闻爬取完成 new=%s errors=%s",
            len(new_articles),
            len(bundle.errors),
        )

        crawled_text = crawl_time.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        next_fetch_text: str | None = None
        if self._settings.continuous_poll:
            next_at = crawl_time.timestamp() + self._settings.poll_interval_seconds
            next_fetch_text = datetime.fromtimestamp(next_at).strftime("%Y-%m-%d %H:%M:%S")

        self._sink.on_crawl_summary(
            crawled_at_text=crawled_text,
            new_count=len(new_articles),
            next_fetch_text=next_fetch_text,
        )
        if bundle.errors:
            self._sink.on_bundle_errors(bundle.errors)
        if new_articles:
            self._sink.on_articles(new_articles)
        for article in new_articles:
            channel = self._news.channel(article.channel_id)
            payload = article_to_message_payload(
                article,
                display_name=channel.display_name,
            )
            if self._broadcaster is not None:
                self._broadcaster.broadcast(payload)
        return len(new_articles)

    def run(self) -> None:
        try:
            while not self._stop.is_set():
                try:
                    self.crawl_once()
                except Exception as exc:
                    _log.exception("新闻爬取失败，下轮间隔后重试：%s", exc)
                if not self._settings.continuous_poll:
                    break
                if self._stop.wait(timeout=self._settings.poll_interval_seconds):
                    break
        finally:
            self._sink.notify_stopped()
            self.shutdown()
