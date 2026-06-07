from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

AGENT_THEME = Theme(
    {
        "hunt.title": "#61afef",
        "hunt.rank": "#c678dd",
        "hunt.world": "#98c379",
        "hunt.region": "#56b6c2",
        "hunt.timer.error": "#e06c75",
        "hunt.timer.success": "#98c379",
        "hunt.timer.info": "#61afef",
        "hunt.timer.warning": "#e5c07b",
        "hunt.spawn": "#d19a66",
        "hunt.new": "#e5c07b",
        "hunt.dim": "#5c6370",
    }
)


def make_console() -> Console:
    return Console(
        theme=AGENT_THEME,
        color_system="truecolor",
        force_terminal=True,
        legacy_windows=False,
    )
