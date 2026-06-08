from __future__ import annotations

from io import BytesIO

from ff14_the_hunt.models import HuntMarkRecord
from rich.console import RenderableType
from textual_image.renderable import Image as TerminalImage

from impl.export.map_mark import decode_region_map_bytes, mark_region_map_png

_PANEL_HORIZONTAL_PADDING = 6


def render_mark_map_image(
    mark: HuntMarkRecord,
    *,
    console_width: int,
) -> RenderableType | None:
    """将区域地图（含刷点标点）渲染为终端图片。"""
    png_bytes = decode_region_map_bytes(mark)
    if png_bytes is None:
        return None
    if mark.spawn_points:
        png_bytes = mark_region_map_png(png_bytes, mark.spawn_points)
    try:
        cell_width = max(48, console_width - _PANEL_HORIZONTAL_PADDING)
        return TerminalImage(
            BytesIO(png_bytes),
            width=cell_width,
            height="auto",
        )
    except Exception:
        return None
