from __future__ import annotations

import base64
import struct
import zlib

from ff14_the_hunt.models import HuntMarkRecord, MapCoordinate


def _crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def _chunk(tag: bytes, payload: bytes) -> bytes:
    body = tag + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", _crc32(body))


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter_scanline(
    *,
    filter_type: int,
    row: bytes,
    previous: bytes | None,
    bpp: int,
) -> bytes:
    if filter_type == 0:
        return row
    out = bytearray(len(row))
    prev = previous or bytes(len(row))
    for index in range(len(row)):
        left = out[index - bpp] if index >= bpp else 0
        up = prev[index]
        up_left = prev[index - bpp] if index >= bpp else 0
        value = row[index]
        if filter_type == 1:
            out[index] = (value + left) & 0xFF
        elif filter_type == 2:
            out[index] = (value + up) & 0xFF
        elif filter_type == 3:
            out[index] = (value + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            out[index] = (value + _paeth(left, up, up_left)) & 0xFF
        else:
            raise ValueError(f"unsupported PNG filter {filter_type}")
    return bytes(out)


def _decode_png_rgba(data: bytes) -> tuple[int, int, bytearray]:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    offset = 8
    width = 0
    height = 0
    color_type = 0
    idat = bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        offset += 4
        tag = data[offset : offset + 4]
        offset += 4
        payload = data[offset : offset + length]
        offset += length + 4
        if tag == b"IHDR":
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(
                ">IIBBBBB",
                payload,
            )
            if bit_depth != 8 or color_type not in (2, 6):
                raise ValueError("only 8-bit RGB/RGBA PNG is supported")
        elif tag == b"IDAT":
            idat.extend(payload)
        elif tag == b"IEND":
            break
    if width <= 0 or height <= 0:
        raise ValueError("invalid PNG dimensions")
    bpp = 4 if color_type == 6 else 3
    stride = width * bpp
    raw = zlib.decompress(bytes(idat))
    pixels = bytearray(width * height * 4)
    previous: bytes | None = None
    cursor = 0
    for row_index in range(height):
        filter_type = raw[cursor]
        cursor += 1
        row = raw[cursor : cursor + stride]
        cursor += stride
        decoded = _unfilter_scanline(
            filter_type=filter_type,
            row=row,
            previous=previous,
            bpp=bpp,
        )
        previous = decoded
        for col in range(width):
            base = col * bpp
            alpha = decoded[base + 3] if bpp == 4 else 255
            red = decoded[base]
            green = decoded[base + 1]
            blue = decoded[base + 2]
            out = (row_index * width + col) * 4
            pixels[out : out + 4] = bytes((red, green, blue, alpha))
    return width, height, pixels


def _encode_png_rgba(width: int, height: int, pixels: bytearray) -> bytes:
    stride = width * 4
    raw = bytearray()
    previous = bytes(stride)
    for row_index in range(height):
        row_start = row_index * stride
        row = bytes(pixels[row_start : row_start + stride])
        filtered = bytearray(stride)
        for index in range(stride):
            left = row[index - 4] if index >= 4 else 0
            up = previous[index]
            filtered[index] = (row[index] - left) & 0xFF
        raw.append(1)
        raw.extend(filtered)
        previous = row
    compressed = zlib.compress(bytes(raw), level=6)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )


def _draw_filled_circle(
    pixels: bytearray,
    *,
    width: int,
    height: int,
    center_x: int,
    center_y: int,
    radius: int,
    color: tuple[int, int, int, int],
) -> None:
    radius_sq = radius * radius
    y_min = max(0, center_y - radius)
    y_max = min(height - 1, center_y + radius)
    x_min = max(0, center_x - radius)
    x_max = min(width - 1, center_x + radius)
    for y in range(y_min, y_max + 1):
        for x in range(x_min, x_max + 1):
            dx = x - center_x
            dy = y - center_y
            if dx * dx + dy * dy > radius_sq:
                continue
            offset = (y * width + x) * 4
            pixels[offset : offset + 4] = bytes(color)


def mark_region_map_png(
    png_bytes: bytes,
    points: list[MapCoordinate],
    *,
    marker_radius: int = 8,
) -> bytes:
    """在区域原图上标出刷点像素位置。"""
    width, height, pixels = _decode_png_rgba(png_bytes)
    outer = (255, 40, 40, 255)
    inner = (255, 220, 80, 255)
    for point in points:
        if point.pixel_x is None or point.pixel_y is None:
            continue
        cx = int(round(point.pixel_x))
        cy = int(round(point.pixel_y))
        _draw_filled_circle(
            pixels,
            width=width,
            height=height,
            center_x=cx,
            center_y=cy,
            radius=marker_radius + 2,
            color=outer,
        )
        _draw_filled_circle(
            pixels,
            width=width,
            height=height,
            center_x=cx,
            center_y=cy,
            radius=marker_radius,
            color=inner,
        )
    return _encode_png_rgba(width, height, pixels)


def decode_region_map_bytes(mark: HuntMarkRecord) -> bytes | None:
    if mark.region_map is None:
        return None
    return base64.b64decode(mark.region_map.data_base64)
