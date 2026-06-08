from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ff14_news.models import NewsArticle
from onebot_protocol import ImageMessageSegment, TextMessageSegment

from impl.news.onebot_adapt import article_to_message_payload


def test_article_to_message_payload() -> None:
    article = NewsArticle(
        channel_id="cn_official",
        id="1",
        title="测试标题",
        publish_date=datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc),
        summary="摘要",
        cover_image_url="https://example.com/cover.jpg",
        source_page_url="https://example.com/1",
    )
    payload = article_to_message_payload(article, display_name="国服官网")
    assert payload.session_id == "ff14_news:cn_official"
    assert payload.messages[0].type == "text"
    assert isinstance(payload.messages[0], TextMessageSegment)
    assert "测试标题" in payload.messages[0].data.text
    assert isinstance(payload.messages[1], ImageMessageSegment)
    assert payload.messages[1].data.content == "https://example.com/cover.jpg"
