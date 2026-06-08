from __future__ import annotations

import urllib.error
import urllib.request
from io import BytesIO

from ff14_news.channel_protocol import NewsChannel
from ff14_news.models import NewsArticle, NewsChannelFetchError
from rich.console import Console, Group, RenderableType
from rich.markup import escape
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from textual_image.renderable import Image as TerminalImage

_USER_AGENT = "Mozilla/5.0 (compatible; ff14hub-news-sink/0.1)"
_PANEL_HORIZONTAL_PADDING = 6
_URL_UPGRADE_PAIRS = (
    ("/orj180/", "/orj1080/"),
    ("/orj360/", "/orj1080/"),
    ("/orj480/", "/orj1080/"),
    ("/thumbnail/", "/large/"),
    ("/bmiddle/", "/large/"),
    ("wap360", "large"),
    ("square", "large"),
)
_CHANNEL_BORDER: dict[str, str] = {
    "cn_official": "#61afef",
    "cn_weibo": "#e5c07b",
    "jp_official": "#98c379",
}
_NEWS_THEME = Theme(
    {
        "news.sender": "#abb2bf",
        "news.time": "#5c6370",
        "news.title": "#e5e5e5",
        "news.summary": "#c8c8c8",
        "news.link": "#61afef",
        "news.error": "#e06c75",
        "news.hint": "#5c6370",
        "news.dim": "#5c6370",
    }
)


def _make_console() -> Console:
    return Console(
        theme=_NEWS_THEME,
        color_system="truecolor",
        force_terminal=True,
        legacy_windows=False,
    )


class NewsFeedLogSink:
    """将新闻抓取结果以聊天样式渲染到终端（含头图）。"""

    def __init__(self, *, channels: dict[str, NewsChannel]) -> None:
        self._channels = channels
        self._console = _make_console()

    def on_crawl_summary(
        self,
        *,
        crawled_at_text: str,
        new_count: int,
        next_fetch_text: str | None,
    ) -> None:
        summary = f"爬取 {crawled_at_text} · 新增 {new_count} 条"
        if next_fetch_text is not None:
            summary += f" · 下次 {next_fetch_text}"
        self._console.print(
            Panel(summary, title="📰 FF14 新闻", border_style="news.link"),
        )

    def on_bundle_errors(self, errors: list[NewsChannelFetchError]) -> None:
        for err in errors:
            channel = self._channels.get(err.channel_id)
            name = channel.display_name if channel is not None else err.channel_id
            self._console.print(
                Panel(
                    Text(err.message, style="news.error"),
                    title=f"[news.sender]{escape(name)}[/]",
                    border_style=_CHANNEL_BORDER.get(err.channel_id, "#5c6370"),
                ),
            )

    def on_articles(self, articles: list[NewsArticle]) -> None:
        for article in articles:
            channel = self._channels.get(article.channel_id)
            display_name = channel.display_name if channel is not None else article.channel_id
            self._console.print(
                self._render_article_message(
                    article,
                    display_name,
                    article.channel_id,
                ),
            )

    def notify_stopped(self) -> None:
        self._console.print("[news.dim]新闻源已停止[/]")

    def _render_article_message(
        self,
        article: NewsArticle,
        display_name: str,
        channel_id: str,
    ) -> RenderableType:
        time_text = article.publish_date.strftime("%Y-%m-%d %H:%M")
        header = Text.assemble(
            (display_name, "news.sender"),
            ("  ", ""),
            (time_text, "news.time"),
        )
        body_lines: list[RenderableType] = [
            Text(article.title, style="news.title bold"),
        ]
        if article.summary:
            body_lines.append(Text(article.summary, style="news.summary"))
        cover = self._render_cover_image(article.cover_image_url)
        if cover is not None:
            body_lines.append(cover)
        elif article.cover_image_url:
            body_lines.append(
                Text(f"头图：{article.cover_image_url}", style="news.hint"),
            )
        body_lines.append(Text(article.source_page_url, style="news.link underline"))
        border = _CHANNEL_BORDER.get(channel_id, "#5c6370")
        return Panel(
            Group(*body_lines),
            title=header,
            border_style=border,
            padding=(0, 1),
        )

    def _render_cover_image(self, url: str | None) -> RenderableType | None:
        if not url:
            return None
        display_url = _upgrade_display_image_url(url)
        data = _download_image_bytes(display_url)
        if data is None and display_url != url:
            data = _download_image_bytes(url)
        if data is None:
            return None
        try:
            cell_width = max(48, self._console.width - _PANEL_HORIZONTAL_PADDING)
            return TerminalImage(
                BytesIO(data),
                width=cell_width,
                height="auto",
            )
        except Exception:
            return None


def _upgrade_display_image_url(url: str) -> str:
    for small, large in _URL_UPGRADE_PAIRS:
        if small in url:
            return url.replace(small, large, 1)
    return url


def _download_image_bytes(url: str) -> bytes | None:
    headers: dict[str, str] = {"User-Agent": _USER_AGENT}
    if "sinaimg.cn" in url or "weibocdn.com" in url:
        headers["Referer"] = "https://m.weibo.cn/"
    request = urllib.request.Request(url, headers=headers)
    try:
        return urllib.request.urlopen(request, timeout=120).read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None
