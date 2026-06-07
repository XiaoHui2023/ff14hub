from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from impl.export.map_mark import mark_region_map_png
from ff14_the_hunt.models import MapCoordinate


def _solid_png(*, width: int, height: int, rgba: tuple[int, int, int, int]) -> bytes:
    stride = width * 4
    raw = bytearray()
    row = bytes(rgba) * width
    for _ in range(height):
        raw.append(0)
        raw.extend(row)
    compressed = zlib.compress(bytes(raw), level=6)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        body = tag + payload
        crc = zlib.crc32(body) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", crc)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )


def test_mark_region_map_png_changes_bytes() -> None:
    source = _solid_png(width=32, height=32, rgba=(20, 40, 60, 255))
    points = [
        MapCoordinate(
            point_key="SpawnPoint01",
            x=0.5,
            y=0.5,
            pixel_x=16.0,
            pixel_y=16.0,
        )
    ]
    marked = mark_region_map_png(source, points, marker_radius=4)
    assert marked != source
    assert marked.startswith(b"\x89PNG")
