from __future__ import annotations

import base64
from io import BytesIO

from ff14_the_hunt.models import HuntMarkRecord, MapCoordinate
from PIL import Image, ImageDraw, ImageFont

_PIN_COLORS: tuple[tuple[int, int, int], ...] = (
    (229, 57, 53),
    (251, 140, 0),
    (67, 160, 71),
    (30, 136, 229),
    (142, 36, 170),
    (0, 172, 193),
)
_PIN_OUTLINE = (255, 255, 255)
_LABEL_FILL = (24, 24, 24, 200)
_LABEL_TEXT = (255, 255, 255)


def _resolve_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _format_game_coordinate(point: MapCoordinate) -> str:
    if point.grid_x is not None and point.grid_y is not None:
        return f"{_format_axis(point.grid_x)}, {_format_axis(point.grid_y)}"
    return f"{_format_axis(point.x)}, {_format_axis(point.y)}"


def _format_axis(value: float) -> str:
    rounded = round(value, 1)
    if abs(rounded - round(rounded)) < 0.05:
        return str(int(round(rounded)))
    text = f"{rounded:.1f}".rstrip("0").rstrip(".")
    return text


def _marker_radius(image: Image.Image) -> int:
    return max(8, min(image.width, image.height) // 72)


def _label_font(image: Image.Image) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return _resolve_font(max(12, min(image.width, image.height) // 48))


def _draw_map_pin(
    draw: ImageDraw.ImageDraw,
    *,
    tip_x: int,
    tip_y: int,
    radius: int,
    fill: tuple[int, int, int],
) -> tuple[int, int]:
    """绘制图钉，尖端落在刷点像素上。"""
    head_cx = tip_x
    head_cy = tip_y - radius * 2
    outer = radius + 2
    draw.ellipse(
        (head_cx - outer, head_cy - outer, head_cx + outer, head_cy + outer),
        fill=_PIN_OUTLINE,
    )
    draw.ellipse(
        (head_cx - radius, head_cy - radius, head_cx + radius, head_cy + radius),
        fill=fill,
    )
    highlight = (
        max(0, fill[0] + 40),
        max(0, fill[1] + 40),
        max(0, fill[2] + 40),
    )
    inner = max(2, radius // 3)
    draw.ellipse(
        (
            head_cx - inner,
            head_cy - inner - radius // 4,
            head_cx + inner,
            head_cy + inner - radius // 4,
        ),
        fill=highlight,
    )
    draw.polygon(
        (
            (tip_x, tip_y),
            (tip_x - int(radius * 0.65), head_cy + int(radius * 0.35)),
            (tip_x + int(radius * 0.65), head_cy + int(radius * 0.35)),
        ),
        fill=fill,
    )
    draw.line(
        (
            tip_x - int(radius * 0.65),
            head_cy + int(radius * 0.35),
            tip_x + int(radius * 0.65),
            head_cy + int(radius * 0.35),
        ),
        fill=_PIN_OUTLINE,
        width=max(1, radius // 6),
    )
    return head_cx, head_cy


def _draw_coord_label(
    draw: ImageDraw.ImageDraw,
    *,
    text: str,
    anchor_x: int,
    anchor_y: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    image_size: tuple[int, int],
) -> None:
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    padding_x = 6
    padding_y = 3
    box_w = text_w + padding_x * 2
    box_h = text_h + padding_y * 2
    margin = 4
    box_x = anchor_x + margin
    box_y = anchor_y - box_h // 2
    width, height = image_size
    if box_x + box_w > width - margin:
        box_x = anchor_x - margin - box_w
    box_y = max(margin, min(box_y, height - box_h - margin))
    box_x = max(margin, min(box_x, width - box_w - margin))
    draw.rounded_rectangle(
        (box_x, box_y, box_x + box_w, box_y + box_h),
        radius=4,
        fill=_LABEL_FILL,
    )
    draw.text(
        (box_x + padding_x, box_y + padding_y - text_bbox[1]),
        text,
        font=font,
        fill=_LABEL_TEXT,
    )


def mark_region_map_png(
    png_bytes: bytes,
    points: list[MapCoordinate],
    *,
    marker_radius: int | None = None,
) -> bytes:
    """在区域原图上标出刷点像素位置，并标注游戏格点坐标。"""
    image = Image.open(BytesIO(png_bytes)).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    radius = marker_radius if marker_radius is not None else _marker_radius(image)
    font = _label_font(image)
    for index, point in enumerate(points):
        if point.pixel_x is None or point.pixel_y is None:
            continue
        tip_x = int(round(point.pixel_x))
        tip_y = int(round(point.pixel_y))
        fill = _PIN_COLORS[index % len(_PIN_COLORS)]
        head_cx, head_cy = _draw_map_pin(
            draw,
            tip_x=tip_x,
            tip_y=tip_y,
            radius=radius,
            fill=fill,
        )
        _draw_coord_label(
            draw,
            text=_format_game_coordinate(point),
            anchor_x=head_cx + radius,
            anchor_y=head_cy,
            font=font,
            image_size=image.size,
        )
    composed = Image.alpha_composite(image, overlay)
    out = BytesIO()
    composed.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()


def decode_region_map_bytes(mark: HuntMarkRecord) -> bytes | None:
    if mark.region_map is None:
        return None
    return base64.b64decode(mark.region_map.data_base64)
