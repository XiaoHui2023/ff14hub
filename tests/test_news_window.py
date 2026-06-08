from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ff14_news.models import NewsArticle, NewsFeed, NewsFeedBundle

from impl.news.window import select_articles_in_window


def _article(
    article_id: str,
    *,
    published: datetime,
    channel_id: str = "cn_official",
) -> NewsArticle:
    return NewsArticle(
        channel_id=channel_id,
        id=article_id,
        title=f"title-{article_id}",
        publish_date=published,
        source_page_url=f"https://example.com/{article_id}",
    )


def test_select_articles_in_window() -> None:
    start = datetime(2026, 6, 8, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 8, 11, 0, tzinfo=timezone.utc)
    bundle = NewsFeedBundle(
        fetched_at=end,
        feeds={
            "cn_official": NewsFeed(
                channel_id="cn_official",
                source_list_url="https://example.com/list",
                fetched_at=end,
                articles=[
                    _article("old", published=datetime(2026, 6, 8, 9, 0, tzinfo=timezone.utc)),
                    _article("new", published=datetime(2026, 6, 8, 10, 30, tzinfo=timezone.utc)),
                    _article(
                        "edge",
                        published=datetime(2026, 6, 8, 10, 0, tzinfo=timezone.utc),
                    ),
                ],
            ),
        },
        errors=[],
    )
    selected = select_articles_in_window(bundle, window_start=start, window_end=end)
    assert [item.id for item in selected] == ["new"]
