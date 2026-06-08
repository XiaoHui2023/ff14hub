from __future__ import annotations

from datetime import datetime, timezone

from ff14_news.models import NewsArticle, NewsFeedBundle


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def select_articles_in_window(
    bundle: NewsFeedBundle,
    *,
    window_start: datetime,
    window_end: datetime,
) -> list[NewsArticle]:
    """保留发布时间在 (window_start, window_end] 内的文章，按发布时间升序。"""
    start = _to_utc(window_start)
    end = _to_utc(window_end)
    selected: list[NewsArticle] = []
    for feed in bundle.feeds.values():
        for article in feed.articles:
            published = _to_utc(article.publish_date)
            if start < published <= end:
                selected.append(article)
    selected.sort(key=lambda item: _to_utc(item.publish_date))
    return selected
