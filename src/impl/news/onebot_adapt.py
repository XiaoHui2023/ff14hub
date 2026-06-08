from __future__ import annotations

from onebot_protocol import (
    ImageMessageSegment,
    MessagePayload,
    TextMessageSegment,
    TextSegmentData,
)
from onebot_protocol.models import ImageSegmentData

from ff14_news.models import NewsArticle


def article_to_message_payload(
    article: NewsArticle,
    *,
    display_name: str,
) -> MessagePayload:
    """将列表级新闻字段转为 onebot-protocol 消息段。"""
    time_text = article.publish_date.strftime("%Y-%m-%d %H:%M")
    lines = [f"[{display_name}] {article.title}", time_text]
    if article.summary:
        lines.append(article.summary)
    lines.append(article.source_page_url)
    segments: list[TextMessageSegment | ImageMessageSegment] = [
        TextMessageSegment(data=TextSegmentData(text="\n".join(lines))),
    ]
    if article.cover_image_url:
        segments.append(
            ImageMessageSegment(
                data=ImageSegmentData(content=article.cover_image_url),
            ),
        )
    return MessagePayload(
        message_type="group",
        group_id=f"ff14_news:{article.channel_id}",
        post_type="message",
        message=segments,
    )
