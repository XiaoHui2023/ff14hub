from __future__ import annotations

import base64

from ff14_the_hunt.locale.tag import HuntDisplayLocale
from ff14_the_hunt.models import HuntMarkRecord
from onebot_protocol import (
    ImageMessageSegment,
    MessagePayload,
    TextMessageSegment,
    TextSegmentData,
)
from onebot_protocol.models import ImageSegmentData

from impl.export.map_mark import decode_region_map_bytes, mark_region_map_png
from impl.hunt.format import format_mark_message_text


def mark_to_message_payload(
    mark: HuntMarkRecord,
    *,
    locale: HuntDisplayLocale = HuntDisplayLocale.ZH,
) -> MessagePayload:
    """将新检出狩猎记录转为 onebot-protocol 消息段。"""
    segments: list[TextMessageSegment | ImageMessageSegment] = [
        TextMessageSegment(
            data=TextSegmentData(text=format_mark_message_text(mark, locale=locale)),
        ),
    ]
    image_segment = _region_map_image_segment(mark)
    if image_segment is not None:
        segments.append(image_segment)
    return MessagePayload(
        source_type="group",
        session_id=f"ff14_hunt:{mark.world_name}:{mark.hunt_key}",
        post_type="message",
        messages=segments,
    )


def _region_map_image_segment(mark: HuntMarkRecord) -> ImageMessageSegment | None:
    png_bytes = decode_region_map_bytes(mark)
    if png_bytes is None:
        return None
    if mark.spawn_points:
        png_bytes = mark_region_map_png(png_bytes, mark.spawn_points)
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return ImageMessageSegment(
        data=ImageSegmentData(
            content=encoded,
            mime_type="image/png",
            name=f"{mark.hunt_key}-{mark.world_name}.png",
        ),
    )
