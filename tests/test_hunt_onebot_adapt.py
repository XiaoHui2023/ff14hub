from __future__ import annotations

import base64
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ff14_the_hunt.models import (
    HuntMarkRecord,
    MapCoordinate,
    RegionMapImage,
    TimerBarColor,
    TimerDisplay,
    TimerKind,
)
from onebot_protocol import ImageMessageSegment, TextMessageSegment

from impl.hunt.onebot_adapt import mark_to_message_payload

_PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_mark_to_message_payload() -> None:
    mark = HuntMarkRecord(
        hunt_key="hunt_a",
        hunt_name="Hunt A",
        world_name="静语庄园",
        region="Coerthas Western Highlands",
        rank=1,
        patch="DT",
        newly_spawned=True,
        trigger_timer=TimerDisplay(
            kind=TimerKind.TRIGGER,
            label="trigger",
            bar_color=TimerBarColor.SUCCESS,
            hex_color="#0f0",
            counts_up=False,
            summary="12:34",
        ),
        spawn_points=[
            MapCoordinate(
                point_key="A",
                x=0.5,
                y=0.5,
                pixel_x=100.0,
                pixel_y=200.0,
            ),
        ],
        region_map=RegionMapImage(
            region="test",
            source_url="https://example.com/map.png",
            width=1,
            height=1,
            data_base64=base64.b64encode(_PNG_1X1).decode("ascii"),
        ),
    )
    payload = mark_to_message_payload(mark)
    assert payload.group_id == "ff14_hunt:静语庄园:hunt_a"
    assert isinstance(payload.message[0], TextMessageSegment)
    assert "静语庄园" in payload.message[0].data.text
    assert isinstance(payload.message[1], ImageMessageSegment)
    assert payload.message[1].data.mime_type == "image/png"
