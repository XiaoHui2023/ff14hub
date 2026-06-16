from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ff14_the_hunt.models import HuntMarkRecord, TimerBarColor, TimerDisplay, TimerKind

from impl.hunt.format import format_mark_message_text


def test_format_mark_message_text() -> None:
    mark = HuntMarkRecord(
        hunt_key="hunt_a",
        hunt_name="Hunt A",
        world_name="静语庄园",
        region="Coerthas Western Highlands",
        rank=1,
        patch="DT",
        trigger_timer=TimerDisplay(
            kind=TimerKind.TRIGGER,
            label="trigger",
            bar_color=TimerBarColor.SUCCESS,
            hex_color="#0f0",
            counts_up=False,
            summary="12:34",
        ),
    )
    text = format_mark_message_text(mark)
    assert text.startswith("[")
    assert "]" in text
    assert "静语庄园" not in text
    assert "12:34" not in text
    assert "刷点" not in text
